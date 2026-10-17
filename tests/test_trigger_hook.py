#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Real ELF interposition with synthetic SDL/libusb libraries; no device opens.

Extends the isolated Forza bridge's explicit-handle and USB-filter tests.
No SDL initialization, installed broker import, game or hardware is used.
"""
import os
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKET = struct.Struct("<4sHHIIQQIiHHI64s16s")
TOKEN = "0123456789abcdef0123456789abcdef"
FAKE_SDL = r"""#include <stdint.h>
#ifndef RESULT
#define RESULT -77
#endif
static int invalidated;
void SDL_TestInvalidate(void) { invalidated=1; }
uint16_t SDL_JoystickGetVendor(void *j) { return invalidated || j == (void*)2 ? 0x045e : 0x3537; }
uint16_t SDL_JoystickGetProduct(void *j) { return j == (void*)3 ? 0x105e : 0x109c; }
int32_t SDL_JoystickInstanceID(void *j) { return invalidated || j == (void*)6 ? -1 : 7; }
#ifndef NO_PATH
const char *SDL_JoystickPath(void *j) {
    if(j == (void*)4) return "/dev/input/event18";
    if(invalidated || j == (void*)5) return 0;
    return "/dev/input/event17";
}
#endif
int SDL_JoystickRumbleTriggers(void *j,uint16_t l,uint16_t r,uint32_t d) {
    (void)j;(void)l;(void)r;(void)d;return RESULT;
}
void SDL_JoystickClose(void *j) { (void)j; }
"""
PROBE = r"""
#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <unistd.h>
typedef int (*rumble_fn)(void*,uint16_t,uint16_t,uint32_t);
static void *library;
static void *worker(void *unused) {
    (void)unused;
    rumble_fn f = (rumble_fn)dlsym(library,"SDL_JoystickRumbleTriggers");
    for(int i=0;i<20;i++) if(f((void*)1,100,200,300)) return (void*)1;
    return 0;
}
int main(int argc,char **argv) {
    if(argc < 3) return 90;
    library=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
    if(!library) { fprintf(stderr,"%s\n",dlerror()); return 91; }
    rumble_fn f=(rumble_fn)dlsym(library,"SDL_JoystickRumbleTriggers");
    void (*c)(void*)=(void (*)(void*))dlsym(library,"SDL_JoystickClose");
    if(!f||!c) return 92;
    if(!strcmp(argv[2],"sequence")) {
        printf("%d ",f((void*)1,65535,12345,4321));
        printf("%d ",f((void*)1,0,0,1000));
        printf("%d\n",f((void*)1,7,8,0xffffffff));
        c((void*)1);
    } else if(!strcmp(argv[2],"one")) {
        printf("%d\n",f((void*)(uintptr_t)strtoul(argv[3],0,10),1,2,100));
    } else if(!strcmp(argv[2],"two")) {
        void *other=dlopen(argv[3],RTLD_NOW|RTLD_LOCAL);
        if(!other) return 93;
        rumble_fn g=(rumble_fn)dlsym(other,"SDL_JoystickRumbleTriggers");
        printf("%d %d\n",f((void*)1,1,2,3),g((void*)1,1,2,3));
        dlclose(other);
        /* The hook's retained library reference makes these callbacks safe. */
        dlclose(library);
        c((void*)1);
    } else if(!strcmp(argv[2],"threads")) {
        pthread_t threads[8];
        for(int i=0;i<8;i++) if(pthread_create(&threads[i],0,worker,0)) return 94;
        for(int i=0;i<8;i++) { void *r; pthread_join(threads[i],&r); if(r) return 95; }
        c((void*)1);
    } else if(!strcmp(argv[2],"fork")) {
        if(f((void*)1,1,2,3)) return 96;
        pid_t child=fork();
        if(child<0) return 97;
        if(!child) _exit(f((void*)1,2,3,4)==-1 ? 0 : 99);
        int status;waitpid(child,&status,0);
        if(!WIFEXITED(status)||WEXITSTATUS(status)) return 98;
        printf("%d\n",f((void*)1,3,4,5));c((void*)1);
    } else if(!strcmp(argv[2],"invalid-close")||!strcmp(argv[2],"invalid-effect")) {
        if(f((void*)1,1,2,0xffffffff)) return 101;
        void (*invalidate)(void)=(void (*)(void))dlsym(library,"SDL_TestInvalidate");
        if(!invalidate) return 102;
        invalidate();
        if(!strcmp(argv[2],"invalid-effect")) printf("%d\n",f((void*)1,2,3,0xffffffff));
        c((void*)1);
    } else if(!strcmp(argv[2],"no-retry")) {
        int first=f((void*)1,1,2,3);
        int s=socket(AF_UNIX,SOCK_STREAM|SOCK_NONBLOCK,0);
        struct sockaddr_un a={.sun_family=AF_UNIX};
        strcpy(a.sun_path,getenv("GSN_TRIGGER_SOCKET"));
        if(bind(s,(struct sockaddr*)&a,sizeof(a))||listen(s,1)) return 100;
        int second=f((void*)1,2,3,4);
        int accepted=accept(s,0,0);
        printf("%d %d %d\n",first,second,accepted);
        if(accepted>=0) close(accepted);
        close(s);unlink(a.sun_path);
    }
    return 0;
}
"""
FAKE_USB = r"""
#include <libusb-1.0/libusb.h>
int libusb_get_device_descriptor(libusb_device *d,struct libusb_device_descriptor *v) {
    v->idVendor=d==(void*)2 ? 0x045e : 0x3537;
    v->idProduct=d==(void*)3 ? 0x105e : 0x109c;return 0;
}
uint8_t libusb_get_bus_number(libusb_device *d) { return d==(void*)4 ? 9 : 8; }
uint8_t libusb_get_device_address(libusb_device *d) { return d==(void*)5 ? 25 : 24; }
int libusb_open(libusb_device *d,libusb_device_handle **h) { (void)d;*h=(void*)123;return 42; }
"""
USB_PROBE = r"""
#include <dlfcn.h>
#include <stdio.h>
#include <libusb-1.0/libusb.h>
int main(void) {
    void *s=dlopen("libusb-1.0.so.0",RTLD_NOW);
    int (*f)(libusb_device*,libusb_device_handle**)=dlsym(s,"libusb_open");
    if(!f) return 90;
    for(unsigned long i=1;i<=5;i++) {
        libusb_device_handle *h=(void*)999;
        int result=libusb_open((void*)i,&h);
        printf("%d:%d ",result,h==0);
        printf("%d ",f((void*)i,&h));
    }
    return 0;
}
"""


class Hook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "build").mkdir(exist_ok=True)
        # AF_UNIX has a small fixed pathname bound, independent of checkout length.
        cls.temp = tempfile.TemporaryDirectory(prefix="gsn-hook-")
        cls.path = Path(cls.temp.name)
        cls.shim = cls.path / "libgamesir-trigger-sdl2.so"
        cc = os.environ.get("CC", "cc")

        def compile_file(name, source, arguments):
            path = cls.path / name
            path.write_text(source)
            result = subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", str(path), *arguments],
                                    capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr)

        subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", "-O2",
                        str(ROOT / "tools/trigger_bridge/sdl2_hook.c"), "-o", str(cls.shim),
                        "-ldl", "-pthread", "-Wl,-z,relro,-z,now"], check=True,
                       capture_output=True, text=True)
        for name, arguments in (("libSDL2-fake.so", []), ("libSDL3-fake.so", []),
                                ("libSDL2-other.so", ["-DRESULT=-88"]),
                                ("libSDL2-no-path.so", ["-DNO_PATH"])):
            compile_file(name + ".c", FAKE_SDL, ["-shared", "-fPIC", *arguments, "-o", str(cls.path / name)])
        compile_file("probe.c", PROBE, ["-o", str(cls.path / "probe"), "-ldl", "-pthread"])
        compile_file("usb.c", FAKE_USB, ["-shared", "-fPIC", "-Wl,-soname,libusb-1.0.so.0",
                                        "-o", str(cls.path / "libusb-1.0.so.0")])
        compile_file("usb-probe.c", USB_PROBE, ["-o", str(cls.path / "usb-probe"), "-L" + str(cls.path),
                                              "-Wl,-rpath," + str(cls.path), "-l:libusb-1.0.so.0", "-ldl"])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def environment(self, **updates):
        env = dict(os.environ)
        for key in tuple(env):
            if key.startswith("GSN_TRIGGER_") or key in ("LD_PRELOAD", "LD_LIBRARY_PATH"):
                env.pop(key)
        env.update(LD_PRELOAD=str(self.shim), GSN_TRIGGER_SOCKET=str(self.path / "events.sock"),
                   GSN_TRIGGER_SOURCE="/dev/input/event17", GSN_TRIGGER_USB_BUS="8",
                   GSN_TRIGGER_USB_ADDRESS="24", GSN_TRIGGER_SESSION=TOKEN)
        env.update(updates)
        return env

    def run_probe(self, mode="sequence", library="libSDL2-fake.so", extra=(), env=None, capture=True):
        path = self.path / "events.sock"
        path.unlink(missing_ok=True)
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            if capture:
                server.bind(str(path))
                server.listen()
                server.settimeout(1)
            started = time.monotonic_ns()
            result = subprocess.run([str(self.path / "probe"), str(self.path / library), mode, *extra],
                                    env=env or self.environment(), check=True, capture_output=True,
                                    text=True, timeout=5)
            finished = time.monotonic_ns()
            packets = []
            if capture:
                try:
                    connection, _ = server.accept()
                except TimeoutError:
                    connection = None
                if connection:
                    with connection:
                        data = bytearray()
                        while chunk := connection.recv(65536):
                            data.extend(chunk)
                    self.assertEqual(len(data) % PACKET.size, 0)
                    packets = [PACKET.unpack(data[i:i + PACKET.size])
                               for i in range(0, len(data), PACKET.size)]
            path.unlink(missing_ok=True)
        return result.stdout.strip(), packets, started, finished

    def test_versioned_wire_stops_close_source_timestamp_and_uint32_duration(self):
        result, packets, start, end = self.run_probe()
        self.assertEqual(result, "0 0 0")
        self.assertEqual(len(packets), 4)
        for sequence, packet in enumerate(packets, 1):
            magic, version, kind, size, reserved, seq, timestamp, pid, instance, left, right, duration, path, session = packet
            self.assertEqual((magic, version, size, reserved), (b"GST2", 2, 128, 0))
            self.assertEqual(seq, sequence)
            self.assertLessEqual(start, timestamp)
            self.assertLessEqual(timestamp, end)
            self.assertGreater(pid, 0)
            self.assertEqual(instance, 7)
            self.assertEqual(path, b"/dev/input/event17" + bytes(46))
            self.assertEqual(session, bytes.fromhex(TOKEN))
        self.assertEqual(packets[0][9:12], (65535, 12345, 4321))
        self.assertEqual(packets[1][9:12], (0, 0, 1000))
        self.assertEqual(packets[2][9:12], (7, 8, 0xffffffff))
        self.assertEqual(packets[3][2], 2)
        self.assertEqual(packets[3][9:12], (0, 0, 0))

    def test_other_controller_variant_wrong_path_and_missing_identity_pass_through(self):
        for identity in range(2, 7):
            with self.subTest(identity=identity):
                result, packets, _, _ = self.run_probe("one", extra=(str(identity),))
                self.assertEqual((result, packets), ("-77", []))

    def test_sdl3_and_sdl2_without_path_are_not_intercepted(self):
        for library in ("libSDL3-fake.so", "libSDL2-no-path.so"):
            with self.subTest(library=library):
                result, packets, _, _ = self.run_probe(library=library)
                self.assertEqual((result, packets), ("-77 -77 -77", []))

    def test_second_library_retains_original_and_first_stays_pinned(self):
        result, packets, _, _ = self.run_probe("two", extra=(str(self.path / "libSDL2-other.so"),))
        self.assertEqual(result, "0 -88")
        self.assertEqual([packet[2] for packet in packets], [1, 2])

    def test_concurrent_handle_lookups_have_unique_ordered_sequences(self):
        _, packets, _, _ = self.run_probe("threads")
        self.assertEqual(len(packets), 161)
        self.assertEqual([packet[5] for packet in packets], list(range(1, 162)))
        self.assertEqual(packets[-1][2], 2)

    def test_fork_cannot_inherit_the_connected_motor_producer(self):
        result, packets, _, _ = self.run_probe("fork")
        self.assertEqual(result, "0")
        self.assertEqual([packet[5] for packet in packets], [1, 2, 3])
        self.assertEqual(len({packet[7] for packet in packets}), 1)

    def test_close_preserves_stop_when_sdl_invalidates_device_metadata(self):
        _, packets, _, _ = self.run_probe("invalid-close")
        self.assertEqual([packet[2] for packet in packets], [1, 2])
        self.assertEqual(packets[-1][8:12], (7, 0, 0, 0))

    def test_metadata_loss_closes_lease_without_competing_original_output(self):
        result, packets, _, _ = self.run_probe("invalid-effect")
        self.assertEqual(result, "-1")
        self.assertEqual([packet[2] for packet in packets], [1])

    def test_failed_transport_never_retries_or_uses_original_trigger_output(self):
        result, packets, _, _ = self.run_probe("no-retry", capture=False)
        self.assertEqual((result, packets), ("-1 -1 -1", []))

    def test_incomplete_or_invalid_activation_is_inert(self):
        changes = (dict(GSN_TRIGGER_SOCKET=""), dict(GSN_TRIGGER_SESSION="0" * 32),
                   dict(GSN_TRIGGER_SESSION="G" * 32), dict(GSN_TRIGGER_USB_BUS="0"),
                   dict(GSN_TRIGGER_USB_ADDRESS="128"), dict(GSN_TRIGGER_SOURCE="/dev/input/event017"))
        for change in changes:
            with self.subTest(change=change):
                result, packets, _, _ = self.run_probe(env=self.environment(**change))
                self.assertEqual((result, packets), ("-77 -77 -77", []))

    def test_usb_filter_requires_exact_authorized_bus_address_and_native_vid_pid(self):
        env = self.environment()
        result = subprocess.run([str(self.path / "usb-probe")], env=env, check=True,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.stdout.strip(), "-3:1 -3 42:0 42 42:0 42 42:0 42 42:0 42")
        env.pop("GSN_TRIGGER_SESSION")
        result = subprocess.run([str(self.path / "usb-probe")], env=env, check=True,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.stdout.strip(), "42:0 42 42:0 42 42:0 42 42:0 42 42:0 42")


if __name__ == "__main__":
    unittest.main()
