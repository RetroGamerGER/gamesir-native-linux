// SPDX-License-Identifier: GPL-2.0-only
/* Compile the real session function against fake syscalls, never a device. */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <time.h>
#include "../include/uapi/gs_native.h"

static unsigned long long virtual_ns = 1000000000000ULL;
static const char *commands = "info\nsample\npulse left 100 400\nstop\nquit\n";
static int starts, ends, pulses, stops, opens, closes, allow_open;
static unsigned long fail_request;
static unsigned int expected_pulse_ms = 400;
static unsigned int boot_calls, expected_boot_flags;
static int boot_case;
static int waiting_case;

static int fake_clock(clockid_t id, struct timespec *ts)
{
	assert(id == CLOCK_MONOTONIC);
	ts->tv_sec = virtual_ns / 1000000000;
	ts->tv_nsec = virtual_ns % 1000000000;
	return 0;
}

static int fake_poll(struct pollfd *fds, nfds_t n, int timeout)
{
	assert(n == 1 && fds[0].fd == 0 && timeout == 100);
	virtual_ns += *commands ? 1000000 : 100000000;
	return *commands ? 1 : 0;
}

static ssize_t fake_read(int fd, void *out, size_t count)
{
	assert(fd == 0 && count == 1 && *commands);
	*(char *)out = *commands++;
	return 1;
}

static int fake_sigaction(int sig, const struct sigaction *action, struct sigaction *old)
{
	assert((sig == SIGINT || sig == SIGTERM || sig == SIGHUP) && action && !old);
	return 0;
}

static int fake_open(const char *name, int flags, ...)
{
	assert(allow_open);
	assert(!strcmp(name, "/dev/gsnative-offline-test"));
	assert(flags == (O_RDWR | O_CLOEXEC | O_NOFOLLOW));
	opens++;
	return 123; /* Synthetic descriptor; never open any path. */
}

static int fake_fstat(int fd, struct stat *st)
{
	assert(fd == 123);
	memset(st, 0, sizeof(*st));
	st->st_mode = 0020000; /* POSIX character-device mode, synthetic only. */
	return 0;
}

static int fake_close(int fd)
{
	assert(fd == 123);
	closes++;
	return 0;
}

static int fake_ioctl(int fd, unsigned long request, ...)
{
	va_list args;
	assert(fd == 123);
	va_start(args, request);
	if (request == GSN_START_SESSION) {
		starts++;
	} else if (request == GSN_BOOTSTRAP) {
		struct gsn_boot_request *r = va_arg(args, struct gsn_boot_request *);
		assert(r->abi_version == 1 && r->flags == expected_boot_flags &&
		       !r->reserved[0] && !r->reserved[1]);
		boot_calls++;
	} else if (request == GSN_GET_BOOT_STATUS) {
		struct gsn_boot_status *s = va_arg(args, struct gsn_boot_status *);
		*s = (struct gsn_boot_status){ .abi_version = 1,
			.state = fail_request ? 8 : waiting_case ? 9 : 7, .error = fail_request ? -EIO : 0,
			.imu_seen = !fail_request && !waiting_case, .port_token = 11, .instance_token = 22 };
	} else if (request == GSN_GET_INFO) {
		struct gsn_info *info = va_arg(args, struct gsn_info *);
		*info = (struct gsn_info){ .abi_version = 1, .pid = boot_case ? 0x100a : 0x109c, .state = 1,
			.output_enabled = 1, .session_active = 1, .accel_counts_per_g_num = 8192,
			.accel_counts_per_g_den = 1, .input_packets = 10, .imu_packets = 20 };
	} else if (request == GSN_GET_SAMPLE) {
		struct gsn_sample *s = va_arg(args, struct gsn_sample *);
		*s = (struct gsn_sample){ .abi_version = 1, .flags = 3,
			.host_monotonic_ns = virtual_ns, .sample_number = 20,
			.gyro_raw = {-32768, 0, 32767}, .accel_raw = {0, 0, 8192},
			.accel_experimental_um_s2 = {0, 0, 9806650} };
	} else if (request == GSN_PULSE) {
		struct gsn_pulse *p = va_arg(args, struct gsn_pulse *);
		assert(p->motor == 2 && p->percent == 100 && p->duration_ms == expected_pulse_ms);
		pulses++;
	} else if (request == GSN_STOP) {
		stops++;
	} else if (request == GSN_END_SESSION) {
		ends++;
	} else {
		abort();
	}
	va_end(args);
	if (request == fail_request) {
		errno = EIO;
		return -1;
	}
	return 0;
}

#define clock_gettime fake_clock
#define poll fake_poll
#define read fake_read
#define sigaction(...) fake_sigaction(__VA_ARGS__)
#define open fake_open
#define fstat fake_fstat
#define close fake_close
#define ioctl fake_ioctl
#define main unused_client_main
#include "../tools/native/gsnative-ctl.c"
#undef main
#undef sigaction

int main(int argc, char **argv)
{
	const char *mode = argc == 2 ? argv[1] : "normal";
	int deadline = !strcmp(mode, "deadline") || !strcmp(mode, "limit-300") ||
		!strcmp(mode, "default-session");
	int boundary = !strcmp(mode, "limit-300") || !strcmp(mode, "limit-301") ||
		!strcmp(mode, "default-session");
	int invalid_pulse = !strcmp(mode, "pulse-1001");
	unsigned int duration = !strcmp(mode, "limit-300") ? 300 :
		!strcmp(mode, "default-session") ? 20 : 1;
	unsigned long long initial_ns = virtual_ns;
	int result;

	if (!strncmp(mode, "bootstrap-", 10)) {
		char *client_argv[] = {"gsnative-ctl", "bootstrap", "/dev/gsnative-offline-test",
			!strcmp(mode, "bootstrap-invalid") ? "--guess" : "--handoff-xpad", NULL};
		boot_case = 1;
		waiting_case = !strcmp(mode, "bootstrap-wait");
		allow_open = strcmp(mode, "bootstrap-invalid") != 0;
		expected_boot_flags = !strcmp(mode, "bootstrap-handover") ? 1 : 0;
		if (!strcmp(mode, "bootstrap-fail"))
			fail_request = GSN_BOOTSTRAP;
		result = unused_client_main(expected_boot_flags || !allow_open ? 4 : 3, client_argv);
		assert(!starts && !ends && !pulses && !stops);
		assert(opens == allow_open && closes == allow_open && boot_calls == (unsigned)allow_open);
		assert(result == (!allow_open ? 2 : fail_request ? 1 : 0));
		return result;
	}
	if (!strcmp(mode, "end-wait") || !strcmp(mode, "info-wait")) {
		waiting_case = allow_open = 1;
		char *client_argv[] = {"gsnative-ctl", !strcmp(mode, "end-wait") ? "end" : "info",
			"/dev/gsnative-offline-test", "--expect-port", "11", "--expect-instance", "22", NULL};
		result = unused_client_main(7, client_argv);
		assert(result == (!strcmp(mode, "info-wait") ? 1 : 0));
		assert(ends == !strcmp(mode, "end-wait") && !starts && !pulses && !stops && !boot_calls);
		assert(opens == 1 && closes == 1);
		return result;
	}
	if (!strcmp(mode, "end-fail"))
		fail_request = GSN_END_SESSION;
	else if (!strcmp(mode, "start-fail"))
		fail_request = GSN_START_SESSION;
	else if (!strcmp(mode, "pulse-fail"))
		fail_request = GSN_PULSE;
	else if (!strcmp(mode, "stop-fail"))
		fail_request = GSN_STOP;
	if (deadline)
		commands = "";
	if (!strcmp(mode, "pulse-1000")) {
		commands = "pulse left 100 1000\nstop\nquit\n";
		expected_pulse_ms = 1000;
	} else if (invalid_pulse) {
		commands = "pulse left 100 1001\nquit\n";
	}
	if (boundary) {
		char *client_argv[] = {"gsnative-ctl", "session", "/dev/gsnative-offline-test",
			!strcmp(mode, "limit-301") ? "301" : "300", NULL};
		allow_open = strcmp(mode, "limit-301") != 0;
		result = unused_client_main(!strcmp(mode, "default-session") ? 3 : 4, client_argv);
		if (!allow_open) {
			assert(result == 2 && !opens && !closes && !starts && !ends && !pulses && !stops);
			return result;
		}
		assert(opens == 1 && closes == 1);
	} else {
		result = session(123, duration);
		assert(!opens && !closes);
	}
	assert(starts == 1 && ends == (fail_request == GSN_START_SESSION ? 0 : 1));
	assert(pulses == (!deadline && !invalid_pulse && fail_request != GSN_START_SESSION));
	assert(stops == (!deadline && !invalid_pulse && fail_request != GSN_START_SESSION && fail_request != GSN_PULSE));
	if (deadline)
		assert(virtual_ns == initial_ns + (unsigned long long)duration * 1000000000);
	assert(result == (fail_request != 0 || invalid_pulse));
	return result;
}
