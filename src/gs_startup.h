/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef GS_STARTUP_H
#define GS_STARTUP_H
#include "gs_protocol.h"

#define GS_BOOT_SETTLE_US 5000000ULL
#define GS_BOOT_TRANSITION_GAP_US 20000ULL
#define GS_BOOT_REENUM_US 10000000ULL
#define GS_BOOT_INIT_GAP_US 50000ULL
#define GS_BOOT_HEARTBEAT_US 450000ULL
#define GS_BOOT_TRANSFER_US 250000ULL
#define GS_BOOT_VERIFY_US 3000000ULL
#define GS_BOOT_TOTAL_US 30000000ULL
#define GS_BOOT_FRESH_US 1000000ULL

enum gs_boot_state {
	GS_BOOT_IDLE, GS_BOOT_TRANSITION, GS_BOOT_WAIT_REMOVE, GS_BOOT_WAIT_ADD,
	GS_BOOT_INITIALIZE, GS_BOOT_VERIFY, GS_BOOT_READY, GS_BOOT_HANDED_OFF,
	GS_BOOT_FAILED
};

/* Adapter-supplied facts, not USB addresses or claims inferred from a PID.
 * port is an adapter-owned unique topology token, discovered at any root/hub
 * port; it is never a configured bus-port number such as "8-6". The adapter
 * must include root/parent-hub lifetimes so replacing a hub cannot alias it.
 * instance identifies one enumeration lifetime. Never recycle a token for an
 * unrelated topology/enumeration. Serials need not be equal across modes.
 * exclusive=1 means IF0 ownership has already been established by the adapter.
 * The core neither claims interfaces nor loads modules, opens devices or binds.
 */
struct gs_boot_device {
	gs_u64 port, instance, enumerated_us;
	unsigned int vid, pid, configuration, interface_number, altsetting;
	unsigned int interface_class, subclass, protocol;
	unsigned int in_ep, out_ep, in_type, out_type, in_size, out_size;
	unsigned int in_interval, out_interval, exclusive;
};

struct gs_boot_tx {
	gs_u64 port, instance;
	unsigned int token, length, endpoint;
	gs_u8 data[64];
};

/* Zero-initialize once per explicitly authorized attempt; serialize all calls.
 * Keep this coordinator alive across the old device's disconnect. Consume each
 * returned TX exactly once and report its completion before another TX. Monitor
 * removals independently; an unexpected ordering/error is terminal, no retry.
 * All timestamps are from ONE monotonic microsecond clock, including RX.
 */
struct gs_startup {
	int state, error, failed_stage;
	struct gs_boot_device device;
	gs_u64 old_instance, now_us, deadline_us, phase_deadline_us, due_us;
	gs_u64 transfer_deadline_us, imu_us, removed_us;
	unsigned int step, token, pending_length, sequence;
	unsigned int transition_completed, native_output_started;
	unsigned int pad_seen, imu_seen;
};

struct gs_boot_handoff {
	gs_u64 port, instance, next_heartbeat_us;
	unsigned int sequence, pad_seen, imu_seen;
};

/* Port-independent candidate recognition from adapter-supplied descriptors.
 * No claim, activation or identity proof; ownership is checked at begin/arrived.
 * An unrequested 109c candidate must never be adopted by a pending transition
 * on another port. One independent coordinator is needed per selected device.
 */
int gs_boot_supported(const struct gs_boot_device *device);
/* Deadline supervision without generating a TX intent; caller serializes. */
int gs_boot_poll(struct gs_startup *s, gs_u64 now_us);
/* Preserve a transport/adapter failure; completed handoff is immutable. */
void gs_boot_abort(struct gs_startup *s, int error);
/* 100a transitions to correlated 109c; experimental 105e initializes the
 * same owned instance directly, sharing init/verification/handoff unchanged.
 */
int gs_boot_begin(struct gs_startup *s, const struct gs_boot_device *device,
		  int authorized, gs_u64 now_us);
/* 1: one new TX intent; 0: wait/no TX; negative: terminal failure.
 * Fresh device identity/ownership is required whenever the device is present.
 * Call even while waiting so deadlines are enforced; zeroed out on no TX.
 */
int gs_boot_next(struct gs_startup *s, const struct gs_boot_device *device,
		 gs_u64 now_us, struct gs_boot_tx *out);
int gs_boot_complete(struct gs_startup *s, const struct gs_boot_device *device,
		     unsigned int token, int status, unsigned int actual,
		     gs_u64 now_us);
int gs_boot_removed(struct gs_startup *s, gs_u64 port, gs_u64 instance,
		    gs_u64 now_us);
int gs_boot_arrived(struct gs_startup *s, const struct gs_boot_device *device,
		    gs_u64 now_us);
/* Only valid current-enumeration IN packets count as liveness. No gyro units. */
int gs_boot_input(struct gs_startup *s, const struct gs_boot_device *device,
		  unsigned int endpoint, int status, const gs_u8 *data,
		  size_t length, gs_u64 now_us);
/* READY requires completed initialization and fresh IMU. pad_seen is separate:
 * GIP can be quiet without user input. Transfer sequence ownership exactly once.
 */
int gs_boot_takeover(struct gs_startup *s, const struct gs_boot_device *device,
		     gs_u64 now_us,
		     struct gs_boot_handoff *out);
void gs_boot_cancel(struct gs_startup *s);
#endif
