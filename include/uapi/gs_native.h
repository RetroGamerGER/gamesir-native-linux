/* SPDX-License-Identifier: GPL-2.0-only WITH Linux-syscall-note */
#ifndef GS_NATIVE_UAPI_H
#define GS_NATIVE_UAPI_H
#include <linux/ioctl.h>
#include <linux/types.h>

#define GSN_ABI_VERSION 1
#define GSN_MAX_PULSE_MS 1000
/* Allows a 300 s guided test plus bounded startup/teardown margin. */
#define GSN_MAX_SESSION_MS 315000
#define GSN_FLAG_EXPERIMENTAL_ACCEL 1
#define GSN_FLAG_ACCEL_VALID 2
/* Private ABI only, not a Linux EV_FF effect type. Persistent mode: cancel one
 * channel only if its last writer was a private pulse, preserving newer FF.
 * percent and duration_ms must both be zero; all reserved fields stay zero.
 */
#define GSN_PULSE_CANCEL 1

struct gsn_info {
	__u32 abi_version;
	__u32 pid;
	__u32 state;
	__s32 last_error;
	__u32 output_enabled;
	__u32 session_active;
	__u32 accel_counts_per_g_num;
	__u32 accel_counts_per_g_den;
	__aligned_u64 input_packets;
	__aligned_u64 imu_packets;
	__aligned_u64 rejected_packets;
};

struct gsn_pulse {
	__u32 abi_version;
	__u32 motor; /* 0 LT, 1 RT, 2 left grip, 3 right grip */
	__u32 percent;
	__u32 duration_ms;
	__u32 flags; /* zero: bounded pulse; GSN_PULSE_CANCEL: conditional channel stop */
	__u32 reserved[3]; /* must be zero */
};

struct gsn_sample {
	__u32 abi_version;
	__u32 flags;
	__aligned_u64 host_monotonic_ns;
	__aligned_u64 sample_number;
	__s16 gyro_raw[3];
	__s16 accel_raw[3];
	__s32 accel_experimental_um_s2[3];
};

/* Additive experimental ABI 1 commands. One synchronous, bounded setup attempt.
 * Opt-in persistent receiver_wait returns in state 9 with setup complete;
 * the kernel retains passive RX, not a userspace call or repeated setup.
 * Direct 105e startup stays on the claimed instance and uses flags=0.
 */
#define GSN_BOOT_ALLOW_XPAD_HANDOVER 1
struct gsn_boot_request {
	__u32 abi_version;
	__u32 flags; /* Optional handover of only the correlated new 109c IF0. */
	__u32 reserved[2];
};

struct gsn_boot_status {
	__u32 abi_version;
	__u32 state; /* gs_boot_state: existing 0..8; appended WAIT_RECEIVER=9. */
	__s32 error;
	__u32 failed_stage;
	__u32 pad_seen;
	__u32 imu_seen;
	__u32 handover_attempted;
	__u32 reserved;
	__aligned_u64 port_token; /* Opaque counters, never kernel pointers. */
	__aligned_u64 instance_token;
};

#define GSN_GET_INFO _IOR('G', 0x70, struct gsn_info)
#define GSN_GET_SAMPLE _IOR('G', 0x71, struct gsn_sample)
#define GSN_START_SESSION _IO('G', 0x72)
#define GSN_PULSE _IOW('G', 0x73, struct gsn_pulse)
#define GSN_STOP _IO('G', 0x74)
#define GSN_END_SESSION _IO('G', 0x75)
#define GSN_BOOTSTRAP _IOW('G', 0x76, struct gsn_boot_request)
#define GSN_GET_BOOT_STATUS _IOR('G', 0x77, struct gsn_boot_status)
/* Persistent mode only: one reinitialization after a completed PM resume of
 * this already bootstrapped native instance, never an identity transition.
 */
#define GSN_RESUME _IO('G', 0x78)
/* Additive ABI 1: optional two-phase input publication, never a USB command.
 * Names identify this binding's kernel objects, not persistent hardware IDs.
 */
#define GSN_INPUT_DEFERRED 1
#define GSN_INPUT_PUBLISHED 2
#define GSN_INPUT_SENSOR 4
struct gsn_input_status {
	__u32 abi_version;
	__u32 flags;
	__aligned_u64 port_token;
	__aligned_u64 instance_token;
	__u32 gyro_resolution;
	__u32 accel_resolution;
	char sensor_name[32];
	char uniq[112];
};

struct gsn_input_publish {
	__u32 abi_version;
	__u32 reserved;
	__aligned_u64 port_token;
	__aligned_u64 instance_token;
};

#define GSN_GET_INPUT_STATUS _IOR('G', 0x79, struct gsn_input_status)
#define GSN_PUBLISH_INPUT _IOW('G', 0x7a, struct gsn_input_publish)

/* Experimental TMR-only maintenance. Default disabled; CAP_SYS_ADMIN required.
 * No raw packet, endpoint, calibration value or arbitrary register access.
 * GET does not renew the lease. Monotonic ns/count are captured by RX; report
 * is the latest complete E0, not a lossless queue. epoch is a continuity
 * guard (including silence/PM), NOT proof of physical RF identity.
 */
#define GSN_TMR_ENABLED 1
#define GSN_TMR_FRESH 2
#define GSN_TMR_LEASED 4
#define GSN_TMR_ACQUIRE 1
#define GSN_TMR_START 2
#define GSN_TMR_FINISH 3
#define GSN_TMR_EXIT 4
#define GSN_TMR_RELEASE 5
#define GSN_TMR_RENEW 6
struct gsn_tmr_request {
	__u32 abi_version;
	__u32 operation;
	__aligned_u64 port_token;
	__aligned_u64 instance_token;
	__aligned_u64 stream_epoch;
	__aligned_u64 generation; /* Nonzero client nonce; fixed for this FD. */
	__u32 reserved[2];
};
struct gsn_tmr_status {
	__u32 abi_version;
	__u32 flags;
	__u32 pid;
	__u32 phase; /* 0 idle, 1 leased, 2 started, 3 finished, 4 exited, 5 failed */
	__s32 error; /* First failure survives cleanup. No storage ACK implied. */
	__u32 reserved;
	__aligned_u64 port_token;
	__aligned_u64 instance_token;
	__aligned_u64 stream_epoch;
	__aligned_u64 generation;
	__aligned_u64 report_number;
	__aligned_u64 host_monotonic_ns;
	__aligned_u64 lease_deadline_ns;
	__u8 report[64];
};
#define GSN_TMR_GET _IOR('G', 0x7b, struct gsn_tmr_status)
#define GSN_TMR_COMMAND _IOW('G', 0x7c, struct gsn_tmr_request)
#endif
