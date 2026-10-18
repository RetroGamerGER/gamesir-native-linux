# SPDX-License-Identifier: GPL-2.0-only
"""Run the full own isolation probe, then exec only the reviewed static REA CLI."""
from pathlib import Path
import hashlib
import json
import os
import runpy
import subprocess
import sys


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    request = json.loads(Path('/opt/rea-check/request.json').read_text())
    baseline = json.loads(Path('/opt/rea-check/baseline.json').read_text())
    if request.get('kind') != 'five-lane-static-rea-only' or baseline.get('analysis_mode') is not True:
        fail('Invalid static-analysis preflight scope')
    # Own trusted helper only; its module body does not start tools or targets.
    helpers = runpy.run_path('/opt/rea-check/sandbox-plan.py', run_name='rea_static_guard_helpers')
    command = helpers['validate_analysis_command'](request['command'])
    out = Path('/out')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    stdout_fd = os.open(out / 'isolation.stdout.log', flags, 0o600)
    stderr_fd = os.open(out / 'isolation.stderr.log', flags, 0o600)
    try:
        # The child inherits only private stdio. No analysis target is opened here.
        checked = subprocess.run(['/usr/bin/python3', '-I', '/opt/rea-check/probe.py'],
            stdin=subprocess.DEVNULL, stdout=stdout_fd, stderr=stderr_fd,
            close_fds=True, pass_fds=(), shell=False, timeout=30, check=False)
    finally:
        os.close(stdout_fd)
        os.close(stderr_fd)
    if checked.returncode != 0:
        fail('Isolation preflight failed; REA was not started')
    receipt = json.loads((out / 'result.json').read_text())
    if receipt.get('passed') is not True or receipt.get('rea_executed') is not False:
        fail('Isolation preflight did not positively pass')
    node, rea = Path(request['node_inside']), Path(request['rea_inside'])
    if str(node) != baseline['node_inside'] or not node.is_relative_to('/tools') or not rea.is_relative_to('/tools'):
        fail('Unexpected tool entrypoint')
    for path, key in ((node, 'node_sha256'), (rea, 'rea_sha256')):
        if hashlib.sha256(path.read_bytes()).hexdigest() != request[key]:
            fail('Reviewed static tool bytes changed')
    # No shell, arbitrary flags, interpreter chosen by input, MCP or target exec.
    os.execve(node, [str(node), str(rea), *command], dict(os.environ))


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt):
        fail('Local static-analysis guard failed; no fallback or retry')
