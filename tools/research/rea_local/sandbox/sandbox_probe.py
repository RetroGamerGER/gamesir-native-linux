# SPDX-License-Identifier: GPL-2.0-only
"""Own isolation probe. Never imports REA or any target program."""
from pathlib import Path
import hashlib
import errno
import json
import os
import socket
import stat
import subprocess
import sys
import traceback

NAMESPACES = ('mnt', 'pid', 'user', 'net', 'ipc', 'uts', 'cgroup')
CAPS = ('CapInh', 'CapPrm', 'CapEff', 'CapBnd', 'CapAmb')
REPORT = {'passed': False, 'firmware_mounted': False, 'rea_executed': False,
          'device_nodes_opened': False, 'checks': {}}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_new(path: Path, value: object) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def mounts() -> list[dict]:
    entries = []
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        a, b = line.split(' - ', 1)
        left, right = a.split(), b.split()
        point = left[4]
        for encoded, decoded in (('\\040', ' '), ('\\011', '\t'), ('\\012', '\n'), ('\\134', '\\')):
            point = point.replace(encoded, decoded)
        entries.append({'point': point, 'options': left[5].split(','),
                        'filesystem': right[0]})
    return entries


def probe() -> None:
    baseline = json.loads(Path('/opt/rea-check/baseline.json').read_text())
    analysis_mode = baseline.get('analysis_mode') is True
    if analysis_mode:
        # Generic copied inputs may include firmware; this probe does not
        # classify their contents and must not claim that none is mounted.
        REPORT['firmware_mounted'] = None
        REPORT['analysis_input_mounted'] = True
    status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    uid_map = [tuple(map(int, line.split())) for line in Path('/proc/self/uid_map').read_text().splitlines()]
    gid_map = [tuple(map(int, line.split())) for line in Path('/proc/self/gid_map').read_text().splitlines()]
    # Record actual values before any assertion; failures must retain diagnosis.
    REPORT['checks']['identity'] = {'uid': os.getuid(), 'euid': os.geteuid(),
        'gid': os.getgid(), 'egid': os.getegid(), 'uid_map': uid_map, 'gid_map': gid_map,
        'capability_sets': {key: status.get(key, '').strip() for key in CAPS},
        'no_new_privs_observed': status.get('NoNewPrivs', '').strip(),
        'mapping_model': baseline.get('mapping_model'),
        'expected_uid_map': baseline.get('expected_uid_map'),
        'expected_gid_map': baseline.get('expected_gid_map')}
    require(os.getuid() == os.geteuid() == baseline['uid'] != 0, 'Wrong/non-root UID guard')
    require(os.getgid() == os.getegid() == baseline['gid'], 'Wrong GID guard')
    for key in CAPS:
        require(int(status[key].strip(), 16) == 0, f'Capability set is nonzero: {key}')
    require(status['NoNewPrivs'].strip() == '1', 'NoNewPrivs must be 1')
    # --dev requires devpts. This reviewed Bubblewrap creates an outer map
    # caller->namespace0 for mounting it, then inner requestedUID->outer0.
    # The second column is the immediate parent user namespace, not host UID0.
    require(uid_map == [tuple(row) for row in baseline['expected_uid_map']], 'Unexpected UID mapping')
    require(gid_map == [tuple(row) for row in baseline['expected_gid_map']], 'Unexpected GID mapping')
    REPORT['checks']['identity'].update({'five_capability_sets_zero': True, 'no_new_privs': 1})
    current_ns = {name: os.readlink(f'/proc/self/ns/{name}') for name in NAMESPACES}
    require(all(current_ns[name] != baseline['namespaces'][name] for name in NAMESPACES),
            'At least one requested namespace is shared with host')
    REPORT['checks']['namespaces'] = current_ns

    # No ambient host sockets or inherited handles beyond the three stdio FDs.
    with os.scandir('/proc/self/fd') as entries:
        fd_names = [entry.name for entry in entries]
    inherited = []
    for name in fd_names:
        try:
            st = os.fstat(int(name))
        except OSError:
            continue  # closed scandir FD, not an admitted retained descriptor
        inherited.append(int(name))
        require(int(name) <= 2, 'Unexpected inherited descriptor')
        if int(name) in (1, 2):
            require(stat.S_ISREG(st.st_mode), 'stdout/stderr must be private regular files')
    require(set(inherited) == {0, 1, 2}, 'Missing stdio descriptor')
    require(os.readlink('/proc/self/fd/0') == '/dev/null', 'stdin must be the reviewed null FD')
    REPORT['checks']['inherited_descriptors'] = sorted(inherited)

    expected_env = {'HOME', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME', 'TMPDIR', 'PATH', 'LC_ALL', 'PWD'}
    extra_env = baseline.get('extra_environment', {})
    allowed_extra = {'REA_LOG_LEVEL': 'silent',
                     'GHIDRA_INSTALL_DIR': '/tools/ghidra_12.1.4_PUBLIC',
                     'JAVA_HOME': '/tools/jdk-21.0.12.1+1',
                     'GHIDRA_HEADLESS_MAXMEM': '2G'}
    require(isinstance(extra_env, dict), 'Invalid extra environment declaration')
    require((analysis_mode and extra_env in (
        {'REA_LOG_LEVEL': 'silent'}, allowed_extra)) or
        (not analysis_mode and extra_env == {}), 'Unreviewed analysis environment')
    for key, value in extra_env.items():
        require(os.environ.get(key) == value, 'Wrong static-analysis environment value')
    expected_env.update(extra_env)
    require(set(os.environ) == expected_env, 'Unexpected ambient environment')
    require(os.environ['HOME'] == '/home/rea' and os.environ['TMPDIR'] == '/tmp', 'Wrong private home/temp')
    require(os.getcwd() == '/out' and os.environ['PWD'] == '/out', 'Wrong working directory/PWD')
    hidden = ['/run', '/sys', '/dev/bus/usb']
    if not analysis_mode:
        hidden.append('/input')
    for p in hidden:
        require(not os.path.lexists(p), f'Unexpected host/hardware surface: {p}')
    require(sorted(x.name for x in Path('/home').iterdir()) == ['rea'], 'Host home is exposed')
    require(not list(Path('/dev').glob('usbmon*')) and not list(Path('/dev').glob('hidraw*')),
            'Unexpected USB/HID node')
    for alias, target in baseline['mount_aliases'].items():
        require(Path(alias).is_symlink() and os.readlink(alias) == target, 'Unexpected system alias')
        require(Path(alias).resolve().is_relative_to('/usr'), 'Compatibility alias escapes /usr')
    for root, directories, files in os.walk('/dev', followlinks=False):
        for name in [*directories, *files]:
            p = Path(root) / name
            st = p.lstat()
            if stat.S_ISCHR(st.st_mode):
                pair = (os.major(st.st_rdev), os.minor(st.st_rdev))
                require(pair in {(1, 3), (1, 5), (1, 7), (1, 8), (1, 9), (5, 0), (5, 2)},
                        'Unexpected character device in private /dev')
            elif stat.S_ISBLK(st.st_mode) or stat.S_ISSOCK(st.st_mode) or stat.S_ISFIFO(st.st_mode):
                raise RuntimeError('Unexpected block/socket/FIFO device surface')
    REPORT['checks']['hidden_host_and_hardware_surfaces'] = True

    entries = mounts()
    lookup = {entry['point']: entry for entry in entries}
    readonly_points = ['/', '/usr', '/tools', '/opt/rea-check/probe.py',
                       '/opt/rea-check/node-probe.mjs', '/opt/rea-check/baseline.json']
    if analysis_mode:
        readonly_points += ['/input', '/opt/rea-check/analysis-guard.py',
                            '/opt/rea-check/sandbox-plan.py', '/opt/rea-check/request.json']
    for point in readonly_points:
        require(point in lookup and 'ro' in lookup[point]['options'], f'Read-only mount missing: {point}')
    require('/out' in lookup and 'rw' in lookup['/out']['options'], 'Private output is not writable')
    for entry in entries:
        if 'rw' not in entry['options']:
            continue
        p = entry['point']
        if p in ('/out', '/proc', '/tmp', '/home/rea') or p == '/dev' or p.startswith('/dev/'):
            continue
        raise RuntimeError(f'Unexpected writable mount: {p}')
    REPORT['checks']['mounts'] = entries

    if analysis_mode:
        copied_entries = 0
        for root, directories, files in os.walk('/input', followlinks=False):
            for p in [Path(root), *(Path(root) / name for name in files)]:
                st = p.lstat()
                copied_entries += 1
                require(copied_entries <= 8193 and st.st_uid == baseline['uid'],
                        'Copied input owner or inspection limit mismatch')
                require((stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o500) or
                        (stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o400),
                        'Copied input is not inert/private')
            for name in directories:
                require(not (Path(root) / name).is_symlink(), 'Copied input contains a directory link')
        REPORT['checks']['copied_input_metadata_entries'] = copied_entries

    # The reviewed tools tree must not provide a host socket or escape link.
    count = 0
    for root, directories, files in os.walk('/tools', followlinks=False):
        for name in [*directories, *files]:
            count += 1
            require(count <= 100000, 'Tools metadata inspection limit exceeded')
            p = Path(root) / name
            st = p.lstat()
            if stat.S_ISLNK(st.st_mode):
                resolved = p.resolve(strict=True)
                require(resolved.is_relative_to('/tools') or resolved.is_relative_to('/usr'), 'Tools symlink escapes admitted trees')
            else:
                require(stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode), 'Special file in tools tree')
    REPORT['checks']['tools_tree_metadata_entries'] = count

    interfaces = socket.if_nameindex()
    require([name for index, name in interfaces] == ['lo'], 'Non-loopback network interface is present')
    ipv4 = [line for line in Path('/proc/net/route').read_text().splitlines()[1:] if line.strip()]
    require(not ipv4, 'IPv4 routing table is not empty')
    ipv6 = Path('/proc/net/ipv6_route')
    if ipv6.exists():
        require(all(line.split()[-1] == 'lo' for line in ipv6.read_text().splitlines() if line.strip()),
                'Unexpected IPv6 route interface')
    REPORT['checks']['network'] = {'interfaces': interfaces, 'ipv4_route_entries': 0,
                                    'host_namespace_reused': False}

    # Fail closed if persistent writes would escape the single new output mount.
    write_denied = ['/', '/usr', '/tools', '/etc', '/opt/rea-check']
    if analysis_mode:
        write_denied.append('/input')
    for parent in write_denied:
        if not Path(parent).exists():
            continue
        candidate = Path(parent) / '.rea-synthetic-forbidden-write'
        require(not os.path.lexists(candidate), 'Unexpected pre-existing write-test path')
        try:
            fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except OSError as error:
            require(error.errno in (errno.EROFS, errno.EACCES, errno.EPERM),
                    'Outside-output write failed for an unexpected reason')
            continue
        else:
            os.close(fd)
            raise RuntimeError(f'Unexpected write outside output: {parent}')
    write_new(Path('/out/python-write-probe.json'), {'synthetic_only': True, 'passed': True})
    node = Path(baseline['node_inside'])
    require(hashlib.sha256(node.read_bytes()).hexdigest() == baseline['node_sha256'], 'Wrong Node digest')
    node_script = Path('/opt/rea-check/node-probe.mjs')
    require(hashlib.sha256(node_script.read_bytes()).hexdigest() == baseline['probe_node_sha256'], 'Changed Node probe')
    version = subprocess.run([str(node), '--version'], stdin=subprocess.DEVNULL, capture_output=True,
                             text=True, close_fds=True, pass_fds=(), timeout=5, check=True)
    require(len(version.stdout) < 100 and not version.stderr, 'Unexpected Node version output')
    check = subprocess.run([str(node), str(node_script)], stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, close_fds=True, pass_fds=(), timeout=5, check=True)
    require(len(check.stdout) < 65536 and len(check.stderr) < 65536, 'Oversized own probe output')
    node_result = json.loads(check.stdout)
    require(node_result.get('passed') is True and node_result.get('synthetic_only') is True,
            'Node synthetic refusal did not pass')
    require(version.stdout.strip() == node_result['node_version'], 'Node version inconsistency')
    REPORT['checks']['node'] = node_result
    REPORT['checks']['persistent_write_scope'] = '/out only; /tmp and /home/rea are ephemeral private tmpfs'
    REPORT['passed'] = True


try:
    probe()
except Exception as error:
    REPORT['failure'] = f'{type(error).__name__}: {error}'
    REPORT['traceback'] = traceback.format_exc()
    try:
        write_new(Path('/out/result.json'), REPORT)
    except Exception:
        pass
    print(REPORT['failure'], file=sys.stderr)
    raise SystemExit(1)
else:
    write_new(Path('/out/result.json'), REPORT)
    print(json.dumps({'passed': True, 'rea_executed': False,
                      'firmware_mounted': REPORT['firmware_mounted']}))
