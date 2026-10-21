#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Prepare a pinned one-time maintainer migration; application is opt-in.

Plan mode reads staged bytes only. Never import this as an automatic GUI repair.
Apply/rollback require the exact separately approved plan SHA256 and fresh gates.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, str(ROOT/'tools/control_center'))
from artifacts import BackendError
from app_packages import load_bundle, bounded_file
from helper_setup import load_payload
from helper_migration import MigrationSpec, MigrationSession, CANDIDATE, BACKUP, HOLD, FAILED


def code_pins():
    files = [Path(__file__), ROOT/'scripts/backup_release_key.py',
             ROOT/'scripts/control_center_handover.py',
             ROOT/'packaging/control-center/migration-from-first-run.json',
             ROOT/'packaging/control-center/release-signing-policy.json']
    files += sorted((ROOT/'tools/control_center').rglob('*.py'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(bounded_file(p,262144)).hexdigest() for p in files}


def prepare(directory):
    directory = Path(directory).absolute()
    if directory != directory.resolve(): raise BackendError('redirected_migration_bundle')
    bundle = load_bundle(directory/'reviewed-packages')
    payload = load_payload(directory/'helper-payload',bundle)
    old = json.loads((ROOT/'packaging/control-center/migration-from-first-run.json').read_bytes())
    if set(old) != {'schema','id','files'} or old['schema'] != 1 or old['id'] != 'first-run-v1-to-signed-v1':
        raise BackendError('invalid_migration_review')
    spec = MigrationSpec(tuple(sorted(old['files'].items())),payload,bundle.distribution);spec.validate()
    policy = json.loads((ROOT/'packaging/control-center/release-signing-policy.json').read_bytes())
    if bundle.trust.release_policy != policy: raise BackendError('migration_public_policy_mismatch')
    review = {'schema':1,'operation':'helper-only-first-run-v1-to-signed-v1',
        'bundle':str(directory),'distribution':spec.distribution,'source_pins':code_pins(),'old':dict(spec.old),
        'new':{p:h for p,d,h in payload.rows},'key_id':policy['keys'][0]['id'],
        'paths':{'candidate':CANDIDATE,'backup':BACKUP,'held_policy':HOLD,'retained_new':FAILED},
        'privileged_commands':[list(argv) for argv,source in spec.commands()],
        'privileged_package_operations':False,'activation':False,'executed':False}
    return spec,review


def execute(spec, *, rollback=False):
    from backend import Request
    from package_preflight import PlanningEvidence
    # Snapshot only: no kernel-build prerequisite, ALPM handle or transaction.
    reader=PlanningEvidence(Request('remove',('steam',)))
    host=reader.collect()
    if host.distribution!=spec.distribution:raise BackendError('migration_target_mismatch')
    initial=host.fingerprint()
    def fresh():
        if reader.collect().fingerprint()!=initial:raise BackendError('host_changed')
    return MigrationSession(spec,fresh_check=fresh,rollback=rollback).run()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',help='reviewed AppDir usr/share/gamesir-control-center')
    parser.add_argument('--output',help='new local approval plan, never overwrite')
    parser.add_argument('--plan-file')
    parser.add_argument('--approved-sha256')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--apply',action='store_true')
    group.add_argument('--rollback',action='store_true')
    args=parser.parse_args()
    try:
        if os.geteuid()==0 or os.getuid()!=os.geteuid():raise BackendError('desktop_user_required')
        if not args.apply and not args.rollback:
            if not args.bundle or not args.output:raise BackendError('migration_plan_arguments_required')
            spec,review=prepare(args.bundle)
            data=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode()
            output=Path(args.output).absolute()
            from package_control_center import safe_output
            safe_output(output)  # system/user-profile/symlink/overwrite guards
            with output.open('xb') as f:f.write(data)
            print(json.dumps({'plan_sha256':hashlib.sha256(data).hexdigest(),
                'privileged_commands':len(review['privileged_commands']),'executed':False}));return 0
        if not args.plan_file or not args.approved_sha256:raise BackendError('exact_approved_plan_required')
        data=bounded_file(Path(args.plan_file),262144)
        if hashlib.sha256(data).hexdigest()!=args.approved_sha256:raise BackendError('migration_plan_changed')
        old=json.loads(data);spec,review=prepare(old['bundle'])
        if review!=old:raise BackendError('migration_source_or_payload_changed')
        result=execute(spec,rollback=args.rollback)
        print(json.dumps(asdict(result)))
        return 0 if result.state.startswith('verified_') else 2
    except Exception:
        print('Migration stopped; no retry/automatic cleanup or package operation.',file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
