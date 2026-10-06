"""Run W2 host behavior scenarios using the version-bound design inputs."""

import argparse
import json
from pathlib import Path

from check_design import evaluate
from firmware_model import Device, MemoryJournal, Receiver


def sample_quality(expected, *devices):
    names = ("sampling_opportunities", "samples_committed", "queue_full_events",
             "missed_samples", "sensor_errors")
    report = {name: sum(getattr(device, name) for device in devices) for name in names}
    gaps = report["queue_full_events"] + report["missed_samples"] + report["sensor_errors"]
    if report["sampling_opportunities"] != expected or report["samples_committed"] + gaps != expected:
        raise ValueError("sample accounting invariant failed")
    return {**report, "data_gaps": gaps, "all_scheduled_samples_retained": gaps == 0}


def scenarios(inputs, design):
    checked = evaluate(inputs, design)
    if not checked["checks_passed"]:
        raise ValueError("design must pass the input, timing and budget checks first")
    sample_s, upload_s = design["sample_period_s"], design["upload_period_s"]

    def make(journal, receiver, start=0):
        return Device(journal, lambda now: (22.0, 55.0), receiver, sample_s,
                      upload_s, inputs["firmware_policy"], start)

    def run_until(device, end):
        while device.next_wakeup() <= end:
            device.tick(device.next_wakeup())

    normal_store, normal_receiver = MemoryJournal(), Receiver()
    normal = make(normal_store, normal_receiver)
    run_until(normal, upload_s * 2)

    store, receiver = MemoryJournal(), Receiver(outcomes=["lost_ack"])
    before_restart = make(store, receiver)
    run_until(before_restart, upload_s)
    pending_before_restart = len(store.records)
    after_restart = make(store, receiver, start=upload_s)
    run_until(after_restart, upload_s * 2)

    offline_store, offline_receiver = MemoryJournal(), Receiver(default="offline")
    offline = make(offline_store, offline_receiver)
    run_until(offline, upload_s * 2 - 1)
    normal_quality = sample_quality(upload_s * 2 // sample_s, normal)
    recovery_quality = sample_quality(2 * (upload_s // sample_s), before_restart, after_restart)
    offline_quality = sample_quality((upload_s * 2 - 1) // sample_s, offline)
    if (len(normal_receiver.received) != normal_quality["samples_committed"]
            or len(receiver.received) != recovery_quality["samples_committed"]
            or len(offline_store.records) != offline_quality["samples_committed"]):
        raise ValueError("committed records are not accounted for")
    if (normal_store.records or store.records or pending_before_restart == 0
            or receiver.duplicates != pending_before_restart
            or offline_receiver.attempts != 1 + len(inputs["firmware_policy"]["retry_delays_s"])):
        raise ValueError("host scenario invariant failed")
    return {
        "design_id": design["design_id"], "input_snapshot": inputs["snapshot"],
        "software_source": inputs["firmware_policy"]["source_ref"],
        "host_scenarios_passed": True,
        "normal": {"unique_records": len(normal_receiver.received),
                   "send_attempts": normal_receiver.attempts, "pending": len(normal_store.records),
                   "sample_quality": normal_quality},
        "lost_ack_then_restart": {"pending_at_restart": pending_before_restart,
                                  "unique_records": len(receiver.received),
                                  "duplicate_deliveries": receiver.duplicates,
                                  "pending": len(store.records), "sample_quality": recovery_quality,
                                  "restart_schedule_gap": (upload_s * 2 // sample_s) - 2 * (upload_s // sample_s)},
        "offline_first_window": {"send_attempts": offline_receiver.attempts,
                                 "pending": len(offline_store.records), "sample_quality": offline_quality},
        "firmware_target_verified": False, "physical_verified": False,
        "production_release_allowed": False,
        "limits": "Host logic only. Atomic journal commits and whole-batch acknowledgements are assumed; no drivers, flash, RTOS, RF or power behavior tested.",
    }


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=root / "inputs.json")
    parser.add_argument("--design", type=Path, default=root / "design.json")
    args = parser.parse_args()
    try:
        result = scenarios(json.loads(args.inputs.read_text(encoding="utf-8")),
                           json.loads(args.design.read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"status": "invalid_input", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
