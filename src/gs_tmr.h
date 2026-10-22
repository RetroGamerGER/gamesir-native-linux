/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef GS_TMR_H
#define GS_TMR_H
#include "gs_protocol.h"
#include "../include/uapi/gs_native.h"
#ifdef __KERNEL__
#include <linux/errno.h>
#include <linux/string.h>
#else
#include <errno.h>
#include <string.h>
#endif

/* Shared, allocation-free policy. Caller serializes this state. No I/O here.
 * Conservative silence bound, NOT a measured RF disconnect indication.
 */
#define GS_TMR_AGE_NS 1500000000ULL
#define GS_TMR_LEASE_NS 2000000000ULL
struct gs_tmr {
	gs_u64 epoch, generation, number, received_ns, deadline_ns;
	unsigned int phase;
	int error, held, handle, used;
	gs_u8 report[64];
};

static inline void gs_tmr_fail(struct gs_tmr *t, int error)
{
	if (!t->error)
		t->error = error;
	t->phase = 5;
}

static inline int gs_tmr_fresh(const struct gs_tmr *t, gs_u64 now)
{
	return t->number && now >= t->received_ns &&
		now - t->received_ns <= GS_TMR_AGE_NS;
}

static inline void gs_tmr_check(struct gs_tmr *t, gs_u64 now)
{
	if (t->held && t->phase != 5 &&
	    (!gs_tmr_fresh(t, now) || now >= t->deadline_ns))
		gs_tmr_fail(t, -ESTALE);
}

static inline void gs_tmr_invalidate(struct gs_tmr *t, int error)
{
	/* Clearing the sample prevents reuse after PM even before another RX. */
	if (t->held)
		gs_tmr_fail(t, error);
	t->number = t->received_ns = 0;
	if (t->epoch != (gs_u64)-1)
		t->epoch++;
}

static inline void gs_tmr_receive(struct gs_tmr *t, const gs_u8 *d,
				  size_t n, gs_u64 now)
{
	if (n != 64 || d[0] != 0x10 || d[1] || d[3] != 0x3c || d[4] != 0xe0)
		return;
	if ((d[30] | d[31]) & ~3u) {
		if (t->held)
			gs_tmr_fail(t, -EPROTO);
		return;
	}
	if (t->number && now <= t->received_ns) {
		gs_tmr_invalidate(t, -ESTALE);
		return;
	}
	gs_tmr_check(t, now); /* A late frame never resurrects the old lease. */
	if (!t->epoch || (t->number && !gs_tmr_fresh(t, now))) {
		if (t->epoch == (gs_u64)-1) {
			gs_tmr_fail(t, -EOVERFLOW);
			return;
		}
		t->epoch++;
	}
	if (t->number == (gs_u64)-1) {
		gs_tmr_fail(t, -EOVERFLOW);
		return;
	}
	memcpy(t->report, d, 64);
	t->number++;
	t->received_ns = now;
}

/* Operation is consumed before USB submission. Failure is never replayable.
 * Positive result means exactly one three-byte provider message is pending.
 */
static inline int gs_tmr_command(struct gs_tmr *t, unsigned int op,
				  gs_u64 epoch, gs_u64 generation, gs_u64 now)
{
	gs_tmr_check(t, now);
	if (now > (gs_u64)-1 - GS_TMR_LEASE_NS)
		return -EOVERFLOW;
	if (!generation || !epoch || epoch != t->epoch)
		return -ESTALE;
	if (op == GSN_TMR_ACQUIRE) {
		if (t->used || t->held)
			return -EBUSY;
		if (t->error)
			return t->error;
		if (!gs_tmr_fresh(t, now))
			return -ENODATA;
		t->handle = t->held = t->used = 1;
		t->generation = generation;
		t->phase = 1;
		t->deadline_ns = now + GS_TMR_LEASE_NS;
		return 0;
	}
	if (!t->held || generation != t->generation)
		return -ESTALE;
	if (op == GSN_TMR_RELEASE) {
		if (t->phase == 2)
			gs_tmr_fail(t, -ECANCELED);
		t->held = 0;
		return 0; /* Local lease drop only: never an implicit Exit/Finish. */
	}
	if (t->error)
		return t->error;
	if (op == GSN_TMR_RENEW) {
		t->deadline_ns = now + GS_TMR_LEASE_NS;
		return 0;
	}
	if (op == GSN_TMR_START && t->phase == 1) {
		/* Do not join an already active calibration initiated elsewhere. */
		if (t->report[30] || t->report[31])
			return -EBUSY;
		t->phase = 2;
		return 1;
	}
	if ((op == GSN_TMR_FINISH || op == GSN_TMR_EXIT) && t->phase == 2) {
		if (op == GSN_TMR_FINISH && (t->report[30] & t->report[31]) != 3)
			return -EAGAIN;
		t->phase = op == GSN_TMR_FINISH ? 3 : 4;
		return 1;
	}
	return -EINVAL;
}

static inline void gs_tmr_close(struct gs_tmr *t)
{
	if (t->held && t->phase == 2)
		gs_tmr_fail(t, -ECANCELED);
	t->held = t->handle = t->used = 0;
	if (!t->error) {
		t->phase = 0;
		t->generation = t->deadline_ns = 0;
	}
}

/* EXPERIMENTAL USB candidate: standard short GIP length=3, zero padding to
 * match existing vendor OUT64. Provider bytes are proven; Windows provider's
 * complete USB framing/ACK behavior still needs a separately approved capture.
 */
static inline int gs_tmr_packet(gs_u8 out[64], gs_u8 sequence, unsigned int op)
{
	if (op < GSN_TMR_START || op > GSN_TMR_EXIT)
		return -EINVAL;
	memset(out, 0, 64);
	out[0] = 0x0f;
	out[2] = sequence;
	out[3] = 3;
	out[4] = 0xfe;
	out[5] = op - GSN_TMR_START;
	out[6] = op == GSN_TMR_START ? 3 : 0;
	return 64;
}
#endif
