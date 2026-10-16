#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compare small saved target packets with the preserved C/Python decoders."""
import ctypes as c
import json
import subprocess
import sys

from project_paths import PROJECT, BUILD, RESULTS
from check_capture_core import Frame

sys.path.insert(0, str(PROJECT / "tools/offline"))
from gamesir_offline.protocol import decode_packet


def main():
    BUILD.mkdir(exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-O2", "-shared", "-fPIC", str(PROJECT / "src/gs_protocol.c"),
                    "-o", str(BUILD / "fixtures.so")], check=True)
    lib = c.CDLL(str(BUILD / "fixtures.so"))
    lib.gs_decode.argtypes = [c.c_void_p, c.c_size_t, c.POINTER(Frame)]
    lib.gs_motor_packet.argtypes = [c.c_void_p, c.c_uint8, c.c_void_p]
    lib.gs_transition.argtypes = [c.c_void_p, c.c_uint]
    lib.gs_gip_init.argtypes = [c.c_void_p, c.c_uint8, c.c_uint]
    fixture = json.loads((PROJECT / "fixtures/sprint002-target.json").read_text())
    assert fixture["origin"] == "real_saved_target_only_excerpt_not_synthetic"
    names = set()
    for case in fixture["cases"]:
        r = case["record"]
        assert r["device"]["vid"] == "3537" and r["device"]["pid"] in ("100a", "109c")
        assert r["status"] == 0 and r["stage"] == "complete" and not r["capture_truncated"]
        data = bytes.fromhex(r["data_hex"])
        assert len(data) == r["reported_length"]
        old = decode_packet(data, endpoint=int(r["endpoint"], 16))
        assert old.disposition == "decoded", case["name"]
        frame = Frame()
        if case["name"] == "imu_nonzero":
            assert lib.gs_decode(data, len(data), c.byref(frame)) == 3
            assert list(frame.gyro) == old.fields["gyro_raw_i16"] == case["expected"]["gyro_raw"]
            assert list(frame.accel) == old.fields["accel_raw_i16"] == case["expected"]["accel_raw"]
            assert list(frame.extras) == list(data[57:59])
        elif case["name"] in ("xinput", "gip"):
            kind = lib.gs_decode(data, len(data), c.byref(frame))
            assert kind == (2 if case["name"] == "xinput" else 1)
            assert list(frame.sticks) == list(old.fields["sticks_raw_i16"].values())
            triggers = ([(v * 1023 + 127) // 255 for v in old.fields["triggers_u8"].values()]
                        if kind == 2 else list(old.fields["triggers_raw_u16"].values()))
            assert list(frame.triggers) == triggers
        else:
            assert old.kind == "gip_four_motor_output"
            values = bytes(old.fields["motor_percentages"].values())
            index = ["left_trigger", "right_trigger", "left_grip", "right_grip"].index(case["name"])
            assert values[index] > 0 and sum(v != 0 for v in values) == 1
            out = c.create_string_buffer(13)
            assert lib.gs_motor_packet(out, data[2], values) == 13
            assert out.raw == data
        names.add(case["name"])
    assert names == {"xinput", "gip", "imu_nonzero", "left_trigger", "right_trigger", "left_grip", "right_grip"}
    assert len(fixture["transition_packets"]) == 9
    for step, packet in enumerate(fixture["transition_packets"]):
        out = c.create_string_buffer(8)
        assert packet["step"] == step and lib.gs_transition(out, step) == 8
        assert out.raw.hex() == packet["data_hex"]
    assert len(fixture["gip_initialization_packets"]) == 3
    for case in fixture["gip_initialization_packets"]:
        data = bytes.fromhex(case["data_hex"])
        out = c.create_string_buffer(64)
        assert lib.gs_gip_init(out, data[2], case["step"]) == len(data)
        assert out.raw[:len(data)] == data
    result = {"gip_initialization_packets": 3, "passed": True, "hardware_access": False, "packet_cases": len(names),
              "transition_packets": 9, "source_capture_sha256": fixture["source_capture_sha256"],
              "scope": "small saved target-only regression selection; no calibration claim"}
    (RESULTS / "protocol-fixtures.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
