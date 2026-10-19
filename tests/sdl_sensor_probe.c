// SPDX-License-Identifier: GPL-2.0-only
/* Exercise the installed SDL API with a syscall fixture in an empty /dev.
 * This program must never be run directly on the host.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#ifdef TEST_SDL2
#include <SDL2/SDL.h>
#else
#include <SDL3/SDL.h>
#endif

#ifndef TEST_SDL2
static uint32_t cache_word(const void *address)
{
    uint32_t value;
    memcpy(&value, address, sizeof(value));
    return value;
}

/* Private diagnostic offset validation against public SDL getters. Called
 * only in the audited synthetic sandbox with the runner's exact hash gate. */
static int steam_cache_layout(SDL_Gamepad *pad, const void *base)
{
    if (sizeof(void *) != 4) return 0;
    SDL_Joystick *joystick = SDL_GetGamepadJoystick(pad);
    const unsigned char *j = (const unsigned char *)joystick;
    const unsigned char *b = base;
    if (cache_word(b + 0x3b3a00) != (uintptr_t)j ||
        cache_word(b + 0x3aadec) != (uintptr_t)(b + 0x221030)) return 0;
    int ok = cache_word(j) == SDL_GetJoystickID(joystick) &&
        cache_word(j + 0x100) == 0 && cache_word(j + 0x58) == 1 &&
        cache_word(j + 0x5c) == 1;
    const char *path = (const char *)(uintptr_t)cache_word(j + 8);
    ok &= path && !strcmp(path, SDL_GetJoystickPath(joystick));
    const unsigned char *sensor = (const void *)(uintptr_t)cache_word(j + 0x60);
    if (!sensor) return 0;
    ok &= cache_word(sensor) == SDL_SENSOR_GYRO &&
        sensor[4] == SDL_GamepadSensorEnabled(pad, SDL_SENSOR_GYRO);
    float actual[3], expected[3];
    memcpy(actual, sensor + 12, sizeof(actual));
    ok &= SDL_GetGamepadSensorData(pad, SDL_SENSOR_GYRO, expected, 3);
    for (unsigned i = 0; i < 3; i++)
        ok &= isfinite(actual[i]) && fabsf(actual[i] - expected[i]) < .00001f;
    printf("private_sdl32_cache_layout=%s\n", ok ? "PASS" : "FAIL");
    return ok;
}

/* Independently written API-level regression for the observed Steam call
 * sequence. Executes SDL only, not Steam or copied proprietary code. */
static int steam_sensor_sequence(SDL_Gamepad *pad, int resolution)
{
    const SDL_SensorType types[] = {SDL_SENSOR_GYRO, SDL_SENSOR_ACCEL,
        SDL_SENSOR_GYRO_L, SDL_SENSOR_ACCEL_L};
    void (*push)(const int *, int32_t) = dlsym(RTLD_DEFAULT, "gs_fixture_push_sensor");
    if (!push || resolution <= 0) return 0;
    int ok = 1;
    for (unsigned i = 0; i < 4; i++) {
        bool enabled = SDL_SetGamepadSensorEnabled(pad, types[i], true);
        printf("steam-sequence enable sensor=%d result=%d\n", types[i], enabled);
        ok &= enabled == (i == 0);
    }
    ok &= SDL_GamepadSensorEnabled(pad, SDL_SENSOR_GYRO);
    SDL_Event event;
    while (SDL_PollEvent(&event)) { }
    /* 1 ms progression, unchanged tick, long stream, then Linux 31-bit wrap.
     * These are deliberately synthetic boundaries, not a live rate claim. */
    const int32_t ticks[] = {17000, 17000, INT32_MAX - 500, 100};
    const uint64_t expected_ns[] = {17000000, 17000000,
        ((uint64_t)INT32_MAX - 500) * 1000, ((uint64_t)INT32_MAX + 101) * 1000};
    for (unsigned n = 0; n < 4; n++) {
        const int values[] = {9000 + (int)n * 100, -4500, 2250};
        push(values, ticks[n]);
        SDL_PumpEvents();
        int found = 0, events = 0, unexpected = 0;
        while (SDL_PollEvent(&event)) {
            if (event.type != SDL_EVENT_GAMEPAD_SENSOR_UPDATE) continue;
            events++;
            if (event.gsensor.sensor != SDL_SENSOR_GYRO) { unexpected++; continue; }
            int match = event.gsensor.which == SDL_GetGamepadID(pad) &&
                event.gsensor.sensor_timestamp == expected_ns[n];
            for (unsigned i = 0; i < 3; i++)
                match &= isfinite(event.gsensor.data[i]) &&
                    fabsf(event.gsensor.data[i] - values[i] * .01745329252f / resolution) < .00001f;
            found += match;
        }
        ok &= found == 1 && events == 1 && unexpected == 0;
        printf("steam-sequence frame=%u tick=%d expected_ns=%llu matches=%d events=%d other_sensors=%d\n",
            n, ticks[n], (unsigned long long)expected_ns[n], found, events, unexpected);
    }
    for (unsigned i = 0; i < 4; i++)
        ok &= SDL_SetGamepadSensorEnabled(pad, types[i], false) == (i == 0);
    ok &= !SDL_GamepadSensorEnabled(pad, SDL_SENSOR_GYRO);
    const int stopped_values[] = {2000, 3000, 4000};
    push(stopped_values, 200);
    SDL_PumpEvents();
    while (SDL_PollEvent(&event))
        if (event.type == SDL_EVENT_GAMEPAD_SENSOR_UPDATE) ok = 0;
    ok &= SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_GYRO, true);
    const int resumed_values[] = {5000, 6000, 7000};
    push(resumed_values, 1200);
    SDL_PumpEvents();
    int resumed = 0;
    while (SDL_PollEvent(&event)) {
        if (event.type != SDL_EVENT_GAMEPAD_SENSOR_UPDATE ||
            event.gsensor.sensor != SDL_SENSOR_GYRO) continue;
        int match = event.gsensor.which == SDL_GetGamepadID(pad);
        for (unsigned i = 0; i < 3; i++)
            match &= fabsf(event.gsensor.data[i] - resumed_values[i] * .01745329252f / resolution) < .00001f;
        resumed += match;
    }
    ok &= resumed > 0;
    printf("steam_enable_missing_channels_timestamps_disable_reenable=%s\n", ok ? "PASS" : "FAIL");
    return ok;
}
#endif

int main(void)
{
    if (access("/fixture/sandbox-marker", R_OK) || !access("/dev/bus/usb", F_OK) ||
        !access("/dev/input", F_OK) || !access("/dev/hidraw0", F_OK)) {
        fprintf(stderr, "Refusing to run without the device-free test namespace.\n");
        return 2;
    }
    const char *s = getenv("GS_SCENARIO");
    if (!s) return 2;
    int accel_resolution = getenv("GS_ACCEL_RES") ? atoi(getenv("GS_ACCEL_RES")) : 8192;
    int gyro_resolution = getenv("GS_GYRO_RES") ? atoi(getenv("GS_GYRO_RES")) : 16;
    if (!strcmp(s, "zero-resolution")) accel_resolution = gyro_resolution = 0;
    SDL_SetHint(SDL_HINT_JOYSTICK_HIDAPI, "0");
    SDL_SetHint("SDL_JOYSTICK_LINUX_CLASSIC", "0");
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");
    SDL_SetHint(SDL_HINT_JOYSTICK_DEVICE, !strcmp(s, "iio-only") ?
        "/fixture/evdev/event0" : "/fixture/evdev/event0:/fixture/evdev/event1");
#ifdef TEST_SDL2
    SDL_version v; SDL_GetVersion(&v);
    printf("SDL2 %d.%d.%d, revision %s\n", v.major, v.minor, v.patch, SDL_GetRevision());
    if (SDL_Init(SDL_INIT_GAMECONTROLLER)) { fprintf(stderr, "%s\n", SDL_GetError()); return 2; }
    int count = SDL_NumJoysticks();
    SDL_Joystick *j = count ? SDL_JoystickOpen(0) : NULL;
    if (!j) { fprintf(stderr, "count=%d %s\n", count, SDL_GetError()); return 2; }
    char guid[33]; SDL_JoystickGetGUIDString(SDL_JoystickGetGUID(j), guid, sizeof(guid));
#else
    const char *expected_library = getenv("GS_EXPECT_SDL3_LIBRARY");
    Dl_info loaded;
    if (!dladdr((void *)SDL_GetVersion, &loaded) || !loaded.dli_fname ||
        (expected_library && strcmp(expected_library, loaded.dli_fname))) {
        fprintf(stderr, "SDL3 library identity mismatch; refusing fallback.\n");
        return 2;
    }
    printf("SDL3 loaded-library=%s\n", loaded.dli_fname);
    printf("SDL3 %d, revision %s\n", SDL_GetVersion(), SDL_GetRevision());
    if (!SDL_Init(SDL_INIT_GAMEPAD)) { fprintf(stderr, "%s\n", SDL_GetError()); return 2; }
    int count = 0; SDL_JoystickID *ids = SDL_GetJoysticks(&count);
    SDL_Joystick *j = count ? SDL_OpenJoystick(ids[0]) : NULL;
    if (!j) { fprintf(stderr, "count=%d %s\n", count, SDL_GetError()); return 2; }
    char guid[33]; SDL_GUIDToString(SDL_GetJoystickGUID(j), guid, sizeof(guid));
#endif
    /* Explicit mapping isolates sensor discovery from the controller DB. */
    char mapping[512];
    snprintf(mapping, sizeof(mapping), "%s,GameSir Offline Fixture,a:b0,b:b1,x:b2,y:b3,leftx:a0,lefty:a1,rightx:a3,righty:a4,lefttrigger:a2,righttrigger:a5,paddle1:b12,paddle2:b11,paddle3:b14,paddle4:b13,platform:Linux,", guid);
#ifdef TEST_SDL2
    if (SDL_GameControllerAddMapping(mapping) < 0) return 2;
    SDL_GameController *pad = SDL_GameControllerOpen(0);
    if (!pad) { fprintf(stderr, "%s\n", SDL_GetError()); return 2; }
    int gyro = SDL_GameControllerHasSensor(pad, SDL_SENSOR_GYRO);
    int accel = SDL_GameControllerHasSensor(pad, SDL_SENSOR_ACCEL);
#else
    if (SDL_AddGamepadMapping(mapping) < 0) return 2;
    SDL_Gamepad *pad = SDL_OpenGamepad(ids[0]);
    SDL_free(ids);
    if (!pad) { fprintf(stderr, "%s\n", SDL_GetError()); return 2; }
    int gyro = SDL_GamepadHasSensor(pad, SDL_SENSOR_GYRO);
    int accel = SDL_GamepadHasSensor(pad, SDL_SENSOR_ACCEL);
#endif
    int absent = !strcmp(s, "iio-only") || !strcmp(s, "wrong-uniq");
    int expected_gyro = !absent && strcmp(s, "missing-rz");
    int expected_accel = !absent && strcmp(s, "observed-gyro");
    int ok = count == 1 && gyro == !!expected_gyro && accel == expected_accel;
    float g[3] = {0}, a[3] = {0};
#ifdef TEST_SDL2
    if (gyro && SDL_GameControllerSetSensorEnabled(pad, SDL_SENSOR_GYRO, SDL_TRUE)) ok = 0;
    if (accel && SDL_GameControllerSetSensorEnabled(pad, SDL_SENSOR_ACCEL, SDL_TRUE)) ok = 0;
    SDL_PumpEvents();
    if (gyro && SDL_GameControllerGetSensorData(pad, SDL_SENSOR_GYRO, g, 3)) ok = 0;
    if (accel && SDL_GameControllerGetSensorData(pad, SDL_SENSOR_ACCEL, a, 3)) ok = 0;
#else
    if (gyro && !SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_GYRO, true)) ok = 0;
    if (accel && !SDL_SetGamepadSensorEnabled(pad, SDL_SENSOR_ACCEL, true)) ok = 0;
    SDL_PumpEvents();
    if (gyro && !SDL_GetGamepadSensorData(pad, SDL_SENSOR_GYRO, g, 3)) ok = 0;
    if (accel && !SDL_GetGamepadSensorData(pad, SDL_SENSOR_ACCEL, a, 3)) ok = 0;
#endif
    int finite = 1;
    if (!strcmp(s, "observed-gyro")) {
        void (*push)(const unsigned *, const int *, unsigned) = dlsym(RTLD_DEFAULT, "gs_fixture_push_keys");
        const unsigned codes[] = {304,704,705,706,707};
        if (!push) return 2;
        for (unsigned mask = 0; mask < 32; mask++) {
            int keys[5];
            for (unsigned i = 0; i < 5; i++) keys[i] = !!(mask & (1u << i));
            push(codes, keys, 5); SDL_PumpEvents();
#ifdef TEST_SDL2
            const SDL_GameControllerButton buttons[] = {SDL_CONTROLLER_BUTTON_A,
                SDL_CONTROLLER_BUTTON_PADDLE2, SDL_CONTROLLER_BUTTON_PADDLE1,
                SDL_CONTROLLER_BUTTON_PADDLE4, SDL_CONTROLLER_BUTTON_PADDLE3};
            for (unsigned i = 0; i < 5; i++) ok &= SDL_GameControllerGetButton(pad, buttons[i]) == keys[i];
#else
            const SDL_GamepadButton buttons[] = {SDL_GAMEPAD_BUTTON_SOUTH,
                SDL_GAMEPAD_BUTTON_LEFT_PADDLE1, SDL_GAMEPAD_BUTTON_RIGHT_PADDLE1,
                SDL_GAMEPAD_BUTTON_LEFT_PADDLE2, SDL_GAMEPAD_BUTTON_RIGHT_PADDLE2};
            for (unsigned i = 0; i < 5; i++) ok &= SDL_GetGamepadButton(pad, buttons[i]) == keys[i];
#endif
        }
        int released[5] = {0}; push(codes, released, 5); SDL_PumpEvents();
        const int raw_buttons[] = {0,11,12,13,14};
#ifdef TEST_SDL2
        for (unsigned i = 0; i < 5; i++) ok &= !SDL_JoystickGetButton(j, raw_buttons[i]);
        ok &= !SDL_GameControllerGetSensorData(pad, SDL_SENSOR_GYRO, g, 3);
#else
        for (unsigned i = 0; i < 5; i++) ok &= !SDL_GetJoystickButton(j, raw_buttons[i]);
        ok &= SDL_GetGamepadSensorData(pad, SDL_SENSOR_GYRO, g, 3);
#endif
        printf("gyro_with_paddles_32_combinations=%s\n", ok ? "PASS" : "FAIL");
    }
#ifndef TEST_SDL2
    if (!strcmp(s, "observed-gyro")) {
        SDL_Event event;
        int gyro_event_matches = 0;
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_EVENT_GAMEPAD_SENSOR_UPDATE) {
                printf("sensor-event type=%d host=%llu sensor=%llu data=%.9g,%.9g,%.9g\n",
                    event.gsensor.sensor, (unsigned long long)event.gsensor.timestamp,
                    (unsigned long long)event.gsensor.sensor_timestamp,
                    event.gsensor.data[0], event.gsensor.data[1], event.gsensor.data[2]);
                if (event.gsensor.sensor == SDL_SENSOR_GYRO &&
                    event.gsensor.sensor_timestamp == 16000000 &&
                    fabsf(event.gsensor.data[0] - g[0]) < .000001f &&
                    fabsf(event.gsensor.data[1] - g[1]) < .000001f &&
                    fabsf(event.gsensor.data[2] - g[2]) < .000001f)
                    gyro_event_matches = 1;
            }
        }
        ok &= gyro_event_matches;
        printf("gyro_event_value_and_timestamp=%s\n", gyro_event_matches ? "PASS" : "FAIL");
    }
#endif
    for (int i = 0; i < 3; i++) if (!isfinite(g[i]) || !isfinite(a[i])) finite = 0;
    if (!strcmp(s, "zero-resolution")) ok &= !finite;
    else if (!absent) {
        int raw[6];
        if (sscanf(getenv("GS_RAW"), "%d,%d,%d,%d,%d,%d", raw, raw+1, raw+2, raw+3, raw+4, raw+5) != 6) return 2;
        for (int i = 0; i < 3; i++) {
            if (accel && fabsf(a[i] - raw[i] * 9.80665f / accel_resolution) > .0001f) ok = 0;
            if (gyro && fabsf(g[i] - raw[i+3] * .01745329252f / gyro_resolution) > .0001f) ok = 0;
        }
        ok &= finite;
    }
#ifndef TEST_SDL2
    if (!strcmp(s, "observed-gyro")) ok &= steam_sensor_sequence(pad, gyro_resolution);
    if (!strcmp(s, "observed-gyro") && getenv("GS_CHECK_STEAM_LAYOUT"))
        ok &= steam_cache_layout(pad, loaded.dli_fbase);
#endif
    printf("scenario=%s gamepads=%d gyro=%d accel=%d finite=%d\ngyro(rad/s)=%.9g,%.9g,%.9g accel(m/s2)=%.9g,%.9g,%.9g\nresult=%s\n",
        s, count, gyro, accel, finite, g[0], g[1], g[2], a[0], a[1], a[2], ok ? "PASS" : "FAIL");
    printf("synthetic input resolutions: accel=%d counts/g gyro=%d counts/(degree/s)\n", accel_resolution, gyro_resolution);
    void (*stats)(void) = dlsym(RTLD_DEFAULT, "gs_fixture_stats");
    if (stats) stats(); else ok = 0;
#ifdef TEST_SDL2
    SDL_GameControllerClose(pad); SDL_JoystickClose(j);
#else
    SDL_CloseGamepad(pad); SDL_CloseJoystick(j);
#endif
    SDL_Quit();
    return ok ? 0 : 1;
}
