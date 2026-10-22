// SPDX-License-Identifier: GPL-2.0-only
/* Reuse the reviewed sensor syscall fixture; add synthetic button/FF events.
 * Only run in the audited device-free Bubblewrap namespace. */
#define open gs_base_open
#define open64 gs_base_open64
#define ioctl gs_base_ioctl
#define read gs_base_read
#include "sdl_evdev_fixture.c"
#undef open
#undef open64
#undef ioctl
#undef read

static struct input_event queue[512];
static _Atomic unsigned queue_length, queue_position;
static unsigned char pressed[KEY_MAX / 8 + 1];
static unsigned ff_uploads, ff_plays;

static int alpha(void) { return strstr(scenario(), "alpha17") != NULL || (!strcmp(scenario(), "observed-gyro") || !strcmp(scenario(), "experimental-six-axis")); }
static int xpad(void) { return strstr(scenario(), "xpad11") != NULL; }
/* Replay only captured input metadata, never actual USB/evdev traffic. */
static int zzz(void) { return getenv("GS_VARIANT") && !strcmp(getenv("GS_VARIANT"), "105e"); }
int open(const char *p, int flags, ...)
{
    mode_t mode = 0;
    if (flags & O_CREAT) { va_list ap; va_start(ap, flags); mode = va_arg(ap, unsigned); va_end(ap); }
    if (fixture_kind(p) == 1) flags = (flags & ~O_ACCMODE) | O_RDONLY;
    return gs_base_open(p, flags, mode);
}
int open64(const char *p, int flags, ...)
{
    mode_t mode = 0;
    if (flags & O_CREAT) { va_list ap; va_start(ap, flags); mode = va_arg(ap, unsigned); va_end(ap); }
    if (fixture_kind(p) == 1) flags = (flags & ~O_ACCMODE) | O_RDONLY;
    return gs_base_open64(p, flags, mode);
}
int ioctl(int fd, unsigned long req, ...)
{
    va_list ap; va_start(ap, req); void *arg = va_arg(ap, void *); va_end(ap);
    int k = fd >= 0 && fd < FD_LIMIT ? kinds[fd] : 0;
    unsigned n = _IOC_NR(req), size = _IOC_SIZE(req);
    if ((k == 1 || k == 2) && _IOC_TYPE(req) == 'E' && n == 0x02) {
        /* Both halves of a synthetic pair keep the real variant identity. */
        *(struct input_id *)arg = (struct input_id){BUS_USB, 0x3537,
            zzz() ? 0x105e : 0x109c, zzz() ? 0x0607 : 1};
        return 0;
    }
    if (k == 1 && _IOC_TYPE(req) == 'E') {
        if (n == 0x06) { snprintf(arg, size, "%s", xpad() ? "Generic X-Box pad" : "GameSir G7 Pro"); return (int)strlen(arg) + 1; }
        if (n == 0x18) { memset(arg, 0, size); memcpy(arg, pressed, size < sizeof(pressed) ? size : sizeof(pressed)); return (int)size; }
        if (n == 0x20 + EV_FF) {
            memset(arg, 0, size); bit(arg, size, FF_RUMBLE);
            if (zzz()) {
                const unsigned effects[] = {FF_PERIODIC, FF_SQUARE, FF_TRIANGLE, FF_SINE, FF_GAIN};
                for (unsigned i = 0; i < sizeof(effects)/sizeof(*effects); i++) bit(arg, size, effects[i]);
            }
            return (int)size;
        }
        if (n == 0x80) { struct ff_effect *e = arg; if (e->type != FF_RUMBLE) { errno = EINVAL; return -1; } e->id = 1; ff_uploads++; return 0; }
        if (n == 0x81) return 0;
        if (n == 0x84) { *(int *)arg = 16; return 0; }
    }
    int result = gs_base_ioctl(fd, req, arg);
    if (result >= 0 && k == 1 && _IOC_TYPE(req) == 'E') {
        if (n == 0x20) bit(arg, size, EV_FF);
        if (n == 0x20 + EV_KEY && !xpad()) {
            for (unsigned code = 704; code <= (alpha() ? 708u : 707u); code++) bit(arg, size, code);
            if (alpha()) bit(arg, size, KEY_RECORD);
        }
        if (n == 0x40 + ABS_Z || n == 0x40 + ABS_RZ) {
            ((struct input_absinfo *)arg)->minimum = 0;
            ((struct input_absinfo *)arg)->maximum = 1023;
        }
    }
    return result;
}
static void push_frame(unsigned type, const unsigned *codes, const int *values, unsigned count)
{
    if (queue_length + count + 1 > 512) abort();
    unsigned index = queue_length;
    struct timespec now; clock_gettime(CLOCK_MONOTONIC, &now);
    for (unsigned i = 0; i < count; i++) {
        unsigned code = codes[i];
        if ((type == EV_KEY && code > KEY_MAX) || (type == EV_ABS && code > ABS_MAX)) abort();
        queue[index + i] = (struct input_event){ .type = type, .code = code, .value = values[i] };
        if (type == EV_KEY) {
            if (values[i]) pressed[code / 8] |= 1u << (code % 8);
            else pressed[code / 8] &= ~(1u << (code % 8));
        }
    }
    queue[index + count] = (struct input_event){ .type = EV_SYN, .code = SYN_REPORT };
    for (unsigned i = index; i <= index + count; i++) {
        queue[i].input_event_sec = now.tv_sec;
        queue[i].input_event_usec = now.tv_nsec / 1000;
    }
    queue_length = index + count + 1;
}
void gs_fixture_push_key(unsigned code, int down) { push_frame(EV_KEY, &code, &down, 1); }
void gs_fixture_push_keys(const unsigned *codes, const int *values, unsigned count)
{ push_frame(EV_KEY, codes, values, count); }
void gs_fixture_push_abs(const unsigned *codes, const int *values, unsigned count)
{ push_frame(EV_ABS, codes, values, count); }
ssize_t read(int fd, void *buf, size_t size)
{
    int k = fd >= 0 && fd < FD_LIMIT ? kinds[fd] : 0;
    if (k != 1) return gs_base_read(fd, buf, size);
    reads[1]++;
    unsigned available = queue_length - queue_position;
    if (!available) { errno = EAGAIN; return -1; }
    if (size < sizeof(struct input_event)) { errno = EINVAL; return -1; }
    unsigned count = size / sizeof(struct input_event);
    if (count > available) count = available;
    memcpy(buf, queue + queue_position, count * sizeof(struct input_event));
    queue_position += count;
    return count * sizeof(struct input_event);
}
ssize_t write(int fd, const void *buf, size_t size)
{
    int k = fd >= 0 && fd < FD_LIMIT ? kinds[fd] : 0;
    if (k == 1) {
        const struct input_event *e = buf;
        if (size != sizeof(*e) || e->type != EV_FF) { errno = EINVAL; return -1; }
        ff_plays++;
        return size;
    }
    static ssize_t (*real_write)(int, const void *, size_t);
    if (!real_write) real_write = dlsym(RTLD_NEXT, "write");
    return real_write(fd, buf, size);
}
unsigned gs_fixture_ff_uploads(void) { return ff_uploads; }
unsigned gs_fixture_ff_plays(void) { return ff_plays; }
