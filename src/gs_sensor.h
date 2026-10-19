/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef GS_SENSOR_H
#define GS_SENSOR_H
#include "gs_protocol.h"

/* Internal offline-prepared conversion contract, NOT a userspace ABI.
 * Verification flags express reviewed evidence; they cannot establish it.
 * No verified G7 Pro calibration is supplied by this project yet.
 */
#define GS_SCALE_VERIFIED 1u
#define GS_AXES_VERIFIED 2u
#define GS_BIAS_VERIFIED 4u
#define GS_SENSOR_VERIFIED 7u
enum gs_sensor_result {
	GS_SENSOR_OK = 0,
	GS_SENSOR_EXPERIMENTAL = 1, /* output written, physical scale unverified */
	GS_SENSOR_NOT_READY = -1,
	GS_SENSOR_BAD_CONFIG = -2,
	GS_SENSOR_RANGE = -3
};
struct gs_sensor_axis {
	gs_u32 numerator, denominator; /* output counts / wire count */
	gs_s32 bias_raw; /* for the selected wire axis, before sign/gain */
	gs_u8 source; /* 0..2, each source used once */
	gs_s8 sign; /* +1 or -1 */
};
struct gs_sensor_calibration {
	gs_u32 verified;
	gs_u32 resolution; /* output counts/g OR counts/(degree/s) */
	struct gs_sensor_axis axis[3]; /* output SDL X, Y, Z */
};
/* Explicit opt-in for accelerometer development only. Sensitivity is
 * counts_per_g_num / counts_per_g_den; the caller supplies the replaceable
 * profile value. No gyro fallback, axis mapping, or bias is inferred.
 */
struct gs_accel_experimental_scale {
	gs_u32 counts_per_g_num, counts_per_g_den;
};
/* Output: micrometres/s^2, including gravity, in wire A0/A1/A2 order.
 * Success returns GS_SENSOR_EXPERIMENTAL, never a verified SDL calibration.
 * Errors leave out unchanged. This API performs no hardware or file access.
 */
int gs_accel_convert_experimental(const struct gs_accel_experimental_scale *scale,
				  const gs_s16 raw[3], gs_s32 out[3]);
/* Separate opt-in evdev experiment: map SDL X/Y/Z to signed 1-based wire
 * axes (+/-1..3). No default map, bias or verified calibration is supplied.
 * evdev requires integral counts/g; reject non-integral rational scales.
 * Both functions leave outputs unchanged on error; success is EXPERIMENTAL.
 */
int gs_accel_evdev_resolution(const struct gs_accel_experimental_scale *scale,
                            const gs_s32 map[3], gs_u32 *resolution);
int gs_accel_evdev_convert(const struct gs_accel_experimental_scale *scale,
                          const gs_s32 map[3], const gs_s16 raw[3], gs_s32 out[3]);
int gs_sensor_ready(const struct gs_sensor_calibration *cal);
int gs_sensor_convert(const struct gs_sensor_calibration *cal,
		      const gs_s16 raw[3], gs_s32 out[3]);

/* User-selected qualitative G7 Pro profile, NOT a verified calibration.
 * SDL frame: +X right, +Y up/out of face, +Z towards the player.
 * The observed body (G0,-G2,G1) becomes SDL (G0,G1,G2).
 * 7 output counts/raw at 100 counts/(degree/s) preserves exactly 0.07.
 * No accelerometer mapping, bias estimate or display sensitivity is applied.
 */
#define GS_GYRO_OBSERVED_RESOLUTION 100
#define GS_GYRO_OBSERVED_MIN (-32768 * 7)
#define GS_GYRO_OBSERVED_MAX (32767 * 7)
int gs_gyro_convert_observed(gs_u16 pid, int enabled,
			     const gs_s16 raw[3], gs_s32 out[3]);

/* Host receive-time clock for evdev, not a sensor/device clock. A paused
 * segment is not integrated on resume. 31-bit us wrap matches SDL's Linux
 * reader; retain sub-us fractions. Call only under the report lock.
 */
struct gs_gyro_clock {
	gs_u64 last_ns;
	gs_u32 ticks_us, fraction_ns;
};
gs_u32 gs_gyro_timestamp(struct gs_gyro_clock *clock, gs_u64 host_ns);
void gs_gyro_pause(struct gs_gyro_clock *clock);
#endif
