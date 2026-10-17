// SPDX-License-Identifier: GPL-2.0-only
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <libusb-1.0/libusb.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

/* Extended from the project-owned Forza bridge at 3a78390. SDL2 >= 2.24,
 * glibc x86_64 only: SDL3 has a different ABI and is deliberately untouched.
 * No SDL initialization, USB open or input-device open happens in this hook.
 * This is a per-launch adapter, not a security sandbox or general USB guard. */
#if !defined(__GLIBC__) || !defined(__x86_64__)
#error "The experimental SDL2 hook currently requires glibc x86_64"
#endif

typedef int (*rumble_fn)(void *, uint16_t, uint16_t, uint32_t);
typedef void (*close_fn)(void *);
typedef int (*usb_open_fn)(libusb_device *, libusb_device_handle **);
struct sdl_api {
    void *base, *pin;
    rumble_fn rumble;
    close_fn close;
    uint16_t (*vendor)(void *), (*product)(void *);
    int32_t (*instance)(void *);
    const char *(*path)(void *);
};
struct usb_api {
    void *pin;
    usb_open_fn open;
    int (*descriptor)(libusb_device *, struct libusb_device_descriptor *);
    uint8_t (*bus)(libusb_device *), (*address)(libusb_device *);
};
static void *(*lookup)(void *, const char *);
static struct sdl_api sdl;
static struct usb_api usb;
static pthread_once_t once = PTHREAD_ONCE_INIT;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static int active, fatal, transport = -1;
static uint8_t usb_bus, usb_address, session[16];
static char socket_path[sizeof(((struct sockaddr_un *)0)->sun_path)];
static char source_path[64];
static uint64_t sequence;
static void *tracked_joystick;
static int32_t tracked_instance = -1;

static void fork_prepare(void) { pthread_mutex_lock(&lock); }
static void fork_parent(void) { pthread_mutex_unlock(&lock); }
static void fork_child(void)
{
    /* An established producer is never silently transferred to its child. */
    if (transport >= 0) { close(transport); transport = -1; fatal = 1; }
    sequence = 0;
    pthread_mutex_unlock(&lock);
}

static int event_path(const char *path)
{
    const char prefix[] = "/dev/input/event";
    if (!path || strncmp(path, prefix, sizeof(prefix) - 1)) return 0;
    const char *number = path + sizeof(prefix) - 1;
    if (!*number || strlen(path) >= sizeof(source_path)) return 0;
    if (number[0] == '0' && number[1]) return 0;
    for (; *number; number++) if (*number < '0' || *number > '9') return 0;
    return 1;
}

static int decimal(const char *text, unsigned int maximum, uint8_t *out)
{
    unsigned int value = 0;
    if (!text || !*text || *text == '0') return 0;
    for (; *text; text++) {
        if (*text < '0' || *text > '9') return 0;
        value = value * 10 + (unsigned int)(*text - '0');
        if (value > maximum) return 0;
    }
    *out = (uint8_t)value;
    return 1;
}

static int hex_digit(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

static void initialize(void)
{
    lookup = (void *(*)(void *, const char *))dlvsym(RTLD_NEXT, "dlsym", "GLIBC_2.2.5");
    const char *path = getenv("GSN_TRIGGER_SOCKET");
    const char *source = getenv("GSN_TRIGGER_SOURCE");
    const char *token = getenv("GSN_TRIGGER_SESSION");
    if (!lookup || !path || !*path || strlen(path) >= sizeof(socket_path) ||
        !event_path(source) || !token || strlen(token) != 32 ||
        !decimal(getenv("GSN_TRIGGER_USB_BUS"), 255, &usb_bus) ||
        !decimal(getenv("GSN_TRIGGER_USB_ADDRESS"), 127, &usb_address)) return;
    unsigned int nonzero = 0;
    for (size_t i = 0; i < sizeof(session); i++) {
        int a = hex_digit(token[2 * i]), b = hex_digit(token[2 * i + 1]);
        if (a < 0 || b < 0) return;
        session[i] = (uint8_t)((a << 4) | b);
        nonzero |= session[i];
    }
    if (!nonzero || pthread_atfork(fork_prepare, fork_parent, fork_child)) return;
    strcpy(socket_path, path);
    strcpy(source_path, source);
    active = 1;
}

static int library(void *symbol, const char *prefix, Dl_info *info)
{
    if (!symbol || !dladdr(symbol, info) || !info->dli_fname) return 0;
    const char *base = strrchr(info->dli_fname, '/');
    base = base ? base + 1 : info->dli_fname;
    return !strncmp(base, prefix, strlen(prefix));
}

static int same_library(void *symbol, void *base)
{
    Dl_info info;
    return symbol && dladdr(symbol, &info) && info.dli_fbase == base;
}

static void write16(uint8_t *p, uint16_t value)
{ p[0] = (uint8_t)value; p[1] = (uint8_t)(value >> 8); }
static void write32(uint8_t *p, uint32_t value)
{ for (size_t i = 0; i < 4; i++) p[i] = (uint8_t)(value >> (8 * i)); }
static void write64(uint8_t *p, uint64_t value)
{ for (size_t i = 0; i < 8; i++) p[i] = (uint8_t)(value >> (8 * i)); }

static int eligible(void *joystick, int32_t *instance)
{
    const char *path = sdl.path(joystick);
    *instance = sdl.instance(joystick);
    return sdl.vendor(joystick) == 0x3537 && sdl.product(joystick) == 0x109c &&
           event_path(path) && !strcmp(path, source_path) && *instance >= 0;
}

static int send_effect(void *joystick, uint16_t left, uint16_t right,
                       uint32_t duration, uint16_t type, int32_t instance)
{
    struct sockaddr_un address = {.sun_family = AF_UNIX};
    struct timespec now;
    uint8_t packet[128] = {0};
    int result = -1;
    pthread_mutex_lock(&lock);
    if (tracked_joystick && tracked_joystick != joystick) goto done;
    if (fatal || sequence == UINT64_MAX || clock_gettime(CLOCK_MONOTONIC, &now)) goto fail;
    if (!tracked_joystick) { tracked_joystick = joystick; tracked_instance = instance; }
    if (tracked_instance != instance) goto fail;
    memcpy(packet, "GST2", 4);
    write16(packet + 4, 2);
    write16(packet + 6, type);
    write32(packet + 8, sizeof(packet));
    write64(packet + 16, ++sequence);
    write64(packet + 24, (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec);
    write32(packet + 32, (uint32_t)getpid());
    write32(packet + 36, (uint32_t)tracked_instance);
    write16(packet + 40, left);
    write16(packet + 42, right);
    write32(packet + 44, duration);
    memcpy(packet + 48, source_path, strlen(source_path));
    memcpy(packet + 112, session, sizeof(session));
    if (transport < 0) {
        transport = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
        if (transport < 0) goto fail;
        strcpy(address.sun_path, socket_path);
        if (connect(transport, (struct sockaddr *)&address, sizeof(address))) goto fail;
    }
    /* One bounded nonblocking send: no input-thread waiting or hidden retries.
     * A partial write/overload closes the lease instead of resending effects. */
    if (send(transport, packet, sizeof(packet), MSG_NOSIGNAL | MSG_DONTWAIT) != sizeof(packet)) goto fail;
    result = 0;
    if (type == 2) { fatal = 1; close(transport); transport = -1; }
    goto done;
fail:
    fatal = 1;
    if (transport >= 0) close(transport);
    transport = -1;
done:
    pthread_mutex_unlock(&lock);
    return result;
}

static int trigger_rumble(void *joystick, uint16_t left, uint16_t right, uint32_t duration)
{
    int32_t instance;
    if (eligible(joystick, &instance)) return send_effect(joystick, left, right, duration, 1, instance);
    pthread_mutex_lock(&lock);
    int tracked = tracked_joystick == joystick;
    if (tracked) {
        /* SDL can invalidate its identity before Close is called. End the
         * producer lease instead of falling back to a competing output path. */
        fatal = 1;
        if (transport >= 0) close(transport);
        transport = -1;
    }
    pthread_mutex_unlock(&lock);
    if (tracked) return -1;
    return sdl.rumble(joystick, left, right, duration);
}

static void joystick_close(void *joystick)
{
    pthread_mutex_lock(&lock);
    int tracked = tracked_joystick == joystick;
    int32_t instance = tracked_instance;
    pthread_mutex_unlock(&lock);
    if (tracked) (void)send_effect(joystick, 0, 0, 0, 2, instance);
    sdl.close(joystick);
}

static int install_sdl(void *handle, const Dl_info *info)
{
    struct sdl_api api = {.base = info->dli_fbase};
    if (sdl.base) return sdl.base == info->dli_fbase;
    api.rumble = (rumble_fn)lookup(handle, "SDL_JoystickRumbleTriggers");
    api.close = (close_fn)lookup(handle, "SDL_JoystickClose");
    api.vendor = (uint16_t (*)(void *))lookup(handle, "SDL_JoystickGetVendor");
    api.product = (uint16_t (*)(void *))lookup(handle, "SDL_JoystickGetProduct");
    api.instance = (int32_t (*)(void *))lookup(handle, "SDL_JoystickInstanceID");
    api.path = (const char *(*)(void *))lookup(handle, "SDL_JoystickPath");
    if (!same_library((void *)api.rumble, api.base) || !same_library((void *)api.close, api.base) ||
        !same_library((void *)api.vendor, api.base) || !same_library((void *)api.product, api.base) ||
        !same_library((void *)api.instance, api.base) || !same_library((void *)api.path, api.base)) return 0;
    /* Hold the selected library for this process, so dlclose cannot leave stale
     * callbacks. Other SDL copies retain their own original function pointers. */
    api.pin = dlopen(info->dli_fname, RTLD_NOW | RTLD_NOLOAD);
    if (!api.pin) return 0;
    sdl = api;
    return 1;
}

static int install_usb(void *handle, void *original)
{
    Dl_info info;
    struct usb_api api = {0};
    if (usb.open) return (void *)usb.open == original;
    if (!library(original, "libusb-1.0.so", &info)) return 0;
    api.open = (usb_open_fn)original;
    api.descriptor = (int (*)(libusb_device *, struct libusb_device_descriptor *))lookup(handle, "libusb_get_device_descriptor");
    api.bus = (uint8_t (*)(libusb_device *))lookup(handle, "libusb_get_bus_number");
    api.address = (uint8_t (*)(libusb_device *))lookup(handle, "libusb_get_device_address");
    if (!same_library((void *)api.descriptor, info.dli_fbase) ||
        !same_library((void *)api.bus, info.dli_fbase) ||
        !same_library((void *)api.address, info.dli_fbase)) return 0;
    api.pin = dlopen(info.dli_fname, RTLD_NOW | RTLD_NOLOAD);
    if (!api.pin) return 0;
    usb = api;
    return 1;
}

int libusb_open(libusb_device *device, libusb_device_handle **handle)
{
    struct libusb_device_descriptor descriptor;
    usb_open_fn original;
    pthread_once(&once, initialize);
    pthread_mutex_lock(&lock);
    if (!usb.open && lookup) (void)install_usb(RTLD_NEXT, lookup(RTLD_NEXT, "libusb_open"));
    original = usb.open;
    pthread_mutex_unlock(&lock);
    if (!original) return LIBUSB_ERROR_OTHER;
    if (active && usb.bus(device) == usb_bus && usb.address(device) == usb_address &&
        !usb.descriptor(device, &descriptor) && descriptor.idVendor == 0x3537 && descriptor.idProduct == 0x109c) {
        if (handle) *handle = NULL;
        return LIBUSB_ERROR_ACCESS;
    }
    return original(device, handle);
}

void *dlsym(void *handle, const char *name)
{
    Dl_info info;
    void *result;
    pthread_once(&once, initialize);
    if (!lookup) return NULL;
    result = lookup(handle, name);
    if (!active || !result) return result;
    if (!strcmp(name, "libusb_open")) {
        pthread_mutex_lock(&lock);
        int installed = install_usb(handle, result);
        pthread_mutex_unlock(&lock);
        return installed ? (void *)libusb_open : result;
    }
    if (strcmp(name, "SDL_JoystickRumbleTriggers") && strcmp(name, "SDL_JoystickClose")) return result;
    if (!library(result, "libSDL2-", &info)) return result;
    pthread_mutex_lock(&lock);
    int installed = install_sdl(handle, &info);
    pthread_mutex_unlock(&lock);
    if (!installed) return result;
    return !strcmp(name, "SDL_JoystickClose") ? (void *)joystick_close : (void *)trigger_rumble;
}
