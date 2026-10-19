// SPDX-License-Identifier: GPL-2.0-only
#include "../src/gs_sensor.h"
#include <assert.h>
#include <errno.h>
#include <linux/input.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint64_t u64;
struct device { struct device *parent; const char *name; };
struct usb_device { struct { int bcdDevice; } descriptor; };
struct usb_interface { struct device dev; };
struct input_dev {
    const char *name, *phys, *uniq;
    struct input_id id;
    struct device dev;
    unsigned long propbit[1];
    int keys[KEY_CNT], abs[ABS_CNT], res[ABS_CNT], lo[ABS_CNT], hi[ABS_CNT];
    unsigned reports, syncs, timestamp;
    u64 host_ns;
    bool registered, has_timestamp, has_ff;
};
struct gsn_device {
    struct input_dev *input, *gyro_input;
    struct usb_device *udev;
    struct usb_interface *intf;
    struct { unsigned pid; } rt;
    struct { unsigned long long instance; } identity;
    struct gs_gyro_clock gyro_clock;
    struct gs_accel_experimental_scale accel_scale;
    char phys[96], gyro_phys[96], sensor_uniq[112];
    bool input_registered, gyro_registered;
};
static bool experimental_accel;
static int accel_axis_map[3], accel_axis_map_count;
static unsigned accel_counts_per_g_num=8192, accel_counts_per_g_den=1;
static bool experimental_gyro, persistent_mode, fail_alloc, fail_register;
#define ARRAY_SIZE(a) (sizeof(a)/sizeof(*(a)))
#define le16_to_cpu(a) (a)
#define ns_to_ktime(a) (a)
#define dev_name(d) ((d)->name)
#define __set_bit(n,p) (*(p) |= 1UL << (n))
static int gsn_play_effect(struct input_dev *a, void *b, struct ff_effect *c) { return 0; }
static void input_set_drvdata(struct input_dev *a, void *b) {}
static int input_ff_create_memless(struct input_dev *a, void *b, void *c) { a->has_ff=true; return 0; }
static void usb_make_path(struct usb_device *u, char *s, size_t n) { snprintf(s,n,"fixture"); }
static struct input_dev *input_allocate_device(void) { return fail_alloc ? NULL : calloc(1,sizeof(struct input_dev)); }
static int input_register_device(struct input_dev *d) { if (fail_register) return -EIO; d->registered=true; return 0; }
static void input_set_abs_params(struct input_dev *d, int a, int lo, int hi, int fuzz, int flat)
{ assert(!fuzz && !flat); d->lo[a]=lo; d->hi[a]=hi; }
static void input_abs_set_res(struct input_dev *d, int a, int r) { d->res[a]=r; }
static void input_set_capability(struct input_dev *d, int t, int c) {
    if(t==EV_KEY)d->keys[c]=1;
    if(t==EV_MSC && c==MSC_TIMESTAMP)d->has_timestamp=true;
}
static void input_set_timestamp(struct input_dev *d, u64 t) { d->host_ns=t; }
static void input_report_abs(struct input_dev *d, int a, int v) { assert(d->registered); d->abs[a]=v; d->reports++; }
static void input_event(struct input_dev *d, int t, int c, int v) { assert(t==EV_MSC && c==MSC_TIMESTAMP); d->timestamp=v; }
static void input_sync(struct input_dev *d) { assert(d->registered); d->syncs++; }
#include "gyro-functions.h"
int main(void) {
    struct usb_device u={.descriptor.bcdDevice=1};
    struct usb_interface intf={.dev.name="2-3.4:1.0"};
    struct gsn_device a={.udev=&u,.intf=&intf,.rt.pid=0x109c,.identity.instance=1,.accel_scale={8192,1}};
    for(unsigned k=0;k<3;k++) {
        struct gsn_device g=a;
        experimental_gyro=k!=0; g.rt.pid=k==1?0x105e:k==2?0x100a:0x109c;
        assert(!gsn_input_register(&g)); assert(!gsn_gyro_register(&g));
        assert(!g.gyro_input && !g.gyro_registered && !g.input->uniq);
        free(g.input);
    }
    experimental_gyro=true; persistent_mode=true;
    assert(!gsn_input_register(&a));
    assert(a.gyro_registered && a.input->has_ff && !a.gyro_input->has_ff);
    assert(!strcmp(a.input->name,"GameSir G7 Pro"));
    assert(a.input->uniq[0] && a.input->uniq==a.gyro_input->uniq);
    for(unsigned c=704;c<=707;c++)assert(a.input->keys[c]);
    assert(a.gyro_input->propbit[0] & (1UL<<INPUT_PROP_ACCELEROMETER));
    assert(a.gyro_input->has_timestamp && !a.gyro_input->res[ABS_X]);
    for(int i=ABS_RX;i<=ABS_RZ;i++) {
        assert(a.gyro_input->res[i]==100 && a.gyro_input->lo[i]==-229376 && a.gyro_input->hi[i]==229369);
    }
    struct gsn_device b={.udev=&u,.intf=&intf,.rt.pid=0x109c,.identity.instance=2};
    assert(!gsn_input_register(&b));
    assert(strcmp(a.input->uniq,b.input->uniq));
    intf.dev.name="9-1:1.0"; struct gsn_device c={.udev=&u,.intf=&intf,.rt.pid=0x109c,.identity.instance=1,.accel_scale={8192,1}};
    assert(!gsn_input_register(&c)); assert(!strcmp(c.input->uniq,"gsn-9-1:1.0-1"));
    free(c.gyro_input); c.gyro_input=NULL; c.gyro_registered=false;
    assert(strcmp(a.input->uniq,c.input->uniq));
    fail_alloc=true; assert(gsn_gyro_register(&c)==-ENOMEM); fail_alloc=false;
    fail_register=true; assert(gsn_gyro_register(&c)==-EIO && !c.gyro_registered); fail_register=false;
    gs_s16 raw[3]={-32768,32767,-1};
    gsn_gyro_report(&a,raw,NULL,1000000); gsn_gyro_report(&a,raw,NULL,17000000);
    assert(a.gyro_input->syncs==2 && a.gyro_input->timestamp==16001);
    assert(a.gyro_input->host_ns==17000000 && a.gyro_input->abs[ABS_RZ]==-7);
    gs_s16 zero[3]={0}; gsn_gyro_report(&a,zero,NULL,18000000); gs_gyro_pause(&a.gyro_clock);
    assert(!a.gyro_input->abs[ABS_RX] && !a.gyro_input->abs[ABS_RY]);
    gsn_gyro_report(&a,raw,NULL,60000000000ULL); assert(a.gyro_input->timestamp==17002);
    gsn_gyro_report(&c,raw,NULL,100); assert(!c.gyro_input->syncs);
    experimental_gyro=false; gsn_gyro_report(&a,raw,NULL,70000000000ULL); assert(a.gyro_input->syncs==4);
    /* Real acceleration is separately opt-in; no default/partial axis map. */
    experimental_accel=true;
    assert(gsn_sensor_options()==-EINVAL);
    experimental_gyro=true;
    assert(gsn_sensor_options()==-EINVAL);
    accel_axis_map_count=2; accel_axis_map[0]=1; accel_axis_map[1]=2; accel_axis_map[2]=3;
    assert(gsn_sensor_options()==-EINVAL);
    accel_axis_map_count=3; accel_axis_map[2]=-2;
    assert(gsn_sensor_options()==-EINVAL);
    accel_axis_map[0]=-3; accel_axis_map[1]=1; accel_axis_map[2]=-2;
    accel_counts_per_g_den=3; assert(gsn_sensor_options()==-EINVAL);
    accel_counts_per_g_den=1; assert(!gsn_sensor_options());
    experimental_gyro=false; assert(gsn_sensor_options()==-EINVAL); experimental_gyro=true;
    struct gsn_device d={.udev=&u,.intf=&intf,.rt.pid=0x109c,.identity.instance=3,.accel_scale={8192,1}};
    assert(!gsn_input_register(&d));
    for(unsigned i=ABS_X;i<=ABS_Z;i++) {
        assert(d.gyro_input->res[i]==8192 && d.gyro_input->lo[i]==-32768 && d.gyro_input->hi[i]==32768);
    }
    gs_s16 acceleration[3]={8192,0,-32768};
    gsn_gyro_report(&d,raw,acceleration,1000000);
    assert(d.gyro_input->syncs==1 && d.gyro_input->reports==6);
    assert(d.gyro_input->abs[ABS_X]==32768 && d.gyro_input->abs[ABS_Y]==8192 && d.gyro_input->abs[ABS_Z]==0);
    assert(d.gyro_input->abs[ABS_RX]==-229376 && d.gyro_input->timestamp==1);
    gsn_gyro_report(&d,zero,NULL,2000000);
    assert(d.gyro_input->syncs==2 && d.gyro_input->reports==9);
    assert(d.gyro_input->abs[ABS_X]==32768 && !d.gyro_input->abs[ABS_RX]);
    /* Disabled experiment never adds fake acceleration; other capabilities survive. */
    for(unsigned i=704;i<=707;i++) assert(d.input->keys[i]);
    assert(d.input->has_ff && !d.gyro_input->has_ff);
    for(unsigned i=0;i<2;i++) {
        struct gsn_device other={.udev=&u,.intf=&intf,.rt.pid=i?0x105e:0x100a,.accel_scale={8192,1}};
        assert(!gsn_input_register(&other));
        assert(!other.gyro_input && !other.gyro_registered);
        free(other.input);
    }
    free(d.gyro_input); free(d.input);
    free(a.gyro_input); free(a.input); free(b.gyro_input); free(b.input); free(c.gyro_input); free(c.input);
    puts("PASS: actual gyro/accel registration/emission; explicit map/scale gates, coherent six-axis report, neutral retains real accel, opt-in/model guards, seat metadata, unique pairing, arbitrary ports, failed allocations/registration, full-range units, unchanged samples, neutral/pause clock, independent FF and paddle capabilities");
}
