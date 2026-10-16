// SPDX-License-Identifier: GPL-2.0-only
#include "gs_runtime.h"
#ifdef __KERNEL__
#include <linux/errno.h>
#include <linux/string.h>
#else
#include <errno.h>
#include <string.h>
#endif

_Static_assert(GS_HAPTIC_MAX_PULSE_MS == GSN_MAX_PULSE_MS,
	       "Protocol and UAPI motor limits must agree");

static int gs_runtime_data_ready(const struct gs_runtime *r, gs_u64 now)
{
	return !r->data_stale && (!r->persistent || now <= r->last_data_ms ||
				 now - r->last_data_ms <= 2000);
}

int gs_runtime_init(struct gs_runtime *r, unsigned int pid, int output)
{
	if ((pid != 0x100a && !gs_pid_native(pid)) || (output && !gs_pid_native(pid)))
		return -EINVAL;
	memset(r, 0, sizeof(*r));
	r->pid = pid;
	r->output_enabled = !!output;
	r->state = GS_RUNNING;
	return 0;
}

int gs_runtime_accepts(const struct gs_runtime *r, int kind)
{
	if (r->state != GS_RUNNING)
		return 0;
	if (r->pid == 0x100a)
		return kind == GS_PAD_XINPUT;
	return kind == GS_PAD_GIP || kind == GS_IMU || kind == GS_GUIDE;
}

int gs_runtime_start(struct gs_runtime *r, gs_u64 now, unsigned int duration)
{
	if (r->state != GS_RUNNING)
		return -ENODEV;
	if (!r->output_enabled || !gs_pid_native(r->pid) || !r->owner)
		return -EPERM;
	if (r->session_started)
		return -EALREADY;
	if (!duration || duration > GSN_MAX_SESSION_MS || now > (gs_u64)-1 - duration)
		return -EINVAL;
	r->session_started = 1;
	r->session_active = 1;
	r->deadline_ms = now + duration;
	return 0;
}

int gs_runtime_pulse(struct gs_runtime *r, const struct gsn_pulse *p, gs_u64 now)
{
	gs_u8 value[4] = {0};

	if (r->state != GS_RUNNING)
		return -ENODEV;
	gs_runtime_tick(r, now);
	if (!r->owner || !r->output_enabled || !r->session_active)
		return -EPERM;
	if (p->abi_version != GSN_ABI_VERSION || p->motor >= 4 ||
	    p->reserved[0] || p->reserved[1] || p->reserved[2])
		return -EINVAL;
	if (p->flags == GSN_PULSE_CANCEL) {
		if (!r->persistent || p->percent || p->duration_ms)
			return -EINVAL;
		/* A broker cleanup must not cancel a newer ordinary FF grip effect.
		 * Client/peer arbitration is the exclusive broker's responsibility.
		 */
		if (r->private_motor_mask & (1u << p->motor)) {
			r->motors.value[p->motor] = 0;
			r->motors.expiry_ms[p->motor] = 0;
			r->private_motor_mask &= ~(1u << p->motor);
			r->dirty = 1;
		}
		return 0;
	}
	if (!gs_runtime_data_ready(r, now))
		return -EAGAIN;
	if (!p->percent ||
	    p->percent > 100 || !p->duration_ms || p->duration_ms > GSN_MAX_PULSE_MS ||
	    p->flags)
		return -EINVAL;
	/* A pulse must finish before the finite session deadline. */
	if (!r->persistent &&
	    (now > r->deadline_ms || p->duration_ms > r->deadline_ms - now))
		return -ETIME;
	value[p->motor] = p->percent;
	if (gs_haptic_update(&r->motors, 1u << p->motor, value, now, p->duration_ms))
		return -EINVAL;
	/* Last writer owns only this grip; never renew a developer pulse as FF. */
	if (p->motor >= GS_LEFT_GRIP)
		r->ff_target[p->motor - GS_LEFT_GRIP] = 0;
	r->private_motor_mask |= 1u << p->motor;
	r->dirty = 1;
	return 0;
}

int gs_runtime_tick(struct gs_runtime *r, gs_u64 now)
{
	gs_u8 before[4];

	if (r->state != GS_RUNNING)
		return 0;
	if (r->session_active && !r->persistent && now >= r->deadline_ms) {
		gs_runtime_stop(r, 1);
		return 1;
	}
	memcpy(before, r->motors.value, sizeof(before));
	gs_haptic_expire(&r->motors, now);
	for (unsigned int i = 0; i < 4; i++)
		if (!r->motors.value[i])
			r->private_motor_mask &= ~(1u << i);
	if (r->persistent && r->session_active && gs_runtime_data_ready(r, now) &&
	    (r->ff_target[0] || r->ff_target[1]) && now >= r->ff_renew_ms) {
		for (unsigned int i = 0; i < 2; i++) {
			if (!r->ff_target[i])
				continue;
			if (now > (gs_u64)-1 - GSN_MAX_PULSE_MS) {
				r->ff_target[i] = 0;
				r->motors.value[i + GS_LEFT_GRIP] = 0;
				r->motors.expiry_ms[i + GS_LEFT_GRIP] = 0;
			} else {
				r->motors.value[i + GS_LEFT_GRIP] = r->ff_target[i];
				r->motors.expiry_ms[i + GS_LEFT_GRIP] = now + GSN_MAX_PULSE_MS;
			}
		}
		r->ff_renew_ms = now > (gs_u64)-1 - 500 ? (gs_u64)-1 : now + 500;
		r->dirty = 1; /* Refresh the bounded wire lease even at unchanged amplitude. */
	}
	if (memcmp(before, r->motors.value, sizeof(before)))
		r->dirty = 1;
	return r->dirty;
}

/* Only the explicitly enabled kernel bootstrap may choose this policy. The
 * developer START API still requires a finite, nonzero duration.
 */
int gs_runtime_start_persistent(struct gs_runtime *r, gs_u64 now)
{
	if (r->state != GS_RUNNING)
		return -ENODEV;
	if (!r->output_enabled || !gs_pid_native(r->pid) || !r->owner)
		return -EPERM;
	if (r->session_started)
		return -EALREADY;
	r->persistent = 1;
	r->session_active = 1;
	r->session_started = 1;
	r->deadline_ms = 0;
	r->last_data_ms = now;
	return 0;
}

void gs_runtime_note_input(struct gs_runtime *r, int kind, gs_u64 now)
{
	if (r->persistent && r->session_active && r->state == GS_RUNNING &&
	    (kind == GS_IMU || kind == GS_PAD_GIP)) {
		r->last_data_ms = now;
		r->data_stale = 0;
	}
}

/* Missing GIP alone is normal at rest. Either accepted stream proves life.
 * Preserve the session and identity; one neutralization, no mode command.
 */
int gs_runtime_check_idle(struct gs_runtime *r, gs_u64 now)
{
	if (!r->persistent || !r->session_active || r->state != GS_RUNNING ||
	    r->data_stale || now <= r->last_data_ms || now - r->last_data_ms <= 2000)
		return 0;
	r->data_stale = 1;
	gs_runtime_stop(r, 0);
	return 1;
}

/* Linux memless owns effect duration/repetitions and sends a zero update on
 * completion, erase or client close. Retain its intent without a driver timer;
 * tick renews only the short wire lease while input liveness remains confirmed.
 * Only the two grips change; trigger motor deadlines remain independent.
 */
int gs_runtime_rumble(struct gs_runtime *r, gs_u16 strong, gs_u16 weak, gs_u64 now)
{
	gs_u8 value[4] = {0};

	if (r->state != GS_RUNNING)
		return -ENODEV;
	if (!r->persistent || !r->output_enabled || !r->session_active)
		return -EPERM;
	if ((strong || weak) && !gs_runtime_data_ready(r, now))
		return -EAGAIN;
	value[GS_LEFT_GRIP] = (strong * 100u + 32767u) / 65535u;
	value[GS_RIGHT_GRIP] = (weak * 100u + 32767u) / 65535u;
	if (gs_haptic_update(&r->motors, 12, value, now, GSN_MAX_PULSE_MS))
		return -EINVAL;
	r->ff_target[0] = value[GS_LEFT_GRIP];
	r->ff_target[1] = value[GS_RIGHT_GRIP];
	r->private_motor_mask &= ~12u;
	r->ff_renew_ms = now + 500; /* Update validates now + 1000 before mutation. */
	r->dirty = 1;
	return 0;
}

void gs_runtime_stop(struct gs_runtime *r, int end_session)
{
	gs_haptic_clear(&r->motors);
	memset(r->ff_target, 0, sizeof(r->ff_target));
	r->ff_renew_ms = 0;
	r->private_motor_mask = 0;
	r->dirty = 1;
	if (end_session)
		r->session_active = 0;
}

void gs_runtime_halt(struct gs_runtime *r, int state, int error)
{
	/* Disconnect is terminal. No resume, recovery, or mode transition here. */
	if (r->state == GS_DISCONNECTED)
		return;
	gs_runtime_stop(r, 1);
	r->state = state;
	r->error = error;
}
