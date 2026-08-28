from pathlib import Path
import tempfile
import unittest

from linux_kb import build_wiki, ingest, load_snapshot, query


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "fixtures" / "linux"


class LinuxKnowledgeBaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name)
        self.manifest = ingest(
            FIXTURE, "fixture-v1", self.output,
            ["kernel/bpf/*.c", "include/uapi/linux/bpf.h", "Documentation/bpf/*.rst"],
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_manifest_is_pinned_and_reports_mode(self):
        self.assertEqual("fixture:fixture-v1", self.manifest["commit"])
        self.assertEqual("syntax-only", self.manifest["mode"])
        self.assertGreaterEqual(self.manifest["counts"]["files"], 4)

    def test_extracts_command_functions_types_and_versioned_citations(self):
        snapshot = load_snapshot(self.output)
        ids = {node["id"] for node in snapshot["nodes"]}
        self.assertIn("command:BPF_PROG_LOAD", ids)
        self.assertIn("symbol:kernel/bpf/syscall.c#__sys_bpf", ids)
        self.assertIn("type:bpf_reg_state", ids)
        self.assertTrue(all("@fixture:fixture-v1" in node["citation"] for node in snapshot["nodes"]))

    def test_resolves_unique_name_calls_but_labels_certainty(self):
        snapshot = load_snapshot(self.output)
        calls = [edge for edge in snapshot["edges"] if edge["type"] == "CALLS_RESOLVED_NAME"]
        pairs = {(edge["from"], edge["to"]) for edge in calls}
        self.assertIn(("symbol:kernel/bpf/syscall.c#bpf_prog_load", "symbol:kernel/bpf/syscall.c#bpf_check"), pairs)
        self.assertTrue(all(edge["certainty"] == "name-resolved" for edge in calls))

    def test_unresolved_edges_do_not_claim_precision(self):
        snapshot = load_snapshot(self.output)
        self.assertTrue(all(item["reason"] in {"not-found", "ambiguous"} for item in snapshot["unresolved"]))
        unresolved_edges = [edge for edge in snapshot["edges"] if edge["to"].startswith("unresolved:")]
        self.assertTrue(all(edge["certainty"] == "syntax-candidate" for edge in unresolved_edges))

    def test_query_returns_source_evidence_and_warning(self):
        result = query(self.output, "BPF_PROG_LOAD verifier_prepare")
        self.assertTrue(result["hits"])
        self.assertTrue(all(hit["citation"].startswith("code://linux/kernel@") for hit in result["hits"]))
        self.assertIn("syntax-only: calls are not compiler-proven", result["warnings"])

    def test_wiki_contains_snapshot_and_symbols(self):
        wiki = build_wiki(self.output)
        self.assertIn("fixture:fixture-v1", wiki)
        self.assertIn("verifier_prepare", wiki)
        self.assertTrue((self.output / "wiki.md").exists())


if __name__ == "__main__":
    unittest.main()
