// SPDX-License-Identifier: GPL-2.0-only
#include "gs_startup.h"
#ifdef __KERNEL__
#include <linux/errno.h>
#include <linux/string.h>
#else
#include <errno.h>
#include <string.h>
#endif

static int boot_fail(struct gs_startup *s, int error)
{
	if (s->state != GS_BOOT_FAILED) {
		s->failed_stage = s->state;
		s->state = GS_BOOT_FAILED;
		s->error = error < 0 ? error : -EPROTO;
	}
	return s->error;
}

static int boot_clock(struct gs_startup *s, gs_u64 now)
{
	if (s->state == GS_BOOT_FAILED)
		return s->error;
	if (s->state == GS_BOOT_IDLE || s->state == GS_BOOT_HANDED_OFF)
		return -EALREADY;
	if (now < s->now_us)
		return boot_fail(s, -EINVAL);
	s->now_us = now;
	if ((s->state != GS_BOOT_WAIT_RECEIVER &&
	     (now >= s->deadline_us || now >= s->phase_deadline_us)) ||
	    (s->pending_length && now >= s->transfer_deadline_us))
		return boot_fail(s, -ETIMEDOUT);
	return 0;
}

static gs_u64 boot_after(const struct gs_startup *s, gs_u64 base, gs_u64 delay)
{
	gs_u64 remaining = s->deadline_us - base;

	return base + (delay < remaining ? delay : remaining);
}

int gs_boot_poll(struct gs_startup *s, gs_u64 now)
{
	return boot_clock(s, now);
}

static gs_u64 boot_limit(const struct gs_startup *s, gs_u64 delay)
{
	return boot_after(s, s->now_us, delay);
}

static int boot_descriptor(const struct gs_boot_device *d, unsigned int pid)
{
	unsigned int size = pid == 0x100a ? 32 : 64;

	return d && d->port && d->instance && d->vid == 0x3537 && d->pid == pid &&
		d->configuration == 1 && !d->interface_number && !d->altsetting &&
		d->interface_class == 0xff &&
		d->subclass == (pid == 0x100a ? 0x5d : 0x47) &&
		d->protocol == (pid == 0x100a ? 1 : 0xd0) &&
		d->in_ep == 0x82 && d->out_ep == 2 &&
		d->in_type == 3 && d->out_type == 3 &&
		d->in_size == size && d->out_size == size &&
		d->in_interval && d->in_interval <= 255 &&
		d->out_interval && d->out_interval <= 255;
}

static int boot_current(struct gs_startup *s, const struct gs_boot_device *d)
{
	const struct gs_boot_device *old = &s->device;

	if (!boot_descriptor(d, old->pid) || d->port != old->port ||
	    d->instance != old->instance || d->enumerated_us != old->enumerated_us ||
	    d->in_interval != old->in_interval || d->out_interval != old->out_interval)
		return boot_fail(s, -ENODEV);
	if (d->exclusive != 1)
		return boot_fail(s, -EBUSY);
	return 0;
}

int gs_boot_supported(const struct gs_boot_device *d)
{
	return boot_descriptor(d, 0x100a) || boot_descriptor(d, 0x109c) ||
		boot_descriptor(d, 0x105e);
}

int gs_boot_begin(struct gs_startup *s, const struct gs_boot_device *d,
		  int authorized, gs_u64 now)
{
	if (s->state != GS_BOOT_IDLE)
		return -EALREADY;
	if (authorized != 1)
		return boot_fail(s, -EPERM);
	if (!gs_boot_supported(d) ||
	    d->enumerated_us > now ||
	    now > (gs_u64)-1 - GS_BOOT_TOTAL_US)
		return boot_fail(s, -EINVAL);
	if (d->exclusive != 1)
		return boot_fail(s, -EBUSY);
	s->device = *d;
	s->old_instance = d->instance;
	s->now_us = now;
	s->deadline_us = now + GS_BOOT_TOTAL_US;
	s->phase_deadline_us = s->deadline_us;
	s->due_us = d->enumerated_us + GS_BOOT_SETTLE_US;
	if (s->due_us < now)
		s->due_us = now;
	if (gs_pid_native(d->pid)) {
		/* Already vendor/GIP: use the captured native init, no mode switch. */
		s->state = GS_BOOT_INITIALIZE;
		s->due_us = now;
		s->phase_deadline_us = boot_limit(s, GS_BOOT_VERIFY_US);
	} else {
		s->state = GS_BOOT_TRANSITION;
	}
	return 0;
}

int gs_boot_begin_receiver(struct gs_startup *s, const struct gs_boot_device *d,
			   int authorized, gs_u64 now)
{
	int ret = gs_boot_begin(s, d, authorized, now);

	if (!ret)
		s->receiver_wait = 1;
	return ret;
}

int gs_boot_next(struct gs_startup *s, const struct gs_boot_device *d,
		 gs_u64 now, struct gs_boot_tx *out)
{
	int ret;

	memset(out, 0, sizeof(*out));
	ret = boot_clock(s, now);
	if (ret)
		return ret;
	if (s->state == GS_BOOT_WAIT_ADD)
		return 0;
	ret = boot_current(s, d);
	if (ret)
		return ret;
	if (s->pending_length || s->state == GS_BOOT_WAIT_REMOVE ||
	    s->state == GS_BOOT_READY)
		return 0;
	if (s->state == GS_BOOT_INITIALIZE && s->step == 6) {
		if (now < s->due_us)
			return 0;
		s->state = s->receiver_wait ? GS_BOOT_WAIT_RECEIVER : GS_BOOT_VERIFY;
		s->phase_deadline_us = boot_after(s, s->due_us, GS_BOOT_VERIFY_US);
		/* Same last-init 50-ms settling + 450-ms maintenance as gsn_start. */
		s->due_us = boot_after(s, s->due_us, GS_BOOT_HEARTBEAT_US);
	}
	if (s->state == GS_BOOT_WAIT_RECEIVER) {
		/* Setup is complete and no transfer is outstanding. Silence, neutral
		 * pad reports and unknown status do not restart or finish setup.
		 */
		if (!s->imu_seen || now - s->imu_us > GS_BOOT_FRESH_US)
			return 0;
		if (now > (gs_u64)-1 - GS_BOOT_FRESH_US)
			return boot_fail(s, -EINVAL);
		s->state = GS_BOOT_READY;
		/* Bound the one-shot handoff even after waiting beyond the original
		 * setup deadline. No pending transfer or old failure is revived.
		 */
		s->deadline_us = now + GS_BOOT_FRESH_US;
		s->phase_deadline_us = s->deadline_us;
		s->due_us = now + GS_BOOT_HEARTBEAT_US;
		return 0;
	}
	if (s->state == GS_BOOT_VERIFY) {
		if (s->imu_seen && now - s->imu_us <= GS_BOOT_FRESH_US) {
			s->state = GS_BOOT_READY;
			return 0;
		}
	}
	if (now < s->due_us)
		return 0;
	if (s->state == GS_BOOT_TRANSITION) {
		out->length = gs_transition(out->data, s->step);
	} else {
		s->sequence = s->sequence % 255 + 1;
		if (s->state == GS_BOOT_INITIALIZE && s->step < 3) {
			out->length = gs_gip_init(out->data, s->sequence, s->step);
		} else {
			gs_heartbeat(out->data, s->sequence);
			out->length = 64;
		}
		s->native_output_started = 1;
	}
	out->port = d->port;
	out->instance = d->instance;
	out->endpoint = 2;
	out->token = ++s->token;
	s->pending_length = out->length;
	s->transfer_deadline_us = boot_limit(s, GS_BOOT_TRANSFER_US);
	return 1;
}

int gs_boot_complete(struct gs_startup *s, const struct gs_boot_device *d,
		     unsigned int token, int status, unsigned int actual,
		     gs_u64 now)
{
	int ret = boot_clock(s, now);

	if (ret)
		return ret;
	ret = boot_current(s, d);
	if (ret)
		return ret;
	if (!s->pending_length || token != s->token)
		return boot_fail(s, -EPROTO);
	if (status || actual != s->pending_length)
		return boot_fail(s, status < 0 ? status : -EREMOTEIO);
	s->pending_length = 0;
	if (s->state == GS_BOOT_TRANSITION) {
		s->step++;
		s->due_us = boot_limit(s, GS_BOOT_TRANSITION_GAP_US);
		if (s->step == 9) {
			s->transition_completed = 1;
			s->state = GS_BOOT_WAIT_REMOVE;
			s->phase_deadline_us = boot_limit(s, GS_BOOT_REENUM_US);
		}
	} else if (s->state == GS_BOOT_INITIALIZE) {
		s->step++;
		s->due_us = boot_limit(s, GS_BOOT_INIT_GAP_US);
	} else if (s->state == GS_BOOT_VERIFY) {
		s->due_us = boot_limit(s, GS_BOOT_HEARTBEAT_US);
	} else {
		return boot_fail(s, -EPROTO);
	}
	return 0;
}

int gs_boot_removed(struct gs_startup *s, gs_u64 port, gs_u64 instance, gs_u64 now)
{
	int ret = boot_clock(s, now);

	if (ret)
		return ret;
	if (port != s->device.port)
		return 0; /* An unrelated port never changes this transaction. */
	if (s->state != GS_BOOT_WAIT_REMOVE || s->pending_length ||
	    instance != s->old_instance)
		return boot_fail(s, -ENODEV);
	s->state = GS_BOOT_WAIT_ADD;
	s->removed_us = now;
	return 0; /* Keep the original re-enumeration deadline. */
}

int gs_boot_arrived(struct gs_startup *s, const struct gs_boot_device *d, gs_u64 now)
{
	int ret = boot_clock(s, now);

	if (ret)
		return ret;
	if (!d)
		return boot_fail(s, -EINVAL);
	if (d->port != s->device.port)
		return 0;
	if (s->state != GS_BOOT_WAIT_ADD || !boot_descriptor(d, 0x109c) ||
	    d->instance == s->old_instance || d->enumerated_us > now ||
	    d->enumerated_us < s->removed_us)
		return boot_fail(s, -ENODEV);
	if (d->exclusive != 1)
		return boot_fail(s, -EBUSY);
	s->device = *d;
	s->state = GS_BOOT_INITIALIZE;
	s->step = 0;
	s->due_us = now;
	s->phase_deadline_us = boot_limit(s, GS_BOOT_VERIFY_US);
	return 0;
}

int gs_boot_input(struct gs_startup *s, const struct gs_boot_device *d,
		  unsigned int endpoint, int status, const gs_u8 *data,
		  size_t length, gs_u64 now)
{
	struct gs_frame frame;
	int ret = boot_clock(s, now);

	if (ret)
		return ret;
	ret = boot_current(s, d);
	if (ret)
		return ret;
	if (s->state != GS_BOOT_INITIALIZE && s->state != GS_BOOT_VERIFY &&
	    s->state != GS_BOOT_READY && s->state != GS_BOOT_WAIT_RECEIVER)
		return boot_fail(s, -EPROTO);
	if (status)
		return boot_fail(s, status < 0 ? status : -EPROTO);
	if (endpoint != 0x82 || !data || !length || length > 64)
		return boot_fail(s, -EPROTO);
	ret = gs_decode(data, length, &frame);
	if (ret < 0)
		return boot_fail(s, -EPROTO);
	if (ret == GS_PAD_XINPUT)
		return boot_fail(s, -EPROTO);
	/* No captured bootstrap Guide-ACK exchange yet. Do not silently ignore
	 * a required ACK or allow a second sequence writer during initialization.
	 */
	if (ret == GS_GUIDE && frame.ack)
		return boot_fail(s, -EOPNOTSUPP);
	if (ret == GS_PAD_GIP)
		s->pad_seen = 1;
	if (ret == GS_IMU) {
		s->imu_seen = 1;
		s->imu_us = now;
	}
	return ret;
}

int gs_boot_takeover(struct gs_startup *s, const struct gs_boot_device *d,
		     gs_u64 now, struct gs_boot_handoff *out)
{
	int ret;

	memset(out, 0, sizeof(*out));
	ret = boot_clock(s, now);
	if (ret)
		return ret;
	ret = boot_current(s, d);
	if (ret)
		return ret;
	if (s->state != GS_BOOT_READY || !s->imu_seen ||
	    now - s->imu_us > GS_BOOT_FRESH_US)
		return boot_fail(s, -EPROTO);
	out->port = s->device.port;
	out->instance = s->device.instance;
	out->sequence = s->sequence;
	out->next_heartbeat_us = s->due_us;
	out->pad_seen = s->pad_seen;
	out->imu_seen = s->imu_seen;
	s->state = GS_BOOT_HANDED_OFF;
	return 0;
}

void gs_boot_cancel(struct gs_startup *s)
{
	gs_boot_abort(s, -ECANCELED);
}

void gs_boot_abort(struct gs_startup *s, int error)
{
	if (s->state != GS_BOOT_HANDED_OFF)
		boot_fail(s, error);
}
