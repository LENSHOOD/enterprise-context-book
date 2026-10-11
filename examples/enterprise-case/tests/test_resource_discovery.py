"""C4 exercises the shared route with real workspace state and role boundaries."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from resource_discovery import investigate_refund
from tutorial_catalog import LESSONS
from workbench import Workspace, WorkspaceStore


class ResourceDiscoveryTest(unittest.TestCase):
    def test_c4_runs_read_only_route_and_includes_readable_sources(self):
        workspace = Workspace()
        before = workspace.snapshot()
        lesson = LESSONS["C4"]
        result = workspace.dispatch({**lesson["request"], "role": lesson["role"]})
        self.assertEqual(before, workspace.snapshot())
        self.assertEqual(842, result["observations"][0]["queue_depth"])
        self.assertEqual([], result["missing"])
        self.assertFalse(result["business_task_completed"])
        docs = {item["id"]: item for item in result["documents"]}
        self.assertIn("禁止", docs["runbook-refund-backlog"]["text"])
        self.assertIn("Policy", {item["entity_type"] for item in docs.values()})
        for step in result["discovery_steps"]:
            self.assertTrue(set(step["object_ids"]) <= docs.keys())
        # Returning materials must not hand a caller mutable platform records.
        result["documents"][0]["text"] = "changed by caller"
        self.assertEqual(before, workspace.snapshot())
        self.assertNotEqual("changed by caller", workspace.platform.by_id[result["documents"][0]["id"]]["text"])

    def test_support_only_receives_visible_business_materials(self):
        result = Workspace().dispatch({"op": "discovery", "role": "support"})
        ids = {item["id"] for item in result["documents"]}
        self.assertIn("process-refund", ids)
        self.assertNotIn("deployment-refund-eu", ids)
        self.assertNotIn("monitor-refund-queue", ids)
        self.assertEqual([], result["observations"])
        self.assertEqual([], result["runbooks"])
        self.assertTrue(result["missing"])
        for edge in result["relations"]:
            self.assertTrue({edge["from"], edge["to"]} <= ids)
        for step in result["discovery_steps"]:
            self.assertTrue(set(step["object_ids"]) <= ids)

    def test_developer_can_find_monitor_but_not_read_runtime(self):
        result = Workspace().dispatch({"op": "discovery", "role": "developer"})
        self.assertIn("monitor-refund-queue", {item["id"] for item in result["documents"]})
        self.assertEqual([], result["observations"])
        self.assertTrue(result["runbooks"])
        self.assertEqual("missing", result["discovery_steps"][2]["status"])

    def test_expired_observation_stays_missing_after_store_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "lab.sqlite3"
            store = WorkspaceStore(database)
            space = store.create()
            call = lambda op: store.call(space, {"op": op, "role": "sre"})
            self.assertTrue(call("discovery")["observations"])
            call("clock.advance")
            store = WorkspaceStore(database)
            result = call("discovery")
            self.assertEqual([], result["observations"])
            self.assertTrue(result["missing"])
            self.assertTrue(result["runbooks"])
            self.assertTrue(result["documents"])

    def test_invisible_business_entry_stops_without_runtime_read(self):
        workspace = Workspace()
        result = workspace.dispatch({"op": "discovery", "role": "executive"})
        self.assertIsNone(result["entry"])
        self.assertEqual([], result["documents"])
        self.assertEqual([], result["observations"])
        self.assertEqual(1, len(result["discovery_steps"]))
        self.assertTrue(result["missing"])

    def test_missing_runbook_is_not_reported_as_complete(self):
        workspace = Workspace()
        platform = workspace.platform
        platform.edges = [edge for edge in platform.edges if edge["to"] != "runbook-refund-backlog"]
        result = investigate_refund(platform, workspace.principal("sre"))
        self.assertTrue(result["observations"])
        self.assertEqual([], result["runbooks"])
        self.assertEqual("missing", result["discovery_steps"][-1]["status"])
        self.assertTrue(result["missing"])


if __name__ == "__main__":
    unittest.main()
