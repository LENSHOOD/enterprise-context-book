from pathlib import Path
import tempfile
import subprocess
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
            fixture=True,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_manifest_is_pinned_and_reports_mode(self):
        self.assertTrue(self.manifest["commit"].startswith("fixture:fixture-v1:"))
        self.assertEqual("syntax-only", self.manifest["mode"])
        self.assertGreaterEqual(self.manifest["counts"]["files"], 4)

    def test_extracts_command_functions_types_and_versioned_citations(self):
        snapshot = load_snapshot(self.output)
        ids = {node["id"] for node in snapshot["nodes"]}
        self.assertIn("command:include/uapi/linux/bpf.h#BPF_PROG_LOAD:L3", ids)
        self.assertTrue(any(n['kind']=='function' and n['name']=='__sys_bpf' for n in snapshot['nodes']))
        self.assertIn("type:kernel/bpf/verifier.c#bpf_reg_state:L1", ids)
        self.assertTrue(all("@fixture:fixture-v1" in node["citation"] for node in snapshot["nodes"]))

    def test_resolves_unique_name_calls_but_labels_certainty(self):
        snapshot = load_snapshot(self.output)
        calls = [edge for edge in snapshot["edges"] if edge["type"] == "CALLS_RESOLVED_NAME"]
        by_id = {node['id']:node for node in snapshot['nodes']}
        pairs = {(by_id[edge['from']]['name'], by_id[edge['to']]['name']) for edge in calls}
        self.assertIn(('bpf_prog_load', 'bpf_check'), pairs)
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

    def test_git_ref_reads_the_requested_tree(self):
        repo = Path(self.temp.name) / "git-repo"
        repo.mkdir()
        def git(*args):
            return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
        git("init")
        git("config", "user.name", "fixture")
        git("config", "user.email", "fixture@example.invalid")
        source = repo / "version.c"
        source.write_text("int old_function(void) { return 1; }\n")
        git("add", "version.c")
        git("commit", "-m", "old")
        git("tag", "v-old")
        old_commit = git("rev-parse", "HEAD")
        source.write_text("int new_function(void) { return 2; }\n")
        git("add", "version.c")
        git("commit", "-m", "new")

        result = ingest(repo, "v-old", self.output / "versioned", ["*.c"])
        snapshot = load_snapshot(self.output / "versioned")
        names = {node["name"] for node in snapshot["nodes"] if node["kind"] == "function"}
        self.assertEqual(old_commit, result["commit"])
        self.assertEqual({"old_function"}, names)
        self.assertTrue(all(f"@{old_commit}" in node["citation"] for node in snapshot["nodes"]))

    def test_git_ref_and_repository_errors_are_explicit(self):
        with self.assertRaises(FileNotFoundError):
            ingest(Path(self.temp.name) / "missing", "v1", self.output / "missing", ["*.c"])


if __name__ == "__main__":
    unittest.main()
