import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


BUILD = load_module("build_baseline", ROOT / "src" / "build_baseline.py")
CONTEXT = load_module("context_demo_for_baseline", ROOT / "src" / "context_demo.py")


class BuildBaselineTest(unittest.TestCase):
    def test_compiler_rebuilds_versioned_objects_from_raw_sources(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "baseline-knowledge.json"
            first = BUILD.write_documents(output)
            first_bytes = output.read_bytes()
            second = BUILD.write_documents(output)

            self.assertEqual(first, second)
            self.assertEqual(first_bytes, output.read_bytes())
            self.assertEqual(5, len(first))
            self.assertTrue(all(item["lineage"]["transform"] == "baseline-compiler@1" for item in first))
            self.assertTrue(all(item["content_hash"].startswith("sha256:") for item in first))

            code = next(item for item in first if item["id"] == "code-refund-consumer")
            self.assertIn("handle_order_cancelled", code["text"])
            self.assertTrue(code["citation"].startswith("code://"))

    def test_compiled_baseline_enforces_acl_before_bm25(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "baseline-knowledge.json"
            BUILD.write_documents(output)
            developer = CONTEXT.query(output, "handle_order_cancelled create_refund", "developer", limit=5)
            support = CONTEXT.query(output, "handle_order_cancelled create_refund", "support", limit=5)

            self.assertIn("code-refund-consumer", {hit["id"] for hit in developer["hits"]})
            self.assertNotIn("code-refund-consumer", {hit["id"] for hit in support["hits"]})

    def test_manifest_is_machine_readable_source_inventory(self):
        manifest = json.loads((ROOT / "data" / "raw" / "manifest.json").read_text())
        self.assertEqual("northstar-raw-fixture/1", manifest["format"])
        self.assertEqual(5, len(manifest["sources"]))
        self.assertEqual(
            {"markdown", "json", "python_symbol"},
            {item["parser"] for item in manifest["sources"]},
        )


if __name__ == "__main__":
    unittest.main()
