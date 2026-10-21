#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Explicit offline publisher tool; existing Ed25519 key only, no key generation.

No network, installation, root execution or publication. Private keys must be
external to this repository, regular, owned by the caller and mode 0600.
"""
import argparse
import base64
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/control_center'))
from artifacts import BackendError
from package_catalog import DOMAIN,parse_catalog,verify_signed_catalog
from package_wire import encode


def sign(payload,private_key,root_review,*,now=None,previous=None):
    if os.geteuid()==0:raise BackendError('desktop_user_required')
    root=parse_catalog(root_review)
    from package_host import protected
    protected('/usr/bin/openssl')
    if type(payload) is not bytes or not 0<len(payload)<=131072:
        raise BackendError('release_catalog_limit')
    path=Path(private_key).absolute()
    if path!=path.resolve() or path==ROOT or ROOT in path.parents:
        raise BackendError('release_private_key_location')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid()
                or stat.S_IMODE(info.st_mode)!=0o600 or info.st_nlink!=1 or not 0<info.st_size<=4096):
            raise BackendError('release_private_key_permissions')
        key=stream.read(4097)
    fds=[]
    try:
        for name,data in (('key',key),('payload',DOMAIN+payload)):
            fd=os.memfd_create('gamesir-sign-'+name,os.MFD_CLOEXEC);fds.append(fd)
            with os.fdopen(os.dup(fd),'wb') as stream:stream.write(data)
            os.lseek(fd,0,os.SEEK_SET)
        keyfile,datafile=('/proc/self/fd/'+str(fd) for fd in fds)
        form='DER' if key.startswith(b'\x30') else 'PEM'
        env={'PATH':'/usr/bin:/bin','LC_ALL':'C','OPENSSL_CONF':'/dev/null',
             'OPENSSL_MODULES':'/nonexistent','OPENSSL_ENGINES':'/nonexistent'}
        def openssl(args):
            result=subprocess.run(('/usr/bin/openssl',*args),pass_fds=tuple(fds),stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,timeout=5,check=False)
            if result.returncode or len(result.stdout)>4096:raise BackendError('release_signing_failed')
            return result.stdout
        public=openssl(('pkey','-in',keyfile,'-inform',form,'-passin','pass:', '-pubout','-outform','DER'))
        if len(public)!=44 or public[:12]!=bytes.fromhex('302a300506032b6570032100'):
            raise BackendError('release_signing_key_type')
        signature=openssl(('pkeyutl','-sign','-keyform',form,'-inkey',keyfile,'-passin','pass:',
                           '-rawin','-in',datafile))
        if len(signature)!=64:raise BackendError('release_signing_failed')
        envelope=encode(dict(schema=1,algorithm='ed25519',key_id=hashlib.sha256(public[12:]).hexdigest(),
            payload=base64.b64encode(payload).decode(),signature=signature.hex()))
        # Refuse an unknown key, malformed/expired payload or unreviewed origins
        # before producing any output. This does not publish or grant root trust.
        prior=(verify_signed_catalog(previous,root,now=now,allow_expired=True)
               if previous is not None else None)
        verify_signed_catalog(envelope,root,now=now,previous=prior)
        return envelope
    except (OSError,subprocess.TimeoutExpired):
        raise BackendError('release_signing_failed') from None
    finally:
        for fd in fds:os.close(fd)


def bounded(path,limit):
    with Path(path).open('rb') as stream:data=stream.read(limit+1)
    if not 0<len(data)<=limit:raise BackendError('release_catalog_limit')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payload',required=True)
    parser.add_argument('--private-key',required=True)
    parser.add_argument('--root-review',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--previous',help='previous signed catalog for monotonic publisher-side checks')
    args=parser.parse_args()
    try:
        result=sign(bounded(args.payload,131072),args.private_key,bounded(args.root_review,65536),
                    previous=bounded(args.previous,196608) if args.previous else None)
        target=Path(args.output).absolute()
        if target!=target.resolve() or any(Path(p)==target or Path(p) in target.parents
                for p in ('/usr','/etc','/var','/boot','/dev','/proc','/sys','/run')):
            raise BackendError('release_output_location')
        with target.open('xb') as stream:stream.write(result+b'\n')
        print('Signed catalog written; no key generated or release uploaded.')
        return 0
    except (BackendError,OSError,ValueError) as error:
        print(error.code if isinstance(error,BackendError) else 'release_signing_failed',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
