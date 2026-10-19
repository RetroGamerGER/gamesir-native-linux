// SPDX-License-Identifier: GPL-2.0-only
/* Synthetic input hotplug in a private mount namespace; never host devices. */
#define open gs_buttons_open
#define open64 gs_buttons_open64
#include "sdl_evdev_fixture.c"
#undef open
#undef open64

static int motion_readable = 1;
void gs_fixture_set_motion_readable(int readable) { motion_readable = !!readable; }

static const char *fixture_path(const char *path)
{
    if (!strcmp(path, "/dev/input/event0")) return "/fixture/evdev/event0";
    if (!strcmp(path, "/dev/input/event1")) return "/fixture/evdev/event1";
    return path;
}

int open(const char *path, int flags, ...)
{
    mode_t mode = 0;
    if (flags & O_CREAT) {
        va_list ap; va_start(ap, flags); mode = va_arg(ap, unsigned); va_end(ap);
    }
    /* Node existence is controlled exclusively by the test probe. */
    if (strcmp(path, fixture_path(path)) && access(path, F_OK)) return -1;
    if (fixture_kind(fixture_path(path)) == 2 && !motion_readable) { errno = EACCES; return -1; }
    return gs_buttons_open(fixture_path(path), flags, mode);
}

int open64(const char *path, int flags, ...)
{
    mode_t mode = 0;
    if (flags & O_CREAT) {
        va_list ap; va_start(ap, flags); mode = va_arg(ap, unsigned); va_end(ap);
    }
    if (strcmp(path, fixture_path(path)) && access(path, F_OK)) return -1;
    if (fixture_kind(fixture_path(path)) == 2 && !motion_readable) { errno = EACCES; return -1; }
    return gs_buttons_open64(fixture_path(path), flags, mode);
}
