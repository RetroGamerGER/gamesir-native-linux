// SPDX-License-Identifier: GPL-2.0-only
/* Actual adapter functions, synthetic input/FF ownership. No kernel/device I/O. */
#include "../src/gs_runtime.h"
#include "../src/gs_sensor.h"
#include "../src/gs_startup.h"
#include <assert.h>
#include <errno.h>
#include <linux/input.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint8_t u8;
typedef uint64_t u64;
typedef struct { bool held; } spinlock_t;
struct mutex { bool held; };
struct kref { unsigned int refs; };
struct device { struct device *parent; };
struct usb_device { struct { unsigned int bcdDevice; } descriptor; unsigned int refs; };
struct usb_interface { struct device dev; void *data; unsigned int refs; };
struct urb { bool active; };
struct delayed_work { bool queued; };
struct iio_dev { bool registered; };
struct iio_buffer { bool allocated; };
struct miscdevice { bool registered; };
struct gsn_boot { struct kref ref; };
struct input_dev;
struct fake_ff {
	void *private;
	int (*play)(struct input_dev *, void *, struct ff_effect *);
	bool stopped;
};
struct input_dev {
	const char *name, *phys, *uniq;
	struct input_id id;
	struct device dev;
	void *drvdata;
	struct fake_ff *ff;
	unsigned int refs;
	bool registered;
};
struct inode { unsigned int unused; };
struct file { void *private_data; };

#define container_of(p, t, m) ((t *)((char *)(p) - offsetof(t, m)))
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define READ_ONCE(x) (x)
#define le16_to_cpu(x) (x)
#define GS_DISCONNECTED_EXPECTED GS_DISCONNECTED
#define system_percpu_wq NULL
#define spin_lock_irqsave(p, f) do { (f) = 0; assert(!(p)->held); (p)->held = true; } while (0)
#define spin_unlock_irqrestore(p, f) do { (void)(f); assert((p)->held); (p)->held = false; } while (0)
#define mutex_lock(p) do { assert(!(p)->held); (p)->held = true; } while (0)
#define mutex_unlock(p) do { assert((p)->held); (p)->held = false; } while (0)

static bool experimental_gyro;
#define dev_name(d) "synthetic-interface"
static bool persistent_mode = true, fail_input_alloc, fail_ff_create, fail_input_register;
static unsigned int g_frees, input_frees, ff_frees, ff_owned_data_frees, stop_callbacks;
static uintptr_t g_address;
static struct input_dev *held_input;
static u64 gsn_now_ms(void) { return 100; }
static void kfree(void *p)
{
	if (p && (uintptr_t)p == g_address)
		g_frees++;
	free(p);
}
static void kref_get(struct kref *r) { assert(r->refs); r->refs++; }
static void kref_put(struct kref *r, void (*release)(struct kref *))
{
	assert(r->refs);
	if (!--r->refs)
		release(r);
}
static void gsn_boot_delete(struct kref *r) { assert(!"Unexpected bootstrap in FF test"); }
static void usb_free_urb(struct urb *u) { free(u); }
static void usb_put_dev(struct usb_device *u) { assert(u->refs > 1); u->refs--; }
static void usb_put_intf(struct usb_interface *i) { assert(i->refs > 1); i->refs--; }
static void *usb_get_intfdata(struct usb_interface *i) { return i->data; }
static void usb_set_intfdata(struct usb_interface *i, void *data) { i->data = data; }
static void usb_make_path(struct usb_device *u, char *buf, size_t n)
{
	assert(snprintf(buf, n, "synthetic-device") > 0);
}
static int mod_delayed_work(void *queue, struct delayed_work *w, unsigned int delay)
{
	w->queued = true;
	return 0;
}
static void cancel_delayed_work_sync(struct delayed_work *w) { w->queued = false; }
static void usb_kill_urb(struct urb *u) { if (u) u->active = false; }
static void misc_deregister(struct miscdevice *m) { m->registered = false; }
static void iio_device_unregister(struct iio_dev *i) { assert(i->registered); i->registered = false; }
static void iio_device_free(struct iio_dev *i) { free(i); }
static void iio_kfifo_free(struct iio_buffer *b) { free(b); }
static void input_set_drvdata(struct input_dev *i, void *data) { i->drvdata = data; }
static void *input_get_drvdata(struct input_dev *i) { return i->drvdata; }
static struct input_dev *input_allocate_device(void)
{
	if (fail_input_alloc)
		return NULL;
	struct input_dev *i = calloc(1, sizeof(*i));
	assert(i);
	i->refs = 1;
	return i;
}
static void input_set_capability(struct input_dev *i, unsigned int type, unsigned int code) {}
static void input_set_abs_params(struct input_dev *i, unsigned int code, int lo, int hi,
				 int fuzz, int flat) {}
static int input_ff_create_memless(struct input_dev *i, void *data,
				   int (*play)(struct input_dev *, void *, struct ff_effect *))
{
	if (fail_ff_create)
		return -ENOMEM;
	i->ff = calloc(1, sizeof(*i->ff));
	assert(i->ff);
	i->ff->private = data;
	i->ff->play = play;
	return 0;
}
static int input_register_device(struct input_dev *i)
{
	if (fail_input_register)
		return -EIO;
	i->registered = true;
	return 0;
}
/* Installed Linux ml_ff_destroy owns data, irrespective of playback history.
 * Last input reference controls destruction; input unregister stops FF first.
 */
static void input_put(struct input_dev *i)
{
	assert(i->refs);
	if (--i->refs)
		return;
	if (i->ff) {
		i->ff->stopped = true;
		if (i->ff->private)
			ff_owned_data_frees++;
		free(i->ff->private);
		free(i->ff);
		ff_frees++;
	}
	free(i);
	input_frees++;
}
static void input_unregister_device(struct input_dev *i)
{
	assert(i->registered);
	if (i->ff) {
		/* A flush callback can still occur during unregister. g must be live. */
		struct ff_effect zero = { .type = FF_RUMBLE };
		assert(i->ff->play(i, i->ff->private, &zero) == -ENODEV);
		stop_callbacks++;
		i->ff->stopped = true;
	}
	i->registered = false;
	input_put(i);
}
static void input_free_device(struct input_dev *i)
{
	if (i) {
		assert(!i->registered);
		input_put(i);
	}
}
struct gsn_device;
/* Dedicated gyro harness exercises registration with the option enabled. */
static int gsn_gyro_register(struct gsn_device *g) { return 0; }
static void gsn_boot_cancel_device(struct gsn_device *g);
static void gsn_boot_detach(struct gsn_device *g);
static void gsn_neutral(struct gsn_device *g);
static int gsn_stop(struct gsn_device *g, bool end);
#include "kernel-ff-lifetime-functions.h"
static void gsn_boot_cancel_device(struct gsn_device *g) { assert(!g->boot); }
static void gsn_boot_detach(struct gsn_device *g) { assert(!g->boot); }
static void gsn_neutral(struct gsn_device *g)
{
	assert(g->stopping && !g->service.queued && !g->rx_urb->active);
}
static int gsn_stop(struct gsn_device *g, bool end)
{
	assert(g->io_lock.held);
	gs_runtime_stop(&g->rt, end);
	return 0;
}
static struct gsn_device *new_device(struct usb_device *u, struct usb_interface *i, unsigned int pid)
{
	struct gsn_device *g = calloc(1, sizeof(*g));
	assert(g);
	g_address = (uintptr_t)g;
	g->ref.refs = 1;
	g->udev = u;
	g->intf = i;
	u->refs++;
	i->refs++;
	i->data = g;
	g->rx_urb = calloc(1, sizeof(*g->rx_urb));
	g->rx_buf = malloc(64);
	g->tx_buf = malloc(64);
	g->misc_name = malloc(32);
	assert(g->rx_urb && g->rx_buf && g->tx_buf && g->misc_name);
	assert(!gs_runtime_init(&g->rt, pid, gs_pid_native(pid)));
	if (gs_pid_native(pid)) {
		g->rt.owner = 1;
		assert(!gs_runtime_start_persistent(&g->rt, gsn_now_ms()));
		g->rt.owner = 0;
		g->boot_handoff = true;
	}
	return g;
}
int main(int argc, char **argv)
{
	assert(argc == 2 || argc == 3);
	const char *name = argv[1];
	bool control = strstr(name, "control") != NULL;
	bool deferred = strstr(name, "deferred") != NULL;
	bool no_ff = !strcmp(name, "100a");
	bool playback = !strcmp(name, "playback") || !strcmp(name, "deferred-playback");
	fail_input_alloc = !strcmp(name, "input-allocation-failure");
	fail_ff_create = !strcmp(name, "ff-create-failure");
	fail_input_register = !strcmp(name, "input-register-failure");
	struct usb_device u = { .refs = 1 };
	struct usb_interface intf = { .refs = 1 };
	unsigned int pid = no_ff ? 0x100a : argc == 3 ? 0x105e : 0x109c;
	struct gsn_device *g = new_device(&u, &intf, pid);
	int ret = gsn_input_register(g);
	if (fail_input_alloc || fail_ff_create || fail_input_register) {
		assert(ret == (fail_input_register ? -EIO : -ENOMEM));
		assert(!g->input_registered);
	} else {
		assert(!ret && g->input_registered && g->input->id.product == pid);
		assert(!!g->input->ff == !no_ff);
		assert(input_get_drvdata(g->input) == g);
		g->rx_urb->active = true;
		g->misc_registered = g->misc.registered = true;
		g->iio = calloc(1, sizeof(*g->iio));
		assert(g->iio);
		g->iio_registered = g->iio->registered = true;
		if (playback) {
			struct ff_effect effect = { .type = FF_RUMBLE,
				.u.rumble = { .strong_magnitude = 40000, .weak_magnitude = 20000 } };
			assert(!g->input->ff->play(g->input, g->input->ff->private, &effect));
			assert(g->service.queued && g->rt.ff_target[0] && g->rt.ff_target[1]);
		}
		if (deferred) {
			held_input = g->input;
			held_input->refs++;
		}
	}
	struct file fd = { .private_data = &g->misc };
	if (control)
		assert(!gsn_open(NULL, &fd) && g->ref.refs == 2);
	gsn_disconnect(&intf);
	assert(!intf.data);
	if (control) {
		assert(!g_frees && g->ref.refs == 1 && !g->input);
		assert(g->rt.state == GS_DISCONNECTED_EXPECTED);
		if (deferred && strstr(name, "input-first")) {
			input_put(held_input);
			held_input = NULL;
			assert(!g_frees && g->ref.refs == 1);
		}
		assert(!gsn_release(NULL, &fd));
	}
	assert(g_frees == 1 && u.refs == 1 && intf.refs == 1);
	if (held_input) {
		assert(!held_input->registered && held_input->ff->stopped);
		input_put(held_input);
	}
	assert(input_frees == !fail_input_alloc);
	assert(ff_frees == !(no_ff || fail_input_alloc || fail_ff_create));
	assert(!ff_owned_data_frees);
	assert(stop_callbacks == !(no_ff || fail_input_alloc || fail_ff_create || fail_input_register));
	printf("PASS: %s; one kref-owned g free, no FF-owned g, references drained\n", name);
	return 0;
}
