import json
import unittest
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DomainModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads((ROOT / "data" / "domain-model.json").read_text())
        cls.documents = json.loads((ROOT / "data" / "knowledge.json").read_text())
        cls.edges = json.loads((ROOT / "data" / "relations.json").read_text())

    def test_competency_questions_reference_declared_relations(self):
        declared = set(self.model["relations"])
        for question in self.model["competencyQuestions"]:
            self.assertTrue(set(question["requiredRelations"]).issubset(declared))

    def test_relations_reference_declared_entity_types(self):
        declared = set(self.model["entityTypes"])
        for name, relation in self.model["relations"].items():
            with self.subTest(relation=name):
                self.assertIn(relation["from"], declared)
                self.assertIn(relation["to"], declared)
                self.assertTrue(relation["allowedEvidence"])

    def test_temporal_relations_are_explicit(self):
        self.assertTrue(self.model["relations"]["CALLS"]["temporal"])
        self.assertTrue(self.model["relations"]["GOVERNED_BY"]["temporal"])
        self.assertTrue(self.model["relations"]["GOVERNED_BY"]["constraints"])

    def test_every_relation_edge_conforms_to_declared_model(self):
        documents = {document["id"]: document for document in self.documents}
        for edge in self.edges:
            with self.subTest(edge=edge):
                relation = self.model["relations"][edge["type"]]
                self.assertEqual(relation["from"], documents[edge["from"]]["entity_type"])
                self.assertEqual(relation["to"], documents[edge["to"]]["entity_type"])
                self.assertIn(edge["evidence_tier"], relation["allowedEvidence"])

    def test_competency_questions_have_instance_edges(self):
        instantiated = {edge["type"] for edge in self.edges}
        for question in self.model["competencyQuestions"]:
            with self.subTest(question=question["id"]):
                self.assertTrue(set(question["requiredRelations"]).issubset(instantiated))

    def test_every_document_has_governance_envelope(self):
        required = {"version_id", "source", "time", "lineage", "content_hash", "entity_type"}
        for document in self.documents:
            with self.subTest(document=document["id"]):
                self.assertTrue(required.issubset(document))
                self.assertTrue(document["content_hash"].startswith("sha256:"))

    def test_policy_versions_have_contiguous_valid_time(self):
        policies = {document["id"]: document for document in self.documents}
        old = policies["product-cancellation-policy-v1"]["time"]
        current = policies["product-cancellation-policy"]["time"]
        self.assertEqual(old["valid_to"], current["valid_from"])

    def test_valid_time_precedes_system_observation_time(self):
        for document in self.documents:
            with self.subTest(document=document["id"]):
                valid_from = datetime.fromisoformat(document["time"]["valid_from"].replace("Z", "+00:00"))
                observed_at = datetime.fromisoformat(document["time"]["observed_at"].replace("Z", "+00:00"))
                self.assertLessEqual(valid_from, observed_at)

    def test_date_versions_start_on_their_business_date(self):
        for document in self.documents:
            version = document["version"]
            if len(version) == 10 and version[4] == "-" and version[7] == "-":
                with self.subTest(document=document["id"]):
                    self.assertTrue(document["time"]["valid_from"].startswith(version))


if __name__ == "__main__":
    unittest.main()
