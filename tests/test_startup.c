// SPDX-License-Identifier: GPL-2.0-only
/* Actual shared startup core, synthetic transport/clock, saved packet bytes. */
#include "../src/gs_startup.h"
#include "../src/gs_runtime.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "startup_fixture.h"

static struct gs_boot_device device(unsigned int pid, gs_u64 now)
{
	return (struct gs_boot_device){
		.port = 7, .instance = pid == 0x100a ? 41 : 42, .enumerated_us = now,
		.vid = 0x3537, .pid = pid, .configuration = 1, .interface_class = 0xff,
		.subclass = pid == 0x100a ? 0x5d : 0x47,
		.protocol = pid == 0x100a ? 1 : 0xd0,
		.in_ep = 0x82, .out_ep = 2, .in_type = 3, .out_type = 3,
		.in_size = pid == 0x100a ? 32 : 64, .out_size = pid == 0x100a ? 32 : 64,
		.in_interval = 1, .out_interval = 8, .exclusive = 1,
	};
}

static void begin(struct gs_startup *s, struct gs_boot_device *d)
{
	memset(s, 0, sizeof(*s));
	*d = device(0x100a, 0);
	assert(gs_boot_begin(s, d, 1, GS_BOOT_SETTLE_US) == 0);
}

static void no_more(struct gs_startup *s, struct gs_boot_device *d)
{
	struct gs_boot_tx tx;
	int original = s->error;

	assert(s->state == GS_BOOT_FAILED && original < 0);
	memset(&tx, 0xaa, sizeof(tx));
	assert(gs_boot_next(s, d, s->now_us, &tx) == original);
	assert(!tx.length && !tx.token && !tx.data[0]);
	assert(gs_boot_begin(s, d, 1, s->now_us) == -EALREADY);
	gs_boot_cancel(s);
	assert(s->error == original);
}

static struct gs_boot_tx issue(struct gs_startup *s, struct gs_boot_device *d)
{
	struct gs_boot_tx tx, second;
	gs_u64 now = s->due_us > s->now_us ? s->due_us : s->now_us;

	assert(gs_boot_next(s, d, now, &tx) == 1);
	assert(tx.port == d->port && tx.instance == d->instance && tx.endpoint == 2);
	assert(tx.data[0] != 9); /* Startup can never request a motor pulse. */
	assert(gs_boot_next(s, d, now, &second) == 0 && !second.length);
	return tx;
}

static void finish(struct gs_startup *s, struct gs_boot_device *d,
		   const struct gs_boot_tx *tx)
{
	assert(gs_boot_complete(s, d, tx->token, 0, tx->length, s->now_us + 1000) == 0);
}

static void reenumerate(struct gs_startup *s, struct gs_boot_device *d)
{
	gs_u64 port = d->port, next_instance = d->instance + 1;

	assert(s->state == GS_BOOT_WAIT_REMOVE);
	assert(gs_boot_removed(s, d->port, d->instance, s->now_us + 100000) == 0);
	*d = device(0x109c, s->now_us + 1000000);
	d->port = port;
	d->instance = next_instance;
	assert(gs_boot_arrived(s, d, d->enumerated_us) == 0);
}

static void advance(struct gs_startup *s, struct gs_boot_device *d, unsigned int count)
{
	unsigned int i;

	begin(s, d);
	for (i = 0; i < count; i++) {
		struct gs_boot_tx tx;

		if (i == 9)
			reenumerate(s, d);
		tx = issue(s, d);
		finish(s, d, &tx);
	}
	if (count == 9)
		reenumerate(s, d);
}

static void ready(struct gs_startup *s, struct gs_boot_device *d, int with_pad)
{
	struct gs_boot_tx tx;

	advance(s, d, 15);
	assert(gs_boot_next(s, d, s->due_us - 1, &tx) == 0);
	assert(s->state == GS_BOOT_INITIALIZE);
	assert(gs_boot_next(s, d, s->due_us, &tx) == 0);
	assert(s->state == GS_BOOT_VERIFY && !s->imu_seen);
	if (with_pad)
		assert(gs_boot_input(s, d, 0x82, 0, captured_pad,
				     sizeof(captured_pad), s->now_us) == GS_PAD_GIP);
	assert(gs_boot_input(s, d, 0x82, 0, captured_imu,
			     sizeof(captured_imu), s->now_us) == GS_IMU);
	assert(gs_boot_next(s, d, s->now_us, &tx) == 0 && !tx.length);
	assert(s->state == GS_BOOT_READY && s->imu_seen);
}

static void capture_replay(void)
{
	struct gs_startup s;
	struct gs_boot_device d;
	struct gs_boot_tx tx;
	struct gs_boot_handoff handoff;
	struct gs_runtime runtime;
	gs_u64 base = GS_BOOT_SETTLE_US, native;
	unsigned int i;

	begin(&s, &d);
	for (i = 0; i < 9; i++) {
		const struct captured_tx *c = &captured_transition[i];

		assert(gs_boot_next(&s, &d, base + c->submit_us, &tx) == 1);
		assert(tx.length == c->length && !memcmp(tx.data, c->data, c->length));
		assert(gs_boot_complete(&s, &d, tx.token, 0, c->length,
					base + c->complete_us) == 0);
	}
	assert(s.transition_completed && !s.native_output_started);
	assert(gs_boot_removed(&s, d.port, d.instance, base + captured_remove_us) == 0);
	native = base + captured_add_us;
	d = device(0x109c, native);
	assert(gs_boot_arrived(&s, &d, native) == 0);
	/* Two separately captured segments, explicitly synthetic join. */
	for (i = 0; i < 6; i++) {
		const struct captured_tx *c = &captured_native[i];

		assert(gs_boot_next(&s, &d, native + c->submit_us, &tx) == 1);
		assert(tx.length == c->length && !memcmp(tx.data, c->data, c->length));
		assert(gs_boot_complete(&s, &d, tx.token, 0, c->length,
					native + c->complete_us) == 0);
	}
	assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, sizeof(captured_imu),
			     native + captured_imu_us) == GS_IMU);
	assert(gs_boot_next(&s, &d, s.now_us, &tx) == 0 && s.state == GS_BOOT_READY);
	assert(gs_boot_takeover(&s, &d, s.now_us, &handoff) == 0);
	assert(handoff.sequence == 6 && handoff.imu_seen && !handoff.pad_seen);
	assert(handoff.next_heartbeat_us > s.now_us);
	assert(gs_boot_next(&s, &d, s.now_us, &tx) == -EALREADY && !tx.length);
	assert(gs_boot_takeover(&s, &d, s.now_us, &handoff) == -EALREADY);
	/* Existing runtime still owns the post-start input policy. */
	assert(gs_runtime_init(&runtime, 0x109c, 1) == 0);
	assert(gs_runtime_accepts(&runtime, GS_PAD_GIP));
	assert(gs_runtime_accepts(&runtime, GS_IMU));
	assert(!gs_runtime_accepts(&runtime, GS_PAD_XINPUT));
}

/* Direct starts use the recorded 109c native-init bytes; the 105e branch
 * remains a synthetic variant, not captured ZZZ packet evidence.
 */
static void direct_variant_start(unsigned int pid)
{
	for (unsigned int failure = 0; failure < 9; failure++) {
		struct gs_startup s = {0};
		struct gs_boot_device d = device(pid, 0);
		struct gs_boot_tx tx;
		struct gs_boot_handoff handoff;
		d.in_interval = 2; d.out_interval = 4;
		assert(gs_boot_supported(&d));
		assert(!gs_boot_begin(&s, &d, 1, 0));
		assert(s.state == GS_BOOT_INITIALIZE && s.old_instance == d.instance);
		for (unsigned int i = 0; i < 6; i++) {
			tx = issue(&s, &d);
			assert(tx.length == captured_native[i].length &&
			       !memcmp(tx.data, captured_native[i].data, tx.length));
			if (failure == i + 1) {
				assert(gs_boot_complete(&s, &d, tx.token, -EPIPE, 0, s.now_us + 1) == -EPIPE);
				assert(s.failed_stage == GS_BOOT_INITIALIZE);
				no_more(&s, &d);
				break;
			}
			finish(&s, &d, &tx);
		}
		assert(!s.transition_completed && s.device.pid == pid &&
		       s.device.instance == d.instance);
		if (failure >= 1 && failure <= 6)
			continue;
		assert(!gs_boot_next(&s, &d, s.due_us, &tx));
		if (failure == 7) {
			assert(gs_boot_next(&s, &d, s.phase_deadline_us, &tx) == -ETIMEDOUT);
			assert(s.failed_stage == GS_BOOT_VERIFY);
			no_more(&s, &d);
			continue;
		}
		if (failure == 8) {
			d.instance++;
			assert(gs_boot_next(&s, &d, s.now_us, &tx) == -ENODEV && !tx.length);
			no_more(&s, &d);
			continue;
		}
		assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu,
				     sizeof(captured_imu), s.now_us) == GS_IMU);
		assert(!gs_boot_next(&s, &d, s.now_us, &tx));
		assert(!gs_boot_takeover(&s, &d, s.now_us, &handoff));
		assert(handoff.instance == d.instance && handoff.port == d.port &&
		       handoff.sequence == 6 && !handoff.pad_seen && handoff.imu_seen);
		assert(gs_boot_takeover(&s, &d, s.now_us, &handoff) == -EALREADY);
	}
	for (unsigned int failure = 0; failure < 5; failure++) {
		struct gs_startup s = {0};
		struct gs_boot_device d = device(pid, 0);
		struct gs_boot_tx tx;
		if (failure == 0) d.exclusive = 0;
		if (failure == 1) d.pid = 0x105d;
		if (failure == 2) d.subclass = 0x5d;
		if (failure == 3) d.in_size = 32;
		assert(gs_boot_begin(&s, &d, failure == 4 ? 0 : 1, 0) < 0);
		assert(gs_boot_next(&s, &d, 0, &tx) < 0 && !tx.length);
		no_more(&s, &d);
	}
}

static void transfer_failures(void)
{
	unsigned int index, failure;

	for (index = 0; index < 15; index++) {
		for (failure = 0; failure < 5; failure++) {
			struct gs_startup s;
			struct gs_boot_device d;
			struct gs_boot_tx tx;
			int ret;

			advance(&s, &d, index);
			tx = issue(&s, &d);
			if (failure == 0)
				ret = gs_boot_complete(&s, &d, tx.token, -EPIPE, 0, s.now_us + 1);
			else if (failure == 1)
				ret = gs_boot_complete(&s, &d, tx.token, 0, tx.length - 1, s.now_us + 1);
			else if (failure == 2)
				ret = gs_boot_complete(&s, &d, tx.token + 1, 0, tx.length, s.now_us + 1);
			else if (failure == 3)
				ret = gs_boot_complete(&s, &d, tx.token, 0, tx.length, s.transfer_deadline_us);
			else {
				d.exclusive = 0;
				ret = gs_boot_complete(&s, &d, tx.token, 0, tx.length, s.now_us + 1);
			}
			assert(ret < 0);
			no_more(&s, &d);
		}
	}
}

static void begin_guards(void)
{
	struct gs_startup s = {0};
	struct gs_boot_device d = device(0x100a, 0);
	struct gs_boot_tx tx;
	unsigned int i;

	assert(gs_boot_begin(&s, &d, 0, 0) == -EPERM);
	no_more(&s, &d);
	memset(&s, 0, sizeof(s));
	assert(gs_boot_begin(&s, &d, 1, 0) == 0);
	assert(gs_boot_next(&s, &d, GS_BOOT_SETTLE_US - 1, &tx) == 0 && !tx.length);
	assert(gs_boot_next(&s, &d, GS_BOOT_SETTLE_US, &tx) == 1);
	assert(gs_boot_begin(&s, &d, 1, s.now_us) == -EALREADY);
	gs_boot_cancel(&s);
	no_more(&s, &d);
	memset(&s, 0, sizeof(s));
	assert(gs_boot_begin(&s, &d, 1, (gs_u64)-1) == -EINVAL);
	memset(&s, 0, sizeof(s));
	d.enumerated_us = 1;
	assert(gs_boot_begin(&s, &d, 1, 0) == -EINVAL);
	for (i = 0; i < 19; i++) {
		unsigned int *fields[16];

		memset(&s, 0, sizeof(s));
		d = device(0x100a, 0);
		fields[0] = &d.vid; fields[1] = &d.pid; fields[2] = &d.configuration;
		fields[3] = &d.interface_number; fields[4] = &d.altsetting;
		fields[5] = &d.interface_class; fields[6] = &d.subclass;
		fields[7] = &d.protocol; fields[8] = &d.in_ep; fields[9] = &d.out_ep;
		fields[10] = &d.in_type; fields[11] = &d.out_type;
		fields[12] = &d.in_size; fields[13] = &d.out_size;
		fields[14] = &d.in_interval; fields[15] = &d.out_interval;
		if (i < 16)
			*fields[i] = *fields[i] ? 0 : 1;
		else if (i == 16)
			d.port = 0;
		else if (i == 17)
			d.instance = 0;
		else
			d.exclusive = 0;
		assert(gs_boot_supported(&d) == (i == 18));
		assert(gs_boot_begin(&s, &d, 1, GS_BOOT_SETTLE_US) < 0);
		no_more(&s, &d);
	}
}

static void enumeration_guards(void)
{
	unsigned int fault;

	for (fault = 0; fault < 9; fault++) {
		struct gs_startup s;
		struct gs_boot_device d, candidate;
		struct gs_boot_tx tx;
		unsigned int i;
		gs_u64 deadline;

		begin(&s, &d);
		for (i = 0; i < 9; i++) {
			tx = issue(&s, &d);
			finish(&s, &d, &tx);
		}
		deadline = s.phase_deadline_us;
		if (fault == 0) {
			assert(gs_boot_next(&s, &d, deadline, &tx) == -ETIMEDOUT);
			no_more(&s, &d);
			continue;
		}
		assert(gs_boot_removed(&s, 999, 555, s.now_us) == 0);
		assert(s.state == GS_BOOT_WAIT_REMOVE);
		assert(gs_boot_removed(&s, d.port, d.instance, s.now_us + 1) == 0);
		assert(s.phase_deadline_us == deadline);
		assert(gs_boot_next(&s, NULL, s.now_us, &tx) == 0);
		candidate = device(0x109c, s.now_us + 10);
		candidate.port = 999;
		assert(gs_boot_arrived(&s, &candidate, s.now_us + 10) == 0);
		assert(s.state == GS_BOOT_WAIT_ADD && s.phase_deadline_us == deadline);
		candidate.port = d.port;
		if (fault == 1) candidate.pid = 0x100a;
		if (fault == 2) candidate.pid = 0x109b;
		if (fault == 3) candidate.instance = d.instance;
		if (fault == 4) candidate.exclusive = 0;
		if (fault == 5) candidate.interface_number = 1;
		if (fault == 6) candidate.enumerated_us = s.removed_us - 1;
		if (fault == 7) candidate.enumerated_us = s.now_us + 1;
		assert(gs_boot_arrived(&s, &candidate, fault == 8 ? deadline : s.now_us) < 0);
		no_more(&s, &d);
	}
}

static void input_and_handoff(void)
{
	struct gs_startup s;
	struct gs_boot_device d, old;
	struct gs_boot_tx tx;
	struct gs_boot_handoff handoff;
	gs_u8 unknown[8] = {3, 0x20, 1, 4, 0x87, 0, 0, 0};
	unsigned int i;

	ready(&s, &d, 1);
	assert(gs_boot_takeover(&s, &d, s.now_us, &handoff) == 0 && handoff.pad_seen);
	gs_boot_cancel(&s);
	assert(s.state == GS_BOOT_HANDED_OFF);
	ready(&s, &d, 0); /* No user motion is needed to initialize. */
	assert(!s.pad_seen);
	d.exclusive = 0;
	assert(gs_boot_takeover(&s, &d, s.now_us, &handoff) == -EBUSY);
	no_more(&s, &d);
	ready(&s, &d, 0);
	assert(gs_boot_takeover(&s, &d, s.now_us + GS_BOOT_FRESH_US + 1, &handoff) < 0);
	no_more(&s, &d);
	advance(&s, &d, 15);
	assert(gs_boot_next(&s, &d, s.due_us, &tx) == 0);
	assert(gs_boot_input(&s, &d, 0x82, 0, unknown, sizeof(unknown), s.now_us) == GS_UNKNOWN);
	assert(!s.imu_seen && s.state == GS_BOOT_VERIFY);
	for (i = 0; i < 4; i++) {
		tx = issue(&s, &d);
		assert(tx.data[0] == 0x0f && tx.data[4] == 0xf2 && tx.data[2] == 7 + i);
		finish(&s, &d, &tx);
	}
	assert(gs_boot_next(&s, &d, s.phase_deadline_us, &tx) == -ETIMEDOUT);
	no_more(&s, &d);
	for (i = 0; i < 4; i++) {
		advance(&s, &d, 15);
		old = d;
		if (i == 0) old.instance--;
		assert(gs_boot_input(&s, &old, i == 1 ? 0x84 : 0x82, i == 2 ? -EPIPE : 0,
				     captured_imu, i == 3 ? 20 : sizeof(captured_imu), s.now_us) < 0);
		no_more(&s, &d);
	}
}

static void ordering_and_deadlines(void)
{
	struct gs_startup s;
	struct gs_boot_device d, wrong;
	struct gs_boot_tx tx;
	unsigned int i;

	for (i = 0; i < 16; i++) {
		advance(&s, &d, i);
		gs_boot_cancel(&s);
		no_more(&s, &d);
	}
	begin(&s, &d);
	assert(gs_boot_removed(&s, d.port, d.instance, s.now_us) < 0);
	no_more(&s, &d);
	begin(&s, &d);
	wrong = device(0x109c, s.now_us);
	assert(gs_boot_arrived(&s, &wrong, s.now_us) < 0);
	no_more(&s, &d);
	begin(&s, &d);
	assert(gs_boot_next(&s, &d, s.now_us - 1, &tx) < 0);
	no_more(&s, &d);
	begin(&s, &d);
	tx = issue(&s, &d);
	finish(&s, &d, &tx);
	assert(gs_boot_complete(&s, &d, tx.token, 0, tx.length, s.now_us) < 0);
	no_more(&s, &d);
	begin(&s, &d);
	tx = issue(&s, &d);
	finish(&s, &d, &tx);
	assert(gs_boot_next(&s, &d, s.due_us - 1, &tx) == 0 && !tx.length);
	assert(gs_boot_next(&s, &d, s.due_us, &tx) == 1);
	assert(gs_boot_next(&s, &d, s.deadline_us, &tx) < 0);
	no_more(&s, &d);
}

static void extra_input_and_ownership_guards(void)
{
	struct gs_startup s;
	struct gs_boot_device d, changed;
	struct gs_boot_tx tx;
	struct gs_boot_handoff handoff;
	gs_u64 expected_heartbeat;
	gs_u8 xinput[20] = {0, 0x14};
	gs_u8 guide_ack[6] = {7, 0x30, 1, 2, 1, 0};
	unsigned int i;

	for (i = 0; i < 6; i++) {
		advance(&s, &d, 9);
		changed = d;
		if (i == 0) changed.port++;
		if (i == 1) changed.instance++;
		if (i == 2) changed.enumerated_us++;
		if (i == 3) changed.pid = 0x100a;
		if (i == 4) changed.out_interval++;
		if (i == 5) changed.in_size = 32;
		assert(gs_boot_next(&s, &changed, s.now_us, &tx) < 0 && !tx.length);
		no_more(&s, &d);
	}
	advance(&s, &d, 15);
	assert(gs_boot_input(&s, &d, 0x82, 0, xinput, sizeof(xinput), s.now_us) < 0);
	no_more(&s, &d);
	advance(&s, &d, 15);
	assert(gs_boot_input(&s, &d, 0x82, 0, guide_ack, sizeof(guide_ack), s.now_us) == -EOPNOTSUPP);
	no_more(&s, &d);
	advance(&s, &d, 15);
	expected_heartbeat = s.due_us + GS_BOOT_HEARTBEAT_US;
	/* A delayed poll must not postpone the inherited maintenance deadline. */
	assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, sizeof(captured_imu), s.due_us + 100000) == GS_IMU);
	assert(gs_boot_next(&s, &d, s.now_us, &tx) == 0 && s.state == GS_BOOT_READY);
	assert(gs_boot_takeover(&s, &d, s.now_us, &handoff) == 0);
	assert(handoff.next_heartbeat_us == expected_heartbeat);
}

static void independent_readiness(void)
{
	struct gs_startup s;
	struct gs_boot_device d;
	struct gs_boot_tx tx;
	struct gs_boot_handoff h;
	unsigned int i;

	advance(&s, &d, 10);
	/* Even fresh valid IMU cannot replace the remaining init completions. */
	assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, sizeof(captured_imu), s.now_us) == GS_IMU);
	assert(s.state == GS_BOOT_INITIALIZE && s.step == 1);
	for (i = 0; i < 5; i++) {
		tx = issue(&s, &d);
		finish(&s, &d, &tx);
	}
	assert(gs_boot_next(&s, &d, s.due_us, &tx) == 0 && s.state == GS_BOOT_READY);

	advance(&s, &d, 15);
	assert(gs_boot_next(&s, &d, s.due_us, &tx) == 0 && s.state == GS_BOOT_VERIFY);
	assert(gs_boot_input(&s, &d, 0x82, 0, captured_pad, sizeof(captured_pad), s.now_us) == GS_PAD_GIP);
	assert(s.pad_seen && !s.imu_seen);
	/* Temporary IMU silence: keep this device and wait, do not re-enumerate. */
	for (i = 0; i < 3; i++) {
		tx = issue(&s, &d);
		finish(&s, &d, &tx);
		assert(s.state == GS_BOOT_VERIFY && s.device.instance == d.instance);
	}
	assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, sizeof(captured_imu), s.now_us) == GS_IMU);
	assert(gs_boot_next(&s, &d, s.now_us, &tx) == 0 && s.state == GS_BOOT_READY);
	assert(gs_boot_takeover(&s, &d, s.now_us, &h) == 0 && h.sequence == 9);

	advance(&s, &d, 15);
	assert(gs_boot_next(&s, &d, s.due_us, &tx) == 0);
	assert(gs_boot_input(&s, &d, 0x82, 0, captured_pad, sizeof(captured_pad), s.now_us) == GS_PAD_GIP);
	assert(gs_boot_next(&s, &d, s.phase_deadline_us, &tx) == -ETIMEDOUT);
	assert(s.failed_stage == GS_BOOT_VERIFY && s.pad_seen && !s.imu_seen);
	assert(s.device.port == d.port && s.device.instance == d.instance);
	assert(s.device.vid == 0x3537 && s.device.pid == 0x109c);
	no_more(&s, &d); /* Readiness timeout retains identity and failure stage. */
}

static void portable_ports_and_multiple_dongles(void)
{
	/* Synthetic adapter tokens: direct 8-6, direct 2-3, hub 2-3.4.1, and
	 * another root with the same hub suffix. No real USB topology is queried.
	 * Production token allocation/hub lifetimes still belong to the adapter.
	 */
	const gs_u64 ports[] = {7, 9101, 0x100000004ULL, 0x200000004ULL};
	struct gs_startup s[2];
	struct gs_boot_device d[2], fresh;
	struct gs_boot_tx tx[2];
	struct gs_boot_handoff h[2];
	unsigned int p, step, n;

	assert(!gs_boot_supported(NULL));
	fresh = device(0x109c, 0);
	fresh.pid = 0x109b;
	assert(!gs_boot_supported(&fresh));
	for (p = 0; p < sizeof(ports) / sizeof(ports[0]); p++) {
		memset(s, 0, sizeof(s));
		for (n = 0; n < 2; n++) {
			d[n] = device(0x100a, 0);
			d[n].port = ports[(p + n) % 4];
			d[n].instance = 100 + n * 100;
			d[n].exclusive = 0;
			assert(gs_boot_supported(&d[n])); /* Recognition is not ownership. */
			d[n].exclusive = 1;
			assert(gs_boot_begin(&s[n], &d[n], 1, GS_BOOT_SETTLE_US) == 0);
		}
		for (step = 0; step < 15; step++) {
			if (step == 9) {
				for (n = 0; n < 2; n++) {
					assert(gs_boot_removed(&s[n], d[n].port, d[n].instance, s[n].now_us + 1) == 0);
					fresh = device(0x109c, s[n].now_us + 1000000);
					fresh.port = d[n].port;
					fresh.instance = d[n].instance + 1;
					d[n] = fresh;
					assert(gs_boot_supported(&d[n]));
				}
				for (n = 0; n < 2; n++) {
					/* Reverse arrival order/another matching dongle cannot steal a session. */
					assert(gs_boot_arrived(&s[n], &d[1 - n], d[n].enumerated_us) == 0);
					assert(s[n].state == GS_BOOT_WAIT_ADD);
					assert(gs_boot_arrived(&s[n], &d[n], d[n].enumerated_us) == 0);
				}
			}
			for (n = 0; n < 2; n++) {
				tx[n] = issue(&s[n], &d[n]);
				finish(&s[n], &d[n], &tx[n]);
			}
		}
		for (n = 0; n < 2; n++) {
			assert(gs_boot_input(&s[n], &d[n], 0x82, 0, captured_imu, sizeof(captured_imu), s[n].due_us) == GS_IMU);
			assert(gs_boot_next(&s[n], &d[n], s[n].now_us, &tx[n]) == 0);
			assert(gs_boot_takeover(&s[n], &d[n], s[n].now_us, &h[n]) == 0);
			assert(h[n].port == d[n].port && h[n].instance == d[n].instance && h[n].sequence == 6);
		}
		assert(h[0].port != h[1].port && h[0].instance != h[1].instance);
	}
	/* An IMU packet from the other dongle cannot confer readiness. */
	advance(&s[0], &d[0], 15);
	fresh = d[0]; fresh.port++;
	assert(gs_boot_input(&s[0], &fresh, 0x82, 0, captured_imu, sizeof(captured_imu), s[0].now_us) == -ENODEV);
	assert(!s[0].imu_seen);
	no_more(&s[0], &d[0]);
}

static void moved_and_reconnected(void)
{
	struct gs_startup old, next = {0};
	struct gs_boot_device d, moved;
	struct gs_boot_tx tx;
	unsigned int i;

	begin(&old, &d);
	for (i = 0; i < 9; i++) {
		tx = issue(&old, &d);
		finish(&old, &d, &tx);
	}
	assert(gs_boot_removed(&old, d.port, d.instance, old.now_us) == 0);
	moved = device(0x109c, old.now_us + 1);
	moved.port = 9101;
	assert(gs_boot_supported(&moved));
	assert(gs_boot_arrived(&old, &moved, moved.enumerated_us) == 0);
	assert(old.state == GS_BOOT_WAIT_ADD && old.device.port == d.port);
	assert(gs_boot_next(&old, NULL, old.phase_deadline_us, &tx) == -ETIMEDOUT);
	no_more(&old, &d); /* Never chase a matching PID to a new port. */
	/* Mere recognition grants no direct start; exact acquisition is required. */
	assert(gs_boot_begin(&next, &moved, 0, old.now_us) == -EPERM);
	for (i = 0; i < 2; i++) {
		memset(&next, 0, sizeof(next));
		moved = device(0x100a, old.now_us);
		moved.port = i ? d.port : 9101;
		moved.instance = 500 + i;
		assert(gs_boot_supported(&moved));
		assert(gs_boot_begin(&next, &moved, 1, old.now_us) == 0);
		assert(gs_boot_next(&next, &moved, next.due_us - 1, &tx) == 0);
		tx = issue(&next, &moved);
		assert(tx.instance == moved.instance && tx.port == moved.port);
		gs_boot_cancel(&next);
		no_more(&next, &moved);
	}
	/* A replaced parent hub must get a new adapter token, even at the same path. */
	advance(&old, &d, 9);
	moved = d; moved.port++;
	assert(gs_boot_next(&old, &moved, old.now_us, &tx) == -ENODEV);
	no_more(&old, &d);
}

/* Diagnose first-native VERIFY without changing timing or accepting fake data.
 * All frames/timestamps below are synthetic, using the actual shared core.
 */
static void direct_sensor_evidence(void)
{
	for (unsigned int condition = 0; condition < 7; condition++) {
		struct gs_startup s = {0};
		struct gs_boot_device d = device(0x109c, 0);
		struct gs_boot_tx tx;
		gs_u8 data[64] = {3, 0x20, 1, 4, 0x87};
		gs_u64 deadline;

		assert(!gs_boot_begin(&s, &d, 1, 0));
		/* PID/descriptor recognition alone grants no sensor-ready state. */
		assert(!s.imu_seen && s.state == GS_BOOT_INITIALIZE);
		for (unsigned int i = 0; i < 6; i++) {
			tx = issue(&s, &d);
			finish(&s, &d, &tx);
		}
		assert(!gs_boot_next(&s, &d, s.due_us, &tx));
		assert(s.state == GS_BOOT_VERIFY && s.step == 6);
		deadline = s.phase_deadline_us;
		if (condition == 1) {
			assert(gs_boot_input(&s, &d, 0x82, 0, data, 8, s.now_us) == GS_UNKNOWN);
		} else if (condition == 2) {
			data[0] = 0x10; data[3] = 0x3c; data[4] = 0xe1;
			assert(gs_boot_input(&s, &d, 0x82, 0, data, 64, s.now_us) == GS_VENDOR);
		} else if (condition == 3) {
			assert(gs_boot_input(&s, &d, 0x82, 0, captured_pad,
					     sizeof(captured_pad), s.now_us) == GS_PAD_GIP);
		} else if (condition == 4) {
			/* A real frame just before the deadline needs no pad/button. */
			assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu,
					     sizeof(captured_imu), deadline - 1) == GS_IMU);
			assert(!gs_boot_next(&s, &d, deadline - 1, &tx));
			assert(s.state == GS_BOOT_READY && s.imu_seen && !s.pad_seen);
			continue;
		} else if (condition == 5) {
			/* Malformed telemetry fails explicitly, not as this timeout. */
			assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu,
					     sizeof(captured_imu) - 1, s.now_us) == -EPROTO);
			no_more(&s, &d);
			continue;
		}
		assert(s.phase_deadline_us == deadline && !s.imu_seen);
		if (condition == 6) {
			assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu,
					     sizeof(captured_imu), deadline) == -ETIMEDOUT);
		} else {
			assert(gs_boot_next(&s, &d, deadline, &tx) == -ETIMEDOUT);
		}
		assert(s.failed_stage == GS_BOOT_VERIFY && s.error == -ETIMEDOUT);
		assert(s.pad_seen == (condition == 3));
		/* Late valid telemetry cannot erase failure or reopen initialization. */
		assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu,
				     sizeof(captured_imu), deadline + 1) == -ETIMEDOUT);
		no_more(&s, &d);
	}
}

static void receiver_wait_cases(void)
{
	for (unsigned int pid_index = 0; pid_index < 3; pid_index++) {
		unsigned int pid = (unsigned int[]){0x100a, 0x109c, 0x105e}[pid_index];
		for (unsigned int test = 0; test < 9; test++) {
			struct gs_startup s = {0};
			struct gs_boot_device d = device(pid, 0), changed;
			struct gs_boot_tx tx;
			struct gs_boot_handoff handoff;
			gs_u64 late = 86400000000ULL;
			unsigned int count = pid == 0x100a ? 15 : 6;

			assert(!gs_boot_begin_receiver(&s, &d, 1, 0));
			for (unsigned int i = 0; i < count; i++) {
				if (pid == 0x100a && i == 9)
					reenumerate(&s, &d);
				tx = issue(&s, &d);
				finish(&s, &d, &tx);
			}
			assert(!gs_boot_next(&s, &d, s.due_us, &tx));
			assert(s.state == GS_BOOT_WAIT_RECEIVER && s.step == 6 && !tx.length);
			for (unsigned int i = 1; i <= 24; i++) {
				assert(!gs_boot_next(&s, &d, late * i / 24, &tx));
				assert(!tx.length && !s.pending_length && s.sequence == 6);
			}
			if (test == 0) {
				assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, 64, late) == GS_IMU);
				assert(!gs_boot_next(&s, &d, late, &tx) && s.state == GS_BOOT_READY);
				assert(!gs_boot_takeover(&s, &d, late, &handoff) && !handoff.pad_seen);
				assert(handoff.sequence == 6 && handoff.next_heartbeat_us > late);
				continue;
			}
			if (test == 1) {
				assert(gs_boot_input(&s, &d, 0x82, 0, captured_pad, sizeof(captured_pad), late) == GS_PAD_GIP);
				assert(!gs_boot_next(&s, &d, late, &tx) && s.state == GS_BOOT_WAIT_RECEIVER);
				gs_boot_cancel(&s);
			} else if (test == 2) {
				assert(gs_boot_input(&s, &d, 0x82, -EPIPE, NULL, 0, late) == -EPIPE);
			} else if (test == 3) {
				assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, 63, late) == -EPROTO);
			} else if (test == 4) {
				changed = d; changed.instance++;
				assert(gs_boot_next(&s, &changed, late, &tx) == -ENODEV);
			} else if (test == 5) {
				changed = d; changed.exclusive = 0;
				assert(gs_boot_next(&s, &changed, late, &tx) == -EBUSY);
			} else if (test == 6) {
				assert(gs_boot_next(&s, &d, late - 1, &tx) == -EINVAL);
			} else if (test == 7) {
				assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, 64, late) == GS_IMU);
				assert(!gs_boot_next(&s, &d, late + GS_BOOT_FRESH_US + 1, &tx));
				assert(s.state == GS_BOOT_WAIT_RECEIVER && !tx.length);
				gs_boot_cancel(&s);
			} else {
				assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, 64, late) == GS_IMU);
				assert(!gs_boot_next(&s, &d, late, &tx));
				assert(gs_boot_takeover(&s, &d, late + GS_BOOT_FRESH_US, &handoff) == -ETIMEDOUT);
			}
			assert(gs_boot_input(&s, &d, 0x82, 0, captured_imu, 64, s.now_us) == s.error);
			no_more(&s, &d);
		}
	}
	/* Waiting cannot extend setup or pending USB-transfer deadlines. */
	struct gs_startup s = {0};
	struct gs_boot_device d = device(0x109c, 0);
	struct gs_boot_tx tx;
	assert(!gs_boot_begin_receiver(&s, &d, 1, 0));
	assert(gs_boot_next(&s, &d, 0, &tx) == 1);
	assert(gs_boot_complete(&s, &d, tx.token, 0, tx.length, GS_BOOT_TRANSFER_US) == -ETIMEDOUT);
	assert(s.failed_stage == GS_BOOT_INITIALIZE);
}

int main(void)
{
	capture_replay();
	direct_variant_start(0x105e);
	direct_variant_start(0x109c);
	transfer_failures();
	begin_guards();
	enumeration_guards();
	input_and_handoff();
	ordering_and_deadlines();
	extra_input_and_ownership_guards();
	independent_readiness();
	portable_ports_and_multiple_dongles();
	moved_and_reconnected();
	direct_sensor_evidence();
	receiver_wait_cases();
	puts("PASS: 15 captured TX packets; 75 per-transfer failures; 109c/experimental 105e direct 6-TX start/failure/same-instance guards, identity, ownership, pacing, deadlines, cancellation, idle-pad liveness, independent IMU, one-shot sequence handoff, four arbitrary topology tokens, two concurrent dongles, port moves and new reconnect sessions; 28 persistent standby cases including day-long no-TX waits and late IMU");
	return 0;
}
