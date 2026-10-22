# SPDX-License-Identifier: GPL-2.0-only
PYTHON ?= python

.PHONY: test test-licensing test-public-readme test-parser test-sensor test-imu-diagnostic test-imu-stream test-iio-buffer test-protocol test-runtime test-startup test-fixtures test-capture test-sdl test-sdl-buttons analyze-imu manifest kernel kernel-analyze tools test-tools test-hardware-helper test-alpha alpha-source test-steam steam-source test-trigger-bridge trigger-bridge trigger-bridge-source

test: test-licensing test-public-readme test-parser test-sensor test-imu-diagnostic test-imu-stream test-iio-buffer test-protocol test-runtime test-startup test-fixtures test-tools test-hardware-helper test-alpha test-steam test-trigger-bridge test-control-center

# Optional desktop UI: isolated demo or unprivileged local metadata (no actions).
.PHONY: test-control-center test-control-center-ui test-control-center-package test-control-center-auth control-center-demo control-center-status control-center-rehearsal control-center-calibration
test-control-center:
	$(PYTHON) -B tests/test_control_center.py
	$(PYTHON) -B tests/test_control_center_calibration.py
	$(PYTHON) -B tests/test_calibration_controller.py
	$(PYTHON) -B tests/test_tmr_gui_path.py
	$(PYTHON) -B tests/test_control_center_status.py
	$(PYTHON) -B tests/test_control_center_backend.py
	$(PYTHON) -B tests/test_control_center_transactions.py
	$(PYTHON) -B tests/test_control_center_authorization.py
	$(PYTHON) -B tests/test_control_center_execution.py
	$(PYTHON) -B tests/test_control_center_preflight.py
	$(PYTHON) -B tests/test_control_center_app_packages.py
	$(PYTHON) -B tests/test_control_center_first_run.py
	$(PYTHON) -B tests/test_control_center_release_download.py
	$(PYTHON) -B tests/test_control_center_public_packages.py
	$(PYTHON) -B tests/test_control_center_signed_updates.py
	$(PYTHON) -B tests/test_release_key_backup.py
	$(PYTHON) -B tests/test_control_center_helper_migration.py
	$(PYTHON) -B tests/test_control_center_handover.py
	$(PYTHON) -B tests/test_control_center_release_reinstall.py
	$(PYTHON) -B tests/test_packaging_control_center.py
	$(PYTHON) -B tests/test_control_center_distribution.py
	$(PYTHON) -B tests/test_control_center_distribution_rebase.py
	$(PYTHON) -B tests/test_packaging_tmr_helper.py

test-control-center-package:
	$(PYTHON) -B tests/test_packaging_control_center.py

test-control-center-auth:
	$(PYTHON) -B tests/test_control_center_authorization.py

test-control-center-ui:
	$(PYTHON) -B tests/test_control_center_ui.py
	$(PYTHON) -B tests/test_control_center_calibration_ui.py
	$(PYTHON) -B tests/test_tmr_gui_ui.py
	$(PYTHON) -B tests/test_control_center_normal_calibration_ui.py
	$(PYTHON) -B tests/test_control_center_transactions_ui.py
	$(PYTHON) -B tests/test_control_center_execution_ui.py
	$(PYTHON) -B tests/test_control_center_app_packages_ui.py
	$(PYTHON) -B tests/test_control_center_first_run_ui.py
	$(PYTHON) -B tests/test_control_center_release_ui.py
	$(PYTHON) -B tests/test_control_center_signed_updates_ui.py
	$(PYTHON) -B tests/test_control_center_lifecycle.py

control-center-demo:
	$(PYTHON) -B tools/control_center/main.py --demo

control-center-status:
	$(PYTHON) -B tools/control_center/main.py

control-center-rehearsal:
	$(PYTHON) -B tools/control_center/main.py --rehearse-backend

control-center-calibration:
	$(PYTHON) -B tools/control_center/main.py --rehearse-calibration

# Optional research-helper tests: synthetic metadata/mocks only, no REA launch.
.PHONY: test-rea-local
test-rea-local:
	$(PYTHON) -B -m unittest discover -s tools/research/rea_local/launcher -p 'test_*.py' -v

# Optional userspace shim only; never start Wine, contact a live broker or install.
trigger-bridge:
	mkdir -p build/trigger_bridge
	$(CC) -std=c11 -Wall -Wextra -Werror -O2 -fPIC -shared tools/trigger_bridge/sdl2_hook.c -o build/trigger_bridge/libgamesir-trigger-sdl2.so -ldl -pthread -Wl,-z,relro,-z,now

test-trigger-bridge: trigger-bridge
	$(PYTHON) -B tests/test_trigger_hook.py
	$(PYTHON) -B tests/test_trigger_relay.py
	$(PYTHON) -B tests/test_trigger_relay_lifecycle.py
	$(PYTHON) -B tests/test_trigger_pipeline.py
	$(PYTHON) -B tests/test_trigger_launcher.py
	$(PYTHON) -B tests/test_packaging_trigger_bridge.py

trigger-bridge-source:
	$(PYTHON) -B scripts/package_trigger_bridge.py source --dest build/trigger-bridge-source

test-licensing:
	$(PYTHON) -B tests/test_licensing.py

test-public-readme:
	$(PYTHON) -B tests/test_public_readme.py

test-alpha:
	$(PYTHON) -B tests/test_tmr_maintenance.py
	$(PYTHON) -B tests/test_tmr_usb_framing.py
	$(PYTHON) -B tests/test_manager_standalone.py
	$(PYTHON) -B tests/test_receiver_wait.py
	$(PYTHON) -B tests/test_input_publication.py
	$(PYTHON) -B tests/test_kernel_toolchain.py
	$(PYTHON) -B tests/test_service_manager.py
	$(PYTHON) -B tests/test_manager_reconnect.py
	$(PYTHON) -B tests/test_service_client.py
	$(PYTHON) -B tests/test_service_haptics.py
	$(PYTHON) -B tests/test_packaging_alpha.py
	$(PYTHON) -B tests/test_sdl_mapping.py
	$(PYTHON) -B tests/test_steam_mapping_audit.py
	$(PYTHON) -B tests/test_steam_paddle_audit.py

# Offline artifact only; destination must be absent/empty. Never install/load.
alpha-source: tools
	$(PYTHON) -B scripts/package_alpha.py source --dest build/alpha-source

# Optional userspace integration only: never start Steam or touch a device.
test-steam:
	$(PYTHON) -B tests/test_input_pair_readiness.py
	$(PYTHON) -B tests/test_steam_gyro_observe.py
	$(PYTHON) -B tests/test_steam_gyro_terminal.py
	$(PYTHON) -B tests/test_steam_gyro_ssh.py
	$(PYTHON) -B tests/test_gamescope_identity.py
	$(PYTHON) -B tests/test_steam_session_env.py
	$(PYTHON) -B tests/test_packaging_steam.py
	$(PYTHON) -B tests/test_packaging_gamescope.py

steam-source:
	$(PYTHON) -B scripts/package_steam.py source --dest build/steam-source

test-startup:
	$(PYTHON) -B tests/run_startup_test.py
	$(PYTHON) -B tests/check_kernel_startup.py
	$(PYTHON) -B tests/check_kernel_claim.py
	$(PYTHON) -B tests/check_kernel_ff_lifetime.py

test-hardware-helper:
	$(PYTHON) -B tests/test_rf_link_capture.py
	$(PYTHON) -B tests/test_rf_link_preflight.py
	$(PYTHON) -B tests/test_hardware_test_002.py
	$(PYTHON) -B tests/test_hardware_test_003.py
	$(PYTHON) -B tests/test_bootstrap_observation.py
	$(PYTHON) -B tests/check_native_client_output.py
	$(PYTHON) -B tests/test_native_usb_capture.py
	$(PYTHON) -B tests/test_hid_sidechannel_capture.py
	$(PYTHON) -B tests/test_hid_short_capture.py

kernel:
	$(PYTHON) -B scripts/build_kernel.py

kernel-analyze: kernel
	$(PYTHON) -B scripts/analyze_kernel.py

tools:
	mkdir -p build
	clang -std=c11 -Wall -Wextra -Werror -O2 tools/native/gsnative-ctl.c -o build/gsnative-ctl

test-tools: tools
	build/gsnative-ctl --self-test

test-parser:
	cd tools/offline && $(PYTHON) -B -m unittest discover -s tests -v

test-sensor:
	$(PYTHON) -B tests/run_sensor_contract_test.py
	$(PYTHON) -B tests/check_kernel_gyro.py

test-imu-diagnostic:
	$(PYTHON) -B tests/test_imu_diagnostic.py
	$(PYTHON) -B tests/test_gyro_axis_profile.py
	$(PYTHON) -B tests/test_gyro_view_model.py
	$(PYTHON) -B tests/test_gyro_live.py

# Optional local GUI dependency: PySide6. Software/offscreen, no devices.
.PHONY: test-gyro-viewer
test-gyro-viewer:
	$(PYTHON) -B tests/test_gyro_viewer.py

test-imu-stream:
	$(PYTHON) -B tests/test_imu_stream.py
	$(PYTHON) -B tests/test_gyro_reference.py
	$(PYTHON) -B tests/test_iio_buffer_setup.py
	$(PYTHON) -B tests/test_gyro_worker.py
	$(PYTHON) -B tests/test_gyro_guided.py

test-iio-buffer:
	$(PYTHON) -B tests/check_kernel_iio_buffer.py

test-protocol:
	$(PYTHON) -B tests/run_protocol_state_test.py

test-runtime:
	$(PYTHON) -B tests/run_runtime_test.py
	$(PYTHON) -B tests/check_kernel_mapping.py
	$(PYTHON) -B tests/check_native_motor_output.py

test-fixtures:
	$(PYTHON) -B tests/check_protocol_fixtures.py

# Optional: private saved files, never live hardware.
test-capture:
	$(PYTHON) -B tests/check_capture_core.py
	$(PYTHON) -B tests/check_kernel_mapping.py --capture

# Device-free synthetic SDL tests; requires installed Bubblewrap/SDL/clang.
test-sdl: test-sdl-buttons test-sdl-hotplug
	$(PYTHON) -B tests/run_sdl_sensor_test.py

.PHONY: test-sdl-hotplug
test-sdl-hotplug:
	$(PYTHON) -B tests/run_sdl_hotplug_test.py

test-sdl-buttons:
	$(PYTHON) -B tests/run_sdl_buttons_test.py

analyze-imu:
	$(PYTHON) -B tests/analyze_imu_calibration.py

manifest:
	$(PYTHON) -B scripts/update_manifest.py
