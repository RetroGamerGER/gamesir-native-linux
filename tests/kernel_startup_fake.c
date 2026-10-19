// SPDX-License-Identifier: GPL-2.0-only
/* Simulated kernel environment. No device nodes, syscalls or actual hardware. */
#include "../src/gs_runtime.h"
#include "../src/gs_sensor.h"
#include "../src/gs_startup.h"
#include "startup_fixture.h"
#include <assert.h>
#include <endian.h>
#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <linux/input.h>
typedef uint8_t u8;
typedef uint32_t u32;
typedef uint64_t u64;
typedef int64_t s64;
#define __aligned(n) __attribute__((aligned(n)))
#undef static_assert
#define static_assert(c) _Static_assert(c, #c)
#define cpu_to_le16(v) htole16((uint16_t)(v))
#define cpu_to_le64(v) htole64((uint64_t)(v))
typedef struct {
	bool held;
} spinlock_t;
static void synthetic_unlock_hook(void *lock);
struct mutex {
	bool held;
};
#define container_of(p, t, m) ((t *)((char *)(p) - offsetof(t, m)))
#define READ_ONCE(x) (x)
#define smp_load_acquire(p) (*(p))
#define smp_store_release(p, v) (*(p) = (v))
#define spin_lock_init(p) ((p)->held = false)
#define spin_lock(p)                                                                               \
	do {                                                                                       \
		assert(!(p)->held);                                                                \
		(p)->held = true;                                                                  \
	} while (0)
#define spin_unlock(p)                                                                             \
	do {                                                                                       \
		assert((p)->held);                                                                 \
		(p)->held = false;                                                                 \
		synthetic_unlock_hook(p);                                                          \
	} while (0)
#define spin_lock_irqsave(p, f)                                                                    \
	do {                                                                                       \
		(f) = 0;                                                                           \
		spin_lock(p);                                                                      \
	} while (0)
#define spin_unlock_irqrestore(p, f)                                                               \
	do {                                                                                       \
		(void)(f);                                                                         \
		spin_unlock(p);                                                                    \
	} while (0)
#define mutex_lock(p) spin_lock(p)
#define mutex_unlock(p) spin_unlock(p)
#define GFP_KERNEL 0
#define GFP_ATOMIC 0
#define GSN_USB_TIMEOUT_MS 250
#define GSN_STALE_NS 1000000000ULL
#define GSN_RX_COMPLETION 1
#define GSN_RX_SUBMIT 2
typedef int pm_message_t;
#define PMSG_SUSPEND 1
#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))
#define BIT(x) (1u << (x))
#define CAP_SYS_ADMIN 1
#define current NULL
#define dev_warn(...) ((void)0)
static char bootstrap_log[512];
static void capture_log(const char *format, ...)
{
	va_list args;
	va_start(args, format);
	vsnprintf(bootstrap_log, sizeof(bootstrap_log), format, args);
	va_end(args);
}
#define dev_info(dev, ...) capture_log(__VA_ARGS__)
#define kzalloc_obj(v, flags) calloc(1, sizeof(v))
#define kfree free
struct kref {
	int refs;
};
static void kref_init(struct kref *p) { p->refs = 1; }
static void kref_get(struct kref *p)
{
	assert(p->refs > 0);
	p->refs++;
}
static void kref_put(struct kref *p, void (*del)(struct kref *))
{
	assert(p->refs > 0);
	if (!--p->refs)
		del(p);
}
struct list_head {
	struct list_head *next, *prev;
};
#define INIT_LIST_HEAD(p)                                                                          \
	do {                                                                                       \
		(p)->next = (p);                                                                   \
		(p)->prev = (p);                                                                   \
	} while (0)
#define list_for_each_entry(p, h, m)                                                               \
	for (struct list_head *l = (h)->next;                                                      \
	     l != (h) && ((p) = container_of(l, __typeof__(*(p)), m), 1); l = l->next)
static void list_add_tail(struct list_head *p, struct list_head *h)
{
	p->prev = h->prev;
	p->next = h;
	h->prev->next = p;
	h->prev = p;
}
static void list_del_init(struct list_head *p)
{
	p->prev->next = p->next;
	p->next->prev = p->prev;
	INIT_LIST_HEAD(p);
}
struct work_struct {
	int dummy;
};
struct delayed_work {
	struct work_struct work;
	bool queued;
	u64 due;
};
#define to_delayed_work(p) container_of(p, struct delayed_work, work)
static u64 clock_us;
#define jiffies (clock_us / 1000)
#define msecs_to_jiffies(x) (x)
#define usecs_to_jiffies(x) (((x) + 999) / 1000)
#define time_after_eq(a, b) ((a) >= (b))
#define system_percpu_wq NULL
#define ktime_get() clock_us
#define ktime_to_ms(x) ((x) / 1000)
#define ktime_to_us(x) (x)
#define ktime_get_ns() (clock_us * 1000)
#define __user
static size_t copy_to_user(void *destination, const void *source, size_t length)
{
	if (!destination || !source)
		return length;
	memcpy(destination, source, length);
	return 0;
}
#define copy_from_user copy_to_user
static int mod_delayed_work(void *q, struct delayed_work *w, u64 delay)
{
	w->queued = true;
	w->due = clock_us + delay * 1000;
	return 0;
}
static void cancel_delayed_work_sync(struct delayed_work *w) { w->queued = false; }
struct device_driver {
	const char *name;
};
struct device {
	struct device_driver *driver;
	bool registered;
};
struct usb_driver {
	struct device_driver driver;
};
static struct usb_driver gsn_driver = {.driver = {.name = "gs_native"}};
static struct device_driver xpad = {.name = "xpad"}, foreign = {.name = "foreign"};
#define USB_INTERFACE_BOUND 1
#define USB_INTERFACE_BINDING 2
#define USB_INTERFACE_UNBINDING 3
#define USB_STATE_NOTATTACHED 0
#define USB_STATE_CONFIGURED 1
struct usb_endpoint_descriptor {
	unsigned bEndpointAddress, bmAttributes, wMaxPacketSize, bInterval;
};
struct usb_host_endpoint {
	struct usb_endpoint_descriptor desc;
};
struct usb_host_interface {
	struct {
		unsigned bInterfaceNumber, bAlternateSetting, bInterfaceClass, bInterfaceSubClass,
		    bInterfaceProtocol, bNumEndpoints;
	} desc;
	struct usb_host_endpoint endpoint[2];
};
struct usb_host_config {
	struct {
		unsigned bConfigurationValue;
	} desc;
};
struct usb_device {
	struct usb_device *parent;
	unsigned portnum, state, refs;
	struct {
		unsigned idVendor, idProduct;
	} descriptor;
	struct usb_host_config *actconfig;
	struct device dev;
	bool locked;
};
struct usb_interface {
	struct usb_device *udev;
	struct usb_host_interface *cur_altsetting;
	struct device dev;
	bool authorized;
	unsigned refs;
	void *data;
	unsigned condition;
};
struct urb {
	void *context;
	int status, actual_length;
};
struct input_dev {
	int keys[KEY_CNT], axes[ABS_CNT];
	void *drvdata;
};
static void *input_get_drvdata(struct input_dev *input) { return input->drvdata; }
struct iio_dev;
/* Startup tests have no attached IIO buffer; the separate actual-adapter
 * buffer harness verifies successful/failed pushes and their exact bytes.
 */
static int iio_push_to_buffers_with_ts(struct iio_dev *i, void *scan, size_t n, s64 ts)
{
	(void)i; (void)scan; (void)n; (void)ts;
	assert(!"Unexpected buffer push in startup-only fixture");
	return -ENODEV;
}
struct miscdevice {
	int dummy;
};
struct inode {
	int dummy;
};
struct file {
	void *private_data;
};
#define le16_to_cpu(x) (x)
#define interface_to_usbdev(i) ((i)->udev)
#define usb_endpoint_type(e) ((e)->bmAttributes & 3)
#define usb_endpoint_maxp(e) ((e)->wMaxPacketSize)
#define usb_endpoint_is_int_in(e) (usb_endpoint_type(e) == 3 && ((e)->bEndpointAddress & 128))
#define usb_endpoint_is_int_out(e) (usb_endpoint_type(e) == 3 && !((e)->bEndpointAddress & 128))
#define device_is_registered(d) ((d)->registered)
#define usb_sndintpipe(d, e) (e)
static struct usb_device *usb_get_dev(struct usb_device *d)
{
	assert(d && d->refs);
	d->refs++;
	return d;
}
static void usb_put_dev(struct usb_device *d)
{
	assert(d && d->refs > 1);
	d->refs--;
}
static struct usb_interface *usb_get_intf(struct usb_interface *i)
{
	i->refs++;
	return i;
}
static void usb_put_intf(struct usb_interface *i)
{
	assert(i->refs > 1);
	i->refs--;
}
static void *usb_get_intfdata(struct usb_interface *i) { return i->data; }
static void usb_lock_device(struct usb_device *d)
{
	assert(!d->locked);
	d->locked = true;
}
static void usb_unlock_device(struct usb_device *d)
{
	assert(d->locked);
	d->locked = false;
}
static void usb_free_urb(struct urb *u) { free(u); }
static void usb_kill_urb(struct urb *u);
static bool bootstrap_mode = true, enable_output = true, admin = true, persistent_mode;
static unsigned session_ms = 30000;
static struct mutex boot_list_lock;
static struct list_head boot_list;
struct gsn_device;
/* Gyro registration/emission has its own extracted-code harness. */
static void gsn_gyro_report(struct gsn_device *g, const gs_s16 raw[3], const gs_s16 accel[3], u64 ns)
{ (void)g; (void)raw; (void)accel; (void)ns; }
static void input_report_key(struct input_dev *, unsigned, int);
static void input_report_abs(struct input_dev *, unsigned, int);
static void input_sync(struct input_dev *);
static int usb_interrupt_msg(struct usb_device *, unsigned, void *, int, int *, int);
static int device_driver_attach(const struct device_driver *, struct device *);
static void device_release_driver(struct device *);
static int usb_for_each_dev(void *, int (*)(struct usb_device *, void *));
static struct usb_interface *usb_ifnum_to_if(struct usb_device *, unsigned);
static void msleep_interruptible(unsigned);
#define msleep(x) msleep_interruptible(x)
static bool signal_pending(void *p);
static bool capable(unsigned cap) { return admin; }
static int usb_submit_urb(struct urb *, int);
#include "kernel-startup-functions.h"

static struct usb_device root, hub, replacement_hub, old_usb, new_usb, other_usb;
static struct usb_host_config config;
static struct usb_host_interface old_alt, new_alt;
static struct usb_interface old_intf, new_intf;
static struct gsn_device *old_g, *new_g;
static struct file old_fd;
static unsigned tx_count, releases, attaches, neutrals, instance;
static int fault_tx, attach_error, scenario, submit_error;
static u64 probe_published;
static bool short_tx, moved, appeared, no_imu, sent_imu, interrupted, found_foreign, all_data,
    direct_probe, direct_105e;
static u64 removal_marked_us, removal_delay_us;
static int rx_fault_tx, rx_fault_status, removal_rx_error;
static bool rx_inject_submit, removal_rx_submit;
static bool removal_rx_injected;
static int second_removal_rx_error;
static bool second_removal_rx_submit;
static unsigned old_rx_transition_kills, old_rx_retired_submits;
static int retirement_callback_status, ready_rx_error;
static bool retirement_submit_race, ready_rx_submit, ready_rx_injected;
static int signal_rx_error;
static bool signal_rx_submit, signal_rx_injected;
static unsigned removal_action;
static void input_report_key(struct input_dev *input, unsigned key, int value)
{
	if (old_g && input == old_g->input)
		assert(!old_g->lock.held);
	if (new_g && input == new_g->input)
		assert(!new_g->lock.held);
	input->keys[key] = value;
}
static void input_report_abs(struct input_dev *input, unsigned axis, int value)
{
	input->axes[axis] = value;
}
static void input_sync(struct input_dev *input) { neutrals++; }
static int usb_submit_urb(struct urb *urb, int flags)
{
	if (old_g && urb == old_g->rx_urb && old_g->boot && old_g->boot->old_rx_quiesced)
		old_rx_retired_submits++;
	return submit_error;
}
static void usb_kill_urb(struct urb *urb)
{
	if (old_g && urb == old_g->rx_urb && old_g->boot && !old_g->stopping &&
	    old_g->boot->core.state == GS_BOOT_WAIT_REMOVE) {
		old_rx_transition_kills++;
		assert(old_g->boot->old_rx_quiesced && !old_g->lock.held &&
		       !old_g->boot->lock.held);
		urb->status = retirement_callback_status;
		urb->actual_length = 0;
		gsn_rx(urb);
		if (retirement_submit_race)
			assert(gsn_boot_rx_teardown(old_g, -EPERM, GSN_RX_SUBMIT));
	}
}

/* Simulate a callback on another CPU after OUT9 completion drops its lock,
 * before the service can logically retire/kill RX. Never change adapter code
 * or pretend that callback itself is a physical USB disconnect.
 */
static void synthetic_unlock_hook(void *lock)
{
	if (ready_rx_error && !ready_rx_injected && new_g && new_g->boot &&
	    lock == &new_g->boot->lock && !new_g->lock.held &&
	    new_g->boot->core.state == GS_BOOT_READY) {
		ready_rx_injected = true;
		int previous_submit_error = submit_error;
		submit_error = ready_rx_submit ? ready_rx_error : 0;
		new_g->rx_urb->status = ready_rx_submit ? 0 : ready_rx_error;
		gsn_rx(new_g->rx_urb);
		submit_error = previous_submit_error;
	}
	if (!old_g || !old_g->boot || lock != &old_g->boot->lock || old_g->lock.held ||
	    old_g->boot->old_rx_quiesced || old_g->boot->core.state != GS_BOOT_WAIT_REMOVE ||
	    !removal_rx_error || removal_rx_injected)
		return;
	assert(tx_count == 9 && old_g->boot->core.transition_completed &&
	       !old_g->boot->core.pending_length);
	removal_rx_injected = true; /* Nested helper locks must not inject again. */
	int previous_submit_error = submit_error;
	submit_error = removal_rx_submit ? removal_rx_error : 0;
	old_g->rx_urb->status = removal_rx_submit ? 0 : removal_rx_error;
	old_g->rx_urb->actual_length = 0;
	gsn_rx(old_g->rx_urb);
	if (second_removal_rx_error) {
		submit_error = second_removal_rx_submit ? second_removal_rx_error : 0;
		old_g->rx_urb->status = second_removal_rx_submit ? 0 : second_removal_rx_error;
		gsn_rx(old_g->rx_urb);
	}
	submit_error = previous_submit_error;
}
static int usb_interrupt_msg(struct usb_device *d, unsigned ep, void *buf, int len, int *actual,
			     int timeout)
{
	assert(ep == 2 && timeout == 250 && len > 0 && len <= 64);
	assert((d == &old_usb && old_g->io_lock.held) || (d == &new_usb && new_g->io_lock.held));
	if (direct_105e && tx_count < 6) {
		const struct captured_tx *c = &captured_native[tx_count];
		assert(d == &old_usb && len == (int)c->length && !memcmp(buf, c->data, len));
	} else if (!direct_105e && tx_count < 15) {
		const struct captured_tx *c =
		    tx_count < 9 ? &captured_transition[tx_count] : &captured_native[tx_count - 9];
		assert(len == (int)c->length && !memcmp(buf, c->data, len));
		assert(d == (tx_count < 9 ? &old_usb : &new_usb));
	}
	tx_count++;
	clock_us += 1000;
	*actual = len;
	if ((int)tx_count == rx_fault_tx) {
		old_g->rx_urb->status = rx_inject_submit ? 0 : rx_fault_status;
		if (rx_inject_submit)
			submit_error = rx_fault_status;
		gsn_rx(old_g->rx_urb); /* RX completes while final OUT is still in flight. */
		submit_error = 0;
	}
	if ((int)tx_count == fault_tx) {
		*actual = short_tx ? len - 1 : 0;
		return short_tx ? 0 : -EPIPE;
	}
	return 0;
}
static struct gsn_device *new_device(struct usb_device *u, struct usb_interface *i)
{
	struct gsn_device *g = calloc(1, sizeof(*g));
	assert(g);
	kref_init(&g->ref);
	g->udev = usb_get_dev(u);
	g->intf = usb_get_intf(i);
	i->data = g;
	g->identity.instance = ++instance;
	g->identity.port = instance;
	g->identity.enumerated_us = clock_us;
	assert(!gsn_describe(i, &g->identity));
	assert(
	    !gs_runtime_init(&g->rt, u->descriptor.idProduct, gs_pid_native(u->descriptor.idProduct)));
	g->rx_buf = calloc(1, 64);
	g->tx_buf = calloc(1, 64);
	g->rx_urb = calloc(1, sizeof(*g->rx_urb));
	g->input = calloc(1, sizeof(*g->input));
	g->input->drvdata = g;
	g->input_registered = true;
	g->rx_urb->context = g;
	return g;
}
static int fake_probe(void)
{
	int ret;
	assert(gsn_boot_pending(&new_usb));
	new_intf.dev.driver = &gsn_driver.driver;
	new_g = new_device(&new_usb, &new_intf);
	new_g->rt.owner = 1;
	assert(gsn_start(new_g) == -EAGAIN); /* misc exposure cannot bypass bootstrap. */
	new_g->rt.owner = 0;
	ret = gsn_boot_connect(new_g);
	if (ret) {
		new_intf.data = NULL;
		new_intf.dev.driver = NULL;
		free(new_g->input);
		kref_put(&new_g->ref, gsn_delete);
		new_g = NULL;
		return ret;
	}
	if (scenario == 10) {
		new_intf.condition = USB_INTERFACE_BINDING;
		probe_published = clock_us;
	}
	if (scenario == 11)
		new_intf.condition = USB_INTERFACE_UNBINDING;
	mod_delayed_work(NULL, &new_g->service, 0);
	return 0;
}
static int device_driver_attach(const struct device_driver *drv, struct device *dev)
{
	assert(drv == &gsn_driver.driver && dev == &new_intf.dev && !new_usb.locked);
	attaches++;
	if (attach_error)
		return attach_error;
	if (scenario == 9) {
		dev->driver = &foreign;
		return -EBUSY;
	}
	int ret = fake_probe();
	return scenario == 12 && !ret ? -EBUSY : ret;
}
static void device_release_driver(struct device *dev)
{
	assert(dev == &new_intf.dev && new_usb.locked && dev->driver == &xpad);
	releases++;
	dev->driver = NULL;
}
static int usb_for_each_dev(void *data, int (*cb)(struct usb_device *, void *))
{
	if (found_foreign)
		cb(&other_usb, data);
	if (appeared)
		return cb(&new_usb, data);
	return 0;
}
static struct usb_interface *usb_ifnum_to_if(struct usb_device *u, unsigned n)
{
	assert(u == &new_usb && !n && u->locked);
	return &new_intf;
}
static bool signal_pending(void *p)
{
	/* The supervisor has just polled the core successfully. Another producer
	 * can latch a fatal cause before this signal check returns true.
	 */
	if (signal_rx_error && !signal_rx_injected && old_g && old_g->boot &&
	    old_g->boot->core.state == GS_BOOT_TRANSITION) {
		assert(!old_g->lock.held && !old_g->boot->lock.held);
		signal_rx_injected = true;
		clock_us++;
		int previous_submit_error = submit_error;
		submit_error = signal_rx_submit ? signal_rx_error : 0;
		old_g->rx_urb->status = signal_rx_submit ? 0 : signal_rx_error;
		gsn_rx(old_g->rx_urb);
		submit_error = previous_submit_error;
		return true;
	}
	return interrupted;
}
static void disconnect_fake(struct gsn_device *g)
{
	g->udev->state = USB_STATE_NOTATTACHED;
	gsn_quiesce(g, GS_DISCONNECTED, -ENODEV);
	gsn_boot_detach(g);
	free(g->input);
	g->input = NULL;
	g->input_registered = false;
	g->intf->data = NULL;
	g->intf->dev.driver = NULL;
	kref_put(&g->ref, gsn_delete); /* USB binding ref, old FD remains alive. */
}
static void msleep_interruptible(unsigned ms)
{
	clock_us += (u64)ms * 1000;
	struct gsn_device *active = direct_105e ? old_g : new_g;
	if (active && active->resuming && !no_imu) {
		active->sample.sample_number++;
		active->sample.host_monotonic_ns = clock_us * 1000;
	}
	if (old_g && !old_g->stopping && old_g->service.queued && old_g->service.due <= clock_us) {
		old_g->service.queued = false;
		gsn_service(&old_g->service.work);
	}
	if (scenario == 15 && !moved && tx_count == 3) {
		moved = true;
		disconnect_fake(old_g);
	}
	if (!moved && old_g && old_g->boot && old_g->boot->core.state == GS_BOOT_WAIT_REMOVE &&
	    removal_delay_us && !removal_marked_us) {
		removal_marked_us = clock_us;
		assert(tx_count == 9 && old_g->boot->core.transition_completed &&
		       !old_g->boot->core.pending_length && !gsn_boot_pending(&new_usb));
		if (!removal_rx_error) {
			/* USB core can publish NOTATTACHED before invoking disconnect. */
			old_usb.state = USB_STATE_NOTATTACHED;
		}
		if (removal_action == 1)
			gsn_boot_cancel_device(old_g);
		if (removal_action == 2)
			assert(!gsn_suspend(&old_intf, PMSG_SUSPEND));
		if (removal_action == 3) {
			/* A manual unbind is not a physical re-enumeration callback. */
			old_usb.state = USB_STATE_CONFIGURED;
			gsn_quiesce(old_g, GS_DISCONNECTED, -ENODEV);
			gsn_boot_detach(old_g);
		}
	}
	if (!moved && old_g && old_g->boot && old_g->boot->core.state == GS_BOOT_WAIT_REMOVE &&
	    (!removal_delay_us || clock_us >= removal_marked_us + removal_delay_us)) {
		moved = true;
		disconnect_fake(old_g);
		if (scenario != 1) {
			appeared = true;
			if (scenario == 2)
				new_usb.portnum++;
			if (scenario == 3)
				new_usb.parent = &replacement_hub;
			if (scenario == 4)
				new_intf.dev.driver = &foreign;
			if (scenario == 5)
				new_usb.descriptor.idProduct = 0x109b;
			if (scenario == 6)
				new_intf.authorized = false;
			if (scenario == 7)
				interrupted = true;
			if (direct_probe)
				assert(!fake_probe());
		}
	}
	if (scenario == 10 && clock_us >= probe_published + 30000)
		new_intf.condition = USB_INTERFACE_BOUND;
	if (new_g && !new_g->stopping && new_g->service.queued && new_g->service.due <= clock_us) {
		new_g->service.queued = false;
		gsn_service(&new_g->service.work);
	}
	if (scenario == 13 && tx_count == 12)
		interrupted = true;
	if (scenario == 14 && new_g && tx_count == 12) {
		struct gsn_device *gone = new_g;
		new_g = NULL;
		disconnect_fake(gone);
	}
	active = direct_105e ? old_g : new_g;
	if (active && !no_imu && !sent_imu && active->boot->core.state == GS_BOOT_INITIALIZE &&
	    active->boot->core.step == 6) {
		sent_imu = true;
		memcpy(active->rx_buf, captured_imu, sizeof(captured_imu));
		active->rx_urb->actual_length = sizeof(captured_imu);
		assert(!gsn_boot_rx(active, active->rx_urb));
		if (all_data) {
			memcpy(active->rx_buf, captured_pad, sizeof(captured_pad));
			active->rx_urb->actual_length = sizeof(captured_pad);
			assert(!gsn_boot_rx(active, active->rx_urb));
		}
	}
	assert(clock_us < 40000000); /* Detect accidental unbounded supervisor loops. */
}
static void setup(unsigned root_port, unsigned child_port, bool via_hub)
{
	memset(&root, 0, sizeof(root));
	memset(&hub, 0, sizeof(hub));
	memset(&replacement_hub, 0, sizeof(replacement_hub));
	memset(&old_usb, 0, sizeof(old_usb));
	memset(&new_usb, 0, sizeof(new_usb));
	memset(&other_usb, 0, sizeof(other_usb));
	root.refs = hub.refs = replacement_hub.refs = old_usb.refs = new_usb.refs = other_usb.refs =
	    1;
	root.state = hub.state = replacement_hub.state = old_usb.state = new_usb.state =
	    other_usb.state = USB_STATE_CONFIGURED;
	hub.parent = &root;
	hub.portnum = root_port;
	replacement_hub.parent = &root;
	replacement_hub.portnum = root_port;
	old_usb.parent = new_usb.parent = via_hub ? &hub : &root;
	old_usb.portnum = new_usb.portnum = child_port;
	old_usb.descriptor.idVendor = new_usb.descriptor.idVendor = 0x3537;
	old_usb.descriptor.idProduct = 0x100a;
	new_usb.descriptor.idProduct = 0x109c;
	config.desc.bConfigurationValue = 1;
	old_usb.actconfig = new_usb.actconfig = &config;
	other_usb.parent = &root;
	other_usb.portnum = 77;
	memset(&old_alt, 0, sizeof(old_alt));
	memset(&new_alt, 0, sizeof(new_alt));
	old_alt.desc.bInterfaceClass = new_alt.desc.bInterfaceClass = 0xff;
	old_alt.desc.bInterfaceSubClass = 0x5d;
	old_alt.desc.bInterfaceProtocol = 1;
	new_alt.desc.bInterfaceSubClass = 0x47;
	new_alt.desc.bInterfaceProtocol = 0xd0;
	old_alt.desc.bNumEndpoints = new_alt.desc.bNumEndpoints = 2;
	for (int n = 0; n < 2; n++) {
		old_alt.endpoint[n].desc =
		    (struct usb_endpoint_descriptor){n ? 2 : 0x82, 3, 32, n ? 8 : 1};
		new_alt.endpoint[n].desc =
		    (struct usb_endpoint_descriptor){n ? 2 : 0x82, 3, 64, n ? 8 : 1};
	}
	old_intf = (struct usb_interface){&old_usb, &old_alt, {&gsn_driver.driver, true}, true,
					  1,	    NULL,     USB_INTERFACE_BOUND};
	new_intf = (struct usb_interface){&new_usb, &new_alt, {&xpad, true},	  true,
					  1,	    NULL,     USB_INTERFACE_BOUND};
	INIT_LIST_HEAD(&boot_list);
	clock_us = 0;
	tx_count = releases = attaches = neutrals = instance = 0;
	fault_tx = attach_error = scenario = submit_error = 0;
	bootstrap_log[0] = '\0';
	removal_marked_us = removal_delay_us = 0;
	rx_fault_tx = rx_fault_status = removal_rx_error = 0;
	rx_inject_submit = removal_rx_submit = false;
	removal_rx_injected = false;
	second_removal_rx_error = 0;
	second_removal_rx_submit = false;
	old_rx_transition_kills = old_rx_retired_submits = 0;
	retirement_callback_status = -ENOENT;
	ready_rx_error = 0;
	retirement_submit_race = ready_rx_submit = ready_rx_injected = false;
	signal_rx_error = 0;
	signal_rx_submit = signal_rx_injected = false;
	removal_action = 0;
	moved = appeared = no_imu = sent_imu = interrupted = found_foreign = direct_probe =
	    all_data = direct_105e = false;
	bootstrap_mode = enable_output = admin = true;
	persistent_mode = false;
	new_g = NULL;
	short_tx = false;
	old_g = new_device(&old_usb, &old_intf);
	old_fd.private_data = &old_g->misc;
	assert(!gsn_open(NULL, &old_fd));
}
static void setup_105e(bool persistent)
{
	setup(4, 3, true);
	direct_105e = true;
	persistent_mode = persistent;
	old_usb.descriptor.idProduct = 0x105e;
	old_alt = new_alt;
	old_alt.endpoint[0].desc.bInterval = 2;
	old_alt.endpoint[1].desc.bInterval = 4;
	assert(!gsn_describe(&old_intf, &old_g->identity));
	assert(!gs_runtime_init(&old_g->rt, 0x105e, 1));
	old_g->rt.owner = 1;
}

static void cleanup(void)
{
	assert(boot_list.next == &boot_list);
	if (old_intf.data)
		disconnect_fake(old_g);
	gsn_release(NULL, &old_fd);
	old_g = NULL;
	if (new_g) {
		disconnect_fake(new_g);
		new_g = NULL;
	}
	if (root.refs != 1 || hub.refs != 1 || old_usb.refs != 1 || new_usb.refs != 1)
		fprintf(stderr, "refs root=%u hub=%u old=%u new=%u scenario=%d tx=%u\n", root.refs,
			hub.refs, old_usb.refs, new_usb.refs, scenario, tx_count);
	assert(root.refs == 1 && hub.refs == 1 && old_usb.refs == 1 && new_usb.refs == 1 &&
	       replacement_hub.refs == 1);
	assert(old_intf.refs == 1 && new_intf.refs == 1);
}
static int run(unsigned flags)
{
	const struct gsn_boot_request request = {.abi_version = 1, .flags = flags};
	struct gsn_boot *other = NULL;
	if (found_foreign) {
		/* A second independently waiting dongle, inserted before our transaction. */
		other = calloc(1, sizeof(*other));
		assert(other);
		kref_init(&other->ref);
		other->origin = usb_get_dev(&other_usb);
		other->parent = usb_get_dev(old_usb.parent);
		other->root = usb_get_dev(&root);
		other->portnum = 77;
		other->core.state = GS_BOOT_WAIT_ADD;
		other->core.device = old_g->identity;
		other->core.device.port = 900;
		other->core.device.instance = 901;
		other->core.deadline_us = other->core.phase_deadline_us = 100000000;
		list_add_tail(&other->node, &boot_list);
	}
	int ret = gsn_bootstrap(old_g, &request);
	if (other) {
		assert(other->core.state == GS_BOOT_WAIT_ADD && !other->core.error);
		assert(!other->handover_attempted && !other->attached);
		assert(boot_list.next == &other->node && boot_list.prev == &other->node);
		list_del_init(&other->node);
		kref_put(&other->ref, gsn_boot_delete);
		assert(other_usb.refs == 1);
	}
	return ret;
}
static unsigned persistent_cases(void)
{
	unsigned cases = 0, count;
	struct ff_effect effect = {.type = FF_RUMBLE,
		.u.rumble = {.strong_magnitude = 65535, .weak_magnitude = 32768}};
	struct file fd;

	setup(7, 3, true);
	persistent_mode = true;
	assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
	assert(new_g->rt.persistent && new_g->rt.session_active && !new_g->rt.deadline_ms);
	fd.private_data = &new_g->misc;
	assert(!gsn_open(NULL, &fd));
	mutex_lock(&new_g->io_lock);
	assert(!gsn_start(new_g) && !gsn_start(new_g) && tx_count == 15);
	mutex_unlock(&new_g->io_lock);
	gsn_release(NULL, &fd);
	assert(new_g->rt.session_active && tx_count == 15);
	new_g->input->keys[BTN_SOUTH] = 1;
	for (int key = BTN_TRIGGER_HAPPY1; key <= BTN_TRIGGER_HAPPY4; key++)
		new_g->input->keys[key] = 1;
	clock_us += 30ULL * 24 * 60 * 60 * 1000000;
	gsn_service(&new_g->service.work);
	assert(new_g->rt.session_active && new_g->rt.data_stale && tx_count == 17);
	assert(!new_g->input->keys[BTN_SOUTH]);
	for (int key = BTN_TRIGGER_HAPPY1; key <= BTN_TRIGGER_HAPPY4; key++)
		assert(!new_g->input->keys[key]);
	assert(gsn_play_effect(new_g->input, NULL, &effect) == -EAGAIN);
	count = neutrals;
	gsn_service(&new_g->service.work);
	assert(tx_count == 17 && neutrals == count); /* Once, heartbeats continue later. */
	gs_runtime_note_input(&new_g->rt, GS_IMU, clock_us / 1000);
	count = tx_count;
	assert(!gsn_play_effect(new_g->input, NULL, &effect));
	assert(tx_count == count && new_g->service.queued); /* Atomic callback has no TX. */
	gsn_service(&new_g->service.work);
	assert(tx_count == count + 1 && new_g->tx_buf[10] == 100);
	clock_us += 1000000;
	gsn_service(&new_g->service.work);
	assert(new_g->rt.motors.value[2] == 100 && new_g->rt.session_active);
	effect.u.rumble.strong_magnitude = effect.u.rumble.weak_magnitude = 0;
	assert(!gsn_play_effect(new_g->input, NULL, &effect));
	gsn_service(&new_g->service.work);
	assert(!new_g->rt.motors.value[2] && !new_g->rt.ff_target[0]);
	effect.u.rumble.strong_magnitude = 65535;
	effect.u.rumble.weak_magnitude = 32768;
	mutex_lock(&new_g->io_lock);
	admin = false;
	assert(gsn_end(new_g) == -EPERM);
	admin = true;
	assert(!gsn_end(new_g));
	count = tx_count;
	assert(!gsn_end(new_g) && tx_count == count); /* No endless stop retries. */
	assert(new_g->stopping && new_g->rt.state == GS_QUIESCED);
	assert(gsn_resume_session(new_g) == -EINVAL); /* END is not PM resume permission. */
	mutex_unlock(&new_g->io_lock);
	assert(gsn_play_effect(new_g->input, NULL, &effect) == -ENODEV);
	cleanup();
	cases++;
	setup(7, 4, true);
	persistent_mode = true;
	assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
	fd.private_data = &new_g->misc;
	assert(!gsn_open(NULL, &fd));
	disconnect_fake(new_g); /* Open FD retains g, input object is already gone. */
	count = tx_count;
	unsigned previous_neutrals = neutrals;
	mutex_lock(&new_g->io_lock);
	assert(gsn_end(new_g) == -ENODEV);
	assert(tx_count == count && neutrals == previous_neutrals);
	mutex_unlock(&new_g->io_lock);
	gsn_release(NULL, &fd);
	new_g = NULL;
	cleanup();
	cases++;

	for (int test = 0; test < 10; test++) {
		setup(9, 2, true);
		persistent_mode = true;
		assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
		mutex_lock(&new_g->io_lock);
		assert(gsn_resume_session(new_g) == -EINVAL);
		mutex_unlock(&new_g->io_lock);
		assert(!gsn_suspend(&new_intf, PMSG_SUSPEND));
		assert(new_g->pm_quiesced && !new_g->resume_ready && new_g->stopping);
		assert(gsn_play_effect(new_g->input, NULL, &effect) == -ENODEV);
		fd.private_data = &new_g->misc;
		assert(!gsn_open(NULL, &fd)); /* Status/explicit resume remain accessible. */
		mutex_lock(&new_g->io_lock);
		assert(gsn_resume_session(new_g) == -EAGAIN);
		mutex_unlock(&new_g->io_lock);
		assert(!gsn_resume(&new_intf));
		count = tx_count;
		if (test == 1) no_imu = true;
		if (test == 2) fault_tx = tx_count + 2;
		if (test == 3) submit_error = -EIO;
		if (test == 4) new_usb.descriptor.idProduct = 0x100a;
		if (test == 5) new_alt.endpoint[0].desc.bEndpointAddress = 0x83;
		if (test == 6) new_usb.state = USB_STATE_NOTATTACHED;
		if (test == 7) no_imu = interrupted = true;
		if (test == 8) {
			admin = false;
			mutex_lock(&new_g->io_lock);
			assert(gsn_resume_session(new_g) == -EPERM && tx_count == count);
			mutex_unlock(&new_g->io_lock);
			admin = true;
		}
		if (test == 9) {
			/* An old sample cannot prove a new post-resume stream. */
			new_g->sample.sample_number = 400;
			new_g->sample.host_monotonic_ns = 1;
			no_imu = true;
		}
		mutex_lock(&new_g->io_lock);
		int ret = gsn_resume_session(new_g);
		assert((test == 0 || test == 8) ? ret == 0 : ret < 0);
		assert(!new_g->pm_quiesced && !new_g->resume_ready && !new_g->resuming);
		assert(gsn_resume_session(new_g) == -EINVAL); /* No duplicate initialization. */
		if (!ret) {
			assert(new_g->rt.session_active && new_g->rt.persistent && !new_g->stopping);
			assert(tx_count == count + 6 && new_g->sample.sample_number);
		} else {
			assert(new_g->stopping && new_g->rt.state == GS_FAULTED);
			assert(!new_g->rt.session_active && !new_g->rt.motors.value[2]);
		}
		mutex_unlock(&new_g->io_lock);
		gsn_release(NULL, &fd);
		if (!ret) {
			assert(new_g->rt.session_active);
			assert(!gsn_pre_reset(&new_intf));
			assert(new_g->pm_quiesced && !new_g->resume_ready);
			gsn_shutdown(&new_intf);
		}
		cleanup();
		cases++;
	}
	return cases;
}

static void private_bridge_case(void)
{
	struct file fd;
	struct gsn_pulse p = {.abi_version = 1, .duration_ms = 1000};
	struct gsn_pulse cancel = {.abi_version = 1, .motor = GS_LT, .flags = GSN_PULSE_CANCEL};
	struct ff_effect effect = {.type = FF_RUMBLE,
		.u.rumble = {.strong_magnitude = 65535, .weak_magnitude = 32768}};
	unsigned count;

	setup(2, 6, true);
	persistent_mode = true;
	assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
	fd.private_data = &new_g->misc;
	assert(!gsn_open(NULL, &fd));
	/* Bootstrap already authorizes the persistent runtime: no START duplication. */
	for (unsigned motor = 0; motor < 4; motor++) {
		p.motor = motor;
		p.percent = 11 * (motor + 1);
		mutex_lock(&new_g->io_lock);
		assert(!gs_runtime_pulse(&new_g->rt, &p, gsn_now_ms()));
		assert(!gsn_flush_motors(new_g));
		mutex_unlock(&new_g->io_lock);
	}
	assert(!memcmp(new_g->tx_buf + 6, (u8[]){11, 22, 33, 44}, 4));
	assert(!gsn_play_effect(new_g->input, NULL, &effect));
	gsn_service(&new_g->service.work);
	assert(!memcmp(new_g->tx_buf + 6, (u8[]){11, 22, 100, 50}, 4));
	mutex_lock(&new_g->io_lock);
	assert(!gs_runtime_pulse(&new_g->rt, &cancel, gsn_now_ms()));
	assert(!gsn_flush_motors(new_g));
	mutex_unlock(&new_g->io_lock);
	assert(!memcmp(new_g->tx_buf + 6, (u8[]){0, 22, 100, 50}, 4));
	count = tx_count;
	gsn_release(NULL, &fd); /* Neither ordinary FF nor the other channel is stopped. */
	assert(tx_count == count && new_g->rt.ff_target[0] == 100 &&
	       new_g->rt.motors.value[GS_RT] == 22);
	clock_us += 1000000;
	gs_runtime_note_input(&new_g->rt, GS_IMU, gsn_now_ms());
	gsn_service(&new_g->service.work);
	assert(!new_g->rt.motors.value[GS_RT] && new_g->rt.motors.value[GS_LEFT_GRIP] == 100);
	assert(!new_g->rt.private_motor_mask);
	cleanup();
}

static unsigned failed_boot_end_cases(void)
{
	unsigned cases = 0, count, neutral_count;
	struct gsn_boot_status old_status, new_status, after;
	struct gsn_info info;
	struct file fd;

	/* Exercise the real ioctl gate, including failure before native arrival. */
	setup(4, 6, true);
	persistent_mode = true;
	assert(gsn_ioctl(&old_fd, GSN_GET_BOOT_STATUS, (unsigned long)&old_status) == -ENODATA);
	assert(gsn_ioctl(&old_fd, GSN_END_SESSION, 0) == -EBUSY && !tx_count);
	fault_tx = 3;
	assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) < 0 && !new_g);
	assert(!gsn_ioctl(&old_fd, GSN_GET_BOOT_STATUS, (unsigned long)&old_status));
	assert(old_status.state == GS_BOOT_FAILED && old_status.failed_stage == GS_BOOT_TRANSITION);
	assert(old_status.instance_token == old_g->identity.instance);
	count = tx_count;
	assert(gsn_ioctl(&old_fd, GSN_END_SESSION, 0) == -EBUSY && tx_count == count);
	cleanup();
	cases++;

	for (unsigned cause = 0; cause < 4; cause++) {
		setup(4, 6, true);
		persistent_mode = true;
		if (cause == 0)
			no_imu = true;
		else if (cause == 1)
			fault_tx = 10;
		else if (cause == 2) {
			fault_tx = 15;
			short_tx = true;
		} else {
			scenario = 13; /* Signal after the new native instance was attached. */
		}
		assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) < 0 && new_g);
		assert(new_g->stopping && new_g->rt.state == GS_FAULTED && !new_g->output_used);
		fd.private_data = &new_g->misc;
		assert(!gsn_open(NULL, &fd));
		assert(!gsn_ioctl(&old_fd, GSN_GET_BOOT_STATUS, (unsigned long)&old_status));
		assert(!gsn_ioctl(&fd, GSN_GET_BOOT_STATUS, (unsigned long)&new_status));
		assert(!memcmp(&old_status, &new_status, sizeof(old_status)));
		assert(new_status.state == GS_BOOT_FAILED && new_status.error < 0);
		assert(new_status.failed_stage >= GS_BOOT_INITIALIZE &&
		       new_status.failed_stage <= GS_BOOT_READY);
		assert(new_status.port_token == old_g->identity.port &&
		       new_status.port_token == new_g->identity.port);
		assert(new_status.instance_token == new_g->identity.instance &&
		       new_status.instance_token != old_g->identity.instance);
		assert(gsn_ioctl(&fd, GSN_GET_BOOT_STATUS, 0) == -EFAULT);
		count = tx_count;
		u8 sequence = new_g->sequence;
		assert(gsn_ioctl(&old_fd, GSN_END_SESSION, 0) == -ENODEV);
		assert(!gsn_ioctl(&fd, GSN_END_SESSION, 0));
		assert(!gsn_ioctl(&fd, GSN_END_SESSION, 0)); /* Idempotent; no transfer or retry. */
		assert(!gsn_ioctl(&fd, GSN_GET_INFO, (unsigned long)&info));
		assert(info.pid == 0x109c && info.state == GS_QUIESCED && !info.session_active);
		assert(!gsn_ioctl(&fd, GSN_GET_BOOT_STATUS, (unsigned long)&after));
		assert(!memcmp(&after, &new_status, sizeof(after))); /* Failure remains visible. */
		assert(gsn_ioctl(&fd, GSN_RESUME, 0) == -EINVAL);
		assert(gsn_ioctl(&fd, GSN_START_SESSION, 0) == -ENODEV);
		assert(gsn_ioctl(&fd, GSN_PULSE, 0) == -ENODEV);
		assert(gsn_ioctl(&fd, GSN_STOP, 0) == -ENODEV);
		gsn_service(&new_g->service.work);
		gsn_release(NULL, &fd);
		assert(tx_count == count && new_g->sequence == sequence && !new_g->rt.owner);
		assert(new_usb.descriptor.idProduct == 0x109c &&
		       new_intf.dev.driver == &gsn_driver.driver); /* No false xpad/100a claim. */
		cleanup();
		cases++;
	}

	/* No caller can turn another, replaced, unbound or ongoing instance into
	 * an authorized failed-bootstrap END. Restore synthetic fields for teardown.
	 */
	for (unsigned invalid = 0; invalid < 14; invalid++) {
		setup(4, 6, true);
		persistent_mode = no_imu = true;
		assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == -ETIMEDOUT);
		fd.private_data = &new_g->misc;
		assert(!gsn_open(NULL, &fd));
		struct gsn_boot *boot = new_g->boot;
		struct gs_startup core = boot->core;
		struct gs_boot_device identity = new_g->identity;
		struct gs_runtime runtime = new_g->rt;
		count = tx_count;
		neutral_count = neutrals;
		switch (invalid) {
		case 0: admin = false; break;
		case 1: new_g->boot = NULL; break;
		case 2: new_g->identity.instance++; break;
		case 3: new_g->identity.port++; break;
		case 4: new_usb.parent = &replacement_hub; break;
		case 5: new_intf.dev.driver = &foreign; break;
		case 6: new_intf.data = NULL; break;
		case 7: boot->core.state = GS_BOOT_INITIALIZE; break;
		case 8: boot->core.old_instance = new_g->identity.instance; break;
		case 9: new_g->stopping = false; new_g->rt.state = GS_RUNNING; break;
		case 10: new_g->output_used = true; break;
		case 11: new_g->rt.pid = 0x100a; break;
		case 12: boot->core.failed_stage = GS_BOOT_WAIT_ADD; break;
		case 13: new_intf.condition = USB_INTERFACE_UNBINDING; break;
		}
		assert(gsn_ioctl(&fd, GSN_END_SESSION, 0) == (invalid ? -EBUSY : -EPERM));
		assert(tx_count == count && neutrals == neutral_count);
		admin = true;
		new_g->boot = boot;
		boot->core = core;
		new_g->identity = identity;
		new_g->rt = runtime;
		new_g->stopping = true;
		new_g->output_used = false;
		new_usb.parent = &hub;
		new_intf.dev.driver = &gsn_driver.driver;
		new_intf.data = new_g;
		new_intf.condition = USB_INTERFACE_BOUND;
		assert(!gsn_ioctl(&fd, GSN_END_SESSION, 0) && tx_count == count);
		gsn_release(NULL, &fd);
		cleanup();
		cases++;
	}

	setup(4, 6, true);
	persistent_mode = no_imu = true;
	assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == -ETIMEDOUT);
	fd.private_data = &new_g->misc;
	assert(!gsn_open(NULL, &fd));
	count = tx_count;
	disconnect_fake(new_g); /* The FD pins diagnostics, never the freed input object. */
	assert(gsn_ioctl(&fd, GSN_END_SESSION, 0) == -ENODEV);
	assert(!gsn_ioctl(&fd, GSN_GET_BOOT_STATUS, (unsigned long)&after));
	assert(after.state == GS_BOOT_FAILED && tx_count == count);
	new_g = NULL;
	gsn_release(NULL, &fd);
	cleanup();
	return cases + 1;
}

static unsigned direct_105e_cases(void)
{
	unsigned cases = 0;
	struct gsn_boot_status status;
	struct gsn_info info;
	for (unsigned int persistent = 0; persistent < 2; persistent++) {
		setup_105e(persistent);
		assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == -EINVAL && !tx_count);
		assert(!run(0));
		assert(!new_g && !releases && !attaches && !moved && tx_count == 6);
		assert(old_g->boot_handoff && old_g->rt.pid == 0x105e);
		assert(!gsn_ioctl(&old_fd, GSN_GET_BOOT_STATUS, (unsigned long)&status));
		assert(status.state == GS_BOOT_HANDED_OFF && !status.handover_attempted &&
		       status.instance_token == old_g->identity.instance &&
		       status.port_token == old_g->identity.port);
		assert(!gsn_ioctl(&old_fd, GSN_GET_INFO, (unsigned long)&info));
		assert(info.pid == 0x105e && info.session_active);
		assert(!gsn_ioctl(&old_fd, GSN_START_SESSION, 0) && tx_count == 6);
		if (persistent) {
			assert(!gsn_suspend(&old_intf, PMSG_SUSPEND));
			assert(!gsn_resume(&old_intf));
			mutex_lock(&old_g->io_lock);
			assert(!gsn_resume_session(old_g));
			assert(gs_pid_native(old_g->rt.pid) && old_g->rt.pid == 0x105e);
			assert(gsn_resume_session(old_g) == -EINVAL);
			mutex_unlock(&old_g->io_lock);
		}
		assert(!gsn_ioctl(&old_fd, GSN_END_SESSION, 0));
		assert(!old_g->rt.session_active && old_usb.descriptor.idProduct == 0x105e);
		cleanup(); cases++;
	}
	/* Every init transfer failure preserves exact same-instance diagnostics. */
	for (unsigned int failure = 0; failure < 9; failure++) {
		setup_105e(true);
		if (failure < 6) fault_tx = failure + 1;
		if (failure == 6) no_imu = true;
		if (failure == 7) interrupted = true;
		if (failure == 8) { fault_tx = 6; short_tx = true; }
		assert(run(0) < 0 && !new_g && !releases && !attaches);
		assert(old_g->stopping && !old_g->output_used);
		assert(!gsn_ioctl(&old_fd, GSN_GET_BOOT_STATUS, (unsigned long)&status));
		assert(status.state == GS_BOOT_FAILED && status.error < 0 &&
		       status.instance_token == old_g->identity.instance &&
		       status.failed_stage >= GS_BOOT_INITIALIZE && status.failed_stage <= GS_BOOT_VERIFY);
		unsigned count = tx_count;
		assert(!gsn_ioctl(&old_fd, GSN_END_SESSION, 0));
		assert(!gsn_ioctl(&old_fd, GSN_END_SESSION, 0));
		assert(tx_count == count && old_g->rt.state == GS_QUIESCED);
		cleanup(); cases++;
	}
	/* Failed direct bootstrap cannot neutralize a changed identity, route or owner. */
	for (unsigned int invalid = 0; invalid < 8; invalid++) {
		setup_105e(true); no_imu = true;
		assert(run(0) == -ETIMEDOUT);
		struct gs_boot_device saved = old_g->identity;
		struct gs_startup core = old_g->boot->core;
		unsigned count = tx_count;
		if (invalid == 0) old_g->identity.instance++;
		if (invalid == 1) old_g->identity.port++;
		if (invalid == 2) old_usb.parent = &replacement_hub;
		if (invalid == 3) old_usb.portnum++;
		if (invalid == 4) old_intf.dev.driver = &foreign;
		if (invalid == 5) old_g->boot->core.old_instance++;
		if (invalid == 6) old_usb.descriptor.idProduct = 0x109c;
		if (invalid == 7) old_g->boot->core.device.pid = 0x109c;
		assert(gsn_ioctl(&old_fd, GSN_END_SESSION, 0) == -EBUSY && tx_count == count);
		old_g->identity = saved; old_g->boot->core = core;
		old_usb.parent = &hub; old_usb.portnum = 3;
		old_usb.descriptor.idProduct = 0x105e; old_intf.dev.driver = &gsn_driver.driver;
		assert(!gsn_ioctl(&old_fd, GSN_END_SESSION, 0));
		cleanup(); cases++;
	}
	setup_105e(true); scenario = 15;
	assert(run(0) < 0 && tx_count == 3 && !new_g);
	assert(gsn_ioctl(&old_fd, GSN_END_SESSION, 0) == -ENODEV);
	cleanup();
	return cases + 1;
}

static unsigned removal_order_cases(unsigned selected)
{
	unsigned cases = 0;
	for (unsigned n = 1; n <= 3; n++) {
		if (selected && selected != n)
			continue;
		setup(3, 2, true);
		if (n == 1)
			removal_delay_us = 30000;
		if (n == 2) {
			removal_delay_us = 30000;
			removal_rx_error = -ENODEV;
			removal_rx_submit = true;
		}
		if (n == 3) {
			removal_delay_us = 30000;
			rx_fault_tx = 9;
			rx_fault_status = -ENODEV;
		}
		int result = run(GSN_BOOT_ALLOW_XPAD_HANDOVER);
		fprintf(stderr, "removal-order=%u result=%d state=%d failed_stage=%d step=%u tx=%u\n",
			n, result, old_g->boot->core.state, old_g->boot->core.failed_stage,
			old_g->boot->core.step, tx_count);
		assert(!result && tx_count == 15 && new_g && new_g->boot_handoff);
		cleanup();
		cases++;
	}
	return cases;
}

static unsigned removal_safety_cases(void)
{
	const int teardown_errors[] = {-ENOENT, -ECONNRESET, -ESHUTDOWN, -ENODEV};
	unsigned cases = 0;
	/* Both RX completion and RX resubmit are transport teardown sites. */
	for (unsigned phase = 0; phase < 2; phase++)
		for (unsigned source = 0; source < 2; source++)
			for (unsigned n = 0; n < ARRAY_SIZE(teardown_errors); n++) {
				setup(3, 2, true);
				removal_delay_us = 225000;
				if (phase) {
					rx_fault_tx = 9;
					rx_fault_status = teardown_errors[n];
					rx_inject_submit = source;
				} else {
					removal_rx_error = teardown_errors[n];
					removal_rx_submit = source;
				}
				assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
				assert(tx_count == 15 && new_g && new_g->boot_handoff &&
				       old_g->boot->core.removed_us >= removal_marked_us + removal_delay_us);
				assert(strstr(bootstrap_log, "failed_stage=0") &&
				       strstr(bootstrap_log, "tx_count=15 tx_step=5 tx_status=0 tx_actual=64 tx_expected=64"));
				cleanup(); cases++;
			}
	/* Incomplete/failed TX9 is terminal even after a deferred RX error. */
	for (unsigned short_case = 0; short_case < 2; short_case++) {
		setup(3, 2, true);
		rx_fault_tx = fault_tx = 9;
		rx_fault_status = -ENODEV;
		short_tx = short_case;
		assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == (short_case ? -EREMOTEIO : -EPIPE));
		assert(tx_count == 9 && !new_g && !moved &&
		       old_g->boot->core.failed_stage == GS_BOOT_TRANSITION &&
		       !old_g->boot->core.transition_completed);
		assert(strstr(bootstrap_log, "failed_stage=1 step=8 pending=8 transition=0 tx_count=9 tx_step=8"));
		assert(strstr(bootstrap_log, short_case ? "tx_status=0 tx_actual=7 tx_expected=8" :
						      "tx_status=-32 tx_actual=0 tx_expected=8"));
		cleanup(); cases++;
	}
	/* No teardown exception before the final OUT intent. */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned step = 1; step <= 8; step++) {
			setup(3, 2, true);
			rx_fault_tx = step;
			rx_fault_status = -ENODEV;
			rx_inject_submit = source;
			assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == -ENODEV);
			assert(tx_count == step && !new_g && !moved &&
			       old_g->boot->core.failed_stage == GS_BOOT_TRANSITION);
			cleanup(); cases++;
		}
	/* USB metadata alone never confirms removal or extends the ten-second deadline. */
	setup(3, 2, true);
	removal_delay_us = GS_BOOT_REENUM_US + 1;
	assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == -ETIMEDOUT);
	assert(tx_count == 9 && !new_g && !moved &&
	       old_g->boot->core.failed_stage == GS_BOOT_WAIT_REMOVE &&
	       old_g->boot->core.removed_us == 0 &&
	       clock_us <= removal_marked_us + GS_BOOT_REENUM_US + 10000);
	assert(strstr(bootstrap_log, "failed_stage=2 step=9 pending=0 transition=1") &&
	       strstr(bootstrap_log, "tx_count=9 tx_step=8 tx_status=0 tx_actual=8 tx_expected=8"));
	cleanup(); cases++;
	/* The deferred window cannot bypass topology, owner, cancellation or PM gates. */
	for (unsigned n = 0; n < 6; n++) {
		setup(3, 2, true);
		removal_delay_us = 30000;
		if (n < 3)
			scenario = n + 2; /* Different port, replaced hub, foreign owner. */
		else
			removal_action = n - 2; /* Cancel, suspend, manual unbind. */
		assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) < 0);
		assert(tx_count == 9 && !new_g && !releases && !attaches &&
		       old_g->boot->core.state == GS_BOOT_FAILED);
		cleanup(); cases++;
	}
	return cases;
}

static void first_rx_diagnostic(int status, unsigned source, int stage, unsigned step,
				bool deferred)
{
	struct gsn_boot *b = old_g->boot;
	char expected[64];

	assert(b->first_rx_status == status && b->first_rx_source == source &&
	       b->first_rx_stage == stage && b->first_rx_step == step &&
	       b->first_rx_pid == 0x100a && b->first_rx_us > 0 &&
	       b->first_rx_deferred == deferred);
	snprintf(expected, sizeof(expected), "first_rx_status=%d", status);
	assert(strstr(bootstrap_log, expected));
	snprintf(expected, sizeof(expected), "first_rx_source=%u", source);
	assert(strstr(bootstrap_log, expected));
}

static unsigned removal_transport_cases(void)
{
	const int errors[] = {-EPIPE, -EPROTO};
	unsigned cases = 0;

	/* A transport fault after nine proven OUT completions is evidence to retain,
	 * not evidence that removal happened. The real callback still gates handoff.
	 */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++) {
			setup(3, 2, true);
			removal_delay_us = 225000;
			removal_rx_error = errors[n];
			removal_rx_submit = source;
			assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
			assert(tx_count == 15 && moved && new_g && new_g->boot_handoff &&
			       old_g->boot->core.removed_us >= removal_marked_us + removal_delay_us);
			assert(old_rx_transition_kills == 1 && !old_rx_retired_submits &&
			       old_g->boot->old_rx_quiesced);
			first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
					    GS_BOOT_WAIT_REMOVE, 9, true);
			assert(strstr(bootstrap_log, "failed_stage=0") &&
			       strstr(bootstrap_log, "tx_count=15 tx_step=5 tx_status=0 tx_actual=64 tx_expected=64"));
			cleanup(); cases++;
		}
	/* Earlier errors remain fatal and must not be replaced by generic ENODEV. */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++)
			for (unsigned step = 1; step <= 8; step++) {
				setup(3, 2, true);
				rx_fault_tx = step;
				rx_fault_status = errors[n];
				rx_inject_submit = source;
				assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == errors[n]);
				assert(tx_count == step && !moved && !new_g &&
				       old_g->boot->core.failed_stage == GS_BOOT_TRANSITION);
				first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
						    GS_BOOT_TRANSITION, step - 1, false);
				cleanup(); cases++;
			}
	/* Pending OUT9 is not a proven transition: the new exception is narrower
	 * than the four known teardown statuses retained by the previous fix.
	 */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++) {
			setup(3, 2, true);
			rx_fault_tx = 9;
			rx_fault_status = errors[n];
			rx_inject_submit = source;
			int result = run(GSN_BOOT_ALLOW_XPAD_HANDOVER);
			if (result != errors[n])
				fprintf(stderr, "pending OUT9: RX=%d source=%u result=%d core=%d stage=%d tx=%u\n",
					errors[n], source, result, old_g->boot->core.state,
					old_g->boot->core.failed_stage, tx_count);
			assert(result == errors[n]);
			assert(tx_count == 9 && !moved && !new_g);
			first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
					    GS_BOOT_TRANSITION, 8, false);
			cleanup(); cases++;
		}
	/* A short/failed final OUT remains terminal, independently of an RX error. */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++)
			for (unsigned short_case = 0; short_case < 2; short_case++) {
				setup(3, 2, true);
				rx_fault_tx = fault_tx = 9;
				rx_fault_status = errors[n];
				rx_inject_submit = source;
				short_tx = short_case;
				assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == errors[n]);
				assert(tx_count == 9 && !moved && !new_g &&
				       old_g->boot->core.failed_stage == GS_BOOT_TRANSITION &&
				       !old_g->boot->core.transition_completed);
				assert(old_g->boot->tx_status == (short_case ? 0 : -EPIPE) &&
				       old_g->boot->tx_actual == (short_case ? 7 : 0) &&
				       old_g->boot->tx_expected == 8);
				first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
						    GS_BOOT_TRANSITION, 8, false);
				cleanup(); cases++;
			}
	/* No physical callback is a deadline failure, never a synthetic handoff. */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++) {
			setup(3, 2, true);
			removal_delay_us = GS_BOOT_REENUM_US + 1;
			removal_rx_error = errors[n];
			removal_rx_submit = source;
			assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == -ETIMEDOUT);
			assert(tx_count == 9 && !moved && !new_g && !releases && !attaches &&
			       old_g->boot->core.failed_stage == GS_BOOT_WAIT_REMOVE &&
			       !old_g->boot->core.removed_us &&
			       clock_us <= removal_marked_us + GS_BOOT_REENUM_US + 10000);
			assert(strstr(bootstrap_log, "failed_stage=2 step=9 pending=0 transition=1") &&
			       strstr(bootstrap_log, "tx_count=9 tx_step=8 tx_status=0 tx_actual=8 tx_expected=8"));
			first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
					    GS_BOOT_WAIT_REMOVE, 9, true);
			cleanup(); cases++;
		}
	/* Later callbacks cannot rewrite the first status or its source/stage. */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++) {
			setup(3, 2, true);
			removal_delay_us = 30000;
			removal_rx_error = errors[n];
			removal_rx_submit = source;
			second_removal_rx_error = errors[1 - n];
			second_removal_rx_submit = !source;
			assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
			assert(tx_count == 15 && new_g && new_g->boot_handoff &&
			       old_rx_transition_kills == 1 && !old_rx_retired_submits);
			first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
					    GS_BOOT_WAIT_REMOVE, 9, true);
			cleanup(); cases++;
		}
	/* A recorded transport error grants no new topology, owner, PM or cancel rights. */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++)
			for (unsigned unsafe = 0; unsafe < 6; unsafe++) {
				setup(3, 2, true);
				removal_delay_us = 30000;
				removal_rx_error = errors[n];
				removal_rx_submit = source;
				if (unsafe < 3)
					scenario = unsafe + 2;
				else
					removal_action = unsafe - 2;
				assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) < 0);
				assert(tx_count == 9 && !new_g && !releases && !attaches &&
				       old_g->boot->core.state == GS_BOOT_FAILED);
				first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
						    GS_BOOT_WAIT_REMOVE, 9, true);
				cleanup(); cases++;
			}
	/* Our own RX retirement does not manufacture a first transport error.
	 * Even a successful callback or a racing submit rejection cannot requeue it.
	 */
	const int local_statuses[] = {0, -ENOENT, -ECONNRESET};
	for (unsigned submit_race = 0; submit_race < 2; submit_race++)
		for (unsigned n = 0; n < ARRAY_SIZE(local_statuses); n++) {
			setup(3, 2, true);
			removal_delay_us = 30000;
			retirement_callback_status = local_statuses[n];
			retirement_submit_race = submit_race;
			assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
			assert(tx_count == 15 && new_g && new_g->boot_handoff &&
			       old_rx_transition_kills == 1 && !old_rx_retired_submits &&
			       old_g->boot->old_rx_quiesced && !old_g->boot->first_rx_status &&
			       !old_g->boot->first_rx_source && !old_g->boot->first_rx_us);
			assert(strstr(bootstrap_log, "first_rx_status=0") &&
			       strstr(bootstrap_log, "old_rx_quiesced=1"));
			cleanup(); cases++;
		}
	/* First fatal cause is also preserved at READY, before runtime adoption. */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++) {
			setup(3, 2, true);
			ready_rx_error = errors[n];
			ready_rx_submit = source;
			assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == errors[n]);
			assert(ready_rx_injected && tx_count == 15 && new_g &&
			       !new_g->boot_handoff && new_g->boot->core.state == GS_BOOT_FAILED &&
			       new_g->boot->core.failed_stage == GS_BOOT_READY &&
			       new_g->boot->core.error == errors[n] && new_g->boot->first_rx_status == errors[n] &&
			       new_g->boot->first_rx_source == (source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION) &&
			       new_g->boot->first_rx_stage == GS_BOOT_READY &&
			       new_g->boot->first_rx_pid == 0x109c && !new_g->boot->first_rx_deferred);
			cleanup(); cases++;
		}
	/* A later supervisor signal must not replace an already latched RX cause
	 * in the ioctl return, journal or cleanup runtime state.
	 */
	for (unsigned source = 0; source < 2; source++)
		for (unsigned n = 0; n < ARRAY_SIZE(errors); n++) {
			setup(3, 2, true);
			signal_rx_error = errors[n];
			signal_rx_submit = source;
			assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == errors[n]);
			assert(signal_rx_injected && !moved && !new_g && !tx_count &&
			       old_g->boot->core.state == GS_BOOT_FAILED &&
			       old_g->boot->core.error == errors[n] && old_g->rt.error == errors[n] &&
			       old_g->boot->core.failed_stage == GS_BOOT_TRANSITION);
			char terminal[96];
			snprintf(terminal, sizeof(terminal), "native bootstrap finished: %d; failed_stage=1", errors[n]);
			assert(strstr(bootstrap_log, terminal));
			first_rx_diagnostic(errors[n], source ? GSN_RX_SUBMIT : GSN_RX_COMPLETION,
					    GS_BOOT_TRANSITION, 0, false);
			cleanup(); cases++;
		}
	return cases;
}

int main(int argc, char **argv)
{
	struct gsn_boot_status status;
	unsigned cases = 0;
	if (argc == 2) {
		assert(removal_order_cases((unsigned)atoi(argv[1])) == 1);
		return 0;
	}
	cases += removal_order_cases(0);
	cases += removal_safety_cases();
	cases += removal_transport_cases();
	for (unsigned n = 0; n < 4; n++) {
		setup(n + 1, n + 2, n & 1);
		direct_probe = !(n & 1);
		found_foreign = true;
		all_data = n & 1;
		assert(!run(GSN_BOOT_ALLOW_XPAD_HANDOVER));
		assert(tx_count == 15 && new_g && new_g->boot_handoff);
		assert(releases == (n & 1) && attaches == (n & 1));
		assert(!gsn_boot_status(old_g, &status) && status.state == GS_BOOT_HANDED_OFF &&
		       status.imu_seen && status.pad_seen == (n & 1));
		assert(new_g->sequence == 6 && !new_g->rt.owner);
		struct file native_fd = {.private_data = &new_g->misc};
		assert(!gsn_open(NULL, &native_fd));
		u64 deadline = new_g->rt.deadline_ms;
		mutex_lock(&new_g->io_lock);
		assert(!gsn_start(new_g));
		assert(gsn_start(new_g) == -EALREADY);
		mutex_unlock(&new_g->io_lock);
		assert(tx_count == 15 && new_g->sequence == 6 && new_g->rt.deadline_ms == deadline);
		clock_us = new_g->next_heartbeat * 1000;
		gsn_service(&new_g->service.work);
		assert(tx_count == 16 && new_g->sequence == 7);
		gsn_release(NULL, &native_fd);
		cleanup();
		cases++;
	}
	for (int n = 1; n <= 9; n++) {
		setup(1, 2, true);
		scenario = n;
		if (n == 8)
			attach_error = -EIO;
		assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) < 0);
		assert(tx_count == 9 && !new_g);
		assert(releases == (n >= 8) && attaches == (n >= 8));
		assert(!gsn_boot_status(old_g, &status) && status.state == GS_BOOT_FAILED);
		cleanup();
		cases++;
	}
	for (int n = 10; n <= 15; n++) {
		setup(3, 4, true);
		scenario = n;
		int result = run(GSN_BOOT_ALLOW_XPAD_HANDOVER);
		assert((n == 10 || n == 12) ? result == 0 : result < 0);
		assert(tx_count == (n == 15 ? 3u : n == 11 ? 9u : n >= 13 ? 12u : 15u));
		cleanup();
		cases++;
	}
	for (int n = 1; n <= 15; n++)
		for (int short_case = 0; short_case < 2; short_case++) {
			setup(3, 5, true);
			fault_tx = n;
			short_tx = short_case;
			assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) < 0);
			assert(tx_count == (unsigned)n);
			assert(!gsn_boot_status(old_g, &status) && status.state == GS_BOOT_FAILED);
			cleanup();
			cases++;
		}
	setup(2, 3, false);
	no_imu = true;
	assert(run(GSN_BOOT_ALLOW_XPAD_HANDOVER) == -ETIMEDOUT);
	assert(!gsn_boot_status(old_g, &status) && status.failed_stage == GS_BOOT_VERIFY &&
	       !status.imu_seen);
	assert(new_g->stopping && tx_count > 15);
	cleanup();
	cases++;
	setup(2, 3, false);
	assert(run(0) == -EBUSY && !releases && !attaches);
	cleanup();
	cases++;
	for (int n = 0; n < 3; n++) {
		setup(8, 6, false);
		if (n == 0)
			admin = false;
		if (n == 1)
			bootstrap_mode = false;
		if (n == 2)
			enable_output = false;
		assert(run(0) == -EPERM && !tx_count);
		cleanup();
		cases++;
	}
	setup(1, 4, true);
	assert(run(2) == -EINVAL && !tx_count);
	cleanup();
	cases++;
	cases += persistent_cases();
	private_bridge_case();
	cases++;
	cases += failed_boot_end_cases();
	cases += direct_105e_cases();
	printf(
	    "PASS: %u actual-kernel adapter scenarios; captured 15-TX bootstrap, arbitrary "
	    "root/hub ports, handover permission/race, signal/disconnect/deadline/transfer "
	    "failures, parallel reservation isolation, balanced refs, finite/persistent runtime, "
	    "atomic bounded FF, explicit END, one-shot checked PM resume, "
	    "actual-ioctl failed-bootstrap attestation and local END, experimental direct105e/PM/same-instance rejection, "
	    "delayed USB removal/RX completion/resubmit ordering with strict final OUT/deadline/ownership gates, "
	    "immutable first RX cause, narrow post-OUT9 EPIPE/EPROTO wait, logical RX retirement, READY and supervisor-signal fault races\n",
	    cases);
	return 0;
}
