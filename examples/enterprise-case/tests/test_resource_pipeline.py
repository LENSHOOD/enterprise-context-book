"""Cross-source publication, discovery, visibility and generated-view contracts."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from northstar import NorthstarPlatform, Principal
from resource_pipeline import compile_resources
from resource_demo import investigate_refund
from resource_views import book_views, VIEWS, relationship_view, mermaid
from workbench import Workspace


class ResourcePipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / "data"
        shutil.copytree(ROOT / "data", self.data)

    def change(self, name, mutation):
        path = self.data / name
        value = json.loads(path.read_text())
        mutation(value)
        path.write_text(json.dumps(value, ensure_ascii=False))

    def test_all_sources_use_one_publication(self):
        p = NorthstarPlatform(self.data)
        self.assertEqual({"operations", "strategy", "refund-journey"},
                         {s["adapter"] for s in p.resources.report["sources"]})
        self.assertEqual(p.manifest, p.resources.report["manifest"])
        self.assertEqual(80, len(p.documents))
        self.assertEqual(69, len(p.edges))
        self.assertEqual(p.by_id["cap-consumer-refund"]["entity_type"],
                         p.by_id["cap-enterprise-sales"]["entity_type"])

    def test_unfamiliar_reader_discovers_monitor_and_runbook(self):
        p = NorthstarPlatform(self.data)
        result = investigate_refund(p, Principal("reader", "sre"))
        ids = {d["id"] for d in result["path"]}
        self.assertTrue({"value-stream-consumer-sale", "process-refund", "product-cancellation-policy", "service-refund-worker",
                         "deployment-refund-eu", "refund-queue", "monitor-refund-queue"} <= ids)
        self.assertEqual(["runbook-refund-backlog"], result["runbooks"])
        self.assertEqual(842, result["observations"][0]["queue_depth"])
        self.assertEqual([], result["missing"])
        self.assertEqual(0, p.execution_count)

    def test_support_sees_business_but_not_deployment_or_reading(self):
        result = investigate_refund(NorthstarPlatform(self.data), Principal("reader", "support"))
        self.assertIn("process-refund", {d["id"] for d in result["path"]})
        self.assertNotIn("refund-queue", {d["id"] for d in result["path"]})
        self.assertEqual([], result["observations"])
        self.assertTrue(result["missing"])

    def test_strategy_uses_common_search_trace_wiki_at_its_snapshot(self):
        p = NorthstarPlatform(self.data)
        actor = Principal("reader", "executive")
        t = "2027-01-02T00:00:00Z"
        self.assertEqual([], p.search("净确认订单额", actor))  # not known at August teaching clock
        self.assertIn("metric-sales-bookings", {h["id"] for h in p.search(
            "净确认订单额", actor, limit=20, valid_at=t, observed_at=t)})
        self.assertTrue(p.trace("cap-enterprise-sales", actor, valid_at=t, observed_at=t))
        self.assertTrue(p.build_wiki(actor, valid_at=t, observed_at=t))
        self.assertEqual([], p.trace("cap-enterprise-sales", Principal("dev", "developer"),
                                    valid_at=t, observed_at=t))
        self.assertEqual([], p.build_wiki(Principal("reader", "executive", "other"), valid_at=t, observed_at=t))

    def test_cross_domain_link_requires_both_endpoints_visible(self):
        p = NorthstarPlatform(self.data)
        t = "2027-01-02T00:00:00Z"
        actor = Principal("reader", "executive")
        self.assertFalse(any(e["type"] == "HAS_REFUND_CAPABILITY" for e in p.trace(
            "enterprise-northstar", actor, valid_at=t, observed_at=t)))
        # An explicitly granted business reader can follow the shared identity.
        self.change("refund-map.json", lambda m: m["objects"][0]["acl"].append("executive"))
        p = NorthstarPlatform(self.data)
        self.assertTrue(any(e["to"] == "cap-consumer-refund" for e in p.trace(
            "enterprise-northstar", actor, valid_at=t, observed_at=t)))

    def test_each_adapter_can_block_the_whole_publication(self):
        for name, mutation in [
            ("knowledge.json", lambda d: d[0].pop("tenant")),
            ("strategy-context.json", lambda d: d["observations"][0].update(unit="wrong")),
            ("refund-map.json", lambda d: d["relations"][0].update(to="missing-object")),
        ]:
            with self.subTest(name=name):
                original = (self.data / name).read_text()
                self.change(name, mutation)
                with self.assertRaises(ValueError):
                    compile_resources(self.data)
                (self.data / name).write_text(original)

    def test_new_mapping_requires_review_and_source_evidence(self):
        for mutation in [lambda d: d.update(status="candidate"),
                         lambda d: d["objects"][0].update(quote="invented quote"),
                         lambda d: d["objects"][0].update(anchor="deployment"),
                         lambda d: d["objects"][0].update(acl="developer")]:
            original = (self.data / "refund-map.json").read_text()
            self.change("refund-map.json", mutation)
            with self.assertRaises(ValueError):
                compile_resources(self.data)
            (self.data / "refund-map.json").write_text(original)

    def test_duplicate_identity_and_unregistered_runtime_are_rejected(self):
        self.change("refund-map.json", lambda d: d["objects"][0].update(id="service-refund-worker"))
        with self.assertRaisesRegex(ValueError, "duplicate resource"):
            compile_resources(self.data)
        shutil.copyfile(ROOT / "data/refund-map.json", self.data / "refund-map.json")
        self.change("runtime.json", lambda d: d.update(unknown=deepcopy(d["refund-queue"])))
        with self.assertRaisesRegex(ValueError, "registered resource"):
            compile_resources(self.data)

    def test_new_source_cannot_escape_raw_root(self):
        self.change("refund-map.json", lambda d: d.update(source="../../secret.md"))
        with self.assertRaisesRegex(ValueError, "source path"):
            compile_resources(self.data)

    def test_diagrams_only_contain_actual_visible_edges(self):
        p = NorthstarPlatform(self.data)
        for name, view in book_views(p).items():
            self.assertEqual(VIEWS[name][2], {d["id"] for d in view["objects"]})
            self.assertTrue(view["relations"])
            for edge in view["relations"]:
                self.assertIn(edge, p.edges)
            self.assertTrue(mermaid(view).startswith("flowchart " + view["direction"]))
        self.assertIn('-. "候选关联，待查证" .->', mermaid(book_views(p)["sales-observations"]))

    def test_source_change_updates_version_search_wiki_and_diagram(self):
        before = NorthstarPlatform(self.data)
        raw = self.data / "raw/business/refund-journey.md"
        raw.write_text(raw.read_text().replace("## process", "退款能力新增核对标记 resourcefresh。\n\n## process"))
        def update(m):
            m["objects"][0]["quote"] = "退款能力新增核对标记 resourcefresh。"
            m["objects"][0]["name"] = "退款能力 resourcefresh"
        self.change("refund-map.json", update)
        after = NorthstarPlatform(self.data)
        actor = Principal("reader", "sre")
        self.assertNotEqual(before.manifest, after.manifest)
        self.assertNotEqual(before.by_id["cap-consumer-refund"]["citation"], after.by_id["cap-consumer-refund"]["citation"])
        self.assertIn("cap-consumer-refund", {h["id"] for h in after.search("resourcefresh", actor)})
        self.assertIn("resourcefresh", json.dumps(after.build_wiki(actor)))
        self.assertIn("resourcefresh", mermaid(book_views(after)["refund-business"]))

    def test_workbench_uses_shared_catalog_for_timed_views(self):
        workspace = Workspace(data_dir=self.data)
        time_args = {"valid_at": "2027-01-02T00:00:00Z", "observed_at": "2027-01-02T00:00:00Z"}
        for op, key in (("wiki", "wiki"), ("trace", "relations")):
            args = {"op": op, "role": "executive", "seed": "cap-enterprise-sales"}
            self.assertEqual([], workspace.dispatch(args)[key])
            self.assertTrue(workspace.dispatch({**args, **time_args})[key])
        catalog = workspace.dispatch({"op": "resources", "role": "executive"})
        self.assertEqual(49, len(catalog["enterprise"]))
        self.assertEqual(time_args["valid_at"], catalog["enterprise_as_of"])
        for item in catalog["enterprise"]:
            self.assertEqual(item, workspace.platform.by_id[item["id"]])


if __name__ == "__main__":
    unittest.main()
