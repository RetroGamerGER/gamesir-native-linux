#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic manager/ABI tests. No native device, socket server or host probe."""
import copy
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_service_manager import service, Fake, device
from tmr_native import NativeTmr, REQUEST, STATUS, GET, COMMAND, decode_status


def report(active=0, done=0):
    data = bytearray(64)
    data[0], data[3], data[4], data[30], data[31] = 0x10, 0x3c, 0xe0, active, done
    return data.hex()


class Backend:
    """Owner test double, not firmware emulation or a protocol proof."""
    def __init__(self, host):
        self.host = host
        self.calls = []
        self.fail = ''
        self.closed = 0
        self.status = {'pid': 0x109c, 'flags': 3, 'phase': 0, 'error': 0,
                       'port_token': 11, 'instance_token': 22, 'stream_epoch': 1,
                       'generation': 0, 'report_number': 1, 'host_monotonic_ns': 1_000_000_000,
                       'lease_deadline_ns': 0, 'report': report()}

    def get(self):
        if self.fail == 'get':
            raise OSError('getter failed')
        return copy.deepcopy(self.status)

    def command(self, operation, target, generation):
        self.calls.append(operation)
        if operation == self.fail:
            raise OSError('original ' + operation + ' failure')
        if operation == 'acquire':
            self.status.update(phase=1, generation=generation, flags=7,
                               lease_deadline_ns=int((self.host.now + 2) * 1e9))
        if operation == 'renew':
            self.status['lease_deadline_ns'] = int((self.host.now + 2) * 1e9)
        if operation in ('Start', 'Finish', 'Exit'):
            self.status['phase'] = {'Start': 2, 'Finish': 3, 'Exit': 4}[operation]

    def close(self):
        self.closed += 1
        if self.fail == 'close':
            raise OSError('close uncertain')


class ManagerTmr(unittest.TestCase):
    def setUp(self):
        self.d = device(pid='109c', driver='gs_native')
        self.host = Fake([self.d])
        self.host.now = 1
        self.manager = service.Manager(self.host, lambda: self.host.now)
        self.manager.entries[self.d.port] = service.Entry(self.d, 'active', kernel_tokens=[11, 22])
        self.manager.observed = dict(self.host.devices)
        self.backend = Backend(self.host)
        self.host.open_tmr = Mock(return_value=self.backend)

    def request(self, action, **fields):
        value = {'version': 1, 'tmr': action, 'port': self.d.port}
        if action in ('probe', 'acquire'):
            value.update(port_token=11, instance_token=22)
            if action == 'acquire':
                value['stream_epoch'] = 1
        else:
            value['lease'] = self.token
        value.update(fields)
        return self.manager.command(value)

    def acquire(self):
        value = self.request('acquire')
        self.token = value['lease']
        return value

    def test_constructor_and_normal_tick_have_no_calibration_access(self):
        self.host.open_tmr.assert_not_called()
        self.manager.entries[self.d.port].next_check = 100
        self.manager.tick()
        self.host.open_tmr.assert_not_called()

    def test_probe_has_no_command_and_preserves_normal_runtime(self):
        value = self.request('probe')
        self.assertEqual(value['link_basis'], 'fresh_e0_continuity_only')
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.backend.closed, 1)
        self.assertFalse(self.manager.tmr.busy(self.d.port))
        self.assertEqual(self.manager.entries[self.d.port].phase, 'active')
        self.assertFalse(self.host.calls)

    def test_start_ready_finish_release_exactly_once(self):
        self.acquire()
        self.request('Start')
        self.backend.status['report'] = report(3, 3)
        self.request('Finish')
        self.request('release')
        self.assertEqual(self.backend.calls, ['acquire', 'Start', 'Finish', 'release'])
        self.assertEqual(self.backend.closed, 1)
        self.assertFalse(self.host.calls)

    def test_exit_and_release_have_no_implicit_finish(self):
        self.acquire()
        self.request('Start')
        self.request('Exit')
        self.request('release')
        self.assertEqual(self.backend.calls, ['acquire', 'Start', 'Exit', 'release'])

    def test_not_ready_never_submits_finish(self):
        self.acquire()
        self.request('Start')
        with self.assertRaisesRegex(service.Unsafe, 'not ready'):
            self.request('Finish')
        self.assertNotIn('Finish', self.backend.calls)
        self.assertNotIn('Exit', self.backend.calls)

    def test_duplicate_operations_are_terminal_without_replay(self):
        for action in ('Start', 'Finish', 'Exit'):
            with self.subTest(action=action):
                self.setUp()
                self.acquire()
                self.request('Start')
                if action != 'Start':
                    self.backend.status['report'] = report(3, 3)
                    self.request(action)
                with self.assertRaises(service.Unsafe):
                    self.request(action)
                self.assertEqual(self.backend.calls.count(action), 1)

    def test_uncertain_submission_is_never_replayed_or_compensated(self):
        for action in ('Start', 'Finish', 'Exit'):
            with self.subTest(action=action):
                self.setUp()
                self.acquire()
                if action != 'Start':
                    self.request('Start')
                    self.backend.status['report'] = report(3, 3)
                self.backend.fail = action
                with self.assertRaisesRegex(service.Unsafe, 'original ' + action):
                    self.request(action)
                with self.assertRaises(service.Unsafe):
                    self.request(action)
                self.assertEqual(self.backend.calls.count(action), 1)
                self.assertEqual(self.backend.calls[-1], 'release')
                self.assertIn('original ' + action, self.manager.tmr.last[self.d.port]['error'])

    def test_first_error_survives_cleanup_failure(self):
        self.acquire()
        self.backend.status['error'] = -32
        self.backend.fail = 'release'
        with self.assertRaises(service.Unsafe):
            self.request('poll')
        last = self.manager.tmr.last[self.d.port]
        self.assertIn('continuity', last['error'])
        self.assertIn('release failure', last['cleanup_error'])
        self.assertEqual(self.backend.closed, 1)

    def test_ambiguous_close_blocks_port_without_retry(self):
        self.acquire()
        self.backend.fail = 'close'
        with self.assertRaises(service.Unsafe): self.request('release')
        with self.assertRaises(service.Unsafe): self.request('release')
        self.manager.tmr.tick()
        self.manager.tmr.close()
        self.assertTrue(self.manager.tmr.busy(self.d.port))
        self.assertEqual(self.backend.closed, 1)
        with self.assertRaises(service.Unsafe):
            self.request('acquire')

    def test_probe_close_failure_is_not_retried(self):
        self.backend.fail = 'close'
        with self.assertRaises(service.Unsafe): self.request('probe')
        self.manager.tmr.tick()
        self.manager.tmr.close()
        self.assertEqual(self.backend.closed, 1)
        self.assertEqual(self.backend.calls, [])

    def test_client_disappearance_expires_without_exit_or_finish(self):
        self.acquire()
        self.request('Start')
        self.host.now = 3
        self.manager.tmr.tick()
        self.assertEqual(self.backend.calls, ['acquire', 'Start', 'release'])
        self.assertEqual(self.backend.closed, 1)
        self.assertFalse(self.manager.tmr.busy(self.d.port))

    def test_release_failure_is_reported_despite_successful_fd_close(self):
        self.acquire()
        self.backend.fail = 'release'
        with self.assertRaisesRegex(service.Unsafe, 'lease return reported'):
            self.request('release')
        self.assertFalse(self.manager.tmr.busy(self.d.port))
        self.assertEqual(self.backend.closed, 1)
        self.assertIn('release failure', self.manager.tmr.last[self.d.port]['cleanup_error'])

    def test_poll_renews_lease_but_not_rx_timestamp_or_counter(self):
        self.acquire()
        self.host.now = 1.2
        before = self.backend.status.copy()
        result = self.request('poll')['status']
        for field in ('report_number', 'host_monotonic_ns', 'report'):
            self.assertEqual(before[field], result[field])
        self.assertGreater(result['lease_deadline_ns'], before['lease_deadline_ns'])

    def test_display_poll_and_watchdog_do_not_repeat_global_fd_audit(self):
        self.acquire()
        with patch.object(self.host,'guard',wraps=self.host.guard) as guard:
            for _ in range(30):
                self.request('poll');self.manager.tmr.tick()
            self.assertEqual(guard.call_count,0)
        self.assertNotIn('Start',self.backend.calls)

    def test_foreign_usb_owner_still_blocks_every_device_command(self):
        for action in ('Start','Finish','Exit'):
            with self.subTest(action=action):
                self.setUp();self.acquire()
                if action!='Start':
                    self.request('Start');self.backend.status['report']=report(3,3)
                count=self.backend.calls.count(action)
                self.host.block.add(self.d.port)
                with self.assertRaises(service.Unsafe):self.request(action)
                self.assertEqual(self.backend.calls.count(action),count)
                self.assertFalse(self.manager.tmr.busy(self.d.port))

    def test_poll_rechecks_live_instance_without_waiting_for_daemon_scan(self):
        self.acquire();self.host.devices.clear()
        with self.assertRaises(service.Unsafe):self.request('poll')
        self.assertFalse(self.manager.tmr.busy(self.d.port))
        self.assertNotIn('renew',self.backend.calls)

    def test_usb_command_has_full_pre_and_post_submit_audits(self):
        self.acquire()
        with patch.object(self.host,'guard',wraps=self.host.guard) as guard:
            self.request('Start')
            self.assertEqual(guard.call_count,2)

    def test_post_submit_owner_conflict_is_terminal_and_never_retried(self):
        self.acquire();command=self.backend.command
        def send(action,*args):
            command(action,*args)
            if action=='Start':self.host.block.add(self.d.port)
        self.backend.command=send
        with self.assertRaises(service.Unsafe):self.request('Start')
        self.assertEqual(self.backend.calls.count('Start'),1)
        self.assertFalse(self.manager.tmr.busy(self.d.port))
        self.assertNotIn('Exit',self.backend.calls)

    def test_changed_or_stale_stream_is_terminal(self):
        for key, value in (('stream_epoch', 2), ('instance_token', 23), ('port_token', 12),
                           ('pid', 0x105e), ('generation', 0), ('flags', 3), ('error', -32),
                           ('host_monotonic_ns', 9_000_000_000), ('host_monotonic_ns', 1),
                           ('lease_deadline_ns', 1), ('report_number', 0)):
            with self.subTest(field=key, value=value):
                self.setUp()
                self.acquire()
                self.backend.status[key] = value
                if key == 'host_monotonic_ns' and value == 1:
                    self.host.now = 1.6
                with self.assertRaises(service.Unsafe):
                    self.request('Start')
                self.assertNotIn('Start', self.backend.calls)

    def test_admission_requires_exact_managed_idle_owner(self):
        for field in ('paused', 'scan', 'port_error', 'job', 'phase', 'foreign', 'replaced'):
            with self.subTest(field=field):
                self.setUp()
                entry = self.manager.entries[self.d.port]
                if field == 'paused': self.manager.paused = True
                if field == 'scan': self.manager.scan_error = 'incomplete'
                if field == 'port_error': self.manager.port_errors[self.d.port] = 'uncertain'
                if field == 'job': entry.job = object()
                if field == 'phase': entry.phase = 'receiver_wait'
                if field == 'foreign': self.host.block.add(self.d.port)
                if field == 'replaced': self.manager.observed.clear()
                with self.assertRaises(service.Unsafe): self.request('acquire')
                self.host.open_tmr.assert_not_called()

    def test_requests_are_narrow_and_strict(self):
        for fields in ({'version': True}, {'packet': 'fe0003'}, {'port_token': True},
                       {'instance_token': 0}, {'stream_epoch': 2**64}, {'stream_epoch': 2}):
            with self.subTest(fields=fields):
                self.setUp()
                with self.assertRaises(service.Unsafe): self.request('acquire', **fields)
                self.assertNotIn('acquire', self.backend.calls)

    def test_wrong_lease_cannot_steal_or_end_real_run(self):
        self.acquire()
        with self.assertRaises(service.Unsafe): self.request('release', lease='other')
        self.assertTrue(self.manager.tmr.busy(self.d.port))
        self.assertEqual(self.backend.calls, ['acquire'])

    def test_normal_manager_jobs_and_haptics_are_deferred_only_on_owned_port(self):
        self.acquire()
        self.manager.tick()
        self.assertFalse(self.host.jobs)
        with self.assertRaises(service.Unsafe): self.manager.command('resume')
        from haptics_broker import Busy
        backend = service.HapticBackend(self.manager)
        identity = next(iter(backend.selections()))
        self.assertTrue(backend.devices()[identity]['busy'])
        with self.assertRaises(Busy): backend.apply(identity, [])

    def test_release_drops_maintenance_before_normal_return(self):
        self.acquire()
        self.request('Start')
        self.manager.command('release')
        self.assertEqual(self.backend.calls[-1], 'release')
        self.assertNotIn('Exit', self.backend.calls)
        self.assertFalse(self.manager.tmr.runs)
        self.assertTrue(self.manager.paused)

    def test_root_socket_bounds_and_fragmented_request(self):
        command = {'version': 1, 'tmr': 'probe', 'port': self.d.port,
                   'port_token': 11, 'instance_token': 22}
        data = (json.dumps(command) + '\n').encode()
        conn = Mock()
        conn.getsockopt.return_value = struct.pack('3i', 111, 0, 0)
        conn.recv.side_effect = [data[:2], data[2:]]
        service.serve_connection(conn, self.manager)
        self.assertTrue(json.loads(conn.sendall.call_args.args[0])['ok'])
        for data in (b'{"version":1}\n' + b'x' * 2048, b'{\n}\n', b'{"version": 1}\ntrailing'):
            conn.recv.side_effect = [data]
            service.serve_connection(conn, self.manager)
            self.assertFalse(json.loads(conn.sendall.call_args.args[0])['ok'])

    def test_unprivileged_peer_is_rejected_before_any_request_read(self):
        conn = Mock()
        conn.getsockopt.return_value = struct.pack('3i', 111, 1000, 1000)
        service.serve_connection(conn, self.manager)
        conn.recv.assert_not_called()
        self.host.open_tmr.assert_not_called()

    def test_slow_partial_root_request_cannot_block_the_manager_indefinitely(self):
        conn = Mock()
        conn.getsockopt.return_value = struct.pack('3i', 111, 0, 0)
        conn.recv.return_value = b'{'
        with patch.object(service.time, 'monotonic', side_effect=[1, 3]):
            service.serve_connection(conn, self.manager)
        self.assertFalse(json.loads(conn.sendall.call_args.args[0])['ok'])
        conn.recv.assert_called_once()
        self.host.open_tmr.assert_not_called()

    def test_disabled_host_interface_never_opens_device(self):
        host = service.Host('unused', Path('/synthetic-state'), sysfs=Path('/synthetic-sys'))
        with patch.object(Path, 'is_file', return_value=False), patch('tmr_native.os.open') as opened:
            with self.assertRaisesRegex(service.Unsafe, 'disabled'): host.open_tmr(self.d)
            opened.assert_not_called()


class NativeAbi(unittest.TestCase):
    def test_shared_c_policy_boundaries_and_packet_candidate(self):
        root = Path(__file__).resolve().parents[1]
        directory = root / 'build/tmr-policy'
        directory.mkdir(exist_ok=True)
        source = directory / 'policy.c'
        source.write_text(r'''
#include "gs_tmr.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
    struct gs_tmr t = {0};
    gs_u8 d[64] = {0x10, 0, 255, 0x3c, 0xe0}, p[64];
    assert(!gs_tmr_fresh(&t, 100));
    for (int size=0; size<64; size++) {
        gs_tmr_receive(&t, d, size, 100);
        assert(!t.number);
    }
    d[1]=1; gs_tmr_receive(&t,d,64,100); assert(!t.number); d[1]=0;
    gs_tmr_receive(&t,d,64,100);
    assert(t.number == 1 && t.epoch == 1 && !memcmp(t.report,d,64));
    d[2]=0; gs_tmr_receive(&t,d,64,101);
    assert(t.number == 2 && t.received_ns == 101); /* wire wrap is not local count */
    assert(gs_tmr_command(&t,GSN_TMR_ACQUIRE,1,0,101)==-ESTALE);
    assert(gs_tmr_command(&t,GSN_TMR_ACQUIRE,2,7,101)==-ESTALE);
    assert(!gs_tmr_command(&t,GSN_TMR_ACQUIRE,1,7,101));
    assert(gs_tmr_command(&t,GSN_TMR_FINISH,1,7,101)==-EINVAL);
    assert(gs_tmr_command(&t,GSN_TMR_START,1,7,101)==1);
    assert(gs_tmr_command(&t,GSN_TMR_START,1,7,101)==-EINVAL);
    assert(gs_tmr_command(&t,GSN_TMR_FINISH,1,7,101)==-EAGAIN);
    d[30]=3; d[31]=3; gs_tmr_receive(&t,d,64,102);
    assert(gs_tmr_command(&t,GSN_TMR_FINISH,1,7,102)==1);
    assert(gs_tmr_command(&t,GSN_TMR_EXIT,1,7,102)==-EINVAL);
    assert(!gs_tmr_command(&t,GSN_TMR_RELEASE,1,7,102));
    assert(gs_tmr_command(&t,GSN_TMR_ACQUIRE,1,8,102)==-EBUSY);
    gs_tmr_close(&t); assert(!t.handle && !t.error && !t.phase);
    t=(struct gs_tmr){0}; d[30]=d[31]=0;
    gs_tmr_receive(&t,d,64,100);
    assert(!gs_tmr_command(&t,GSN_TMR_ACQUIRE,1,9,100));
    assert(gs_tmr_command(&t,GSN_TMR_START,1,9,100)==1);
    gs_tmr_receive(&t,d,64,100); /* non-increasing RX invalidates, not renews */
    assert(t.phase==5 && t.error==-ESTALE && t.epoch==2 && !t.number);
    gs_tmr_fail(&t,-EPIPE); assert(t.error==-ESTALE);
    gs_tmr_close(&t); assert(t.error==-ESTALE);
    assert(gs_tmr_command(&t,GSN_TMR_ACQUIRE,2,10,101)==-ESTALE);
    t=(struct gs_tmr){0};
    gs_tmr_receive(&t,d,64,100);
    assert(!gs_tmr_command(&t,GSN_TMR_ACQUIRE,1,9,100));
    gs_tmr_check(&t,100+GS_TMR_AGE_NS); assert(!t.error);
    gs_tmr_check(&t,101+GS_TMR_AGE_NS); assert(t.error==-ESTALE);
    t=(struct gs_tmr){0}; gs_tmr_receive(&t,d,64,100);
    assert(gs_tmr_command(&t,GSN_TMR_ACQUIRE,1,9,(gs_u64)-1)==-EOVERFLOW);
    t.number=(gs_u64)-1; gs_tmr_receive(&t,d,64,101); assert(t.error==-EOVERFLOW);
    for (unsigned op=GSN_TMR_START;op<=GSN_TMR_EXIT;op++) {
        memset(p,0xab,64); assert(gs_tmr_packet(p,255,op)==64);
        assert(p[0]==15 && !p[1] && p[2]==255 && p[3]==3 && p[4]==254);
        assert(p[5]==op-2 && p[6]==(op==2 ? 3:0));
        for (int n=7;n<64;n++) assert(!p[n]);
    }
    assert(gs_tmr_packet(p,1,GSN_TMR_ACQUIRE)==-EINVAL);
    assert(gs_tmr_packet(p,1,GSN_TMR_RENEW)==-EINVAL);
    puts("PASS: TMR shared C boundaries; synthetic wire candidate only");
}
''')
        executable = directory / 'policy'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                        '-I', str(root / 'src'), str(source), '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True, capture_output=True)

    def packed(self, **updates):
        fields = dict(abi=1, flags=3, pid=0x109c, phase=0, error=0, reserved=0,
                      port_token=11, instance_token=22, stream_epoch=1, generation=0,
                      report_number=5, host_monotonic_ns=123, lease_deadline_ns=0,
                      report=bytes.fromhex(report()))
        fields.update(updates)
        return STATUS.pack(*fields.values())

    def test_uapi_layout(self):
        self.assertEqual((REQUEST.size, STATUS.size), (48, 144))
        self.assertEqual((GET, COMMAND), (0x8090477b, 0x4030477c))
        self.assertEqual(decode_status(self.packed())['report_number'], 5)
        for fields in ({'abi': 2}, {'reserved': 1}, {'flags': 8}, {'phase': 6},
                       {'pid': 0x100a}, {'instance_token': 0}):
            with self.assertRaises(ValueError): decode_status(self.packed(**fields))

    def test_adapter_has_only_narrow_ioctl_no_fallback(self):
        opened, closed, calls = Mock(return_value=123), Mock(), []
        def ioctl(fd, request, data, mutate=False):
            calls.append((fd, request, bytes(data)))
            if request == GET: data[:] = self.packed()
        native = NativeTmr('/synthetic-native', open_fd=opened, close_fd=closed,
                           fstat=lambda fd: SimpleNamespace(st_mode=stat.S_IFCHR), ioctl=ioctl)
        target = {'port_token': 11, 'instance_token': 22, 'stream_epoch': 1}
        native.command('Start', target, 77)
        self.assertEqual(REQUEST.unpack(calls[1][2]), (1, 2, 11, 22, 1, 77, 0, 0))
        opened.assert_called_once_with('/synthetic-native', os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
        with self.assertRaises(KeyError): native.command('raw', target, 77)
        native.close()
        native.close()
        closed.assert_called_once_with(123)

    def test_unknown_ioctl_does_not_retry_or_fallback(self):
        closed = Mock()
        with self.assertRaises(OSError):
            NativeTmr('/synthetic-native', open_fd=lambda *a: 123, close_fd=closed,
                      fstat=lambda fd: SimpleNamespace(st_mode=stat.S_IFCHR),
                      ioctl=Mock(side_effect=OSError('unsupported')))
        closed.assert_called_once_with(123)


if __name__ == '__main__':
    unittest.main()
