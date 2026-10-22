# SPDX-License-Identifier: GPL-2.0-only
"""Counterexamples at a static dialog boundary; NOT Nexus hardware tests."""

import unittest

from nexus_calibration_flow_model import ObservedDialog, measuring


class CalibrationFlowWitnesses(unittest.TestCase):
    def complete(self, dialog, device="device-A"):
        dialog.notification(device, active=True, left=True, right=True)

    def test_finish_is_requested_before_the_finish_button(self):
        d = measuring()
        self.complete(d)
        self.assertEqual(d.requests, [("device-A", "Start")])
        d.completion_elapsed()
        self.assertEqual(d.requests[-1], ("device-A", "Finish"))
        before = list(d.requests)
        d.close()
        self.assertEqual(d.requests, before)

    def test_one_stick_and_repeated_identical_status_do_not_finish(self):
        d = measuring()
        for _ in range(3):
            d.notification("device-A", active=True, left=True, right=False)
        d.completion_elapsed()
        self.assertEqual(d.pending_completions, 0)
        self.complete(d)
        self.complete(d)
        self.assertEqual(d.pending_completions, 1)

    def test_close_before_start_sends_nothing(self):
        d = ObservedDialog(phase=1)
        d.close()
        self.assertEqual(d.requests, [])

    def test_close_while_measuring_requests_exit(self):
        d = measuring()
        d.close()
        self.assertEqual([op for _, op in d.requests], ["Start", "Exit"])

    def test_pending_completion_survives_close(self):
        d = measuring()
        self.complete(d)
        d.close()
        d.completion_elapsed()
        self.assertFalse(d.visible)
        self.assertEqual([op for _, op in d.requests], ["Start", "Exit", "Finish"])

    def test_regressed_flags_do_not_cancel_pending_finish(self):
        d = measuring()
        self.complete(d)
        d.notification("device-A", active=True, left=False, right=False)
        d.completion_elapsed()
        self.assertEqual(d.requests[-1][1], "Finish")

    def test_inactive_status_does_not_clear_success_flags(self):
        d = measuring()
        self.complete(d)
        d.notification("device-A", active=False, left=False, right=False)
        self.assertTrue(d.left and d.right)
        self.assertEqual(d.pending_completions, 1)

    def test_hidden_preparation_can_still_start(self):
        d = ObservedDialog()
        d.change_phase(2)
        d.close()
        d.preparation_elapsed()
        self.assertEqual(d.requests, [("device-A", "Start")])
        self.assertFalse(d.visible)

    def test_back_during_delay_can_reenter_preparation(self):
        d = measuring()
        self.complete(d)
        d.change_phase(1)
        d.completion_elapsed()
        self.assertEqual(d.phase, 2)
        d.preparation_elapsed()
        self.assertEqual([op for _, op in d.requests], ["Start", "Exit", "Start"])

    def test_unfiltered_foreign_status_reaches_completion_boundary(self):
        d = measuring()
        self.complete(d, "device-B")
        d.completion_elapsed()
        self.assertEqual(d.requests[-1], ("device-A", "Finish"))

    def test_changed_selection_changes_request_target(self):
        d = measuring()
        self.complete(d)
        d.device = "device-B"
        d.completion_elapsed()
        self.assertEqual(d.requests, [("device-A", "Start"), ("device-B", "Finish")])

    def test_missing_selection_is_not_an_exit_acknowledgement(self):
        d = measuring()
        d.device = None
        with self.assertRaises(LookupError):
            d.close()
        self.assertEqual(d.requests, [("device-A", "Start")])

    def test_selection_lost_during_preparation_does_not_deliver_start(self):
        d = ObservedDialog()
        d.change_phase(2)
        d.device = None
        with self.assertRaises(LookupError):
            d.preparation_elapsed()
        self.assertEqual(d.requests, [])
        self.assertFalse(d.preparation_active)
        # UI advancement is not evidence of delivery to a controller.
        self.assertEqual(d.phase, 3)

    def test_selection_lost_before_delayed_finish_does_not_deliver_it(self):
        d = measuring()
        self.complete(d)
        d.device = None
        with self.assertRaises(LookupError):
            d.completion_elapsed()
        self.assertEqual(d.requests, [("device-A", "Start")])
        self.assertEqual(d.phase, 4)
        self.assertEqual(d.pending_completions, 0)

    def test_failed_exit_on_missing_selection_does_not_cancel_finish_timer(self):
        d = measuring()
        self.complete(d)
        d.device = None
        with self.assertRaises(LookupError):
            d.close()
        self.assertFalse(d.visible)
        self.assertEqual(d.pending_completions, 1)
        with self.assertRaises(LookupError):
            d.completion_elapsed()
        self.assertEqual(d.requests, [("device-A", "Start")])

    def test_destroy_clears_preparation_without_exit(self):
        d = ObservedDialog()
        d.change_phase(2)
        d.destroy()
        d.preparation_elapsed()
        self.assertEqual(d.requests, [])
        d = measuring()
        d.destroy()
        self.assertEqual(d.requests, [("device-A", "Start")])


if __name__ == "__main__":
    unittest.main()
