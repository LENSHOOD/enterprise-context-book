import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "src" / "context_demo.py"
SPEC = importlib.util.spec_from_file_location("context_demo", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
DATA = Path(__file__).parents[1] / "data" / "knowledge.json"


class ContextDemoTest(unittest.TestCase):
    def test_developer_finds_code_and_adr(self):
        result = MODULE.query(DATA, "handle_order_cancelled create_refund order.cancelled", "developer", limit=8)
        ids = {hit["id"] for hit in result["hits"]}
        self.assertIn("adr-refund-event", ids)
        self.assertIn("code-refund-consumer", ids)

    def test_support_cannot_see_code_or_runbook(self):
        result = MODULE.query(DATA, "退款积压 consumer", "support")
        ids = {hit["id"] for hit in result["hits"]}
        self.assertNotIn("code-refund-consumer", ids)
        self.assertNotIn("runbook-refund-backlog", ids)

    def test_every_hit_has_versioned_citation(self):
        result = MODULE.query(DATA, "退款", "developer")
        self.assertTrue(result["hits"])
        self.assertTrue(all("@" in hit["citation"] for hit in result["hits"]))

    def test_code_hit_uses_navigable_code_citation(self):
        result = MODULE.query(DATA, "handle_order_cancelled", "developer")
        code_hits = [hit for hit in result["hits"] if hit["kind"] == "code"]
        self.assertTrue(code_hits)
        self.assertTrue(all(hit["citation"].startswith("code://") for hit in code_hits))


if __name__ == "__main__":
    unittest.main()
