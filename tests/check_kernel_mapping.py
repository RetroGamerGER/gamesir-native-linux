#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compile the actual kernel pad adapter with fake input callbacks, no devices."""
import argparse
import ctypes as c
import hashlib
import json
import struct
import subprocess
import sys
from project_paths import PROJECT, BUILD, RESULTS, local_directory

sys.path.insert(0, str(PROJECT / "tools/offline"))
from gamesir_offline.protocol import decode_packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    source = (PROJECT / "kernel/gs_native_usb.c").read_text()
    start = source.index("static void gsn_pad(")
    end = source.index("\nstatic void gsn_neutral(", start)
    adapter = source[start:end]
    code = '''#include <linux/input-event-codes.h>
#include <string.h>
#include "gs_protocol.h"
#define ARRAY_SIZE(x) (sizeof(x)/sizeof((x)[0]))
#define BIT(x) (1u << (x))
struct input_dev { int unused; };
struct gsn_device { struct input_dev *input; };
static int keys[KEY_CNT], axes[ABS_CNT];
static void input_report_key(struct input_dev *d, unsigned int k, int v) { (void)d; keys[k]=v; }
static void input_report_abs(struct input_dev *d, unsigned int a, int v) { (void)d; axes[a]=v; }
static void input_sync(struct input_dev *d) { (void)d; }
''' + adapter + '''
int test_mapping(const unsigned char *data, unsigned int len) {
 struct gs_frame f; struct gsn_device g={0}; int kind=gs_decode(data,len,&f);
 memset(keys,0,sizeof(keys)); memset(axes,0,sizeof(axes));
 if(kind != GS_PAD_XINPUT && kind != GS_PAD_GIP) return -1;
 gsn_pad(&g,&f); return kind;
}
int test_key(unsigned int k) { return keys[k]; }
int test_axis(unsigned int k) { return axes[k]; }
'''
    file = BUILD / "mapping-fixture.c"
    file.write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                    "-I", str(PROJECT / "src"), str(file), str(PROJECT / "src/gs_protocol.c"),
                    "-o", str(BUILD / "mapping-fixture.so")], check=True, timeout=30)
    lib = c.CDLL(str(BUILD / "mapping-fixture.so"))
    lib.test_mapping.argtypes = [c.c_void_p, c.c_uint]
    lib.test_key.argtypes = [c.c_uint]
    lib.test_axis.argtypes = [c.c_uint]
    packets = []
    fixture = json.loads((PROJECT / "fixtures/sprint002-target.json").read_text())
    packets += [bytes.fromhex(case["record"]["data_hex"]) for case in fixture["cases"] if case["name"] in ("xinput", "gip")]
    # Independent single button bits plus axis/trigger endpoints, marked synthetic.
    for bit in range(16):
        d = bytearray(20); d[:2] = b"\x00\x14"; d[2:4] = (1 << bit).to_bytes(2, "little")
        d[4:6] = bytes((0, 255)); struct.pack_into("<4h", d, 6, -32768, 32767, -1, 0)
        packets.append(bytes(d))
        d = bytearray(36); d[:4] = b"\x20\x00\x01\x20"; d[4:6] = (1 << bit).to_bytes(2, "little")
        struct.pack_into("<2H4h", d, 6, 1023, 0, 32767, -32768, 0, -1)
        packets.append(bytes(d))
    capture_count = 0
    if args.capture:
        path = local_directory("capture_dir") / "derived/parser-records.jsonl"
        with path.open("rb") as data:
            assert hashlib.file_digest(data, "sha256").hexdigest() == fixture["source_records_sha256"]
        for line in path.open():
            r = json.loads(line)
            if r["status"] or r["capture_truncated"] or r["endpoint"] != "82":
                continue
            data = bytes.fromhex(r["data_hex"])
            if decode_packet(data).kind in ("x360_input", "gip_input_basic"):
                packets.append(data); capture_count += 1
        assert capture_count == 5244
    names = {2:"menu",3:"view",4:"a",5:"b",6:"x",7:"y",8:"up",9:"down",10:"left",11:"right",12:"lb",13:"rb",14:"ls",15:"rs"}
    keycodes = {"a":304,"b":305,"x":307,"y":308,"lb":310,"rb":311,"view":314,"menu":315,"home":316,"ls":317,"rs":318}
    for data in packets:
        ref = decode_packet(data)
        fields = ref.fields
        kind = lib.test_mapping(data, len(data))
        assert kind in (1, 2)
        buttons = (fields["buttons"] if kind == 2 else
                   {name:bool(int.from_bytes(data[4:6], "little") & (1 << bit)) for bit,name in names.items()})
        for name, code in keycodes.items():
            assert lib.test_key(code) == int(buttons.get(name, False)), (ref.kind,name,data.hex())
        sticks = list(fields["sticks_raw_i16"].values())
        expected = dict(zip([0,1,3,4], [sticks[0],~sticks[1],sticks[2],~sticks[3]]))
        triggers = ([(v*1023+127)//255 for v in fields["triggers_u8"].values()] if kind == 2 else list(fields["triggers_raw_u16"].values()))
        expected.update({2:triggers[0],5:triggers[1],16:int(buttons["right"])-int(buttons["left"]),17:int(buttons["down"])-int(buttons["up"])})
        for code,value in expected.items():
            assert lib.test_axis(code) == value,(ref.kind,code,value,data.hex())
    result = {"passed": True,"hardware_access": False,"method":"actual gsn_pad function compiled with fake input callbacks, independent Python packet reference",
              "packets":len(packets),"synthetic_packets":32,"capture_packets":capture_count,
              "limits":"does not execute kernel input core or URB callbacks"}
    name = "kernel-mapping-capture.json" if args.capture else "kernel-mapping-fixtures.json"
    (RESULTS / name).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
