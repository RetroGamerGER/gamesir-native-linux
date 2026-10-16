/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef GS_PROTOCOL_H
#define GS_PROTOCOL_H
#ifdef __KERNEL__
#include <linux/types.h>
typedef u8 gs_u8;
typedef u16 gs_u16;
typedef s16 gs_s16;
typedef s8 gs_s8;
typedef s32 gs_s32;
typedef u32 gs_u32;
typedef u64 gs_u64;
#else
#include <stdint.h>
#include <stddef.h>
typedef uint8_t gs_u8;
typedef uint16_t gs_u16;
typedef int16_t gs_s16;
typedef int8_t gs_s8;
typedef int32_t gs_s32;
typedef uint32_t gs_u32;
typedef uint64_t gs_u64;
#endif

/* Shared native protocol family. 105e uses an experimental same-instance start. */
static inline int gs_pid_native(unsigned int pid)
{
	return pid == 0x109c || pid == 0x105e;
}

enum gs_kind { GS_UNKNOWN, GS_PAD_GIP, GS_PAD_XINPUT, GS_IMU, GS_GUIDE, GS_VENDOR };
enum gs_motor { GS_LT, GS_RT, GS_LEFT_GRIP, GS_RIGHT_GRIP, GS_MOTORS };
#define GS_HAPTIC_MAX_PULSE_MS 1000
struct gs_frame {
	int kind;
	gs_u16 buttons; /* GIP bitmap; legacy input is normalized to this layout. */
	gs_s16 sticks[4];
	gs_u16 triggers[2];
	gs_s16 gyro[3], accel[3];
	gs_u8 extras[2], sequence, guide, ack;
};
struct gs_haptics {
	gs_u8 value[GS_MOTORS];
	gs_u64 expiry_ms[GS_MOTORS]; /* zero means controlled by FF, not a pulse */
};
/* Known malformed frames return -1. Unknown types/options return GS_UNKNOWN. */
int gs_decode(const gs_u8 *data, size_t len, struct gs_frame *frame);
int gs_motor_packet(gs_u8 out[13], gs_u8 sequence, const gs_u8 values[4]);
/* Bounded duration in milliseconds; nonzero values use ceil(ms / 10). */
int gs_motor_packet_timed(gs_u8 out[13], gs_u8 sequence,
			  const gs_u8 values[4], unsigned int duration_ms);
/* Encode remaining deadlines; expired channels are zero, never restarted. */
int gs_haptic_packet(gs_u8 out[13], gs_u8 sequence,
		     const struct gs_haptics *state, gs_u64 now_ms);
void gs_heartbeat(gs_u8 out[64], gs_u8 sequence);
void gs_info_request(gs_u8 out[64], gs_u8 sequence, gs_u8 selector);
int gs_gip_init(gs_u8 out[64], gs_u8 sequence, unsigned int step);
int gs_transition(gs_u8 out[8], unsigned int step);
void gs_guide_ack(gs_u8 out[13], gs_u8 sequence);
int gs_haptic_update(struct gs_haptics *state, unsigned int mask,
		     const gs_u8 value[4], gs_u64 now_ms, unsigned int duration_ms);
void gs_haptic_ff(struct gs_haptics *state, gs_u16 strong, gs_u16 weak);
void gs_haptic_expire(struct gs_haptics *state, gs_u64 now_ms);
void gs_haptic_clear(struct gs_haptics *state);
#endif
