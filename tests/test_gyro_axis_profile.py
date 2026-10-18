#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Offline profile/verified-replay tests; no live device or GUI access."""
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/imu'))
import gamesir_imu_diagnostic as diag
from gamesir_imu_stream import ScanDecoder, CHANNELS

PROFILE = diag.OBSERVED_AXIS_PROFILE


class AxisProfile(unittest.TestCase):
    def test_six_observed_directions_in_right_handed_body_frame(self):
        # Body X=right, Y=front, Z=face-up. Signs follow physical rotation,
        # not a relabelling of the arbitrary IIO x/y/z raw channel names.
        cases = [([0, 100, 0], [0, 0, 7]), ([0, -100, 0], [0, 0, -7]),
                 ([-100, 0, 0], [-7, 0, 0]), ([100, 0, 0], [7, 0, 0]),
                 ([0, 0, 100], [0, -7, 0]), ([0, 0, -100], [0, 7, 0])]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                v = diag.convert(raw, [1, 2, 8192], 2000, axis_profile=PROFILE)
                for actual, want in zip(v['experimental_axes']['body_gyro_dps_xyz'], expected):
                    self.assertAlmostEqual(actual, want)
                for actual, want in zip(v['experimental_axes']['body_gyro_rad_s_xyz'], expected):
                    self.assertAlmostEqual(actual, math.radians(want))
                self.assertEqual(v['gyro_raw'], raw)
                self.assertEqual(v['accel_raw'], [1, 2, 8192])
                self.assertEqual(v['test_values']['accel_g'], [1/8192, 2/8192, 1])

    def test_default_stays_wire_order_without_axis_selection(self):
        v = diag.convert([1, 2, 3], [4, 5, 6], 2000)
        self.assertNotIn('experimental_axes', v)
        for actual, expected in zip(v['test_values']['gyro_dps'], [.07, .14, .21]):
            self.assertAlmostEqual(actual, expected)

    def test_bias_is_in_wire_order_and_removed_before_permutation(self):
        v = diag.convert([100, 200, 300], [0, 8192, 0], 2000,
                         bias=[10, 20, 30], axis_profile=PROFILE)
        for actual, expected in zip(v['experimental_axes']['body_gyro_dps_xyz'], [6.3, -18.9, 12.6]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(v['gyro_raw'], [100, 200, 300])

    def test_int16_negative_extreme_does_not_overflow_on_sign_change(self):
        v = diag.convert([0, 0, -32768], [0, 8192, 0], 2000, axis_profile=PROFILE)
        self.assertAlmostEqual(v['experimental_axes']['body_gyro_dps_xyz'][1], 2293.76)

    def test_all_five_gains_remain_independent_explicit_choices(self):
        for profile, gain in diag.PROFILES.items():
            v = diag.convert([1600, 800, 400], [0, 0, 0], profile, axis_profile=PROFILE)
            self.assertEqual(v['experimental_axes']['body_gyro_dps_xyz'],
                             [1600*float(gain), -400*float(gain), 800*float(gain)])
        with self.assertRaises(TypeError):
            diag.convert([0, 0, 0], [0, 0, 0], axis_profile=PROFILE)

    def test_unknown_profile_is_not_a_fallback(self):
        for p in ('automatic', 'zzz', '', True):
            with self.subTest(p=p), self.assertRaises(ValueError):
                diag.convert([0, 0, 0], [0, 0, 0], 2000, axis_profile=p)

    def test_profile_metadata_cannot_enable_runtime_or_calibration(self):
        p = diag.axis_profile_info(PROFILE)
        for flag in ('scale_verified', 'physical_axis_mapping_verified', 'calibration_verified',
                     'sdl_runtime_enable', 'accelerometer_mapping_applied'):
            self.assertIs(p[flag], False)
        p['body_xyz_from_wire'][0]['sign'] = -1
        self.assertEqual(diag.axis_profile_info(PROFILE)['body_xyz_from_wire'][0]['sign'], 1)

    def test_norm_and_handedness_preserved(self):
        cross = lambda a,b: [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
        a,b = [3, -4, 7], [2, 1, -5]
        self.assertEqual(cross(diag.body_vector(a, PROFILE), diag.body_vector(b, PROFILE)),
                         diag.body_vector(cross(a,b), PROFILE))
        self.assertEqual(sum(x*x for x in a), sum(x*x for x in diag.body_vector(a, PROFILE)))


class CoherentReplay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.capture = self.root/'capture'
        self.capture.mkdir(mode=0o700)
        instance = 'synthetic-saved-iio:25:123'
        raw = b''.join(struct.pack('<6h4xQq', 0, 8192, 0, 100, 200, 300, n+1,
                                  1_000_000_000+n*16_000_000) for n in range(4))
        decoder = ScanDecoder(instance, 250_000_000, 'iio_buffer')
        rows = list(decoder.feed(raw));decoder.finish()
        self.files = {
            'scans.bin': raw,
            'observations.jsonl': ''.join(json.dumps(s)+'\n' for s in rows).encode(),
            'layout.json': json.dumps({'channels':list(CHANNELS),'scan_bytes':32,
                'counter_offset':16,'host_timestamp_offset':24,
                'metadata':{'clock':'monotonic','instance_id':instance}}).encode(),
            'report.json': json.dumps({'completed':True,'restored':True,'failure':None,
                'cleanup_errors':[], 'capture_started_monotonic_ns':999_000_000,
                'observations':4,'original_bytes':len(raw)}).encode(),
            'buffer-transaction.json': json.dumps({'restored':True,'errors':[],
                'before':{'directory':'synthetic-saved-iio','iio_identity':[25,123],
                'usb':{'vid':'3537','pid':'109c','interface_number':0,'driver':'gs_native'}}}).encode()}
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        for name,data in self.files.items():
            p=self.capture/name;p.write_bytes(data);p.chmod(0o600)
        p=self.capture/'SHA256SUMS'
        p.write_text(''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n'
                             for name,data in self.files.items()));p.chmod(0o600)

    def update_json(self,name,fn):
        v=json.loads(self.files[name]);fn(v);self.files[name]=json.dumps(v).encode();self.save()

    def test_binary_replayed_and_agrees_with_saved_json(self):
        rows,m=diag.replay_buffer(self.capture,axis_profile=PROFILE)
        self.assertEqual(len(rows),4)
        self.assertTrue(m['capture_sha256_verified'])
        self.assertEqual(rows[0]['gyro_raw'],[100,200,300])
        self.assertFalse(m['device_clock_verified'])

    def test_cli_end_to_end_offline_bundle_preserves_originals(self):
        before={p.name:p.read_bytes() for p in self.capture.iterdir()}
        out=self.root/'result'
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()), \
                patch.object(diag,'read_iio_snapshot',side_effect=AssertionError('hardware forbidden')):
            rc=diag.main(['replay-buffer','--experimental','--profile','2000','--axis-profile',PROFILE,
                          '--capture-dir',str(self.capture),'--output',str(out)])
        self.assertEqual(rc,0)
        report=json.loads((out/'report.json').read_text())
        self.assertTrue(report['completed'])
        self.assertFalse(report['profiles']['2000']['calibration_verified'])
        values=json.loads((out/'observations.jsonl').read_text().splitlines()[0])
        self.assertEqual(values['sample_number'],1)
        self.assertEqual(values['conversions']['2000']['gyro_raw'],[100,200,300])
        for actual,expected in zip(values['conversions']['2000']['experimental_axes']['body_gyro_dps_xyz'],[7,-21,14]):
            self.assertAlmostEqual(actual,expected)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.capture.iterdir()})
        for line in (out/'SHA256SUMS').read_text().splitlines():
            sha,name=line.split('  ',1);self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),sha)

    def test_checksum_corruption_is_rejected(self):
        (self.capture/'scans.bin').write_bytes(bytes(128))
        with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):
            diag.replay_buffer(self.capture,axis_profile=PROFILE)

    def test_failed_capture_is_not_an_accepted_profile_test(self):
        self.update_json('report.json',lambda v:v.update(completed=False,failure='device lost'))
        with self.assertRaisesRegex(ValueError,'does not verify'):
            diag.replay_buffer(self.capture,axis_profile=PROFILE)

    def test_zzz_has_no_automatic_profile_inheritance(self):
        self.update_json('buffer-transaction.json',lambda v:v['before']['usb'].update(pid='105e'))
        with self.assertRaisesRegex(ValueError,'3537:109c'):
            diag.replay_buffer(self.capture,axis_profile=PROFILE)

    def test_wrong_instance_and_layout_are_rejected(self):
        for field,value in [('instance_id','replacement'),('clock','realtime')]:
            with self.subTest(field=field):
                old=copy.deepcopy(self.files)
                self.update_json('layout.json',lambda v:v['metadata'].update({field:value}))
                with self.assertRaisesRegex(ValueError,'layout/instance mismatch'):
                    diag.replay_buffer(self.capture,axis_profile=PROFILE)
                self.files=old;self.save()

    def test_binary_json_disagreement_even_with_updated_hashes_fails(self):
        rows=[json.loads(x) for x in self.files['observations.jsonl'].splitlines()]
        rows[0]['gyro_raw'][0]=101
        self.files['observations.jsonl']=''.join(json.dumps(x)+'\n' for x in rows).encode();self.save()
        with self.assertRaisesRegex(ValueError,'disagreement'):
            diag.replay_buffer(self.capture,axis_profile=PROFILE)

    def test_gaps_counter_reset_and_partial_frame_are_rejected(self):
        original=self.files['scans.bin']
        for offset,fmt,value in ((48,'<Q',7),(56,'<q',2_000_000_000)):
            raw=bytearray(original);struct.pack_into(fmt,raw,offset,value)
            self.files['scans.bin']=bytes(raw);self.save()
            with self.assertRaises(ValueError):diag.replay_buffer(self.capture,axis_profile=PROFILE)
        self.files['scans.bin']=original[:-1];self.save()
        with self.assertRaisesRegex(ValueError,'incomplete'):
            diag.replay_buffer(self.capture,axis_profile=PROFILE)

    def test_no_live_axis_profile_cli_was_added(self):
        with redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
            diag.cli_parser().parse_args(['observe-iio','--experimental','--profile','2000',
                '--axis-profile',PROFILE,'--iio-dir','unused','--output','unused'])

    def test_malformed_saved_metadata_fails_before_output(self):
        original=copy.deepcopy(self.files)
        for name, value in [('report.json', []), ('layout.json', []),
                            ('buffer-transaction.json', {'restored':True,'errors':[], 'before':None})]:
            with self.subTest(name=name):
                self.files=copy.deepcopy(original)
                self.files[name]=json.dumps(value).encode();self.save()
                with self.assertRaises(ValueError):
                    diag.replay_buffer(self.capture,axis_profile=PROFILE)


if __name__=='__main__':
    unittest.main()
