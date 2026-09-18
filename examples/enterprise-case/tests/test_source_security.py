"""Regression coverage for source containment and fixture authorization metadata."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_baseline import compile_documents
from build_knowledge import compile_knowledge
from northstar import NorthstarPlatform, Principal
from strategy import StrategicContext


class SourceSecurityTest(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.data = Path(temporary_directory.name) / "data"
        shutil.copytree(ROOT / "data", self.data)
        self.raw = self.data / "raw"
        self.manifest_path = self.raw / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.source = next(
            item for item in self.manifest["sources"] if item["parser"] == "markdown"
        )
        self.knowledge_path = self.data / "knowledge.json"
        self.documents = json.loads(self.knowledge_path.read_text(encoding="utf-8"))
        self.strategy_path = self.data / "strategy-context.json"
        # A sibling with the same prefix also catches naive string-prefix checks.
        self.outside = self.data / "raw-sibling" / "outside.md"
        self.outside.parent.mkdir()
        self.outside.write_text("Outside-root sentinel.\n", encoding="utf-8")

    @staticmethod
    def write_json(path, payload):
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def assert_source_path_rejected(self, path):
        self.source["path"] = path
        self.write_json(self.manifest_path, self.manifest)
        with self.assertRaisesRegex(ValueError, "source path"):
            compile_documents(self.manifest_path)
        with self.assertRaisesRegex(ValueError, "source path"):
            compile_knowledge(self.data)

    def test_valid_fixtures_still_compile(self):
        raw = compile_documents(self.manifest_path)
        knowledge = compile_knowledge(self.data)
        self.assertEqual(len(self.manifest["sources"]), len(raw))
        self.assertEqual(len(self.documents), len(knowledge))
        compiled = {document["id"]: document for document in knowledge}
        for document in raw:
            self.assertEqual(document["text"], compiled[document["id"]]["text"])
        self.assertFalse(any("Outside-root sentinel" in doc["text"] for doc in knowledge))

    def test_absolute_source_paths_are_rejected(self):
        inside = self.raw / self.source["path"]
        for path in (inside, self.outside):
            with self.subTest(path=str(path)):
                self.assert_source_path_rejected(str(path.resolve()))

    def test_parent_traversal_and_repeated_slashes_are_rejected(self):
        for path in ("../raw-sibling/outside.md", "..//raw-sibling//outside.md"):
            with self.subTest(path=path):
                self.assert_source_path_rejected(path)

    def test_file_symlink_escape_is_rejected(self):
        (self.raw / "linked.md").symlink_to(self.outside)
        self.assert_source_path_rejected("linked.md")

    def test_directory_symlink_escape_is_rejected(self):
        (self.raw / "linked").symlink_to(self.outside.parent, target_is_directory=True)
        self.assert_source_path_rejected("linked/outside.md")

    def test_raw_source_without_tenant_is_rejected(self):
        self.source.pop("tenant")
        self.write_json(self.manifest_path, self.manifest)
        with self.assertRaisesRegex(ValueError, "source tenant"):
            compile_documents(self.manifest_path)
        with self.assertRaisesRegex(ValueError, "source tenant"):
            compile_knowledge(self.data)

    def test_authored_and_supplemental_objects_without_tenant_are_rejected(self):
        raw_ids = {item["id"] for item in self.manifest["sources"]}
        supplemental = next(doc for doc in self.documents if doc["id"] not in raw_ids)
        for document_id in (self.source["id"], supplemental["id"]):
            with self.subTest(document_id=document_id):
                documents = deepcopy(self.documents)
                next(doc for doc in documents if doc["id"] == document_id).pop("tenant")
                self.write_json(self.knowledge_path, documents)
                with self.assertRaisesRegex(ValueError, "knowledge tenant"):
                    compile_knowledge(self.data)

    def test_raw_string_acl_is_rejected(self):
        self.source["acl"] = "developer"
        self.write_json(self.manifest_path, self.manifest)
        with self.assertRaisesRegex(ValueError, "source ACL"):
            compile_documents(self.manifest_path)
        with self.assertRaisesRegex(ValueError, "source ACL"):
            compile_knowledge(self.data)

    def test_authored_and_supplemental_string_acls_are_rejected(self):
        raw_ids = {item["id"] for item in self.manifest["sources"]}
        supplemental = next(doc for doc in self.documents if doc["id"] not in raw_ids)
        for document_id in (self.source["id"], supplemental["id"]):
            with self.subTest(document_id=document_id):
                documents = deepcopy(self.documents)
                next(doc for doc in documents if doc["id"] == document_id)["acl"] = "developer"
                self.write_json(self.knowledge_path, documents)
                with self.assertRaisesRegex(ValueError, "knowledge ACL"):
                    compile_knowledge(self.data)

    def test_allowed_denies_missing_and_foreign_tenants(self):
        principal = Principal("reader", "developer", "northstar")
        self.assertFalse(NorthstarPlatform.allowed({"acl": ["developer"]}, principal))
        self.assertFalse(NorthstarPlatform.allowed(
            {"tenant": "other", "acl": ["developer"]}, principal
        ))
        self.assertTrue(NorthstarPlatform.allowed(
            {"tenant": "northstar", "acl": ["developer"]}, principal
        ))

    def test_allowed_requires_a_list_and_an_exact_role(self):
        for acl in ("developer", ["developer"]):
            with self.subTest(acl=acl):
                document = {"tenant": "northstar", "acl": acl}
                self.assertFalse(NorthstarPlatform.allowed(document, Principal("reader", "dev")))
                self.assertEqual(
                    isinstance(acl, list),
                    NorthstarPlatform.allowed(document, Principal("reader", "developer")),
                )

    def test_c7_rejects_string_acl(self):
        data = json.loads(self.strategy_path.read_text(encoding="utf-8"))
        data["fixture"]["acl"] = "executive"
        self.write_json(self.strategy_path, data)
        with self.assertRaisesRegex(ValueError, "strategy ACL"):
            StrategicContext(self.strategy_path)

    def test_c7_valid_acl_requires_an_exact_role(self):
        context = StrategicContext(self.strategy_path)
        confirmation = context.definition_confirmation()
        for role in ("e", "cutive"):
            with self.subTest(role=role), self.assertRaises(PermissionError):
                context.package(
                    "H1 H2 sales",
                    {"user_id": "reader", "tenant": "northstar", "role": role},
                    confirmation=confirmation,
                )
        package = context.package(
            "H1 H2 sales",
            {"user_id": "reader", "tenant": "northstar", "role": "executive"},
            confirmation=confirmation,
        )
        self.assertEqual("ready_for_review", package["status"])


if __name__ == "__main__":
    unittest.main()
