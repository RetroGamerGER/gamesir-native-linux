// SPDX-License-Identifier: GPL-2.0-only
/* Installed SDL + synthetic evdev test. Never execute on the host. */
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifdef TEST_SDL2
#include <SDL2/SDL.h>
#define PAD SDL_GameController
#define PADBTN SDL_GameControllerButton
#define PGET SDL_GameControllerGetButton
#define PMAX SDL_CONTROLLER_BUTTON_MAX
#define JGET SDL_JoystickGetButton
#define JCOUNT SDL_JoystickNumButtons
#define AXCOUNT SDL_JoystickNumAxes
#define JAXIS SDL_JoystickGetAxis
#define JHAT SDL_JoystickGetHat
#define PAXIS SDL_GameControllerGetAxis
#define PADAXIS SDL_GameControllerAxis
#define JVENDOR SDL_JoystickGetVendor
#define JPRODUCT SDL_JoystickGetProduct
#define JVERSION SDL_JoystickGetProductVersion
static const PADBTN dpad[] = {SDL_CONTROLLER_BUTTON_DPAD_UP, SDL_CONTROLLER_BUTTON_DPAD_RIGHT,
 SDL_CONTROLLER_BUTTON_DPAD_DOWN, SDL_CONTROLLER_BUTTON_DPAD_LEFT};
static const PADBTN expected[] = {SDL_CONTROLLER_BUTTON_A, SDL_CONTROLLER_BUTTON_B,
 SDL_CONTROLLER_BUTTON_X, SDL_CONTROLLER_BUTTON_Y, SDL_CONTROLLER_BUTTON_LEFTSHOULDER,
 SDL_CONTROLLER_BUTTON_RIGHTSHOULDER, SDL_CONTROLLER_BUTTON_BACK, SDL_CONTROLLER_BUTTON_START,
 SDL_CONTROLLER_BUTTON_GUIDE, SDL_CONTROLLER_BUTTON_LEFTSTICK, SDL_CONTROLLER_BUTTON_RIGHTSTICK,
 SDL_CONTROLLER_BUTTON_PADDLE2, SDL_CONTROLLER_BUTTON_PADDLE1, SDL_CONTROLLER_BUTTON_PADDLE4,
 SDL_CONTROLLER_BUTTON_PADDLE3, SDL_CONTROLLER_BUTTON_INVALID, SDL_CONTROLLER_BUTTON_MISC1};
#else
#include <SDL3/SDL.h>
#define PAD SDL_Gamepad
#define PADBTN SDL_GamepadButton
#define PGET SDL_GetGamepadButton
#define PMAX SDL_GAMEPAD_BUTTON_COUNT
#define JGET SDL_GetJoystickButton
#define JCOUNT SDL_GetNumJoystickButtons
#define AXCOUNT SDL_GetNumJoystickAxes
#define JAXIS SDL_GetJoystickAxis
#define JHAT SDL_GetJoystickHat
#define PAXIS SDL_GetGamepadAxis
#define PADAXIS SDL_GamepadAxis
#define JVENDOR SDL_GetJoystickVendor
#define JPRODUCT SDL_GetJoystickProduct
#define JVERSION SDL_GetJoystickProductVersion
static const PADBTN dpad[] = {SDL_GAMEPAD_BUTTON_DPAD_UP, SDL_GAMEPAD_BUTTON_DPAD_RIGHT,
 SDL_GAMEPAD_BUTTON_DPAD_DOWN, SDL_GAMEPAD_BUTTON_DPAD_LEFT};
static const PADBTN expected[] = {SDL_GAMEPAD_BUTTON_SOUTH, SDL_GAMEPAD_BUTTON_EAST,
 SDL_GAMEPAD_BUTTON_WEST, SDL_GAMEPAD_BUTTON_NORTH, SDL_GAMEPAD_BUTTON_LEFT_SHOULDER,
 SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER, SDL_GAMEPAD_BUTTON_BACK, SDL_GAMEPAD_BUTTON_START,
 SDL_GAMEPAD_BUTTON_GUIDE, SDL_GAMEPAD_BUTTON_LEFT_STICK, SDL_GAMEPAD_BUTTON_RIGHT_STICK,
 SDL_GAMEPAD_BUTTON_LEFT_PADDLE1, SDL_GAMEPAD_BUTTON_RIGHT_PADDLE1, SDL_GAMEPAD_BUTTON_LEFT_PADDLE2,
 SDL_GAMEPAD_BUTTON_RIGHT_PADDLE2, SDL_GAMEPAD_BUTTON_MISC2, SDL_GAMEPAD_BUTTON_MISC1};
#endif
static const unsigned codes[] = {304,305,307,308,310,311,314,315,316,317,318,704,705,706,707,708,167};
static unsigned raw_edges[17][2], mapped_edges[PMAX][2], expected_edges[PMAX];
static int mapped_button(int raw_button, int mapped, int misc2)
{
    if (raw_button == 15 && !misc2) return -1;
    return !mapped && raw_button >= 11 && raw_button <= 15 ? -1 : expected[raw_button];
}
static void drain(void)
{
    SDL_Event e;
    SDL_PumpEvents();
    while (SDL_PollEvent(&e)) {
#ifdef TEST_SDL2
        if (e.type == SDL_JOYBUTTONDOWN || e.type == SDL_JOYBUTTONUP) {
            if (e.jbutton.button < 17) raw_edges[e.jbutton.button][e.type == SDL_JOYBUTTONDOWN]++;
        }
        if (e.type == SDL_CONTROLLERBUTTONDOWN || e.type == SDL_CONTROLLERBUTTONUP) {
            if (e.cbutton.button < PMAX) mapped_edges[e.cbutton.button][e.type == SDL_CONTROLLERBUTTONDOWN]++;
        }
#else
        if (e.type == SDL_EVENT_JOYSTICK_BUTTON_DOWN || e.type == SDL_EVENT_JOYSTICK_BUTTON_UP) {
            if (e.jbutton.button < 17) raw_edges[e.jbutton.button][e.type == SDL_EVENT_JOYSTICK_BUTTON_DOWN]++;
        }
        if (e.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN || e.type == SDL_EVENT_GAMEPAD_BUTTON_UP) {
            if (e.gbutton.button < PMAX) mapped_edges[e.gbutton.button][e.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN]++;
        }
#endif
    }
}

int main(void)
{
    if (access("/fixture/sandbox-marker", R_OK) || !access("/dev/input", F_OK) ||
        !access("/dev/bus/usb", F_OK) || !access("/dev/hidraw0", F_OK)) return 2;
    const char *scenario = getenv("GS_SCENARIO"), *mapping = getenv("GS_MAPPING");
    if (!scenario) return 2;
    int alpha = strstr(scenario, "alpha17") != NULL, mapped = mapping != NULL;
    int xpad = strstr(scenario, "xpad11") != NULL;
    if (xpad && (!mapping || !getenv("SDL_GAMECONTROLLERCONFIG") ||
                 strcmp(mapping, getenv("SDL_GAMECONTROLLERCONFIG")))) return 2;
    int misc2 = mapping && strstr(mapping,",misc2:") != NULL;
    int count_expected = xpad ? 11 : alpha ? 17 : 15, ok = 1;
    SDL_SetHint(SDL_HINT_JOYSTICK_HIDAPI, "0");
    SDL_SetHint("SDL_JOYSTICK_LINUX_CLASSIC", "0");
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");
    SDL_SetHint(SDL_HINT_JOYSTICK_DEVICE, "/fixture/evdev/event0");
#ifdef TEST_SDL2
    if (SDL_Init(SDL_INIT_GAMECONTROLLER | SDL_INIT_HAPTIC)) return 2;
    SDL_Joystick *j = SDL_NumJoysticks() == 1 ? SDL_JoystickOpen(0) : NULL;
    char guid[33]; if (!j) return 2;
    SDL_JoystickGetGUIDString(SDL_JoystickGetGUID(j), guid, sizeof(guid));
    if (mapped && !xpad && SDL_GameControllerAddMapping(mapping) < 0) return 2;
    PAD *pad = SDL_GameControllerOpen(0);
    SDL_version version; SDL_GetVersion(&version);
    printf("SDL2=%d.%d.%d revision=%s\n", version.major,version.minor,version.patch,SDL_GetRevision());
#else
    if (!SDL_Init(SDL_INIT_GAMEPAD | SDL_INIT_HAPTIC)) return 2;
    int count; SDL_JoystickID *ids = SDL_GetJoysticks(&count);
    SDL_Joystick *j = count == 1 ? SDL_OpenJoystick(ids[0]) : NULL;
    char guid[33]; if (!j) return 2;
    SDL_GUIDToString(SDL_GetJoystickGUID(j), guid, sizeof(guid));
    if (mapped && !xpad && SDL_AddGamepadMapping(mapping) < 0) return 2;
    PAD *pad = SDL_OpenGamepad(ids[0]); SDL_free(ids);
    printf("SDL3=%d revision=%s\n", SDL_GetVersion(),SDL_GetRevision());
#endif
    if (!pad) { fprintf(stderr,"Open failed: %s\n",SDL_GetError()); return 2; }
    printf("guid=%s raw_buttons=%d scenario=%s\n",guid,JCOUNT(j),scenario);
    int zzz = getenv("GS_VARIANT") && !strcmp(getenv("GS_VARIANT"), "105e");
    printf("synthetic_identity=%04x:%04x version=%04x hardware_guid_observed=0\n",
           JVENDOR(j), JPRODUCT(j), JVERSION(j));
    ok &= JVENDOR(j) == 0x3537 && JPRODUCT(j) == (zzz ? 0x105e : 0x109c) &&
          JVERSION(j) == (zzz ? 0x0607 : 1);
    ok &= JCOUNT(j) == count_expected;
    if (xpad) {
        /* Same USB identity/version, different evdev name CRC and capabilities.
         * Inspect SDL's chosen mapping, not just whether unavailable buttons fire. */
#ifdef TEST_SDL2
        char *selected = SDL_GameControllerMapping(pad);
#else
        char *selected = SDL_GetGamepadMapping(pad);
#endif
        int applied = !selected || strstr(selected, "GameSir G7 Pro") || strstr(selected, "paddle");
        printf("selected_mapping=%s\n", selected ? selected : "(none)");
        ok &= !applied && strcmp(guid, "03004535373500005e10000007060000");
        printf("mapping_scope_negative=xpad105e native_hint_applied=%d steam_ui_verified=0 result=%s\n",applied,ok?"PASS":"FAIL");
        SDL_free(selected);
        void (*stats)(void) = dlsym(RTLD_DEFAULT,"gs_fixture_stats"); if (stats) stats(); else ok=0;
#ifdef TEST_SDL2
        SDL_GameControllerClose(pad); SDL_JoystickClose(j);
#else
        SDL_CloseGamepad(pad); SDL_CloseJoystick(j);
#endif
        SDL_Quit();
        return ok ? 0 : 1;
    }
    void (*push)(unsigned,int) = dlsym(RTLD_DEFAULT,"gs_fixture_push_key");
    void (*push_keys)(const unsigned *,const int *,unsigned) = dlsym(RTLD_DEFAULT,"gs_fixture_push_keys");
    void (*push_abs)(const unsigned *,const int *,unsigned) = dlsym(RTLD_DEFAULT,"gs_fixture_push_abs");
    unsigned (*uploads)(void) = dlsym(RTLD_DEFAULT,"gs_fixture_ff_uploads");
    unsigned (*plays)(void) = dlsym(RTLD_DEFAULT,"gs_fixture_ff_plays");
    if (!push || !push_keys || !push_abs || !uploads || !plays) return 2;
    drain();
    unsigned tested = 0;
    for (int i = 0; i < count_expected; i++) {
        int wanted = mapped_button(i,mapped,misc2);
        if (wanted >= 0) expected_edges[wanted]++;
        for (int down = 1; down >= 0; down--) {
            push(codes[i],down); drain();
            if (!down && i == 8) { SDL_Delay(300); drain(); } /* SDL guide-button minimum hold. */
            for (int b = 0; b < count_expected; b++) {
                if (!!JGET(j,b) != !!(down && b == i)) {
                    fprintf(stderr,"raw key=%u state=%d got-b%d=%d\n",codes[i],down,b,JGET(j,b)); ok=0;
                }
            }
            for (int b = 0; b < PMAX; b++) {
                if (!!PGET(pad,(PADBTN)b) != !!(down && b == wanted)) {
                    fprintf(stderr,"mapped key=%u state=%d wanted=%d got-b%d=%d\n",codes[i],down,wanted,b,PGET(pad,(PADBTN)b)); ok=0;
                }
            }
        }
        printf("key=%u raw=b%d SDL_button=%d independent=%s\n",codes[i],i,wanted,ok?"yes":"FAIL");
        tested++;
    }
    for (int i = 0; i < count_expected; i++) {
        if (raw_edges[i][0] != 1 || raw_edges[i][1] != 1) {
            fprintf(stderr,"raw edge mismatch b%d up=%u down=%u\n",i,raw_edges[i][0],raw_edges[i][1]); ok=0;
        }
    }
    for (int i = 0; i < PMAX; i++) {
        if (mapped_edges[i][0] != expected_edges[i] || mapped_edges[i][1] != expected_edges[i]) {
            fprintf(stderr,"gamepad edge mismatch b%d up=%u down=%u expected=%u\n",i,mapped_edges[i][0],mapped_edges[i][1],expected_edges[i]); ok=0;
        }
    }
    /* Every combination of A and four paddles, then duplicate held state and
     * release. Each frame has one SYN_REPORT: held keys must survive unrelated
     * releases and no duplicate edge may appear for an unchanged key. */
    static const unsigned combo_codes[] = {304,704,705,706,707};
    static const int combo_raw[] = {0,11,12,13,14};
    unsigned wanted_raw_edges[17][2], wanted_pad_edges[PMAX][2];
    unsigned previous = 0, combo_edges = 0;
    memcpy(wanted_raw_edges,raw_edges,sizeof(raw_edges));
    memcpy(wanted_pad_edges,mapped_edges,sizeof(mapped_edges));
    for (unsigned frame = 0; frame < 34; frame++) {
        unsigned mask = frame < 32 ? frame : frame == 32 ? 31 : 0;
        int states[5], raw_states[17] = {0}, pad_states[PMAX] = {0};
        for (unsigned i = 0; i < 5; i++) {
            int raw = combo_raw[i], target = mapped_button(raw,mapped,misc2);
            states[i] = !!(mask & (1u << i)); raw_states[raw] = states[i];
            if (target >= 0) pad_states[target] = states[i];
            if ((mask ^ previous) & (1u << i)) {
                wanted_raw_edges[raw][states[i]]++; combo_edges++;
                if (target >= 0) wanted_pad_edges[target][states[i]]++;
            }
        }
        push_keys(combo_codes,states,5); drain();
        for (int i = 0; i < count_expected; i++) {
            if (!!JGET(j,i) != raw_states[i] || memcmp(raw_edges[i],wanted_raw_edges[i],sizeof(raw_edges[i]))) {
                fprintf(stderr,"combo frame=%u mask=%u raw b%d state/edges mismatch\n",frame,mask,i); ok=0;
            }
        }
        for (int i = 0; i < PMAX; i++) {
            if (!!PGET(pad,(PADBTN)i) != pad_states[i] || memcmp(mapped_edges[i],wanted_pad_edges[i],sizeof(mapped_edges[i]))) {
                fprintf(stderr,"combo frame=%u mask=%u gamepad b%d state/edges mismatch\n",frame,mask,i); ok=0;
            }
        }
        previous = mask;
    }
    printf("combination_masks=32 combination_frames=34 combination_key_edges=%u held_duplicate_and_release=%s\n",combo_edges,ok?"PASS":"FAIL");

    /* Linux ABS_X/Y/Z/RX/RY/RZ -> SDL raw axes 0..5; gamepad keeps
     * left/right sticks and analog triggers. Extremes avoid rounding ambiguity. */
    static const unsigned axis_codes[] = {0,1,2,3,4,5};
    static const int pad_axis_for_raw[] = {0,1,4,2,3,5};
    int raw_axes[6] = {0,0,-32768,0,0,-32768}, pad_axes[6] = {0};
    ok &= AXCOUNT(j) == 6;
    for (unsigned axis = 0; axis < 6; axis++) {
        int trigger_axis = axis == 2 || axis == 5;
        int values[3] = {trigger_axis ? 1023 : -32768, trigger_axis ? 0 : 32767, 0};
        for (unsigned step = 0; step < 3; step++) {
            push_abs(axis_codes+axis,values+step,1); drain();
            raw_axes[axis] = trigger_axis ? (values[step] ? 32767 : -32768) : values[step];
            pad_axes[pad_axis_for_raw[axis]] = trigger_axis ? (values[step] ? 32767 : 0) : values[step];
            for (int i = 0; i < 6; i++) {
                if (JAXIS(j,i) != raw_axes[i] || PAXIS(pad,(PADAXIS)i) != pad_axes[i]) {
                    fprintf(stderr,"axis=%u step=%u index=%d raw=%d expected=%d gamepad=%d expected=%d\n",
                        axis,step,i,JAXIS(j,i),raw_axes[i],PAXIS(pad,(PADAXIS)i),pad_axes[i]); ok=0;
                }
            }
        }
    }
    static const unsigned hat_codes[] = {16,17}; /* ABS_HAT0X/Y */
    static const int directions[][2] = {{0,-1},{1,-1},{1,0},{1,1},{0,1},{-1,1},{-1,0},{-1,-1},{0,0}};
    for (unsigned step = 0; step < sizeof(directions)/sizeof(*directions); step++) {
        unsigned hat = (directions[step][0] < 0 ? SDL_HAT_LEFT : directions[step][0] > 0 ? SDL_HAT_RIGHT : 0) |
                       (directions[step][1] < 0 ? SDL_HAT_UP : directions[step][1] > 0 ? SDL_HAT_DOWN : 0);
        push_abs(hat_codes,directions[step],2); drain();
        if (JHAT(j,0) != hat) { fprintf(stderr,"D-pad step=%u hat=%u expected=%u\n",step,JHAT(j,0),hat); ok=0; }
        for (int i = 0; i < PMAX; i++) {
            int pressed = 0;
            for (unsigned d = 0; d < 4; d++) if (i == dpad[d]) pressed = !!(hat & (1u << d));
            if (!!PGET(pad,(PADBTN)i) != pressed) { fprintf(stderr,"D-pad step=%u button=%d mismatch\n",step,i); ok=0; }
        }
        for (int i = 0; i < count_expected; i++) if (JGET(j,i)) ok=0;
        for (int i = 0; i < 6; i++) if (PAXIS(pad,(PADAXIS)i) != pad_axes[i]) ok=0;
    }
    printf("axis_snapshots=18 dpad_snapshots=9 standard_controls=%s\n",ok?"PASS":"FAIL");
#ifdef TEST_SDL2
    int normal = SDL_GameControllerRumble(pad,0x8000,0x4000,100) == 0;
    int trigger = SDL_GameControllerRumbleTriggers(pad,0x8000,0x4000,100) == 0;
#else
    int normal = SDL_RumbleGamepad(pad,0x8000,0x4000,100);
    int trigger = SDL_RumbleGamepadTriggers(pad,0x8000,0x4000,100);
#endif
    printf("synthetic_FF_RUMBLE=%d trigger_rumble=%d ff_uploads=%u ff_plays=%u trigger_error=%s\n",
           normal,trigger,uploads(),plays(),SDL_GetError());
    ok &= normal && !trigger && uploads() > 0 && plays() > 0;
    void (*stats)(void) = dlsym(RTLD_DEFAULT,"gs_fixture_stats"); if (stats) stats(); else ok=0;
    printf("tested_keys=%u edges=%u explicit_mapping=%d steam_ui_verified=0 result=%s\n",tested,tested*2+combo_edges,mapped,ok?"PASS":"FAIL");
#ifdef TEST_SDL2
    SDL_GameControllerClose(pad); SDL_JoystickClose(j);
#else
    SDL_CloseGamepad(pad); SDL_CloseJoystick(j);
#endif
    SDL_Quit();
    return ok ? 0 : 1;
}
