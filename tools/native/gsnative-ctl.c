// SPDX-License-Identifier: GPL-2.0-only
#define _POSIX_C_SOURCE 200809L
#include "../../include/uapi/gs_native.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define GSN_TOOL_MAX_SESSION_SECONDS 300

static volatile sig_atomic_t interrupted;

static void on_signal(int sig)
{
	(void)sig;
	interrupted = 1;
}

static unsigned long long now_ns(void)
{
	struct timespec ts;

	if (clock_gettime(CLOCK_MONOTONIC, &ts)) {
		perror("clock_gettime");
		exit(1);
	}
	return (unsigned long long)ts.tv_sec * 1000000000 + ts.tv_nsec;
}

static unsigned long long now_ms(void)
{
	return now_ns() / 1000000;
}

static bool number(const char *text, unsigned int low, unsigned int high, unsigned int *out)
{
	char *end;
	unsigned long value;

	if (!text || !*text)
		return false;
	for (const char *p = text; *p; p++)
		if (*p < '0' || *p > '9')
			return false;
	errno = 0;
	value = strtoul(text, &end, 10);
	if (errno || *end || value < low || value > high)
		return false;
	*out = value;
	return true;
}

static bool parse_pulse(char *line, struct gsn_pulse *pulse)
{
	static const char *const motors[] = {"lt", "rt", "left", "right"};
	char *save = NULL, *words[5];
	unsigned int count = 0;

	for (char *w = strtok_r(line, " \t\r\n", &save); w; w = strtok_r(NULL, " \t\r\n", &save)) {
		if (count == 5)
			return false;
		words[count++] = w;
	}
	if (count != 4 || strcmp(words[0], "pulse"))
		return false;
	memset(pulse, 0, sizeof(*pulse));
	pulse->abi_version = GSN_ABI_VERSION;
	for (pulse->motor = 0; pulse->motor < 4; pulse->motor++)
		if (!strcmp(words[1], motors[pulse->motor]))
			break;
	return pulse->motor < 4 && number(words[2], 1, 100, &pulse->percent) &&
		number(words[3], 1, GSN_MAX_PULSE_MS, &pulse->duration_ms);
}

static int self_test(void)
{
	const char *good[] = {"pulse lt 100 400", "pulse rt 100 400", "pulse left 100 400", "pulse right 100 400"};
	const char *bad[] = {"pulse lt 101 400", "pulse lt 100 1001", "pulse rt 0 400",
		"pulse all 100 400", "pulse lt 100 0", "pulse lt -1 400", "pulse lt 100 400 extra",
		"pulse lt 9999999999999999999999 400", "pulse lt 100", "pulse lt 100 400x"};
	char buffer[128];
	struct gsn_pulse pulse;
	unsigned int seconds;

	_Static_assert(sizeof(struct gsn_boot_request) == 16, "bootstrap request ABI");
	_Static_assert(sizeof(struct gsn_boot_status) == 48, "bootstrap status ABI");
	_Static_assert(sizeof(struct gsn_info) == 56, "info ABI");
	_Static_assert(sizeof(struct gsn_sample) == 48, "sample ABI");
	_Static_assert(sizeof(struct gsn_pulse) == 32, "pulse ABI");
	_Static_assert(GSN_TOOL_MAX_SESSION_SECONDS * 1000 < GSN_MAX_SESSION_MS,
		       "kernel deadline leaves time for userspace final stop");
	if (!number("300", 1, GSN_TOOL_MAX_SESSION_SECONDS, &seconds) ||
	    seconds != 300 || number("301", 1, GSN_TOOL_MAX_SESSION_SECONDS, &seconds) ||
	    number("0", 1, GSN_TOOL_MAX_SESSION_SECONDS, &seconds))
		return 1;
	for (unsigned int i = 0; i < sizeof(good) / sizeof(good[0]); i++) {
		strcpy(buffer, good[i]);
		if (!parse_pulse(buffer, &pulse) || pulse.motor != i)
			return 1;
	}
	strcpy(buffer, "pulse left 100 1000");
	if (!parse_pulse(buffer, &pulse) || pulse.motor != 2 || pulse.duration_ms != 1000)
		return 1;
	for (unsigned int i = 0; i < sizeof(bad) / sizeof(bad[0]); i++) {
		strcpy(buffer, bad[i]);
		if (parse_pulse(buffer, &pulse))
			return 1;
	}
	puts("PASS: offline tool parser/ABI; no file or device opened");
	return 0;
}

static int info(int fd)
{
	struct gsn_info i;

	if (ioctl(fd, GSN_GET_INFO, &i)) {
		perror("GET_INFO");
		return 1;
	}
	if (i.abi_version != GSN_ABI_VERSION ||
	    (i.pid != 0x100a && i.pid != 0x109c && i.pid != 0x105e)) {
		fputs("Unexpected device/ABI; stop\n", stderr);
		return 1;
	}
	printf("pid=%04x state=%u error=%d OUT=%u session=%u pad=%llu imu=%llu rejected=%llu experimental_accel=%u/%u LSB/g\n",
	       i.pid, i.state, i.last_error, i.output_enabled, i.session_active,
	       (unsigned long long)i.input_packets, (unsigned long long)i.imu_packets,
	       (unsigned long long)i.rejected_packets, i.accel_counts_per_g_num, i.accel_counts_per_g_den);
	return i.last_error != 0;
}

static int sample(int fd)
{
	struct gsn_sample s;

	if (ioctl(fd, GSN_GET_SAMPLE, &s)) {
		perror("GET_SAMPLE (no sample, stale or device error)");
		return 1;
	}
	printf("host_monotonic_ns=%llu sample=%llu gyro_raw=[%d,%d,%d] accel_raw=[%d,%d,%d] experiment_valid=%u accel_um_s2=[%d,%d,%d]\n",
	       (unsigned long long)s.host_monotonic_ns, (unsigned long long)s.sample_number,
	       s.gyro_raw[0], s.gyro_raw[1], s.gyro_raw[2], s.accel_raw[0], s.accel_raw[1], s.accel_raw[2],
	       !!(s.flags & GSN_FLAG_ACCEL_VALID), s.accel_experimental_um_s2[0],
	       s.accel_experimental_um_s2[1], s.accel_experimental_um_s2[2]);
	return 0;
}

static int session(int fd, unsigned int seconds)
{
	struct sigaction action = { .sa_handler = on_signal };
	unsigned long long end, start_ns, pulse_end = 0;
	char line[128];
	size_t used = 0;
	int failed = 0;

	sigemptyset(&action.sa_mask);
	if (sigaction(SIGINT, &action, NULL) || sigaction(SIGTERM, &action, NULL) ||
	    sigaction(SIGHUP, &action, NULL)) {
		perror("sigaction");
		return 1;
	}
	/* Set our deadline before START, so initialization counts towards it. */
	start_ns = now_ns();
	end = start_ns + (unsigned long long)seconds * 1000000000;
	printf("START_CALL monotonic_ns=%llu\n", start_ns);
	fflush(stdout);
	if (ioctl(fd, GSN_START_SESSION)) {
		perror("START_SESSION");
		return 1;
	}
	puts("Session started. No motor runs automatically.");
	puts("Commands: info | sample | pulse lt|rt|left|right PERCENT MS | stop | quit");
	fflush(stdout);
	while (!interrupted && now_ns() < end) {
		struct pollfd input = { .fd = STDIN_FILENO, .events = POLLIN };
		int ret = poll(&input, 1, 100);
		char ch;

		if (ret < 0) {
			if (errno == EINTR)
				continue;
			failed = 1;
			break;
		}
		if (!ret)
			continue;
		if (read(STDIN_FILENO, &ch, 1) != 1)
			break;
		if (ch != '\n') {
			if (used + 1 >= sizeof(line)) {
				fputs("Command too long; ending session\n", stderr);
				failed = 1;
				break;
			}
			line[used++] = ch;
			continue;
		}
		line[used] = 0;
		used = 0;
		if (!strcmp(line, "quit"))
			break;
		if (!strcmp(line, "info"))
			failed = info(fd);
		else if (!strcmp(line, "sample"))
			failed = sample(fd);
		else if (!strcmp(line, "stop")) {
			failed = ioctl(fd, GSN_STOP) != 0;
			pulse_end = 0;
			if (!failed)
				puts("STOP accepted; zero motor transfer confirmed.");
		} else {
			struct gsn_pulse pulse;

			if (!parse_pulse(line, &pulse)) {
				fputs("Invalid command; ending session\n", stderr);
				failed = 1;
				break;
			}
			if (now_ms() < pulse_end) {
				fputs("Previous single-motor test still running; ending session\n", stderr);
				failed = 1;
				break;
			}
			failed = ioctl(fd, GSN_PULSE, &pulse) != 0;
			pulse_end = now_ms() + pulse.duration_ms;
			if (!failed)
				puts("One motor pulse accepted; bounded by kernel deadline and explicit stop.");
		}
		fflush(stdout);
		if (failed) {
			perror("Command failed; ending session");
			break;
		}
	}
	if (ioctl(fd, GSN_END_SESSION)) {
		perror("FINAL STOP failed; physical stop is not confirmed");
		failed = 1;
	} else {
		puts("Session ended; zero motor packet confirmed by USB transfer (not mechanical feedback).");
	}
	return failed || interrupted;
}

static int read_boot_info(int fd, struct gsn_boot_status *status)
{
	memset(status, 0, sizeof(*status));
	if (ioctl(fd, GSN_GET_BOOT_STATUS, status)) {
		perror("GET_BOOT_STATUS");
		return 1;
	}
	if (status->abi_version != GSN_ABI_VERSION || status->state > 9 || status->reserved)
		return 1;
	printf("bootstrap state=%u error=%d failed_stage=%u pad=%u imu=%u handover=%u port_token=%llu instance_token=%llu\n",
	       status->state, status->error, status->failed_stage, status->pad_seen,
	       status->imu_seen, status->handover_attempted,
	       (unsigned long long)status->port_token, (unsigned long long)status->instance_token);
	return 0;
}

static int boot_info(int fd)
{
	struct gsn_boot_status status;

	if (read_boot_info(fd, &status))
		return 1;
	return status.error != 0;
}

static int bootstrap(int fd, bool handover)
{
	struct gsn_boot_request request = { .abi_version = GSN_ABI_VERSION,
		.flags = handover ? GSN_BOOT_ALLOW_XPAD_HANDOVER : 0 };
	struct sigaction action = { .sa_handler = on_signal };
	struct gsn_boot_status status;
	int ret;

	sigemptyset(&action.sa_mask);
	sigaction(SIGINT, &action, NULL);
	sigaction(SIGTERM, &action, NULL);
	puts("One explicit native bootstrap; no motor pulses. Setup deadline: 30 seconds; opt-in receiver standby returns pending, never reinitializes.");
	fflush(stdout);
	ret = ioctl(fd, GSN_BOOTSTRAP, &request);
	if (ret)
		perror("BOOTSTRAP failed; no retry or automatic restore");
	if (read_boot_info(fd, &status))
		return 1;
	/* HANDED_OFF=7; WAIT_RECEIVER=9 is pending, never runtime success. */
	if (ret || status.error || (status.state != 7 && status.state != 9) ||
	    !status.port_token || !status.instance_token || (status.state == 9 && status.failed_stage))
		return 1;
	if (status.state == 9) {
		puts("Native receiver waiting. One setup completed; no runtime readiness or radio connection claimed.");
		return 0;
	}
	puts("Native startup completed. Attested device owns the native runtime; no second initialization needed.");
	return 0;
}

static int check_boot_owner(int fd, unsigned long long port, unsigned long long instance,
			    const char *operation)
{
	struct gsn_boot_status status;

	/* Both getters use this pinned FD. HANDED_OFF=7 and FAILED=8 are existing
	 * ownership proofs. WAIT_RECEIVER=9 permits END only, never runtime input.
	 */
	if (read_boot_info(fd, &status) || status.port_token != port ||
	    status.instance_token != instance || (status.state != 7 && status.state != 8 &&
	    !(status.state == 9 && !strcmp(operation, "END")))) {
		fprintf(stderr, "%s ownership proof mismatch; no %s issued\n", operation, operation);
		return 1;
	}
	return 0;
}

/* Service operations never START a new developer session or pulse a motor. */
static int service_command(int fd, bool resume, unsigned long long port, unsigned long long instance)
{
	if (port && check_boot_owner(fd, port, instance, "END"))
		return 1;
	if (ioctl(fd, resume ? GSN_RESUME : GSN_END_SESSION)) {
		int saved_errno = errno;

		perror(resume ? "RESUME" : "END_SESSION");
		/* Only PM-not-ready can be retried; every other failure is terminal. */
		return resume && saved_errno == EAGAIN ? 3 : 1;
	}
	puts(resume ? "Persistent runtime resumed." :
	     "Native runtime quiesced; USB identity and xpad return require separate verification.");
	return 0;
}

static bool token_number(const char *text, unsigned long long *out)
{
	char *end;
	unsigned long long value;

	if (!text || !*text)
		return false;
	for (const char *p = text; *p; p++)
		if (*p < '0' || *p > '9')
			return false;
	errno = 0;
	value = strtoull(text, &end, 10);
	if (errno || *end || !value)
		return false;
	*out = value;
	return true;
}

static int input_command(int fd, bool publish, unsigned long long port, unsigned long long instance)
{
	struct gsn_input_status status = {0};
	struct gsn_input_publish request = { .abi_version = GSN_ABI_VERSION,
		.port_token = port, .instance_token = instance };

	if (!port || !instance || check_boot_owner(fd, port, instance, "INPUT"))
		return 1;
	if (publish && ioctl(fd, GSN_PUBLISH_INPUT, &request)) {
		perror("PUBLISH_INPUT; no retry");
		return 1;
	}
	if (ioctl(fd, GSN_GET_INPUT_STATUS, &status)) {
		perror("GET_INPUT_STATUS");
		return 1;
	}
	if (status.abi_version != GSN_ABI_VERSION || status.flags & ~7u ||
	    status.port_token != port || status.instance_token != instance ||
	    !memchr(status.sensor_name, 0, sizeof(status.sensor_name)) ||
	    !memchr(status.uniq, 0, sizeof(status.uniq)))
		return 1;
	/* Kernel-generated names only; no user-controlled JSON string escaping. */
	for (const char *p = status.sensor_name; *p; p++)
		if ((*p < '0' || *p > '9') && (*p < 'a' || *p > 'z')) return 1;
	for (const char *p = status.uniq; *p; p++)
		if ((*p < '0' || *p > '9') && (*p < 'a' || *p > 'z') &&
		    !strchr("-.:", *p)) return 1;
	printf("input-publication {\"flags\":%u,\"port\":%llu,\"instance\":%llu,"
	       "\"sensor\":\"%s\",\"uniq\":\"%s\",\"gyro\":%u,\"accel\":%u}\n",
	       status.flags, (unsigned long long)status.port_token,
	       (unsigned long long)status.instance_token, status.sensor_name, status.uniq,
	       status.gyro_resolution, status.accel_resolution);
	return publish && !(status.flags & GSN_INPUT_PUBLISHED) ? 1 : 0;
}

int main(int argc, char **argv)
{
	struct stat st;
	unsigned int seconds = 20;
	unsigned long long expected_port = 0, expected_instance = 0;
	int fd, ret;
	const char *path;

	if (argc == 2 && !strcmp(argv[1], "--self-test"))
		return self_test();
	if (argc < 3 || (strcmp(argv[1], "input-info") && strcmp(argv[1], "publish-input") && strcmp(argv[1], "info") && strcmp(argv[1], "sample") && strcmp(argv[1], "session") && strcmp(argv[1], "bootstrap") && strcmp(argv[1], "boot-info") && strcmp(argv[1], "end") && strcmp(argv[1], "resume"))) {
		printf("gsnative-ctl --help | --self-test\ngsnative-ctl info /dev/gsnative-INTERFACE [--expect-port TOKEN --expect-instance TOKEN]\ngsnative-ctl sample /dev/gsnative-INTERFACE\ngsnative-ctl session /dev/gsnative-INTERFACE [SECONDS 1..%u]\ngsnative-ctl bootstrap /dev/gsnative-INTERFACE [--handoff-xpad]\ngsnative-ctl boot-info /dev/gsnative-INTERFACE\ngsnative-ctl end /dev/gsnative-INTERFACE [--expect-port TOKEN --expect-instance TOKEN]\ngsnative-ctl resume /dev/gsnative-INTERFACE\nStatus commands info/boot-info return 4 only if open reports a busy control node.\nHardware operations require separate user approval.\n", GSN_TOOL_MAX_SESSION_SECONDS);
		puts("gsnative-ctl input-info|publish-input /dev/gsnative-INTERFACE --expect-port TOKEN --expect-instance TOKEN\nOptional deferred input only; publication never retries or starts USB output.");
		return argc == 1 || (argc == 2 && !strcmp(argv[1], "--help")) ? 0 : 2;
	}
	bool input_op = !strcmp(argv[1], "input-info") || !strcmp(argv[1], "publish-input");
	if (input_op && argc != 7) return 2;
	if ((!strcmp(argv[1], "end") || !strcmp(argv[1], "info") || input_op) && argc != 3 &&
	    (argc != 7 || strcmp(argv[3], "--expect-port") || strcmp(argv[5], "--expect-instance") ||
	     !token_number(argv[4], &expected_port) || !token_number(argv[6], &expected_instance)))
		return 2;
	if ((!strcmp(argv[1], "session") && (argc > 4 || (argc == 4 && !number(argv[3], 1, GSN_TOOL_MAX_SESSION_SECONDS, &seconds)))) ||
	    (!strcmp(argv[1], "bootstrap") && (argc > 4 || (argc == 4 && strcmp(argv[3], "--handoff-xpad")))) ||
	    (strcmp(argv[1], "session") && strcmp(argv[1], "bootstrap") && strcmp(argv[1], "end") &&
	     strcmp(argv[1], "info") && !input_op && argc != 3))
		return 2;
	path = argv[2];
	if (strncmp(path, "/dev/gsnative-", 14) || !path[14] || strchr(path + 14, '/')) {
		fputs("Only an explicitly named /dev/gsnative-* node is accepted\n", stderr);
		return 2;
	}
	fd = open(path, O_RDWR | O_CLOEXEC | O_NOFOLLOW);
	if (fd < 0) {
		int saved_errno = errno;

		perror("open native test node");
		/* Only a passive status open can be retried without an uncertain action. */
		if (saved_errno == EBUSY &&
		    (!strcmp(argv[1], "info") || !strcmp(argv[1], "boot-info") || !strcmp(argv[1], "input-info")))
			return 4;
		return 1;
	}
	if (fstat(fd, &st) || !S_ISCHR(st.st_mode)) {
		fputs("Not a character device; stop\n", stderr);
		close(fd);
		return 1;
	}
	if (input_op)
		ret = input_command(fd, !strcmp(argv[1], "publish-input"), expected_port, expected_instance);
	else if (!strcmp(argv[1], "end") || !strcmp(argv[1], "resume"))
		ret = service_command(fd, !strcmp(argv[1], "resume"), expected_port, expected_instance);
	else if (!strcmp(argv[1], "info") && expected_port &&
		 check_boot_owner(fd, expected_port, expected_instance, "INFO"))
		ret = 1;
	else
		ret = !strcmp(argv[1], "boot-info") ? boot_info(fd) : info(fd);
	if (!ret && !strcmp(argv[1], "bootstrap"))
		ret = bootstrap(fd, argc == 4);
	if (!ret && !strcmp(argv[1], "sample"))
		ret = sample(fd);
	if (!ret && !strcmp(argv[1], "session"))
		ret = session(fd, seconds);
	if (close(fd)) {
		perror("close");
		ret = 1;
	}
	return ret;
}
