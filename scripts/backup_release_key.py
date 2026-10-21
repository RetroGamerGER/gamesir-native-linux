#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Maintainer-only encrypted key backup. No key generation, network or root.

Secrets are obtained from the controlling terminal, never arguments/stdin.
Only encrypted PKCS8 bytes can be written; recovery verification stays in RAM.
"""
import argparse
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
ENV = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'OPENSSL_CONF': '/dev/null',
       'OPENSSL_MODULES': '/nonexistent', 'OPENSSL_ENGINES': '/nonexistent'}
ITERATIONS = 600000
SEALS = fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL
SPKI = bytes.fromhex('302a300506032b6570032100')


class BackupError(Exception):
    pass


def tool():
    for p in (Path('/usr'), Path('/usr/bin'), Path('/usr/bin/openssl')):
        s = p.lstat()
        if s.st_uid != 0 or s.st_mode & 0o022 or stat.S_ISLNK(s.st_mode):
            raise BackupError('unprotected_openssl')


def external(path):
    p = Path(path).absolute()
    if p != p.resolve() or p == ROOT or ROOT in p.parents or any(
            os.path.lexists(parent / '.git') for parent in p.parents):
        raise BackupError('external_nonrepository_path_required')
    if any(p == Path(q) or Path(q) in p.parents
           for q in ('/usr', '/etc', '/var', '/boot', '/dev', '/proc', '/sys', '/run')):
        raise BackupError('external_nonrepository_path_required')
    return p


def secret_file(path):
    p = external(path)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        s = os.fstat(stream.fileno())
        if (not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_nlink != 1
                or stat.S_IMODE(s.st_mode) != 0o600 or not 0 < s.st_size <= 4096):
            raise BackupError('private_key_permissions')
        return stream.read(4097)


def phrase(value):
    if (type(value) is not str or len(value) < 16 or len(value.encode('utf-8')) > 1024
            or any(c in value for c in '\x00\r\n')):
        raise BackupError('passphrase_minimum_16_characters_no_controls')
    return value.encode('utf-8') + b'\n'


def memfd(data):
    fd = os.memfd_create('gamesir-key-backup', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        with os.fdopen(os.dup(fd), 'wb') as stream: stream.write(data)
        os.lseek(fd, 0, os.SEEK_SET)
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, SEALS)
        return fd
    except BaseException:
        os.close(fd)
        raise


def openssl(args, fds, *, output=subprocess.PIPE):
    r = subprocess.run(('/usr/bin/openssl', *args), pass_fds=tuple(fds),
        stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.DEVNULL,
        env=ENV, timeout=30, check=False)
    if r.returncode or r.stdout is not None and len(r.stdout) > 16384:
        raise BackupError('backup_crypto_failed')
    return r.stdout


def identity(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    public = openssl(('pkey', '-inform', 'DER', '-in', '/proc/self/fd/' + str(fd),
                      '-passin', 'pass:', '-pubout', '-outform', 'DER'), (fd,))
    if len(public) != 44 or not public.startswith(SPKI):
        raise BackupError('ed25519_key_required')
    return hashlib.sha256(public[12:]).hexdigest()


def verify_encrypted(encrypted, password, expected):
    """No plaintext file: decrypted key goes directly into anonymous memory."""
    fds = []
    try:
        enc = memfd(encrypted); fds.append(enc)
        pw = memfd(phrase(password)); fds.append(pw)
        recovered = os.memfd_create('gamesir-key-recovery-check', os.MFD_CLOEXEC)
        fds.append(recovered)
        openssl(('pkcs8', '-inform', 'DER', '-in', '/proc/self/fd/' + str(enc),
                 '-passin', 'fd:' + str(pw), '-outform', 'DER'), (enc, pw), output=recovered)
        if identity(recovered) != expected:
            raise BackupError('backup_public_key_mismatch')
    finally:
        for fd in fds: os.close(fd)


def encrypt(private, password, expected):
    fds = []
    try:
        key = memfd(private); fds.append(key)
        if identity(key) != expected: raise BackupError('backup_public_key_mismatch')
        os.lseek(key, 0, os.SEEK_SET)
        pw = memfd(phrase(password)); fds.append(pw)
        encrypted = openssl(('pkcs8', '-topk8', '-inform', 'DER', '-in',
            '/proc/self/fd/' + str(key), '-passin', 'pass:', '-outform', 'DER',
            '-v2', 'aes-256-cbc', '-v2prf', 'hmacWithSHA256', '-iter', str(ITERATIONS),
            '-passout', 'fd:' + str(pw)), (key, pw))
        verify_encrypted(encrypted, password, expected)
        return encrypted
    finally:
        for fd in fds: os.close(fd)


def backup(key, destination, password, expected):
    if os.getuid() == 0 or os.geteuid() != os.getuid(): raise BackupError('desktop_user_required')
    tool()
    p = external(destination)
    if os.path.lexists(p): raise BackupError('backup_destination_exists')
    # Open each parent without following symlinks, then keep that directory FD
    # for exclusive creation and postcheck even if its pathname changes.
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for component in p.parent.parts[1:]:
            nextfd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                             dir_fd=parent)
            os.close(parent); parent = nextfd
            s = os.fstat(parent)
            if s.st_uid not in (0, os.getuid()) or s.st_mode & 0o022 and not (
                    s.st_uid == 0 and s.st_mode & stat.S_ISVTX):
                raise BackupError('unsafe_backup_parent')
        encrypted = encrypt(secret_file(key), password, expected)
        fd = os.open(p.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encrypted); stream.flush(); os.fsync(stream.fileno())
        os.fsync(parent)
        fd = os.open(p.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            s = os.fstat(stream.fileno())
            if (not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or s.st_nlink != 1
                    or stat.S_IMODE(s.st_mode) != 0o600): raise BackupError('unsafe_backup_output')
            data = stream.read(16385)
        if data != encrypted: raise BackupError('backup_postcheck_failed')
        verify_encrypted(data, password, expected)
        return {'encrypted_backup_verified': True, 'key_id': expected,
                'cipher': 'PKCS8/PBES2 AES-256-CBC', 'kdf': 'PBKDF2-HMAC-SHA256',
                'iterations': ITERATIONS, 'sha256': hashlib.sha256(data).hexdigest(),
                'private_key_copied_in_plaintext': False, 'off_device_copy_confirmed': False}
    finally:
        os.close(parent)


def interactive_password():
    # Failure to disable terminal echo must stop, never fall back to stdin.
    fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY | os.O_CLOEXEC)
    with os.fdopen(fd, 'w', buffering=1) as tty:
        if not os.isatty(tty.fileno()): raise BackupError('controlling_terminal_required')
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            first = getpass.getpass('Neue Sicherungspassphrase (mindestens 16 Zeichen): ', stream=tty)
            second = getpass.getpass('Sicherungspassphrase wiederholen: ', stream=tty)
    if first != second: raise BackupError('passphrases_differ')
    phrase(first)
    return first


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-key', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--public-policy', default=str(ROOT/'packaging/control-center/release-signing-policy.json'))
    parser.add_argument('--create', action='store_true', help='explicit approval gate; otherwise show plan only')
    args = parser.parse_args()
    try:
        policy = json.loads(Path(args.public_policy).read_bytes())
        if len(policy['keys']) != 1: raise BackupError('single_reviewed_key_required')
        expected = policy['keys'][0]['id']
        if hashlib.sha256(bytes.fromhex(policy['keys'][0]['public_key'])).hexdigest() != expected:
            raise BackupError('invalid_public_policy')
        external(args.private_key); external(args.destination)
        if not args.create:
            print(json.dumps({'operation': 'encrypted_backup_only', 'key_id': expected,
                'destination': str(Path(args.destination).absolute()), 'created': False,
                'password_source': 'controlling terminal, twice; never chat/argv',
                'iterations': ITERATIONS})); return 0
        print(json.dumps(backup(args.private_key, args.destination, interactive_password(), expected)))
        return 0
    except (BackupError, OSError, ValueError, KeyError, subprocess.SubprocessError,
            getpass.GetPassWarning, EOFError, KeyboardInterrupt):
        print('Backup stopped; no retry. Existing/partial files are preserved.', file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())
