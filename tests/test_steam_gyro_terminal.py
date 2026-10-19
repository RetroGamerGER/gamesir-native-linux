#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real PTY + timeout + tee, synthetic child; no Steam, sudo or controller I/O."""
import errno
import json
import os
from pathlib import Path
import pty
import select
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
OBSERVER = ROOT/'tools/sdl/steam_gyro_observe.py'
STUB = r'''
import importlib.util, os, select, sys, time
spec=importlib.util.spec_from_file_location('observer',sys.argv[1])
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
def forbidden(*args,**kwargs):
    raise AssertionError('Synthetic terminal test must not access a target')
m.find_steam=m.target_identity=m.process_identity=m.snapshot=forbidden
m.os.pread=forbidden
try:
    if sys.argv[2]=='legacy':
        m.emit('legacy_ready',foreground=os.tcgetpgrp(0)==os.getpgrp())
        print('TEST_READY',file=sys.stderr,flush=True)
        ready,_,_=select.select([sys.stdin],[],[],0.35)
        m.require(bool(ready) and sys.stdin.readline().strip().lower()=='go','No local GO; no memory open')
    elif sys.argv[2]=='wedged':
        print('TEST_READY',file=sys.stderr,flush=True)
        while True: time.sleep(0.1)
    else:
        m.wait_local_go(timeout_s=0.35)
    m.emit('synthetic_complete',process_memory_opened=False)
except m.Halt as error:
    m.emit('stopped',reason=str(error),process_memory_opened=False)
    sys.exit(2)
'''


class TerminalTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='gamesir-terminal-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.stub=self.root/'synthetic.py'
        self.stub.write_text(STUB)

    def run_pty(self, *, foreground=True, mode='corrected', answer=b'GO\n'):
        """Own controlling terminal; inject test text, never a real approval."""
        log=self.root/'events.jsonl'
        timeout=['/usr/bin/timeout']+(['--foreground'] if foreground else [])
        command=shlex.join(timeout+['--signal=TERM','--kill-after=0.1s','1.5s',
                                   sys.executable,'-I','-B',str(self.stub),str(OBSERVER),mode])
        # Same noninteractive shell/pipeline/redirection as the reviewed launch.
        command+=' | /usr/bin/tee '+shlex.quote(str(log))+' >/dev/null'
        pid,master=pty.fork()
        if pid==0:
            try:
                os.execv('/usr/bin/bash',['bash','-o','pipefail','-c',command])
            finally:
                os._exit(127)
        terminal=b''; sent=False; status=None; reaped=False
        try:
            deadline=time.monotonic()+4
            while time.monotonic()<deadline:
                if select.select([master],[],[],0.02)[0]:
                    try: data=os.read(master,8192)
                    except OSError as error:
                        if error.errno==errno.EIO: break
                        raise
                    if not data: break
                    terminal+=data
                ready=b'GO eingeben' in terminal or b'TEST_READY' in terminal
                if ready and answer is not None and not sent:
                    os.write(master,answer)
                    sent=True
            else:
                self.fail('Synthetic terminal child did not terminate within deadline')
            waited,status=os.waitpid(pid,os.WNOHANG)
            while not waited and time.monotonic()<deadline:
                time.sleep(0.01)
                waited,status=os.waitpid(pid,os.WNOHANG)
            self.assertEqual(waited,pid,'Synthetic shell still running')
            reaped=True
        finally:
            os.close(master)
            if not reaped:
                # Only this test-owned shell/process group; no target signals.
                try: os.killpg(pid,signal.SIGKILL)
                except ProcessLookupError: pass
                os.waitpid(pid,0)
        events=[json.loads(line) for line in log.read_text().splitlines()]
        return os.waitstatus_to_exitcode(status),events,terminal,sent

    def test_legacy_pipeline_echoes_go_but_child_is_background(self):
        code,events,terminal,sent=self.run_pty(foreground=False,mode='legacy')
        self.assertTrue(sent)
        self.assertIn(b'GO\r\n',terminal)
        self.assertEqual(events[0],dict(event='legacy_ready',monotonic_ns=events[0]['monotonic_ns'],foreground=False))
        self.assertIn(code,(2,124))
        self.assertFalse(any(x['event']=='synthetic_complete' for x in events))

    def test_foreground_pipeline_accepts_case_and_whitespace(self):
        for answer in (b'GO\n',b'go\n',b'  Go  \n'):
            with self.subTest(answer=answer):
                code,events,terminal,sent=self.run_pty(answer=answer)
                self.assertEqual(code,0)
                self.assertTrue(sent)
                self.assertEqual([x['event'] for x in events],
                                 ['ready_for_local_go','local_go_accepted','synthetic_complete'])
                self.assertIn(b'GO erkannt',terminal)
                self.assertTrue(all(x['process_memory_opened'] is False for x in events))

    def test_wrong_timeout_flags_fail_before_prompt(self):
        code,events,terminal,sent=self.run_pty(foreground=False)
        self.assertEqual(code,2)
        self.assertFalse(sent)
        self.assertNotIn(b'GO eingeben',terminal)
        self.assertEqual(len(events),1)
        self.assertIn('timeout --foreground',events[0]['reason'])

    def test_cancel_does_not_accept(self):
        code,events,_,_=self.run_pty(answer=b'stop\n')
        self.assertEqual(code,2)
        self.assertEqual([x['event'] for x in events],['ready_for_local_go','stopped'])

    def test_eof_does_not_accept(self):
        code,events,_,_=self.run_pty(answer=b'\x04')
        self.assertEqual(code,2)
        self.assertEqual([x['event'] for x in events],['ready_for_local_go','stopped'])

    def test_missing_input_or_enter_times_out_without_acceptance(self):
        for answer in (None,b'GO'):
            with self.subTest(answer=answer):
                code,events,_,_=self.run_pty(answer=answer)
                self.assertEqual(code,2)
                self.assertEqual([x['event'] for x in events],['ready_for_local_go','stopped'])

    def test_pipe_cannot_supply_a_fake_local_go(self):
        result=subprocess.run([sys.executable,'-I','-B',str(self.stub),str(OBSERVER),'corrected'],
                              input='GO\n',capture_output=True,text=True,timeout=3)
        self.assertEqual(result.returncode,2)
        event=json.loads(result.stdout)
        self.assertIn('terminal stdin',event['reason'])
        self.assertFalse(event['process_memory_opened'])

    def test_foreground_external_deadline_still_stops_wedged_child(self):
        code,events,_,_=self.run_pty(mode='wedged',answer=None)
        self.assertEqual(code,124)
        self.assertEqual(events,[])

    def test_proposed_timeout_commands_preserve_foreground(self):
        plan=(ROOT/'docs/STEAM_GYRO_OBSERVATION_PLAN.md').read_text()
        commands=[line for line in plan.splitlines() if line.lstrip().startswith('/usr/bin/timeout ')]
        self.assertEqual(len(commands),2)
        self.assertTrue(all('--foreground ' in line for line in commands))


if __name__=='__main__':
    unittest.main()
