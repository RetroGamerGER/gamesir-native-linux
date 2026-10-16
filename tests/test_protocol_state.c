// SPDX-License-Identifier: GPL-2.0-only
/* Offline contracts only: no USB transport, real motors or device access. */
#include "../src/gs_protocol.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void expect_rejected(struct gs_haptics *state, unsigned int mask,
			    const gs_u8 values[4], gs_u64 now, unsigned int duration)
{
	struct gs_haptics before;
	memcpy(&before, state, sizeof(before));
	assert(gs_haptic_update(state, mask, values, now, duration) == -1);
	assert(memcmp(&before, state, sizeof(before)) == 0);
}

static void independent_channels(void)
{
	struct gs_haptics state;
	const gs_u8 all[4] = {75, 100, 50, 25};
	const gs_u8 stop[4] = {0};
	const gs_u8 rt[4] = {0, 90, 0, 0};
	gs_haptic_clear(&state);
	assert(gs_haptic_update(&state, 15, all, 1000, 400) == 0);
	/* An explicit LT stop must not cancel either grip or the RT pulse. */
	assert(gs_haptic_update(&state, 1, stop, 1010, 1) == 0);
	assert(state.value[GS_LT] == 0 && state.expiry_ms[GS_LT] == 0);
	assert(state.value[GS_RT] == 100 && state.expiry_ms[GS_RT] == 1400);
	assert(state.value[GS_LEFT_GRIP] == 50 && state.value[GS_RIGHT_GRIP] == 25);
	/* FF owns grip updates only, including FF stop; trigger pulse survives. */
	gs_haptic_ff(&state, 65535, 32768);
	assert(state.value[GS_LEFT_GRIP] == 100 && state.value[GS_RIGHT_GRIP] == 50);
	assert(state.expiry_ms[GS_LEFT_GRIP] == 0 && state.expiry_ms[GS_RIGHT_GRIP] == 0);
	assert(state.value[GS_RT] == 100 && state.expiry_ms[GS_RT] == 1400);
	assert(gs_haptic_update(&state, 2, rt, 1020, 30) == 0);
	gs_haptic_expire(&state, 1049);
	assert(state.value[GS_RT] == 90 && state.value[GS_LEFT_GRIP] == 100);
	gs_haptic_expire(&state, 1050);
	assert(state.value[GS_RT] == 0 && state.expiry_ms[GS_RT] == 0);
	assert(state.value[GS_LEFT_GRIP] == 100 && state.value[GS_RIGHT_GRIP] == 50);
	gs_haptic_expire(&state, 2000);
	assert(state.value[GS_LEFT_GRIP] == 100 && state.value[GS_RIGHT_GRIP] == 50);
	assert(gs_haptic_update(&state, 2, rt, 2000, 400) == 0);
	gs_haptic_ff(&state, 0, 0);
	assert(state.value[GS_RT] == 90 && state.expiry_ms[GS_RT] == 2400);
	assert(state.value[GS_LEFT_GRIP] == 0 && state.value[GS_RIGHT_GRIP] == 0);
	gs_haptic_clear(&state);
	for (unsigned int i = 0; i < 4; i++)
		assert(state.value[i] == 0 && state.expiry_ms[i] == 0);
}

static void all_masks_and_expiry(void)
{
	for (unsigned int mask = 1; mask < 16; mask++) {
		struct gs_haptics state;
		const gs_u8 base[4] = {11, 22, 33, 44};
		gs_u8 values[4] = {0};
		gs_haptic_clear(&state);
		assert(gs_haptic_update(&state, 15, base, 100, 400) == 0);
		for (unsigned int i = 0; i < 4; i++)
			if (mask & (1u << i)) values[i] = 100;
		assert(gs_haptic_update(&state, mask, values, 200, 1) == 0);
		gs_haptic_expire(&state, 200);
		for (unsigned int i = 0; i < 4; i++) {
			assert(state.value[i] == ((mask & (1u << i)) ? 100 : base[i]));
			assert(state.expiry_ms[i] == ((mask & (1u << i)) ? 201 : 500));
		}
		gs_haptic_expire(&state, 201);
		for (unsigned int i = 0; i < 4; i++)
			assert(state.value[i] == ((mask & (1u << i)) ? 0 : base[i]));
		gs_haptic_expire(&state, 500);
		for (unsigned int i = 0; i < 4; i++)
			assert(state.value[i] == 0 && state.expiry_ms[i] == 0);
	}
}

static void invalid_updates_are_atomic(void)
{
	struct gs_haptics state;
	const gs_u8 base[4] = {10, 20, 30, 40};
	gs_u8 value[4] = {50, 0, 0, 0};
	gs_haptic_clear(&state);
	assert(gs_haptic_update(&state, 15, base, 100, 200) == 0);
	expect_rejected(&state, 0, value, 100, 1);
	expect_rejected(&state, 16, value, 100, 1);
	expect_rejected(&state, 0xffffffffu, value, 100, 1);
	expect_rejected(&state, 1, value, 100, 0);
	expect_rejected(&state, 1, value, 100, 1001);
	expect_rejected(&state, 1, value, (gs_u64)-1, 1);
	expect_rejected(&state, 1, value, (gs_u64)-400, 400);
	value[3] = 1; /* Nonselected nonzero channel must reject the whole request. */
	expect_rejected(&state, 1, value, 100, 1);
	value[3] = 101;
	expect_rejected(&state, 15, value, 100, 1);
	value[3] = 255;
	expect_rejected(&state, 15, value, 100, 1);
	value[3] = 0;
	/* Largest representable deadline is allowed; no wrap to zero. */
	assert(gs_haptic_update(&state, 1, value, (gs_u64)-401, 400) == 0);
	assert(state.expiry_ms[GS_LT] == (gs_u64)-1);
	gs_haptic_expire(&state, (gs_u64)-2);
	assert(state.value[GS_LT] == 50);
	gs_haptic_expire(&state, (gs_u64)-1);
	assert(state.value[GS_LT] == 0);
}

static void ff_limits_and_motor_stop(void)
{
	struct gs_haptics state;
	const gs_u8 trigger[4] = {80, 70, 0, 0};
	const gs_u16 input[] = {0, 16384, 32768, 49151, 65535};
	const gs_u8 expected[] = {0, 25, 50, 75, 100};
	gs_haptic_clear(&state);
	assert(gs_haptic_update(&state, 3, trigger, 1, 400) == 0);
	for (unsigned int i = 0; i < sizeof(input) / sizeof(input[0]); i++) {
		gs_haptic_ff(&state, input[i], input[4-i]);
		assert(state.value[GS_LEFT_GRIP] == expected[i]);
		assert(state.value[GS_RIGHT_GRIP] == expected[4-i]);
		assert(state.value[GS_LT] == 80 && state.value[GS_RT] == 70);
		assert(state.expiry_ms[GS_LT] == 401 && state.expiry_ms[GS_RT] == 401);
	}
	gs_u8 out[13];
	const gs_u8 zero[4] = {0};
	assert(gs_motor_packet(out, 255, zero) == 13);
	const gs_u8 stop[13] = {9, 0, 255, 9, 0, 15, 0, 0, 0, 0, 0, 0, 0};
	assert(memcmp(out, stop, sizeof(stop)) == 0);
	memset(out, 0xa5, sizeof(out));
	gs_u8 bad[4] = {0, 0, 0, 101};
	assert(gs_motor_packet(out, 1, bad) == -1);
	for (unsigned int i = 0; i < sizeof(out); i++) assert(out[i] == 0xa5);
}

static void timed_packets_and_remaining_deadlines(void)
{
	struct gs_haptics state;
	gs_u8 out[13], legacy[13];
	const gs_u8 zero[4] = {0};

	for (unsigned int motor = 0; motor < 4; motor++) {
		gs_u8 value[4] = {0};
		gs_u8 expected[13] = {9, 0, 17, 9, 0, 15, 0, 0, 0, 0, 100, 0, 0};

		value[motor] = 100;
		expected[6 + motor] = 100;
		assert(gs_motor_packet_timed(out, 17, value, 1000) == 13);
		assert(!memcmp(out, expected, 13));
		assert(gs_motor_packet(legacy, 17, value) == 13);
		assert(gs_motor_packet_timed(out, 17, value, 400) == 13);
		assert(!memcmp(out, legacy, 13));
		for (unsigned int ms = 1; ms <= 1000; ms++) {
			assert(gs_motor_packet_timed(out, 17, value, ms) == 13);
			assert((unsigned int)out[10] * 10 >= ms);
			assert((unsigned int)out[10] * 10 < ms + 10);
		}
		memset(out, 0xa5, 13);
		assert(gs_motor_packet_timed(out, 17, value, 0) == -1);
		assert(gs_motor_packet_timed(out, 17, value, 1001) == -1);
		assert(gs_motor_packet_timed(out, 17, value, ~0u) == -1);
		for (unsigned int i = 0; i < 13; i++) assert(out[i] == 0xa5);
		gs_haptic_clear(&state);
		assert(gs_haptic_update(&state, 1u << motor, value, 1000, 1000) == 0);
		assert(gs_haptic_packet(out, 17, &state, 1000) == 13);
		assert(!memcmp(out, expected, 13));
		/* Later flushing must not restart the original full-second duration. */
		assert(gs_haptic_packet(out, 17, &state, 1500) == 13 && out[10] == 50);
		assert(gs_haptic_packet(out, 17, &state, 1999) == 13 && out[10] == 1);
		assert(gs_haptic_packet(out, 17, &state, 2000) == 13 && out[10] == 0);
		assert(!memcmp(out + 6, zero, 4));
	}
	gs_haptic_clear(&state);
	state.value[GS_LT] = 100; state.expiry_ms[GS_LT] = 2000;
	state.value[GS_RT] = 80; state.expiry_ms[GS_RT] = 1600;
	assert(gs_haptic_packet(out, 4, &state, 1600) == 13);
	assert(out[6] == 100 && out[7] == 0 && out[10] == 40);
	assert(gs_motor_packet_timed(out, 5, zero, 0) == 13 && out[10] == 0);
	memset(out, 0xa5, 13);
	assert(gs_haptic_packet(out, 6, &state, 998) == -1);
	for (unsigned int i = 0; i < 13; i++) assert(out[i] == 0xa5);
}

static void reject_partial_input(void)
{
	struct gs_frame frame;
	gs_u8 data[65] = {0};
	data[1] = 0x14;
	for (size_t n = 0; n <= sizeof(data); n++)
		assert(gs_decode(data, n, &frame) == (n == 20 ? GS_PAD_XINPUT : -1));
	memset(data, 0, sizeof(data)); data[0] = 0x20; data[3] = 32;
	for (size_t n = 0; n <= sizeof(data); n++)
		assert(gs_decode(data, n, &frame) == (n == 36 ? GS_PAD_GIP : -1));
	data[6] = 0; data[7] = 4; /* Trigger 1024 exceeds the observed range. */
	assert(gs_decode(data, 36, &frame) == -1);
	data[7] = 0; data[1] = 1;
	assert(gs_decode(data, 36, &frame) == GS_UNKNOWN);
	memset(data, 0, sizeof(data)); data[0] = 0x10; data[3] = 0x3c; data[4] = 0xe0;
	for (size_t n = 0; n <= sizeof(data); n++)
		assert(gs_decode(data, n, &frame) == (n == 64 ? GS_IMU : -1));
	data[4] = 5;
	assert(gs_decode(data, 64, &frame) == GS_VENDOR);
	data[0] = 0xff;
	assert(gs_decode(data, 64, &frame) == GS_UNKNOWN);
}

int main(void)
{
	independent_channels();
	all_masks_and_expiry();
	invalid_updates_are_atomic();
	ff_limits_and_motor_stop();
	timed_packets_and_remaining_deadlines();
	reject_partial_input();
	puts("PASS: independent motors, all 15 masks, 1..1000-ms wire durations and remaining deadlines, legacy 400-ms bytes, pulse expiry, FF coexistence, atomic rejection, time overflow, stop packet, incomplete input");
	return 0;
}
