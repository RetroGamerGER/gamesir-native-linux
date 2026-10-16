// SPDX-License-Identifier: GPL-2.0-only
#include "gs_protocol.h"
#ifdef __KERNEL__
#include <linux/string.h>
#else
#include <string.h>
#endif

static gs_u16 gs_le16(const gs_u8 *p)
{
	return (gs_u16)p[0] | (gs_u16)p[1] << 8;
}

int gs_decode(const gs_u8 *d, size_t n, struct gs_frame *f)
{
	unsigned int i;
	memset(f, 0, sizeof(*f));
	if (!n || n > 64)
		return -1;
	if (d[0] == 0x20) {
		if (n < 4)
			return -1;
		if (d[1] || (d[3] & 0x80))
			return GS_UNKNOWN;
		/* Only the 36-byte layout observed on this RF dongle is enabled. */
		if (n != 36 || d[3] != 32)
			return -1;
		f->buttons = gs_le16(d + 4);
		f->triggers[0] = gs_le16(d + 6);
		f->triggers[1] = gs_le16(d + 8);
		if (f->triggers[0] > 1023 || f->triggers[1] > 1023)
			return -1;
		for (i = 0; i < 4; i++)
			f->sticks[i] = (gs_s16)gs_le16(d + 10 + 2 * i);
		f->sequence = d[2];
		return f->kind = GS_PAD_GIP;
	}
	if (d[0] == 0x00) {
		if (n != 20 || d[1] != 0x14)
			return -1;
		/* Match xpad's normal button/axis semantics, without deadzones. */
		f->buttons = ((d[2] & 0x10) >> 2) | ((d[2] & 0x20) >> 2) |
			((gs_u16)(d[3] & 0xf0)) | ((gs_u16)(d[2] & 0x0f) << 8) |
			((gs_u16)(d[3] & 0x03) << 12) | ((gs_u16)(d[2] & 0xc0) << 8);
		for (i = 0; i < 4; i++)
			f->sticks[i] = (gs_s16)gs_le16(d + 6 + 2 * i);
		/* Normalize 8-bit legacy triggers to the native 0..1023 range. */
		f->triggers[0] = (d[4] * 1023u + 127u) / 255u;
		f->triggers[1] = (d[5] * 1023u + 127u) / 255u;
		f->guide = !!(d[3] & 4);
		return f->kind = GS_PAD_XINPUT;
	}
	if (d[0] == 0x10) {
		if (n != 64 || d[3] != 0x3c)
			return -1;
		if (d[4] != 0xe0)
			return f->kind = GS_VENDOR;
		for (i = 0; i < 3; i++) {
			f->gyro[i] = (gs_s16)gs_le16(d + 17 + 2 * i);
			f->accel[i] = (gs_s16)gs_le16(d + 23 + 2 * i);
		}
		f->extras[0] = d[57];
		f->extras[1] = d[58];
		return f->kind = GS_IMU;
	}
	/* Source-backed GIP guide packet; not observed in the current capture. */
	if (d[0] == 7) {
		if (n != 6 || d[3] != 2)
			return -1;
		if (d[1] != 0x20 && d[1] != 0x30)
			return GS_UNKNOWN;
		f->sequence = d[2];
		f->guide = !!(d[4] & 3);
		f->ack = d[1] == 0x30;
		return f->kind = GS_GUIDE;
	}
	return GS_UNKNOWN;
}

int gs_motor_packet_timed(gs_u8 out[13], gs_u8 seq, const gs_u8 v[4],
			  unsigned int duration)
{
	unsigned int i;
	int active = v[0] || v[1] || v[2] || v[3];

	if (duration > GS_HAPTIC_MAX_PULSE_MS || (active && !duration))
		return -1;
	for (i = 0; i < 4; i++)
		if (v[i] > 100)
			return -1;
	memset(out, 0, 13);
	out[0] = 9; out[2] = seq; out[3] = 9; out[5] = 15;
	memcpy(out + 6, v, 4);
	out[10] = active ? (duration + 9) / 10 : 0;
	return 13;
}

int gs_motor_packet(gs_u8 out[13], gs_u8 seq, const gs_u8 v[4])
{
	/* Preserve the recorded 400-ms packet contract for existing callers. */
	return gs_motor_packet_timed(out, seq, v, 400);
}

int gs_haptic_packet(gs_u8 out[13], gs_u8 seq,
		     const struct gs_haptics *s, gs_u64 now)
{
	gs_u8 values[4] = {0};
	gs_u64 duration = 0;
	unsigned int i;

	for (i = 0; i < 4; i++) {
		gs_u64 remaining;

		if (!s->value[i] || (s->expiry_ms[i] && s->expiry_ms[i] <= now))
			continue;
		/* The separate FF contract has no pulse deadline; retain 400 ms. */
		remaining = s->expiry_ms[i] ? s->expiry_ms[i] - now : 400;
		if (remaining > GS_HAPTIC_MAX_PULSE_MS)
			return -1;
		values[i] = s->value[i];
		if (remaining > duration)
			duration = remaining;
	}
	return gs_motor_packet_timed(out, seq, values, (unsigned int)duration);
}

void gs_heartbeat(gs_u8 out[64], gs_u8 seq)
{
	memset(out, 0, 64);
	out[0] = 15; out[2] = seq; out[3] = 2; out[4] = 0xf2;
}

void gs_info_request(gs_u8 out[64], gs_u8 seq, gs_u8 selector)
{
	memset(out, 0, 64);
	out[0] = 15; out[2] = seq; out[3] = 1; out[4] = selector;
}

int gs_gip_init(gs_u8 out[64], gs_u8 seq, unsigned int step)
{
	static const gs_u8 packet[3][7] = {
		{5, 0x20, 0, 1, 0}, {0x0a, 0x20, 0, 3, 0, 1, 0x14},
		{6, 0x20, 0, 2, 1, 0}
	};
	static const unsigned int length[3] = {5, 7, 6};
	if (step >= 3)
		return -1;
	memset(out, 0, 64);
	memcpy(out, packet[step], length[step]);
	out[2] = seq;
	return length[step];
}

int gs_transition(gs_u8 out[8], unsigned int step)
{
	static const gs_u8 words[5][2] = {{'g','a'}, {'m','e'}, {'s','i'}, {'r','a'}, {'p','p'}};
	if (step >= 9)
		return -1;
	memset(out, 0, 8);
	out[1] = 8;
	/* Five words interleaved with four empty flush packets. */
	if (!(step & 1)) {
		out[3] = words[step / 2][0];
		out[4] = words[step / 2][1];
	}
	return 8;
}

void gs_guide_ack(gs_u8 out[13], gs_u8 seq)
{
	static const gs_u8 bytes[13] = {1, 0x20, 0, 9, 0, 7, 0x20, 2, 0, 0, 0, 0, 0};
	memcpy(out, bytes, 13);
	out[2] = seq;
}

int gs_haptic_update(struct gs_haptics *s, unsigned int mask,
		     const gs_u8 v[4], gs_u64 now, unsigned int duration)
{
	unsigned int i;
	if (!mask || mask & ~15u || !duration || duration > GS_HAPTIC_MAX_PULSE_MS ||
	    now > (gs_u64)-1 - duration)
		return -1;
	for (i = 0; i < 4; i++)
		if (v[i] > 100 || (!(mask & (1u << i)) && v[i]))
			return -1;
	for (i = 0; i < 4; i++) {
		if (!(mask & (1u << i)))
			continue;
		s->value[i] = v[i];
		s->expiry_ms[i] = v[i] ? now + duration : 0;
	}
	return 0;
}

void gs_haptic_ff(struct gs_haptics *s, gs_u16 strong, gs_u16 weak)
{
	s->value[GS_LEFT_GRIP] = (strong * 100u + 32767u) / 65535u;
	s->value[GS_RIGHT_GRIP] = (weak * 100u + 32767u) / 65535u;
	s->expiry_ms[GS_LEFT_GRIP] = s->expiry_ms[GS_RIGHT_GRIP] = 0;
}

void gs_haptic_expire(struct gs_haptics *s, gs_u64 now)
{
	unsigned int i;
	for (i = 0; i < 4; i++)
		if (s->expiry_ms[i] && now >= s->expiry_ms[i]) {
			s->expiry_ms[i] = 0;
			s->value[i] = 0;
		}
}

void gs_haptic_clear(struct gs_haptics *s)
{
	memset(s, 0, sizeof(*s));
}
