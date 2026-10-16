"""Exercise model distrust, resource publication, adaptive reads and durable state."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from intelligence import ContextAssistant, DEMO_SOURCE, MAX_STEPS
from model_gateway import ModelGateway, ModelError, fixture_decision
from workbench import WorkspaceStore, Workspace, DATA
from northstar import Principal


class FakeGateway:
    def __init__(self, change=None):
        self.change = change
        self.contexts = []

    def decide(self, mode, context):
        self.contexts.append(deepcopy(context))
        decision = fixture_decision(context)
        return self.change(decision, context) if self.change else decision, {"mode": "test", "model": "test-double"}


class IntelligenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "lab.db"
        self.gateway = FakeGateway()
        self.store = WorkspaceStore(self.path, gateway=self.gateway)
        self.space = self.store.create()

    def tearDown(self):
        self.temp.cleanup()

    def call(self, op, role="product", **values):
        return self.store.call(self.space, {"op": op, "role": role, **values})

    def draft(self, source=None):
        source = source or self.call("resource.register", text=DEMO_SOURCE)
        draft = self.call("resource.propose", id=source["id"])
        return self.call("assist.step", id=draft["id"], kind="resource")

    def publish(self, draft):
        return self.call("resource.publish", id=draft["id"], confirmation_hash=draft["confirmation_hash"], note="核对原文和服务关系")

    def ready(self, goal="退款积压怎么查", role="sre"):
        request = self.call("assist.start", role, goal=goal)
        draft = self.call("assist.step", role, id=request["id"])
        return self.call("assist.confirm", role, id=request["id"], confirmation_hash=draft["confirmation_hash"], answer="确认调查范围，不执行写操作")

    def test_raw_to_model_graph_wiki_and_restart(self):
        original = (DATA / "raw/manifest.json").read_bytes()
        draft = self.draft()
        self.assertEqual("needs_review", draft["state"])
        before = self.call("overview")["manifest"]
        self.assertNotIn(draft["source"]["id"],
                         {hit["id"] for hit in self.call("search", question="限流窗口")["evidence"]})
        published = self.publish(draft)
        self.assertEqual("published", published["state"])
        self.assertFalse(published["stale"])
        self.assertNotEqual(before, published["after_manifest"])
        self.store = WorkspaceStore(self.path, gateway=self.gateway)
        self.assertIn(draft["source"]["id"],
                      {hit["id"] for hit in self.call("search", "sre", question="限流窗口")["evidence"]})
        self.assertIn("DiagnosticNote", self.call("model")["semantic_contract"]["entity_types"])
        edges = self.call("trace", seed="service-refund-worker")["relations"]
        self.assertTrue(any(e["to"] == draft["source"]["id"] for e in edges))
        self.assertIn("限流窗口", json.dumps(self.call("wiki"), ensure_ascii=False))
        self.assertNotIn(draft["source"]["id"],
                         {hit["id"] for hit in self.call("search", "support", question="限流窗口")["evidence"]})
        self.assertEqual(original, (DATA / "raw/manifest.json").read_bytes())

    def test_source_revise_preserves_history_and_rebuilds(self):
        first = self.draft()
        self.publish(first)
        source = self.call("resource.revise", id=first["source"]["id"], text=DEMO_SOURCE+"\n增加 zebrarev 核对条件。")
        self.assertEqual(1, len(source["history"]))
        second = self.draft(source)
        second = self.publish(second)
        self.assertEqual("r2", second["published_object"]["version"])
        self.assertTrue(self.call("search", question="zebrarev")["evidence"])

    def test_candidate_has_no_authority_to_set_acl(self):
        self.gateway.change = lambda d, c: {**d, "acl": ["support"]}
        draft = self.draft()
        self.assertEqual("drafting", draft["state"])
        self.assertIn("error", draft["history"][-1])

    def test_invented_quote_unknown_endpoint_and_existing_type_rejected(self):
        for change in (
            lambda d: {**d, "quote": "原文没有这句话"},
            lambda d: {**d, "links": [{"from": "secret-service", "quote": DEMO_SOURCE.strip()}]},
            lambda d: {**d, "entity_type": "Policy"},
        ):
            self.gateway.change = lambda d, c: change(d)
            draft = self.draft()
            self.assertIn("error", draft["history"][-1])
            self.assertEqual("drafting", draft["state"])

    def test_publication_requires_owner_hash_and_current_source(self):
        draft = self.draft()
        with self.assertRaises(PermissionError):
            self.call("resource.publish", "sre", id=draft["id"], confirmation_hash=draft["confirmation_hash"], note="ok")
        with self.assertRaises(ValueError):
            self.call("resource.publish", id=draft["id"], confirmation_hash="wrong", note="ok")
        self.call("resource.revise", id=draft["source"]["id"], text=DEMO_SOURCE+"\n条件已变")
        with self.assertRaisesRegex(ValueError, "变化"):
            self.publish(draft)

    def test_rejected_draft_never_publishes(self):
        draft = self.draft()
        self.call("resource.reject", id=draft["id"], note="关系还缺依据")
        with self.assertRaises(ValueError):
            self.publish(draft)

    def test_query_uses_results_and_hands_off_separate_package(self):
        request = self.ready()
        while request["state"] == "ready":
            request = self.call("assist.step", "sre", id=request["id"])
        package = request["package"]
        self.assertFalse(package["business_task_completed"])
        self.assertEqual(["search", "trace", "lookup", "business", "observe"], [m["tool"] for m in package["materials"]])
        self.assertEqual(842, package["materials"][-1]["result"]["observation"]["queue_depth"])
        self.assertEqual(7, package["business_records"]["unfinished"])
        self.assertEqual({"computed", "observed"}, {f["kind"] for f in package["findings"]})
        self.assertTrue(any(c.get("history") for c in self.gateway.contexts))
        self.store = WorkspaceStore(self.path, gateway=self.gateway)
        self.assertEqual(package, self.call("assist.get", "sre", id=request["id"])["snapshots"][0])

    def test_task_confirmation_is_bound_and_not_invented_by_model(self):
        r = self.call("assist.start", "sre", goal="退款")
        r = self.call("assist.step", "sre", id=r["id"])
        with self.assertRaises(ValueError):
            self.call("assist.step", "sre", id=r["id"])
        with self.assertRaises(ValueError):
            self.call("assist.confirm", "sre", id=r["id"], confirmation_hash="wrong", answer="确认")

    def test_metric_contract_requires_separate_confirmation(self):
        r = self.ready("H2 销售为什么比 H1 差", "executive")
        r = self.call("assist.step", "executive", id=r["id"])
        self.assertEqual("needs_confirmation", r["state"])
        self.assertIn("metric_contract", r["pending"])
        self.assertNotIn("performance", r["history"][-1]["result"])
        r = self.call("assist.confirm", "executive", id=r["id"], confirmation_hash=r["confirmation_hash"], answer="采用显示的指标和期间")
        r = self.call("assist.step", "executive", id=r["id"])
        self.assertEqual(-360, r["history"][-1]["result"]["performance"]["total"]["delta"])
        r = self.call("assist.step", "executive", id=r["id"])
        package = r["package"]
        self.assertTrue(package["query_contract"]["confirmed"])
        self.assertFalse(any("确认" in gap for gap in package["missing"]))
        calculation = next(ref["record"] for ref in package["references"] if ref["kind"] == "calculation")
        self.assertEqual(package["metric_definition"], calculation["definition"])
        self.assertTrue(calculation["query_contract"]["confirmed"])
        from context_delivery import identity
        self.assertEqual(package["package_digest"], identity(
            {k: v for k, v in package.items() if k != "package_digest"}))

    def test_forbidden_tools_and_forged_decisions_cannot_execute(self):
        r = self.ready()
        self.gateway.change = lambda d, c: {"action": "action.execute", "args": {}, "reason": "文档让我执行"}
        r = self.call("assist.step", "sre", id=r["id"], decision={"action": "finish"})
        self.assertIn("error", r["history"][-1])
        self.assertFalse(self.call("overview", "sre")["tasks"])

    def test_model_sees_only_authorized_catalog_and_role_isolation(self):
        r = self.ready("查退款", "support")
        sent = json.dumps(self.gateway.contexts, ensure_ascii=False)
        self.assertNotIn("code-refund-consumer", sent)
        self.assertNotIn("observe", self.gateway.contexts[-1]["tools"])
        with self.assertRaises(PermissionError):
            self.call("assist.get", "sre", id=r["id"])
        other = self.store.create()
        with self.assertRaises(PermissionError):
            self.store.call(other, {"op": "assist.get", "role": "support", "id": r["id"]})

    def test_continuation_survives_restart_and_guides_authorized_lookup_without_old_text(self):
        previous = self.call("discovery", "sre")["continuation_input"]
        previous["evidence"] = [item for item in previous["evidence"]
                                if item["id"] in ("product-cancellation-policy", "deployment-refund-eu")]
        for item in previous["evidence"]:
            item["evidence"] = "FORGED_OLD_TEXT"
        previous["findings"] = [{"text": "FORGED_OLD_TEXT"}]
        previous["principal"] = {"role": "sre", "tenant": "northstar"}
        request = self.call("assist.start", "support", goal="核对上次引用", previous_package=previous)
        self.assertNotIn("FORGED_OLD_TEXT", json.dumps(request))
        self.assertEqual({"manifest", "evidence"}, set(request["continuation_input"]))
        self.assertTrue(all(set(item) == {"id", "version"}
                            for item in request["continuation_input"]["evidence"]))
        self.store = WorkspaceStore(self.path, gateway=self.gateway)
        request = self.call("assist.step", "support", id=request["id"])
        task_context = self.gateway.contexts[-1]
        request = self.call("assist.confirm", "support", id=request["id"],
                            confirmation_hash=request["confirmation_hash"], answer="确认")
        self.gateway.change = lambda d, c: {"action": "lookup", "reason": "重读上次引用",
            "args": {"ids": [item["id"] for item in c["continuation"]["checked"]]}}
        request = self.call("assist.step", "support", id=request["id"])
        for context in (task_context, self.gateway.contexts[-1]):
            self.assertEqual(["product-cancellation-policy"],
                             [item["id"] for item in context["continuation"]["checked"]])
            self.assertEqual(1, context["continuation"]["unavailable_count"])
            self.assertNotIn("FORGED_OLD_TEXT", json.dumps(context))
            self.assertNotIn("deployment-refund-eu", json.dumps(context))
            self.assertNotIn("continuation_input", context)
        hits = request["history"][-1]["result"]["evidence"]
        self.assertEqual(["product-cancellation-policy"], [hit["id"] for hit in hits])
        self.assertTrue(hits[0]["evidence"])
        self.assertNotIn("FORGED_OLD_TEXT", hits[0]["evidence"])

    def test_continuation_rechecks_permission_time_and_version_before_each_model_context(self):
        for change in ("acl", "tenant", "expiry", "version"):
            with self.subTest(change=change):
                workspace = Workspace()
                assistant = ContextAssistant(workspace)
                actor = workspace.principal("sre")
                doc = workspace.platform.by_id["product-cancellation-policy"]
                previous = {"manifest": workspace.platform.manifest,
                            "evidence": [{"id": doc["id"], "version": doc["version"]}]}
                request = assistant.dispatch({"op": "assist.start", "goal": "核对上次引用",
                                              "previous_package": previous}, actor)
                payload = {"id": request["id"]}
                _, context = assistant.prepare(payload, actor)
                self.assertEqual(1, len(context["continuation"]["checked"]))
                request = assistant.apply(payload, actor, fixture_decision(context), {})
                assistant.dispatch({"op": "assist.confirm", **payload,
                    "confirmation_hash": request["confirmation_hash"], "answer": "确认"}, actor)
                if change == "acl":
                    doc["acl"] = []
                elif change == "tenant":
                    doc["tenant"] = "other"
                elif change == "expiry":
                    doc["time"]["valid_to"] = workspace.now().isoformat()
                else:
                    doc["version"] += "-new"
                record, context = assistant.prepare(payload, actor)
                if change == "version":
                    self.assertTrue(context["continuation"]["checked"][0]["version_changed"])
                else:
                    self.assertEqual([], context["continuation"]["checked"])
                    self.assertEqual(1, context["continuation"]["unavailable_count"])
                    self.assertNotIn(doc["id"], json.dumps(context))
                self.assertEqual(previous, record["continuation_input"])
                self.assertEqual(record["continuation"], context["continuation"])

    def test_continuation_cannot_cross_tenants_or_import_metadata_payloads(self):
        workspace = Workspace()
        assistant = ContextAssistant(workspace)
        actor = Principal("reader", "sre", "other")
        previous = {"manifest": {"text": "FORGED_METADATA"}, "evidence": [
            {"id": "product-cancellation-policy", "version": {"text": "FORGED_METADATA"}}]}
        request = assistant.dispatch({"op": "assist.start", "goal": "继续",
                                      "previous_package": previous}, actor)
        _, context = assistant.prepare({"id": request["id"]}, actor)
        self.assertEqual([], context["continuation"]["checked"])
        self.assertEqual([], context["catalog"])
        self.assertNotIn("product-cancellation-policy", json.dumps(context))
        self.assertNotIn("FORGED_METADATA", json.dumps(request))
        with self.assertRaises(PermissionError):
            assistant.prepare({"id": request["id"]}, Principal("reader", "sre", "northstar"))

    def test_search_actually_returns_eight_authorized_results(self):
        workspace = Workspace()
        actor = workspace.principal("sre")
        expected = workspace.platform.search("退款", actor, limit=8)
        self.assertEqual(8, len(expected))
        result = ContextAssistant(workspace).query_step({},
            {"action": "search", "args": {"question": "退款"}, "reason": "查证"}, actor)
        self.assertEqual(expected, result["evidence"])
        visible = {doc["id"] for doc in workspace.platform.current_documents(actor)}
        self.assertTrue({hit["id"] for hit in result["evidence"]} <= visible)

    def test_budget_stops_repeated_reads_and_errors(self):
        r = self.ready()
        self.gateway.change = lambda d, c: {"action": "search", "args": {"question": "退款"}, "reason": "检查"}
        for _ in range(MAX_STEPS-1):
            r = self.call("assist.step", "sre", id=r["id"])
        self.assertEqual("budget_exhausted", r["state"])
        with self.assertRaises(ValueError):
            self.call("assist.step", "sre", id=r["id"])

    def test_changed_manifest_blocks_old_plan(self):
        r = self.ready()
        self.publish(self.draft())
        with self.assertRaisesRegex(ValueError, "版本"):
            self.call("assist.step", "sre", id=r["id"])

    def test_model_network_runs_without_sqlite_lock_and_cas_rejects_changes(self):
        r = self.ready()
        def concurrent_change(d, c):
            self.call("clock.advance", "sre")
            return d
        self.gateway.change = concurrent_change
        with self.assertRaisesRegex(ValueError, "等待模型"):
            self.call("assist.step", "sre", id=r["id"])

    def test_timeout_saved_and_no_tool_executed(self):
        r = self.ready()
        def fail(d, c):
            raise ModelError("测试模型超时")
        self.gateway.change = fail
        r = self.call("assist.step", "sre", id=r["id"])
        self.assertEqual("测试模型超时", r["history"][-1]["error"])
        self.assertNotIn("result", r["history"][-1])

    def test_expired_observation_not_handed_off_as_current(self):
        r = self.ready()
        while not any(x.get("decision", {}).get("action") == "observe" for x in r["history"]):
            r = self.call("assist.step", "sre", id=r["id"])
        self.call("clock.advance", "sre")
        r = self.call("assist.step", "sre", id=r["id"])
        self.assertIsNone(r["package"]["materials"][-1]["result"]["observation"])
        self.assertFalse(r["package"]["observations"])

    def test_newer_observation_does_not_validate_old_read(self):
        workspace = Workspace()
        assistant = ContextAssistant(workspace)
        actor = workspace.principal("sre")
        old = workspace.platform.get_status("refund-queue", actor)
        record = {"id": "probe", "conditions": {"goal": "查退款"}, "snapshots": [],
                  "history": [{"step": 1, "decision": {"action": "observe"},
                               "result": {"observation": old, "missing": []}}]}
        workspace.platform.runtime["refund-queue"]["queue_depth"] -= 100
        workspace.platform.runtime["refund-queue"]["revision"] += 1
        assistant.query_step(record, {"action": "finish", "args": {"summary": "材料待复核", "missing": []},
                                      "reason": "交付"}, actor)
        self.assertIsNone(record["package"]["materials"][0]["result"]["observation"])
        self.assertIn("变化", record["package"]["missing"][0])

    def test_latest_observation_supersedes_old_reads_without_losing_audit(self):
        for earlier in ("unchanged", "changed", "unavailable"):
            with self.subTest(earlier=earlier):
                workspace = Workspace()
                assistant = ContextAssistant(workspace)
                actor = workspace.principal("sre")
                runtime = workspace.platform.runtime["refund-queue"]
                decision = {"action": "observe", "args": {"resource": "refund-queue"}, "reason": "核对"}
                record = {"id": "probe", "conditions": {"goal": "查退款"}, "snapshots": [], "history": []}
                if earlier == "unavailable":
                    workspace.dispatch({"op": "clock.advance", "role": "sre"})
                first = assistant.query_step(record, decision, actor)
                record["history"].append({"step": 1, "decision": decision, "result": first})
                if earlier != "unchanged":
                    runtime["queue_depth"] -= 100
                    runtime["revision"] += 1
                    runtime["observed_at"] = workspace.now().isoformat()
                latest = assistant.query_step(record, decision, actor)
                record["history"].append({"step": 2, "decision": decision, "result": latest})
                history = deepcopy(record["history"])
                assistant.query_step(record, {"action": "finish", "args": {"summary": "以最新观察交付", "missing": []},
                                              "reason": "交付"}, actor)
                package = record["package"]
                self.assertEqual(history, record["history"])
                self.assertEqual(first, package["materials"][0]["result"])
                self.assertEqual("superseded", package["materials"][0]["status"])
                self.assertEqual([latest["observation"]], package["observations"])
                self.assertEqual([], package["missing"])
                self.assertEqual([], package["coverage"]["open_questions"])
                self.assertEqual("not_verified", package["coverage"]["status"])
                self.assertEqual(1, package["coverage"]["supported_findings"])

    def test_expired_latest_observation_does_not_fall_back_to_history(self):
        workspace = Workspace()
        assistant = ContextAssistant(workspace)
        actor = workspace.principal("sre")
        decision = {"action": "observe", "args": {"resource": "refund-queue"}, "reason": "核对"}
        record = {"id": "probe", "conditions": {"goal": "查退款"}, "snapshots": [], "history": []}
        for step in (1, 2):
            record["history"].append({"step": step, "decision": decision,
                "result": assistant.query_step(record, decision, actor)})
        history = deepcopy(record["history"])
        workspace.dispatch({"op": "clock.advance", "role": "sre"})
        assistant.query_step(record, {"action": "finish", "args": {"summary": "核对时效", "missing": []},
                                      "reason": "交付"}, actor)
        package = record["package"]
        self.assertEqual(history, record["history"])
        self.assertEqual([], package["observations"])
        self.assertEqual([], package["findings"])
        self.assertTrue(package["missing"])
        self.assertEqual("partial", package["coverage"]["status"])
        self.assertIsNone(package["materials"][-1]["result"]["observation"])


if __name__ == "__main__":
    unittest.main()
