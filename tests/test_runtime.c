// SPDX-License-Identifier: GPL-2.0-only
#include "../src/gs_runtime.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>

static unsigned int native_pid;

static void mode_policy(void)
{
	struct gs_runtime r;

	assert(gs_runtime_init(&r, 0x100a, 0) == 0);
	assert(gs_runtime_accepts(&r, GS_PAD_XINPUT));
	assert(!gs_runtime_accepts(&r, GS_PAD_GIP));
	assert(!gs_runtime_accepts(&r, GS_IMU));
	assert(!gs_runtime_accepts(&r, GS_GUIDE));
	assert(gs_runtime_start(&r, 0, 100) == -EPERM);
	assert(gs_runtime_init(&r, 0x100a, 1) == -EINVAL);
	assert(gs_runtime_init(&r, 0x9999, 0) == -EINVAL);
	/* Unselected editions remain rejected; native family shares one runtime. */
	assert(gs_runtime_init(&r, 0x105d, 0) == -EINVAL);
	assert(gs_runtime_init(&r, 0x1022, 1) == -EINVAL);
	assert(gs_runtime_init(&r, native_pid, 0) == 0);
	assert(!gs_runtime_accepts(&r, GS_PAD_XINPUT));
	assert(gs_runtime_accepts(&r, GS_PAD_GIP));
	assert(gs_runtime_accepts(&r, GS_IMU));
	assert(gs_runtime_accepts(&r, GS_GUIDE));
	assert(!gs_runtime_accepts(&r, GS_VENDOR));
	assert(!gs_runtime_accepts(&r, GS_UNKNOWN));
	r.owner = 1;
	assert(gs_runtime_start(&r, 0, 100) == -EPERM);
}

static void bounded_sessions(void)
{
	struct gs_runtime r;
	struct gsn_pulse p = { .abi_version = 1, .motor = 0, .percent = 100, .duration_ms = 400 };

	assert(gs_runtime_init(&r, native_pid, 1) == 0);
	assert(gs_runtime_start(&r, 1000, 1000) == -EPERM);
	r.owner = 1;
	assert(gs_runtime_start(&r, 1000, 0) == -EINVAL);
	assert(gs_runtime_start(&r, 1000, GSN_MAX_SESSION_MS + 1) == -EINVAL);
	assert(gs_runtime_start(&r, (gs_u64)-500, 1000) == -EINVAL);
	assert(gs_runtime_start(&r, 1000, 1000) == 0);
	assert(gs_runtime_start(&r, 1000, 1000) == -EALREADY);
	assert(gs_runtime_pulse(&r, &p, 1000) == 0);
	assert(r.motors.value[0] == 100 && r.motors.expiry_ms[0] == 1400);
	p.motor = 3; p.percent = 75; p.duration_ms = 100;
	assert(gs_runtime_pulse(&r, &p, 1050) == 0);
	assert(r.motors.value[0] == 100 && r.motors.value[3] == 75);
	gs_runtime_tick(&r, 1149);
	assert(r.motors.value[3] == 75);
	gs_runtime_tick(&r, 1150);
	assert(r.motors.value[3] == 0 && r.motors.value[0] == 100);
	gs_runtime_tick(&r, 1400);
	assert(r.motors.value[0] == 0);
	p.duration_ms = 400;
	assert(gs_runtime_pulse(&r, &p, 1601) == -ETIME);
	assert(gs_runtime_pulse(&r, &p, 1600) == 0);
	gs_runtime_tick(&r, 2000);
	assert(!r.session_active && r.motors.value[3] == 0 && r.dirty);
	assert(gs_runtime_pulse(&r, &p, 2000) == -EPERM);
	assert(gs_runtime_start(&r, 2001, 1000) == -EALREADY);
}

static void extended_test_deadline(void)
{
	struct gs_runtime r;
	struct gsn_pulse p = { .abi_version = 1, .motor = 2, .percent = 100, .duration_ms = 400 };
	const unsigned int limits[] = {120000, 300000, GSN_MAX_SESSION_MS};

	for (unsigned int i = 0; i < sizeof(limits) / sizeof(limits[0]); i++) {
		gs_u64 end = 1000 + limits[i];

		assert(gs_runtime_init(&r, native_pid, 1) == 0);
		r.owner = 1;
		assert(gs_runtime_start(&r, 1000, limits[i]) == 0);
		/* A longer session must not lengthen a single motor impulse. */
		assert(gs_runtime_pulse(&r, &p, 91000) == 0);
		gs_runtime_tick(&r, 91399);
		assert(r.motors.value[2] == 100);
		gs_runtime_tick(&r, 91400);
		assert(!r.motors.value[2] && r.session_active);
		assert(gs_runtime_pulse(&r, &p, end - 399) == -ETIME);
		assert(gs_runtime_pulse(&r, &p, end - 400) == 0);
		gs_runtime_tick(&r, end - 1);
		assert(r.session_active && r.motors.value[2] == 100);
		gs_runtime_tick(&r, end);
		assert(!r.session_active && !r.motors.value[2]);
		assert(gs_runtime_pulse(&r, &p, end) == -EPERM);
		assert(gs_runtime_start(&r, end + 1, limits[i]) == -EALREADY);
	}
}

static void invalid_requests(void)
{
	struct gs_runtime r, before;
	struct gsn_pulse good = { .abi_version = 1, .motor = 2, .percent = 100, .duration_ms = 400 };
	struct gsn_pulse bad;

	assert(gs_runtime_init(&r, native_pid, 1) == 0);
	r.owner = 1;
	assert(gs_runtime_start(&r, 0, 1000) == 0);
	assert(gs_runtime_pulse(&r, &good, 1) == 0);
	for (unsigned int field = 0; field < 10; field++) {
		bad = good;
		switch (field) {
		case 0: bad.abi_version = 2; break;
		case 1: bad.motor = 4; break;
		case 2: bad.percent = 0; break;
		case 3: bad.percent = 101; break;
		case 4: bad.duration_ms = 0; break;
		case 5: bad.duration_ms = 1001; break;
		case 6: bad.flags = 1; break;
		case 7: bad.reserved[0] = 1; break;
		case 8: bad.reserved[1] = 1; break;
		case 9: bad.reserved[2] = 1; break;
		}
		memcpy(&before, &r, sizeof(r));
		assert(gs_runtime_pulse(&r, &bad, 2) == -EINVAL);
		assert(memcmp(&before, &r, sizeof(r)) == 0);
	}
	gs_runtime_stop(&r, 0);
	assert(r.session_active && !r.motors.value[2]);
	assert(gs_runtime_pulse(&r, &good, 3) == 0);
	gs_runtime_stop(&r, 1);
	assert(!r.session_active);
	assert(gs_runtime_pulse(&r, &good, 4) == -EPERM);
}

static void one_second_pulses(void)
{
	for (unsigned int motor = 0; motor < 4; motor++) {
		struct gs_runtime r;
		struct gsn_pulse p = { .abi_version = 1, .percent = 100, .duration_ms = 1000 };
		gs_u8 packet[13];

		p.motor = motor;
		assert(gs_runtime_init(&r, native_pid, 1) == 0);
		r.owner = 1;
		assert(gs_runtime_start(&r, 1000, 315000) == 0);
		assert(gs_runtime_pulse(&r, &p, 46000) == 0);
		assert(gs_haptic_packet(packet, 10, &r.motors, 46000) == 13);
		assert(packet[10] == 100 && packet[6 + motor] == 100);
		gs_runtime_tick(&r, 46999);
		assert(r.motors.value[motor] == 100);
		gs_runtime_tick(&r, 47000);
		assert(!r.motors.value[motor] && r.session_active);
		assert(gs_haptic_packet(packet, 11, &r.motors, 47000) == 13 && !packet[10]);
		assert(gs_runtime_pulse(&r, &p, 315001) == -ETIME);
		assert(gs_runtime_pulse(&r, &p, 315000) == 0);
		gs_runtime_tick(&r, 316000);
		assert(!r.session_active && !r.motors.value[motor]);
	}
}

static void terminal_errors(void)
{
	const int states[] = {GS_FAULTED, GS_QUIESCED, GS_DISCONNECTED};
	struct gsn_pulse p = { .abi_version = 1, .motor = 0, .percent = 100, .duration_ms = 400 };

	for (unsigned int i = 0; i < sizeof(states) / sizeof(states[0]); i++) {
		struct gs_runtime r;

		assert(gs_runtime_init(&r, native_pid, 1) == 0);
		r.owner = 1;
		assert(gs_runtime_start(&r, 0, 1000) == 0);
		assert(gs_runtime_pulse(&r, &p, 1) == 0);
		gs_runtime_halt(&r, states[i], -EIO);
		assert(!r.session_active && r.state == states[i] && r.error == -EIO);
		for (unsigned int j = 0; j < 4; j++)
			assert(!r.motors.value[j] && !r.motors.expiry_ms[j]);
		assert(!gs_runtime_accepts(&r, GS_IMU));
		assert(!gs_runtime_accepts(&r, GS_PAD_GIP));
		assert(gs_runtime_pulse(&r, &p, 2) == -ENODEV);
		assert(gs_runtime_start(&r, 2, 1000) == -ENODEV);
		gs_runtime_halt(&r, GS_DISCONNECTED, -ENODEV);
		gs_runtime_halt(&r, GS_FAULTED, -EPIPE);
		assert(r.state == GS_DISCONNECTED);
		assert(r.error == (states[i] == GS_DISCONNECTED ? -EIO : -ENODEV));
	}
}

static void persistent_runtime_and_rumble(void)
{
	struct gs_runtime r, before;
	struct gsn_pulse pulse = {.abi_version = 1, .motor = 0, .percent = 60,
		.duration_ms = 800};
	const gs_u64 late = 30ULL * 24 * 60 * 60 * 1000;

	assert(!gs_runtime_init(&r, 0x100a, 0));
	r.owner = 1;
	assert(gs_runtime_start_persistent(&r, 0) == -EPERM);
	assert(!gs_runtime_init(&r, native_pid, 1));
	assert(gs_runtime_start_persistent(&r, 0) == -EPERM);
	r.owner = 1;
	assert(!gs_runtime_start_persistent(&r, 0));
	assert(r.persistent && r.session_active && !r.deadline_ms);
	assert(gs_runtime_start_persistent(&r, 0) == -EALREADY);
	gs_runtime_tick(&r, late);
	assert(r.session_active); /* Thirty days does not end input/heartbeat runtime. */
	gs_runtime_note_input(&r, GS_IMU, late);
	assert(!gs_runtime_pulse(&r, &pulse, late));
	r.owner = 0; /* Input FF is not gated on an open privileged control client. */
	assert(!gs_runtime_rumble(&r, 65535, 32768, late + 10));
	assert(r.motors.value[0] == 60 && r.motors.value[2] == 100 &&
	       r.motors.value[3] == 50);
	assert(r.motors.expiry_ms[0] == late + 800);
	assert(r.motors.expiry_ms[2] == late + 1010);
	gs_runtime_tick(&r, late + 799);
	assert(r.motors.value[0] == 60);
	assert(!gs_runtime_rumble(&r, 0, 0, late + 799));
	assert(!r.motors.value[2] && !r.motors.value[3] && r.motors.value[0] == 60);
	assert(!gs_runtime_rumble(&r, 65535, 65535, late + 799));
	gs_runtime_tick(&r, late + 800);
	assert(!r.motors.value[0] && r.motors.value[2] == 100);
	gs_runtime_tick(&r, late + 1798);
	assert(r.motors.value[2] == 100);
	gs_runtime_tick(&r, late + 1799);
	assert(r.motors.value[2] == 100 && r.motors.value[3] == 100 && r.session_active);
	assert(!gs_runtime_rumble(&r, 0, 0, late + 1800));
	assert(!r.ff_target[0] && !r.ff_target[1] && !r.motors.value[2]);
	before = r;
	assert(gs_runtime_rumble(&r, 0, 0, (gs_u64)-500) == -EINVAL);
	assert(!memcmp(&before, &r, sizeof(r)));
	r.owner = 1;
	pulse.duration_ms = 1001;
	assert(gs_runtime_pulse(&r, &pulse, late) == -EINVAL);
	gs_runtime_stop(&r, 1);
	assert(!r.session_active);
	assert(gs_runtime_rumble(&r, 1, 1, late) == -EPERM);
	assert(gs_runtime_start_persistent(&r, 0) == -EALREADY);
	for (int state = GS_FAULTED; state <= GS_DISCONNECTED; state++) {
		assert(!gs_runtime_init(&r, native_pid, 1));
		r.owner = 1;
		assert(!gs_runtime_start_persistent(&r, 0));
		assert(!gs_runtime_rumble(&r, 65535, 65535, 0));
		gs_runtime_halt(&r, state, -EIO);
		assert(!r.session_active && !r.motors.value[2] && !r.motors.value[3]);
		assert(gs_runtime_rumble(&r, 65535, 65535, 1) == -ENODEV);
		assert(gs_runtime_start_persistent(&r, 0) == -ENODEV);
	}
}

static void application_ff_duration(void)
{
	const unsigned int duration[] = {5000, 60000, 3600000};
	struct gs_runtime r;
	gs_u8 packet[13];

	for (unsigned int n = 0; n < sizeof(duration) / sizeof(duration[0]); n++) {
		assert(!gs_runtime_init(&r, native_pid, 1));
		r.owner = 1;
		assert(!gs_runtime_start_persistent(&r, 0));
		assert(!gs_runtime_rumble(&r, 65535, 32768, 0));
		for (unsigned int now = 0; now < duration[n]; now += 10) {
			gs_runtime_note_input(&r, GS_IMU, now);
			gs_runtime_tick(&r, now);
			assert(r.motors.value[2] == 100 && r.motors.value[3] == 50);
			if (r.dirty) {
				assert(gs_haptic_packet(packet, 1, &r.motors, now) == 13);
				assert(packet[8] == 100 && packet[9] == 50 && packet[10] == 100);
				assert(now % 500 == 0); /* Application need not resend unchanged FF. */
				r.dirty = 0;
			}
		}
		/* A real Linux memless stop/erase/client-close delivers zero magnitudes. */
		assert(!gs_runtime_rumble(&r, 0, 0, duration[n]));
		for (unsigned int now = duration[n]; now < duration[n] + 5000; now += 500) {
			gs_runtime_note_input(&r, GS_IMU, now);
			gs_runtime_tick(&r, now);
			assert(!r.ff_target[0] && !r.ff_target[1] && !r.motors.value[2] &&
			       !r.motors.value[3]);
		}
	}
	assert(!gs_runtime_init(&r, native_pid, 1));
	r.owner = 1;
	assert(!gs_runtime_start_persistent(&r, 0));
	assert(!gs_runtime_rumble(&r, 65535, 65535, 0));
	struct gsn_pulse pulse = {.abi_version = 1, .motor = GS_LT, .percent = 33,
		.duration_ms = 800};
	assert(!gs_runtime_pulse(&r, &pulse, 10));
	pulse.motor = GS_LEFT_GRIP;
	pulse.percent = 70;
	assert(!gs_runtime_pulse(&r, &pulse, 20));
	assert(!r.ff_target[0] && r.ff_target[1] == 100);
	gs_runtime_tick(&r, 500);
	assert(r.motors.value[0] == 33 && r.motors.value[2] == 70 &&
	       r.motors.value[3] == 100);
	assert(r.motors.expiry_ms[0] == 810 && r.motors.expiry_ms[2] == 820);
	gs_runtime_tick(&r, 820);
	assert(!r.motors.value[0] && !r.motors.value[2] && r.motors.value[3] == 100);
	/* If the worker misses all renewals, the last USB packet still has a 1s lease. */
	assert(gs_haptic_packet(packet, 1, &r.motors, 1500) == 13);
	assert(!packet[8] && !packet[9] && !packet[10]);
	assert(gs_runtime_check_idle(&r, 2001));
	assert(!r.ff_target[0] && !r.ff_target[1]);
	gs_runtime_note_input(&r, GS_IMU, 2010);
	gs_runtime_tick(&r, 2010);
	assert(!r.motors.value[3]); /* Fresh traffic never resurrects discarded FF. */
}

static void four_motor_private_bridge(void)
{
	struct gs_runtime r, before;
	struct gsn_pulse p = {.abi_version = 1, .percent = 10, .duration_ms = 1000};
	struct gsn_pulse cancel = {.abi_version = 1, .flags = GSN_PULSE_CANCEL};
	gs_u8 packet[13];

	assert(!gs_runtime_init(&r, native_pid, 1));
	r.owner = 1;
	assert(!gs_runtime_start_persistent(&r, 0));
	/* Ten seconds, all four application channels kept alive through short leases. */
	for (unsigned now = 0; now < 10000; now += 500) {
		gs_runtime_note_input(&r, GS_IMU, now);
		for (unsigned motor = 0; motor < 4; motor++) {
			p.motor = motor;
			p.percent = (motor + 1) * 11;
			assert(!gs_runtime_pulse(&r, &p, now));
		}
		assert(r.private_motor_mask == 15);
		assert(gs_haptic_packet(packet, 3, &r.motors, now) == 13);
		for (unsigned motor = 0; motor < 4; motor++)
			assert(packet[6 + motor] == (motor + 1) * 11);
		assert(packet[10] == 100);
	}
	for (unsigned motor = 0; motor < 4; motor++) {
		before = r;
		cancel.motor = motor;
		assert(!gs_runtime_pulse(&r, &cancel, 9501));
		for (unsigned other = 0; other < 4; other++) {
			assert(r.motors.value[other] == (other == motor ? 0 : before.motors.value[other]));
			assert(r.motors.expiry_ms[other] ==
			       (other == motor ? 0 : before.motors.expiry_ms[other]));
		}
		assert(r.private_motor_mask == (before.private_motor_mask & ~(1u << motor)));
	}
	assert(r.session_active && !r.private_motor_mask);
	for (unsigned motor = 0; motor < 4; motor++) {
		p.motor = motor;
		assert(!gs_runtime_pulse(&r, &p, 9502));
	}
	assert(!gs_runtime_rumble(&r, 65535, 32768, 9503));
	assert(r.private_motor_mask == 3 && r.motors.value[0] && r.motors.value[1]);
	for (unsigned motor = 2; motor < 4; motor++) {
		before = r;
		cancel.motor = motor;
		assert(!gs_runtime_pulse(&r, &cancel, 9504));
		assert(!memcmp(&before, &r, sizeof(r))); /* Cleanup cannot stop newer game FF. */
	}
	p.motor = GS_LEFT_GRIP;
	p.percent = 88;
	assert(!gs_runtime_pulse(&r, &p, 9505));
	assert(!r.ff_target[0] && r.ff_target[1] == 50);
	cancel.motor = GS_LEFT_GRIP;
	assert(!gs_runtime_pulse(&r, &cancel, 9506));
	assert(!r.motors.value[2] && r.motors.value[3] == 50 && r.motors.value[0]);
	before = r;
	cancel.percent = 1;
	assert(gs_runtime_pulse(&r, &cancel, 9507) == -EINVAL);
	assert(!memcmp(&before, &r, sizeof(r)));
	cancel.percent = 0;
	cancel.duration_ms = 1;
	assert(gs_runtime_pulse(&r, &cancel, 9507) == -EINVAL);
	cancel.duration_ms = 0;
	cancel.reserved[0] = 1;
	assert(gs_runtime_pulse(&r, &cancel, 9507) == -EINVAL);
	cancel.reserved[0] = 0;
	cancel.flags = 3;
	assert(gs_runtime_pulse(&r, &cancel, 9507) == -EINVAL);
	cancel.flags = GSN_PULSE_CANCEL;
	r.owner = 0;
	assert(gs_runtime_pulse(&r, &cancel, 9507) == -EPERM);
	r.owner = 1;
	gs_runtime_halt(&r, GS_QUIESCED, -ESHUTDOWN);
	assert(!r.private_motor_mask && !r.ff_target[0] && !r.ff_target[1]);
	assert(gs_runtime_pulse(&r, &cancel, 9507) == -ENODEV);
	assert(!gs_runtime_init(&r, native_pid, 1));
	r.owner = 1;
	assert(!gs_runtime_start(&r, 0, 1000));
	assert(gs_runtime_pulse(&r, &cancel, 1) == -EINVAL); /* Legacy ABI unchanged. */
}

static void persistent_data_idle(void)
{
	struct gs_runtime r;
	struct gsn_pulse pulse = {.abi_version = 1, .motor = 1, .percent = 75,
		.duration_ms = 1000};

	for (int kind = GS_PAD_GIP; kind <= GS_IMU; kind++) {
		if (kind != GS_PAD_GIP && kind != GS_IMU)
			continue;
		assert(!gs_runtime_init(&r, native_pid, 1));
		r.owner = 1;
		assert(!gs_runtime_start_persistent(&r, 100));
		assert(!gs_runtime_check_idle(&r, 2100)); /* Exactly two seconds is tolerated. */
		gs_runtime_note_input(&r, kind, 2100);
		assert(!gs_runtime_check_idle(&r, 4100));
		assert(!gs_runtime_pulse(&r, &pulse, 4099));
		assert(!gs_runtime_rumble(&r, 65535, 65535, 4099));
		assert(gs_runtime_check_idle(&r, 4101) == 1);
		assert(r.data_stale && r.session_active && r.state == GS_RUNNING &&
		       r.pid == native_pid);
		for (unsigned i = 0; i < 4; i++)
			assert(!r.motors.value[i] && !r.motors.expiry_ms[i]);
		assert(!gs_runtime_check_idle(&r, 999999)); /* No repeated stop/neutral action. */
		assert(gs_runtime_pulse(&r, &pulse, 4102) == -EAGAIN);
		assert(gs_runtime_rumble(&r, 65535, 65535, 4102) == -EAGAIN);
		gs_runtime_note_input(&r, GS_UNKNOWN, 4102);
		gs_runtime_note_input(&r, GS_PAD_XINPUT, 4102);
		assert(r.data_stale); /* Foreign/unknown report cannot clear the gate. */
		gs_runtime_note_input(&r, kind, 4103);
		assert(!r.data_stale && r.session_active && r.pid == native_pid);
		assert(!gs_runtime_pulse(&r, &pulse, 4104));
		assert(!gs_runtime_rumble(&r, 65535, 65535, 4104));
		assert(!gs_runtime_check_idle(&r, 6103));
		assert(gs_runtime_check_idle(&r, 6104));
		gs_runtime_stop(&r, 1);
		gs_runtime_note_input(&r, kind, 6105);
		assert(!r.session_active && r.data_stale); /* END cannot be undone by traffic. */
	}
	assert(!gs_runtime_init(&r, native_pid, 1));
	r.owner = 1;
	assert(!gs_runtime_start(&r, 0, 30000));
	assert(!gs_runtime_check_idle(&r, 2001)); /* Legacy hardware test unchanged. */
}

int main(void)
{
	_Static_assert(sizeof(struct gsn_info) == 56, "stable info ABI");
	_Static_assert(sizeof(struct gsn_sample) == 48, "stable sample ABI");
	_Static_assert(sizeof(struct gsn_pulse) == 32, "stable pulse ABI");
	const unsigned int pids[] = {0x109c, 0x105e};
	for (unsigned int i = 0; i < sizeof(pids) / sizeof(pids[0]); i++) {
		native_pid = pids[i];
		mode_policy();
		bounded_sessions();
		extended_test_deadline();
		one_second_pulses();
		invalid_requests();
		terminal_errors();
		persistent_runtime_and_rumble();
		persistent_data_idle();
		application_ff_duration();
		four_motor_private_bridge();
	}
	puts("PASS: shared 109c/experimental 105e finite/persistent sessions, 30-day runtime, 5s/60s/1h FF with wire leases, simultaneous four-motor bridge, per-channel cancel/FF ownership, stop/overlap/overflow, idle recovery, ABI and fault/suspend/disconnect gates");
	return 0;
}
