// SPDX-License-Identifier: GPL-2.0-only
/* Synthetic syscall fixture, never a hardware recorder or uinput device.
 * Run ONLY via run_sdl_sensor_test.py in its device-free mount namespace.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <time.h>
#include <unistd.h>

#define FD_LIMIT 4096
static _Atomic int kinds[FD_LIMIT];
static _Atomic int sent[FD_LIMIT];
static _Atomic unsigned opens[4], reads[4], requests[4], writes_blocked;
static int fixture_kind(const char *p)
{
    if (!strcmp(p, "/fixture/evdev/event0")) return 1;
    if (!strcmp(p, "/fixture/evdev/event1")) return 2;
    if (!strcmp(p, "/dev/iio:device0")) return 3;
    return 0;
}

static int do_open(const char *p, int flags, mode_t mode)
{
    static int (*real_open)(const char *, int, ...);
    if (!real_open) real_open = dlsym(RTLD_NEXT, "open");
    int k = fixture_kind(p);
    if (k && (flags & O_ACCMODE) != O_RDONLY) {
        /* SDL tries RW first for force feedback; this fixture has no output. */
        writes_blocked++;
        errno = EACCES;
        return -1;
    }
    int fd = real_open(p, flags, mode);
    if (fd >= 0 && fd < FD_LIMIT && k) {
        kinds[fd] = k;
        sent[fd] = 0;
        opens[k]++;
    }
    return fd;
}

int open(const char *p, int flags, ...)
{
    mode_t mode = 0;
    if (flags & O_CREAT) {
        va_list ap; va_start(ap, flags); mode = va_arg(ap, unsigned); va_end(ap);
    }
    return do_open(p, flags, mode);
}
int open64(const char *p, int flags, ...)
{
    mode_t mode = 0;
    if (flags & O_CREAT) {
        va_list ap; va_start(ap, flags); mode = va_arg(ap, unsigned); va_end(ap);
    }
    return do_open(p, flags, mode);
}
int close(int fd)
{
    static int (*real_close)(int);
    if (!real_close) real_close = dlsym(RTLD_NEXT, "close");
    if (fd >= 0 && fd < FD_LIMIT) { kinds[fd] = 0; sent[fd] = 0; }
    return real_close(fd);
}
int fstat(int fd, struct stat *s)
{
    static int (*real_fstat)(int, struct stat *);
    if (!real_fstat) real_fstat = dlsym(RTLD_NEXT, "fstat");
    int r = real_fstat(fd, s);
    if (!r && fd >= 0 && fd < FD_LIMIT && kinds[fd])
        s->st_rdev = makedev(240, kinds[fd]);
    return r;
}
int fstat64(int fd, struct stat64 *s)
{
    static int (*real_fstat)(int, struct stat64 *);
    if (!real_fstat) real_fstat = dlsym(RTLD_NEXT, "fstat64");
    int r = real_fstat(fd, s);
    if (!r && fd >= 0 && fd < FD_LIMIT && kinds[fd])
        s->st_rdev = makedev(240, kinds[fd]);
    return r;
}
static void bit(void *buf, size_t size, unsigned n)
{
    if (n / 8 < size) ((unsigned char *)buf)[n / 8] |= 1u << (n % 8);
}
static const char *scenario(void) { return getenv("GS_SCENARIO"); }
static int raw(unsigned axis)
{
    const char *s = getenv("GS_RAW");
    int v[6] = {1000, -2000, 3000, 4000, -5000, 6000};
    if (s) (void)sscanf(s, "%d,%d,%d,%d,%d,%d", v, v+1, v+2, v+3, v+4, v+5);
    return axis < 6 ? v[axis] : 0;
}

int ioctl(int fd, unsigned long req, ...)
{
    va_list ap; va_start(ap, req); void *arg = va_arg(ap, void *); va_end(ap);
    int k = (fd >= 0 && fd < FD_LIMIT) ? kinds[fd] : 0;
    if (!k) {
        static int (*real_ioctl)(int, unsigned long, ...);
        if (!real_ioctl) real_ioctl = dlsym(RTLD_NEXT, "ioctl");
        return real_ioctl(fd, req, arg);
    }
    requests[k]++;
    unsigned n = _IOC_NR(req), size = _IOC_SIZE(req);
    if (_IOC_TYPE(req) != 'E' || k == 3) { errno = ENOTTY; return -1; }
    if (n == 0x01) { *(int *)arg = EV_VERSION; return 0; }
    if (n == 0x02) {
        *(struct input_id *)arg = (struct input_id){BUS_USB, 0x3537, 0x109c, 1};
        return 0;
    }
    if (n == 0x06 || n == 0x07 || n == 0x08) {
        const char *value = n == 0x06 ? (k == 1 ? "GameSir G7 Pro Offline Fixture" : "GameSir G7 Pro Motion Fixture") :
            n == 0x07 ? "offline-fixture/input0" :
            k == 2 && !strcmp(scenario(), "wrong-uniq") ? "offline-other-port" : "offline-g7pro-port8-6";
        snprintf(arg, size, "%s", value);
        return (int)strlen(arg) + 1;
    }
    if (n == 0x09) {
        memset(arg, 0, size);
        if (k == 2) bit(arg, size, INPUT_PROP_ACCELEROMETER);
        return (int)size;
    }
    if (n >= 0x20 && n < 0x40) {
        memset(arg, 0, size);
        switch (n - 0x20) {
        case 0:
            bit(arg, size, EV_SYN); bit(arg, size, EV_ABS);
            bit(arg, size, k == 1 ? EV_KEY : EV_MSC);
            break;
        case EV_KEY:
            if (k == 1) {
                unsigned b[] = {BTN_A, BTN_B, BTN_X, BTN_Y, BTN_TL, BTN_TR,
                    BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL, BTN_THUMBR};
                for (unsigned i = 0; i < sizeof(b)/sizeof(*b); i++) bit(arg, size, b[i]);
            }
            break;
        case EV_ABS:
            for (unsigned i = 0; i < 6; i++) {
                if (k == 2 && i == ABS_RZ && !strcmp(scenario(), "missing-rz")) continue;
                bit(arg, size, i);
            }
            if (k == 1) { bit(arg, size, ABS_HAT0X); bit(arg, size, ABS_HAT0Y); }
            break;
        case EV_MSC: if (k == 2) bit(arg, size, MSC_TIMESTAMP); break;
        }
        return (int)size;
    }
    if (n >= 0x40 && n < 0x80) {
        unsigned axis = n - 0x40;
        struct input_absinfo a = {.minimum = -32768, .maximum = 32767};
        if (k == 1 && axis >= ABS_HAT0X) { a.minimum = -1; a.maximum = 1; }
        if (k == 2) {
            a.value = raw(axis);
            /* Synthetic scale, explicitly NOT a measured G7 Pro calibration. */
            const char *res = getenv(axis < 3 ? "GS_ACCEL_RES" : "GS_GYRO_RES");
            a.resolution = !strcmp(scenario(), "zero-resolution") ? 0 : res ? atoi(res) : axis < 3 ? 8192 : 16;
        }
        *(struct input_absinfo *)arg = a;
        return 0;
    }
    if (n == 0x18) { memset(arg, 0, size); return (int)size; }
    if (n == 0xa0) return 0; /* EVIOCSCLOCKID affects fixture only. */
    errno = ENOTTY; return -1;
}

ssize_t read(int fd, void *buf, size_t size)
{
    int k = (fd >= 0 && fd < FD_LIMIT) ? kinds[fd] : 0;
    if (!k) {
        static ssize_t (*real_read)(int, void *, size_t);
        if (!real_read) real_read = dlsym(RTLD_NEXT, "read");
        return real_read(fd, buf, size);
    }
    reads[k]++;
    if (k != 2 || sent[fd]) { errno = EAGAIN; return -1; }
    struct input_event e[8] = {0};
    struct timespec now; clock_gettime(CLOCK_MONOTONIC, &now);
    for (unsigned i = 0; i < 8; i++) {
        e[i].input_event_sec = now.tv_sec;
        e[i].input_event_usec = now.tv_nsec / 1000;
    }
    for (unsigned i = 0; i < 6; i++) {
        if (i == ABS_RZ && !strcmp(scenario(), "missing-rz")) continue;
        e[i].type = EV_ABS; e[i].code = i; e[i].value = raw(i);
    }
    e[6].type = EV_MSC; e[6].code = MSC_TIMESTAMP; e[6].value = 16000;
    e[7].type = EV_SYN; e[7].code = SYN_REPORT;
    if (size < sizeof(e)) { errno = EINVAL; return -1; }
    memcpy(buf, e, sizeof(e)); sent[fd] = 1;
    return sizeof(e);
}

void gs_fixture_stats(void)
{
    fprintf(stderr, "fixture: pad opens=%u ioctls=%u reads=%u; sensor opens=%u ioctls=%u reads=%u; iio opens=%u; RW opens denied=%u\n",
        opens[1], requests[1], reads[1], opens[2], requests[2], reads[2], opens[3], writes_blocked);
}
