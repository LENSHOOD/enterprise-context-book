from pathlib import Path
import tempfile
import unittest

from linux_kb import ingest_full, query_full, report_full
from linux_kb.full_kernel import subsystem


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "fixtures" / "linux"


class FullKernelModelTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "linux.db"
        self.manifest = ingest_full(FIXTURE, "fixture-v1", self.database)

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


if __name__ == "__main__":
    unittest.main()
