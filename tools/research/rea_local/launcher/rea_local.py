#!/usr/bin/python3 -I
# SPDX-License-Identifier: GPL-2.0-only
"""Local static REA launcher. No setup, MCP, target execution or updates.

All real process launch goes through the separately reviewed sandbox backend.
Importing this file never launches tools or inspects an analysis input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
TOOLS = Path.home() / '.local/share/rea-local/tools'
JOBS = Path.home() / 'Documents/REA-Analysen'
SANDBOX = HERE.parent / 'sandbox/sandbox_plan.py'
NODE = Path('node-v24.19.0/bin/node')
REA = Path('rea-6.5.0/node_modules/rea-agents/scripts/rea.mjs')
MAX_FILES = 4096
MAX_ENTRIES = 8192
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_DEPTH = 32
TIMEOUT_SECONDS = 900
LOG_LIMIT_BYTES = 128 * 1024 * 1024


class Refused(Exception):
    """An admission or integrity guard failed; message must not contain inputs."""


def write_json(path: Path, value: object) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def selected_path(value: str | Path) -> Path:
    """Lexical normalization only; never resolve a caller-controlled symlink."""
    path = Path(os.path.abspath(os.path.expanduser(str(value))))
    if any(path == root or path.is_relative_to(root) for root in (Path('/proc'), Path('/sys'), Path('/dev'), Path('/run'))):
        raise Refused('Kernel, device and process files are not analysis inputs')
    return path


def open_selected(value: str | Path) -> int:
    """Open each directory component without following symlinks, then the leaf."""
    path = selected_path(value)
    if path == Path('/'):
        raise Refused('Filesystem root is not an analysis input')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        parts = path.parts[1:]
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = child
        result = open_item(parts[-1], fd)
    except OSError as exc:
        raise Refused('Input is missing, inaccessible, or contains a symlink') from exc
    finally:
        os.close(fd)
    return result


def open_item(name: str, parent_fd: int) -> int:
    """Inspect with O_PATH first: never open a special input node for reading."""
    anchor = os.open(name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
    try:
        info = os.fstat(anchor)
        if stat.S_ISDIR(info.st_mode):
            return os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=anchor)
        if not stat.S_ISREG(info.st_mode):
            raise Refused('Only regular files and directories are admitted')
        # This kernel-owned proc link refers to the pinned regular inode, even
        # if its caller-controlled directory entry is replaced in the meantime.
        result = os.open(f'/proc/self/fd/{anchor}', os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK)
        if identity(os.fstat(result)) != identity(info):
            os.close(result)
            raise Refused('Input inode changed while opening')
        return result
    finally:
        os.close(anchor)


def identity(st: os.stat_result) -> list[int]:
    return [st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def snapshot(value: str | Path, destination: Path | None = None) -> dict:
    """Hash a bounded regular file/tree; optionally make a non-executable copy.

    Directory descriptors anchor traversal. Every opened item is fstat-checked;
    symlinks, devices, sockets, FIFOs and changing files fail closed.
    """
    records: list[dict] = []
    totals = {'files': 0, 'entries': 0, 'bytes': 0}
    root_fd = open_selected(value)

    def visit(fd: int, relative: str, target: Path | None, depth: int) -> None:
        before = os.fstat(fd)
        totals['entries'] += 1
        if totals['entries'] > MAX_ENTRIES or depth > MAX_DEPTH:
            raise Refused('Input entry/depth limit exceeded')
        if stat.S_ISREG(before.st_mode):
            totals['files'] += 1
            totals['bytes'] += before.st_size
            if (totals['files'] > MAX_FILES or before.st_size > MAX_FILE_BYTES
                    or totals['bytes'] > MAX_TOTAL_BYTES):
                raise Refused('Input file/byte limit exceeded')
            digest = hashlib.sha256()
            output = None
            if target is not None:
                output = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
            observed = 0
            try:
                while True:
                    block = os.read(fd, 1024 * 1024)
                    if not block:
                        break
                    observed += len(block)
                    if observed > before.st_size or observed > MAX_FILE_BYTES:
                        raise Refused('Input grew during copying')
                    digest.update(block)
                    if output is not None:
                        view = memoryview(block)
                        while view:
                            written = os.write(output, view)
                            view = view[written:]
                if output is not None:
                    os.fsync(output)
            finally:
                if output is not None:
                    os.close(output)
            if observed != before.st_size or identity(os.fstat(fd)) != identity(before):
                raise Refused('Input changed during hashing/copying')
            records.append({'relative': relative, 'kind': 'file', 'bytes': observed,
                            'sha256': digest.hexdigest(), 'identity': identity(before)})
        elif stat.S_ISDIR(before.st_mode):
            if target is not None:
                target.mkdir(mode=0o700)
            entries = []
            with os.scandir(fd) as iterator:
                for entry in iterator:
                    entries.append(entry.name)
                    if len(entries) + totals['entries'] > MAX_ENTRIES:
                        raise Refused('Input entry limit exceeded')
            entries.sort()
            records.append({'relative': relative, 'kind': 'directory', 'identity': identity(before)})
            for entry in entries:
                try:
                    child = open_item(entry, fd)
                except OSError as exc:
                    raise Refused('Input contains an inaccessible item or symlink') from exc
                try:
                    child_relative = entry if relative == '.' else relative + '/' + entry
                    visit(child, child_relative, None if target is None else target / entry, depth + 1)
                finally:
                    os.close(child)
            if identity(os.fstat(fd)) != identity(before):
                raise Refused('Input directory changed during traversal')
            if target is not None:
                target.chmod(0o500)
        else:
            raise Refused('Only regular files and directories are admitted')

    try:
        root_kind = 'directory' if stat.S_ISDIR(os.fstat(root_fd).st_mode) else 'file'
        visit(root_fd, '.', destination, 0)
    finally:
        os.close(root_fd)
    content = [{key: item[key] for key in ('relative', 'kind', 'bytes', 'sha256') if key in item}
               for item in records]
    tree_hash = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schema': 1, 'kind': root_kind, 'files': totals['files'], 'bytes': totals['bytes'],
            'content_sha256': tree_hash, 'records': records}


def content_matches(left: dict, right: dict) -> bool:
    return (left['kind'], left['files'], left['bytes'], left['content_sha256']) == (
        right['kind'], right['files'], right['bytes'], right['content_sha256'])


def static_command(mode: str, target: str, address: str | None = None) -> list[str]:
    """No arbitrary REA arguments, architecture guesses, runtimes or MCP entry."""
    if not target.startswith('/input/') or '\x00' in target or '..' in Path(target).parts:
        raise Refused('Invalid sandbox input target')
    if mode == 'function':
        if address is None or re.fullmatch(r'0x[0-9a-fA-F]{1,16}', address) is None:
            raise Refused('Function selector must be an explicit hexadecimal address')
        return ['function', target, address.lower(), '--provider', 'ghidra', '--json']
    if address is not None:
        raise Refused('Unexpected function selector')
    if mode == 'native':
        return ['inspect', target, '--provider', 'ghidra', '--json']
    if mode == 'javascript':
        return ['analyze-javascript-application', target, '--json']
    if mode == 'managed':
        return ['inspect-managed-artifact', target, '--json']
    if mode == 'artifact':
        return ['inspect-artifact', target, '--json']
    raise Refused('Only static analysis commands are admitted')


def private_root(path: Path) -> Path:
    path = selected_path(path)
    if not path.exists():
        # Only the single final component is created; an absent parent is an error.
        path.mkdir(mode=0o700)
    descriptor = open_selected(path)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise Refused('Analysis root must be current-user owned and mode 0700')
    finally:
        os.close(descriptor)
    return path


def load_backend():
    # This trusted sibling is part of the separately reviewed local installation.
    if SANDBOX != SANDBOX.resolve(strict=True) or not SANDBOX.is_file():
        raise Refused('Reviewed sandbox backend missing')
    info = SANDBOX.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o022:
        raise Refused('Sandbox backend owner/permissions changed')
    spec = importlib.util.spec_from_file_location('rea_local_sandbox', SANDBOX)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_job(mode: str, selected: str, address: str | None = None, *, jobs_root: Path = JOBS) -> dict:
    if os.geteuid() == 0:
        raise Refused('Run as the regular user; never sudo')
    # Validate command/selector before accessing the selected input.
    static_command(mode, '/input/source', address)
    source = selected_path(selected)
    before = snapshot(source)
    if mode != 'javascript' and before['kind'] != 'file':
        raise Refused('This static lane requires one regular file')
    jobs = private_root(jobs_root)
    # Avoid recursively copying our own destination into a selected source tree.
    if before['kind'] == 'directory' and (jobs == source or jobs.is_relative_to(source)):
        raise Refused('Analysis destination lies inside selected input')
    job = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-'), dir=jobs))
    job.chmod(0o700)
    input_root, work = job / 'input', job / 'work'
    input_root.mkdir(mode=0o700)
    work.mkdir(mode=0o700)
    suffix = source.suffix.lower()
    if before['kind'] == 'directory':
        copied = input_root / 'application'
        target = '/input/application'
    elif mode == 'javascript' and suffix in ('.js', '.mjs', '.cjs', '.jsx', '.ts', '.tsx'):
        application = input_root / 'application'
        application.mkdir(mode=0o700)
        copied = application / ('source' + suffix)
        target = '/input/application'
    else:
        # Keep only a short inert suffix; no caller-controlled REA option or path.
        safe_suffix = suffix if re.fullmatch(r'\.[a-z0-9]{1,12}', suffix) else '.bin'
        copied = input_root / ('source' + safe_suffix)
        target = '/input/' + copied.name
    during = snapshot(source, copied)
    after = snapshot(source)
    copy_hash = snapshot(copied)
    if before != during or before != after or not content_matches(before, copy_hash):
        raise Refused('Original or staged input changed')
    for directory, dirs, files in os.walk(input_root, topdown=False, followlinks=False):
        Path(directory).chmod(0o500)
    command = static_command(mode, target, address)
    plan = {'schema': 1, 'kind': 'static-rea-analysis', 'job_id': job.name,
            'job': str(job), 'mode': mode, 'source': str(source),
            'before': before, 'copy': copy_hash, 'copy_path': str(copied), 'input_dir': str(input_root),
            'work_dir': str(work), 'command': command, 'target': target}
    write_json(job / 'plan.json', plan)
    return plan


def child_limits() -> None:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LOG_LIMIT_BYTES, LOG_LIMIT_BYTES))


def run_job(plan: dict, backend, *, tools_root: Path = TOOLS, runner=subprocess.Popen) -> dict:
    """Called only by explicit CLI invocation, after source/plan review."""
    if not hasattr(backend, 'prepare_analysis_argv'):
        raise Refused('Analysis sandbox backend not yet approved; draft remains plan-only')
    if plan['command'] != static_command(plan['mode'], plan['target'],
            plan['command'][2] if plan['mode'] == 'function' else None):
        raise Refused('Prepared command changed')
    if snapshot(plan['source']) != plan['before']:
        raise Refused('Original changed before analysis')
    if not content_matches(snapshot(plan['copy_path']), plan['copy']):
        raise Refused('Staged input changed before analysis')
    job = private_root(Path(plan['job']))
    work = private_root(Path(plan['work_dir']))
    argv = backend.prepare_analysis_argv(tools_root=str(tools_root),
                input_dir=plan['input_dir'], work_dir=str(work),
                command=plan['command'])
    write_json(job / 'launch.json', {'schema': 1, 'argv': argv, 'timeout_seconds': TIMEOUT_SECONDS,
                                   'target_execution': False, 'network': False})
    stdout_fd = os.open(work / 'rea.stdout.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    stderr_fd = os.open(work / 'rea.stderr.log', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    completed = None
    failure = None
    process = None
    try:
        process = runner(argv, stdin=subprocess.DEVNULL, stdout=stdout_fd, stderr=stderr_fd,
                         env={}, close_fds=True, pass_fds=(), shell=False,
                         start_new_session=True, preexec_fn=child_limits)
        try:
            completed = process.wait(timeout=TIMEOUT_SECONDS)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            failure = 'timeout-or-interruption'
    except (Exception, KeyboardInterrupt):
        failure = 'sandbox-launch-failed'
    finally:
        if process is not None:
            try:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)
            except (Exception, KeyboardInterrupt):
                failure = 'sandbox-cleanup-unconfirmed'
        os.close(stdout_fd)
        os.close(stderr_fd)
    try:
        unchanged = snapshot(plan['source']) == plan['before']
    except Exception:
        unchanged = False
    try:
        copy_unchanged = content_matches(snapshot(plan['copy_path']), plan['copy'])
    except Exception:
        copy_unchanged = False
    source_hash = (plan['before']['records'][0]['sha256'] if plan['before']['kind'] == 'file'
                   else plan['before']['content_sha256'])
    result = {'schema': 1, 'job_id': plan['job_id'], 'mode': plan['mode'],
              'input_sha256': source_hash, 'hash_kind': 'file' if plan['before']['kind'] == 'file' else 'tree-manifest',
              'original_unchanged': unchanged, 'staged_input_unchanged': copy_unchanged,
              'exit_code': completed, 'failure': failure,
              'completed': completed == 0 and failure is None and unchanged and copy_unchanged,
              'note': 'Process completion is not proof of a successful or correct REA analysis; inspect private reports.'}
    write_json(job / 'result.json', result)
    return result


def check(backend, *, tools_root: Path = TOOLS, jobs_root: Path = JOBS) -> dict:
    jobs = private_root(jobs_root)
    plan = backend.prepare_plan(node_binary=str(tools_root / NODE), tools_root=str(tools_root), output_root=str(jobs))
    result = backend.run_reviewed_dry_run(plan, authorization='device-free-bubblewrap-dry-run')
    return {'check': result.get('passed') is True, 'job_id': Path(plan['run_root']).name,
            'rea_executed': False, 'analysis_input_mounted': False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Private, network-isolated static REA analysis; no target execution')
    commands = parser.add_subparsers(dest='mode', required=True)
    commands.add_parser('check', help='Check isolation without REA or an analysis input')
    for mode in ('javascript', 'native', 'managed', 'artifact', 'function'):
        sub = commands.add_parser(mode)
        sub.add_argument('path')
        if mode == 'function':
            sub.add_argument('address')
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        if os.geteuid() == 0:
            raise Refused('Run as the regular user; never sudo')
        backend = load_backend()
        if args.mode == 'check':
            status = check(backend)
        else:
            # Fail before copying if the separately reviewed backend is absent.
            if not hasattr(backend, 'prepare_analysis_argv'):
                raise Refused('Analysis sandbox backend not yet approved; draft remains plan-only')
            plan = prepare_job(args.mode, args.path, getattr(args, 'address', None))
            status = run_job(plan, backend)
        print(json.dumps(status, ensure_ascii=True))
        return 0 if status.get('check', status.get('completed', False)) else 1
    except (Exception, KeyboardInterrupt) as exc:
        # Never emit exception repr/traceback or an input-derived string to terminal.
        reason = str(exc) if isinstance(exc, Refused) else 'Local guard failed; no raw diagnostics printed'
        print(json.dumps({'completed': False, 'reason': reason}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
