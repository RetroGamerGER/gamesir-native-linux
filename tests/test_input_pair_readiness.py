#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Pure offline gate tests; no device enumeration, service calls or writes."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/sdl"))
from input_pair_readiness import Action, Binding, PublicationGate, Sensor


class Readiness(unittest.TestCase):
    def setUp(self):
        self.binding = Binding("hub-life-1", "kernel-instance-8", "/fixture/2-3.4:1.0", "gsn-test-8")
        self.sensor = Sensor(self.binding, "input-life-1", "input-life-1", True,
                             (100, 100, 100), (8192, 8192, 8192))
        self.gate = PublicationGate(self.binding, 10)

    def test_missing_sensor_waits_without_publishing(self):
        self.assertEqual(self.gate.observe(self.binding, None, 10).action, Action.WAIT)

    def test_node_creation_is_not_processed_hotplug(self):
        sensor = replace(self.sensor, processed_node_token="")
        self.assertEqual(self.gate.observe(self.binding, sensor, 10.1).action, Action.WAIT)

    def test_old_processed_event_cannot_validate_reused_event_number(self):
        sensor = replace(self.sensor, node_token="input-life-2")
        self.assertEqual(self.gate.observe(self.binding, sensor, 10.1).action, Action.WAIT)

    def test_processed_but_inaccessible_sensor_waits(self):
        sensor = replace(self.sensor, readable=False)
        self.assertEqual(self.gate.observe(self.binding, sensor, 10.2).action, Action.WAIT)

    def test_exact_ready_pair_can_be_published_only_once_after_acknowledgement(self):
        result = self.gate.observe(self.binding, self.sensor, 10.3)
        self.assertEqual(result.action, Action.PUBLISH)
        self.assertFalse(self.gate.published)  # Plan is not claimed success.
        self.gate.acknowledge(self.binding, result.sensor_node_token)
        self.assertEqual(self.gate.observe(self.binding, self.sensor, 12).action, Action.DONE)
        with self.assertRaises(ValueError):
            self.gate.acknowledge(self.binding, result.sensor_node_token)

    def test_proposal_is_revoked_by_next_inaccessible_snapshot(self):
        self.gate.observe(self.binding, self.sensor, 10.3)
        self.gate.observe(self.binding, replace(self.sensor, readable=False), 10.4)
        with self.assertRaises(ValueError):
            self.gate.acknowledge(self.binding, self.sensor.node_token)

    def test_removed_or_replaced_binding_aborts_and_never_adopts_it(self):
        for current in (None, replace(self.binding, instance_token="kernel-instance-9"),
                        replace(self.binding, parent_token="replacement-hub"),
                        replace(self.binding, interface_path="/fixture/9-2:1.0")):
            with self.subTest(current=current):
                gate = PublicationGate(self.binding, 10)
                self.assertEqual(gate.observe(current, self.sensor, 10.5).action, Action.ABORT)
                self.assertEqual(gate.observe(self.binding, self.sensor, 10.6).action, Action.ABORT)

    def test_same_usb_pid_is_not_individual_identity(self):
        second = replace(self.binding, interface_path="/fixture/9-1:1.0", uniq="gsn-test-other")
        self.assertEqual(self.gate.observe(self.binding, replace(self.sensor, binding=second), 10.5).action,
                         Action.ABORT)

    def test_timeout_is_terminal_even_if_sensor_arrives_later(self):
        self.assertEqual(self.gate.observe(self.binding, None, 13).action, Action.ABORT)
        self.assertEqual(self.gate.observe(self.binding, self.sensor, 14).action, Action.ABORT)

    def test_deadline_cannot_be_extended_by_duplicate_events(self):
        for now in (10.1, 11, 12.9):
            self.assertEqual(self.gate.observe(self.binding, None, now).action, Action.WAIT)
        self.assertEqual(self.gate.observe(self.binding, self.sensor, 13).action, Action.ABORT)

    def test_incomplete_or_invalid_motion_profile_does_not_fake_gyro(self):
        for values in ((0, 0, 0), (100, 100), (100, -1, 100), (True, 100, 100)):
            for field in ("gyro_resolution", "accel_resolution"):
                with self.subTest(field=field, values=values):
                    gate = PublicationGate(self.binding, 10)
                    sensor = replace(self.sensor, **{field: values})
                    self.assertEqual(gate.observe(self.binding, sensor, 10.5).action, Action.ABORT)

    def test_bad_clocks_and_limits_are_rejected(self):
        for timeout in (0, -1, 11, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                PublicationGate(self.binding, 10, timeout)
        for now in (9, float("nan"), float("inf")):
            gate = PublicationGate(self.binding, 10)
            self.assertEqual(gate.observe(self.binding, self.sensor, now).action, Action.ABORT)

    def test_no_acknowledgement_from_wrong_session_or_node(self):
        self.gate.observe(self.binding, self.sensor, 10.3)
        for binding, token in ((replace(self.binding, instance_token="other"), self.sensor.node_token),
                               (self.binding, "another-node")):
            with self.assertRaises(ValueError):
                self.gate.acknowledge(binding, token)

    def test_new_binding_needs_a_new_gate(self):
        self.gate.observe(None, None, 11)
        new = replace(self.binding, instance_token="kernel-instance-9", uniq="gsn-test-9")
        gate = PublicationGate(new, 20)
        sensor = replace(self.sensor, binding=new, node_token="new-input", processed_node_token="new-input")
        self.assertEqual(gate.observe(new, sensor, 20.2).action, Action.PUBLISH)

    def test_arbitrary_ports_and_hubs(self):
        for path in ("/fixture/1-1:1.0", "/fixture/4-3.2.1:1.0"):
            binding = replace(self.binding, interface_path=path)
            gate = PublicationGate(binding, 0)
            self.assertEqual(gate.observe(binding, replace(self.sensor, binding=binding), 0.1).action,
                             Action.PUBLISH)


if __name__ == "__main__":
    unittest.main()
