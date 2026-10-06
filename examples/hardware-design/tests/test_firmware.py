import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from firmware_model import Device, MemoryJournal, Receiver
from check_design import inputs_digest
from simulate_firmware import scenarios


class FirmwareBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.policy = {"queue_capacity": 32, "retry_delays_s": [10, 20]}
        self.store = MemoryJournal()
        self.receiver = Receiver()

    def device(self, receiver=None, sensor=None, start=0):
        return Device(self.store, sensor or (lambda now: (22.0, 55.0)),
                      receiver or self.receiver, 60, 300, self.policy, start)

    def sample_to(self, device, end):
        while device.next_wakeup() <= end:
            device.tick(device.next_wakeup())

    def test_normal_batch_includes_sample_at_upload_deadline(self):
        device = self.device()
        self.sample_to(device, 300)
        self.assertEqual([r["time_s"] for r in self.receiver.received.values()], [60, 120, 180, 240, 300])
        self.assertEqual(self.receiver.attempts, 1)
        self.assertEqual(self.store.records, [])
        self.assertEqual(device.next_wakeup(), 360)

    def test_lost_ack_retries_same_records_without_double_counting(self):
        receiver = Receiver(["lost_ack", "ack"])
        device = self.device(receiver)
        self.sample_to(device, 300)
        self.assertEqual(len(self.store.records), 5)
        self.assertEqual(device.next_wakeup(), 310)
        device.tick(310)
        self.assertEqual(len(receiver.received), 5)
        self.assertEqual(receiver.duplicates, 5)
        self.assertEqual(self.store.records, [])

    def test_offline_retry_budget_and_next_period(self):
        receiver = Receiver(default="offline")
        device = self.device(receiver)
        self.sample_to(device, 599)
        self.assertEqual(receiver.attempts, 3)
        self.assertEqual([t for t, event in device.events if event == "unconfirmed_attempt"], [300, 310, 330])
        self.assertEqual(len(self.store.records), 9)
        receiver.default = "ack"
        device.tick(600)
        self.assertEqual(len(receiver.received), 10)
        self.assertEqual(self.store.records, [])

    def test_wrong_ack_does_not_clear_queue(self):
        receiver = Receiver(default="wrong_ack")
        device = self.device(receiver)
        self.sample_to(device, 330)
        self.assertEqual(len(self.store.records), 5)
        self.assertEqual(device.attempts_in_window, 3)

    def test_ack_for_wrong_sequence_does_not_clear_queue(self):
        class WrongSequence(Receiver):
            def send(self, batch):
                device_id, sequence = super().send(batch)
                return device_id, sequence + 1

        self.sample_to(self.device(WrongSequence()), 300)
        self.assertEqual(len(self.store.records), 5)

    def test_restart_retains_sequence_and_unconfirmed_records(self):
        receiver = Receiver(["lost_ack"])
        self.sample_to(self.device(receiver), 300)
        self.sample_to(self.device(receiver, start=300), 600)
        self.assertEqual(len(receiver.received), 10)
        self.assertEqual(receiver.duplicates, 5)
        self.assertEqual(self.store.next_sequence, 11)
        self.assertEqual(self.store.records, [])

    def test_nonboundary_restart_sends_saved_records_without_waiting_a_period(self):
        self.sample_to(self.device(Receiver(default="offline")), 240)
        device = self.device(start=299)
        self.assertEqual(device.next_wakeup(), 299)
        device.tick(299)
        self.assertEqual(len(self.receiver.received), 4)
        self.assertEqual(self.store.records, [])
        # Sampling restarts after a full period; reboot downtime is not a continuous-cadence guarantee.
        self.assertEqual(device.next_sample, 359)

    def test_failure_after_remote_ack_does_not_erase_local_batch(self):
        journal = self.store

        class CutAfterAck(Receiver):
            def send(self, batch):
                ack = super().send(batch)
                journal.fail_next_write = True
                return ack

        cut = CutAfterAck()
        device = self.device(cut)
        self.sample_to(device, 240)
        with self.assertRaises(OSError):
            device.tick(300)
        self.assertEqual(len(self.store.records), 5)
        self.assertEqual(self.store.next_sequence, 6)
        recovered = Receiver()
        recovered.received = cut.received.copy()
        self.sample_to(self.device(recovered, start=300), 600)
        self.assertEqual(len(recovered.received), 10)
        self.assertEqual(recovered.duplicates, 5)

    def test_failed_sample_commit_keeps_old_journal(self):
        self.store.fail_next_write = True
        device = self.device()
        with self.assertRaises(OSError):
            device.tick(60)
        self.assertEqual(self.store.records, [])
        self.assertEqual(self.store.next_sequence, 1)
        self.assertEqual(self.receiver.attempts, 0)

    def test_queue_full_is_visible_and_preserves_unconfirmed_records(self):
        receiver = Receiver(default="offline")
        device = self.device(receiver)
        self.sample_to(device, 33 * 60)
        self.assertEqual(len(self.store.records), 32)
        self.assertEqual(self.store.records[0]["sequence"], 1)
        self.assertEqual(self.store.records[-1]["sequence"], 32)
        self.assertEqual(device.queue_full_events, 1)
        self.assertIn((1980, "queue_full"), device.events)

    def test_sensor_failure_does_not_create_zero_measurement(self):
        for reading in (None, (float("nan"), 20), (True, 30), (1 << 10000, 20)):
            device = self.device(sensor=lambda now: reading)
            device.tick(60)
            self.assertEqual(device.sensor_errors, 1)
            self.assertEqual(self.store.records, [])

    def test_sensor_io_error_is_reported(self):
        def failed_read(now):
            raise OSError("sensor timeout")

        device = self.device(sensor=failed_read)
        device.tick(60)
        self.assertEqual(device.sensor_errors, 1)
        self.assertEqual(self.store.records, [])

    def test_delayed_scheduler_does_not_fabricate_historical_samples(self):
        device = self.device()
        device.tick(300)
        self.assertEqual(device.missed_samples, 4)
        self.assertEqual([r["time_s"] for r in self.receiver.received.values()], [300])
        with self.assertRaisesRegex(ValueError, "backwards"):
            device.tick(299)

    def test_new_samples_during_retry_are_not_cleared_by_old_batch_ack(self):
        self.policy["retry_delays_s"] = [70, 80]
        receiver = Receiver(["lost_ack", "ack"])
        device = self.device(receiver)
        self.sample_to(device, 370)
        self.assertEqual([r["sequence"] for r in self.store.records], [6])
        self.assertEqual(len(receiver.received), 5)

    def test_cli_scenarios_and_verification_boundary(self):
        result = subprocess.run([sys.executable, str(ROOT / "simulate_firmware.py")],
                                cwd=ROOT.parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["normal"]["unique_records"], 10)
        self.assertEqual(report["normal"]["send_attempts"], 2)
        self.assertEqual(report["normal"]["pending"], 0)
        self.assertTrue(report["normal"]["sample_quality"]["all_scheduled_samples_retained"])
        self.assertEqual(report["lost_ack_then_restart"]["duplicate_deliveries"], 5)
        self.assertEqual(report["offline_first_window"]["send_attempts"], 3)
        self.assertFalse(report["firmware_target_verified"])
        self.assertFalse(report["production_release_allowed"])

    def test_smaller_queue_reports_offline_data_gaps_even_if_policy_checks_pass(self):
        inputs = json.loads((ROOT / "inputs.json").read_text(encoding="utf-8"))
        design = json.loads((ROOT / "design.json").read_text(encoding="utf-8"))
        inputs["firmware_policy"]["queue_capacity"] = 5
        design["input_sha256"] = inputs_digest(inputs)
        report = scenarios(inputs, design)
        quality = report["offline_first_window"]["sample_quality"]
        self.assertTrue(report["host_scenarios_passed"])
        self.assertEqual(quality["queue_full_events"], 4)
        self.assertEqual(quality["data_gaps"], 4)
        self.assertFalse(quality["all_scheduled_samples_retained"])


if __name__ == "__main__":
    unittest.main()
