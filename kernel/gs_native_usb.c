// SPDX-License-Identifier: GPL-2.0-only
/* Explicit test binding or opt-in, per-device native startup. No autoload. */
#include <linux/capability.h>
#include <linux/compat.h>
#include <linux/delay.h>
#include <linux/iio/buffer.h>
#include <linux/iio/iio.h>
#include <linux/iio/kfifo_buf.h>
#include <linux/iio/sysfs.h>
#include <linux/input.h>
#include <linux/jiffies.h>
#include <linux/kernfs.h>
#include <linux/kref.h>
#include <linux/ktime.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/sched/signal.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/uaccess.h>
#include <linux/usb.h>
#include <linux/workqueue.h>
#include "../src/gs_runtime.h"
#include "../src/gs_sensor.h"
#include "../src/gs_startup.h"

#define GSN_DRIVER "gs_native"
#define GSN_USB_TIMEOUT_MS 250
#define GSN_STALE_NS NSEC_PER_SEC
#define GSN_RX_COMPLETION 1
#define GSN_RX_SUBMIT 2

static bool bootstrap_mode;
module_param(bootstrap_mode, bool, 0400);
MODULE_PARM_DESC(bootstrap_mode, "Opt-in dynamic ports; explicit per-device BOOTSTRAP required, no autoload");
static bool persistent_mode;
module_param(persistent_mode, bool, 0400);
MODULE_PARM_DESC(persistent_mode, "Opt-in service runtime without session deadline; requires bootstrap_mode and enable_output");
static bool receiver_wait;
module_param(receiver_wait, bool, 0400);
MODULE_PARM_DESC(receiver_wait, "Experimental persistent standby after one setup; passive RX only until fresh native IMU, default false");
static char *test_interface;
module_param(test_interface, charp, 0400);
MODULE_PARM_DESC(test_interface, "Exact sysfs interface (e.g. 8-6:1.0); required, single binding only");
static ushort test_pid;
module_param(test_pid, ushort, 0400);
MODULE_PARM_DESC(test_pid, "Exact expected PID: 0x100a, 0x109c or experimental 0x105e; required");
static bool enable_output;
module_param(enable_output, bool, 0400);
MODULE_PARM_DESC(enable_output, "Permit explicit native OUT activation; default false; persistent_mode selects service runtime");
static bool experimental_gyro;
static bool defer_input;
module_param(defer_input, bool, 0400);
MODULE_PARM_DESC(defer_input, "Opt-in two-phase persistent 109c six-axis input; requires updated manager, default false");
module_param(experimental_gyro, bool, 0400);
MODULE_PARM_DESC(experimental_gyro, "Opt-in 109c evdev gyro: observed axes, user-selected 0.07 dps/raw; no accelerometer calibration");
static uint accel_counts_per_g_num = 8192;
module_param(accel_counts_per_g_num, uint, 0400);
MODULE_PARM_DESC(accel_counts_per_g_num, "EXPERIMENTAL replaceable acceleration counts/g numerator");
static uint accel_counts_per_g_den = 1;
module_param(accel_counts_per_g_den, uint, 0400);
/* No guessed accelerometer frame: a separate explicit experiment only. */
static bool experimental_accel;
module_param(experimental_accel, bool, 0400);
MODULE_PARM_DESC(experimental_accel, "Opt-in real 109c evdev acceleration; requires experimental_gyro and explicit accel_axis_map");
static int accel_axis_map[3];
static int accel_axis_map_count;
module_param_array(accel_axis_map, int, &accel_axis_map_count, 0400);
MODULE_PARM_DESC(accel_axis_map, "Experimental SDL X,Y,Z signed wire axes +/-1..3; no default or proven hardware mapping");

static int gsn_sensor_options(void)
{
	struct gs_accel_experimental_scale scale = {
		accel_counts_per_g_num, accel_counts_per_g_den };
	gs_u32 resolution;

	if (!experimental_accel)
		return 0;
	if (!experimental_gyro || accel_axis_map_count != 3 ||
	    gs_accel_evdev_resolution(&scale, accel_axis_map, &resolution) !=
	    GS_SENSOR_EXPERIMENTAL)
		return -EINVAL;
	return 0;
}

static uint session_ms = 30000;
module_param(session_ms, uint, 0400);
MODULE_PARM_DESC(session_ms, "Legacy finite session only: default 30000 ms, hard limit 1..315000 ms");
static atomic_t binding_used = ATOMIC_INIT(0);
static atomic64_t instance_counter = ATOMIC64_INIT(0);
static DEFINE_MUTEX(boot_list_lock);
static LIST_HEAD(boot_list);
static struct usb_driver gsn_driver;

/* One synchronous, explicitly requested claim; never a hotplug permission. */
struct gsn_claim {
	char interface[64];
	unsigned int bus, address, pid;
	u64 device_inode, parent_inode;
	struct usb_interface *intf;
	struct task_struct *task;
	bool consumed;
	bool allow_xpad;
};

static DEFINE_MUTEX(claim_lock);
static DEFINE_SPINLOCK(claim_gate_lock);
static struct gsn_claim *pending_claim;

struct gsn_device;
struct gsn_boot {
	struct kref ref;
	struct list_head node;
	spinlock_t lock; /* Shared core: RX, service and synchronous supervisor. */
	struct gs_startup core;
	struct usb_device *parent, *root, *origin;
	unsigned int portnum, flags;
	/* Last completed OUT, for failure diagnosis only; never ownership proof. */
	unsigned int tx_count, tx_step, tx_expected;
	int tx_status, tx_actual;
	/* Fixed 100a control-IN preamble, separate from interrupt-OUT counters. */
	bool xinput_query_attempted;
	int xinput_query_result;
	/* First nonlocal RX observation; terminal result is recorded separately. */
	int first_rx_status, first_rx_stage;
	unsigned int first_rx_source, first_rx_step, first_rx_pid;
	u64 first_rx_us;
	bool first_rx_deferred, old_rx_quiesced;
	bool handover_attempted;
	struct gsn_device *attached; /* Binding pins it; boot_list_lock guards removal. */
};

struct gsn_device {
	struct kref ref;
	struct usb_device *udev;
	struct usb_interface *intf;
	struct urb *rx_urb;
	u8 *rx_buf, *tx_buf;
	struct input_dev *input;
	struct input_dev *gyro_input;
	struct gs_gyro_clock gyro_clock;
	struct iio_dev *iio;
	struct iio_buffer *iio_buffer;
	struct miscdevice misc;
	char *misc_name;
	char phys[96];
	char gyro_phys[96], sensor_uniq[112];
	struct mutex io_lock; /* All sleeping USB OUT operations and teardown. */
	spinlock_t lock; /* Runtime, sample, counters; also used by RX completion. */
	spinlock_t report_lock; /* Serialize RX input reports against neutralization. */
	struct delayed_work service;
	struct gs_runtime rt;
	struct gs_boot_device identity;
	struct gsn_boot *boot;
	bool boot_handoff, boot_claimed, pm_quiesced, resume_ready, resuming;
	bool direct_native; /* Exact acquire_109c grant, never an unrestricted probe. */
	struct gsn_sample sample;
	u64 input_packets, imu_packets, rejected_packets, iio_push_errors;
	struct gs_accel_experimental_scale accel_scale;
	unsigned long next_heartbeat;
	u8 sequence, ack_sequence;
	int stop_error;
	bool ack_pending, stopping, output_used, stop_sent;
	bool input_registered, iio_registered, misc_registered;
	bool gyro_registered;
	bool input_deferred, publication_cancelled, have_deferred_pad, last_guide;
	struct gs_frame deferred_pad;
	u8 deferred_extras[2];
	bool iio_buffer_active; /* report_lock: push vs buffer layout changes. */
};

static bool gsn_boot_service(struct gsn_device *g);
static int gsn_boot_rx(struct gsn_device *g, struct urb *urb);
static bool gsn_boot_rx_teardown(struct gsn_device *g, int status, unsigned int source);
static void gsn_boot_detach(struct gsn_device *g);
static void gsn_boot_cancel_device(struct gsn_device *g);
static void gsn_quiesce(struct gsn_device *g, int state, int error);
static int gsn_gyro_register(struct gsn_device *g);

static u64 gsn_now_us(void)
{
	return ktime_to_us(ktime_get());
}

static void gsn_boot_delete(struct kref *ref)
{
	struct gsn_boot *b = container_of(ref, struct gsn_boot, ref);

	usb_put_dev(b->origin);
	usb_put_dev(b->parent);
	usb_put_dev(b->root);
	kfree(b);
}

static u64 gsn_now_ms(void)
{
	return ktime_to_ms(ktime_get());
}

static void gsn_delete(struct kref *ref)
{
	struct gsn_device *g = container_of(ref, struct gsn_device, ref);

	if (g->boot)
		kref_put(&g->boot->ref, gsn_boot_delete);
	usb_free_urb(g->rx_urb);
	kfree(g->rx_buf);
	kfree(g->tx_buf);
	kfree(g->misc_name);
	usb_put_intf(g->intf);
	usb_put_dev(g->udev);
	kfree(g);
}

static u8 gsn_sequence(struct gsn_device *g)
{
	/* Only io_lock holders allocate sequences. Skip zero like Deadband. */
	g->sequence = g->sequence % 255 + 1;
	return g->sequence;
}

static void gsn_fault(struct gsn_device *g, int error)
{
	struct gsn_boot *b;
	unsigned long flags;

	spin_lock_irqsave(&g->lock, flags);
	if (!g->stopping && g->rt.state == GS_RUNNING) {
		gs_runtime_halt(&g->rt, GS_FAULTED, error);
		/* Latch a terminal cause at its producer. A last OUT completion,
		 * disconnect or READY/adopt racing the next worker must not win over it.
		 * Lock order matches adoption/retirement: runtime, then bootstrap.
		 */
		b = smp_load_acquire(&g->boot);
		if (b && !g->boot_handoff) {
			spin_lock(&b->lock);
			gs_boot_abort(&b->core, error);
			spin_unlock(&b->lock);
		}
		/* Queuing and stopping share this lock: no late work after drain. */
		mod_delayed_work(system_percpu_wq, &g->service, 0);
	}
	spin_unlock_irqrestore(&g->lock, flags);
}

/* io_lock held. NULL packet encodes current motor deadlines at the send gate.
 * DMA buffer is heap-backed, never a caller's stack packet.
 */
static int gsn_send(struct gsn_device *g, const u8 *packet, int len, bool stop)
{
	unsigned long flags;
	int ret, actual = 0;
	bool allowed;
	u64 now;

	if (len < 1 || len > 64 || (!packet && (len != 13 || stop)))
		return -EINVAL;

	spin_lock_irqsave(&g->lock, flags);
	now = gsn_now_ms();
	if (!stop)
		gs_runtime_tick(&g->rt, now);
	allowed = g->rt.output_enabled && gs_pid_native(g->rt.pid) &&
		(stop || (!g->stopping && g->rt.state == GS_RUNNING && g->rt.session_active &&
			  READ_ONCE(g->intf->condition) == USB_INTERFACE_BOUND));
	ret = 0;
	if (allowed && !packet &&
	    gs_haptic_packet(g->tx_buf, gsn_sequence(g), &g->rt.motors, now) != len)
		ret = -EINVAL;
	spin_unlock_irqrestore(&g->lock, flags);
	if (!allowed)
		return -EPERM;
	if (ret) {
		gsn_fault(g, ret);
		return ret;
	}
	if (packet)
		memcpy(g->tx_buf, packet, len);
	ret = usb_interrupt_msg(g->udev, usb_sndintpipe(g->udev, 2),
				g->tx_buf, len, &actual, GSN_USB_TIMEOUT_MS);
	if (!ret && actual != len)
		ret = -EREMOTEIO;
	if (ret && !stop)
		gsn_fault(g, ret);
	return ret;
}

/* One best-effort zero packet on fault/close/unbind; no retry loop. */
static int gsn_stop(struct gsn_device *g, bool end_session)
{
	u8 packet[13], zero[4] = {0};
	unsigned long flags;
	int ret = 0;

	spin_lock_irqsave(&g->lock, flags);
	gs_runtime_stop(&g->rt, end_session);
	g->rt.dirty = 0;
	spin_unlock_irqrestore(&g->lock, flags);
	if (g->output_used && g->stop_sent)
		return g->stop_error;
	if (g->output_used) {
		g->stop_sent = true;
		gs_motor_packet(packet, gsn_sequence(g), zero);
		ret = gsn_send(g, packet, sizeof(packet), true);
		g->stop_error = ret;
		if (ret) {
			gsn_fault(g, ret);
			dev_warn(&g->udev->dev, "final motor stop failed: %d; no retry\n", ret);
		}
	}
	return ret;
}

static int gsn_flush_motors(struct gsn_device *g)
{
	unsigned long flags;
	bool dirty;

	spin_lock_irqsave(&g->lock, flags);
	gs_runtime_tick(&g->rt, gsn_now_ms());
	dirty = g->rt.dirty;
	g->rt.dirty = 0;
	spin_unlock_irqrestore(&g->lock, flags);
	if (!dirty)
		return 0;
	g->stop_error = 0;
	g->stop_sent = false; /* Even a failed nonzero transfer may reach hardware. */
	return gsn_send(g, NULL, 13, false);
}

static void gsn_neutral(struct gsn_device *g);
static void gsn_neutral_locked(struct gsn_device *g);
static void gsn_gyro_report(struct gsn_device *g, const gs_s16 raw[3],
			    const gs_s16 accel[3], u64 host_ns);
static int gsn_input_control(struct gsn_device *g, unsigned int cmd, void __user *user);

/* report_lock held. Preserve held buttons while the gamepad is unpublished. */
static void gsn_extras(struct gsn_device *g, const u8 extras[2])
{
	memmove(g->deferred_extras, extras, 2);
	g->last_guide = !!(extras[0] & 1);
	if (!g->input_registered)
		return;
	input_report_key(g->input, BTN_MODE, g->last_guide);
	input_report_key(g->input, KEY_RECORD, !!(extras[0] & 2));
	input_report_key(g->input, BTN_TRIGGER_HAPPY1, !!(extras[0] & 8));
	input_report_key(g->input, BTN_TRIGGER_HAPPY2, !!(extras[0] & 16));
	input_report_key(g->input, BTN_TRIGGER_HAPPY3, !!(extras[1] & 1));
	input_report_key(g->input, BTN_TRIGGER_HAPPY4, !!(extras[1] & 2));
	input_report_key(g->input, BTN_TRIGGER_HAPPY5, !!(extras[0] & 32));
	input_sync(g->input);
}

/* io_lock held. report_lock is always outside rt.lock; input reporting never
 * holds rt.lock because FF callbacks arrive holding input's own event lock.
 */
static int gsn_check_idle(struct gsn_device *g)
{
	unsigned long flags;
	bool stale;

	spin_lock_irqsave(&g->report_lock, flags);
	spin_lock(&g->lock);
	stale = gs_runtime_check_idle(&g->rt, gsn_now_ms());
	spin_unlock(&g->lock);
	if (stale)
		gsn_neutral_locked(g);
	spin_unlock_irqrestore(&g->report_lock, flags);
	return stale ? gsn_stop(g, false) : 0;
}

static void gsn_service(struct work_struct *work)
{
	struct gsn_device *g = container_of(to_delayed_work(work), struct gsn_device, service);
	unsigned long flags;
	u8 packet[64], ack = 0;
	bool active, pending;
	int state, ret = 0;

	mutex_lock(&g->io_lock);
	spin_lock_irqsave(&g->lock, flags);
	if (g->stopping) {
		spin_unlock_irqrestore(&g->lock, flags);
		goto out;
	}
	spin_unlock_irqrestore(&g->lock, flags);
	if (gsn_boot_service(g))
		goto out;
	ret = gsn_check_idle(g);
	if (ret)
		goto out;
	spin_lock_irqsave(&g->lock, flags);
	gs_runtime_tick(&g->rt, gsn_now_ms());
	state = g->rt.state;
	active = g->rt.session_active;
	pending = g->ack_pending;
	ack = g->ack_sequence;
	g->ack_pending = false;
	spin_unlock_irqrestore(&g->lock, flags);
	if (state != GS_RUNNING || !active) {
		if (state != GS_RUNNING) {
			usb_kill_urb(g->rx_urb);
			gsn_neutral(g);
		}
		gsn_stop(g, true);
		goto out;
	}
	if (pending) {
		gs_guide_ack(packet, ack);
		ret = gsn_send(g, packet, 13, false);
	}
	if (!ret)
		ret = gsn_flush_motors(g);
	if (!ret && time_after_eq(jiffies, g->next_heartbeat)) {
		gs_heartbeat(packet, gsn_sequence(g));
		ret = gsn_send(g, packet, 64, false);
		g->next_heartbeat = jiffies + msecs_to_jiffies(450);
	}
	if (ret) {
		gsn_stop(g, true);
		goto out;
	}
	spin_lock_irqsave(&g->lock, flags);
	if (!g->stopping && g->rt.state == GS_RUNNING && g->rt.session_active)
		mod_delayed_work(system_percpu_wq, &g->service, msecs_to_jiffies(10));
	spin_unlock_irqrestore(&g->lock, flags);
out:
	mutex_unlock(&g->io_lock);
}

static void gsn_pad(struct gsn_device *g, const struct gs_frame *f)
{
	static const unsigned int keys[] = {
		BTN_START, BTN_SELECT, BTN_SOUTH, BTN_EAST, BTN_NORTH, BTN_WEST,
		0, 0, 0, 0, BTN_TL, BTN_TR, BTN_THUMBL, BTN_THUMBR
	};
	unsigned int i;

	for (i = 0; i < ARRAY_SIZE(keys); i++)
		if (keys[i])
			input_report_key(g->input, keys[i], !!(f->buttons & BIT(i + 2)));
	input_report_abs(g->input, ABS_HAT0X, !!(f->buttons & BIT(11)) - !!(f->buttons & BIT(10)));
	input_report_abs(g->input, ABS_HAT0Y, !!(f->buttons & BIT(9)) - !!(f->buttons & BIT(8)));
	input_report_abs(g->input, ABS_X, f->sticks[0]);
	input_report_abs(g->input, ABS_Y, ~f->sticks[1]);
	input_report_abs(g->input, ABS_RX, f->sticks[2]);
	input_report_abs(g->input, ABS_RY, ~f->sticks[3]);
	input_report_abs(g->input, ABS_Z, f->triggers[0]);
	input_report_abs(g->input, ABS_RZ, f->triggers[1]);
	if (f->kind == GS_PAD_XINPUT)
		input_report_key(g->input, BTN_MODE, f->guide);
	input_sync(g->input);
}

static void gsn_neutral(struct gsn_device *g)
{
	unsigned long flags;

	spin_lock_irqsave(&g->report_lock, flags);
	gsn_neutral_locked(g);
	spin_unlock_irqrestore(&g->report_lock, flags);
}

static void gsn_neutral_locked(struct gsn_device *g)
{
	struct gs_frame zero = { .kind = GS_PAD_XINPUT };
	unsigned int key;

	gsn_gyro_report(g, zero.gyro, NULL, ktime_get_ns());
	gs_gyro_pause(&g->gyro_clock);
	g->have_deferred_pad = false;
	memset(g->deferred_extras, 0, sizeof(g->deferred_extras));
	g->last_guide = false;
	if (!g->input_registered)
		return;
	gsn_pad(g, &zero);
	if (gs_pid_native(g->rt.pid)) {
		input_report_key(g->input, KEY_RECORD, 0);
		for (key = BTN_TRIGGER_HAPPY1; key <= BTN_TRIGGER_HAPPY5; key++)
			input_report_key(g->input, key, 0);
		input_sync(g->input);
	}
}

/* Same accepted IMU packet as IIO; no extra USB consumer or buffer setup.
 * MSC_TIMESTAMP also preserves unchanged-rate samples in evdev. Its clock
 * is explicitly host-derived, with paused intervals excluded, NOT a claim
 * of a firmware timestamp. input_event timestamps retain actual host time.
 */
static void gsn_gyro_report(struct gsn_device *g, const gs_s16 raw[3],
			    const gs_s16 accel[3], u64 host_ns)
{
	gs_s32 values[3], acceleration[3];
	const bool report_accel = experimental_accel && accel;
	unsigned int i;

	if (!g->gyro_registered ||
	    gs_gyro_convert_observed(g->rt.pid, experimental_gyro, raw, values) !=
	    GS_SENSOR_EXPERIMENTAL)
		return;
	/* NULL means lifecycle neutralization: never invent a gravity sample. */
	if (report_accel &&
	    gs_accel_evdev_convert(&g->accel_scale, accel_axis_map, accel,
				   acceleration) != GS_SENSOR_EXPERIMENTAL)
		return;
	input_set_timestamp(g->gyro_input, ns_to_ktime(host_ns));
	if (report_accel)
		for (i = 0; i < 3; i++)
			input_report_abs(g->gyro_input, ABS_X + i, acceleration[i]);
	for (i = 0; i < 3; i++)
		input_report_abs(g->gyro_input, ABS_RX + i, values[i]);
	input_event(g->gyro_input, EV_MSC, MSC_TIMESTAMP,
		    gs_gyro_timestamp(&g->gyro_clock, host_ns));
	input_sync(g->gyro_input);
}

static void gsn_imu(struct gsn_device *g, const struct gs_frame *f)
{
	/* IIO scan order: six LE s16 values, zero padding, accepted-report count,
	 * then the standard IIO software timestamp. Never a device/RF sequence.
	 * Natural u64 alignment fixes count at byte 16 and timestamp at byte 24.
	 */
	struct {
		__le16 accel[3];
		__le16 gyro[3];
		u32 padding;

		__le64 count __aligned(8);
		s64 timestamp;
	} scan = {0};
	struct gsn_sample sample = { .abi_version = GSN_ABI_VERSION,
		.flags = GSN_FLAG_EXPERIMENTAL_ACCEL, .host_monotonic_ns = ktime_get_ns() };
	unsigned long flags;
	int i, ret;

	static_assert(sizeof(scan) == 32);
	static_assert(offsetof(typeof(scan), count) == 16);
	static_assert(offsetof(typeof(scan), timestamp) == 24);
	memcpy(sample.gyro_raw, f->gyro, sizeof(sample.gyro_raw));
	memcpy(sample.accel_raw, f->accel, sizeof(sample.accel_raw));
	ret = gs_accel_convert_experimental(&g->accel_scale, f->accel,
					    sample.accel_experimental_um_s2);
	if (ret == GS_SENSOR_EXPERIMENTAL)
		sample.flags |= GSN_FLAG_ACCEL_VALID;
	spin_lock_irqsave(&g->lock, flags);
	sample.sample_number = ++g->imu_packets;
	g->sample = sample;
	spin_unlock_irqrestore(&g->lock, flags);
	gsn_gyro_report(g, f->gyro, f->accel, sample.host_monotonic_ns);
	/* No buffer activation, allocation, owner claim, USB command or sleeping
	 * lock here. The single RX URB orders pushes; disconnect kills it before
	 * unregistering IIO. Queue overflow must not fault normal gamepad input:
	 * the next accepted-report count exposes missing queued observations.
	 */
	if (g->iio_buffer_active) {
		for (i = 0; i < 3; i++) {
			scan.accel[i] = cpu_to_le16(sample.accel_raw[i]);
			scan.gyro[i] = cpu_to_le16(sample.gyro_raw[i]);
		}
		scan.count = cpu_to_le64(sample.sample_number);
		ret = iio_push_to_buffers_with_ts(g->iio, &scan, sizeof(scan),
						  sample.host_monotonic_ns);
		if (ret < 0) {
			spin_lock_irqsave(&g->lock, flags);
			g->iio_push_errors++;
			spin_unlock_irqrestore(&g->lock, flags);
		}
	}
	gsn_extras(g, f->extras);
}

static void gsn_rx(struct urb *urb)
{
	struct gsn_device *g = urb->context;
	struct gs_frame frame;
	unsigned long flags, report_flags;
	bool accepts;
	int kind, ret;

	if (READ_ONCE(g->stopping))
		return;
	ret = gsn_boot_rx(g, urb);
	if (ret)
		return;
	if (urb->status) {
		gsn_fault(g, urb->status);
		return;
	}
	kind = gs_decode(g->rx_buf, urb->actual_length, &frame);
	spin_lock_irqsave(&g->lock, flags);
	accepts = gs_runtime_accepts(&g->rt, kind);
	if (!accepts)
		g->rejected_packets++;
	else if (kind == GS_PAD_XINPUT || kind == GS_PAD_GIP)
		g->input_packets++;
	spin_unlock_irqrestore(&g->lock, flags);
	if (accepts) {
		/* Single RX URB, but the watchdog may neutralize concurrently. Keep
		 * its liveness decision and these reports in one ordered stream.
		 */
		spin_lock_irqsave(&g->report_lock, report_flags);
		spin_lock_irqsave(&g->lock, flags);
		gs_runtime_note_input(&g->rt, kind, gsn_now_ms());
		spin_unlock_irqrestore(&g->lock, flags);
		if (kind == GS_PAD_XINPUT || kind == GS_PAD_GIP) {
			g->deferred_pad = frame;
			g->have_deferred_pad = true;
			if (kind == GS_PAD_XINPUT)
				g->last_guide = frame.guide;
			if (g->input_registered)
				gsn_pad(g, &frame);
		} else if (kind == GS_IMU) {
			gsn_imu(g, &frame);
		} else if (kind == GS_GUIDE) {
			g->last_guide = frame.guide;
			if (g->input_registered) {
				input_report_key(g->input, BTN_MODE, frame.guide);
				input_sync(g->input);
			}
			if (frame.ack) {
				spin_lock_irqsave(&g->lock, flags);
				if (!g->stopping && g->rt.session_active) {
					if (g->ack_pending)
						gs_runtime_halt(&g->rt, GS_FAULTED, -EOVERFLOW);
					g->ack_sequence = frame.sequence;
					g->ack_pending = true;
					mod_delayed_work(system_percpu_wq, &g->service, 0);
				}
				spin_unlock_irqrestore(&g->lock, flags);
			}
		}
		spin_unlock_irqrestore(&g->report_lock, report_flags);
	}
	spin_lock_irqsave(&g->lock, flags);
	accepts = !g->stopping && g->rt.state == GS_RUNNING;
	spin_unlock_irqrestore(&g->lock, flags);
	if (accepts) {
		ret = usb_submit_urb(urb, GFP_ATOMIC);
		if (ret && !gsn_boot_rx_teardown(g, ret, GSN_RX_SUBMIT))
			gsn_fault(g, ret);
	}
}

static int gsn_sample_snapshot(struct gsn_device *g, struct gsn_sample *out)
{
	unsigned long flags;
	int ret = 0;

	spin_lock_irqsave(&g->lock, flags);
	if (g->stopping || g->rt.state == GS_DISCONNECTED)
		ret = -ENODEV;
	else if (g->rt.state != GS_RUNNING)
		ret = -EIO;
	else if (!g->sample.sample_number)
		ret = -ENODATA;
	else if (ktime_get_ns() - g->sample.host_monotonic_ns > GSN_STALE_NS)
		ret = -ESTALE;
	else
		*out = g->sample;
	spin_unlock_irqrestore(&g->lock, flags);
	return ret;
}

static int gsn_iio_raw(struct iio_dev *indio, const struct iio_chan_spec *chan,
		       int *val, int *val2, long mask)
{
	struct gsn_device *g = iio_device_get_drvdata(indio);
	struct gsn_sample sample;
	int ret;

	if (mask != IIO_CHAN_INFO_RAW)
		return -EINVAL;
	ret = gsn_sample_snapshot(g, &sample);
	if (ret)
		return ret;
	*val = chan->type == IIO_ACCEL ? sample.accel_raw[chan->address] :
		sample.gyro_raw[chan->address];
	return IIO_VAL_INT;
}

static ssize_t accel_experimental_um_s2_show(struct device *dev,
					     struct device_attribute *attr, char *buf)
{
	struct gsn_device *g = iio_device_get_drvdata(dev_to_iio_dev(dev));
	struct gsn_sample sample;
	int ret = gsn_sample_snapshot(g, &sample);

	if (ret)
		return ret;
	if (!(sample.flags & GSN_FLAG_ACCEL_VALID))
		return -ERANGE;
	return sysfs_emit(buf, "%d %d %d\n", sample.accel_experimental_um_s2[0],
			  sample.accel_experimental_um_s2[1], sample.accel_experimental_um_s2[2]);
}

static ssize_t calibration_status_show(struct device *dev,
				       struct device_attribute *attr, char *buf)
{
	struct gsn_device *g = iio_device_get_drvdata(dev_to_iio_dev(dev));

	return sysfs_emit(buf, "experimental=%u/%u_LSB/g gyro_raw axes_unverified\n",
			  g->accel_scale.counts_per_g_num, g->accel_scale.counts_per_g_den);
}

static ssize_t buffer_push_errors_show(struct device *dev,
				       struct device_attribute *attr, char *buf)
{
	struct gsn_device *g = iio_device_get_drvdata(dev_to_iio_dev(dev));
	unsigned long flags;
	u64 count;

	spin_lock_irqsave(&g->lock, flags);
	count = g->iio_push_errors;
	spin_unlock_irqrestore(&g->lock, flags);
	return sysfs_emit(buf, "%llu\n", count);
}

static ssize_t buffer_stream_active_show(struct device *dev,
					 struct device_attribute *attr, char *buf)
{
	struct gsn_device *g = iio_device_get_drvdata(dev_to_iio_dev(dev));
	unsigned long flags;
	bool active;

	spin_lock_irqsave(&g->report_lock, flags);
	active = g->iio_buffer_active;
	spin_unlock_irqrestore(&g->report_lock, flags);
	return sysfs_emit(buf, "%u\n", active);
}

static IIO_DEVICE_ATTR_RO(accel_experimental_um_s2, 0);
static IIO_DEVICE_ATTR_RO(calibration_status, 0);
static IIO_DEVICE_ATTR_RO(buffer_push_errors, 0);
static IIO_DEVICE_ATTR_RO(buffer_stream_active, 0);
static struct attribute *gsn_iio_attrs[] = {
	&iio_dev_attr_accel_experimental_um_s2.dev_attr.attr,
	&iio_dev_attr_calibration_status.dev_attr.attr,
	&iio_dev_attr_buffer_push_errors.dev_attr.attr,
	&iio_dev_attr_buffer_stream_active.dev_attr.attr, NULL
};

static const struct attribute_group gsn_iio_group = { .attrs = gsn_iio_attrs };
static const struct iio_info gsn_iio_info = {
	.read_raw = gsn_iio_raw, .attrs = &gsn_iio_group,
};

#define GSN_CHANNEL(_type, _mod, _address, _index) { \
	.type = _type, .modified = 1, .channel2 = _mod, .address = _address, \
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW), .scan_index = _index, \
	.scan_type = { .sign = 's', .realbits = 16, .storagebits = 16, \
		.endianness = IIO_LE } }
static const struct iio_chan_spec gsn_channels[] = {
	GSN_CHANNEL(IIO_ACCEL, IIO_MOD_X, 0, 0), GSN_CHANNEL(IIO_ACCEL, IIO_MOD_Y, 1, 1),
	GSN_CHANNEL(IIO_ACCEL, IIO_MOD_Z, 2, 2), GSN_CHANNEL(IIO_ANGL_VEL, IIO_MOD_X, 0, 3),
	GSN_CHANNEL(IIO_ANGL_VEL, IIO_MOD_Y, 1, 4), GSN_CHANNEL(IIO_ANGL_VEL, IIO_MOD_Z, 2, 5),
	/* Host count of accepted IMU reports, scoped to this device instance.
	 * Buffer-only: preserve the existing direct raw-channel interface.
	 */
	{ .type = IIO_COUNT, .indexed = 1, .channel = 0, .scan_index = 6,
	  .scan_type = { .sign = 'u', .realbits = 64, .storagebits = 64,
			 .endianness = IIO_LE } },
	IIO_CHAN_SOFT_TIMESTAMP(7),
};

/* The producer always supplies all six channels plus the report count. IIO
 * may accept a userspace subset and demultiplex it from this complete scan.
 * Do not require the full mask in validate_scan_mask: that callback also runs
 * for each intermediate sysfs channel enable, before the buffer starts.
 * The standard software timestamp remains separately selectable.
 */
static const unsigned long gsn_scan_masks[] = { GENMASK(6, 0), 0 };

static int gsn_iio_preenable(struct iio_dev *indio)
{
	struct gsn_device *g = iio_device_get_drvdata(indio);
	struct gsn_sample sample;

	/* Check the core-selected producer layout, not the intermediate request. */
	if (!indio->active_scan_mask ||
	    indio->active_scan_mask[0] != gsn_scan_masks[0])
		return -EINVAL;

	/* The existing report snapshot and buffered timestamps share ktime_get_ns.
	 * Reject a different selected clock instead of mislabelling host time.
	 */
	if (iio_device_get_clock(indio) != CLOCK_MONOTONIC)
		return -EINVAL;
	return gsn_sample_snapshot(g, &sample);
}

static int gsn_iio_postenable(struct iio_dev *indio)
{
	struct gsn_device *g = iio_device_get_drvdata(indio);
	struct gsn_sample sample;
	unsigned long flags;
	int ret;

	spin_lock_irqsave(&g->report_lock, flags);
	ret = gsn_sample_snapshot(g, &sample);
	if (!ret)
		g->iio_buffer_active = true;
	spin_unlock_irqrestore(&g->report_lock, flags);
	return ret;
}

static int gsn_iio_predisable(struct iio_dev *indio)
{
	struct gsn_device *g = iio_device_get_drvdata(indio);
	unsigned long flags;

	/* Drain a concurrent push before IIO changes active masks/layout. This
	 * does not pause the shared RX URB, gamepad, motor state or runtime owner.
	 */
	spin_lock_irqsave(&g->report_lock, flags);
	g->iio_buffer_active = false;
	spin_unlock_irqrestore(&g->report_lock, flags);
	return 0;
}

static const struct iio_buffer_setup_ops gsn_iio_buffer_ops = {
	.preenable = gsn_iio_preenable,
	.postenable = gsn_iio_postenable,
	.predisable = gsn_iio_predisable,
};

static int gsn_open(struct inode *inode, struct file *file)
{
	struct gsn_device *g = container_of(file->private_data, struct gsn_device, misc);
	unsigned long flags;
	int ret = 0;

	mutex_lock(&g->io_lock);
	spin_lock_irqsave(&g->lock, flags);
	if (g->stopping && (!persistent_mode || g->rt.state == GS_DISCONNECTED)) {
		ret = -ENODEV;
	} else if (g->rt.owner) {
		ret = -EBUSY;
	} else {
		g->rt.owner = 1;
		kref_get(&g->ref);
		file->private_data = g;
	}
	spin_unlock_irqrestore(&g->lock, flags);
	mutex_unlock(&g->io_lock);
	return ret;
}

static int gsn_release(struct inode *inode, struct file *file)
{
	struct gsn_device *g = file->private_data;
	unsigned long flags;

	mutex_lock(&g->io_lock);
	if (!g->stopping && (!persistent_mode || !g->boot_handoff) &&
	    (!g->boot_handoff || g->boot_claimed))
		gsn_stop(g, true);
	spin_lock_irqsave(&g->lock, flags);
	g->rt.owner = 0;
	spin_unlock_irqrestore(&g->lock, flags);
	mutex_unlock(&g->io_lock);
	kref_put(&g->ref, gsn_delete);
	return 0;
}

static int gsn_start(struct gsn_device *g)
{
	u8 packet[64];
	unsigned long flags;
	int ret, len, i;

	if (bootstrap_mode && !g->boot_handoff)
		return -EAGAIN;
	spin_lock_irqsave(&g->lock, flags);
	if (g->boot_handoff) {
		/* Persistent clients may claim again; no init replay/deadline reset. */
		gs_runtime_tick(&g->rt, gsn_now_ms());
		ret = (persistent_mode || !g->boot_claimed) && g->rt.session_active ?
			0 : -EALREADY;
		if (!ret)
			g->boot_claimed = true;
		spin_unlock_irqrestore(&g->lock, flags);
		return ret;
	}
	ret = gs_runtime_start(&g->rt, gsn_now_ms(), session_ms);
	spin_unlock_irqrestore(&g->lock, flags);
	if (ret)
		return ret;
	g->output_used = true;
	g->stop_sent = false;
	/* Explicit START only. No initialization from probe, open, or hotplug. */
	for (i = 0; i < 3; i++) {
		len = gs_gip_init(packet, gsn_sequence(g), i);
		ret = gsn_send(g, packet, len, false);
		if (ret)
			goto fail;
		msleep(50);
	}
	for (i = 0; i < 3; i++) {
		gs_heartbeat(packet, gsn_sequence(g));
		ret = gsn_send(g, packet, 64, false);
		if (ret)
			goto fail;
		msleep(50);
	}
	g->next_heartbeat = jiffies + msecs_to_jiffies(450);
	spin_lock_irqsave(&g->lock, flags);
	if (!g->stopping && g->rt.state == GS_RUNNING)
		mod_delayed_work(system_percpu_wq, &g->service, msecs_to_jiffies(10));
	spin_unlock_irqrestore(&g->lock, flags);
	return 0;
fail:
	gsn_stop(g, true);
	return ret;
}

/* Native startup adapter. USB objects are pinned; no address/serial matching. */
static struct usb_device *gsn_root(struct usb_device *udev)
{
	while (udev->parent)
		udev = udev->parent;
	return udev;
}

static bool gsn_boot_route(struct gsn_boot *b, struct usb_device *udev)
{
	return udev->parent == b->parent && gsn_root(udev) == b->root &&
		udev->portnum == b->portnum && udev != b->origin &&
		READ_ONCE(b->parent->state) != USB_STATE_NOTATTACHED &&
		READ_ONCE(b->root->state) != USB_STATE_NOTATTACHED;
}

/* Same-instance direct start is never permission to adopt a re-enumerated node.
 * Pinned origin/parent/root plus the core tokens attest a native start lifetime.
 */
static bool gsn_boot_owned_route(struct gsn_boot *b, struct gsn_device *g)
{
	if (le16_to_cpu(b->origin->descriptor.idProduct) == 0x100a)
		return gsn_boot_route(b, g->udev);
	return g->udev == b->origin && g->udev->parent == b->parent &&
		gsn_root(g->udev) == b->root && g->udev->portnum == b->portnum &&
		READ_ONCE(b->parent->state) != USB_STATE_NOTATTACHED &&
		READ_ONCE(b->root->state) != USB_STATE_NOTATTACHED;
}

/* Cached descriptors only. Called with probe's USB lock or a quiesce barrier. */
static int gsn_describe(struct usb_interface *intf, struct gs_boot_device *d)
{
	struct usb_device *udev = interface_to_usbdev(intf);
	struct usb_host_interface *alt = intf->cur_altsetting;
	unsigned int i;

	if (!alt || !udev->actconfig || alt->desc.bNumEndpoints != 2)
		return -ENODEV;
	d->vid = le16_to_cpu(udev->descriptor.idVendor);
	d->pid = le16_to_cpu(udev->descriptor.idProduct);
	d->configuration = udev->actconfig->desc.bConfigurationValue;
	d->interface_number = alt->desc.bInterfaceNumber;
	d->altsetting = alt->desc.bAlternateSetting;
	d->interface_class = alt->desc.bInterfaceClass;
	d->subclass = alt->desc.bInterfaceSubClass;
	d->protocol = alt->desc.bInterfaceProtocol;
	d->in_ep = 0;
	d->out_ep = 0;
	for (i = 0; i < alt->desc.bNumEndpoints; i++) {
		struct usb_endpoint_descriptor *ep = &alt->endpoint[i].desc;

		if (usb_endpoint_is_int_in(ep)) {
			d->in_ep = ep->bEndpointAddress;
			d->in_type = usb_endpoint_type(ep);
			d->in_size = usb_endpoint_maxp(ep);
			d->in_interval = ep->bInterval;
		} else if (usb_endpoint_is_int_out(ep)) {
			d->out_ep = ep->bEndpointAddress;
			d->out_type = usb_endpoint_type(ep);
			d->out_size = usb_endpoint_maxp(ep);
			d->out_interval = ep->bInterval;
		}
	}
	d->exclusive = intf->dev.driver == &gsn_driver.driver && intf->authorized &&
		(intf->condition == USB_INTERFACE_BOUND ||
		 intf->condition == USB_INTERFACE_BINDING) &&
		READ_ONCE(udev->state) == USB_STATE_CONFIGURED;
	return gs_boot_supported(d) ? 0 : -ENODEV;
}

/* Private version-1 text ABI: version interface bus address device-ino parent-ino. */
static int gsn_claim_parse(struct gsn_claim *claim, const char *buf, size_t count)
{
	char text[192], *cursor = text, *fields[6], *p;
	u64 values[6] = {0};
	unsigned int i;

	if (!count || count >= sizeof(text) || memchr(buf, '\0', count))
		return -EINVAL;
	memcpy(text, buf, count);
	text[count] = '\0';
	if (text[count - 1] == '\n')
		text[count - 1] = '\0';
	for (i = 0; i < ARRAY_SIZE(fields); i++) {
		fields[i] = strsep(&cursor, " ");
		if (!fields[i] || !*fields[i])
			return -EINVAL;
		if (i == 1)
			continue;
		for (p = fields[i]; *p; p++)
			if (*p < '0' || *p > '9')
				return -EINVAL;
		if (kstrtou64(fields[i], 10, &values[i]) || !values[i])
			return -EINVAL;
	}
	if (cursor || values[0] != 1 || values[2] > 65535 || values[3] > 127 ||
	    strlen(fields[1]) >= sizeof(claim->interface))
		return -EINVAL;
	memcpy(claim->interface, fields[1], strlen(fields[1]) + 1);
	claim->bus = values[2];
	claim->address = values[3];
	claim->device_inode = values[4];
	claim->parent_inode = values[5];
	return 0;
}

/* USB device lock held, including by the driver core at the final probe gate. */
static bool gsn_claim_identity(struct gsn_claim *claim, struct usb_device *udev)
{
	return udev->parent && udev->bus && udev->bus->busnum == claim->bus &&
		udev->devnum == claim->address && udev->state == USB_STATE_CONFIGURED &&
		le16_to_cpu(udev->descriptor.idVendor) == 0x3537 &&
		le16_to_cpu(udev->descriptor.idProduct) == claim->pid &&
		device_is_registered(&udev->dev) && device_is_registered(&udev->parent->dev) &&
		udev->dev.kobj.sd && udev->parent->dev.kobj.sd &&
		kernfs_ino(udev->dev.kobj.sd) == claim->device_inode &&
		kernfs_ino(udev->parent->dev.kobj.sd) == claim->parent_inode;
}

static int gsn_claim_find(struct usb_device *udev, void *data)
{
	struct gsn_claim *claim = data;
	struct usb_interface *intf;
	/* Nonzero placeholders only for cached descriptor-shape validation. */
	struct gs_boot_device descriptor = { .port = 1, .instance = 1 };

	usb_lock_device(udev);
	if (gsn_claim_identity(claim, udev)) {
		intf = usb_ifnum_to_if(udev, 0);
		if (intf && device_is_registered(&intf->dev) &&
		    (!intf->dev.driver || (claim->allow_xpad &&
		     !strcmp(intf->dev.driver->name, "xpad"))) &&
		    intf->authorized && !strcmp(dev_name(&intf->dev), claim->interface) &&
		    !gsn_describe(intf, &descriptor)) {
			claim->intf = usb_get_intf(intf);
			/* Exact USB object pinned and its lock held: no sysfs-name unbind.
			 * A free interface is claimed directly; xpad is optional, never
			 * loaded or bound as an initialization prerequisite.
			 */
			if (intf->dev.driver)
				device_release_driver(&intf->dev);
		}
	}
	usb_unlock_device(udev);
	return claim->intf ? 1 : 0;
}

static bool gsn_claim_consume(struct usb_interface *intf)
{
	struct gsn_claim *claim;
	unsigned long flags;
	bool allowed = false;

	spin_lock_irqsave(&claim_gate_lock, flags);
	claim = pending_claim;
	if (claim && claim->task == current && claim->intf == intf && !claim->consumed) {
		claim->consumed = true;
		allowed = true;
	}
	spin_unlock_irqrestore(&claim_gate_lock, flags);
	/* Only this synchronous caller can use the stack-backed claim after unlock. */
	return allowed && gsn_claim_identity(claim, interface_to_usbdev(intf)) &&
		!strcmp(dev_name(&intf->dev), claim->interface);
}

static ssize_t gsn_claim_store(const char *buf, size_t count, unsigned int pid,
			       bool allow_xpad)
{
	struct gsn_claim claim = { .pid = pid, .allow_xpad = allow_xpad };
	unsigned long flags;
	int ret;

	if (!capable(CAP_SYS_ADMIN) || !persistent_mode || !bootstrap_mode || !enable_output)
		return -EPERM;
	ret = gsn_claim_parse(&claim, buf, count);
	if (ret)
		return ret;
	if (mutex_lock_interruptible(&claim_lock))
		return -ERESTARTSYS;
	usb_for_each_dev(&claim, gsn_claim_find);
	if (!claim.intf) {
		ret = -ENODEV;
		goto unlock;
	}
	claim.task = current;
	spin_lock_irqsave(&claim_gate_lock, flags);
	pending_claim = &claim;
	spin_unlock_irqrestore(&claim_gate_lock, flags);
	/* Pins the selected interface; core locks it and its USB parent before probe. */
	ret = device_driver_attach(&gsn_driver.driver, &claim.intf->dev);
	spin_lock_irqsave(&claim_gate_lock, flags);
	pending_claim = NULL;
	spin_unlock_irqrestore(&claim_gate_lock, flags);
	if (!ret && !claim.consumed)
		ret = -ENODEV;
	usb_put_intf(claim.intf);
unlock:
	mutex_unlock(&claim_lock);
	return ret ? ret : count;
}

static ssize_t claim_100a_store(struct device_driver *driver, const char *buf, size_t count)
{
	return gsn_claim_store(buf, count, 0x100a, false);
}
static DRIVER_ATTR_WO(claim_100a);

static ssize_t claim_105e_store(struct device_driver *driver, const char *buf, size_t count)
{
	return gsn_claim_store(buf, count, 0x105e, false);
}
static DRIVER_ATTR_WO(claim_105e);

/* Separate attributes keep the historical unbound-only claim contract intact. */
static ssize_t acquire_100a_store(struct device_driver *driver, const char *buf, size_t count)
{
	return gsn_claim_store(buf, count, 0x100a, true);
}
static DRIVER_ATTR_WO(acquire_100a);

static ssize_t acquire_105e_store(struct device_driver *driver, const char *buf, size_t count)
{
	return gsn_claim_store(buf, count, 0x105e, true);
}
static DRIVER_ATTR_WO(acquire_105e);

static ssize_t acquire_109c_store(struct device_driver *driver, const char *buf, size_t count)
{
	return gsn_claim_store(buf, count, 0x109c, true);
}
static DRIVER_ATTR_WO(acquire_109c);

static struct attribute *gsn_driver_attrs[] = {
	&driver_attr_claim_100a.attr,
	&driver_attr_claim_105e.attr,
	&driver_attr_acquire_100a.attr,
	&driver_attr_acquire_105e.attr,
	&driver_attr_acquire_109c.attr,
	NULL
};
ATTRIBUTE_GROUPS(gsn_driver);

static void gsn_boot_cancel_device(struct gsn_device *g)
{
	unsigned long flags;

	if (!g->boot || g->boot_handoff)
		return;
	spin_lock_irqsave(&g->boot->lock, flags);
	gs_boot_cancel(&g->boot->core);
	spin_unlock_irqrestore(&g->boot->lock, flags);
}

/* Called only after service and RX are drained, before dropping binding ref. */
static void gsn_boot_detach(struct gsn_device *g)
{
	/* Acquire the initialized core/identity published by probe or BOOTSTRAP. */
	struct gsn_boot *b = smp_load_acquire(&g->boot);
	unsigned long flags;

	if (!b)
		return;
	mutex_lock(&boot_list_lock);
	spin_lock_irqsave(&b->lock, flags);
	if (b->core.state != GS_BOOT_HANDED_OFF) {
		if (READ_ONCE(g->udev->state) == USB_STATE_NOTATTACHED)
			gs_boot_removed(&b->core, g->identity.port, g->identity.instance,
					gsn_now_us());
		else
			gs_boot_cancel(&b->core); /* Manual unbind is not re-enumeration. */
	}
	if (b->attached == g)
		b->attached = NULL;
	spin_unlock_irqrestore(&b->lock, flags);
	mutex_unlock(&boot_list_lock);
}

static bool gsn_boot_pending(struct usb_device *udev)
{
	struct gsn_boot *b;
	unsigned long flags;
	bool match = false;

	mutex_lock(&boot_list_lock);
	list_for_each_entry(b, &boot_list, node) {
		if (!gsn_boot_route(b, udev))
			continue;
		spin_lock_irqsave(&b->lock, flags);
		match = b->core.state == GS_BOOT_WAIT_ADD && !b->attached;
		spin_unlock_irqrestore(&b->lock, flags);
		break;
	}
	mutex_unlock(&boot_list_lock);
	return match;
}

/* Called before allocation/RX. Direct 109c needs the same one-shot, exact
 * acquisition gate as start-mode devices. A correlated transition retains
 * its existing pending-bootstrap path, without granting a second startup.
 */
static int gsn_probe_authorize(struct usb_interface *intf, unsigned int pid,
			       bool *direct_native)
{
	*direct_native = false;
	if (persistent_mode && (pid == 0x100a || pid == 0x105e) && !gsn_claim_consume(intf))
		return -ENODEV;
	if (bootstrap_mode && pid == 0x109c) {
		*direct_native = persistent_mode && gsn_claim_consume(intf);
		if (!*direct_native && !gsn_boot_pending(interface_to_usbdev(intf)))
			return -ENODEV;
	}
	return 0;
}

/* Match one outstanding, explicitly requested transition. Caller owns USB lock. */
static int gsn_boot_connect(struct gsn_device *g)
{
	struct gsn_boot *b;
	unsigned long flags;
	int ret = -ENODEV;

	mutex_lock(&boot_list_lock);
	list_for_each_entry(b, &boot_list, node) {
		if (!gsn_boot_route(b, g->udev))
			continue;
		spin_lock_irqsave(&b->lock, flags);
		g->identity.port = b->core.device.port;
		if (b->attached) {
			ret = -EBUSY;
		} else {
			ret = gs_boot_arrived(&b->core, &g->identity, gsn_now_us());
			if (!ret && b->core.state != GS_BOOT_INITIALIZE)
				ret = -ENODEV;
			if (!ret) {
				kref_get(&b->ref);
				/* Publish identity and core before RX can observe this session. */
				smp_store_release(&g->boot, b);
				b->attached = g;
			}
		}
		spin_unlock_irqrestore(&b->lock, flags);
		break;
	}
	mutex_unlock(&boot_list_lock);
	return ret;
}

/* b->lock held; the old instance, never a newly enumerated native device. */
static bool gsn_boot_old_rx(struct gsn_device *g, struct gsn_boot *b)
{
	return b->origin == g->udev && g->identity.pid == 0x100a &&
		b->core.old_instance == g->identity.instance &&
		b->core.device.instance == g->identity.instance &&
		b->core.device.port == g->identity.port;
}

static bool gsn_boot_rx_teardown(struct gsn_device *g, int status, unsigned int source)
{
	/* Acquire the initialized core/identity published by probe or BOOTSTRAP. */
	struct gsn_boot *b = smp_load_acquire(&g->boot);
	unsigned long flags;
	bool expected = false, old, waiting, local_stop, terminal;

	if (!b || READ_ONCE(g->boot_handoff))
		return false;
	spin_lock_irqsave(&b->lock, flags);
	old = gsn_boot_old_rx(g, b);
	waiting = old && b->core.state == GS_BOOT_WAIT_REMOVE &&
		b->core.transition_completed && b->core.step == 9 && !b->core.pending_length;
	terminal = status == -ENOENT || status == -ECONNRESET ||
		status == -ESHUTDOWN || status == -ENODEV;
	/* A logically retired RX must never requeue, even on a successful callback.
	 * A submit already racing that retirement may return local -EPERM.
	 */
	if (old && b->old_rx_quiesced)
		expected = true;
	else if (status < 0 && old)
		expected = (waiting && (terminal || status == -EPIPE || status == -EPROTO)) ||
			   (terminal && b->core.state == GS_BOOT_TRANSITION &&
			    b->core.step == 8 && b->core.pending_length == 8);
	local_stop = old && b->old_rx_quiesced &&
		(status == -ENOENT || status == -ECONNRESET || status == -EPERM);
	/* Record at the producer before a later worker/cleanup changes the phase.
	 * Our own cancel and post-retirement submit rejection are not transport faults.
	 */
	if (status < 0 && !local_stop && !b->first_rx_status &&
	    b->core.state != GS_BOOT_FAILED && b->core.state != GS_BOOT_HANDED_OFF) {
		b->first_rx_status = status;
		b->first_rx_source = source;
		b->first_rx_stage = b->core.state;
		b->first_rx_step = b->core.step;
		b->first_rx_pid = g->identity.pid;
		b->first_rx_us = gsn_now_us();
		b->first_rx_deferred = expected;
	}
	spin_unlock_irqrestore(&b->lock, flags);
	/* RX can finish before the last synchronous OUT returns. Stop RX only:
	 * that OUT must still complete fully and the real disconnect callback must
	 * confirm removal. A short/failed OUT or earlier disconnect remains fatal.
	 */
	return expected;
}

/* io_lock held. Stop the old RX exactly once after the final full OUT. This
 * does not confirm USB removal or permit any new device to be acquired.
 */
static void gsn_boot_retire_rx(struct gsn_device *g)
{
	/* Acquire the identity/core published before RX or service can use them. */
	struct gsn_boot *b = smp_load_acquire(&g->boot);
	unsigned long flags;
	bool retire = false;

	spin_lock_irqsave(&g->lock, flags);
	spin_lock(&b->lock);
	if (!g->stopping && g->rt.state == GS_RUNNING && gsn_boot_old_rx(g, b) &&
	    b->core.state == GS_BOOT_WAIT_REMOVE && b->core.transition_completed &&
	    b->core.step == 9 && !b->core.pending_length && !b->old_rx_quiesced) {
		b->old_rx_quiesced = true;
		retire = true;
	}
	spin_unlock(&b->lock);
	spin_unlock_irqrestore(&g->lock, flags);
	if (retire)
		usb_kill_urb(g->rx_urb);
}

static int gsn_boot_rx(struct gsn_device *g, struct urb *urb)
{
	/* Acquire the initialized core/identity published by probe or BOOTSTRAP. */
	struct gsn_boot *b = smp_load_acquire(&g->boot);
	unsigned long flags;
	int ret = 0;

	if (!b || READ_ONCE(g->boot_handoff))
		return 0;
	if (gsn_boot_rx_teardown(g, urb->status, GSN_RX_COMPLETION))
		return 1;
	spin_lock_irqsave(&b->lock, flags);
	if (gs_pid_native(g->identity.pid) && b->core.state != GS_BOOT_HANDED_OFF)
		ret = gs_boot_input(&b->core, &g->identity, 0x82, urb->status,
				    g->rx_buf, urb->actual_length, gsn_now_us());
	spin_unlock_irqrestore(&b->lock, flags);
	if (ret < 0) {
		gsn_fault(g, ret);
		return 1;
	}
	return 0;
}

/* io_lock held. Atomic sequence ownership transfer; never repeat gsn_start. */
static int gsn_boot_adopt(struct gsn_device *g)
{
	struct gs_runtime runtime;
	struct gs_boot_handoff h;
	unsigned long flags;
	u64 now, remaining;
	int ret;

	spin_lock_irqsave(&g->lock, flags);
	spin_lock(&g->boot->lock);
	runtime = g->rt;
	runtime.owner = 1; /* The explicit bootstrap authorizes this runtime. */
	if (runtime.state != GS_RUNNING)
		ret = runtime.error < 0 ? runtime.error : -ENODEV;
	else
		ret = persistent_mode ? gs_runtime_start_persistent(&runtime, gsn_now_ms()) :
			gs_runtime_start(&runtime, gsn_now_ms(), session_ms);
	if (!ret)
		ret = gs_boot_takeover(&g->boot->core, &g->identity, gsn_now_us(), &h);
	if (!ret) {
		runtime.owner = g->rt.owner;
		g->rt = runtime;
		g->sequence = h.sequence;
		now = gsn_now_us();
		remaining = h.next_heartbeat_us > now ? h.next_heartbeat_us - now : 0;
		g->next_heartbeat = jiffies + usecs_to_jiffies(remaining);
		g->output_used = true;
		g->stop_sent = false;
		g->boot_handoff = true;
	} else {
		gs_boot_abort(&g->boot->core, ret);
	}
	spin_unlock(&g->boot->lock);
	spin_unlock_irqrestore(&g->lock, flags);
	return ret;
}

/* io_lock held; gs_boot_next has validated/reserved the first 100a OUT.
 * Captured xpad setup c1/01/0100/0000/20, before any mode-switch packet.
 * Use the allocated transfer buffer, never a stack buffer for USB DMA.
 */
static int gsn_boot_xinput_query(struct gsn_device *g)
{
	struct gsn_boot *b = g->boot;
	struct gs_boot_device identity = g->identity;
	struct gs_boot_tx pending;
	unsigned long flags;
	int ret, actual;

	spin_lock_irqsave(&b->lock, flags);
	ret = gs_boot_poll(&b->core, gsn_now_us());
	if (ret || b->xinput_query_attempted)
		goto unlock;
	if (g->identity.pid != 0x100a || b->origin != g->udev ||
	    b->core.state != GS_BOOT_TRANSITION || b->core.step ||
	    b->core.pending_length != 8 ||
	    b->core.device.instance != g->identity.instance ||
	    b->core.device.port != g->identity.port) {
		gs_boot_abort(&b->core, -ENODEV);
		ret = b->core.error;
		goto unlock;
	}
	b->xinput_query_attempted = true;
	spin_unlock_irqrestore(&b->lock, flags);
	actual = usb_control_msg(g->udev, usb_rcvctrlpipe(g->udev, 0), 0x01,
				 USB_DIR_IN | USB_TYPE_VENDOR | USB_RECIP_INTERFACE,
				 0x0100, 0, g->tx_buf, 20, 25);
	ret = actual == 20 ? gsn_describe(g->intf, &identity) :
		(actual < 0 ? actual : -EREMOTEIO);
	spin_lock_irqsave(&b->lock, flags);
	b->xinput_query_result = actual;
	/* Unlike xpad's warning-only policy, do not switch modes after an
	 * incomplete/failed query. Preserve an earlier concurrent RX failure.
	 */
	if (ret)
		gs_boot_abort(&b->core, ret);
	/* The pending first OUT prevents a second intent. Recheck full identity,
	 * ownership and deadlines after the sleeping control transfer.
	 */
	ret = gs_boot_next(&b->core, &identity, gsn_now_us(), &pending);
unlock:
	spin_unlock_irqrestore(&b->lock, flags);
	return ret;
}

/* io_lock held. The shared core is the source of bootstrap interrupt OUT. */
static bool gsn_boot_service(struct gsn_device *g)
{
	/* Acquire the initialized core/identity published by probe or BOOTSTRAP. */
	struct gsn_boot *b = smp_load_acquire(&g->boot);
	struct gs_boot_tx tx;
	struct gs_boot_device identity = g->identity;
	unsigned long flags;
	int ret = 0, actual = 0, state = 0;
	bool waiting;

	if (!b || g->boot_handoff)
		return false;
	/* Probe publishes the session before usbcore commits the binding. */
	if (READ_ONCE(g->intf->condition) == USB_INTERFACE_BINDING)
		goto requeue;
	spin_lock_irqsave(&g->lock, flags);
	if (g->rt.state != GS_RUNNING)
		ret = g->rt.error < 0 ? g->rt.error : -ENODEV;
	spin_unlock_irqrestore(&g->lock, flags);
	spin_lock_irqsave(&b->lock, flags);
	if (ret)
		gs_boot_abort(&b->core, ret);
	waiting = b->core.state == GS_BOOT_WAIT_REMOVE &&
		b->core.transition_completed && b->core.step == 9 &&
		!b->core.pending_length && b->origin == g->udev &&
		g->identity.pid == 0x100a && b->core.old_instance == g->identity.instance &&
		b->core.device.instance == g->identity.instance &&
		b->core.device.port == g->identity.port;
	if (waiting)
		ret = gs_boot_poll(&b->core, gsn_now_us());
	spin_unlock_irqrestore(&b->lock, flags);
	/* All nine OUTs are proven complete. USB core may already have marked
	 * this old device NOTATTACHED while its disconnect callback is pending.
	 * No more OUTs or descriptor/ownership checks on the dying instance:
	 * supervise the original deadline, never infer removal or accept a new PID.
	 */
	if (waiting)
		goto completed;
	ret = gsn_describe(g->intf, &identity);
	spin_lock_irqsave(&b->lock, flags);
	if (ret)
		gs_boot_abort(&b->core, ret);
	ret = gs_boot_next(&b->core, &identity, gsn_now_us(), &tx);
	spin_unlock_irqrestore(&b->lock, flags);
	if (ret == 1) {
		if (identity.pid == 0x100a) {
			ret = gsn_boot_xinput_query(g);
			if (ret)
				goto completed;
		}
		memcpy(g->tx_buf, tx.data, tx.length);
		ret = usb_interrupt_msg(g->udev, usb_sndintpipe(g->udev, tx.endpoint),
					g->tx_buf, tx.length, &actual, GSN_USB_TIMEOUT_MS);
		spin_lock_irqsave(&b->lock, flags);
		b->tx_count++;
		b->tx_step = b->core.step;
		b->tx_expected = tx.length;
		b->tx_status = ret;
		b->tx_actual = actual;
		ret = gs_boot_complete(&b->core, &identity, tx.token, ret, actual,
				       gsn_now_us());
		spin_unlock_irqrestore(&b->lock, flags);
	}
completed:
	if (!ret)
		gsn_boot_retire_rx(g);
	spin_lock_irqsave(&b->lock, flags);
	state = b->core.state;
	spin_unlock_irqrestore(&b->lock, flags);
	if (!ret && state == GS_BOOT_READY)
		ret = gsn_boot_adopt(g);
	if (ret < 0) {
		gsn_fault(g, ret);
		/* Persistent standby may outlive the synchronous supervisor. Make
		 * its failed instance locally END-able without waiting for that client
		 * to quiesce it. Never drain this work item from within itself.
		 */
		if (receiver_wait) {
			spin_lock_irqsave(&g->lock, flags);
			g->stopping = true;
			g->publication_cancelled = true;
			spin_unlock_irqrestore(&g->lock, flags);
		}
		usb_kill_urb(g->rx_urb);
		gsn_neutral(g);
		return true;
	}
requeue:
	spin_lock_irqsave(&g->lock, flags);
	if (!g->stopping)
		mod_delayed_work(system_percpu_wq, &g->service,
				 msecs_to_jiffies(state == GS_BOOT_WAIT_RECEIVER ? 250 : 10));
	spin_unlock_irqrestore(&g->lock, flags);
	return true;
}

struct gsn_boot_search {
	struct gsn_boot *boot;
	struct usb_device *found;
};

static int gsn_boot_find(struct usb_device *udev, void *data)
{
	struct gsn_boot_search *search = data;

	if (gsn_boot_route(search->boot, udev)) {
		search->found = usb_get_dev(udev);
		return 1;
	}
	return 0;
}

/* One attempt, from the synchronous supervisor, never from probe/RX.
 * USB parent lock serializes driver changes; drop it before driver_attach,
 * which takes it internally. A competing owner after release is an error.
 */
static int gsn_boot_handover(struct gsn_boot *b)
{
	struct gsn_boot_search search = { .boot = b };
	struct usb_interface *intf = NULL;
	struct gs_boot_device d = {0};
	struct usb_device *udev;
	unsigned long flags;
	bool attach = false;
	int ret = 0;

	usb_for_each_dev(&search, gsn_boot_find);
	udev = search.found;
	if (!udev)
		return 0;
	usb_lock_device(udev);
	if (READ_ONCE(udev->state) != USB_STATE_CONFIGURED || !udev->actconfig)
		goto unlock;
	intf = usb_ifnum_to_if(udev, 0);
	if (!intf || !intf->authorized || !device_is_registered(&intf->dev))
		goto unlock;
	usb_get_intf(intf);
	spin_lock_irqsave(&b->lock, flags);
	d.port = b->core.device.port;
	d.instance = 1; /* Descriptor validation only; probe allocates the real token. */
	d.enumerated_us = gsn_now_us();
	if (b->core.state != GS_BOOT_WAIT_ADD || b->handover_attempted) {
		spin_unlock_irqrestore(&b->lock, flags);
		goto put_intf;
	}
	spin_unlock_irqrestore(&b->lock, flags);
	if (!gsn_boot_route(b, udev) || gsn_describe(intf, &d) || d.pid != 0x109c) {
		ret = -ENODEV;
		goto put_intf;
	}
	if (intf->dev.driver == &gsn_driver.driver)
		goto put_intf;
	if (intf->dev.driver &&
	    (!(b->flags & GSN_BOOT_ALLOW_XPAD_HANDOVER) ||
	     strcmp(intf->dev.driver->name, "xpad"))) {
		ret = -EBUSY;
		goto put_intf;
	}
	spin_lock_irqsave(&b->lock, flags);
	ret = gs_boot_poll(&b->core, gsn_now_us());
	if (!ret)
		b->handover_attempted = true;
	spin_unlock_irqrestore(&b->lock, flags);
	if (ret)
		goto put_intf;
	if (intf->dev.driver)
		device_release_driver(&intf->dev); /* Only the checked new IF0/xpad. */
	attach = true;
put_intf:
	usb_unlock_device(udev);
	if (attach) {
		struct gsn_device *bound;

		ret = device_driver_attach(&gsn_driver.driver, &intf->dev);
		usb_lock_device(udev);
		bound = usb_get_intfdata(intf);
		if (intf->dev.driver == &gsn_driver.driver && bound && bound->boot == b)
			ret = 0; /* Our probe may have won the attach race. */
		else if (!ret)
			ret = -EBUSY;
		usb_unlock_device(udev);
	}
	usb_put_intf(intf);
	usb_put_dev(udev);
	return ret;
unlock:
	usb_unlock_device(udev);
	usb_put_dev(udev);
	return 0;
}

/* Old control FD pins this module and its old g across disconnect. The pending
 * list exists only for the duration of this ioctl; no autonomous retry/worker.
 */
static int gsn_bootstrap(struct gsn_device *g, const struct gsn_boot_request *request)
{
	struct gsn_boot *b, *other;
	struct gsn_device *last;
	unsigned long flags;
	int ret, state;
	int failed_stage, tx_status, tx_actual;
	unsigned int step, pending, transitioned, tx_count, tx_step, tx_expected;
	int first_rx_status, first_rx_stage;
	unsigned int first_rx_source, first_rx_step, first_rx_pid;
	u64 first_rx_us;
	bool first_rx_deferred, old_rx_quiesced;
	bool xinput_query_attempted;
	int xinput_query_result;

	if (!capable(CAP_SYS_ADMIN) || !bootstrap_mode || !enable_output)
		return -EPERM;
	if (request->abi_version != GSN_ABI_VERSION || request->reserved[0] ||
	    request->reserved[1] || (request->flags & ~GSN_BOOT_ALLOW_XPAD_HANDOVER) ||
	    (gs_pid_native(g->identity.pid) && request->flags))
		return -EINVAL;
	mutex_lock(&g->io_lock);
	if (g->stopping || (g->identity.pid != 0x100a && g->identity.pid != 0x105e &&
			    !(g->identity.pid == 0x109c && g->direct_native)) ||
	    !g->rt.owner || g->boot) {
		ret = -EBUSY;
		goto unlock;
	}
	ret = gsn_describe(g->intf, &g->identity);
	if (ret)
		goto unlock;
	b = kzalloc_obj(*b, GFP_KERNEL);
	if (!b) {
		ret = -ENOMEM;
		goto unlock;
	}
	kref_init(&b->ref);
	spin_lock_init(&b->lock);
	INIT_LIST_HEAD(&b->node);
	b->origin = usb_get_dev(g->udev);
	b->parent = usb_get_dev(g->udev->parent);
	b->root = usb_get_dev(gsn_root(g->udev));
	b->portnum = g->udev->portnum;
	b->flags = request->flags;
	ret = receiver_wait ? gs_boot_begin_receiver(&b->core, &g->identity, 1, gsn_now_us()) :
		gs_boot_begin(&b->core, &g->identity, 1, gsn_now_us());
	mutex_lock(&boot_list_lock);
	list_for_each_entry(other, &boot_list, node)
		if (other->parent == b->parent && other->portnum == b->portnum)
			ret = -EBUSY;
	if (ret) {
		mutex_unlock(&boot_list_lock);
		kref_put(&b->ref, gsn_boot_delete);
		goto unlock;
	}
	smp_store_release(&g->boot, b); /* initial ref belongs to g; supervisor takes another */
	kref_get(&b->ref);
	b->attached = g;
	list_add_tail(&b->node, &boot_list);
	mutex_unlock(&boot_list_lock);
	spin_lock_irqsave(&g->lock, flags);
	mod_delayed_work(system_percpu_wq, &g->service, 0);
	spin_unlock_irqrestore(&g->lock, flags);
	mutex_unlock(&g->io_lock);
	for (;;) {
		spin_lock_irqsave(&b->lock, flags);
		state = b->core.state;
		ret = state == GS_BOOT_HANDED_OFF ? 0 : gs_boot_poll(&b->core, gsn_now_us());
		spin_unlock_irqrestore(&b->lock, flags);
		if (ret || state == GS_BOOT_HANDED_OFF)
			break;
		if (signal_pending(current)) {
			ret = -EINTR;
			break;
		}
		if (state == GS_BOOT_WAIT_RECEIVER)
			break;
		if (state == GS_BOOT_WAIT_ADD) {
			ret = gsn_boot_handover(b);
			if (ret)
				break;
		}
		msleep_interruptible(10);
	}
	spin_lock_irqsave(&b->lock, flags);
	if (ret)
		gs_boot_abort(&b->core, ret);
	/* A producer may have failed after the last poll but before a signal or
	 * handover error reached this supervisor. Return the latched first cause.
	 */
	if (b->core.state == GS_BOOT_FAILED)
		ret = b->core.error;
	spin_unlock_irqrestore(&b->lock, flags);
	mutex_lock(&boot_list_lock);
	list_del_init(&b->node);
	last = b->attached;
	if (last)
		kref_get(&last->ref); /* Before disconnect can drop the binding ref. */
	b->attached = NULL;
	mutex_unlock(&boot_list_lock);
	if (last) {
		if (ret) {
			/* Serialize against disconnect's input/IIO deregistration. */
			usb_lock_device(last->udev);
			if (last->intf->dev.driver == &gsn_driver.driver &&
			    usb_get_intfdata(last->intf) == last)
				gsn_quiesce(last, GS_FAULTED, ret);
			usb_unlock_device(last->udev);
		}
		kref_put(&last->ref, gsn_delete);
	}
	spin_lock_irqsave(&b->lock, flags);
	failed_stage = b->core.failed_stage;
	step = b->core.step;
	pending = b->core.pending_length;
	transitioned = b->core.transition_completed;
	tx_count = b->tx_count;
	tx_step = b->tx_step;
	tx_expected = b->tx_expected;
	tx_status = b->tx_status;
	tx_actual = b->tx_actual;
	first_rx_status = b->first_rx_status;
	first_rx_source = b->first_rx_source;
	first_rx_stage = b->first_rx_stage;
	first_rx_step = b->first_rx_step;
	first_rx_pid = b->first_rx_pid;
	first_rx_us = b->first_rx_us;
	first_rx_deferred = b->first_rx_deferred;
	old_rx_quiesced = b->old_rx_quiesced;
	xinput_query_attempted = b->xinput_query_attempted;
	xinput_query_result = b->xinput_query_result;
	spin_unlock_irqrestore(&b->lock, flags);
	dev_info(&g->udev->dev,
		 "native bootstrap finished: %d; failed_stage=%d step=%u pending=%u transition=%u tx_count=%u tx_step=%u tx_status=%d tx_actual=%d tx_expected=%u; "
		 "first_rx_status=%d first_rx_source=%u first_rx_stage=%d first_rx_step=%u first_rx_pid=%04x first_rx_us=%llu first_rx_deferred=%u old_rx_quiesced=%u; "
		 "xinput_query_attempted=%u xinput_query_result=%d; no automatic retry\n",
		 ret, failed_stage, step, pending, transitioned, tx_count, tx_step,
		 tx_status, tx_actual, tx_expected, first_rx_status, first_rx_source,
		 first_rx_stage, first_rx_step, first_rx_pid, (unsigned long long)first_rx_us,
		 first_rx_deferred, old_rx_quiesced, xinput_query_attempted, xinput_query_result);
	kref_put(&b->ref, gsn_boot_delete);
	return ret;
unlock:
	mutex_unlock(&g->io_lock);
	return ret;
}

static int gsn_boot_status(struct gsn_device *g, struct gsn_boot_status *status)
{
	unsigned long flags;

	if (!g->boot)
		return -ENODATA;
	spin_lock_irqsave(&g->boot->lock, flags);
	status->state = g->boot->core.state;
	/* The retained old FD may race adoption on the new interface's io_lock.
	 * Until handoff is committed, report pending rather than a transient READY.
	 */
	if (g->boot->core.receiver_wait && status->state == GS_BOOT_READY)
		status->state = GS_BOOT_WAIT_RECEIVER;
	status->error = g->boot->core.error;
	status->failed_stage = g->boot->core.failed_stage;
	status->pad_seen = g->boot->core.pad_seen;
	status->imu_seen = g->boot->core.imu_seen;
	status->handover_attempted = g->boot->handover_attempted;
	/* Both the old status FD and the correlated new FD share these tokens.
	 * gs_boot_arrived publishes the new identity before initialization; FAILED
	 * preserves it. A pre-arrival failure still names only the old 100a object.
	 */
	status->port_token = g->boot->core.device.port;
	status->instance_token = g->boot->core.device.instance;
	spin_unlock_irqrestore(&g->boot->lock, flags);
	return 0;
}

/* io_lock held. Resume only the same, previously initialized native binding.
 * The PM callback never sends initialization or changes the USB identity.
 * One explicit attempt per completed PM cycle, bounded by fresh IMU evidence.
 */
static int gsn_resume_session(struct gsn_device *g)
{
	struct gs_boot_device identity = g->identity;
	unsigned long flags;
	u64 sample_number, deadline;
	u8 packet[64];
	int ret, i, len;
	bool fresh;

	if (!persistent_mode || !capable(CAP_SYS_ADMIN))
		return -EPERM;
	spin_lock_irqsave(&g->lock, flags);
	if (!g->boot_handoff || !g->pm_quiesced || !gs_pid_native(g->rt.pid) ||
	    g->rt.state != GS_QUIESCED || !g->stopping) {
		ret = -EINVAL;
	} else if (!g->resume_ready) {
		ret = -EAGAIN;
	} else {
		g->resume_ready = false;
		g->pm_quiesced = false; /* Consumed even when the attempted resume fails. */
		g->resuming = true;
		ret = 0;
	}
	spin_unlock_irqrestore(&g->lock, flags);
	if (ret)
		return ret;
	ret = gsn_describe(g->intf, &identity);
	if (ret || identity.pid != g->rt.pid || !gs_pid_native(identity.pid) ||
	    !identity.exclusive || !gsn_boot_owned_route(g->boot, g)) {
		ret = -ENODEV;
		goto fail;
	}
	spin_lock_irqsave(&g->lock, flags);
	ret = gs_runtime_init(&g->rt, identity.pid, 1);
	g->rt.owner = 1; /* The exclusive control FD owns this explicit attempt. */
	if (!ret)
		ret = gs_runtime_start_persistent(&g->rt, gsn_now_ms());
	sample_number = g->sample.sample_number;
	g->ack_pending = false;
	g->stopping = false;
	spin_unlock_irqrestore(&g->lock, flags);
	if (ret)
		goto fail;
	g->stop_sent = false;
	g->stop_error = 0;
	ret = usb_submit_urb(g->rx_urb, GFP_KERNEL);
	if (ret)
		goto fail;
	for (i = 0; i < 6; i++) {
		if (i < 3) {
			len = gs_gip_init(packet, gsn_sequence(g), i);
		} else {
			gs_heartbeat(packet, gsn_sequence(g));
			len = 64;
		}
		ret = gsn_send(g, packet, len, false);
		if (ret)
			goto fail;
		msleep(50);
	}
	deadline = gsn_now_ms() + 3000;
	g->next_heartbeat = jiffies + msecs_to_jiffies(450);
	for (;;) {
		spin_lock_irqsave(&g->lock, flags);
		fresh = g->sample.sample_number > sample_number &&
			ktime_get_ns() - g->sample.host_monotonic_ns <= GSN_STALE_NS;
		ret = g->rt.state == GS_RUNNING ? 0 : -EIO;
		spin_unlock_irqrestore(&g->lock, flags);
		if (ret)
			goto fail;
		if (fresh)
			break;
		if (gsn_now_ms() >= deadline || signal_pending(current)) {
			ret = signal_pending(current) ? -EINTR : -ETIMEDOUT;
			goto fail;
		}
		if (time_after_eq(jiffies, g->next_heartbeat)) {
			gs_heartbeat(packet, gsn_sequence(g));
			ret = gsn_send(g, packet, 64, false);
			if (ret)
				goto fail;
			g->next_heartbeat = jiffies + msecs_to_jiffies(450);
		}
		msleep_interruptible(10);
	}
	spin_lock_irqsave(&g->lock, flags);
	g->resuming = false;
	mod_delayed_work(system_percpu_wq, &g->service, 0);
	spin_unlock_irqrestore(&g->lock, flags);
	return 0;
fail:
	spin_lock_irqsave(&g->lock, flags);
	g->stopping = true;
	g->resuming = false;
	gs_runtime_halt(&g->rt, GS_FAULTED, ret);
	spin_unlock_irqrestore(&g->lock, flags);
	usb_kill_urb(g->rx_urb);
	gsn_neutral(g);
	gsn_stop(g, true);
	return ret;
}

/* io_lock held. Permit local END of an attested failed or waiting bootstrap.
 * No successful runtime means no motor output was authorized. In particular,
 * this is not permission to invent a 109c->100a command or adopt another node.
 */
static bool gsn_unready_boot_owned(struct gsn_device *g)
{
	struct gs_boot_device identity = g->identity;
	struct gsn_boot *b = g->boot;
	unsigned long flags;
	bool owned, waiting;

	waiting = receiver_wait && !g->stopping && g->rt.state == GS_RUNNING && !g->rt.error;
	if (!persistent_mode || !bootstrap_mode || !b || g->boot_handoff ||
	    g->output_used || !g->rt.owner ||
	    (!waiting && (!g->stopping ||
	     (g->rt.state != GS_FAULTED && g->rt.state != GS_QUIESCED))) ||
	    !gs_pid_native(g->identity.pid) || g->rt.pid != g->identity.pid ||
	    READ_ONCE(g->intf->condition) != USB_INTERFACE_BOUND ||
	    g->intf->dev.driver != &gsn_driver.driver ||
	    usb_get_intfdata(g->intf) != g || !device_is_registered(&g->intf->dev) ||
	    !gsn_boot_owned_route(b, g) || gsn_describe(g->intf, &identity))
		return false;
	spin_lock_irqsave(&b->lock, flags);
	owned = ((b->core.state == GS_BOOT_FAILED && b->core.error < 0 &&
		 b->core.failed_stage >= GS_BOOT_INITIALIZE &&
		 (b->core.failed_stage <= GS_BOOT_READY ||
		  (b->core.receiver_wait && b->core.failed_stage == GS_BOOT_WAIT_RECEIVER))) ||
		(waiting && b->core.receiver_wait && !b->core.error && !b->core.pending_length &&
		 b->core.step == 6 && (b->core.state == GS_BOOT_WAIT_RECEIVER ||
				     b->core.state == GS_BOOT_READY))) && identity.exclusive &&
		b->core.device.pid == identity.pid &&
		b->core.device.port == identity.port &&
		b->core.device.instance == identity.instance &&
		(le16_to_cpu(b->origin->descriptor.idProduct) != 0x100a ?
		 identity.instance == b->core.old_instance :
		 identity.instance != b->core.old_instance) &&
		b->core.device.enumerated_us == identity.enumerated_us &&
		b->core.device.in_interval == identity.in_interval &&
		b->core.device.out_interval == identity.out_interval;
	spin_unlock_irqrestore(&b->lock, flags);
	return owned;
}

/* Root control END is distinct from closing an informational client FD. */
static int gsn_end(struct gsn_device *g)
{
	unsigned long flags;
	int ret;

	/* A retained control FD outlives input_unregister_device after disconnect.
	 * Never touch its removed input object or issue another USB transfer.
	 */
	if (READ_ONCE(g->rt.state) == GS_DISCONNECTED)
		return -ENODEV;
	if (persistent_mode && !capable(CAP_SYS_ADMIN))
		return -EPERM;
	if (bootstrap_mode && !g->boot_handoff && !gsn_unready_boot_owned(g))
		return -EBUSY;
	gsn_boot_cancel_device(g); /* Cancels waiting; never overwrites a prior failure. */
	/* A failed bootstrap has output_used=false: this only clears local state.
	 * The successful-runtime path retains its existing bounded zero transfer.
	 */
	ret = gsn_stop(g, true);
	if (persistent_mode) {
		spin_lock_irqsave(&g->lock, flags);
		g->stopping = true;
		g->pm_quiesced = false;
		g->resume_ready = false;
		gs_runtime_halt(&g->rt, ret ? GS_FAULTED : GS_QUIESCED, ret);
		spin_unlock_irqrestore(&g->lock, flags);
		usb_kill_urb(g->rx_urb);
		gsn_neutral(g);
	}
	return ret;
}

static long gsn_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	struct gsn_device *g = file->private_data;
	void __user *user = (void __user *)arg;
	struct gsn_info info = { .abi_version = GSN_ABI_VERSION };
	struct gsn_sample sample;
	struct gsn_pulse pulse;
	struct gsn_boot_request request;
	struct gsn_boot_status boot_status = { .abi_version = GSN_ABI_VERSION };
	unsigned long flags;
	int ret = 0;

	/* BOOTSTRAP must not hold old io_lock across the USB disconnect. */
	if (cmd == GSN_GET_INPUT_STATUS || cmd == GSN_PUBLISH_INPUT)
		return gsn_input_control(g, cmd, user);
	if (cmd == GSN_BOOTSTRAP) {
		if (copy_from_user(&request, user, sizeof(request)))
			return -EFAULT;
		return gsn_bootstrap(g, &request);
	}
	mutex_lock(&g->io_lock);
	if (cmd == GSN_GET_BOOT_STATUS) {
		ret = gsn_boot_status(g, &boot_status);
		if (!ret && copy_to_user(user, &boot_status, sizeof(boot_status)))
			ret = -EFAULT;
		goto out; /* Old FD remains a status handle after disconnect. */
	}
	if (READ_ONCE(g->rt.state) == GS_DISCONNECTED && cmd != GSN_GET_INFO) {
		ret = -ENODEV;
		goto out;
	}
	if (cmd == GSN_RESUME) {
		ret = gsn_resume_session(g);
		goto out;
	}
	if (g->stopping && cmd != GSN_GET_INFO && cmd != GSN_END_SESSION) {
		ret = -ENODEV;
		goto out;
	}
	if (bootstrap_mode && !g->boot_handoff && cmd != GSN_GET_INFO &&
	    cmd != GSN_GET_SAMPLE && cmd != GSN_END_SESSION) {
		ret = -EBUSY;
		goto out;
	}
	switch (cmd) {
	case GSN_GET_INFO:
		spin_lock_irqsave(&g->lock, flags);
		info.pid = g->rt.pid;
		info.state = g->rt.state;
		info.last_error = g->rt.error;
		info.output_enabled = g->rt.output_enabled;
		info.session_active = g->rt.session_active;
		info.accel_counts_per_g_num = g->accel_scale.counts_per_g_num;
		info.accel_counts_per_g_den = g->accel_scale.counts_per_g_den;
		info.input_packets = g->input_packets;
		info.imu_packets = g->imu_packets;
		info.rejected_packets = g->rejected_packets;
		spin_unlock_irqrestore(&g->lock, flags);
		ret = copy_to_user(user, &info, sizeof(info)) ? -EFAULT : 0;
		break;
	case GSN_GET_SAMPLE:
		ret = gsn_sample_snapshot(g, &sample);
		if (!ret && copy_to_user(user, &sample, sizeof(sample)))
			ret = -EFAULT;
		break;
	case GSN_START_SESSION:
		ret = gsn_start(g);
		break;
	case GSN_PULSE:
		if (copy_from_user(&pulse, user, sizeof(pulse))) {
			ret = -EFAULT;
			break;
		}
		spin_lock_irqsave(&g->lock, flags);
		ret = gs_runtime_pulse(&g->rt, &pulse, gsn_now_ms());
		spin_unlock_irqrestore(&g->lock, flags);
		if (!ret)
			ret = gsn_flush_motors(g);
		if (ret && (!persistent_mode || READ_ONCE(g->rt.state) != GS_RUNNING))
			gsn_stop(g, true);
		break;
	case GSN_STOP:
		g->publication_cancelled = true;
		ret = gsn_stop(g, false);
		break;
	case GSN_END_SESSION:
		ret = gsn_end(g);
		break;
	default:
		ret = -ENOTTY;
	}
 out:
	mutex_unlock(&g->io_lock);
	return ret;
}

static const struct file_operations gsn_fops = {
	.owner = THIS_MODULE, .open = gsn_open, .release = gsn_release,
	.unlocked_ioctl = gsn_ioctl,
#ifdef CONFIG_COMPAT
	.compat_ioctl = compat_ptr_ioctl,
#endif
};

/* The memless callback can run under input's spinlock or its timer: no sleeping,
 * allocation or USB here. The existing serialized worker performs every TX.
 */
static int gsn_play_effect(struct input_dev *input, void *data, struct ff_effect *effect)
{
	struct gsn_device *g = input_get_drvdata(input);
	unsigned long flags;
	int ret;

	if (effect->type != FF_RUMBLE)
		return -EINVAL;
	spin_lock_irqsave(&g->lock, flags);
	ret = g->stopping || g->resuming ? -ENODEV :
		gs_runtime_rumble(&g->rt, effect->u.rumble.strong_magnitude,
				  effect->u.rumble.weak_magnitude, gsn_now_ms());
	if (!ret)
		mod_delayed_work(system_percpu_wq, &g->service, 0);
	spin_unlock_irqrestore(&g->lock, flags);
	return ret;
}

static int gsn_input_register(struct gsn_device *g)
{
	static const unsigned int keys[] = {
		BTN_SOUTH, BTN_EAST, BTN_NORTH, BTN_WEST, BTN_START, BTN_SELECT,
		BTN_TL, BTN_TR, BTN_THUMBL, BTN_THUMBR, BTN_MODE
	};
	unsigned int i;
	int ret;

	g->input_deferred = defer_input && persistent_mode && experimental_gyro &&
		experimental_accel && g->rt.pid == 0x109c;
	g->input = input_allocate_device();
	if (!g->input)
		return -ENOMEM;
	/* Borrow g through drvdata: memless frees its private data on destruction.
	 * Our binding/control krefs own g; unregister drains FF before their drop.
	 */
	input_set_drvdata(g->input, g);
	usb_make_path(g->udev, g->phys, sizeof(g->phys));
	strlcat(g->phys, "/input0", sizeof(g->phys));
	g->input->name = "GameSir G7 Pro";
	g->input->phys = g->phys;
	g->input->id.bustype = BUS_USB;
	g->input->id.vendor = 0x3537;
	g->input->id.product = g->rt.pid;
	g->input->id.version = le16_to_cpu(g->udev->descriptor.bcdDevice);
	g->input->dev.parent = &g->intf->dev;
	if (experimental_gyro && g->rt.pid == 0x109c) {
		/* Session association, not a claimed hardware serial. Nonempty and
		 * distinct for simultaneous dongles and replacement bindings.
		 */
		snprintf(g->sensor_uniq, sizeof(g->sensor_uniq), "gsn-%s-%llu",
			 dev_name(&g->intf->dev), (unsigned long long)g->identity.instance);
		g->input->uniq = g->sensor_uniq;
	}
	for (i = 0; i < ARRAY_SIZE(keys); i++)
		input_set_capability(g->input, EV_KEY, keys[i]);
	if (gs_pid_native(g->rt.pid)) {
		input_set_capability(g->input, EV_KEY, KEY_RECORD);
		for (i = BTN_TRIGGER_HAPPY1; i <= BTN_TRIGGER_HAPPY5; i++)
			input_set_capability(g->input, EV_KEY, i);
	}
	input_set_abs_params(g->input, ABS_X, -32768, 32767, 0, 0);
	input_set_abs_params(g->input, ABS_Y, -32768, 32767, 0, 0);
	input_set_abs_params(g->input, ABS_RX, -32768, 32767, 0, 0);
	input_set_abs_params(g->input, ABS_RY, -32768, 32767, 0, 0);
	input_set_abs_params(g->input, ABS_Z, 0, 1023, 0, 0);
	input_set_abs_params(g->input, ABS_RZ, 0, 1023, 0, 0);
	input_set_abs_params(g->input, ABS_HAT0X, -1, 1, 0, 0);
	input_set_abs_params(g->input, ABS_HAT0Y, -1, 1, 0, 0);
	if (persistent_mode && gs_pid_native(g->rt.pid)) {
		input_set_capability(g->input, EV_FF, FF_RUMBLE);
		ret = input_ff_create_memless(g->input, NULL, gsn_play_effect);
		if (ret)
			return ret;
	}
	/* Publish sensors first so a consumer opening the new gamepad can find
	 * its partner immediately. Both allocations are unwound on probe error.
	 */
	ret = gsn_gyro_register(g);
	if (ret)
		return ret;
	if (g->input_deferred)
		return 0;
	ret = input_register_device(g->input);
	if (!ret)
		g->input_registered = true;
	return ret;
}

/* USB device lock serializes against disconnect/PM; io_lock against END/STOP.
 * No USB transfer, re-registration, new identity or start permission here.
 */
static int gsn_input_control(struct gsn_device *g, unsigned int cmd, void __user *user)
{
	struct gsn_input_publish request = {0};
	struct gsn_input_status status = { .abi_version = GSN_ABI_VERSION };
	unsigned long flags;
	bool guide;
	int ret = 0;

	if (cmd != GSN_GET_INPUT_STATUS && cmd != GSN_PUBLISH_INPUT)
		return -ENOTTY;
	if (!capable(CAP_SYS_ADMIN))
		return -EPERM;
	if (cmd == GSN_PUBLISH_INPUT && copy_from_user(&request, user, sizeof(request)))
		return -EFAULT;
	usb_lock_device(g->udev);
	mutex_lock(&g->io_lock);
	if (g->intf->dev.driver != &gsn_driver.driver || usb_get_intfdata(g->intf) != g ||
	    READ_ONCE(g->intf->condition) != USB_INTERFACE_BOUND ||
	    !device_is_registered(&g->intf->dev) || g->rt.state == GS_DISCONNECTED) {
		ret = -ENODEV;
		goto out;
	}
	if (cmd == GSN_GET_INPUT_STATUS) {
		status.flags = (g->input_deferred ? GSN_INPUT_DEFERRED : 0) |
			(g->input_registered ? GSN_INPUT_PUBLISHED : 0) |
			(g->gyro_registered ? GSN_INPUT_SENSOR : 0);
		status.port_token = g->identity.port;
		status.instance_token = g->identity.instance;
		if (g->gyro_registered) {
			strscpy(status.sensor_name, dev_name(&g->gyro_input->dev),
				sizeof(status.sensor_name));
			strscpy(status.uniq, g->sensor_uniq, sizeof(status.uniq));
			status.gyro_resolution = input_abs_get_res(g->gyro_input, ABS_RX);
			status.accel_resolution = input_abs_get_res(g->gyro_input, ABS_X);
		}
		ret = copy_to_user(user, &status, sizeof(status)) ? -EFAULT : 0;
		goto out;
	}
	if (request.abi_version != GSN_ABI_VERSION || request.reserved ||
	    !request.port_token || !request.instance_token ||
	    request.port_token != g->identity.port ||
	    request.instance_token != g->identity.instance) {
		ret = -EINVAL;
		goto out;
	}
	spin_lock_irqsave(&g->lock, flags);
	if (!g->input_deferred || !g->gyro_registered || !g->boot_handoff ||
	    !persistent_mode || g->rt.pid != 0x109c || g->stopping || g->resuming ||
	    g->pm_quiesced || g->publication_cancelled || g->rt.state != GS_RUNNING ||
	    g->rt.error || !g->rt.session_active)
		ret = -ENODEV;
	else if (g->input_registered)
		ret = -EALREADY;
	spin_unlock_irqrestore(&g->lock, flags);
	if (ret)
		goto out;
	ret = input_register_device(g->input);
	if (ret)
		g->publication_cancelled = true; /* Uncertain registration is never retried. */
	if (!ret) {
		spin_lock_irqsave(&g->report_lock, flags);
		g->input_registered = true;
		/* RX may latch a fault during sleeping input registration. Preserve
		 * published ownership for cleanup, but never replay held input then.
		 */
		if (READ_ONCE(g->rt.state) != GS_RUNNING) {
			gsn_neutral_locked(g);
			ret = -EIO;
			spin_unlock_irqrestore(&g->report_lock, flags);
			goto out;
		}
		guide = g->last_guide;
		if (g->have_deferred_pad)
			gsn_pad(g, &g->deferred_pad);
		gsn_extras(g, g->deferred_extras);
		g->last_guide = guide;
		input_report_key(g->input, BTN_MODE, guide);
		input_sync(g->input);
		spin_unlock_irqrestore(&g->report_lock, flags);
	}
out:
	mutex_unlock(&g->io_lock);
	usb_unlock_device(g->udev);
	return ret;
}

static int gsn_gyro_register(struct gsn_device *g)
{
	unsigned int i;
	int ret;
	gs_u32 resolution;

	if (gsn_sensor_options())
		return -EINVAL;
	if (!experimental_gyro || g->rt.pid != 0x109c)
		return 0;
	g->gyro_input = input_allocate_device();
	if (!g->gyro_input)
		return -ENOMEM;
	usb_make_path(g->udev, g->gyro_phys, sizeof(g->gyro_phys));
	strlcat(g->gyro_phys, "/input1", sizeof(g->gyro_phys));
	g->gyro_input->name = "GameSir G7 Pro Motion Sensors";
	g->gyro_input->phys = g->gyro_phys;
	g->gyro_input->uniq = g->sensor_uniq;
	g->gyro_input->id = g->input->id;
	g->gyro_input->dev.parent = &g->intf->dev;
	__set_bit(INPUT_PROP_ACCELEROMETER, g->gyro_input->propbit);
	input_set_capability(g->gyro_input, EV_MSC, MSC_TIMESTAMP);
	for (i = ABS_RX; i <= ABS_RZ; i++) {
		input_set_abs_params(g->gyro_input, i, GS_GYRO_OBSERVED_MIN,
				     GS_GYRO_OBSERVED_MAX, 0, 0);
		input_abs_set_res(g->gyro_input, i, GS_GYRO_OBSERVED_RESOLUTION);
	}
	if (experimental_accel) {
		ret = gs_accel_evdev_resolution(&g->accel_scale, accel_axis_map, &resolution);
		if (ret != GS_SENSOR_EXPERIMENTAL)
			return -EINVAL;
		for (i = ABS_X; i <= ABS_Z; i++) {
			/* Negating s16 minimum requires +32768 in s32. */
			input_set_abs_params(g->gyro_input, i, -32768, 32768, 0, 0);
			input_abs_set_res(g->gyro_input, i, resolution);
		}
	}
	ret = input_register_device(g->gyro_input);
	if (!ret)
		g->gyro_registered = true;
	return ret;
}

/* Permanent quiesce; no automatic resume/reprobe, reset, or mode switch. */
static void gsn_quiesce(struct gsn_device *g, int state, int error)
{
	unsigned long flags;

	if (!g)
		return;
	mutex_lock(&g->io_lock);
	spin_lock_irqsave(&g->lock, flags);
	g->stopping = true;
	g->publication_cancelled = true;
	gs_runtime_halt(&g->rt, state, error);
	spin_unlock_irqrestore(&g->lock, flags);
	mutex_unlock(&g->io_lock);
	/* CLOCK_MONOTONIC stops in suspend. Never silently concatenate a buffered
	 * calibration stream across PM/quiesce; a fresh explicit buffer cycle is
	 * required even if the manager later resumes normal gamepad operation.
	 */
	spin_lock_irqsave(&g->report_lock, flags);
	g->iio_buffer_active = false;
	spin_unlock_irqrestore(&g->report_lock, flags);
	if (state != GS_DISCONNECTED)
		gsn_boot_cancel_device(g);
	usb_kill_urb(g->rx_urb);
	cancel_delayed_work_sync(&g->service); /* Never while holding io_lock. */
	gsn_neutral(g);
	mutex_lock(&g->io_lock);
	gsn_stop(g, true);
	mutex_unlock(&g->io_lock);
}

static void gsn_disconnect(struct usb_interface *intf)
{
	struct gsn_device *g = usb_get_intfdata(intf);

	if (!g)
		return;
	usb_set_intfdata(intf, NULL);
	gsn_quiesce(g, GS_DISCONNECTED, -ENODEV);
	gsn_boot_detach(g);
	if (g->misc_registered)
		misc_deregister(&g->misc);
	if (g->gyro_registered) {
		g->gyro_registered = false;
		input_unregister_device(g->gyro_input);
	} else {
		input_free_device(g->gyro_input);
	}
	g->gyro_input = NULL;
	if (g->input_registered) {
		g->input_registered = false;
		input_unregister_device(g->input);
	} else {
		input_free_device(g->input);
	}
	g->input = NULL;
	if (g->iio_registered) {
		iio_device_unregister(g->iio);
		g->iio_registered = false;
	}
	/* Manual buffer ownership matches manual iio_device_free. Device-managed
	 * cleanup on intf->dev would run after this IIO device has been freed.
	 */
	if (g->iio_buffer)
		iio_kfifo_free(g->iio_buffer);
	g->iio_buffer = NULL;
	if (g->iio)
		iio_device_free(g->iio);
	g->iio = NULL;
	kref_put(&g->ref, gsn_delete);
}

static int gsn_probe(struct usb_interface *intf, const struct usb_device_id *id)
{
	struct usb_device *udev = interface_to_usbdev(intf);
	struct usb_host_interface *alt = intf->cur_altsetting;
	struct usb_endpoint_descriptor *in = NULL, *out = NULL;
	struct gsn_device *g;
	unsigned int i, maxpacket, pid = le16_to_cpu(udev->descriptor.idProduct);
	unsigned long flags;
	struct gs_boot_device identity = {0};
	bool direct_native;
	int ret;

	if (!udev->parent || !alt || le16_to_cpu(udev->descriptor.idVendor) != 0x3537 ||
	    (pid != 0x100a && !gs_pid_native(pid)) || alt->desc.bInterfaceNumber != 0 ||
	    alt->desc.bAlternateSetting != 0)
		return -ENODEV;
	ret = gsn_probe_authorize(intf, pid, &direct_native);
	if (ret)
		return ret;
	if (!bootstrap_mode) {
		if (!test_interface || strcmp(dev_name(&intf->dev), test_interface) ||
		    pid != test_pid)
			return -ENODEV;
		if (atomic_cmpxchg(&binding_used, 0, 1))
			return -EBUSY;
	}
	identity.instance = atomic64_inc_return(&instance_counter);
	identity.port = identity.instance;
	identity.enumerated_us = gsn_now_us(); /* Conservative first-observed age. */
	if (!identity.instance || (bootstrap_mode && gsn_describe(intf, &identity)))
		return -ENODEV;
	for (i = 0; i < alt->desc.bNumEndpoints; i++) {
		struct usb_endpoint_descriptor *ep = &alt->endpoint[i].desc;

		if (ep->bEndpointAddress == 0x82 && usb_endpoint_is_int_in(ep))
			in = ep;
		if (ep->bEndpointAddress == 0x02 && usb_endpoint_is_int_out(ep))
			out = ep;
	}
	if (!in || !out || !in->bInterval || !out->bInterval)
		return -ENODEV;
	maxpacket = usb_endpoint_maxp(in);
	if (maxpacket < (pid == 0x100a ? 20 : 64) || maxpacket > 64 ||
	    (enable_output && gs_pid_native(pid) && usb_endpoint_maxp(out) < 64))
		return -ENODEV;
	g = kzalloc_obj(*g, GFP_KERNEL);
	if (!g)
		return -ENOMEM;
	kref_init(&g->ref);
	mutex_init(&g->io_lock);
	spin_lock_init(&g->lock);
	spin_lock_init(&g->report_lock);
	INIT_DELAYED_WORK(&g->service, gsn_service);
	g->udev = usb_get_dev(udev);
	g->intf = usb_get_intf(intf);
	g->identity = identity;
	g->direct_native = direct_native;
	g->accel_scale.counts_per_g_num = accel_counts_per_g_num;
	g->accel_scale.counts_per_g_den = accel_counts_per_g_den;
	ret = gs_runtime_init(&g->rt, pid, enable_output && gs_pid_native(pid));
	if (ret)
		goto free;
	g->rx_buf = kmalloc(64, GFP_KERNEL);
	g->tx_buf = kmalloc(64, GFP_KERNEL);
	g->rx_urb = usb_alloc_urb(0, GFP_KERNEL);
	if (!g->rx_buf || !g->tx_buf || !g->rx_urb) {
		ret = -ENOMEM;
		goto free;
	}
	ret = gsn_input_register(g);
	if (ret)
		goto cleanup;
	if (gs_pid_native(pid)) {
		g->iio = iio_device_alloc(&intf->dev, 0);
		if (!g->iio) {
			ret = -ENOMEM;
			goto cleanup;
		}
		iio_device_set_drvdata(g->iio, g);
		g->iio->name = "gamesir_g7pro_raw_experimental";
		g->iio->modes = INDIO_DIRECT_MODE | INDIO_BUFFER_SOFTWARE;
		g->iio->info = &gsn_iio_info;
		g->iio->channels = gsn_channels;
		g->iio->num_channels = ARRAY_SIZE(gsn_channels);
		g->iio->available_scan_masks = gsn_scan_masks;
		g->iio->setup_ops = &gsn_iio_buffer_ops;
		ret = iio_device_set_clock(g->iio, CLOCK_MONOTONIC);
		if (ret)
			goto cleanup;
		g->iio_buffer = iio_kfifo_allocate();
		if (!g->iio_buffer) {
			ret = -ENOMEM;
			goto cleanup;
		}
		ret = iio_device_attach_buffer(g->iio, g->iio_buffer);
		if (ret)
			goto cleanup;
		ret = iio_device_register(g->iio);
		if (ret)
			goto cleanup;
		g->iio_registered = true;
	}
	g->misc_name = kasprintf(GFP_KERNEL, "gsnative-%s", dev_name(&intf->dev));
	if (!g->misc_name) {
		ret = -ENOMEM;
		goto cleanup;
	}
	g->misc.minor = MISC_DYNAMIC_MINOR;
	g->misc.name = g->misc_name;
	g->misc.fops = &gsn_fops;
	g->misc.mode = 0600;
	g->misc.parent = &intf->dev;
	usb_set_intfdata(intf, g);
	usb_fill_int_urb(g->rx_urb, udev, usb_rcvintpipe(udev, usb_endpoint_num(in)),
			 g->rx_buf, maxpacket, gsn_rx, g, in->bInterval);
	ret = usb_submit_urb(g->rx_urb, GFP_KERNEL);
	if (ret)
		goto cleanup;
	ret = misc_register(&g->misc);
	if (ret)
		goto cleanup;
	g->misc_registered = true;
	if (bootstrap_mode && pid == 0x109c && !direct_native) {
		ret = gsn_boot_connect(g);
		if (ret)
			goto cleanup;
		spin_lock_irqsave(&g->lock, flags);
		if (!g->stopping)
			mod_delayed_work(system_percpu_wq, &g->service, 0);
		spin_unlock_irqrestore(&g->lock, flags);
	}
	dev_info(&intf->dev, "%s binding: pid=%04x, OUT=%d; explicit activation required\n",
		 bootstrap_mode ? "dynamic" : "TEST", pid, g->rt.output_enabled);
	return 0;
cleanup:
	usb_set_intfdata(intf, g);
	gsn_disconnect(intf);
	return ret;
free:
	kref_put(&g->ref, gsn_delete);
	return ret;
}

static int gsn_suspend(struct usb_interface *intf, pm_message_t message)
{
	struct gsn_device *g = usb_get_intfdata(intf);
	unsigned long flags;

	if (g) {
		spin_lock_irqsave(&g->lock, flags);
		g->pm_quiesced = persistent_mode && g->boot_handoff &&
			g->rt.state == GS_RUNNING && g->rt.session_active;
		g->resume_ready = false;
		spin_unlock_irqrestore(&g->lock, flags);
	}
	gsn_quiesce(g, GS_QUIESCED, -ESHUTDOWN);
	return 0;
}

static int gsn_resume(struct usb_interface *intf)
{
	struct gsn_device *g = usb_get_intfdata(intf);
	unsigned long flags;

	/* No USB command here: the service must request the checked GSN_RESUME. */
	if (g) {
		spin_lock_irqsave(&g->lock, flags);
		if (g->pm_quiesced && g->rt.state == GS_QUIESCED)
			g->resume_ready = true;
		spin_unlock_irqrestore(&g->lock, flags);
	}
	return 0;
}

static int gsn_pre_reset(struct usb_interface *intf)
{
	return gsn_suspend(intf, PMSG_SUSPEND);
}

static void gsn_shutdown(struct usb_interface *intf)
{
	struct gsn_device *g = usb_get_intfdata(intf);
	unsigned long flags;

	if (g) {
		spin_lock_irqsave(&g->lock, flags);
		g->pm_quiesced = false;
		g->resume_ready = false;
		spin_unlock_irqrestore(&g->lock, flags);
	}
	gsn_quiesce(g, GS_QUIESCED, -ESHUTDOWN);
}

static const struct usb_device_id gsn_ids[] = {
	{ USB_DEVICE_INTERFACE_NUMBER(0x3537, 0x100a, 0) },
	{ USB_DEVICE_INTERFACE_NUMBER(0x3537, 0x109c, 0) },
	{ USB_DEVICE_INTERFACE_NUMBER(0x3537, 0x105e, 0) },
	{ }
};

/* Deliberately no MODULE_DEVICE_TABLE: no USB modalias/autoload. */
static struct usb_driver gsn_driver = {
	.name = GSN_DRIVER, .probe = gsn_probe, .disconnect = gsn_disconnect,
	.suspend = gsn_suspend, .resume = gsn_resume, .reset_resume = gsn_resume,
	.pre_reset = gsn_pre_reset, .post_reset = gsn_resume, .shutdown = gsn_shutdown,
	.id_table = gsn_ids, .no_dynamic_id = 1, .soft_unbind = 1,
	.driver = { .groups = gsn_driver_groups },
};

static int __init gsn_init(void)
{
	if (defer_input && !persistent_mode)
		return -EINVAL;
	if (gsn_sensor_options())
		return -EINVAL;
	if (persistent_mode && (!bootstrap_mode || !enable_output))
		return -EINVAL;
	if (receiver_wait && !persistent_mode)
		return -EINVAL;
	if (bootstrap_mode) {
		if (test_interface || test_pid || !enable_output)
			return -EINVAL;
	} else if (!test_interface || !strchr(test_interface, ':') ||
		   strlen(test_interface) > 63 || strchr(test_interface, '/') ||
		   (test_pid != 0x100a && !gs_pid_native(test_pid)) ||
		   (enable_output && !gs_pid_native(test_pid))) {
		return -EINVAL;
	}
	if (!session_ms || session_ms > GSN_MAX_SESSION_MS || !accel_counts_per_g_num ||
	    accel_counts_per_g_num > 1000000 || !accel_counts_per_g_den ||
	    accel_counts_per_g_den > 1000000)
		return -EINVAL;
	return usb_register(&gsn_driver);
}

static void __exit gsn_exit(void)
{
	usb_deregister(&gsn_driver);
}
module_init(gsn_init);
module_exit(gsn_exit);
MODULE_AUTHOR("Dennis");
MODULE_DESCRIPTION("Opt-in GameSir G7 Pro alpha USB gamepad/IIO/four-motor driver");
MODULE_LICENSE("GPL");
MODULE_VERSION("0.1.0.alpha3");
