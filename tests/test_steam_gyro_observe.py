#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline observer guards with synthetic maps/memory; no live process/device."""
import importlib.util
import contextlib
import io
import json
import errno
import hashlib
import mmap
import os
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('observer', ROOT/'tools/sdl/steam_gyro_observe.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class LibraryIdentityTests(unittest.TestCase):
    """Own temporary files and fake proc links only; no Steam or sudo."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.library = self.root/'libSDL3.so.0'
        self.payload = b'\x7fELF\x01\x01' + bytes(8192)
        self.library.write_bytes(self.payload)
        self.proc = self.root/'fake-proc'
        (self.proc/'map_files').mkdir(parents=True)
        # Deliberately different from stat.st_dev, as observed on Btrfs.
        dev = self.library.stat().st_dev
        self.map_dev = f'{os.major(dev):02x}:{os.minor(dev)+1:02x}'
        ino = self.library.stat().st_ino
        self.rows = m.maps_parse(
            f'100000-101000 r--p 0 {self.map_dev} {ino} {self.library}\n'
            f'101000-104000 r-xp 1000 {self.map_dev} {ino} {self.library}')
        for a,b,*_ in self.rows:
            (self.proc/'map_files'/f'{a:x}-{b:x}').symlink_to(self.library)
        patches = contextlib.ExitStack()
        self.addCleanup(patches.close)
        patches.enter_context(patch.object(m, 'SDL_SHA', hashlib.sha256(self.payload).hexdigest()))
        patches.enter_context(patch.object(m, 'SDL_BYTES', len(self.payload)))

    def identity(self):
        return m.library_identity(self.rows, self.proc)

    def relink(self, index, target):
        a,b,*_ = self.rows[index]
        link = self.proc/'map_files'/f'{a:x}-{b:x}'
        link.unlink()
        link.symlink_to(target)

    def test_btrfs_style_device_difference_accepts_same_backing_file(self):
        info = self.library.stat()
        old_dev = f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}'
        self.assertFalse(all(x[4] == old_dev and x[5] == info.st_ino for x in self.rows))
        result = self.identity()
        self.assertEqual(result[:4], (0x100000, str(self.library), info.st_dev, info.st_ino))
        m.verify_library_mappings(self.rows, self.proc, result)

    def test_ordinary_same_device_identity_also_accepted(self):
        info = self.library.stat()
        dev = f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}'
        self.rows = [(*x[:4],dev,*x[5:]) for x in self.rows]
        self.identity()

    def test_same_bytes_different_inode_rejected_for_every_segment(self):
        copy = self.root/'copy'
        copy.write_bytes(self.payload)
        for i in range(len(self.rows)):
            with self.subTest(segment=i):
                self.relink(i,copy)
                with self.assertRaisesRegex(m.Halt, 'backing file identity differs'):
                    self.identity()
                self.relink(i,self.library)

    def test_same_inode_on_different_subvolume_not_accepted(self):
        original = Path.stat
        def stat(path, *args, **kwargs):
            result = original(path,*args,**kwargs)
            if path.parent == self.proc/'map_files':
                fields = {name:getattr(result,name) for name in
                          ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns')}
                fields['st_dev'] += 1
                return SimpleNamespace(**fields)
            return result
        with patch.object(Path,'stat',stat):
            with self.assertRaisesRegex(m.Halt,'backing file identity differs'): self.identity()

    def test_map_files_denial_or_disappearance_stops_without_fallback(self):
        original = Path.stat
        for number in (errno.EPERM,errno.EACCES,errno.ENOENT):
            def stat(path,*args,**kwargs):
                if path.parent == self.proc/'map_files': raise OSError(number,'synthetic')
                return original(path,*args,**kwargs)
            with self.subTest(errno=number), patch.object(Path,'stat',stat):
                with self.assertRaisesRegex(m.Halt,f'errno {number}.*no fallback'): self.identity()

    def test_inconsistent_map_inode_rejected(self):
        self.rows[1] = (*self.rows[1][:5],self.rows[1][5]+1,self.rows[1][6])
        with self.assertRaisesRegex(m.Halt,'Inconsistent'): self.identity()

    def test_deleted_mapping_rejected(self):
        self.rows = [(*x[:6],x[6]+' (deleted)') for x in self.rows]
        with self.assertRaisesRegex(m.Halt,'Missing/deleted'): self.identity()

    def test_non_regular_file_rejected_before_open(self):
        self.library.unlink()
        self.library.mkdir()
        with self.assertRaisesRegex(m.Halt,'not regular'): self.identity()

    def test_wrong_size_or_hash_rejected(self):
        self.library.write_bytes(b'wrong')
        with self.assertRaisesRegex(m.Halt,'size not reviewed'): self.identity()
        self.library.write_bytes(b'x'*len(self.payload))
        with self.assertRaisesRegex(m.Halt,'version not reviewed'): self.identity()

    def test_wrong_elf_abi_rejected_even_with_matching_hash(self):
        wrong = b'\x7fELF\x02\x01'+self.payload[6:]
        self.library.write_bytes(wrong)
        with patch.object(m,'SDL_SHA',hashlib.sha256(wrong).hexdigest()):
            with self.assertRaisesRegex(m.Halt,'ELF32'): self.identity()

    def test_replacement_between_stat_and_open_rejected(self):
        original = Path.open
        def opening(path,*args,**kwargs):
            if path == self.library:
                path.rename(self.root/'previous')
                original(path,'wb').close()
            return original(path,*args,**kwargs)
        with patch.object(Path,'open',opening):
            with self.assertRaisesRegex(m.Halt,'changed before hash'): self.identity()

    def test_replacement_during_hash_rejected(self):
        original = hashlib.sha256
        def digest(data):
            self.library.rename(self.root/'previous')
            self.library.write_bytes(self.payload)
            return original(data)
        with patch.object(m.hashlib,'sha256',digest):
            with self.assertRaisesRegex(m.Halt,'changed during hash'): self.identity()

    def test_in_place_change_during_hash_rejected(self):
        original = hashlib.sha256
        def digest(data):
            self.library.write_bytes(b'x'*len(self.payload))
            meta=self.library.stat()
            os.utime(self.library, ns=(meta.st_atime_ns,meta.st_mtime_ns+1000000000))
            return original(data)
        with patch.object(m.hashlib,'sha256',digest):
            with self.assertRaisesRegex(m.Halt,'changed during hash'): self.identity()

    def test_mapping_replaced_during_hash_rejected(self):
        copy=self.root/'copy'; copy.write_bytes(self.payload)
        original=hashlib.sha256
        def digest(data):
            self.relink(1,copy)
            return original(data)
        with patch.object(m.hashlib,'sha256',digest):
            with self.assertRaisesRegex(m.Halt,'backing file identity differs'): self.identity()

    def test_sample_checks_all_segments_not_only_load_base(self):
        saved=self.identity()
        for field,value in ((1,0x105000),(2,'r--p'),(3,0x2000),(4,'01:02'),(5,22)):
            changed=list(self.rows); row=list(changed[1]); row[field]=value; changed[1]=tuple(row)
            with self.subTest(field=field), self.assertRaises(m.Halt):
                m.verify_library_mappings(changed,self.proc,saved)

    def test_sample_rejects_backing_file_replacement(self):
        saved=self.identity()
        copy=self.root/'copy'; copy.write_bytes(self.payload)
        self.relink(1,copy)
        with self.assertRaisesRegex(m.Halt,'backing file identity differs'):
            m.verify_library_mappings(self.rows,self.proc,saved)

    def test_multiple_libraries_rejected(self):
        self.rows.append((*self.rows[0][:6],str(self.root/'other/libSDL3.so.0')))
        with self.assertRaisesRegex(m.Halt,'exactly one SDL3'): self.identity()

    def test_own_readonly_mapping_with_fake_proc_metadata(self):
        # Real mmap of our synthetic bytes only; never load/execute the file.
        # Kernel map_files traversal requires extra capabilities: the aliases
        # remain synthetic. This is not validation against the Steam process.
        with self.library.open('rb') as file, mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ):
            self.rows = [row for row in m.maps_parse(Path('/proc/self/maps').read_text())
                         if row[6] == str(self.library)]
            self.assertEqual(len(self.rows),1)
            a,b,*_=self.rows[0]
            (self.proc/'map_files'/f'{a:x}-{b:x}').symlink_to(self.library)
            # Fixture has no executable mapping; add only that synthetic flag
            # to exercise library identification without executing anything.
            self.rows[0]=(*self.rows[0][:2],'r-xp',*self.rows[0][3:])
            self.identity()


class FakeMemory:
    string = m.Memory.string

    def __init__(self):
        self.data = {}
        self.base = 0x10000000
        self.node = 0x20000000
        self.sensors = 0x20002000
        self.path = 0x20001000
        self.put(self.base+m.FUNCTION_SLOT, struct.pack('<I',self.base+m.FUNCTION_OFFSET))
        self.put(self.base+m.LIST_OFFSET, struct.pack('<I',self.node))
        self.put(self.node, struct.pack('<III', 23,0,self.path))
        self.put(self.path,b'/dev/input/event99\0')
        self.put(self.node+0x100, struct.pack('<I',0))
        self.put(self.node+0x58, struct.pack('<III',1,1,self.sensors))
        self.entry(2,1,(.25,-.5,.75))

    def put(self,address,data):
        self.data.update({address+i:b for i,b in enumerate(data)})

    def entry(self,kind,enabled,values):
        self.put(self.sensors, struct.pack('<IB3xf3f',kind,enabled,0.,*values))

    def read(self,address,size):
        return bytes(self.data[address+i] for i in range(size))

    def snapshot(self):
        return m.snapshot(self,self.base,'/dev/input/event99')


class ObserverTests(unittest.TestCase):
    def test_pinned_layout_extracts_only_selected_gyro(self):
        f=FakeMemory()
        node,instance,sensors,data=f.snapshot()
        self.assertEqual((node,instance,sensors),(f.node,23,f.sensors))
        self.assertEqual(data,{'enabled':True,'rad_s':(.25,-.5,.75)})

    def test_disabled_is_observed_not_enabled_by_tool(self):
        f=FakeMemory(); f.entry(2,0,(0,0,0))
        f.put(f.node+0x5c,struct.pack('<I',0))
        before=dict(f.data)
        self.assertFalse(f.snapshot()[3]['enabled'])
        self.assertEqual(before,f.data)

    def test_dynamic_api_override_stops(self):
        f=FakeMemory(); f.put(f.base+m.FUNCTION_SLOT,struct.pack('<I',123))
        with self.assertRaisesRegex(m.Halt,'dynamic API'): f.snapshot()

    def test_joystick_loop_stops(self):
        f=FakeMemory(); f.put(f.node+0x100,struct.pack('<I',f.node))
        with self.assertRaisesRegex(m.Halt,'joystick list'): f.snapshot()

    def test_no_matching_device_stops(self):
        f=FakeMemory()
        with self.assertRaisesRegex(m.Halt,'matching SDL joystick'):
            m.snapshot(f,f.base,'/dev/input/event1')

    def test_ambiguous_target_stops(self):
        f=FakeMemory()
        # Use another object sharing the same target path.
        other=f.node+0x4000
        f.put(other,f.read(f.node,12)); f.put(other+0x58,f.read(f.node+0x58,12))
        f.put(other+0x100,struct.pack('<I',0)); f.put(f.node+0x100,struct.pack('<I',other))
        with self.assertRaisesRegex(m.Halt,'exactly one matching'): f.snapshot()

    def test_unbounded_sensor_count_stops(self):
        f=FakeMemory(); f.put(f.node+0x58,struct.pack('<I',1000))
        with self.assertRaisesRegex(m.Halt,'sensor metadata'): f.snapshot()

    def test_missing_gyro_stops(self):
        f=FakeMemory(); f.entry(1,1,(0,0,0))
        with self.assertRaisesRegex(m.Halt,'one SDL gyro'): f.snapshot()

    def test_invalid_sensor_state_stops(self):
        f=FakeMemory(); f.entry(2,7,(0,0,0))
        with self.assertRaisesRegex(m.Halt,'sensor entry'): f.snapshot()

    def test_nan_and_absurd_values_stop(self):
        for value in (float('nan'),float('inf'),1001.):
            f=FakeMemory(); f.entry(2,1,(value,0,0))
            with self.assertRaisesRegex(m.Halt,'gyro values'): f.snapshot()

    def test_concurrent_value_update_is_not_reported_as_motion(self):
        f=FakeMemory(); original=f.read; count=0
        def read(address,size):
            nonlocal count
            if address==f.sensors:
                count+=1
                if count==2: f.entry(2,1,(1,2,3))
            return original(address,size)
        f.read=read
        with self.assertRaises(m.BusySnapshot): f.snapshot()

    def test_metadata_change_is_fatal(self):
        f=FakeMemory(); original=f.read; count=0
        def read(address,size):
            nonlocal count
            if address==f.node+0x58:
                count+=1
                if count==2: f.put(f.node+0x60,struct.pack('<I',f.sensors+100))
            return original(address,size)
        f.read=read
        with self.assertRaisesRegex(m.Halt,'metadata changed'): f.snapshot()

    def test_read_permission_range_and_budget(self):
        rows=m.maps_parse('1000-2000 r--p 00000000 00:00 0\n2000-3000 ---p 00000000 00:00 0')
        memory=m.Memory(19,rows)
        with patch.object(m.os,'pread',return_value=b'abcd') as pread:
            self.assertEqual(memory.read(0x1000,4),b'abcd')
            pread.assert_called_once_with(19,4,0x1000)
            for address,size in ((0,4),(0x1000,257),(0x1fff,4),(0x2000,4),(2**32,4)):
                with self.assertRaises(m.Halt): memory.read(address,size)
            memory.total=4*1024*1024
            with self.assertRaisesRegex(m.Halt,'budget'): memory.read(0x1000,4)

    def test_short_read_stops(self):
        memory=m.Memory(19,m.maps_parse('1000-2000 r--p 0 00:00 0'))
        with patch.object(m.os,'pread',return_value=b'x'):
            with self.assertRaisesRegex(m.Halt,'Short'): memory.read(0x1000,4)

    def test_library_guard_failure_never_opens_process_memory(self):
        opening=self.fake_main('--precheck')
        with patch.object(m,'library_identity',side_effect=m.Halt('backing file identity differs')):
            with self.assertRaisesRegex(m.Halt,'backing file identity differs'): m.main()
        opening.assert_not_called()

    def fake_main(self, mode, answer='go\n'):
        stack=contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(m.sys,'argv',['observer',mode]))
        stack.enter_context(patch.object(m.sys,'stdin',io.StringIO(answer)))
        stack.enter_context(patch.dict(m.os.environ,{'SUDO_UID':'1000'}))
        stack.enter_context(patch.object(m,'find_steam',return_value=123))
        stack.enter_context(patch.object(m,'process_identity',return_value=(123,'77','steam',1000)))
        stack.enter_context(patch.object(m,'target_identity',return_value=(('/dev/input/event99',),('/dev/input/event100',))))
        stack.enter_context(patch.object(m,'library_identity',return_value=(0x10000000,'/fake/SDL',1,4)))
        stack.enter_context(patch.object(m,'descriptors',return_value={'gamepad_fds':1,'sensor_fds':0}))
        stack.enter_context(patch.object(Path,'read_text',return_value='1000-2000 r--p 0 00:00 0'))
        stack.enter_context(patch.object(m.select,'select',return_value=([m.sys.stdin],[],[])))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        return stack.enter_context(patch.object(m.os,'open',side_effect=AssertionError('No memory open allowed')))

    def test_precheck_never_opens_process_memory(self):
        opening=self.fake_main('--precheck')
        self.assertEqual(m.main(),0)
        opening.assert_not_called()

    def test_local_cancel_and_eof_never_open_process_memory(self):
        opening=self.fake_main('--observe',answer='stop\n')
        with self.assertRaisesRegex(m.Halt,'No local GO'): m.main()
        opening.assert_not_called()

    def test_no_response_never_opens_process_memory(self):
        opening=self.fake_main('--observe')
        with patch.object(m.select,'select',return_value=([],[],[])):
            with self.assertRaisesRegex(m.Halt,'No local GO'): m.main()
        opening.assert_not_called()

    def test_changed_process_before_go_never_opens_memory(self):
        opening=self.fake_main('--observe')
        with patch.object(m,'process_identity',side_effect=[('first',),('replacement',)]):
            with self.assertRaisesRegex(m.Halt,'Instance changed'): m.main()
        opening.assert_not_called()

    def test_library_failure_after_go_never_opens_memory(self):
        opening=self.fake_main('--observe')
        with patch.object(m,'library_identity',side_effect=[('initial',),m.Halt('backing file identity differs')]):
            with self.assertRaisesRegex(m.Halt,'backing file identity differs'): m.main()
        opening.assert_not_called()

    def test_no_explicit_cli_mode_is_safe(self):
        with patch.object(m.sys,'argv',['observer']), patch.object(m,'find_steam') as discover:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): m.main()
            discover.assert_not_called()

    def test_no_automatic_retry_and_no_target_mutations_in_source(self):
        source=(ROOT/'tools/sdl/steam_gyro_observe.py').read_text()
        for forbidden in ('os.kill(', 'os.pwrite(', 'subprocess.', 'ctypes.', 'PTRACE_', 'O_RDWR', 'O_WRONLY'):
            self.assertNotIn(forbidden,source)
        self.assertIn("os.open(proc/'mem', os.O_RDONLY | os.O_CLOEXEC)",source)
        self.assertEqual(m.MAX_SECONDS,70)

    def test_report_does_not_include_raw_memory_or_paths(self):
        f=FakeMemory()
        data=json.dumps(f.snapshot()[3])
        self.assertNotIn('/dev/',data)
        self.assertEqual(set(json.loads(data)),{'enabled','rad_s'})


if __name__ == '__main__':
    unittest.main()
