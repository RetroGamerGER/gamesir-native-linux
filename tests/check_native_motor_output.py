#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Actual kernel motor send/flush functions with synthetic clock and USB only."""
import hashlib
import json
import re
import subprocess

from project_paths import PROJECT, BUILD, RESULTS


SHIM = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gs_runtime.h"

typedef gs_u8 u8;
typedef gs_u64 u64;
struct fake_usb_device { int dev; };
struct fake_interface { int condition; };
/* This isolated motor fixture never owns an in-progress bootstrap. The real
 * producer latch is covered by the adapter/startup harness, not this shim.
 */
struct gsn_boot { int lock, core; };
#define USB_INTERFACE_BOUND 1
#define READ_ONCE(x) (x)
#define smp_load_acquire(ptr) (*(ptr))
#define spin_lock(lock) do { (void)(lock); assert(0 && "unexpected bootstrap lock"); } while (0)
#define spin_unlock(lock) do { (void)(lock); assert(0 && "unexpected bootstrap unlock"); } while (0)
struct gsn_device {
    struct gs_runtime rt;
    struct fake_usb_device *udev;
    struct fake_interface *intf;
    u8 *tx_buf;
    u8 sequence;
    int lock, service, stop_error;
    bool stopping, output_used, stop_sent, boot_handoff;
    struct gsn_boot *boot;
};

static void gs_boot_abort(int *core, int error)
{
    (void)core; (void)error;
    assert(0 && "motor-only fixture reached bootstrap producer latch");
}

static int spin_depth, io_depth, scheduled, warnings;
static unsigned int native_pid;
static int usb_calls, usb_return, usb_actual = 13;
static unsigned int clock_reads;
static u64 clock_values[2];
static u8 usb_bytes[8][64];
static int usb_lengths[8];
static struct fake_usb_device fake_device;
static struct fake_interface fake_intf;

#define spin_lock_irqsave(lock, flags) do { \
    (void)(lock); (flags) = 0; assert(spin_depth == 0); spin_depth = 1; \
} while (0)
#define spin_unlock_irqrestore(lock, flags) do { \
    (void)(lock); (void)(flags); assert(spin_depth == 1); spin_depth = 0; \
} while (0)
#define system_percpu_wq ((void *)1)

static u64 gsn_now_ms(void)
{
    assert(spin_depth == 1 && clock_reads < 2);
    return clock_values[clock_reads++];
}

static int mod_delayed_work(void *queue, int *work, unsigned long delay)
{
    assert(queue == system_percpu_wq && work && delay == 0 && spin_depth == 1);
    scheduled++;
    return 0;
}

static void dev_warn(int *dev, const char *format, int error)
{
    assert(dev == &fake_device.dev && format && error < 0);
    warnings++;
}

static unsigned int usb_sndintpipe(struct fake_usb_device *device, unsigned int endpoint)
{
    assert(device == &fake_device && endpoint == 2);
    return endpoint;
}

static int usb_interrupt_msg(struct fake_usb_device *device, unsigned int pipe,
                             void *data, int length, int *actual, int timeout)
{
    assert(device == &fake_device && pipe == 2 && io_depth == 1 && spin_depth == 0);
    assert(length > 0 && length <= 64 && timeout == 250 && usb_calls < 8);
    memcpy(usb_bytes[usb_calls], data, (size_t)length);
    usb_lengths[usb_calls++] = length;
    *actual = usb_actual;
    return usb_return;
}
'''


CASES = r'''
static void setup(struct gsn_device *g, unsigned int motor, unsigned int session_ms)
{
    struct gsn_pulse pulse = { .abi_version = 1, .percent = 100, .duration_ms = 1000 };
    memset(g, 0, sizeof(*g));
    memset(usb_bytes, 0, sizeof(usb_bytes));
    memset(usb_lengths, 0, sizeof(usb_lengths));
    spin_depth = 0; io_depth = 1; scheduled = 0; warnings = 0;
    usb_calls = 0; usb_return = 0; usb_actual = 13;
    clock_reads = 0; clock_values[0] = clock_values[1] = 1000;
    g->udev = &fake_device;
    g->intf = &fake_intf;
    fake_intf.condition = USB_INTERFACE_BOUND;
    g->tx_buf = calloc(64, 1);
    assert(g->tx_buf);
    assert(gs_runtime_init(&g->rt, native_pid, 1) == 0);
    g->rt.owner = 1;
    assert(gs_runtime_start(&g->rt, 1000, session_ms) == 0);
    pulse.motor = motor;
    assert(gs_runtime_pulse(&g->rt, &pulse, 1000) == 0);
    g->output_used = true;
}

static void finish(struct gsn_device *g, const char *name)
{
    assert(spin_depth == 0 && io_depth == 1);
    assert(g->boot == NULL && !g->boot_handoff);
    free(g->tx_buf);
    printf("PASS: %s\n", name);
}

static void expect_motor(int call, unsigned int sequence, int motor, unsigned int ticks)
{
    /* Independent wire expectation; do not generate it using our encoder. */
    u8 expected[13] = {9, 0, 0, 9, 0, 15, 0, 0, 0, 0, 0, 0, 0};
    expected[2] = (u8)sequence;
    if (motor >= 0)
        expected[6 + motor] = 100;
    expected[10] = (u8)ticks;
    assert(call < usb_calls && usb_lengths[call] == 13);
    assert(memcmp(usb_bytes[call], expected, sizeof(expected)) == 0);
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    native_pid = (unsigned int)strtoul(argv[1], NULL, 16);
    assert(gs_pid_native(native_pid));
    struct gsn_device g;
    const char *names[] = {"1000-ms LT wire packet", "1000-ms RT wire packet",
                          "1000-ms left-grip wire packet", "1000-ms right-grip wire packet"};
    for (unsigned int motor = 0; motor < 4; motor++) {
        setup(&g, motor, 315000);
        assert(gsn_flush_motors(&g) == 0 && usb_calls == 1 && clock_reads == 2);
        expect_motor(0, 1, (int)motor, 100);
        assert(!scheduled && g.rt.state == GS_RUNNING);
        finish(&g, names[motor]);
    }

    setup(&g, 2, 315000);
    clock_values[0] = clock_values[1] = 1500;
    assert(gsn_flush_motors(&g) == 0 && usb_calls == 1);
    expect_motor(0, 1, 2, 50);
    finish(&g, "500-ms remaining deadline reaches wire");

    setup(&g, 2, 315000);
    clock_values[0] = 1999; clock_values[1] = 2001;
    assert(gsn_flush_motors(&g) == 0 && usb_calls == 1 && clock_reads == 2);
    expect_motor(0, 1, -1, 0);
    assert(g.rt.motors.value[2] == 0 && g.rt.session_active);
    finish(&g, "expiry between flush and send emits zero instead of restarting pulse");

    setup(&g, 2, 315000);
    clock_values[0] = clock_values[1] = 2001;
    assert(gsn_flush_motors(&g) == 0 && usb_calls == 1);
    expect_motor(0, 1, -1, 0);
    finish(&g, "already expired pulse emits zero");

    setup(&g, 2, 1000);
    clock_values[0] = 1999; clock_values[1] = 2001;
    assert(gsn_flush_motors(&g) == -EPERM && usb_calls == 0 && clock_reads == 2);
    assert(!g.rt.session_active && !g.rt.motors.value[2] && !g.sequence);
    finish(&g, "expired session cannot send a new motor packet");

    setup(&g, 2, 315000);
    clock_values[0] = 1500;
    assert(gsn_stop(&g, false) == 0 && usb_calls == 1);
    expect_motor(0, 1, -1, 0);
    assert(!g.rt.motors.value[2] && g.rt.session_active && g.stop_sent);
    assert(gsn_stop(&g, true) == 0 && usb_calls == 1 && !g.rt.session_active);
    finish(&g, "explicit stop emits zero and successful END does not duplicate it");

    setup(&g, 2, 315000);
    usb_return = -EPIPE; usb_actual = 0;
    assert(gsn_flush_motors(&g) == -EPIPE && usb_calls == 1);
    assert(g.rt.state == GS_FAULTED && g.rt.error == -EPIPE && !g.rt.session_active);
    assert(!g.rt.motors.value[2] && scheduled == 1);
    finish(&g, "USB transport error faults runtime and cannot report success");

    setup(&g, 2, 315000);
    usb_actual = 12;
    assert(gsn_flush_motors(&g) == -EREMOTEIO && usb_calls == 1);
    assert(g.rt.state == GS_FAULTED && g.rt.error == -EREMOTEIO && scheduled == 1);
    assert(!g.rt.session_active && !g.rt.motors.value[2]);
    finish(&g, "short USB transfer faults runtime and cannot report success");

    setup(&g, 2, 315000);
    usb_return = -EIO; usb_actual = 0;
    assert(gsn_stop(&g, true) == -EIO && usb_calls == 1);
    expect_motor(0, 1, -1, 0);
    assert(g.stop_sent && g.stop_error == -EIO && warnings == 1);
    assert(gsn_stop(&g, true) == -EIO && usb_calls == 1);
    finish(&g, "failed final stop is retained without retry or false success");

    setup(&g, 2, 315000);
    assert(gsn_send(&g, NULL, 0, false) == -EINVAL);
    assert(gsn_send(&g, NULL, 65, false) == -EINVAL);
    assert(gsn_send(&g, NULL, 12, false) == -EINVAL);
    assert(gsn_send(&g, NULL, 13, true) == -EINVAL);
    assert(!usb_calls && !clock_reads && !g.sequence && !scheduled);
    finish(&g, "invalid internal send shapes do not reach USB");

    setup(&g, 2, 315000);
    g.rt.dirty = 0;
    assert(gsn_flush_motors(&g) == 0 && !usb_calls && clock_reads == 1 && !g.sequence);
    finish(&g, "clean unexpired state does not resend motor packet");

    setup(&g, 2, 315000);
    {
        u8 heartbeat[64];
        gs_heartbeat(heartbeat, gsn_sequence(&g));
        usb_actual = 64;
        assert(gsn_send(&g, heartbeat, 64, false) == 0 && usb_calls == 1);
        assert(usb_lengths[0] == 64 && usb_bytes[0][0] == 15 && usb_bytes[0][2] == 1);
        clock_reads = 0; usb_actual = 13;
        assert(gsn_flush_motors(&g) == 0 && usb_calls == 2);
        expect_motor(1, 2, 2, 100);
    }
    finish(&g, "maintenance and motor packets retain shared sequence");
    setup(&g, 2, 315000);
    fake_intf.condition = 3; /* USB_INTERFACE_UNBINDING */
    assert(gsn_flush_motors(&g) == -EPERM && !usb_calls && !g.sequence);
    clock_reads = 0;
    assert(gsn_stop(&g, true) == 0 && usb_calls == 1);
    expect_motor(0, 1, -1, 0);
    finish(&g, "unbind blocks a new pulse but permits the final zero packet");
    return 0;
}
'''


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    kernel_path = PROJECT / "kernel/gs_native_usb.c"
    source = kernel_path.read_text()
    start = source.index("static u8 gsn_sequence(")
    end = source.index("\nstatic void gsn_neutral(", start)
    actual_functions = source[start:end]
    for name in ("gsn_sequence", "gsn_fault", "gsn_send", "gsn_stop", "gsn_flush_motors"):
        assert re.search(rf"^static .*\b{name}\(", actual_functions, re.MULTILINE), name
    timeout = re.search(r"^#define GSN_USB_TIMEOUT_MS\s+\d+\s*$", source, re.MULTILINE)
    assert timeout, "USB timeout definition missing"
    fixture = BUILD / "native-motor-output-fixture.c"
    binary = BUILD / "test-native-motor-output"
    fixture.write_text(SHIM + "\n" + timeout.group(0) + "\n" + actual_functions + CASES)
    command = ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-g",
               "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
               "-I", str(PROJECT / "src"), str(fixture),
               str(PROJECT / "src/gs_protocol.c"), str(PROJECT / "src/gs_runtime.c"),
               "-o", str(binary)]
    compiled = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
    cases = []
    logs = compiled.stdout + compiled.stderr
    for pid in ("109c", "105e"):
        tested = subprocess.run([str(binary), pid], capture_output=True, text=True, check=True, timeout=20)
        lines = tested.stdout.splitlines()
        assert len(lines) == 16 and all(line.startswith("PASS: ") for line in lines)
        cases.extend(pid + ": " + line.removeprefix("PASS: ") for line in lines)
        logs += tested.stdout + tested.stderr
    report = {"passed": True, "hardware_access": False, "sanitizers": ["address", "undefined"],
              "method": "Actual gsn_sequence/gsn_fault/gsn_send/gsn_stop/gsn_flush_motors extracted unchanged; own shared C runtime and protocol; synthetic clock/locks/USB",
              "cases": cases, "kernel_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "extracted_functions_sha256": hashlib.sha256(actual_functions.encode()).hexdigest(),
              "source_sha256": {str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in (PROJECT / "src/gs_protocol.c", PROJECT / "src/gs_runtime.c", PROJECT / "include/uapi/gs_native.h")},
              "limits": ["No real kernel lock scheduling, DMA, USB device, workqueue or concurrent IRQ execution.",
                         "All cases keep g.boot=NULL; reaching the bootstrap-only lock/latch stubs fails an assertion. Bootstrap producer-latch coverage belongs to the separate adapter/startup harness.",
                         "Simulated clock jump covers expiry between flush and the final send gate; host scheduling after that gate is not a hard realtime guarantee.",
                         "USB replacement records requested bytes and injects completion results; no mechanical effect is measured."]}
    (RESULTS / "native-motor-output.log").write_text(logs)
    (RESULTS / "native-motor-output.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
