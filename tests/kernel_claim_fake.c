// SPDX-License-Identifier: GPL-2.0-only
/* Actual driver claim functions, with no device nodes or real USB operations. */
#include "../src/gs_startup.h"
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
typedef uint64_t u64;
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define CAP_SYS_ADMIN 1
#define ERESTARTSYS 512
#define READ_ONCE(a) (a)
#define USB_STATE_CONFIGURED 1
#define USB_INTERFACE_BOUND 1
#define USB_INTERFACE_BINDING 2
#define le16_to_cpu(a) (a)
struct task_struct { int id; } owner_task, foreign_task;
static struct task_struct *current = &owner_task;
struct mutex { bool held; };
typedef struct mutex spinlock_t;
static struct mutex claim_lock;
static spinlock_t claim_gate_lock;
static bool lock_interrupted, admin, persistent_mode, bootstrap_mode, enable_output;
static struct gsn_claim *pending_claim;
static int mutex_lock_interruptible(struct mutex *lock)
{
	if (lock_interrupted)
		return 1;
	assert(!lock->held);
	lock->held = true;
	return 0;
}
static void mutex_unlock(struct mutex *lock) { assert(lock->held); lock->held = false; }
#define spin_lock_irqsave(lock, flags) do { (flags) = 0; assert(!(lock)->held); (lock)->held = true; } while (0)
#define spin_unlock_irqrestore(lock, flags) do { (void)(flags); assert((lock)->held); (lock)->held = false; } while (0)
struct kernfs_node { u64 id; } device_node, parent_node;
struct device_driver { int unused; };
struct device {
	struct device_driver *driver;
	struct { struct kernfs_node *sd; } kobj;
	bool registered;
	const char *name;
};
struct usb_driver { struct device_driver driver; } gsn_driver;
struct device_driver xpad;
struct usb_bus { unsigned busnum; } bus;
struct usb_endpoint_descriptor {
	unsigned bEndpointAddress, bmAttributes, wMaxPacketSize, bInterval;
};
struct usb_host_interface {
	struct { unsigned bInterfaceNumber, bAlternateSetting, bInterfaceClass,
		bInterfaceSubClass, bInterfaceProtocol, bNumEndpoints; } desc;
	struct { struct usb_endpoint_descriptor desc; } endpoint[2];
} alt;
struct usb_host_config { struct { unsigned bConfigurationValue; } desc; } config;
struct usb_interface;
struct usb_device {
	struct usb_device *parent;
	struct usb_bus *bus;
	unsigned devnum, state;
	struct { unsigned idVendor, idProduct; } descriptor;
	struct usb_host_config *actconfig;
	struct device dev;
	bool locked;
} root_usb, target_usb;
struct usb_interface {
	struct usb_device *udev;
	struct usb_host_interface *cur_altsetting;
	struct device dev;
	unsigned refs, condition;
	bool authorized;
} target_intf, foreign_intf;
#define interface_to_usbdev(i) ((i)->udev)
#define usb_endpoint_type(e) ((e)->bmAttributes & 3)
#define usb_endpoint_maxp(e) ((e)->wMaxPacketSize)
#define usb_endpoint_is_int_in(e) (usb_endpoint_type(e) == 3 && ((e)->bEndpointAddress & 128))
#define usb_endpoint_is_int_out(e) (usb_endpoint_type(e) == 3 && !((e)->bEndpointAddress & 128))
#define device_is_registered(d) ((d)->registered)
#define dev_name(d) ((d)->name)
#define kernfs_ino(n) ((n)->id)
static bool capable(unsigned capability) { return admin; }
static int kstrtou64(const char *value, int base, u64 *number)
{
	char *end;
	errno = 0;
	*number = strtoull(value, &end, base);
	return errno || *end ? -EINVAL : 0;
}
static void usb_lock_device(struct usb_device *device) { assert(!device->locked); device->locked = true; }
static void usb_unlock_device(struct usb_device *device) { assert(device->locked); device->locked = false; }
static struct usb_interface *usb_ifnum_to_if(struct usb_device *device, unsigned number)
{
	assert(device->locked && device == &target_usb && number == 0);
	return &target_intf;
}
static struct usb_interface *usb_get_intf(struct usb_interface *intf) { intf->refs++; return intf; }
static void usb_put_intf(struct usb_interface *intf) { assert(intf->refs > 1); intf->refs--; }
static unsigned enumerations, attaches, requested_pid;
static int mutation;
static int usb_for_each_dev(void *data, int (*callback)(struct usb_device *, void *))
{
	enumerations++;
	assert(!callback(&root_usb, data));
	return callback(&target_usb, data);
}
static int device_driver_attach(const struct device_driver *, struct device *);
#include "kernel-claim-functions.h"

static int device_driver_attach(const struct device_driver *driver, struct device *device)
{
	assert(driver == &gsn_driver.driver && device == &target_intf.dev && pending_claim);
	attaches++;
	/* A concurrent automatic probe cannot consume this synchronous authorization. */
	current = &foreign_task;
	assert(!gsn_claim_consume(&target_intf));
	current = &owner_task;
	assert(!gsn_claim_consume(&foreign_intf));
	assert(!pending_claim->consumed);
	if (mutation == 1) device_node.id++;
	if (mutation == 2) parent_node.id++;
	if (mutation == 3) target_usb.state = 0;
	if (mutation == 4) target_intf.dev.driver = &xpad;
	if (mutation == 5) return -ENOMEM;
	if (mutation == 6) return 0; /* A core return without our probe is not success. */
	if (mutation == 7) target_usb.descriptor.idProduct = 0x109c;
	if (mutation == 8) target_usb.devnum++;
	if (mutation == 9) target_intf.dev.name = "4-3.2:1.0";
	if (device->driver)
		return -EBUSY;
	usb_lock_device(&target_usb);
	bool accepted = gsn_claim_consume(&target_intf);
	assert(!gsn_claim_consume(&target_intf)); /* One probe, including failure. */
	usb_unlock_device(&target_usb);
	if (!accepted)
		return -ENODEV;
	device->driver = &gsn_driver.driver;
	return 0;
}

static void reset(void)
{
	assert(!pending_claim && !claim_lock.held && !claim_gate_lock.held);
	admin = persistent_mode = bootstrap_mode = enable_output = true;
	lock_interrupted = false;
	mutation = 0;
	enumerations = attaches = 0;
	requested_pid = 0x100a;
	device_node.id = 10001;
	parent_node.id = 20002;
	bus.busnum = 4;
	root_usb = (struct usb_device){.bus = &bus, .state = 1,
		.dev = {.registered = true, .kobj.sd = &parent_node}};
	target_usb = (struct usb_device){.parent = &root_usb, .bus = &bus, .devnum = 42,
		.state = 1, .descriptor = {0x3537, 0x100a}, .actconfig = &config,
		.dev = {.registered = true, .kobj.sd = &device_node}};
	alt = (struct usb_host_interface){.desc = {0, 0, 0xff, 0x5d, 1, 2},
		.endpoint = {{{0x82, 3, 32, 1}}, {{2, 3, 32, 1}}}};
	config.desc.bConfigurationValue = 1;
	target_intf = (struct usb_interface){.udev = &target_usb, .cur_altsetting = &alt,
		.dev = {.registered = true, .name = "4-3.1:1.0"}, .refs = 1, .authorized = true};
	foreign_intf = target_intf;
}

static const char valid[] = "1 4-3.1:1.0 4 42 10001 20002\n";
static ssize_t run(const char *request)
{
	ssize_t result = requested_pid == 0x105e ?
		claim_105e_store(&gsn_driver.driver, request, strlen(request)) :
		claim_100a_store(&gsn_driver.driver, request, strlen(request));
	assert(!pending_claim && !claim_lock.held && !claim_gate_lock.held);
	assert(target_intf.refs == 1 && !target_usb.locked);
	assert(!gsn_claim_consume(&target_intf)); /* No reusable right after return. */
	return result;
}

int main(void)
{
	unsigned cases = 0;
	reset();
	assert(!gsn_claim_consume(&target_intf)); /* Registration, hotplug, generic bind. */
	assert(run(valid) == (ssize_t)strlen(valid) && attaches == 1);
	assert(target_intf.dev.driver == &gsn_driver.driver);
	assert(run(valid) == -ENODEV && attaches == 1); /* Already bound, no takeover. */
	cases++;
	for (int n = 1; n <= 9; n++) {
		reset(); mutation = n;
		assert(run(valid) < 0 && attaches == 1);
		cases++;
	}
	const char *invalid[] = {"", "2 4-3.1:1.0 4 42 10001 20002", "1 x 0 42 1 1",
		"1 x 65536 42 1 1", "1 x 4 128 1 1", "1 x 4 0 1 1", "1 x 4 42 0 1",
		"1 x 4 42 1 0", "1 x 4 42 -1 1", "1 x 4 42 +1 1", "1 x 4 42 0x1 1",
		"1 x 4 42 18446744073709551616 1", "1 x 4 42 1", "1 x 4 42 1 1 extra",
		"1  x 4 42 1 1", "1 x 4 42 1 1 ", "1 x 4 42 1 1\n\n"};
	for (unsigned n = 0; n < ARRAY_SIZE(invalid); n++) {
		reset(); assert(run(invalid[n]) == -EINVAL && !enumerations && !attaches); cases++;
	}
	for (int n = 0; n < 14; n++) {
		reset();
		if (n == 0) admin = false;
		if (n == 1) persistent_mode = false;
		if (n == 2) bootstrap_mode = false;
		if (n == 3) enable_output = false;
		if (n == 4) lock_interrupted = true;
		if (n == 5) target_usb.devnum++;
		if (n == 6) bus.busnum++;
		if (n == 7) device_node.id++;
		if (n == 8) parent_node.id++;
		if (n == 9) target_intf.dev.driver = &xpad;
		if (n == 10) target_intf.authorized = false;
		if (n == 11) alt.endpoint[0].desc.wMaxPacketSize = 64;
		if (n == 12) target_usb.dev.registered = false;
		if (n == 13) target_intf.dev.name = "4-3.1:1.1";
		assert(run(valid) < 0 && !attaches);
		cases++;
	}
	reset();
	assert(claim_100a_store(&gsn_driver.driver, valid, sizeof(valid)) == -EINVAL);
	assert(!enumerations); cases++;
	/* Same shared gate, PID pinned by its attribute; no cross-edition takeover. */
	for (unsigned int wrong = 0; wrong < 12; wrong++) {
		reset();
		target_usb.descriptor.idProduct = 0x105e;
		alt.desc.bInterfaceSubClass = 0x47;
		alt.desc.bInterfaceProtocol = 0xd0;
		alt.endpoint[0].desc.wMaxPacketSize = alt.endpoint[1].desc.wMaxPacketSize = 64;
		alt.endpoint[0].desc.bInterval = 2; alt.endpoint[1].desc.bInterval = 4;
		requested_pid = 0x105e;
		if (wrong == 1) requested_pid = 0x100a;
		if (wrong == 2) target_usb.descriptor.idProduct = 0x109c;
		if (wrong >= 3) mutation = wrong - 2;
		assert(wrong ? run(valid) < 0 : run(valid) == (ssize_t)strlen(valid));
		assert(attaches == (wrong == 1 || wrong == 2 ? 0u : 1u));
		cases++;
	}
	printf("PASS: %u actual-kernel claim scenarios; exact instance/inodes, auto/manual gate, "
		"concurrent task, single consume, malformed input, disconnect/replacement/attach failure, "
		"balanced refs and no surviving permission\n", cases);
	return 0;
}
