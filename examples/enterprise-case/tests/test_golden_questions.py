import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("northstar_golden", ROOT / "src" / "northstar.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GoldenQuestionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions = json.loads((ROOT / "data" / "golden-questions.json").read_text())

    def test_dataset_has_24_unique_questions_and_required_buckets(self):
        self.assertEqual(24, len(self.questions))
        self.assertEqual(24, len({item["id"] for item in self.questions}))
        self.assertGreaterEqual(len({item["bucket"] for item in self.questions}), 9)

    def test_every_golden_question_satisfies_its_contract(self):
        for item in self.questions:
            with self.subTest(question=item["id"]):
                platform = MODULE.NorthstarPlatform()
                principal = MODULE.Principal(item["id"], item["role"])
                mode = item["mode"]
                if mode in {"search", "search_any", "visibility"}:
                    ids = {hit["id"] for hit in platform.search(item["question"], principal, limit=12)}
                    if mode == "search":
                        self.assertTrue(set(item["expected_ids"]).issubset(ids))
                    elif mode == "search_any":
                        self.assertTrue(set(item["expected_ids"]) & ids)
                    else:
                        self.assertFalse(set(item["forbidden_ids"]) & ids)
                elif mode == "graph":
                    ids = {edge["to"] for edge in platform.trace(item["seed"], principal)}
                    self.assertTrue(set(item["expected_ids"]).issubset(ids))
                elif mode == "missing":
                    package = platform.context(item["question"], principal, item["id"], runtime_resource=item["resource"])
                    self.assertEqual(item["expected_missing"], package["missing"])
                elif mode == "tool_visibility":
                    tools = set(platform.allowed_tools(principal, item["id"]))
                    self.assertFalse(set(item["forbidden_tools"]) & tools)
                elif mode == "action_preview":
                    platform.begin_diagnosis(item["id"], principal)
                    self.assertIn(item["expected_tool"], platform.allowed_tools(principal, item["id"]))
                    preview = platform.prepare_replay(item["id"], "refund-queue", principal)
                    self.assertGreater(preview["message_count"], 0)
                else:
                    self.fail(f"unsupported mode: {mode}")


if __name__ == "__main__":
    unittest.main()
