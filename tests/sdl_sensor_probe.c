// SPDX-License-Identifier: GPL-2.0-only
/* Exercise the installed SDL API with a syscall fixture in an empty /dev.
 * This program must never be run directly on the host.
 */
#include <dlfcn.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifdef TEST_SDL2
#include <SDL2/SDL.h>
#else
#include <SDL3/SDL.h>
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
    printf("SDL3 %d, revision %s\n", SDL_GetVersion(), SDL_GetRevision());
    if (!SDL_Init(SDL_INIT_GAMEPAD)) { fprintf(stderr, "%s\n", SDL_GetError()); return 2; }
    int count = 0; SDL_JoystickID *ids = SDL_GetJoysticks(&count);
    SDL_Joystick *j = count ? SDL_OpenJoystick(ids[0]) : NULL;
    if (!j) { fprintf(stderr, "count=%d %s\n", count, SDL_GetError()); return 2; }
    char guid[33]; SDL_GUIDToString(SDL_GetJoystickGUID(j), guid, sizeof(guid));
#endif
    /* Explicit mapping isolates sensor discovery from the controller DB. */
    char mapping[512];
    snprintf(mapping, sizeof(mapping), "%s,GameSir Offline Fixture,a:b0,b:b1,x:b2,y:b3,leftx:a0,lefty:a1,rightx:a3,righty:a4,lefttrigger:a2,righttrigger:a5,platform:Linux,", guid);
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
    int expected_accel = !absent;
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
