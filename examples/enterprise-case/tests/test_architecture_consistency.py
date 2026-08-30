import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


MODULE_PATH = Path(__file__).parents[1] / "src" / "northstar.py"
SPEC = importlib.util.spec_from_file_location("northstar_architecture", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def edge_keys(records):
    return {(item["from"], item["type"], item["to"]) for item in records}


class ArchitectureConsistencyTest(unittest.TestCase):
    def setUp(self):
        self.platform = MODULE.NorthstarPlatform()

    def test_reports_confirmed_declared_only_and_evidenced_only_candidates(self):
        result = self.platform.architecture_consistency(
            MODULE.Principal("dev", "developer")
        )
        self.assertEqual(
            {("service-refund-worker", "CALLS", "api-create-refund")},
            edge_keys(result["declared_and_evidenced"]),
        )
        self.assertEqual(
            {("service-refund-worker", "CALLS", "api-legacy-refund")},
            edge_keys(result["declared_not_evidenced"]),
        )
        self.assertEqual(
            {("service-refund-worker", "CALLS", "api-risk-check")},
            edge_keys(result["evidenced_not_declared"]),
        )

    def test_keeps_claim_and_runtime_evidence_distinct(self):
        result = self.platform.architecture_consistency(
            MODULE.Principal("dev", "developer")
        )
        confirmed = result["declared_and_evidenced"][0]
        self.assertEqual("asserted", confirmed["claim_source"]["evidence_tier"])
        self.assertEqual("resolved", confirmed["evidence"][0]["evidence_tier"])
        shadow = result["evidenced_not_declared"][0]
        self.assertEqual("observed", shadow["evidence"][0]["evidence_tier"])

    def test_acl_is_applied_before_comparison(self):
        result = self.platform.architecture_consistency(
            MODULE.Principal("support", "support")
        )
        self.assertTrue(all(not records for records in result.values()))

    def test_claim_scope_excludes_unrelated_visible_calls(self):
        self.platform.documents.append(
            {
                "id": "service-out-of-scope",
                "kind": "service",
                "tenant": "northstar",
                "acl": ["developer"],
            }
        )
        self.platform.edges.append(
            {
                "from": "service-out-of-scope",
                "type": "CALLS",
                "to": "api-risk-check",
                "evidence_tier": "observed",
                "evidence": "runtime://northstar/out-of-scope#risk_check",
            }
        )
        result = self.platform.architecture_consistency(
            MODULE.Principal("dev", "developer")
        )
        all_records = [record for records in result.values() for record in records]
        self.assertNotIn("service-out-of-scope", {record["from"] for record in all_records})

    def test_optional_target_scope_limits_comparison(self):
        self.platform.architecture_claims["scope"]["to_ids"] = ["api-create-refund"]
        result = self.platform.architecture_consistency(
            MODULE.Principal("dev", "developer")
        )
        self.assertEqual(
            {("service-refund-worker", "CALLS", "api-create-refund")},
            edge_keys(result["declared_and_evidenced"]),
        )
        self.assertFalse(result["declared_not_evidenced"])
        self.assertFalse(result["evidenced_not_declared"])

    def test_asserted_relation_is_not_treated_as_implementation_evidence(self):
        self.platform.edges.append(
            {
                "from": "service-refund-worker",
                "type": "CALLS",
                "to": "api-legacy-refund",
                "evidence_tier": "asserted",
                "evidence": "knowledge://northstar/another-architecture-view#legacy_refund",
            }
        )
        result = self.platform.architecture_consistency(
            MODULE.Principal("dev", "developer")
        )
        self.assertEqual(
            {("service-refund-worker", "CALLS", "api-legacy-refund")},
            edge_keys(result["declared_not_evidenced"]),
        )

    def test_cli_emits_architecture_consistency_result(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--architecture-consistency",
                "--role",
                "developer",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(
            {("service-refund-worker", "CALLS", "api-risk-check")},
            edge_keys(result["evidenced_not_declared"]),
        )


if __name__ == "__main__":
    unittest.main()
