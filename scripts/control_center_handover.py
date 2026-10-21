#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""One approval, encrypted backup then helper migration. Plan is offline only.

No automatic rollback, GUI/package launch, download or publication. The working
key stays external; the AppImage does not ship or call maintainer key custody.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'tools/control_center'))
import backup_release_key as backup
import migrate_control_center_helper as migration
from app_packages import bounded_file
from artifacts import BackendError


def prepare(bundle,image,key,destination):
    spec,review=migration.prepare(bundle)
    image=Path(image).absolute()
    if image!=image.resolve() or image.is_symlink() or not image.is_file():
        raise BackendError('handover_image_invalid')
    with image.open('rb') as stream:
        if stream.read(11)!=b'\x7fELF\x02\x01\x01\x00AI\x02':raise BackendError('handover_image_invalid')
    # Check the actual staged AppDir against its independently recorded inputs,
    # not just the helper subset. No AppRun or host/status probing here.
    appdir=Path(bundle).parents[2]
    if any(p.is_symlink() and (p!=appdir/'.DirIcon' or p.readlink()!=Path('gamesir-control-center.svg'))
           for p in appdir.rglob('*')):raise BackendError('handover_appdir_changed')
    manifest=json.loads(bounded_file(appdir/'BUILD_INPUTS.json',1048576))
    actual={p.relative_to(appdir).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in appdir.rglob('*') if p.is_file() and not p.is_symlink() and p!=appdir/'BUILD_INPUTS.json'}
    if manifest['files']!=actual:raise BackendError('handover_appdir_changed')
    key=backup.external(key);destination=backup.external(destination)
    if key==destination:raise BackendError('handover_key_is_not_backup_destination')
    plan={'schema':1,'operation':'encrypted-backup-then-helper-only-migration',
        'migration':review,'image':{'path':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest()},
        'backup':{'private_key':str(key),'destination':str(destination),'key_id':review['key_id'],
            'format':'PKCS8/PBES2 AES-256-CBC','pbkdf2_hmac_sha256_iterations':backup.ITERATIONS},
        'executed':False,'install_driver_packages':False,'publish':False,'launch_appimage':False}
    return spec,plan


def load_approved(path,digest):
    data=bounded_file(Path(path),262144)
    if hashlib.sha256(data).hexdigest()!=digest:raise BackendError('handover_plan_changed')
    old=json.loads(data)
    spec,review=prepare(old['migration']['bundle'],old['image']['path'],
        old['backup']['private_key'],old['backup']['destination'])
    if old!=review:raise BackendError('handover_source_or_image_changed')
    return spec,review


def run(spec,plan,*,password=None,backup_action=backup.backup,migrate_action=migration.execute):
    if password is None:password=backup.interactive_password()
    b=plan['backup']
    result=backup_action(b['private_key'],b['destination'],password,b['key_id'])
    if result.get('encrypted_backup_verified') is not True:
        raise BackendError('handover_backup_unconfirmed')
    # Only a verified, persisted encrypted backup can open the root phase.
    print('Verschluesselte Sicherung verifiziert. Jetzt einmalige Helferumstellung.',flush=True)
    outcome=migrate_action(spec)
    return {'backup':result,'helper':asdict(outcome),'driver_changed':False,
            'published':False,'off_device_copy_still_required':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle');p.add_argument('--image');p.add_argument('--private-key')
    p.add_argument('--backup-destination');p.add_argument('--output')
    p.add_argument('--plan-file');p.add_argument('--approved-sha256')
    modes=p.add_mutually_exclusive_group()
    modes.add_argument('--apply',action='store_true');modes.add_argument('--rollback',action='store_true')
    a=p.parse_args()
    try:
        if os.getuid()==0 or os.geteuid()!=os.getuid():raise BackendError('desktop_user_required')
        if not a.apply and not a.rollback:
            if not all((a.bundle,a.image,a.private_key,a.backup_destination,a.output)):
                raise BackendError('handover_plan_arguments_required')
            spec,review=prepare(a.bundle,a.image,a.private_key,a.backup_destination)
            data=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode()
            from package_control_center import safe_output
            output=safe_output(a.output)
            with output.open('xb') as stream:stream.write(data)
            print(json.dumps({'approval_sha256':hashlib.sha256(data).hexdigest(),
                'privileged_commands':len(review['migration']['privileged_commands']),
                'executed':False}));return 0
        if not a.plan_file or not a.approved_sha256:raise BackendError('exact_approved_plan_required')
        spec,review=load_approved(a.plan_file,a.approved_sha256)
        if a.rollback:
            outcome=migration.execute(spec,rollback=True);print(json.dumps(asdict(outcome)))
            return 0 if outcome.state=='verified_rollback' else 2
        result=run(spec,review);print(json.dumps(result))
        return 0 if result['helper']['state']=='verified_migration' else 2
    except (Exception,KeyboardInterrupt):
        print('Stopped. No retry, automatic rollback or cleanup. Preserve any backup/partial helper.',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
