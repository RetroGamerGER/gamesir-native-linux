#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Optional file-only check of pinned Eden methods; no download/app execution.

The GPL-3.0-or-later reference is supplied privately and is NOT copied into
our GPL-2.0-only project or any distributable. Only a temporary test harness
is compiled. This is not an emulator/game acceptance test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from project_paths import BUILD, RESULTS

EXPECTED = 'ff6037c3d2cea0f590053f5517672a0f89d4e17f3c58b13fee1076048d49bb82'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', type=Path, required=True)
a = p.parse_args()
assert a.source.is_file() and not a.source.is_symlink()
data = a.source.read_bytes()
assert hashlib.sha256(data).hexdigest() == EXPECTED, 'Unreviewed Eden source'
s = data.decode()
start = s.index('    bool HasMotion() const {')
stop = s.index('    const BasicMotion& GetMotion()', start)
methods = s[start:stop]
code = '''#include <cassert>
#include <cmath>
#include <mutex>
#include <numbers>
#include <cstdint>
using u64=uint64_t; using f32=float;
enum {SDL_SENSOR_ACCEL=1, SDL_SENSOR_GYRO=2};
struct SDL_GamepadSensorEvent { u64 timestamp, sensor_timestamp; int sensor; float data[3]; };
struct BasicMotion { float accel_x=0,accel_y=0,accel_z=0,gyro_x=0,gyro_y=0,gyro_z=0; u64 delta_timestamp=0; };
struct Checked {
 std::mutex mutex; bool has_gyro=true,has_accel=false; u64 last_motion_update=0;
 unsigned motion_error_count=0,restarts=0; BasicMotion motion;
 void EnableMotion() {restarts++;}
''' + methods + '''};
int main() {
 for(int axis=0;axis<3;axis++) for(int sign : {-1,1}) {
  Checked c; assert(c.HasMotion());
  SDL_GamepadSensorEvent e{1000000,16000000,SDL_SENSOR_GYRO,{}};
  e.data[axis]=sign*100.0f*0.07f*std::numbers::pi_v<float>/180;
  assert(!c.UpdateMotion(e));
  e.timestamp+=16000000; e.sensor_timestamp+=16000000;
  assert(c.UpdateMotion(e)); assert(c.motion.delta_timestamp==16000);
  const float out[]={c.motion.gyro_x,c.motion.gyro_z,-c.motion.gyro_y};
  for(int i=0;i<3;i++)assert(std::abs(out[i]-(i==axis?sign*7.0f/360:0))<1e-7);
  assert(!c.motion.accel_x && !c.motion.accel_y && !c.motion.accel_z);
  assert(!c.UpdateMotion(e)); e.sensor_timestamp--; assert(!c.UpdateMotion(e));
 }
 Checked host;
 SDL_GamepadSensorEvent e{100000000,0,SDL_SENSOR_GYRO,{0,1,0}};
 assert(!host.UpdateMotion(e)); e.timestamp+=16000000;
 assert(host.UpdateMotion(e) && host.motion.delta_timestamp==16000);
 // Existing Eden limitation: switching from initial host time to a smaller
 // device clock is rejected until it catches up. Record, don't hide it.
 Checked late; e={100000000000,0,SDL_SENSOR_GYRO,{0,1,0}};
 assert(!late.UpdateMotion(e)); e.sensor_timestamp=16000000;
 assert(!late.UpdateMotion(e));
}
'''
out = BUILD / 'eden-motion'
out.mkdir(parents=True, exist_ok=True)
f = out / 'reference-test.cpp'; f.write_text(code)
subprocess.run(['clang++','-std=c++20','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all',
                str(f),'-o',str(out/'test')],check=True)
subprocess.run([str(out/'test')],check=True)
RESULTS.mkdir(exist_ok=True)
report={'passed':True,'source_sha256':EXPECTED,'commit':'e0d47f2790e3f758fa2188926a0bb2f56af6b310',
 'hardware_access':False,'emulator_executed':False,'code_vendored':False,
 'cases':['gyro-only capability','six signed directions','rad/s to revolutions/s',
          'nanoseconds to microseconds','duplicate/backward rejection','host-clock fallback'],
 'known_limit':'Eden mixes initial host-time with later sensor-time; late hotplug can reject samples until the sensor clock catches up. Start the emulator after native startup for the first approved test.',
 'limits':['Only the two actual input methods, not the complete emulator or sensor fusion.',
           'No accelerometer drift correction is provided by the gyro-only profile.']}
(RESULTS/'eden-motion.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
