# SPDX-License-Identifier: GPL-2.0-only
"""File-only replay model. No GUI, devices, networking or runtime writes."""
from bisect import bisect_right
from dataclasses import dataclass
import math
import statistics

from gamesir_imu_diagnostic import PROFILES, axis_profile_info, convert, replay_buffer
from gyro_reference import validate_samples

IDENTITY = (1., 0., 0., 0.)  # w, x, y, z; body -> initial reference frame
MAX_SAMPLES = 100_000


def multiply(a, b):
    w, x, y, z = a
    v, i, j, k = b
    return (w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
            w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v)


def inverse(q):
    # All stored orientations are unit quaternions.
    return (q[0], -q[1], -q[2], -q[3])


def rotation(vector):
    """Exponential of a body rotation vector in radians, not Euler angles."""
    angle = math.hypot(*vector)
    if angle < 1e-12:
        return IDENTITY
    gain = math.sin(angle / 2) / angle
    return (math.cos(angle / 2), *(v * gain for v in vector))


def rotate(q, vector):
    return multiply(multiply(q, (0., *vector)), inverse(q))[1:]


def relative(q, reference):
    return multiply(inverse(reference), q)


def rotation_degrees(q):
    """Shortest relative orientation distance, 0..180, NOT accumulated travel."""
    return math.degrees(2 * math.atan2(math.hypot(*q[1:]), abs(q[0])))


def crosshair(q, gain):
    """Screen normalized x/right, y/down. Positive body yaw points left.

    A 45-degree forward field each way at 1x. Clamp the visible indicator;
    never wrap a backward-facing ray into an apparently centered target.
    """
    if not math.isfinite(gain) or not .25 <= gain <= 4:
        raise ValueError('display gain must be between 0.25 and 4')
    x, y, z = rotate(q, (0., 1., 0.))
    yaw = math.atan2(x, y)
    pitch = math.atan2(z, math.hypot(x, y))
    px, py = gain * yaw / (math.pi/4), -gain * pitch / (math.pi/4)
    outside = y <= 0 or abs(px) > 1 or abs(py) > 1
    return max(-1., min(1., px)), max(-1., min(1., py)), outside


@dataclass(frozen=True)
class Frame:
    elapsed: float
    timestamp_ns: int
    number: int
    gyro_raw: tuple
    accel_raw: tuple
    body_dps: tuple
    body_rad_s: tuple
    orientation: tuple


@dataclass(frozen=True)
class Clip:
    frames: tuple
    times: tuple
    profile: int
    axis_profile: str
    median_dt_ms: float
    max_dt_ms: float
    wide_intervals: int

    @property
    def duration(self):
        return self.times[-1]

    @classmethod
    def from_samples(cls, samples, *, profile, axis_profile):
        if type(profile) is not int or profile not in PROFILES:
            raise ValueError('explicit experimental gain profile required')
        axis_profile_info(axis_profile)
        if len(samples) > MAX_SAMPLES:
            raise ValueError('replay limited to 100000 samples per capture')
        validate_samples(samples, 250_000_000)
        frames, q, previous = [], IDENTITY, None
        first_stamp = samples[0]['timestamp_ns']
        intervals = []
        for s in samples:
            values = convert(s['gyro_raw'], s['accel_raw'], profile,
                             axis_profile=axis_profile)['experimental_axes']
            dps = tuple(values['body_gyro_dps_xyz'])
            radians = tuple(values['body_gyro_rad_s_xyz'])
            if previous is not None:
                delta = s['timestamp_ns'] - previous.timestamp_ns
                intervals.append(delta)
                # Midpoint angular velocity in the body frame; right multiply.
                # Receive timestamps approximate sample time. No bias removal,
                # acceleration fusion or claim of calibrated/absolute attitude.
                increment = rotation(tuple((a+b)*.5*delta/1e9
                                           for a,b in zip(previous.body_rad_s, radians)))
                q = multiply(q, increment)
                norm = math.hypot(*q)
                q = tuple(x/norm for x in q)
            previous = Frame((s['timestamp_ns']-first_stamp)/1e9, s['timestamp_ns'],
                             s['sample_number'], tuple(s['gyro_raw']), tuple(s['accel_raw']),
                             dps, radians, q)
            frames.append(previous)
        median = statistics.median(intervals)
        return cls(tuple(frames), tuple(f.elapsed for f in frames), profile, axis_profile,
                   median/1e6, max(intervals)/1e6, sum(x > 2*median for x in intervals))

    @classmethod
    def load(cls, path, *, profile, axis_profile):
        # Checksummed files only. Recorded sysfs paths are metadata, never opened.
        samples, metadata = replay_buffer(path, axis_profile=axis_profile)
        return cls.from_samples(samples, profile=profile, axis_profile=axis_profile), metadata


class Playback:
    """Wall time advances the cursor only; orientation is precomputed once."""
    def __init__(self, clip):
        self.clip = clip
        self.position = 0.
        self.playing = False
        self.speed = 1.
        self.gain = 1.
        self.reference = IDENTITY

    @property
    def frame(self):
        i = max(0, bisect_right(self.clip.times, self.position) - 1)
        return self.clip.frames[i]

    @property
    def orientation(self):
        return relative(self.frame.orientation, self.reference)

    def seek(self, seconds):
        if not math.isfinite(seconds):
            raise ValueError('finite playback position required')
        self.position = max(0., min(self.clip.duration, seconds))
        if self.position >= self.clip.duration:
            self.playing = False

    def advance(self, wall_seconds):
        if not math.isfinite(wall_seconds) or wall_seconds < 0:
            raise ValueError('nonnegative finite wall time required')
        if self.playing:
            self.seek(self.position + wall_seconds*self.speed)

    def center(self):
        self.reference = self.frame.orientation

    def restart(self):
        self.playing = False
        self.reference = IDENTITY
        self.seek(0.)
