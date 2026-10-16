// SPDX-License-Identifier: GPL-2.0-only
#include "gs_sensor.h"
#ifdef __KERNEL__
#include <linux/math64.h>
#endif

int gs_accel_convert_experimental(const struct gs_accel_experimental_scale *s,
				  const gs_s16 raw[3], gs_s32 out[3])
{
	gs_s32 values[3];
	unsigned int i;
	if (!s || !raw || !out || !s->counts_per_g_num ||
	    s->counts_per_g_num > 1000000 || !s->counts_per_g_den ||
	    s->counts_per_g_den > 1000000)
		return GS_SENSOR_BAD_CONFIG;
	for (i = 0; i < 3; i++) {
		gs_s32 value = raw[i];
		/* Standard gravity = 9806650 micrometres/s^2. Maximum product
		 * 32768 * 9806650 * 1000000 fits u64. Round ties away from zero.
		 */
		gs_u64 magnitude = (gs_u64)(value < 0 ? -value : value) *
			9806650u * s->counts_per_g_den;
		gs_u64 rounded;
#ifdef __KERNEL__
		rounded = div_u64(magnitude + s->counts_per_g_num / 2,
				  s->counts_per_g_num);
#else
		rounded = (magnitude + s->counts_per_g_num / 2) /
			  s->counts_per_g_num;
#endif
		if (rounded > (value < 0 ? 2147483648ULL : 2147483647ULL))
			return GS_SENSOR_RANGE;
		values[i] = value < 0 && rounded == 2147483648ULL ? (-2147483647 - 1) :
			value < 0 ? -(gs_s32)rounded : (gs_s32)rounded;
	}
	for (i = 0; i < 3; i++)
		out[i] = values[i];
	return GS_SENSOR_EXPERIMENTAL;
}

int gs_sensor_ready(const struct gs_sensor_calibration *c)
{
	unsigned int i, used = 0;
	if (!c)
		return GS_SENSOR_BAD_CONFIG;
	if (c->verified & ~GS_SENSOR_VERIFIED)
		return GS_SENSOR_BAD_CONFIG;
	if (c->verified != GS_SENSOR_VERIFIED)
		return GS_SENSOR_NOT_READY;
	if (!c->resolution || c->resolution > 1000000)
		return GS_SENSOR_BAD_CONFIG;
	for (i = 0; i < 3; i++) {
		const struct gs_sensor_axis *a = &c->axis[i];
		if (a->source > 2 || (used & (1u << a->source)) ||
		    (a->sign != -1 && a->sign != 1) ||
		    !a->numerator || a->numerator > 1000000 ||
		    !a->denominator || a->denominator > 1000000 ||
		    a->bias_raw < -32768 || a->bias_raw > 32767)
			return GS_SENSOR_BAD_CONFIG;
		used |= 1u << a->source;
	}
	return GS_SENSOR_OK;
}

int gs_sensor_convert(const struct gs_sensor_calibration *c,
		      const gs_s16 raw[3], gs_s32 out[3])
{
	gs_s32 values[3];
	unsigned int i;
	int ret = gs_sensor_ready(c);
	if (ret)
		return ret;
	if (!raw || !out)
		return GS_SENSOR_BAD_CONFIG;
	for (i = 0; i < 3; i++) {
		const struct gs_sensor_axis *a = &c->axis[i];
		/* Bounds checked above: magnitude <= 65535 * 1000000, fits u64. */
		gs_s32 delta = (gs_s32)raw[a->source] - a->bias_raw;
		int negative = (delta < 0) != (a->sign < 0);
		gs_u64 magnitude = (gs_u64)(delta < 0 ? -delta : delta) * a->numerator;
		gs_u64 rounded;
#ifdef __KERNEL__
		rounded = div_u64(magnitude + a->denominator / 2, a->denominator);
#else
		rounded = (magnitude + a->denominator / 2) / a->denominator;
#endif
		if (rounded > (negative ? 2147483648ULL : 2147483647ULL))
			return GS_SENSOR_RANGE;
		/* Avoid negating INT_MIN in a 32-bit signed expression. */
		values[i] = negative && rounded == 2147483648ULL ? (-2147483647 - 1) :
			negative ? -(gs_s32)rounded : (gs_s32)rounded;
	}
	/* Never leave a partially converted sample on a validation failure. */
	for (i = 0; i < 3; i++)
		out[i] = values[i];
	return GS_SENSOR_OK;
}
