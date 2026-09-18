import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


MODULE_PATH = Path(__file__).parents[1] / "src" / "northstar.py"
SPEC = importlib.util.spec_from_file_location("northstar", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NorthstarPlatformTest(unittest.TestCase):
    def setUp(self):
        self.platform = MODULE.NorthstarPlatform()
        self.developer = MODULE.Principal("dev", "developer")
        self.support = MODULE.Principal("agent", "support")
        self.sre = MODULE.Principal("sre", "sre")

    def test_hybrid_search_returns_versioned_evidence(self):
        hits = self.platform.search("取消事件有哪些 consumer 影响", self.developer)
        self.assertTrue(hits)
        self.assertTrue(all("@" in hit["citation"] for hit in hits))
        self.assertTrue(any("semantic_proxy" in hit["channels"] for hit in hits))

    def test_acl_is_applied_before_every_search_channel(self):
        hits = self.platform.search("handle_order_cancelled consumer.py", self.support)
        self.assertNotIn("code-refund-consumer", {hit["id"] for hit in hits})

    def test_graph_traversal_does_not_cross_acl_boundary(self):
        self.assertEqual([], self.platform.trace("event-order-cancelled", self.support))
        edges = self.platform.trace("event-order-cancelled", self.developer)
        targets = {edge["to"] for edge in edges}
        self.assertIn("code-refund-consumer", targets)
        self.assertIn("code-inventory-consumer", targets)
        self.assertIn("code-notification-consumer", targets)
        self.assertNotIn("incident-refund-1042", {
            endpoint for edge in edges for endpoint in (edge["from"], edge["to"])
        })

    def test_wiki_has_lineage_and_role_specific_inputs(self):
        support_pages = self.platform.build_wiki(self.support)
        all_inputs = {item for page in support_pages for item in page["inputs"]}
        self.assertTrue(all("@" in item for item in all_inputs))
        self.assertFalse(any(item.startswith("code://") for item in all_inputs))

    def test_task_memory_is_isolated(self):
        self.platform.begin_diagnosis("INC-1", self.sre)
        self.assertEqual(1, len(self.platform.memory.read("INC-1", self.sre)))
        other_tenant = MODULE.Principal("other", "sre", "other")
        self.assertEqual([], self.platform.memory.read("INC-1", other_tenant))
        self.assertEqual([], self.platform.memory.read("INC-2", self.sre))

    def test_runtime_observation_requires_role_and_tenant(self):
        commander = MODULE.Principal("ic", "incident_commander")
        observation = self.platform.get_status("refund-queue", commander)
        self.assertEqual(842, observation["queue_depth"])
        self.assertIsNone(self.platform.get_status("refund-queue", self.support))
        other_tenant = MODULE.Principal("ic", "incident_commander", "other")
        self.assertIsNone(self.platform.get_status("refund-queue", other_tenant))

    def test_context_package_exposes_missing_runtime_data(self):
        result = self.platform.context(
            "退款积压", self.developer, "INC-3", runtime_resource="refund-queue"
        )
        self.assertEqual(["refund-queue"], result["missing"])
        self.assertEqual([], result["observations"])
        self.assertRegex(result["manifest"], r"^northstar-[0-9a-f]{12}$")

    def test_context_package_includes_the_model_slice_needed_to_interpret_evidence(self):
        result = self.platform.context(
            "修改 order.cancelled 会影响什么",
            self.developer,
            "CHANGE-1",
            graph_seed="event-order-cancelled",
            competency_question_id="CQ-EVENT-001",
        )
        contract = result["semantic_contract"]
        self.assertEqual("northstar.enterprise-context", contract["model_id"])
        self.assertEqual("CQ-EVENT-001", contract["competency_question"]["id"])
        self.assertTrue(contract["competency_coverage"]["satisfied"])
        self.assertIn("EventSchema", contract["entity_types"])
        self.assertIn("CodeSymbol", contract["entity_types"])
        self.assertIn("CONSUMED_BY", contract["relations"])
        self.assertEqual(
            "EventSchema", contract["relations"]["CONSUMED_BY"]["from"]
        )
        self.assertEqual(
            {"EventSchema", "CodeSymbol", "Test"}, set(contract["entity_types"])
        )

    def test_api_impact_question_navigates_inverse_edges_without_reversing_semantics(self):
        result = self.platform.context(
            "退款网关 API 变化会影响什么",
            self.developer,
            "CHANGE-API",
            graph_seed="api-create-refund",
            competency_question_id="CQ-IMPACT-001",
        )
        endpoints = {
            endpoint
            for edge in result["relations"]
            for endpoint in (edge["from"], edge["to"])
        }
        self.assertTrue({
            "api-create-refund",
            "service-refund-worker",
            "repo-refund-worker",
            "team-payments-oncall",
            "runbook-refund-backlog",
        }.issubset(endpoints))
        self.assertNotIn("api-risk-check", endpoints)
        self.assertEqual(
            {"CALLS", "IMPLEMENTS", "ON_CALL_FOR", "DOCUMENTED_BY"},
            {edge["type"] for edge in result["relations"]},
        )
        self.assertEqual(
            {"API", "Service", "Repository", "Team", "Runbook"},
            set(result["semantic_contract"]["entity_types"]),
        )
        call = next(edge for edge in result["relations"] if edge["type"] == "CALLS")
        self.assertEqual("service-refund-worker", call["from"])
        self.assertEqual("api-create-refund", call["to"])

    def test_unknown_competency_question_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown competency question"):
            self.platform.context(
                "test",
                self.developer,
                "CHANGE-UNKNOWN",
                graph_seed="api-create-refund",
                competency_question_id="CQ-UNKNOWN",
            )

    def test_competency_contract_is_complete_when_no_graph_query_has_run(self):
        result = self.platform.context(
            "退款网关 API 变化会影响什么",
            self.developer,
            "CHANGE-NO-GRAPH",
            competency_question_id="CQ-IMPACT-001",
        )
        contract = result["semantic_contract"]
        self.assertTrue(set(contract["competency_question"]["requiredEntityTypes"]).issubset(
            contract["entity_types"]
        ))
        self.assertTrue(set(contract["competency_question"]["requiredRelations"]).issubset(
            contract["relations"]
        ))
        self.assertEqual(
            set(contract["competency_question"]["requiredEntityTypes"]),
            set(contract["entity_types"]),
        )
        self.assertFalse(contract["competency_coverage"]["satisfied"])
        self.assertEqual([], result["relations"])

    def test_acl_blocked_question_exposes_contract_but_no_instances(self):
        result = self.platform.context(
            "退款网关 API 变化会影响什么",
            self.support,
            "CHANGE-BLOCKED",
            graph_seed="api-create-refund",
            competency_question_id="CQ-IMPACT-001",
        )
        contract = result["semantic_contract"]
        self.assertFalse(contract["competency_coverage"]["satisfied"])
        self.assertEqual([], result["relations"])
        self.assertFalse(any(
            item["id"] in {
                "api-create-refund",
                "service-refund-worker",
                "repo-refund-worker",
                "team-payments-oncall",
                "runbook-refund-backlog",
            }
            for item in result["evidence"]
        ))

    def test_context_reports_disabled_channel(self):
        result = self.platform.context(
            "退款积压", self.developer, "INC-4", disabled_channels={"semantic_proxy"}
        )
        self.assertEqual(["semantic_proxy"], result["degraded_channels"])
        self.assertTrue(all("semantic_proxy" not in hit["channels"] for hit in result["evidence"]))

    def test_bitemporal_query_selects_policy_valid_at_that_time(self):
        before_change = self.platform.documents_as_of(
            self.support,
            valid_at="2026-07-20T00:00:00Z",
            observed_at="2026-08-27T00:00:00Z",
            kinds={"policy"},
        )
        after_change = self.platform.documents_as_of(
            self.support,
            valid_at="2026-08-15T00:00:00Z",
            observed_at="2026-08-27T00:00:00Z",
            kinds={"policy"},
        )
        not_yet_ingested = self.platform.documents_as_of(
            self.support,
            valid_at="2026-07-20T00:00:00Z",
            observed_at="2026-08-26T23:59:59Z",
            kinds={"policy"},
        )
        self.assertEqual(["product-cancellation-policy-v1"], [doc["id"] for doc in before_change])
        self.assertEqual(["product-cancellation-policy"], [doc["id"] for doc in after_change])
        self.assertEqual([], not_yet_ingested)

    def test_cli_emits_role_scoped_wiki(self):
        output = subprocess.check_output(
            [sys.executable, str(MODULE_PATH), "--wiki", "--role", "support"],
            text=True,
        )
        pages = json.loads(output)
        inputs = {item for page in pages for item in page["inputs"]}
        self.assertTrue(pages)
        self.assertFalse(any(item.startswith("code://") for item in inputs))

    def test_time_demo_exposes_both_time_axes(self):
        output = subprocess.check_output(
            [sys.executable, str(MODULE_PATH.parents[0] / "time_demo.py")],
            text=True,
        )
        result = json.loads(output)
        self.assertEqual(["product-cancellation-policy-v1"], result["before_policy_change"])
        self.assertEqual(["product-cancellation-policy"], result["after_policy_change"])
        self.assertEqual([], result["not_yet_ingested"])


if __name__ == "__main__":
    unittest.main()
