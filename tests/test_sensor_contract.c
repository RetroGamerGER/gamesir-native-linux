// SPDX-License-Identifier: GPL-2.0-only
/* References in this file test arithmetic, never establish device calibration.
 */
#include "../src/gs_sensor.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static struct gs_sensor_calibration synthetic(unsigned resolution,
					    unsigned num, unsigned den)
{
	struct gs_sensor_calibration c = {0};
	c.verified = GS_SENSOR_VERIFIED;
	c.resolution = resolution;
	for (unsigned i = 0; i < 3; i++)
		c.axis[i] = (struct gs_sensor_axis){num, den, 0, i, 1};
	return c;
}

static void experimental_accel(void)
{
	struct gs_accel_experimental_scale s = {8192, 1};
	gs_s16 raw[3] = {8192, 0, -8192};
	gs_s32 out[3] = {101, 102, 103}, unchanged[3];
	assert(gs_accel_convert_experimental(&s, raw, out) == GS_SENSOR_EXPERIMENTAL);
	assert(out[0] == 9806650 && out[1] == 0 && out[2] == -9806650);
	/* Replacing the scale changes acceleration only; no gyro value exists here. */
	s.counts_per_g_num = 16384;
	assert(gs_accel_convert_experimental(&s, raw, out) == GS_SENSOR_EXPERIMENTAL);
	assert(out[0] == 4903325 && out[2] == -4903325);
	s = (struct gs_accel_experimental_scale){81920, 10};
	raw[0] = 32767; raw[1] = -32768; raw[2] = -1;
	assert(gs_accel_convert_experimental(&s, raw, out) == GS_SENSOR_EXPERIMENTAL);
	assert(out[0] == 39225403 && out[1] == -39226600 && out[2] == -1197);
	s = (struct gs_accel_experimental_scale){4, 1};
	raw[0] = 1; raw[1] = -1; raw[2] = 0;
	assert(gs_accel_convert_experimental(&s, raw, out) == GS_SENSOR_EXPERIMENTAL);
	assert(out[0] == 2451663 && out[1] == -2451663 && out[2] == 0);
	memcpy(unchanged, out, sizeof(out));
	for (unsigned kind = 0; kind < 4; kind++) {
		s = (struct gs_accel_experimental_scale){8192, 1};
		switch (kind) {
		case 0: s.counts_per_g_num = 0; break;
		case 1: s.counts_per_g_den = 0; break;
		case 2: s.counts_per_g_num = 1000001; break;
		case 3: s.counts_per_g_den = 1000001; break;
		}
		assert(gs_accel_convert_experimental(&s, raw, out) == GS_SENSOR_BAD_CONFIG);
		assert(memcmp(out, unchanged, sizeof(out)) == 0);
	}
	s = (struct gs_accel_experimental_scale){1, 1000000};
	raw[0] = 0; raw[1] = 1; raw[2] = 0; /* failure after a valid first axis */
	assert(gs_accel_convert_experimental(&s, raw, out) == GS_SENSOR_RANGE);
	assert(memcmp(out, unchanged, sizeof(out)) == 0);
	assert(gs_accel_convert_experimental(NULL, raw, out) == GS_SENSOR_BAD_CONFIG);
	assert(gs_accel_convert_experimental(&s, NULL, out) == GS_SENSOR_BAD_CONFIG);
	assert(gs_accel_convert_experimental(&s, raw, NULL) == GS_SENSOR_BAD_CONFIG);
}

int main(void)
{
	/* Exact selected profile, including signed endpoints and model/opt-in gates. */
	gs_s16 observed[3] = {-32768, 32767, -1};
	gs_s32 evdev[3] = {11, 22, 33};
	for (unsigned pid = 0; pid < 65536; pid++) {
		assert(gs_gyro_convert_observed(pid, 0, observed, evdev) == GS_SENSOR_NOT_READY);
		if (pid != 0x109c)
			assert(gs_gyro_convert_observed(pid, 1, observed, evdev) == GS_SENSOR_NOT_READY);
	}
	assert(evdev[0] == 11 && evdev[1] == 22 && evdev[2] == 33);
	assert(gs_gyro_convert_observed(0x109c, 1, NULL, evdev) == GS_SENSOR_BAD_CONFIG);
	assert(gs_gyro_convert_observed(0x109c, 1, observed, NULL) == GS_SENSOR_BAD_CONFIG);
	assert(gs_gyro_convert_observed(0x109c, 1, observed, evdev) == GS_SENSOR_EXPERIMENTAL);
	assert(evdev[0] == GS_GYRO_OBSERVED_MIN && evdev[1] == GS_GYRO_OBSERVED_MAX && evdev[2] == -7);
	for (int value = -32768; value <= 32767; value++) {
		observed[0] = observed[1] = observed[2] = value;
		assert(gs_gyro_convert_observed(0x109c, 1, observed, evdev) == GS_SENSOR_EXPERIMENTAL);
		for (unsigned i = 0; i < 3; i++)
			assert(evdev[i] == value * 7);
	}
	struct gs_gyro_clock clock = {0};
	assert(gs_gyro_timestamp(&clock, 1000000) == 1);
	assert(gs_gyro_timestamp(&clock, 17000000) == 16001);
	assert(gs_gyro_timestamp(&clock, 17000600) == 16001);
	assert(gs_gyro_timestamp(&clock, 17001200) == 16002);
	gs_gyro_pause(&clock);
	assert(gs_gyro_timestamp(&clock, 600000000000ULL) == 16003);
	clock.ticks_us = 0x7ffffffe;
	assert(gs_gyro_timestamp(&clock, 600000003000ULL) == 1);
	assert(gs_gyro_timestamp(&clock, 100) == 2);
	experimental_accel();
	gs_s16 raw[3] = {8192, 0, -8192};
	gs_s32 out[3] = {101, 102, 103};
	struct gs_sensor_calibration c = {0};
	assert(gs_sensor_convert(&c, raw, out) == GS_SENSOR_NOT_READY);
	assert(out[0] == 101 && out[1] == 102 && out[2] == 103);
	c = synthetic(10000, 625, 512);
	assert(gs_sensor_convert(&c, raw, out) == 0);
	assert(out[0] == 10000 && out[1] == 0 && out[2] == -10000);
	/* Synthetic fractional gyro sensitivity: 16.4 counts/(degree/s).
	 * 1476 input counts = 90 degree/s, output resolution = 100.
	 */
	c = synthetic(100, 250, 41);
	raw[0] = 1476; raw[1] = -1476; raw[2] = 0;
	assert(gs_sensor_convert(&c, raw, out) == 0);
	assert(out[0] == 9000 && out[1] == -9000 && out[2] == 0);
	/* Nontrivial signed axis map and per-source bias. */
	c = synthetic(1, 1, 1);
	c.axis[0] = (struct gs_sensor_axis){1, 1, 3, 2, -1};
	c.axis[1] = (struct gs_sensor_axis){1, 1, 5, 0, 1};
	c.axis[2] = (struct gs_sensor_axis){1, 1, -2, 1, -1};
	raw[0] = 11; raw[1] = -7; raw[2] = 17;
	assert(gs_sensor_convert(&c, raw, out) == 0);
	assert(out[0] == -14 && out[1] == 6 && out[2] == 5);
	for (unsigned flags = 0; flags < 7; flags++) {
		c.verified = flags;
		assert(gs_sensor_ready(&c) == GS_SENSOR_NOT_READY);
	}
	c = synthetic(1, 1, 2);
	raw[0] = 1; raw[1] = -1; raw[2] = 3;
	assert(gs_sensor_convert(&c, raw, out) == 0);
	assert(out[0] == 1 && out[1] == -1 && out[2] == 2);
	for (unsigned kind = 0; kind < 7; kind++) {
		c = synthetic(1, 1, 1);
		switch (kind) {
		case 0: c.resolution = 0; break;
		case 1: c.axis[0].source = 1; break;
		case 2: c.axis[0].source = 3; break;
		case 3: c.axis[0].sign = 0; break;
		case 4: c.axis[0].denominator = 0; break;
		case 5: c.axis[0].numerator = 1000001; break;
		case 6: c.verified = 15; break;
		}
		assert(gs_sensor_ready(&c) == GS_SENSOR_BAD_CONFIG);
	}
	c = synthetic(1, 1000000, 1);
	raw[0] = 32767;
	gs_s32 unchanged[3]; memcpy(unchanged, out, sizeof(out));
	assert(gs_sensor_convert(&c, raw, out) == GS_SENSOR_RANGE);
	assert(memcmp(out, unchanged, sizeof(out)) == 0);
	assert(gs_sensor_ready(NULL) == GS_SENSOR_BAD_CONFIG);
	printf("PASS: experimental replaceable accel, synthetic units, fractional sensitivity, signed axes, bias, rounding, verification gates, invalid metadata, overflow\n");
	return 0;
}
