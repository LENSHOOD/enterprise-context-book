from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from linux_kb import ingest_full, query_full, report_full
from linux_kb.full_kernel import _insert_node, _schema, subsystem


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "fixtures" / "linux"


class FullKernelModelTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "linux.db"
        self.manifest = ingest_full(FIXTURE, "fixture-v1", self.database, fixture=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_subsystem_partition(self):
        self.assertEqual("drivers/gpu", subsystem("drivers/gpu/drm/file.c"))
        self.assertEqual("arch/x86", subsystem("arch/x86/kernel/traps.c"))
        self.assertEqual("kernel", subsystem("kernel/bpf/syscall.c"))

    def test_streaming_manifest_and_database(self):
        self.assertEqual("sqlite-syntax-only", self.manifest["mode"])
        self.assertGreater(self.manifest["counts"]["nodes"], 5)
        self.assertTrue(self.database.exists())

    def test_full_query_finds_syscall_and_verifier(self):
        result = query_full(self.database, "BPF_PROG_LOAD verifier_prepare", limit=8)
        names = {hit["name"] for hit in result["hits"]}
        self.assertIn("verifier_prepare", names)
        self.assertTrue(any("syscall.c" in hit["path"] for hit in result["hits"]))

    def test_report_groups_subsystems_and_sizes_database(self):
        report = report_full(self.database)
        self.assertGreater(report["database_bytes"], 0)
        names = {item["subsystem"] for item in report["top_subsystems"]}
        self.assertIn("kernel", names)
        self.assertIn("include", names)

    def test_duplicate_insert_returns_existing_stable_id(self):
        connection = sqlite3.connect(":memory:")
        _schema(connection)
        values = ("stable:a", "type", "a", "a.c", "root", 1, "fixture:a", "a")
        first = _insert_node(connection, values)
        _insert_node(connection, ("stable:b", "type", "b", "b.c", "root", 1, "fixture:b", "b"))
        repeated = _insert_node(connection, values)
        self.assertEqual(first, repeated)
        self.assertEqual(1, connection.execute("SELECT id FROM nodes WHERE stable_id='stable:a'").fetchone()[0])
        connection.close()

    def test_full_ingest_reads_the_requested_git_revision(self):
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

        database = Path(self.temp.name) / "versioned.db"
        manifest = ingest_full(repo, "v-old", database, include_docs=False)
        result = query_full(database, "old_function new_function", limit=10)
        names = {hit["name"] for hit in result["hits"]}
        self.assertEqual(old_commit, manifest["commit"])
        self.assertIn("old_function", names)
        self.assertNotIn("new_function", names)


if __name__ == "__main__":
    unittest.main()
