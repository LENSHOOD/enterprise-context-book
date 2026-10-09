"""Different tasks share execution and assembly without sharing permissions."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from context_flow import ContextFlow
from northstar import NorthstarPlatform, Principal


class ContextFlowTest(unittest.TestCase):
    def setUp(self):
        self.p = NorthstarPlatform()
        self.question = "H2 销售为什么比 H1 差"

    def test_three_tasks_execute_plans_and_share_package_fields(self):
        cases = [("developer", "修改 order.cancelled", {"graph_seed": "event-order-cancelled"}, ["search", "trace"]),
                 ("sre", "退款积压", {"runtime_resource": "refund-queue"}, ["search", "observe"]),
                 ("executive", self.question, {"mode": "strategic", "definition_confirmation": self.p.strategy_context.definition_confirmation()}, ["metric"])]
        for role, question, options, expected in cases:
            with self.subTest(role=role), patch.object(ContextFlow, "read", autospec=True, side_effect=ContextFlow.read) as reads:
                package = self.p.context(question, Principal(role, role), "task", **options)
                self.assertEqual(expected, [call.args[1] for call in reads.call_args_list])
                self.assertEqual(expected, [step["tool"] for step in package["query_plan"]])
                self.assertTrue(package["evidence"])
                for key in ("principal", "task_id", "manifest", "relations", "observations", "memories", "missing", "allowed_tools"):
                    self.assertIn(key, package)

    def test_confirmation_gate_runs_before_any_metric_calculation(self):
        with patch.object(self.p.strategy_context, "_view", side_effect=AssertionError("must not calculate")):
            package = self.p.context(self.question, Principal("ceo", "executive"), "task", mode="strategic")
        self.assertEqual("needs_clarification", package["status"])
        self.assertEqual([], package["evidence"])
        self.assertNotIn("performance", package)
        self.assertEqual([], package["allowed_tools"])

    def test_common_reader_cannot_bypass_role_or_tenant(self):
        for actor in (Principal("support", "support"), Principal("other", "executive", "other")):
            with self.subTest(actor=actor), self.assertRaises(PermissionError):
                ContextFlow(self.p).read("metric", {"question": self.question}, actor)
        self.assertEqual([], ContextFlow(self.p).read("observe", {"resource": "refund-queue"}, Principal("dev", "developer"))["observations"])

    def test_shared_flow_preserves_missing_and_disabled_channels(self):
        package = self.p.context("退款", Principal("dev", "developer"), "task",
                                 runtime_resource="refund-queue", disabled_channels={"bm25", "semantic_proxy"})
        self.assertEqual([], package["evidence"])
        self.assertIn("refund-queue", package["missing"])
        self.assertEqual(["bm25", "semantic_proxy"], package["degraded_channels"])

    def test_compatibility_entry_uses_shared_flow(self):
        actor = Principal("ceo", "executive")
        with patch.object(ContextFlow, "assemble", autospec=True, side_effect=ContextFlow.assemble) as assemble:
            result = self.p.strategic_context(self.question, actor, "task")
        self.assertEqual(1, assemble.call_count)
        self.assertEqual("strategic", result["context_kind"])


if __name__ == "__main__":
    unittest.main()
