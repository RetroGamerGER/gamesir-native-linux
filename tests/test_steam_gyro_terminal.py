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
    elif sys.argv[2]=='upfront':
        m.require_foreground_terminal()
        m.wait_local_go(timeout_s=0.35)
    elif sys.argv[2]=='inner_deadline':
        with m.alarm_scope(0.1,'Synthetic diagnostic deadline'):
            print('TEST_READY',file=sys.stderr,flush=True)
            time.sleep(2)
    elif sys.argv[2]=='nested_deadline':
        with m.alarm_scope(0.1,'Original enclosing deadline'):
            m.wait_local_go(timeout_s=0.35)
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


# Model only the documented sudo monitor/PTY job-control behavior. This is
# ordinary-user test code: no real sudo, authentication, privilege or target.
SUDO_MODEL = r'''
import errno, fcntl, os, select, signal, sys, termios, time
master,slave=os.openpty()
monitor=os.fork()
if monitor==0:
    os.close(master)
    os.setsid()
    fcntl.ioctl(slave,termios.TIOCSCTTY,0)
    os.dup2(slave,0); os.dup2(slave,2)
    if slave>2: os.close(slave)
    signal.signal(signal.SIGTTOU,signal.SIG_IGN)
    os.tcsetpgrp(0,os.getpgrp())
    worker=os.fork()
    if worker==0:
        os.setpgid(0,0)
        signal.signal(signal.SIGTTIN,signal.SIG_DFL)
        signal.signal(signal.SIGTTOU,signal.SIG_DFL)
        os.execv(sys.argv[1],sys.argv[1:])
    try: os.setpgid(worker,worker)
    except PermissionError:
        if os.getpgid(worker)!=worker: raise
    granted=False
    while True:
        _,status=os.waitpid(worker,os.WUNTRACED)
        if os.WIFSTOPPED(status):
            if os.WSTOPSIG(status)!=signal.SIGTTIN or granted:
                os.killpg(worker,signal.SIGKILL)
                os.waitpid(worker,0)
                os._exit(90)
            os.write(2,b'SIMULATED_SUDO_HANDOVER\n')
            os.tcsetpgrp(0,worker)
            os.killpg(worker,signal.SIGCONT)
            granted=True
            continue
        os.tcsetpgrp(0,os.getpgrp())
        code=os.waitstatus_to_exitcode(status)
        os._exit(code if code>=0 else 128-code)
os.close(slave)
status=None
try:
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        ready,_,_=select.select([0,master],[],[],0.02)
        if 0 in ready:
            data=os.read(0,4096)
            if not data: break
            os.write(master,data)
        if master in ready:
            try: data=os.read(master,4096)
            except OSError as error:
                if error.errno==errno.EIO: break
                raise
            if not data: break
            os.write(2,data)
    while time.monotonic()<deadline:
        pid,value=os.waitpid(monitor,os.WNOHANG)
        if pid:
            status=value; break
        time.sleep(0.01)
finally:
    os.close(master)
    if status is None:
        try: os.killpg(monitor,signal.SIGKILL)
        except ProcessLookupError: pass
        os.waitpid(monitor,0)
if status is None: sys.exit(91)
code=os.waitstatus_to_exitcode(status)
sys.exit(code if code>=0 else 128-code)
'''


class TerminalTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='gamesir-terminal-test-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.stub=self.root/'synthetic.py'
        self.stub.write_text(STUB)
        self.sudo_model=self.root/'sudo-model.py'
        self.sudo_model.write_text(SUDO_MODEL)

    def run_pty(self, *, foreground=True, mode='corrected', answer=b'GO\n',
                sudo_model=False, interposer=False):
        """Own controlling terminal; inject test text, never a real approval."""
        log=self.root/'events.jsonl'
        timeout=['/usr/bin/timeout']+(['--foreground'] if foreground else [])
        argv=timeout+['--signal=TERM','--kill-after=0.1s','1.5s',
                      sys.executable,'-I','-B',str(self.stub),str(OBSERVER),mode]
        if sudo_model:
            # sudo's monitor must own the Python child directly. An inner
            # timeout interposer can prevent delivery of the SIGTTIN handover.
            argv=timeout+['--signal=TERM','--kill-after=0.1s','2.5s',
                          sys.executable,'-I','-B',str(self.sudo_model),
                          sys.executable,'-I','-B',str(self.stub),str(OBSERVER),mode]
            if interposer:
                argv=timeout+['--signal=TERM','--kill-after=0.1s','2.5s',
                              sys.executable,'-I','-B',str(self.sudo_model)]+\
                     timeout+['--signal=TERM','--kill-after=0.1s','1.5s',
                              sys.executable,'-I','-B',str(self.stub),str(OBSERVER),mode]
        command=shlex.join(argv)
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

    def test_sudo_model_grants_terminal_on_first_read_and_accepts_go(self):
        code,events,terminal,sent=self.run_pty(sudo_model=True)
        self.assertEqual(code,0)
        self.assertTrue(sent)
        self.assertIn(b'SIMULATED_SUDO_HANDOVER',terminal)
        self.assertEqual([x['event'] for x in events],
                         ['ready_for_local_go','local_go_accepted','synthetic_complete'])
        self.assertFalse(events[0]['terminal_foreground'])
        self.assertTrue(events[1]['terminal_foreground'])

    def test_sudo_model_reproduces_upfront_guard_failure_with_interposer(self):
        code,events,terminal,sent=self.run_pty(sudo_model=True,interposer=True,mode='upfront')
        self.assertEqual(code,2)
        self.assertFalse(sent)
        self.assertEqual(len(events),1)
        self.assertIn('handover not confirmed',events[0]['reason'])
        self.assertNotIn(b'SIMULATED_SUDO_HANDOVER',terminal)

    def test_inner_timeout_interposer_prevents_read_handover(self):
        code,events,terminal,_=self.run_pty(sudo_model=True,interposer=True)
        self.assertIn(code,(124,137))
        self.assertNotIn(b'SIMULATED_SUDO_HANDOVER',terminal)
        self.assertFalse(any(x['event']=='local_go_accepted' for x in events))

    def test_sudo_model_deadline_and_cancel_still_require_real_go(self):
        for answer in (None,b'stop\n'):
            with self.subTest(answer=answer):
                code,events,terminal,_=self.run_pty(sudo_model=True,answer=answer)
                self.assertEqual(code,2)
                self.assertIn(b'SIMULATED_SUDO_HANDOVER',terminal)
                self.assertFalse(any(x['event']=='local_go_accepted' for x in events))
                self.assertTrue(all(x['process_memory_opened'] is False for x in events))

    def test_internal_deadline_stops_sudo_model_child_without_inner_timeout(self):
        code,events,_,_=self.run_pty(sudo_model=True,mode='inner_deadline',answer=None)
        self.assertEqual(code,2)
        self.assertEqual(events[0]['reason'],'Synthetic diagnostic deadline')

    def test_shorter_enclosing_deadline_survives_go_wait(self):
        code,events,_,_=self.run_pty(sudo_model=True,mode='nested_deadline',answer=None)
        self.assertEqual(code,2)
        self.assertEqual(events[-1]['reason'],'Original enclosing deadline')
        self.assertFalse(any(x['event']=='local_go_accepted' for x in events))

    def test_background_without_monitor_never_accepts(self):
        code,events,terminal,sent=self.run_pty(foreground=False)
        self.assertIn(code,(124,137))
        self.assertTrue(sent)
        self.assertFalse(events[0]['terminal_foreground'])
        self.assertFalse(any(x['event']=='local_go_accepted' for x in events))

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
        observation=plan.split('# Approved step 2:',1)[1].split('```',1)[0]
        self.assertLess(observation.index('/usr/bin/timeout '),observation.index('/usr/bin/sudo -A'))
        self.assertEqual(observation.count('/usr/bin/timeout '),1)
        self.assertIn('/usr/bin/sudo -A \\\n  /usr/bin/python3',observation)


if __name__=='__main__':
    unittest.main()
