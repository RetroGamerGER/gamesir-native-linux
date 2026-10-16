/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef GS_RUNTIME_H
#define GS_RUNTIME_H
#include "gs_protocol.h"
#include "../include/uapi/gs_native.h"

enum gs_runtime_state {
	GS_RUNNING = 1, GS_FAULTED, GS_QUIESCED, GS_DISCONNECTED
};

/* Caller serializes every access. This contains no USB or kernel objects. */
struct gs_runtime {
	unsigned int pid, output_enabled, session_active, session_started;
	unsigned int owner, dirty, persistent, data_stale;
	int state, error;
	gs_u64 deadline_ms, last_data_ms;
	gs_u64 ff_renew_ms;
	gs_u8 ff_target[2]; /* Persistent application intent for left/right grip. */
	unsigned int private_motor_mask; /* Last writer is the exclusive control API. */
	struct gs_haptics motors;
};

int gs_runtime_init(struct gs_runtime *r, unsigned int pid, int output);
int gs_runtime_accepts(const struct gs_runtime *r, int kind);
int gs_runtime_start(struct gs_runtime *r, gs_u64 now, unsigned int duration);
int gs_runtime_start_persistent(struct gs_runtime *r, gs_u64 now);
void gs_runtime_note_input(struct gs_runtime *r, int kind, gs_u64 now);
int gs_runtime_check_idle(struct gs_runtime *r, gs_u64 now);
int gs_runtime_rumble(struct gs_runtime *r, gs_u16 strong, gs_u16 weak, gs_u64 now);
int gs_runtime_pulse(struct gs_runtime *r, const struct gsn_pulse *p, gs_u64 now);
int gs_runtime_tick(struct gs_runtime *r, gs_u64 now);
void gs_runtime_stop(struct gs_runtime *r, int end_session);
void gs_runtime_halt(struct gs_runtime *r, int state, int error);
#endif
