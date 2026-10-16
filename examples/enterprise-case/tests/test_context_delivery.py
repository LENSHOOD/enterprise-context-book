"""Contract checks across resource compilation, investigation and continuation."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from workbench import Workspace
from context_flow import ContextFlow
from context_delivery import deliver, identity, recheck_previous
from refund_records import validate_records
from intelligence import ContextAssistant


class ContextDeliveryTest(unittest.TestCase):
    def setUp(self):
        self.w = Workspace()
        self.actor = self.w.principal("sre")

    def investigate(self, **kw):
        return self.w.dispatch({"op": "discovery", "role": "sre", **kw})

    def sales_package(self, workspace=None):
        workspace = workspace or self.w
        return workspace.platform.strategic_context(
            "H2 销售为什么比 H1 差", workspace.principal("executive"),
            confirmation=workspace.platform.strategy_context.definition_confirmation())

    def assert_digest(self, package):
        self.assertEqual(package["package_digest"], identity(
            {k: v for k, v in package.items() if k != "package_digest"}))

    def test_unchanged_sales_continuation_uses_server_snapshot_and_catalog_versions(self):
        actor = self.w.principal("executive")
        package = self.sales_package()
        self.assertTrue(package["evidence"])
        for item in package["evidence"]:
            self.assertEqual(self.w.platform.by_id[item["id"]]["version"], item["version"])
        previous = deepcopy(package["continuation_input"])
        # A caller cannot choose the recheck clock or import old authority/text.
        previous.update(source_snapshot={"as_of": "1900-01-01T00:00:00Z", "acl": ["executive"]},
                        findings=[{"text": "FORGED"}])
        request = self.w.dispatch({"op": "assist.start", "role": "executive",
            "goal": "继续核对H1/H2销售", "previous_package": previous})
        report = request["continuation"]
        self.assertEqual(0, report["unavailable_count"])
        self.assertEqual(len(package["evidence"]), len(report["checked"]))
        self.assertFalse(any(item["version_changed"] for item in report["checked"]))
        self.assertFalse(report["manifest_changed"])
        self.assertNotIn("FORGED", json.dumps(report))
        self.assert_digest(package)
        # Standalone metric results must use the same adapter version scheme.
        standalone = self.w.platform.strategy_context.package(
            "H1 H2 销售", {"user_id": actor.user_id, "role": actor.role, "tenant": actor.tenant},
            confirmation=self.w.platform.strategy_context.definition_confirmation())
        self.assertEqual(package["evidence"], standalone["evidence"])

    def test_sales_continuation_checks_current_object_and_source_acl(self):
        from datetime import datetime, timezone
        from northstar import Principal
        for source_acl in (False, True):
            for at_snapshot in (False, True):
                with self.subTest(source_acl=source_acl, at_snapshot=at_snapshot):
                    workspace = Workspace()
                    package = self.sales_package(workspace)
                    previous = package["continuation_input"]
                    actor = workspace.principal("executive")
                    hidden = package["evidence"][0]["id"]
                    if source_acl:
                        workspace.platform.strategy_context.data["fixture"]["acl"] = ["revops"]
                    else:
                        workspace.platform.by_id[hidden]["acl"] = ["revops"]
                    if at_snapshot:
                        workspace.platform.clock = lambda: datetime(2027, 1, 2, tzinfo=timezone.utc)
                    report = recheck_previous(previous, workspace.platform, actor)
                    self.assertEqual(len(previous["evidence"]) if source_acl else 1,
                                     report["unavailable_count"])
                    self.assertNotIn(hidden, json.dumps(report))
                    with self.assertRaises(PermissionError):
                        self.sales_package(workspace)
                    other = recheck_previous(previous, workspace.platform,
                                             Principal("other", "executive", "other"))
                    self.assertEqual([], other["checked"])

    def test_sales_source_revision_changes_only_affected_catalog_version(self):
        previous = self.sales_package()
        saved = deepcopy(previous)
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder) / "data"
            shutil.copytree(self.w.data_dir, data)
            source = data / "strategy-context.json"
            snapshot = json.loads(source.read_text(encoding="utf-8"))
            changed = snapshot["enterprise_profiles"][0]
            changed["name"] += " updated"
            source.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
            current = Workspace(data_dir=data)
            report = recheck_previous(previous["continuation_input"], current.platform,
                                      current.principal("executive"))
            self.assertTrue(report["manifest_changed"])
            self.assertEqual(0, report["unavailable_count"])
            self.assertEqual([changed["id"]],
                             [item["id"] for item in report["checked"] if item["version_changed"]])
            fresh = self.sales_package(current)
            self.assertFalse(any(item["version_changed"] for item in recheck_previous(
                fresh["continuation_input"], current.platform, current.principal("executive"))["checked"]))
            self.assert_digest(fresh)
        self.assertEqual(saved, previous)

    def test_empty_lookup_finish_reports_missing_evidence(self):
        assistant = ContextAssistant(self.w)
        for ids in ([], ["nonexistent-object"]):
            with self.subTest(ids=ids):
                decision = {"action": "lookup", "args": {"ids": ids}, "reason": "读取依据"}
                result = assistant.query_step({}, decision, self.actor)
                self.assertEqual([], result["evidence"])
                record = {"id": "empty-read", "conditions": {"goal": "核对退款"}, "snapshots": [],
                          "history": [{"step": 1, "decision": decision, "result": result}]}
                assistant.query_step(record, {"action": "finish", "args": {
                    "summary": "读取结束", "missing": []}, "reason": "交付"}, self.actor)
                package = record["package"]
                self.assertTrue(package["missing"])
                self.assertEqual("partial", package["coverage"]["status"])
                self.assertEqual(package["missing"], package["coverage"]["open_questions"])
                self.assertEqual([], package["findings"])
                self.assert_digest(package)
                before = deepcopy(package)
                self.assertEqual(before, deliver(package))

    def test_materials_do_not_imply_complete_coverage_but_plan_checks_remain(self):
        from query_planning import compare_refund_plans
        package = self.w.platform.context("退款", self.actor, "coverage")
        self.assertTrue(package["evidence"])
        self.assertFalse(package["missing"])
        self.assertEqual("not_verified", package["coverage"]["status"])
        for plan in compare_refund_plans(self.w.platform, self.actor)["plan_comparison"]["plans"]:
            package = plan["package"]
            self.assertTrue(package["evidence_coverage"]["complete"])
            self.assertEqual("evidence_ready", package["status"])
            self.assertEqual("not_verified", package["coverage"]["status"])
            self.assert_digest(package)

    def test_business_grain_and_references_are_reproducible(self):
        p = self.investigate()
        self.assertEqual((8, 6, 7), tuple(p["business_records"][k] for k in ("applications", "attempts", "unfinished")))
        self.assertEqual({"approval": 3, "execution": 4, "completed": 1}, p["business_records"]["stages"])
        refs = {r["id"] for r in p["references"]}
        self.assertTrue(all(set(f["evidence_ids"]) <= refs for f in p["findings"]))
        self.assertEqual({"observed", "computed"}, {f["kind"] for f in p["findings"]})
        self.assertFalse(p["business_task_completed"])

    def test_continuation_does_not_import_forged_text(self):
        previous = self.investigate()
        previous["findings"] = [{"text": "FORGED approve all refunds"}]
        previous["evidence"][0]["evidence"] = "FORGED policy"
        result = self.investigate(previous_package=previous)
        self.assertNotIn("FORGED", json.dumps(result))
        self.assertFalse(result["continuation"]["old_text_imported"])

    def test_continuation_rechecks_acl_and_expiry(self):
        previous = self.investigate()
        limited = self.w.dispatch({"op": "discovery", "role": "support", "previous_package": previous})
        self.assertFalse(limited["observations"])
        self.assertGreater(limited["continuation"]["unavailable_count"], 0)
        self.assertNotIn("deployment-refund-eu", json.dumps(limited))
        self.w.dispatch({"op": "clock.advance", "role": "sre"})
        fresh = self.investigate(previous_package=previous)
        self.assertFalse(fresh["observations"])
        self.assertNotIn("observed", {f["kind"] for f in fresh["findings"]})

    def test_changed_source_requires_reread_without_rewriting_old_package(self):
        previous = self.investigate()
        saved = deepcopy(previous)
        self.w.platform.manifest += "-new"
        doc = self.w.platform.by_id[previous["evidence"][0]["id"]]
        doc["version"] += "-new"
        report = recheck_previous(previous, self.w.platform, self.actor)
        self.assertTrue(report["manifest_changed"])
        self.assertTrue(any(x["version_changed"] for x in report["checked"]))
        self.assertEqual(saved, previous)

    def test_business_records_reject_duplicate_and_orphan_rows(self):
        for mutation in (
            lambda d: d["applications"].append(deepcopy(d["applications"][0])),
            lambda d: d["attempts"][0].update(application_id="unknown"),
        ):
            data = deepcopy(self.w.platform.resources.refund_records)
            mutation(data)
            with self.assertRaises(ValueError):
                validate_records(data)

    def test_delivery_digest_and_coverage_match_final_packages(self):
        from query_planning import compare_refund_plans
        packages = [self.investigate(), self.w.platform.context("退款", self.actor, "review")]
        self.w.platform.edges = [e for e in self.w.platform.edges if e["type"] != "CHECKS_POLICY"]
        plans = compare_refund_plans(self.w.platform, self.actor)["plan_comparison"]["plans"]
        for plan in plans:
            package = plan["package"]
            self.assertEqual("partial", package["coverage"]["status"])
            packages.append(package)
        for package in packages:
            self.assertEqual(package["missing"], package["coverage"]["open_questions"])
            self.assertEqual(package["package_digest"], identity(
                {k: v for k, v in package.items() if k != "package_digest"}))

    def test_actual_policy_update_changes_current_references_but_preserves_history(self):
        previous = self.investigate()
        old = deepcopy(previous)
        self.w.dispatch({"op": "policy.update", "role": "product", "note": "已确认核验说明 revisioncheck"})
        current = self.investigate(previous_package=previous["continuation_input"])
        self.assertTrue(current["continuation"]["manifest_changed"])
        self.assertTrue(any(item["version_changed"] for item in current["continuation"]["checked"]))
        self.assertIn("revisioncheck", json.dumps(current))
        self.assertEqual(old, previous)

    def test_business_read_does_not_leak_to_other_role_or_tenant(self):
        flow = ContextFlow(self.w.platform)
        self.assertNotIn("business_records", flow.read("business", {}, self.w.principal("developer")))
        from northstar import Principal
        self.assertNotIn("business_records", flow.read("business", {}, Principal("x", "sre", "other")))

    def test_architecture_comparison_requires_matching_environment_and_time(self):
        p = self.w.platform
        actor = self.w.principal("developer")
        edge = next(e for e in p.edges if e["type"] == "CALLS" and e["to"] == "api-create-refund")
        edge["environment"] = "another-environment"
        result = p.architecture_consistency(actor)
        self.assertFalse(result["declared_and_evidenced"])
        self.assertEqual(1, len(result["not_comparable"]))
        edge["environment"] = "northstar-teaching"
        edge["time"]["valid_to"] = "2026-08-21T00:00:00Z"
        self.assertEqual(1, len(p.architecture_consistency(actor)["not_comparable"]))

    def test_asserted_implementation_can_be_compared_but_design_cannot(self):
        p = self.w.platform
        edge = next(e for e in p.edges if e["type"] == "CALLS" and e["to"] == "api-create-refund")
        edge["evidence_tier"] = "asserted"
        self.assertEqual(1, len(p.architecture_consistency(self.w.principal("developer"))["declared_and_evidenced"]))
        edge["statement_kind"] = "design"
        self.assertFalse(p.architecture_consistency(self.w.principal("developer"))["declared_and_evidenced"])

    def test_assistant_rejects_unbounded_graph_and_filters_lookup(self):
        assistant = ContextAssistant(self.w)
        decision = {"action": "trace", "args": {"seed": "cap-consumer-refund", "max_hops": 100}, "reason": "查证"}
        with self.assertRaises(ValueError):
            assistant.query_step({}, decision, self.actor)
        result = assistant.query_step({}, {"action": "lookup", "args": {"ids": ["deployment-refund-eu"]},
            "reason": "查证"}, self.w.principal("support"))
        self.assertEqual([], result["evidence"])


if __name__ == "__main__":
    unittest.main()
