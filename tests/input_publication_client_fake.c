// SPDX-License-Identifier: GPL-2.0-only
/* Actual command client; only synthetic stat/ioctl/open, never a device. */
#define main client_main
#define open fixture_open
#define close fixture_close
#define ioctl fixture_ioctl
#define fstat fixture_fstat
#include "../tools/native/gsnative-ctl.c"
#undef main
#undef open
#undef close
#undef ioctl
#undef fstat
#include <assert.h>
#include <stdarg.h>

_Static_assert(sizeof(struct gsn_input_status)==176, "compat status layout");
_Static_assert(sizeof(struct gsn_input_publish)==24, "compat publish layout");
static const char *mode;
static int publications;
int fixture_open(const char *path, int flags, ...) {
    assert(!strcmp(path,"/dev/gsnative-fixture") && flags & O_NOFOLLOW);
    if (!strcmp(mode,"busy")) { errno=EBUSY; return -1; }
    return 17;
}
int fixture_close(int fd) { assert(fd==17); return 0; }
int fixture_fstat(int fd,struct stat *out) { assert(fd==17); memset(out,0,sizeof(*out));out->st_mode=S_IFCHR;return 0; }
int fixture_ioctl(int fd,unsigned long command,...) {
    assert(fd==17);
    va_list ap; va_start(ap,command); void *out=va_arg(ap,void *);va_end(ap);
    if(command==GSN_GET_BOOT_STATUS) {
        *(struct gsn_boot_status *)out=(struct gsn_boot_status){.abi_version=1,.state=7,.port_token=91,.instance_token=42};
        if(!strcmp(mode,"wrong-owner")) ((struct gsn_boot_status *)out)->instance_token=43;
        return 0;
    }
    if(command==GSN_PUBLISH_INPUT) {
        struct gsn_input_publish *p=out;
        assert(p->abi_version==1 && !p->reserved && p->port_token==91 && p->instance_token==42);
        assert(++publications==1);
        if(!strcmp(mode,"publish-failure")) { errno=ENODEV;return -1; }
        return 0;
    }
    assert(command==GSN_GET_INPUT_STATUS);
    if(!strcmp(mode,"unsupported")) { errno=ENOTTY;return -1; }
    struct gsn_input_status *s=out;
    *s=(struct gsn_input_status){.abi_version=1,.flags=publications?7:5,.port_token=91,.instance_token=42,
        .gyro_resolution=100,.accel_resolution=8192};
    strcpy(s->sensor_name,"input42");strcpy(s->uniq,"gsn-2-3.4:1.0-42");
    if(!strcmp(mode,"bad-status")) s->instance_token++;
    if(!strcmp(mode,"bad-strings")) strcpy(s->uniq,"bad\"json");
    return 0;
}
int main(int argc,char **argv) {
    assert(argc==3);mode=argv[2];
    char *args[]={"fixture",argv[1],"/dev/gsnative-fixture","--expect-port","91","--expect-instance","42"};
    int ret=client_main(7,args);
    assert(publications<=1);
    if(!strcmp(mode,"wrong-owner") || !strcmp(mode,"busy")) assert(!publications);
    return ret;
}
