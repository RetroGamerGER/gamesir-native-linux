// SPDX-License-Identifier: GPL-2.0-only
/* Run only with run_sdl_hotplug_test.py: all event nodes are regular files. */
#define _GNU_SOURCE
#include <SDL3/SDL.h>
#include <assert.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static void node(unsigned number, bool add)
{
    char path[64];
    snprintf(path, sizeof(path), "/dev/input/event%u", number);
    if (add) {
        /* fopen uses a real regular file, not the fixture's open wrapper. */
        FILE *file = fopen(path, "w");
        assert(file); fclose(file);
    } else {
        assert(!unlink(path));
    }
}

static void pump(void)
{
    /* Bounded event pumping, not a proposed production startup delay. */
    for (unsigned i = 0; i < 6; i++) { SDL_PumpEvents(); SDL_Delay(10); }
}

static SDL_Gamepad *open_pad(void)
{
    pump();
    int count = 0;
    SDL_JoystickID *ids = SDL_GetJoysticks(&count);
    assert(count == 1 && ids);
    SDL_Gamepad *pad = SDL_OpenGamepad(ids[0]);
    SDL_free(ids);
    assert(pad);
    return pad;
}

static bool has_gyro(SDL_Gamepad *pad)
{
    bool has = SDL_GamepadHasSensor(pad, SDL_SENSOR_GYRO);
    if (has) {
        float values[3];
        assert(SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_GYRO, true));
        pump();
        assert(SDL_GetGamepadSensorData(pad, SDL_SENSOR_GYRO, values, 3));
        assert(values[0] != 0 && values[1] != 0 && values[2] != 0);
    }
    return has;
}

int main(void)
{
    const char *scenario = getenv("GS_HOTPLUG_SCENARIO");
    assert(scenario && getenv("GS_HOST_NS"));
    assert(!mkdir("/dev/input", 0700));
    SDL_SetHint(SDL_HINT_JOYSTICK_HIDAPI, "0");
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");
    SDL_SetHint("SDL_JOYSTICK_THREAD", "0");
    SDL_SetHint("SDL_JOYSTICK_DISABLE_UDEV", "1");
    const char *expected_library = getenv("GS_EXPECT_SDL3_LIBRARY");
    if (expected_library) {
        Dl_info loaded;
        assert(dladdr((void *)SDL_GetVersion, &loaded) && loaded.dli_fname);
        assert(!strcmp(loaded.dli_fname, expected_library));
    }
    void (*readable)(int) = dlsym(RTLD_DEFAULT, "gs_fixture_set_motion_readable");
    assert(readable);
    bool race = !strcmp(scenario, "readability-race");
    bool gated = !strcmp(scenario, "readiness-gated");
    if (!strcmp(scenario, "present-at-init")) { node(1, true); node(0, true); }
    assert(SDL_Init(SDL_INIT_GAMEPAD));
    printf("SDL version=%d revision=%s\n", SDL_GetVersion(), SDL_GetRevision());
    if (strcmp(scenario, "present-at-init")) {
        if (race || gated) readable(0);
        if (strcmp(scenario, "sensor-after-open")) { node(1, true); pump(); }
        if (gated) {
            /* The runner's real policy withholds publication until processed
             * notification AND access for this exact sensor/session exist. */
            assert(getenv("GS_GATE_PERMISSION") && !strcmp(getenv("GS_GATE_PERMISSION"), "1"));
            readable(1);
            assert(!chmod("/dev/input/event1", 0600));
            pump();
        }
        node(0, true);
    }
    SDL_Gamepad *pad = open_pad();
    bool initial = has_gyro(pad);
    bool after = initial;
    if (!strcmp(scenario, "sensor-after-open") || race) {
        assert(!initial);
        if (race) { readable(1); assert(!chmod("/dev/input/event1", 0600)); }
        else node(1, true);
        pump();
        after = has_gyro(pad);
        assert(!after); /* Reproduced missing late association. */
        SDL_CloseGamepad(pad);
        pad = open_pad();
        assert(has_gyro(pad)); /* Closing/reopening is a diagnostic only. */
    } else {
        assert(initial);
    }
    SDL_CloseGamepad(pad);
    node(0, false); node(1, false); pump();
    int count = -1; SDL_JoystickID *ids = SDL_GetJoysticks(&count);
    assert(count == 0); SDL_free(ids);
    /* Reconnect while the SAME SDL instance stays running. */
    node(1, true); pump(); node(0, true);
    pad = open_pad(); assert(has_gyro(pad)); SDL_CloseGamepad(pad);
    printf("scenario=%s initial_gyro=%d late_gyro=%d sensor_first_reconnect=1 result=PASS\n",
           scenario, initial, after);
    void (*stats)(void) = dlsym(RTLD_DEFAULT, "gs_fixture_stats");
    assert(stats); stats();
    SDL_Quit();
    return 0;
}
