import copy
import importlib.util
import json
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("hardware_design_checker", ROOT / "check_design.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class HardwareDesignTest(unittest.TestCase):
    def setUp(self):
        self.inputs = json.loads((ROOT / "inputs.json").read_text(encoding="utf-8"))
        self.design = json.loads((ROOT / "design.json").read_text(encoding="utf-8"))

    def test_budget_alternatives_and_physical_boundary(self):
        result = CHECKER.evaluate(self.inputs, self.design)
        rows = {r["radio"]: r for r in result["alternatives"]}
        self.assertEqual(Decimal(rows["RADIO-A"]["average_current_uA"]), Decimal("117.2"))
        self.assertEqual(Decimal(rows["RADIO-A"]["required_capacity_mAh"]), Decimal("2053.344"))
        self.assertFalse(rows["RADIO-A"]["power_budget_pass"])
        self.assertEqual(Decimal(rows["RADIO-B"]["average_current_uA"]), Decimal("57.2"))
        self.assertEqual(Decimal(rows["RADIO-B"]["required_capacity_mAh"]), Decimal("1002.144"))
        self.assertEqual(Decimal(rows["RADIO-B"]["bom_cny"]), Decimal("72"))
        self.assertTrue(result["checks_passed"])
        self.assertFalse(result["physical_verified"])
        self.assertFalse(result["production_release_allowed"])
        self.assertEqual(result["requirements_traced"], 6)
        self.assertEqual(result["software_requirements_traced"], 4)
        self.assertTrue(result["open_items"])

    def test_cheaper_radio_is_not_accepted_if_power_budget_fails(self):
        self.design["selected_radio"] = "RADIO-A"
        result = CHECKER.evaluate(self.inputs, self.design)
        self.assertFalse(result["checks_passed"])
        self.assertEqual(result["status"], "draft_needs_revision")

    def test_longer_upload_interval_cannot_hide_requirement_violation(self):
        self.design["selected_radio"] = "RADIO-A"
        self.design["upload_period_s"] = 600
        result = CHECKER.evaluate(self.inputs, self.design)
        self.assertTrue(result["alternatives"][0]["power_budget_pass"])
        self.assertFalse(result["timing_configuration_pass"])
        self.assertFalse(result["checks_passed"])

    def test_source_change_invalidates_draft_even_if_snapshot_label_unchanged(self):
        self.inputs["capacity"]["available_mAh"] = 800
        with self.assertRaisesRegex(ValueError, "input content changed"):
            CHECKER.evaluate(self.inputs, self.design)

    def test_rebased_context_recomputes_budget_after_capacity_change(self):
        self.inputs["snapshot"] = "w2-inputs-r3"
        self.inputs["capacity"]["available_mAh"] = 800
        self.inputs["capacity"]["source_ref"] = "CAPACITY@r2"
        for source in self.inputs["sources"]:
            if source["ref"] == "CAPACITY@r1":
                source["ref"] = "CAPACITY@r2"
        self.design["source_refs"] = ["CAPACITY@r2" if ref == "CAPACITY@r1" else ref for ref in self.design["source_refs"]]
        self.design["input_snapshot"] = self.inputs["snapshot"]
        self.design["input_sha256"] = CHECKER.inputs_digest(self.inputs)
        result = CHECKER.evaluate(self.inputs, self.design)
        self.assertFalse(result["checks_passed"])

    def test_missing_or_unknown_source_reference_is_rejected(self):
        for refs in [self.design["source_refs"][:-1], self.design["source_refs"] + ["RADIO-B@unknown"]]:
            design = copy.deepcopy(self.design)
            design["source_refs"] = refs
            with self.assertRaisesRegex(ValueError, "source reference"):
                CHECKER.evaluate(self.inputs, design)

    def test_missing_requirement_or_broken_verification_link_is_rejected(self):
        self.design["traceability"].pop()
        with self.assertRaisesRegex(ValueError, "every requirement"):
            CHECKER.evaluate(self.inputs, self.design)
        self.setUp()
        self.design["traceability"][0]["verification_id"] = "NONEXISTENT"
        with self.assertRaisesRegex(ValueError, "unresolved"):
            CHECKER.evaluate(self.inputs, self.design)

    def test_planned_tests_cannot_be_marked_passed_without_hardware_results(self):
        self.design["verification_plan"][0]["status"] = "passed"
        with self.assertRaisesRegex(ValueError, "physical verification"):
            CHECKER.evaluate(self.inputs, self.design)

    def test_invalid_periods_and_current_reference_are_rejected(self):
        for value in [0, -1, "NaN", True]:
            design = copy.deepcopy(self.design)
            design["sample_period_s"] = value
            with self.assertRaises(ValueError):
                CHECKER.evaluate(self.inputs, design)
        self.inputs["power"]["reference"] = "sensor_output"
        self.design["input_sha256"] = CHECKER.inputs_digest(self.inputs)
        with self.assertRaisesRegex(ValueError, "power reference"):
            CHECKER.evaluate(self.inputs, self.design)

    def test_cli_works_outside_fixture_directory(self):
        result = subprocess.run([sys.executable, str(ROOT / "check_design.py")], cwd=ROOT.parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "draft_ready_for_review")

    def test_missing_input_source_is_rejected_after_rebinding(self):
        records = self.inputs["requirements"] + self.inputs["radios"]
        records += [self.inputs["capacity"], self.inputs["power"], self.inputs["bom_base"], self.inputs["firmware_policy"]]
        for record in records:
            ref = record.pop("source_ref")
            self.design["input_sha256"] = CHECKER.inputs_digest(self.inputs)
            with self.assertRaisesRegex(ValueError, "source reference"):
                CHECKER.evaluate(self.inputs, self.design)
            record["source_ref"] = ref

    def test_design_names_without_content_do_not_pass(self):
        for sections in [list(self.design["sections"]), {**self.design["sections"], "interfaces": " "}]:
            design = copy.deepcopy(self.design)
            design["sections"] = sections
            with self.assertRaises(ValueError):
                CHECKER.evaluate(self.inputs, design)

    def test_missing_verification_method_and_invalid_open_items_are_rejected(self):
        self.design["verification_plan"][0].pop("method")
        with self.assertRaisesRegex(ValueError, "verification method"):
            CHECKER.evaluate(self.inputs, self.design)
        self.setUp()
        for value in ["done", [], [""]]:
            self.design["open_items"] = value
            with self.assertRaisesRegex(ValueError, "open items"):
                CHECKER.evaluate(self.inputs, self.design)

    def test_extreme_number_returns_cli_input_error_json(self):
        self.design["sample_period_s"] = "1e-1000000"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "design.json"
            path.write_text(json.dumps(self.design), encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "check_design.py"), "--design", str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid_input")
        self.assertNotIn("Traceback", result.stderr)

    def test_software_policy_and_allocation_are_checked(self):
        for wrong in ("MISSING", "V-COST"):
            self.design["software_traceability"][0]["verification_id"] = wrong
            with self.assertRaisesRegex(ValueError, "unresolved software"):
                CHECKER.evaluate(self.inputs, self.design)
        self.setUp()
        for policy in [
            {"queue_capacity": 4, "retry_delays_s": [10, 20]},
            {"queue_capacity": 32, "retry_delays_s": [100, 200]},
            {"queue_capacity": True, "retry_delays_s": [10]},
            {"queue_capacity": 32, "retry_delays_s": [0]},
        ]:
            self.inputs["firmware_policy"] = {**policy, "source_ref": "FW-W2@r1"}
            self.design["input_sha256"] = CHECKER.inputs_digest(self.inputs)
            with self.assertRaises(ValueError):
                CHECKER.evaluate(self.inputs, self.design)

    def test_measurement_software_allocation_cannot_be_dropped(self):
        self.design["software_traceability"] = [
            row for row in self.design["software_traceability"] if row["requirement_id"] != "R-MEASUREMENT"]
        with self.assertRaisesRegex(ValueError, "software allocation"):
            CHECKER.evaluate(self.inputs, self.design)


if __name__ == "__main__":
    unittest.main()
