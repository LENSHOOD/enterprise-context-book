"""Integration contracts for the local, persistent teaching system."""
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from workbench import WorkspaceStore, SCENARIOS, DATA
from lab_server import make_server


class WorkbenchTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "lab.sqlite3"
        self.store = WorkspaceStore(self.database)
        self.identity = self.store.create()

    def tearDown(self):
        self.temp.cleanup()

    def call(self, op, role="sre", **kwargs):
        return self.store.call(self.identity, {"op": op, "role": role, **kwargs})

    def create(self, kind="incident"):
        preset = SCENARIOS[kind]
        return self.call("task.create", kind=kind, **preset)["id"]

    def prepare(self):
        task = self.create()
        self.call("task.context", task_id=task)
        preview = self.call("action.prepare", task_id=task)["preview"]
        return task, preview

    def test_restart_recovers_task_and_exactly_once_execution(self):
        task, preview = self.prepare()
        self.call("action.confirm", "incident_commander", task_id=task, params_hash=preview["params_hash"])
        self.store = WorkspaceStore(self.database)
        first = self.call("action.execute", task_id=task)
        self.store = WorkspaceStore(self.database)
        second = self.call("action.execute", task_id=task)
        self.assertEqual(first["receipt"], second["receipt"])
        final = self.call("action.verify", task_id=task)
        self.assertEqual("resolved", final["state"])
        self.assertEqual(742, final["verification"]["observation"]["queue_depth"])
        self.assertNotIn("token", final)

    def test_two_concurrent_execute_requests_only_change_queue_once(self):
        task, preview = self.prepare()
        self.call("action.confirm", "incident_commander", task_id=task, params_hash=preview["params_hash"])
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: self.call("action.execute", task_id=task), range(2)))
        self.assertEqual(results[0]["receipt"], results[1]["receipt"])
        self.assertEqual(742, self.call("action.verify", task_id=task)["verification"]["observation"]["queue_depth"])

    def test_sessions_and_roles_do_not_share_tasks(self):
        task, preview = self.prepare()
        other = self.store.create()
        with self.assertRaises(ValueError):
            self.store.call(other, {"op": "task.get", "role": "sre", "task_id": task})
        with self.assertRaises(PermissionError):
            self.call("task.get", "support", task_id=task)
        restricted = self.call("task.get", "incident_commander", task_id=task)
        self.assertTrue(restricted["approval_only"])
        self.assertNotIn("package", restricted)
        self.assertNotIn("events", restricted)
        with self.assertRaises(PermissionError):
            self.call("action.confirm", task_id=task, params_hash=preview["params_hash"])

    def test_expired_confirmation_rolls_back_without_executing(self):
        task, preview = self.prepare()
        self.call("action.confirm", "incident_commander", task_id=task, params_hash=preview["params_hash"])
        self.call("clock.advance")
        with self.assertRaisesRegex(ValueError, "expired"):
            self.call("action.execute", task_id=task)
        self.assertEqual("approved", self.call("task.get", task_id=task)["state"])
        self.assertNotIn("receipt", self.call("task.get", task_id=task))

    def test_rejection_is_durable_and_no_execution_possible(self):
        task, preview = self.prepare()
        self.call("action.reject", "incident_commander", task_id=task, params_hash=preview["params_hash"])
        self.store = WorkspaceStore(self.database)
        self.assertEqual("needs_human", self.call("task.get", task_id=task)["state"])
        with self.assertRaises(PermissionError):
            self.call("action.execute", task_id=task)

    def test_confirm_requires_reviewed_parameters(self):
        task, _ = self.prepare()
        with self.assertRaisesRegex(ValueError, "预览"):
            self.call("action.confirm", "incident_commander", task_id=task, params_hash="modified")

    def test_strategy_records_contract_and_work_progress(self):
        task = self.create("strategy")
        first = self.call("task.context", "executive", task_id=task)
        self.assertEqual("needs_clarification", first["state"])
        confirmation = {k: v for k, v in first["package"]["query_contract"].items() if k != "confirmed"}
        self.call("task.confirm_definition", "executive", task_id=task, confirmation=confirmation)
        self.call("task.note", "executive", task_id=task, note="需补充客户订单级明细")
        second = self.call("task.context", "executive", task_id=task)
        self.assertEqual("ready_for_review", second["state"])
        self.assertEqual(2, len(second["snapshots"]))
        self.assertNotEqual(first["package"]["trace_id"], second["package"]["trace_id"])
        self.assertEqual(first["package"], second["snapshots"][0])
        self.assertTrue(any(e["type"] == "definition_confirmed" for e in second["package"]["memories"]))
        self.assertEqual(SCENARIOS["strategy"]["completion"], second["package"]["task_conditions"]["completion"])

    def test_policy_update_rebuilds_views_and_marks_old_task_stale(self):
        path = DATA / "raw/business/order-cancellation.md"
        original = path.read_bytes()
        task = self.create("change")
        old = self.call("task.context", "developer", task_id=task)
        result = self.call("policy.update", "product", note="新增核验说明：checkpointalpha")
        self.assertNotEqual(result["before_manifest"], result["after_manifest"])
        self.assertIn("checkpointalpha", json.dumps(result["wiki"]))
        self.assertIn(task, result["invalidated_tasks"])
        stale = self.call("task.get", "developer", task_id=task)
        self.assertTrue(stale["stale"])
        self.assertEqual(old["package"], stale["package"])
        refreshed = self.call("task.context", "developer", task_id=task)
        self.assertFalse(refreshed["stale"])
        self.assertEqual(2, len(refreshed["snapshots"]))
        self.assertEqual(original, path.read_bytes())
        isolated = self.store.call(self.store.create(), {"op": "search", "role": "support", "question": "checkpointalpha"})
        self.assertEqual([], isolated["evidence"])

    def test_old_approval_cannot_execute_after_resource_update(self):
        task, preview = self.prepare()
        self.call("action.confirm", "incident_commander", task_id=task, params_hash=preview["params_hash"])
        self.call("policy.update", "product", note="新政策补充")
        with self.assertRaisesRegex(ValueError, "资源更新"):
            self.call("action.execute", task_id=task)
        with self.assertRaisesRegex(ValueError, "新建事故"):
            self.call("task.context", task_id=task)

    def test_resource_model_and_wiki_keep_role_filtering(self):
        for op in ("resources", "model", "wiki"):
            serialized = json.dumps(self.call(op, "support"))
            self.assertNotIn("code://", serialized)
        self.assertTrue(self.call("resources", "executive")["enterprise"])
        self.assertEqual([], self.call("resources", "support")["enterprise"])

    def test_contract_fields_required_and_shell_is_not_an_operation(self):
        with self.assertRaises(ValueError):
            self.call("task.create", kind="incident", goal="test", scope="queue")
        with self.assertRaises(ValueError):
            self.call("shell", command="echo unsafe")

    def test_fixed_scope_cannot_be_relabelled_as_a_broader_task(self):
        with self.assertRaisesRegex(ValueError, "固定范围"):
            self.call("task.create", kind="incident", **{**SCENARIOS["incident"], "scope": "all tenants"})

    def test_source_version_change_requires_a_new_workspace(self):
        self.create()
        with patch("workbench.source_revision", return_value="different-code"):
            with self.assertRaisesRegex(ValueError, "源码已变化"):
                self.call("overview")

    def test_review_is_recorded_but_never_changes_business_metrics(self):
        task = self.create("strategy")
        with self.assertRaises(ValueError):
            self.call("task.review", "executive", task_id=task, note="premature")
        initial = self.call("task.context", "executive", task_id=task)
        contract = {k: v for k, v in initial["package"]["query_contract"].items() if k != "confirmed"}
        with self.assertRaises(ValueError):
            self.call("task.confirm_definition", "executive", task_id=task, confirmation=True)
        self.call("task.confirm_definition", "executive", task_id=task, confirmation=contract)
        before = self.call("task.context", "executive", task_id=task)
        after = self.call("task.review", "executive", task_id=task, note="核对差异，根因仍待补充证据")
        self.assertEqual("reviewed", after["state"])
        self.assertEqual(before["package"]["performance"], after["package"]["performance"])
        self.assertEqual("human_reviewed", after["events"][-1]["type"])


class LabHTTPTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.site = self.root / "site"
        self.site.mkdir()
        (self.site / "index.html").write_text("book", encoding="utf-8")
        (self.site / "lab.html").write_text("workbench", encoding="utf-8")
        self.server = make_server(0, self.root / "lab.sqlite3", self.site)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, payload=None, headers=None):
        client = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        headers = headers or {}
        if payload is not None:
            headers = {"Content-Type": "application/json", "X-Northstar-Lab": "1", **headers}
        client.request("POST" if payload is not None else "GET", path,
                       json.dumps(payload) if payload is not None else None, headers)
        response = client.getresponse()
        result = response.status, response.read().decode(), dict(response.getheaders())
        client.close()
        return result

    def test_same_origin_session_cookie_and_clean_routes(self):
        self.assertEqual(200, self.request("/lab")[0])
        self.assertEqual(200, self.request("/api/health")[0])
        status, _, headers = self.request("/api/session", {})
        self.assertEqual(200, status)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        cookie = headers["Set-Cookie"].split(";")[0]
        self.assertEqual(200, self.request("/api/lab", {"op": "resources"}, {"Cookie": cookie})[0])
        self.assertEqual(403, self.request("/api/lab", {"op": "resources"})[0])

    def test_cross_origin_and_rebinding_are_rejected(self):
        self.assertEqual(403, self.request("/api/session", {}, {"Origin": "https://other.example"})[0])
        self.assertEqual(403, self.request("/api/health", headers={"Host": "other.example"})[0])
        self.assertEqual(403, self.request("/api/session", {}, {"X-Northstar-Lab": ""})[0])

    def test_static_paths_cannot_expose_database_or_symlink(self):
        (self.site / "secret.txt").symlink_to(self.root / "lab.sqlite3")
        self.assertEqual(403, self.request("/secret.txt")[0])
        self.assertEqual(403, self.request("/%2e%2e/lab.sqlite3")[0])
        (self.site / "alias.html").symlink_to(self.root / "lab.sqlite3")
        self.assertEqual(403, self.request("/alias")[0])
        (self.site / "nested").mkdir()
        (self.site / "nested/index.html").symlink_to(self.root / "lab.sqlite3")
        self.assertEqual(403, self.request("/nested/")[0])


if __name__ == "__main__":
    unittest.main()
