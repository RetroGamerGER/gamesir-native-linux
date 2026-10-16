#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compile the real C service commands against fake device syscalls only."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>
#include "include/uapi/gs_native.h"

static unsigned long expected;
static int opens, closes, calls, error_code;
static int fake_open(const char *path, int flags, ...)
{
    assert(!strcmp(path, "/dev/gsnative-offline"));
    assert(flags == (O_RDWR | O_CLOEXEC | O_NOFOLLOW));
    opens++;
    return 123;
}
static int fake_fstat(int fd, struct stat *st)
{
    assert(fd == 123);
    memset(st, 0, sizeof(*st));
    st->st_mode = 0020000;
    return 0;
}
static int fake_ioctl(int fd, unsigned long request, ...)
{
    assert(fd == 123 && request == expected);
    /* No GET_INFO gate, START, BOOTSTRAP or pulse is allowed here. */
    calls++;
    errno = error_code;
    return error_code ? -1 : 0;
}
static int fake_close(int fd)
{
    assert(fd == 123);
    closes++;
    return 0;
}
#define open fake_open
#define fstat fake_fstat
#define ioctl fake_ioctl
#define close fake_close
#define main client_main
#include "tools/native/gsnative-ctl.c"
#undef main

int main(int argc, char **argv)
{
    char *arguments[] = {"gsnative-ctl", "end", "/dev/gsnative-offline", "extra", NULL};
    bool resume = argc > 1 && !strncmp(argv[1], "resume", 6);
    bool invalid = argc > 1 && strstr(argv[1], "invalid");
    int ret;

    expected = resume ? GSN_RESUME : GSN_END_SESSION;
    if (resume)
        arguments[1] = "resume";
    if (argc > 1 && strstr(argv[1], "again"))
        error_code = EAGAIN;
    else if (argc > 1 && strstr(argv[1], "fail"))
        error_code = EINVAL;
    ret = client_main(invalid ? 4 : 3, arguments);
    assert(opens == !invalid && closes == !invalid && calls == !invalid);
    assert(ret == (invalid ? 2 : error_code == EAGAIN && resume ? 3 : error_code ? 1 : 0));
    return ret;
}
'''


class ServiceClient(unittest.TestCase):
    def test_status_busy_is_only_an_unopened_passive_node(self):
        build = ROOT / "build/test-service-client"
        build.mkdir(parents=True, exist_ok=True)
        source, binary = build / "status.c", build / "status"
        source.write_text(STATUS_SOURCE)
        subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=address,undefined", "-I", str(ROOT), str(source),
                        "-o", str(binary)], check=True)
        cases = [(command, failure, 4 if failure == "open-busy" else
                  0 if failure == "none" else 1)
                 for command in ("info", "boot-info")
                 for failure in ("none", "open-busy", "open-access", "open-absent",
                                 "open-disconnected", "fstat-busy", "ioctl-busy", "close-busy")]
        cases += [(command, "open-busy", 1)
                  for command in ("sample", "session", "bootstrap", "end", "resume")]
        cases += [(command, identity, status)
                  for command in ("info", "checked-info")
                  for identity, status in (("zzz", 0), ("unknown-pid", 1))]
        cases += [("checked-info", failure, status) for failure, status in (
            ("none", 0), ("pm", 1), ("failed", 1), ("open-busy", 4),
            ("open-access", 1), ("open-absent", 1), ("open-disconnected", 1),
            ("fstat-busy", 1), ("ioctl-busy", 1), ("close-busy", 1),
            ("proof-instance", 1), ("proof-port", 1), ("proof-state", 1),
            ("proof-abi", 1), ("proof-reserved", 1), ("proof-read-failure", 1),
            ("bad-zero", 2), ("bad-negative", 2), ("bad-overflow", 2),
            ("bad-whitespace", 2), ("bad-incomplete", 2))]
        for command, failure, status in cases:
            with self.subTest(command=command, failure=failure):
                result = subprocess.run([str(binary), command, failure], capture_output=True,
                                        text=True, timeout=5)
                self.assertEqual(result.returncode, status, result.stderr)
                if status == 4:
                    self.assertNotIn("pid=", result.stdout)
                    self.assertNotIn("bootstrap state=", result.stdout)
                if failure.startswith("proof-"):
                    self.assertNotIn("pid=", result.stdout)
                if command == "checked-info" and failure in ("none", "pm", "failed"):
                    self.assertIn("port_token=91 instance_token=9223372036854775811", result.stdout)
                    self.assertIn("pid=109c", result.stdout)
                if failure == "pm":
                    self.assertIn("bootstrap state=7", result.stdout)
                    self.assertIn("state=3 error=-108", result.stdout)
                if failure == "zzz":
                    self.assertIn("pid=105e", result.stdout)
                if failure == "unknown-pid":
                    self.assertNotIn("pid=", result.stdout)

    def test_end_and_resume_exact_syscalls_and_status(self):
        build = ROOT / "build/test-service-client"
        build.mkdir(parents=True, exist_ok=True)
        source, binary = build / "fake.c", build / "fake"
        source.write_text(SOURCE)
        subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=address,undefined", "-I", str(ROOT), str(source),
                        "-o", str(binary)], check=True)
        cases = {"end": 0, "end-fail": 1, "end-again": 1, "end-invalid": 2,
                 "resume": 0, "resume-fail": 1, "resume-again": 3, "resume-invalid": 2}
        for mode, status in cases.items():
            with self.subTest(mode=mode):
                result = subprocess.run([str(binary), mode], capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, status, result.stderr)
                if status == 0:
                    self.assertIn("Persistent runtime resumed." if mode == "resume" else
                                  "Native runtime quiesced; USB identity and xpad return require separate verification.", result.stdout)

    def test_bootstrap_failure_proof_and_pinned_end(self):
        build = ROOT / "build/test-service-client"
        build.mkdir(parents=True, exist_ok=True)
        source, binary = build / "proof.c", build / "proof"
        source.write_text(PROOF_SOURCE)
        subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-fsanitize=address,undefined", "-I", str(ROOT), str(source),
                        "-o", str(binary)], check=True)
        cases = {"bootstrap-fail": 1, "bootstrap-ok": 0, "bootstrap-false-ready": 1,
                 "bootstrap-zzz": 0, "bootstrap-zzz-fail": 1,
                 "bootstrap-unknown-pid": 1,
                 "boot-info-fail": 1, "end-failed-owned": 0, "end-owned": 0,
                 "end-mismatch": 1, "end-state": 1, "end-abi": 1,
                 "end-read-error": 1, "end-reserved": 1,
                 "end-zero": 2, "end-negative": 2, "end-overflow": 2,
                 "end-whitespace": 2, "end-incomplete": 2}
        for mode, status in cases.items():
            with self.subTest(mode=mode):
                result = subprocess.run([str(binary), mode], capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, status, result.stderr)
                if mode in ("bootstrap-fail", "boot-info-fail"):
                    self.assertIn("state=8 error=-5", result.stdout)
                    self.assertIn("port_token=91 instance_token=9223372036854775811", result.stdout)
                if mode.startswith("bootstrap-") and status:
                    self.assertNotIn("Native startup completed.", result.stdout)
                if mode == "bootstrap-zzz":
                    self.assertIn("pid=105e", result.stdout)
                    self.assertIn("Native startup completed.", result.stdout)
                    self.assertNotIn("New 109c", result.stdout)
                if mode == "bootstrap-unknown-pid":
                    self.assertNotIn("One explicit native bootstrap", result.stdout)
                if mode.startswith("end-") and status:
                    self.assertNotIn("Native runtime quiesced", result.stdout)


STATUS_SOURCE = r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>
#include "include/uapi/gs_native.h"
static const char *command, *failure;
static bool checked;
static int opens, stats, calls, closes;
static int fake_open(const char *path, int flags, ...)
{
    assert(!strcmp(path, "/dev/gsnative-offline"));
    assert(flags == (O_RDWR | O_CLOEXEC | O_NOFOLLOW));
    opens++;
    if (!strncmp(failure, "open-", 5)) {
        errno = !strcmp(failure, "open-busy") ? EBUSY :
            !strcmp(failure, "open-access") ? EACCES :
            !strcmp(failure, "open-absent") ? ENOENT : ENODEV;
        return -1;
    }
    return 123;
}
static int fake_fstat(int fd, struct stat *st)
{
    assert(fd == 123); stats++;
    if (!strcmp(failure, "fstat-busy")) { errno = EBUSY; return -1; }
    memset(st, 0, sizeof(*st)); st->st_mode = 0020000;
    return 0;
}
static int fake_ioctl(int fd, unsigned long request, ...)
{
    va_list ap;
    assert(fd == 123); calls++;
    assert(request == (checked ? (calls == 1 ? GSN_GET_BOOT_STATUS : GSN_GET_INFO) :
        !strcmp(command, "info") ? GSN_GET_INFO : GSN_GET_BOOT_STATUS));
    assert(calls <= (checked ? 2 : 1));
    if (!strcmp(failure, "ioctl-busy")) { errno = EBUSY; return -1; }
    if (!strcmp(failure, "proof-read-failure")) { errno = ENODEV; return -1; }
    va_start(ap, request);
    if (request == GSN_GET_INFO) {
        struct gsn_info *info = va_arg(ap, struct gsn_info *);
        memset(info, 0, sizeof(*info)); info->abi_version = 1; info->pid = 0x109c;
        if (!strcmp(failure, "zzz")) info->pid = 0x105e;
        if (!strcmp(failure, "unknown-pid")) info->pid = 0x105f;
        info->state = 1; info->output_enabled = info->session_active = 1;
        if (!strcmp(failure, "pm")) {
            info->state = 3; info->last_error = -ESHUTDOWN; info->session_active = 0;
        }
        if (!strcmp(failure, "failed")) {
            info->state = 2; info->last_error = -EIO; info->session_active = 0;
        }
    } else {
        struct gsn_boot_status *status = va_arg(ap, struct gsn_boot_status *);
        memset(status, 0, sizeof(*status)); status->abi_version = 1; status->state = 7;
        status->port_token = 91; status->instance_token = 9223372036854775811ULL;
        if (!strcmp(failure, "failed")) {
            status->state = 8; status->error = -EIO; status->failed_stage = 5;
        }
        if (!strcmp(failure, "proof-instance")) status->instance_token++;
        if (!strcmp(failure, "proof-port")) status->port_token++;
        if (!strcmp(failure, "proof-state")) status->state = 3;
        if (!strcmp(failure, "proof-abi")) status->abi_version++;
        if (!strcmp(failure, "proof-reserved")) status->reserved = 1;
    }
    va_end(ap);
    return 0;
}
static int fake_close(int fd)
{
    assert(fd == 123); closes++;
    if (!strcmp(failure, "close-busy")) { errno = EBUSY; return -1; }
    return 0;
}
#define open fake_open
#define fstat fake_fstat
#define ioctl fake_ioctl
#define close fake_close
#define main client_main
#include "tools/native/gsnative-ctl.c"
#undef main
int main(int argc, char **argv)
{
    char *args[] = {"gsnative-ctl", NULL, "/dev/gsnative-offline", "--expect-port", "91",
        "--expect-instance", "9223372036854775811", NULL};
    int result, count;
    assert(argc == 3); failure = argv[2];
    checked = !strcmp(argv[1], "checked-info");
    command = checked ? "info" : argv[1]; args[1] = (char *)command;
    count = checked ? 7 : 3;
    if (!strcmp(failure, "bad-zero")) args[4] = "0";
    if (!strcmp(failure, "bad-negative")) args[4] = "-91";
    if (!strcmp(failure, "bad-overflow")) args[6] = "18446744073709551616";
    if (!strcmp(failure, "bad-whitespace")) args[4] = " 91";
    if (!strcmp(failure, "bad-incomplete")) count = 5;
    result = client_main(count, args);
    if (!strncmp(failure, "bad-", 4)) {
        assert(!opens && !stats && !calls && !closes);
        return result;
    }
    assert(opens == 1);
    if (!strncmp(failure, "open-", 5))
        assert(!stats && !calls && !closes);
    else {
        assert(stats == 1 && closes == 1);
        assert(calls == (!strcmp(failure, "fstat-busy") ? 0 :
            checked && strncmp(failure, "proof-", 6) && strcmp(failure, "ioctl-busy") ? 2 : 1));
    }
    return result;
}
'''


PROOF_SOURCE = r'''
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdarg.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>
#include "include/uapi/gs_native.h"
static const char *mode;
static int opens, closes, calls, ends;
static int fake_open(const char *path, int flags, ...)
{
    assert(!strcmp(path, "/dev/gsnative-offline"));
    assert(flags == (O_RDWR | O_CLOEXEC | O_NOFOLLOW));
    opens++;
    return 123;
}
static int fake_fstat(int fd, struct stat *st)
{
    assert(fd == 123);
    memset(st, 0, sizeof(*st)); st->st_mode = 0020000;
    return 0;
}
static int fake_ioctl(int fd, unsigned long request, ...)
{
    va_list ap;
    assert(fd == 123);
    calls++;
    va_start(ap, request);
    if (request == GSN_GET_INFO) {
        struct gsn_info *i = va_arg(ap, struct gsn_info *);
        assert(!strncmp(mode, "bootstrap-", 10) && calls == 1);
        memset(i, 0, sizeof(*i)); i->abi_version = 1; i->pid = 0x100a; i->state = 1;
        if (strstr(mode, "zzz")) i->pid = 0x105e;
        if (!strcmp(mode, "bootstrap-unknown-pid")) i->pid = 0x105f;
    } else if (request == GSN_BOOTSTRAP) {
        struct gsn_boot_request *b = va_arg(ap, struct gsn_boot_request *);
        assert(calls == 2 && b->abi_version == 1);
        assert(b->flags == (strstr(mode, "zzz") ? 0 : GSN_BOOT_ALLOW_XPAD_HANDOVER));
        if (strstr(mode, "fail") && strcmp(mode, "bootstrap-false-ready")) {
            va_end(ap); errno = EIO; return -1;
        }
    } else if (request == GSN_GET_BOOT_STATUS) {
        struct gsn_boot_status *s = va_arg(ap, struct gsn_boot_status *);
        assert(calls == (!strncmp(mode, "bootstrap-", 10) ? 3 : 1));
        if (!strcmp(mode, "end-read-error")) {
            va_end(ap); errno = ENODEV; return -1;
        }
        memset(s, 0, sizeof(*s)); s->abi_version = 1; s->state = 7;
        s->port_token = 91; s->instance_token = 9223372036854775811ULL;
        if (strstr(mode, "fail")) { s->state = 8; s->error = -EIO; s->failed_stage = 5; }
        if (!strcmp(mode, "bootstrap-false-ready")) { s->state = 6; }
        if (!strcmp(mode, "end-mismatch")) { s->instance_token++; }
        if (!strcmp(mode, "end-state")) { s->state = 3; }
        if (!strcmp(mode, "end-abi")) { s->abi_version++; }
        if (!strcmp(mode, "end-reserved")) { s->reserved = 1; }
    } else {
        assert(request == GSN_END_SESSION && calls == 2);
        assert(!strcmp(mode, "end-owned") || !strcmp(mode, "end-failed-owned"));
        ends++;
    }
    va_end(ap);
    return 0;
}
static int fake_close(int fd) { assert(fd == 123); closes++; return 0; }
#define open fake_open
#define fstat fake_fstat
#define ioctl fake_ioctl
#define close fake_close
#define main client_main
#include "tools/native/gsnative-ctl.c"
#undef main
int main(int argc, char **argv)
{
    char *args[] = {"ctl", "end", "/dev/gsnative-offline", "--expect-port", "91",
                    "--expect-instance", "9223372036854775811", NULL};
    int count = 7, result;
    bool invalid;
    assert(argc == 2); mode = argv[1];
    invalid = !strcmp(mode, "end-zero") || !strcmp(mode, "end-negative") ||
        !strcmp(mode, "end-overflow") || !strcmp(mode, "end-whitespace") ||
        !strcmp(mode, "end-incomplete");
    if (!strncmp(mode, "bootstrap-", 10)) { args[1] = "bootstrap"; args[3] = "--handoff-xpad"; count = 4; }
    else if (!strcmp(mode, "boot-info-fail")) { args[1] = "boot-info"; count = 3; }
    else if (!strcmp(mode, "end-zero")) args[4] = "0";
    else if (!strcmp(mode, "end-negative")) args[4] = "-91";
    else if (!strcmp(mode, "end-overflow")) args[6] = "18446744073709551616";
    else if (!strcmp(mode, "end-whitespace")) args[4] = " 91";
    else if (!strcmp(mode, "end-incomplete")) count = 5;
    if (strstr(mode, "zzz")) count = 3;
    result = client_main(count, args);
    assert(opens == !invalid && closes == !invalid);
    assert(!invalid || calls == 0);
    if (!strcmp(mode, "bootstrap-unknown-pid")) assert(calls == 1);
    assert(ends == (!strcmp(mode, "end-owned") || !strcmp(mode, "end-failed-owned")));
    return result;
}
'''


if __name__ == "__main__":
    unittest.main()
