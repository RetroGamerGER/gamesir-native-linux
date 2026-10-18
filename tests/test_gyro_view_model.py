#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Synthetic offline orientation and playback regression tests."""
import copy
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/imu'))
import gamesir_imu_diagnostic as diag
from gyro_view_model import (Clip, Playback, IDENTITY, rotation, rotate, multiply,
                             relative, crosshair, rotation_degrees)
import test_gyro_axis_profile as capture_fixture


def samples(raw=(0, 1000, 0), count=101):
    return [dict(timestamp_ns=1_000_000_000+i*10_000_000, sample_number=i+1,
                 gyro_raw=list(raw), accel_raw=[0, 8192, 0], coherent=True,
                 timebase='host_monotonic_receive', source_kind='synthetic',
                 instance_id='synthetic-test') for i in range(count)]


def clip(rows=None):
    return Clip.from_samples(rows if rows is not None else samples(), profile=2000,
                             axis_profile=diag.OBSERVED_AXIS_PROFILE)


class Orientation(unittest.TestCase):
    def assertVector(self, actual, expected):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=10)

    def test_exact_quarter_turns_and_noncommuting_body_composition(self):
        x = rotation((math.pi/2, 0, 0))
        z = rotation((0, 0, math.pi/2))
        self.assertVector(rotate(z, (0, 1, 0)), (-1, 0, 0))
        self.assertVector(rotate(x, (0, 1, 0)), (0, 0, 1))
        self.assertVector(rotate(multiply(z, x), (0, 1, 0)), (0, 0, 1))
        self.assertVector(rotate(multiply(x, z), (0, 1, 0)), (-1, 0, 0))

    def test_constant_wire_rotation_uses_sample_timestamps(self):
        c = clip()
        self.assertAlmostEqual(rotation_degrees(c.frames[-1].orientation), 70.)
        self.assertVector(rotate(c.frames[-1].orientation, (0, 1, 0)),
                          (-math.sin(math.radians(70)), math.cos(math.radians(70)), 0))
        self.assertEqual(c.median_dt_ms, 10)

    def test_midpoint_integrates_linear_rate(self):
        rows = samples()
        for i, row in enumerate(rows):
            row['gyro_raw'][1] = 10*i
        self.assertAlmostEqual(rotation_degrees(clip(rows).frames[-1].orientation), 35.)

    def test_stream_composes_successive_body_axes_not_world_axes(self):
        rows=samples(count=5)
        for i,row in enumerate(rows):
            row['timestamp_ns']=1_000_000_000+i*100_000_000
            row['gyro_raw']=[0,0,0]
        rows[1]['gyro_raw']=[9000,0,0]  # triangular X pulse, 63 degrees
        rows[3]['gyro_raw']=[0,9000,0]  # then body Z, 63 degrees
        a=math.radians(63)
        # R_X(a) R_Z(a) * forward; independent matrix-derived expectation.
        expected=(-math.sin(a),math.cos(a)**2,math.cos(a)*math.sin(a))
        self.assertVector(rotate(clip(rows).frames[-1].orientation,(0,1,0)),expected)

    def test_all_six_signs_have_physical_directions(self):
        for raw, axis, sign in [((1000,0,0),0,1), ((-1000,0,0),0,-1),
                                ((0,1000,0),2,1), ((0,-1000,0),2,-1),
                                ((0,0,1000),1,-1), ((0,0,-1000),1,1)]:
            with self.subTest(raw=raw):
                q=clip(samples(raw)).frames[-1].orientation
                expected=[0.,0.,0.];expected[axis]=sign*math.radians(70)
                self.assertVector(q, rotation(expected))

    def test_quaternions_stay_unit_and_return_to_zero(self):
        rows=samples(count=10001)
        for i,row in enumerate(rows):
            row['gyro_raw'][1]=1000 if i < 5000 else (-1000 if i > 5000 else 0)
        c=clip(rows)
        for frame in c.frames:
            self.assertAlmostEqual(math.hypot(*frame.orientation), 1.)
        self.assertAlmostEqual(rotation_degrees(c.frames[-1].orientation),0.,places=8)

    def test_center_and_gain_do_not_modify_source_or_calibration(self):
        rows=samples();original=copy.deepcopy(rows);c=clip(rows);b=Playback(c)
        b.seek(.5);q=b.frame.orientation;b.center()
        self.assertVector(b.orientation, IDENTITY)
        b.gain=4.;crosshair(b.orientation,b.gain)
        self.assertEqual(q,b.frame.orientation)
        self.assertEqual(c.profile,2000)
        self.assertEqual(rows,original)
        self.assertEqual(c.frames[0].accel_raw,(0,8192,0))

    def test_crosshair_gain_sign_and_out_of_view(self):
        q=rotation((0,0,math.radians(10)))
        x,y,out=crosshair(q,1.)
        self.assertLess(x,0);self.assertAlmostEqual(y,0);self.assertFalse(out)
        self.assertAlmostEqual(crosshair(q,2.)[0],2*x)
        self.assertLess(crosshair(rotation((math.radians(10),0,0)),1.)[1],0)
        self.assertTrue(crosshair(rotation((0,0,math.pi)),1.)[2])
        for gain in (0,5,float('nan')):
            with self.assertRaises(ValueError):crosshair(q,gain)

    def test_rotation_distance_is_shortest_not_total_travel(self):
        self.assertAlmostEqual(rotation_degrees(rotation((0,0,math.radians(270)))),90)
        self.assertVector(relative(rotation((1,0,0)),rotation((1,0,0))), IDENTITY)

    def test_broken_stream_rejected_instead_of_skipped_or_interpolated(self):
        for mutate in (lambda r:r[20].update(timestamp_ns=r[19]['timestamp_ns']),
                       lambda r:r[20].update(timestamp_ns=r[19]['timestamp_ns']+300_000_000),
                       lambda r:r[20].update(sample_number=200),
                       lambda r:r[20].update(instance_id='replacement'),
                       lambda r:r[20].update(coherent=False),
                       lambda r:r[20].update(gyro_raw=[32767,0,0])):
            rows=samples();mutate(rows)
            with self.assertRaises(ValueError):clip(rows)

    def test_wider_intervals_reported_without_inventing_packet_loss(self):
        rows=samples()
        for r in rows[50:]:r['timestamp_ns']+=15_000_000
        c=clip(rows)
        self.assertEqual(c.wide_intervals,1);self.assertEqual(c.max_dt_ms,25)

    def test_profile_is_explicit_and_no_automatic_guess(self):
        for profile in (None, True, 2010):
            with self.assertRaises(ValueError):
                Clip.from_samples(samples(),profile=profile,axis_profile=diag.OBSERVED_AXIS_PROFILE)
        for profile,gain in diag.PROFILES.items():
            c=Clip.from_samples(samples(),profile=profile,axis_profile=diag.OBSERVED_AXIS_PROFILE)
            self.assertAlmostEqual(rotation_degrees(c.frames[-1].orientation),1000*float(gain))


class Replay(unittest.TestCase):
    def test_playback_speed_affects_cursor_not_orientation(self):
        c=clip();a=Playback(c);b=Playback(c)
        a.playing=b.playing=True;b.speed=4
        a.advance(.4);b.advance(.1)
        self.assertEqual(a.frame,b.frame)
        a.seek(.1);a.seek(.4)
        self.assertEqual(a.frame,b.frame)

    def test_end_pause_restart_and_no_extrapolation(self):
        b=Playback(clip());self.assertFalse(b.playing)
        b.playing=True;b.advance(100)
        self.assertFalse(b.playing);self.assertEqual(b.position,b.clip.duration)
        end=b.frame;b.advance(10);self.assertEqual(end,b.frame)
        b.center();b.restart();self.assertEqual(b.position,0)
        self.assertEqual(b.reference,IDENTITY);self.assertFalse(b.playing)
        for elapsed in (-1,float('inf')):
            with self.assertRaises(ValueError):b.advance(elapsed)
        with self.assertRaises(ValueError):b.seek(float('nan'))

    def test_saved_bundle_uses_existing_validation_and_never_live_metadata(self):
        fixture=capture_fixture.CoherentReplay();fixture.setUp()
        try:
            before={p.name:p.read_bytes() for p in fixture.capture.iterdir()}
            with patch.object(diag,'read_iio_snapshot',side_effect=AssertionError('no hardware')):
                c,m=Clip.load(fixture.capture,profile=2000,axis_profile=diag.OBSERVED_AXIS_PROFILE)
            self.assertEqual(len(c.frames),4);self.assertTrue(m['capture_sha256_verified'])
            self.assertEqual(before,{p.name:p.read_bytes() for p in fixture.capture.iterdir()})
            (fixture.capture/'scans.bin').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                Clip.load(fixture.capture,profile=2000,axis_profile=diag.OBSERVED_AXIS_PROFILE)
        finally:fixture.tearDown()


if __name__=='__main__':
    unittest.main()
