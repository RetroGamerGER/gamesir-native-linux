# SPDX-License-Identifier: GPL-2.0-only
"""Prepare a device-free Bubblewrap probe; importing/planning never runs it.

This does not run REA, admit firmware, install dependencies or edit MCP settings.
Root must review these files before explicitly calling run_reviewed_dry_run().
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
NAMESPACES = ('mnt', 'pid', 'user', 'net', 'ipc', 'uts', 'cgroup')
SOURCE_NAMES = ('sandbox_probe.py', 'node_probe.mjs', 'sandbox_plan.py')


def canonical_regular(value: str | Path, executable: bool = False) -> Path:
    path = Path(value)
    if not path.is_absolute() or path != path.resolve(strict=True):
        raise ValueError('Explicit canonical absolute path required')
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode):
        raise ValueError('Regular file required')
    if st.st_mode & 0o022:
        raise ValueError('Group/world writable executable or probe refused')
    if executable and not os.access(path, os.X_OK):
        raise ValueError('Executable prerequisite missing')
    return path


def private_directory(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute() or path != path.resolve(strict=True):
        raise ValueError('Explicit canonical directory required')
    st = path.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700:
        raise ValueError('Current-user private directory with mode 0700 required')
    return path


def stamp(path: Path) -> dict:
    st = path.lstat()
    return {'path': str(path), 'device': st.st_dev, 'inode': st.st_ino,
            'bytes': st.st_size, 'mode': stat.S_IMODE(st.st_mode),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def write_new_json(path: Path, value: object) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def build_argv(*, bwrap: str, node_binary: str, tools_root: str,
               out_dir: str, baseline: str, probe_python: str,
               probe_node: str, uid: int, gid: int,
               system_aliases: dict[str, str], ld_cache: str | None) -> list[str]:
    """Pure argument construction only; no discovery, files or subprocesses."""
    if type(uid) is not int or uid <= 0 or type(gid) is not int or gid < 0:
        raise ValueError('Probe must preserve a non-root user identity')
    paths = (bwrap, node_binary, tools_root, out_dir, baseline, probe_python, probe_node)
    if any(not isinstance(x, str) or not x.startswith('/') or '\x00' in x for x in paths):
        raise ValueError('Explicit absolute arguments required')
    node_relative = Path(node_binary).relative_to(Path(tools_root))
    node_inside = str(Path('/tools') / node_relative)
    argv = [bwrap, '--die-with-parent', '--new-session',
            '--unshare-user', '--unshare-pid', '--unshare-net', '--unshare-ipc',
            '--unshare-uts', '--unshare-cgroup', '--uid', str(uid), '--gid', str(gid),
            '--cap-drop', 'ALL', '--clearenv', '--ro-bind', '/usr', '/usr']
    for alias, target in sorted(system_aliases.items()):
        if alias not in ('/bin', '/sbin', '/lib', '/lib64') or not target.startswith('usr/'):
            raise ValueError('Unexpected system compatibility alias')
        argv += ['--symlink', target, alias]
    if ld_cache is not None:
        argv += ['--dir', '/etc', '--ro-bind', ld_cache, '/etc/ld.so.cache']
    argv += ['--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
             '--dir', '/home', '--tmpfs', '/home/rea',
             '--chmod', '0700', '/tmp', '--chmod', '0700', '/home/rea',
             '--dir', '/opt', '--dir', '/opt/rea-check',
             '--ro-bind', tools_root, '/tools',
             '--ro-bind', probe_python, '/opt/rea-check/probe.py',
             '--ro-bind', probe_node, '/opt/rea-check/node-probe.mjs',
             '--ro-bind', baseline, '/opt/rea-check/baseline.json',
             '--bind', out_dir, '/out',
             '--setenv', 'HOME', '/home/rea',
             '--setenv', 'XDG_CACHE_HOME', '/home/rea/.cache',
             '--setenv', 'XDG_CONFIG_HOME', '/home/rea/.config',
             '--setenv', 'TMPDIR', '/tmp',
             '--setenv', 'PATH', str(Path(node_inside).parent) + ':/usr/bin',
             '--setenv', 'LC_ALL', 'C',
             '--remount-ro', '/', '--chdir', '/out',
             '/usr/bin/python3', '-I', '/opt/rea-check/probe.py']
    return argv


def prepare_plan(*, node_binary: str, tools_root: str, output_root: str,
                 bwrap_binary: str = '/usr/bin/bwrap') -> dict:
    """Read prerequisite metadata and create only one new private run directory."""
    uid, gid = os.geteuid(), os.getegid()
    if uid == 0:
        raise ValueError('No sudo/root execution admitted')
    node = canonical_regular(node_binary, executable=True)
    bwrap = canonical_regular(bwrap_binary, executable=True)
    if bwrap.stat().st_uid != 0:
        raise ValueError('Expected system-owned Bubblewrap')
    tools = private_directory(tools_root)
    if not node.is_relative_to(tools):
        raise ValueError('Node must be the reviewed copy within the tools root')
    output = private_directory(output_root)
    probes = {name: canonical_regular(HERE / name) for name in SOURCE_NAMES}
    aliases = {}
    for alias in ('/bin', '/sbin', '/lib', '/lib64'):
        p = Path(alias)
        if not p.is_symlink():
            raise ValueError('Host compatibility path requires separate review')
        target = p.resolve(strict=True)
        if not target.is_relative_to('/usr') or not target.is_dir():
            raise ValueError('Compatibility link escapes /usr')
        aliases[alias] = str(target).lstrip('/')
    ld_cache = None
    if Path('/etc/ld.so.cache').exists():
        ld_cache = str(canonical_regular('/etc/ld.so.cache'))
    run_root = Path(tempfile.mkdtemp(prefix='device-free-dry-run-', dir=output))
    run_root.chmod(0o700)
    out = run_root / 'out'
    out.mkdir(mode=0o700)
    baseline = {'schema': 1, 'uid': uid, 'gid': gid,
                'namespaces': {name: os.readlink(f'/proc/self/ns/{name}') for name in NAMESPACES},
                'mount_aliases': aliases,
                'expected_uid_map': [[uid, 0, 1]], 'expected_gid_map': [[gid, 0, 1]],
                'mapping_model': 'bubblewrap-0.13.1 --dev: outer caller->0, inner requested-id->outer-0; not host root',
                'mapping_source': 'https://github.com/containers/bubblewrap/blob/v0.13.1/bubblewrap.c#L3030-L3048',
                'node_sha256': stamp(node)['sha256'],
                'probe_node_sha256': stamp(probes['node_probe.mjs'])['sha256'],
                'expected_stdout_regular': True,
                'node_inside': str(Path('/tools') / node.relative_to(tools))}
    baseline_path = run_root / 'baseline.json'
    write_new_json(baseline_path, baseline)
    builder_spec = dict(bwrap=str(bwrap), node_binary=str(node), tools_root=str(tools),
                      out_dir=str(out), baseline=str(baseline_path),
                      probe_python=str(probes['sandbox_probe.py']),
                      probe_node=str(probes['node_probe.mjs']), uid=uid, gid=gid,
                      system_aliases=aliases, ld_cache=ld_cache)
    argv = build_argv(**builder_spec)
    plan = {'schema': 1, 'kind': 'device-free-bubblewrap-probe-only',
            'rea_executed': False, 'firmware_mounted': False,
            'run_root': str(run_root), 'out_dir': str(out),
            'uid': uid, 'gid': gid, 'argv': argv, 'builder_spec': builder_spec,
            'source_stamps': [stamp(p) for p in [node, bwrap, baseline_path, *probes.values()]],
            'tools_root': str(tools),
            'tools_root_note': 'Only mounted read-only; no REA or dependency entrypoint is invoked by this probe.'}
    write_new_json(run_root / 'plan.json', plan)
    return plan


def run_reviewed_dry_run(plan: dict, *, authorization: str) -> dict:
    """Call only after source/plan review. No REA, firmware, device or sudo path."""
    if authorization != 'device-free-bubblewrap-dry-run':
        raise ValueError('Explicit reviewed dry-run authorization required')
    if plan.get('kind') != 'device-free-bubblewrap-probe-only' or plan.get('uid') != os.geteuid() or os.geteuid() == 0:
        raise ValueError('Wrong plan or identity')
    if build_argv(**plan['builder_spec']) != plan['argv']:
        raise ValueError('Prepared Bubblewrap arguments changed')
    for expected in plan['source_stamps']:
        p = canonical_regular(expected['path'])
        if stamp(p) != expected:
            raise ValueError('Reviewed source/prerequisite changed')
    private_directory(plan['tools_root'])
    out = private_directory(plan['out_dir'])
    stdout_path, stderr_path = out / 'probe.stdout', out / 'probe.stderr'
    stdout_fd = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    stderr_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with open(os.devnull, 'rb') as null:
            completed = subprocess.run(plan['argv'], stdin=null, stdout=stdout_fd,
                                       stderr=stderr_fd, shell=False, close_fds=True,
                                       pass_fds=(), check=False, timeout=30)
    finally:
        os.close(stdout_fd)
        os.close(stderr_fd)
    if completed.returncode != 0:
        raise RuntimeError('Device-free isolation probe failed; stop and review private diagnostics')
    result_path = out / 'result.json'
    result = json.loads(result_path.read_text())
    if result.get('passed') is not True:
        raise RuntimeError('Probe did not positively confirm every requested guard')
    for expected in plan['source_stamps']:
        if stamp(Path(expected['path'])) != expected:
            raise RuntimeError('Reviewed source/prerequisite changed during probe')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare only; never launches Bubblewrap, Node or REA')
    parser.add_argument('--node-binary', required=True)
    parser.add_argument('--tools-root', required=True)
    parser.add_argument('--output-root', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_plan(node_binary=args.node_binary, tools_root=args.tools_root,
                                  output_root=args.output_root), indent=2))

# Reusable static-analysis extension. The original device-free API stays intact.
def validate_analysis_command(command: list[str]) -> list[str]:
    """Exactly five static lanes; no free flags, target execution or MCP entry."""
    import re
    if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
        raise ValueError('Static command vector required')
    if len(command) < 2 or re.fullmatch(r'/input/(?:source(?:\.[a-z0-9]{1,12})?|application)', command[1]) is None:
        raise ValueError('Only the staged inert input target is admitted')
    name, target = command[:2]
    if name == 'inspect':
        expected = ['inspect', target, '--provider', 'ghidra', '--json']
    elif name == 'function':
        if len(command) < 3 or re.fullmatch(r'0x[0-9a-fA-F]{1,16}', command[2]) is None:
            raise ValueError('Explicit hexadecimal function selector required')
        expected = ['function', target, command[2], '--provider', 'ghidra', '--json']
    elif name in ('analyze-javascript-application', 'inspect-managed-artifact', 'inspect-artifact'):
        expected = [name, target, '--json']
    else:
        raise ValueError('Only the five reviewed static operations are admitted')
    if command != expected:
        raise ValueError('Unreviewed static operation arguments')
    return list(command)


def prepare_analysis_argv(*, tools_root: str, input_dir: str,
                          work_dir: str, command: list[str]) -> list[str]:
    """Prepare a fresh copied-input job only; never launches any process.

    Launcher owns copied input admission and before/after hashing. This backend
    independently refuses links/specials, arbitrary commands, extra writable
    host mounts and privileged identities. The in-sandbox guard runs the same
    complete probe BEFORE replacing itself with the trusted REA entrypoint.
    """
    command = validate_analysis_command(command)
    if os.geteuid() == 0:
        raise ValueError('Never run analysis as root')
    tools = private_directory(tools_root)
    work = private_directory(work_dir)
    source = Path(input_dir)
    if not source.is_absolute() or source != source.resolve(strict=True):
        raise ValueError('Canonical staged input directory required')
    source_st = source.lstat()
    if (not stat.S_ISDIR(source_st.st_mode) or source_st.st_uid != os.geteuid()
            or stat.S_IMODE(source_st.st_mode) != 0o500):
        raise ValueError('Staged input must be current-user owned and mode 0500')
    job = private_directory(work.parent)
    if source.parent != job or work.name != 'work' or source.name != 'input':
        raise ValueError('Expected fresh job/input and job/work siblings')
    if any(work.iterdir()):
        raise ValueError('Static-analysis work directory must be fresh and empty')
    node = canonical_regular(tools / 'node-v24.19.0/bin/node', executable=True)
    rea = canonical_regular(tools / 'rea-6.5.0/node_modules/rea-agents/scripts/rea.mjs')
    bwrap = canonical_regular('/usr/bin/bwrap', executable=True)
    if bwrap.stat().st_uid != 0:
        raise ValueError('Expected system-owned Bubblewrap')
    probes = {name: canonical_regular(HERE / name) for name in (*SOURCE_NAMES, 'analysis_guard.py')}
    # Input is a private, non-executable copy; admit no links or special nodes.
    entries = 0
    for root, directories, files in os.walk(source, followlinks=False):
        for name in [*directories, *files]:
            p = Path(root) / name
            st = p.lstat()
            entries += 1
            if entries > 8192 or st.st_uid != os.geteuid():
                raise ValueError('Staged input metadata limit or owner mismatch')
            if stat.S_ISDIR(st.st_mode):
                if stat.S_IMODE(st.st_mode) != 0o500:
                    raise ValueError('Staged directory must have mode 0500')
            elif stat.S_ISREG(st.st_mode):
                if stat.S_IMODE(st.st_mode) != 0o400:
                    raise ValueError('Staged file must have mode 0400')
            else:
                raise ValueError('Staged input contains a link or special node')
    target = source / Path(command[1]).relative_to('/input')
    if not target.exists():
        raise ValueError('Selected copied target is absent')
    if command[0] != 'analyze-javascript-application' and not target.is_file():
        raise ValueError('This static lane requires a regular copied file')
    aliases = {}
    for alias in ('/bin', '/sbin', '/lib', '/lib64'):
        p = Path(alias)
        target_alias = p.resolve(strict=True)
        if not p.is_symlink() or not target_alias.is_relative_to('/usr') or not target_alias.is_dir():
            raise ValueError('Compatibility path requires separate review')
        aliases[alias] = str(target_alias).lstrip('/')
    ld_cache = str(canonical_regular('/etc/ld.so.cache')) if Path('/etc/ld.so.cache').exists() else None
    uid, gid = os.geteuid(), os.getegid()
    metadata = job / '.sandbox'
    metadata.mkdir(mode=0o700)  # exclusive: no reusing an earlier prepared job
    node_inside = str(Path('/tools') / node.relative_to(tools))
    rea_inside = str(Path('/tools') / rea.relative_to(tools))
    extra_env = {'REA_LOG_LEVEL': 'silent'}
    if command[0] in ('inspect', 'function'):
        ghidra = tools / 'ghidra_12.1.4_PUBLIC'
        jdk = tools / 'jdk-21.0.12.1+1'
        if not ghidra.is_dir() or not jdk.is_dir() or ghidra.is_symlink() or jdk.is_symlink():
            raise ValueError('Reviewed Ghidra/JDK prerequisites absent')
        extra_env.update({'GHIDRA_INSTALL_DIR': '/tools/ghidra_12.1.4_PUBLIC',
                          'JAVA_HOME': '/tools/jdk-21.0.12.1+1',
                          'GHIDRA_HEADLESS_MAXMEM': '2G'})
    baseline = {'schema': 1, 'uid': uid, 'gid': gid,
        'namespaces': {name: os.readlink(f'/proc/self/ns/{name}') for name in NAMESPACES},
        'mount_aliases': aliases, 'expected_uid_map': [[uid, 0, 1]], 'expected_gid_map': [[gid, 0, 1]],
        'mapping_model': 'bubblewrap-0.13.1 --dev: outer caller->0, inner requested-id->outer-0; not host root',
        'node_sha256': stamp(node)['sha256'], 'probe_node_sha256': stamp(probes['node_probe.mjs'])['sha256'],
        'node_inside': node_inside, 'expected_stdout_regular': True,
        'analysis_mode': True, 'extra_environment': extra_env}
    baseline_path = metadata / 'baseline.json'
    write_new_json(baseline_path, baseline)
    request = {'schema': 1, 'kind': 'five-lane-static-rea-only', 'command': command,
               'node_inside': node_inside, 'rea_inside': rea_inside,
               'node_sha256': stamp(node)['sha256'], 'rea_sha256': stamp(rea)['sha256'],
               'target_execution': False, 'network': False}
    request_path = metadata / 'request.json'
    write_new_json(request_path, request)
    argv = build_argv(bwrap=str(bwrap), node_binary=str(node), tools_root=str(tools), out_dir=str(work),
                      baseline=str(baseline_path), probe_python=str(probes['sandbox_probe.py']),
                      probe_node=str(probes['node_probe.mjs']), uid=uid, gid=gid,
                      system_aliases=aliases, ld_cache=ld_cache)
    at = argv.index('--remount-ro')
    additions = ['--ro-bind', str(source), '/input',
                 '--ro-bind', str(probes['analysis_guard.py']), '/opt/rea-check/analysis-guard.py',
                 '--ro-bind', str(probes['sandbox_plan.py']), '/opt/rea-check/sandbox-plan.py',
                 '--ro-bind', str(request_path), '/opt/rea-check/request.json']
    for key, value in sorted(extra_env.items()):
        additions += ['--setenv', key, value]
    argv[at:at] = additions
    if argv[-3:] != ['/usr/bin/python3', '-I', '/opt/rea-check/probe.py']:
        raise ValueError('Shared preflight entrypoint changed')
    argv[-3:] = ['/usr/bin/python3', '-I', '/opt/rea-check/analysis-guard.py']
    write_new_json(metadata / 'prepared.json', {'argv': argv,
        'sources': [stamp(p) for p in [node, rea, bwrap, *probes.values()]],
        'rea_executed_during_preparation': False})
    return argv
