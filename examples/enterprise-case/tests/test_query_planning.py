"""Plan cost never substitutes for authorized, current evidence."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from context_flow import ContextFlow
from northstar import Principal
from query_planning import candidate_plans, choose_plan, compare_refund_plans, REQUIRED_IDS
from workbench import Workspace


class QueryPlanningTest(unittest.TestCase):
    def setUp(self):
        self.workspace = Workspace()
        self.platform = self.workspace.platform
        self.actor = self.workspace.principal("sre")

    def compare(self, **kwargs):
        return self.workspace.dispatch({"op": "planning", "role": "sre", **kwargs})["plan_comparison"]

    def test_both_routes_cover_same_requirements_with_fewer_reads(self):
        before = self.workspace.snapshot()
        result = self.compare()
        self.assertEqual(before, self.workspace.snapshot())
        self.assertEqual("directed", result["selected"])
        broad, directed = result["plans"]
        for plan in result["plans"]:
            self.assertEqual("evidence_ready", plan["status"])
            self.assertEqual(842, plan["package"]["observations"][0]["queue_depth"])
            ids = {item["id"] for item in plan["package"]["evidence"]}
            self.assertTrue(set(REQUIRED_IDS) <= ids)
            self.assertEqual(len(ids), len(plan["package"]["evidence"]))
        self.assertLess(directed["execution"]["tool_calls"], broad["execution"]["tool_calls"])
        self.assertLess(directed["execution"]["returned_items"], broad["execution"]["returned_items"])
        self.assertEqual(broad["coverage"], directed["coverage"])
        self.assertFalse(result["business_task_completed"])
        # Reports do not expose mutable platform state.
        directed["package"]["observations"][0]["queue_depth"] = 0
        self.assertEqual(before, self.workspace.snapshot())

    def test_budget_filters_before_execution_and_counts_only_executed_steps(self):
        with patch.object(ContextFlow, "read", side_effect=AssertionError("no reads allowed")):
            result = self.compare(estimated_budget=20)
        self.assertIsNone(result["selected"])
        self.assertEqual("budget_insufficient", result["status"])
        with patch.object(ContextFlow, "read", autospec=True, side_effect=ContextFlow.read) as reads:
            result = self.compare(estimated_budget=30)
        self.assertEqual("not_run", result["plans"][0]["status"])
        self.assertEqual(["trace", "lookup", "observe"], [call.args[1] for call in reads.call_args_list])

    def test_choice_depends_on_estimates_not_a_hardcoded_winner(self):
        plans = candidate_plans()
        for step in plans[0]["steps"]:
            step["estimated_units"] = 1
        self.assertEqual("broad", choose_plan(plans, 60)["selected"])

    def test_invalid_budgets_are_rejected(self):
        for budget in (True, 0, -1, 1001, 1.5, "30", None):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                self.compare(estimated_budget=budget)

    def test_missing_relation_cannot_be_hidden_by_successful_search(self):
        self.platform.edges = [edge for edge in self.platform.edges if edge["type"] != "CHECKS_POLICY"]
        result = self.compare()
        self.assertEqual("incomplete", result["status"])
        for plan in result["plans"]:
            self.assertFalse(plan["coverage"]["checks"][1]["met"])
            self.assertTrue(plan["package"]["missing"])

    def test_expired_observation_is_not_replaced_by_history(self):
        self.workspace.dispatch({"op": "clock.advance", "role": "sre"})
        for plan in self.compare()["plans"]:
            self.assertEqual("incomplete", plan["status"])
            self.assertEqual([], plan["package"]["observations"])
            self.assertFalse(plan["coverage"]["checks"][2]["met"])

    def test_role_and_tenant_boundaries_apply_to_both_plans(self):
        for actor in (Principal("dev", "developer"), Principal("support", "support"),
                      Principal("sre", "sre", "other")):
            result = compare_refund_plans(self.platform, actor)["plan_comparison"]
            for plan in result["plans"]:
                self.assertEqual("incomplete", plan["status"])
                self.assertEqual([], plan["package"]["observations"])
                ids = {item["id"] for item in plan["package"]["evidence"]}
                authorized = {doc["id"] for doc in self.platform.current_documents(actor)}
                self.assertTrue(ids <= authorized)
                for edge in plan["package"]["relations"]:
                    self.assertTrue({edge["from"], edge["to"]} <= authorized)

    def test_lookup_obeys_time_and_scope_mismatch_blocks_coverage(self):
        flow = ContextFlow(self.platform)
        result = flow.read("lookup", {"ids": REQUIRED_IDS, "observed_at": "2020-01-01T00:00:00Z"}, self.actor)
        self.assertEqual([], result["evidence"])
        self.platform.by_id["deployment-refund-eu"]["attributes"]["environment"] = "other-environment"
        self.assertEqual("incomplete", self.compare()["status"])

if __name__ == "__main__":
    unittest.main()
