// SPDX-License-Identifier: GPL-2.0-only
/* Actual adapter code, synthetic kernel objects. No device or kernel access. */
#include "../src/gs_runtime.h"
#include "../src/gs_sensor.h"
#include "../src/gs_startup.h"
#include <assert.h>
#include <endian.h>
#include <errno.h>
#include <linux/input.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef uint8_t u8;
typedef uint32_t u32;
typedef unsigned long long u64;
typedef long long s64;
typedef struct { bool held; } spinlock_t;
struct mutex { bool held; };
struct kref { unsigned refs; };
struct usb_device { unsigned refs; };
struct usb_interface { unsigned refs; void *data; };
struct urb { bool active; };
struct delayed_work { bool queued; };
struct miscdevice { bool registered; };
struct input_dev { int keys[KEY_CNT]; unsigned syncs; bool registered; };
struct gsn_boot { struct kref ref; };
struct gsn_device;
struct iio_buffer { unsigned refs; bool owner_released; };
struct device { void *owner; };
struct device_attribute { unsigned unused; };
struct iio_dev {
	struct device dev;
	struct gsn_device *g;
	struct iio_buffer *buffer;
	unsigned refs;
	int clock_id;
	bool registered, timestamp_enabled, owner_released;
};
enum { IIO_ACCEL = 1, IIO_ANGL_VEL, IIO_COUNT, IIO_TIMESTAMP };
enum { IIO_MOD_X = 1, IIO_MOD_Y, IIO_MOD_Z };
enum { IIO_CHAN_INFO_RAW, IIO_VAL_INT = 1, IIO_LE = 1 };
struct iio_chan_spec {
	unsigned type, modified, channel2, address, info_mask_separate, indexed;
	int channel, scan_index;
	struct { char sign; unsigned realbits, storagebits, endianness; } scan_type;
};
#define IIO_CHAN_SOFT_TIMESTAMP(si) { .type = IIO_TIMESTAMP, .channel = -1, \
	.scan_index = si, .scan_type = { .sign = 's', .realbits = 64, .storagebits = 64 } }
#define BIT(n) (1UL << (n))
#define GENMASK(h, l) (((~0UL) << (l)) & ((~0UL) >> (sizeof(unsigned long) * 8 - 1 - (h))))
#define __aligned(n) __attribute__((aligned(n)))
#undef static_assert
#define static_assert(c) _Static_assert(c, #c)
#define cpu_to_le16(v) htole16((uint16_t)(v))
#define cpu_to_le64(v) htole64((uint64_t)(v))
#define container_of(p, t, m) ((t *)((char *)(p) - offsetof(t, m)))
#define spin_lock_irqsave(p, f) do { (f) = 0; assert(!(p)->held); (p)->held = true; } while (0)
#define spin_unlock_irqrestore(p, f) do { (void)(f); assert((p)->held); (p)->held = false; } while (0)
#define mutex_lock(p) do { assert(!(p)->held); (p)->held = true; } while (0)
#define mutex_unlock(p) do { assert((p)->held); (p)->held = false; } while (0)
#define GSN_STALE_NS 1000000000ULL
typedef int pm_message_t;
static bool persistent_mode = true;
static u64 now_ns;
#define ktime_get_ns() now_ns
#define kfree free
#define sysfs_emit snprintf_wrapper
static unsigned tests, pushes, stops, kills, iio_frees, buffer_frees, g_frees;
static unsigned neutralizations, boot_cancels, teardown_step;
static int push_error;
static unsigned char last_scan[32];
static size_t last_scan_length;
static s64 last_timestamp;
static FILE *synthetic_scan_output;
static int snprintf_wrapper(char *buf, const char *format, ...)
{
	va_list args;
	va_start(args, format);
	int ret = vsnprintf(buf, 64, format, args);
	va_end(args);
	return ret;
}
static void *iio_device_get_drvdata(struct iio_dev *i) { return i->g; }
static struct iio_dev *dev_to_iio_dev(struct device *d) { return d->owner; }
static int iio_device_get_clock(struct iio_dev *i) { return i->clock_id; }
static int iio_push_to_buffers_with_ts(struct iio_dev *, void *, size_t, s64);
static void gsn_boot_cancel_device(struct gsn_device *);
static void gsn_boot_detach(struct gsn_device *);
static void gsn_neutral(struct gsn_device *);
static int gsn_stop(struct gsn_device *, bool);
static void usb_kill_urb(struct urb *);
static void cancel_delayed_work_sync(struct delayed_work *);
static void iio_device_unregister(struct iio_dev *);
static void iio_device_free(struct iio_dev *);
static void iio_kfifo_free(struct iio_buffer *);
static void input_unregister_device(struct input_dev *i) { assert(i->registered); free(i); }
static void input_free_device(struct input_dev *i) { free(i); }
static void input_report_key(struct input_dev *i, unsigned k, int value) { assert(i); i->keys[k] = value; }
static void input_sync(struct input_dev *i) { i->syncs++; }
static void misc_deregister(struct miscdevice *m) { assert(m->registered); m->registered = false; }
static void *usb_get_intfdata(struct usb_interface *i) { return i->data; }
static void usb_set_intfdata(struct usb_interface *i, void *g) { i->data = g; }
static void usb_free_urb(struct urb *u) { free(u); }
static void usb_put_intf(struct usb_interface *i) { assert(i->refs > 1); i->refs--; }
static void usb_put_dev(struct usb_device *u) { assert(u->refs > 1); u->refs--; }
static void gsn_boot_delete(struct kref *r) { assert(!"Unexpected bootstrap object in buffer-only test"); }
static void kref_put(struct kref *r, void (*release)(struct kref *))
{
	assert(r->refs);
	if (!--r->refs) {
		g_frees++;
		release(r);
	}
}
#include "kernel-iio-buffer-functions.h"

static int iio_push_to_buffers_with_ts(struct iio_dev *i, void *data, size_t n, s64 ts)
{
	assert(i && i->registered && i->g && i->g->report_lock.held && !i->g->lock.held);
	assert(i->g->iio_buffer_active && !i->g->stopping && n == 32);
	assert(((uintptr_t)data & 7) == 0);
	/* Kernel API writes a native-endian IIO software timestamp, independently
	 * of the explicitly little-endian raw channels and counter.
	 */
	last_scan_length = i->timestamp_enabled ? 32 : 24;
	if (i->timestamp_enabled)
		memcpy((unsigned char *)data + 24, &ts, sizeof(ts));
	pushes++;
	if (push_error)
		return push_error;
	memcpy(last_scan, data, last_scan_length);
	last_timestamp = ts;
	if (synthetic_scan_output)
		assert(fwrite(data, 1, last_scan_length, synthetic_scan_output) == last_scan_length);
	return 0;
}
static void gsn_boot_cancel_device(struct gsn_device *g) { assert(g->stopping); boot_cancels++; }
static void gsn_boot_detach(struct gsn_device *g) { assert(g->stopping); }
static void usb_kill_urb(struct urb *u)
{
	assert(teardown_step == 0);
	teardown_step = 1;
	if (u) u->active = false;
	kills++;
}
static void cancel_delayed_work_sync(struct delayed_work *w) { w->queued = false; }
static void gsn_neutral(struct gsn_device *g)
{
	assert(g->stopping && !g->rx_urb->active && !g->service.queued);
	assert(!g->iio_buffer_active);
	neutralizations++;
}
static int gsn_stop(struct gsn_device *g, bool end)
{
	assert(g->io_lock.held && !g->iio_buffer_active);
	gs_runtime_stop(&g->rt, end);
	stops++;
	return 0;
}
static void iio_device_unregister(struct iio_dev *i)
{
	assert(i->registered && i->g->stopping && !i->g->iio_buffer_active);
	assert(!i->g->rx_urb->active && teardown_step == 1);
	teardown_step = 2;
	i->registered = false;
}
static void iio_buffer_put(struct iio_buffer *b)
{
	assert(b->refs);
	if (!--b->refs) { free(b); buffer_frees++; }
}
static void iio_kfifo_free(struct iio_buffer *b)
{
	assert(!b->owner_released && (teardown_step == 1 || teardown_step == 2));
	teardown_step = 3;
	b->owner_released = true;
	iio_buffer_put(b);
}
static void iio_device_put(struct iio_dev *i)
{
	assert(i->refs);
	if (!--i->refs) {
		assert(i->owner_released && !i->registered);
		if (i->buffer) {
			assert(i->buffer->owner_released);
			iio_buffer_put(i->buffer);
		}
		free(i);
		iio_frees++;
	}
}
static void iio_device_free(struct iio_dev *i)
{
	assert(!i->registered && !i->owner_released &&
	       (teardown_step == 3 || (!i->buffer && teardown_step == 1)));
	teardown_step = 4;
	i->owner_released = true;
	iio_device_put(i);
}
static struct gsn_device *new_device(void)
{
	struct gsn_device *g = calloc(1, sizeof(*g));
	assert(g);
	g->ref.refs = 1;
	g->udev = calloc(1, sizeof(*g->udev));
	g->intf = calloc(1, sizeof(*g->intf));
	g->rx_urb = calloc(1, sizeof(*g->rx_urb));
	g->input = calloc(1, sizeof(*g->input));
	g->iio = calloc(1, sizeof(*g->iio));
	g->iio_buffer = calloc(1, sizeof(*g->iio_buffer));
	assert(g->udev && g->intf && g->rx_urb && g->input && g->iio && g->iio_buffer);
	g->udev->refs = g->intf->refs = 2;
	g->intf->data = g;
	g->input_registered = g->input->registered = true;
	g->iio_registered = g->iio->registered = true;
	g->iio->g = g;
	g->iio->dev.owner = g->iio;
	g->iio->buffer = g->iio_buffer;
	g->iio->refs = 1;
	g->iio_buffer->refs = 2; /* Caller ownership plus attached-IIO reference. */
	g->iio->timestamp_enabled = true;
	g->iio->clock_id = CLOCK_MONOTONIC;
	g->rx_urb->active = g->service.queued = true;
	g->accel_scale.counts_per_g_num = 8192;
	g->accel_scale.counts_per_g_den = 1;
	assert(!gs_runtime_init(&g->rt, 0x109c, 1));
	g->rt.owner = 1;
	assert(!gs_runtime_start_persistent(&g->rt, 1000));
	g->rt.owner = 0;
	gs_runtime_note_input(&g->rt, GS_PAD_GIP, 1000);
	assert(!gs_runtime_rumble(&g->rt, 65535, 32767, 1000));
	g->boot_handoff = true;
	now_ns = 1000000000ULL;
	teardown_step = 0;
	return g;
}
static void receive(struct gsn_device *g, const struct gs_frame *f)
{
	unsigned long flags;
	spin_lock_irqsave(&g->report_lock, flags);
	gsn_imu(g, f);
	spin_unlock_irqrestore(&g->report_lock, flags);
}
static uint16_t le16_at(unsigned at)
{
	return last_scan[at] | (uint16_t)last_scan[at + 1] << 8;
}
static u64 le64_at(unsigned at)
{
	u64 value = 0;
	for (unsigned n = 0; n < 8; n++) value |= (u64)last_scan[at + n] << (8 * n);
	return value;
}
static void verify_channels(void)
{
	assert(sizeof(gsn_channels) / sizeof(gsn_channels[0]) == 8);
	for (unsigned n = 0; n < 6; n++) {
		const struct iio_chan_spec *c = &gsn_channels[n];
		assert(c->scan_index == (int)n && c->address == n % 3);
		assert(c->type == (n < 3 ? IIO_ACCEL : IIO_ANGL_VEL));
		assert(c->scan_type.sign == 's' && c->scan_type.realbits == 16);
		assert(c->scan_type.storagebits == 16 && c->scan_type.endianness == IIO_LE);
		assert(c->info_mask_separate == BIT(IIO_CHAN_INFO_RAW));
	}
	assert(gsn_channels[6].type == IIO_COUNT && gsn_channels[6].indexed);
	assert(gsn_channels[6].channel == 0 && gsn_channels[6].scan_index == 6);
	assert(gsn_channels[6].scan_type.sign == 'u' && gsn_channels[6].scan_type.realbits == 64);
	assert(gsn_channels[6].scan_type.storagebits == 64 && gsn_channels[6].scan_type.endianness == IIO_LE);
	assert(!gsn_channels[6].info_mask_separate);
	assert(gsn_channels[7].type == IIO_TIMESTAMP && gsn_channels[7].scan_index == 7);
	tests++;
}
static void verify_stream_active(struct gsn_device *g, bool expected)
{
	char text[64];
	struct gs_runtime before = g->rt;
	assert(buffer_stream_active_show(&g->iio->dev, NULL, text) == 2);
	assert(!strcmp(text, expected ? "1\n" : "0\n"));
	assert(!g->report_lock.held && !memcmp(&before, &g->rt, sizeof(before)));
	tests++;
}
static void buffer_cases(void)
{
	struct gsn_device *g = new_device();
	struct gs_frame f = { .kind = GS_IMU, .accel = {-32768, 8192, 32767},
		.gyro = {-1, 12345, -23456}, .extras = {0x3b, 3} };
	int value, unused;
	unsigned before = pushes, stop_before = stops;
	unsigned long mask;
	struct gs_runtime runtime = g->rt;
	verify_stream_active(g, false);
	assert(gsn_iio_preenable(g->iio) == -ENODATA); tests++;
	receive(g, &f);
	assert(pushes == before && g->sample.sample_number == 1); tests++;
	assert(!memcmp(&runtime, &g->rt, sizeof(runtime)) && stops == stop_before); tests++;
	for (mask = 0; mask < 256; mask++)
		assert(gsn_iio_scan_mask(g->iio, &mask) == (mask == 127));
	tests++;
	g->iio->clock_id = CLOCK_BOOTTIME;
	assert(gsn_iio_preenable(g->iio) == -EINVAL); tests++;
	g->iio->clock_id = CLOCK_MONOTONIC;
	assert(!gsn_iio_preenable(g->iio) && !g->iio_buffer_active); tests++;
	g->rt.owner = 1;
	assert(!gsn_iio_preenable(g->iio) && g->rt.owner == 1);
	g->rt.owner = 0; tests++;
	assert(!gsn_iio_postenable(g->iio) && g->iio_buffer_active); tests++;
	verify_stream_active(g, true);
	now_ns += 1234567;
	receive(g, &f);
	assert(pushes == before + 1 && last_scan_length == 32 && last_timestamp == (s64)now_ns);
	assert(le64_at(16) == 2 && g->sample.sample_number == 2); tests++;
	for (unsigned n = 0; n < 3; n++) {
		assert(le16_at(n * 2) == (uint16_t)f.accel[n]);
		assert(le16_at(6 + n * 2) == (uint16_t)f.gyro[n]);
		assert(g->sample.accel_raw[n] == f.accel[n] && g->sample.gyro_raw[n] == f.gyro[n]);
	}
	for (unsigned n = 12; n < 16; n++) assert(last_scan[n] == 0);
	s64 packed_time;
	memcpy(&packed_time, last_scan + 24, sizeof(packed_time));
	assert(packed_time == (s64)now_ns && g->sample.host_monotonic_ns == now_ns); tests++;
	assert(g->input->keys[BTN_TRIGGER_HAPPY1] && g->input->keys[BTN_TRIGGER_HAPPY2]);
	assert(g->input->keys[BTN_TRIGGER_HAPPY3] && g->input->keys[BTN_TRIGGER_HAPPY4]); tests++;
	for (unsigned n = 0; n < 6; n++) {
		assert(gsn_iio_raw(g->iio, &gsn_channels[n], &value, &unused, IIO_CHAN_INFO_RAW) == IIO_VAL_INT);
		assert(value == (n < 3 ? f.accel[n] : f.gyro[n - 3]));
	}
	assert(gsn_iio_raw(g->iio, &gsn_channels[0], &value, &unused, 999) == -EINVAL); tests++;
	for (int failure = 0; failure < 2; failure++) {
		push_error = failure ? -ENOMEM : -ENOSPC;
		now_ns += 1000000;
		receive(g, &f);
		assert(g->iio_push_errors == (u64)failure + 1 && le64_at(16) == 2);
		assert(g->sample.sample_number == (u64)failure + 3);
		assert(!g->stopping && !memcmp(&runtime, &g->rt, sizeof(runtime)) && stops == stop_before);
		tests++;
	}
	char text[64];
	assert(buffer_push_errors_show(&g->iio->dev, NULL, text) == 2 && !strcmp(text, "2\n")); tests++;
	push_error = 0;
	now_ns += 1000000;
	f.accel[0] = 123;
	f.gyro[2] = -222;
	receive(g, &f);
	assert(le64_at(16) == 5 && le16_at(0) == 123 && le16_at(10) == (uint16_t)-222); tests++;
	assert(!gsn_iio_predisable(g->iio) && !g->iio_buffer_active);
	verify_stream_active(g, false);
	before = pushes;
	receive(g, &f);
	assert(pushes == before && g->sample.sample_number == 6); tests++;
	assert(!gsn_iio_preenable(g->iio) && !gsn_iio_postenable(g->iio));
	now_ns += 1000000;
	receive(g, &f);
	assert(le64_at(16) == 7); tests++;
	/* Standard IIO permits timestamps to be disabled independently. Such a
	 * 24-byte scan remains a valid IIO subset but is not calibration input.
	 */
	assert(!gsn_iio_predisable(g->iio));
	g->iio->timestamp_enabled = false;
	assert(!gsn_iio_preenable(g->iio) && !gsn_iio_postenable(g->iio));
	now_ns += 1000000;
	receive(g, &f);
	assert(last_scan_length == 24 && le64_at(16) == 8); tests++;
	g->iio->timestamp_enabled = true;
	g->imu_packets = 0x100000002ULL;
	now_ns = (1ULL << 53) + 123456;
	receive(g, &f);
	memcpy(&packed_time, last_scan + 24, sizeof(packed_time));
	assert(le64_at(16) == 0x100000003ULL && packed_time == (s64)now_ns); tests++;
	/* Invalid experimental acceleration conversion must not invalidate raw
	 * coherent measurements or introduce a gyro-scale assumption.
	 */
	g->accel_scale.counts_per_g_den = 0;
	now_ns++;
	receive(g, &f);
	assert(!(g->sample.flags & GSN_FLAG_ACCEL_VALID));
	assert(le16_at(0) == 123 && le16_at(10) == (uint16_t)-222); tests++;
	/* A stale or faulted runtime cannot begin a fresh buffered measurement. */
	now_ns += GSN_STALE_NS + 1;
	assert(gsn_iio_preenable(g->iio) == -ESTALE); tests++;
	assert(!gsn_iio_predisable(g->iio));
	assert(gsn_iio_postenable(g->iio) == -ESTALE && !g->iio_buffer_active); tests++;
	g->rt.state = GS_FAULTED;
	assert(gsn_iio_preenable(g->iio) == -EIO); tests++;
	g->rt.state = GS_RUNNING;
	struct usb_device *u = g->udev;
	struct usb_interface *i = g->intf;
	gsn_disconnect(i);
	assert(!i->data && u->refs == 1 && i->refs == 1 && teardown_step == 4); tests++;
	free(u); free(i);
}
static void pm_and_lifetime_cases(void)
{
	struct gsn_device *g = new_device();
	struct gs_frame f = { .kind = GS_IMU, .accel = {0, 0, 8192}, .gyro = {1, 2, 3} };
	receive(g, &f);
	assert(!gsn_iio_preenable(g->iio) && !gsn_iio_postenable(g->iio));
	u64 sequence = g->imu_packets;
	unsigned before = pushes, cancel_before = boot_cancels;
	assert(!gsn_suspend(g->intf, 0));
	verify_stream_active(g, false);
	assert(!g->iio_buffer_active && g->stopping && g->pm_quiesced);
	assert(g->rt.state == GS_QUIESCED && !g->rx_urb->active && !g->service.queued); tests++;
	assert(gsn_iio_preenable(g->iio) == -ENODEV); tests++;
	assert(!gsn_resume(g->intf) && g->resume_ready && !g->iio_buffer_active); tests++;
	verify_stream_active(g, false);
	/* Simulate manager-approved runtime recovery only. It cannot silently
	 * reconnect an old calibration stream; explicit buffer cycling is needed.
	 */
	g->stopping = false;
	g->rt.state = GS_RUNNING;
	g->rx_urb->active = true;
	now_ns += 1000000;
	receive(g, &f);
	assert(g->imu_packets == sequence + 1 && pushes == before && !g->iio_buffer_active); tests++;
	assert(!gsn_iio_predisable(g->iio));
	assert(!gsn_iio_preenable(g->iio) && !gsn_iio_postenable(g->iio));
	verify_stream_active(g, true);
	now_ns += 1000000;
	receive(g, &f);
	assert(le64_at(16) == sequence + 2 && pushes == before + 1); tests++;
	/* Retain both a control-side device reference and an IIO-side open-file
	 * reference. The real Linux IIO-core mechanics are not executed here.
	 */
	g->ref.refs++;
	struct iio_dev *retained_iio = g->iio;
	retained_iio->refs++;
	struct usb_device *u = g->udev;
	struct usb_interface *i = g->intf;
	unsigned freed_iio = iio_frees, freed_buffers = buffer_frees;
	teardown_step = 0;
	gsn_disconnect(i);
	assert(g->ref.refs == 1 && !g->input && !g->iio && !g->iio_buffer);
	assert(!g->iio_registered && !g->input_registered && !g->iio_buffer_active); tests++;
	assert(gsn_sample_snapshot(g, &(struct gsn_sample){0}) == -ENODEV); tests++;
	assert(!retained_iio->registered && retained_iio->owner_released);
	assert(retained_iio->buffer->owner_released && retained_iio->buffer->refs == 1);
	assert(iio_frees == freed_iio && buffer_frees == freed_buffers); tests++;
	assert(boot_cancels == cancel_before + 1); /* Disconnect never retries bootstrap. */
	kref_put(&g->ref, gsn_delete);
	assert(u->refs == 1 && i->refs == 1); tests++;
	/* A retained IIO FD may release core-owned memory after g has gone; no
	 * driver callback or stale g dereference is allowed in that release.
	 */
	iio_device_put(retained_iio);
	assert(iio_frees == freed_iio + 1 && buffer_frees == freed_buffers + 1); tests++;
	free(u); free(i);
	gsn_quiesce(NULL, GS_DISCONNECTED, -ENODEV); tests++;
}
static void partial_probe_cleanup_cases(void)
{
	/* Drive the actual teardown for the allocation/attach/register stages.
	 * Probe allocation calls and IIO-core attachment are simulated explicitly.
	 */
	for (unsigned stage = 0; stage < 4; stage++) {
		struct gsn_device *g = new_device();
		struct usb_device *u = g->udev;
		struct usb_interface *i = g->intf;
		g->iio_registered = g->iio->registered = false;
		if (stage < 2) {
			/* IIO allocation/clock step succeeded, FIFO absent. */
			free(g->iio_buffer);
			g->iio_buffer = g->iio->buffer = NULL;
			if (!stage) {
				free(g->iio);
				g->iio = NULL;
			}
		} else if (stage == 2) {
			/* FIFO allocation succeeded, attachment failed. */
			g->iio_buffer->refs = 1;
			g->iio->buffer = NULL;
		}
		unsigned before_g = g_frees, before_iio = iio_frees;
		unsigned before_buffer = buffer_frees;
		gsn_disconnect(i);
		assert(!i->data && u->refs == 1 && i->refs == 1);
		assert(g_frees == before_g + 1);
		assert(iio_frees == before_iio + (stage != 0));
		assert(buffer_frees == before_buffer + (stage >= 2));
		tests++;
		free(u); free(i);
	}
}
static void emit_synthetic_reference(unsigned axis, int angle)
{
	/* Own analytic triangular pulse. Integer nanosecond sampling and raw counts
	 * imply 90.00000821525 degrees under the deliberately constructed 500-dps
	 * hypothesis. This is not real hardware or a selected runtime profile.
	 */
	assert(axis < 3 && (angle == 90 || angle == -90 || angle == 180 || angle == -180));
	struct gsn_device *g = new_device();
	struct gs_frame f = { .kind = GS_IMU, .accel = {123, -456, 8192}, .gyro = {7, -11, 23} };
	receive(g, &f); /* Establish the ordinary fresh snapshot before buffer enable. */
	assert(!gsn_iio_preenable(g->iio) && !gsn_iio_postenable(g->iio));
	synthetic_scan_output = stdout;
	for (unsigned i = 0; i < 405; i++) {
		const int bias[3] = {7, -11, 23};
		for (unsigned n = 0; n < 3; n++) f.gyro[n] = bias[n];
		if (i >= 101 && i <= 303) {
			unsigned relative = i - 101;
			unsigned rise = relative < 202 - relative ? relative : 202 - relative;
			int pulse = rise * 100 * abs(angle) / 90;
			f.gyro[axis] += angle < 0 ? -pulse : pulse;
		}
		now_ns = 1000000000ULL + (u64)i * 5041523ULL;
		receive(g, &f);
	}
	assert(!fflush(stdout));
	synthetic_scan_output = NULL;
	struct usb_device *u = g->udev;
	struct usb_interface *i = g->intf;
	gsn_disconnect(i);
	free(u); free(i);
}
int main(int argc, char **argv)
{
	if (argc == 4 && !strcmp(argv[1], "--emit-synthetic-angle")) {
		emit_synthetic_reference((unsigned)strtoul(argv[2], NULL, 10), atoi(argv[3]));
		return 0;
	}
	assert(argc == 1);
	verify_channels();
	buffer_cases();
	pm_and_lifetime_cases();
	partial_probe_cleanup_cases();
	assert(iio_frees == 5 && buffer_frees == 4 && g_frees == 6);
	assert(kills == 7 && neutralizations == 7 && stops == 7);
	printf("PASS: %u actual-kernel IIO adapter groups; scan metadata, full masks, coherent 32-byte packing, signed extremes, zero padding, shared RX timestamp/count, unchanged raw/Paddles/runtime, nonfatal FIFO errors, re-enable, stale/fault rejection, PM stream break, retained IIO/control-reference teardown and partial-probe cleanup\n", tests);
	return 0;
}
