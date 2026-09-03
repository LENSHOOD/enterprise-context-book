import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from modeling import (
    ModelValidationError,
    compile_domain_model,
    validate_domain_model,
    validate_instances,
)


class KnowledgeModelingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = compile_domain_model(ROOT / "data" / "modeling")
        cls.documents = json.loads((ROOT / "data" / "knowledge.json").read_text())
        cls.edges = json.loads((ROOT / "data" / "relations.json").read_text())

    def test_authoring_assets_compile_into_an_executable_model(self):
        self.assertEqual("northstar-domain-model/2", self.model["format"])
        self.assertEqual(12, len(self.model["glossary"]))
        self.assertEqual(set(self.model["entityTypes"]), {
            term["canonicalName"] for term in self.model["glossary"]
        })
        self.assertEqual(3, len(self.model["competencyQuestions"]))

    def test_every_model_element_has_a_source_mapping(self):
        mapped = {
            product
            for mapping in self.model["sourceMappings"]
            for product in mapping["produces"]
        }
        self.assertTrue(set(self.model["entityTypes"]).issubset(mapped))
        self.assertTrue(set(self.model["relations"]).issubset(mapped))

    def test_fixture_instances_support_every_competency_question(self):
        report = validate_instances(self.model, self.documents, self.edges)
        self.assertTrue(report["valid"])
        self.assertTrue(all(item["supported"] for item in report["competency_questions"]))
        self.assertTrue(
            all(item["connectedAnswerSubgraph"] for item in report["competency_questions"])
        )
        event_question = next(
            item for item in report["competency_questions"] if item["id"] == "CQ-EVENT-001"
        )
        self.assertEqual(
            {"CONSUMED_BY", "TESTED_BY"}, set(event_question["sampleEvidence"])
        )

    def test_ambiguous_enterprise_language_inside_one_context_is_rejected(self):
        invalid = copy.deepcopy(self.model)
        operations_term = next(
            term for term in invalid["glossary"]
            if term["boundedContext"] == "operations" and term["id"] != "term.service"
        )
        operations_term["aliases"].append("运行服务")
        with self.assertRaisesRegex(ModelValidationError, "ambiguous"):
            validate_domain_model(invalid)

    def test_same_language_label_in_different_bounded_contexts_is_namespaced(self):
        valid = copy.deepcopy(self.model)
        engineering_term = next(
            term for term in valid["glossary"]
            if term["boundedContext"] == "engineering"
        )
        engineering_term["aliases"].append("运行服务")
        self.assertTrue(validate_domain_model(valid)["valid"])

    def test_wrong_relation_direction_is_rejected(self):
        invalid_edges = copy.deepcopy(self.edges)
        invalid_edges[0]["from"], invalid_edges[0]["to"] = (
            invalid_edges[0]["to"], invalid_edges[0]["from"]
        )
        with self.assertRaisesRegex(ModelValidationError, "source must be EventSchema"):
            validate_instances(self.model, self.documents, invalid_edges)

    def test_policy_relation_must_hold_at_event_region_and_time(self):
        invalid_edges = copy.deepcopy(self.edges)
        governed = next(edge for edge in invalid_edges if edge["type"] == "GOVERNED_BY")
        governed["to"] = "product-cancellation-policy-v1"
        with self.assertRaisesRegex(ModelValidationError, "not valid at the event time"):
            validate_instances(self.model, self.documents, invalid_edges)

    def test_event_cannot_have_overlapping_policy_targets(self):
        invalid_edges = copy.deepcopy(self.edges)
        governed = next(edge for edge in invalid_edges if edge["type"] == "GOVERNED_BY")
        conflicting = copy.deepcopy(governed)
        policy = copy.deepcopy(
            next(item for item in self.documents if item["id"] == governed["to"])
        )
        policy["id"] = "product-cancellation-policy-correction"
        invalid_documents = [*self.documents, policy]
        conflicting["to"] = policy["id"]
        conflicting["evidence"] += "#conflict"
        invalid_edges.append(conflicting)
        with self.assertRaisesRegex(ModelValidationError, "overlapping targets"):
            validate_instances(self.model, invalid_documents, invalid_edges)

    def test_corrected_policy_mapping_may_use_a_non_overlapping_window(self):
        edges = copy.deepcopy(self.edges)
        governed = next(edge for edge in edges if edge["type"] == "GOVERNED_BY")
        governed["time"]["valid_to"] = "2026-08-23T00:00:00Z"
        policy = copy.deepcopy(
            next(item for item in self.documents if item["id"] == governed["to"])
        )
        policy["id"] = "product-cancellation-policy-correction"
        corrected = copy.deepcopy(governed)
        corrected["to"] = policy["id"]
        corrected["evidence"] += "#corrected"
        corrected["time"]["valid_from"] = "2026-08-23T00:00:00Z"
        corrected["time"]["valid_to"] = None
        corrected["time"]["observed_at"] = "2026-08-23T00:00:00Z"
        edges.append(corrected)
        report = validate_instances(self.model, [*self.documents, policy], edges)
        self.assertTrue(report["valid"])

    def test_temporal_relation_requires_an_explicit_time_envelope(self):
        invalid_edges = copy.deepcopy(self.edges)
        temporal_edge = next(
            edge for edge in invalid_edges
            if self.model["relations"][edge["type"]].get("temporal")
        )
        temporal_edge.pop("time")
        with self.assertRaisesRegex(ModelValidationError, "time envelope"):
            validate_instances(self.model, self.documents, invalid_edges)

    def test_temporal_relation_rejects_an_invalid_interval(self):
        invalid_edges = copy.deepcopy(self.edges)
        temporal_edge = next(
            edge for edge in invalid_edges
            if self.model["relations"][edge["type"]].get("temporal")
        )
        temporal_edge["time"]["valid_to"] = temporal_edge["time"]["valid_from"]
        with self.assertRaisesRegex(ModelValidationError, "must be after valid_from"):
            validate_instances(self.model, self.documents, invalid_edges)

    def test_every_declared_model_element_must_be_exercised_by_the_fixture(self):
        without_adr = [item for item in self.documents if item["entity_type"] != "ADR"]
        with self.assertRaisesRegex(ModelValidationError, "entity types have no fixture instances"):
            validate_instances(self.model, without_adr, self.edges)
        without_affected = [edge for edge in self.edges if edge["type"] != "AFFECTED"]
        with self.assertRaisesRegex(ModelValidationError, "relation types have no fixture instances"):
            validate_instances(self.model, self.documents, without_affected)

    def test_question_relations_must_form_one_answer_subgraph(self):
        documents = copy.deepcopy(self.documents)
        detached_service = copy.deepcopy(
            next(item for item in documents if item["id"] == "service-refund-worker")
        )
        detached_service["id"] = "service-detached"
        documents.append(detached_service)
        edges = copy.deepcopy(self.edges)
        documented = next(edge for edge in edges if edge["type"] == "DOCUMENTED_BY")
        documented["from"] = "service-detached"
        with self.assertRaisesRegex(ModelValidationError, "connected answer subgraph"):
            validate_instances(self.model, documents, edges)

    def test_cli_writes_model_and_validation_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "domain-model.json"
            report = Path(directory) / "model-validation.json"
            result = subprocess.check_output(
                [
                    sys.executable,
                    str(SRC / "build_domain_model.py"),
                    "--output",
                    str(output),
                    "--report",
                    str(report),
                ],
                text=True,
            )
            summary = json.loads(result)
            self.assertTrue(summary["valid"])
            self.assertEqual(3, summary["supported_questions"])
            self.assertEqual(self.model, json.loads(output.read_text()))
            self.assertTrue(json.loads(report.read_text())["instances"]["valid"])


if __name__ == "__main__":
    unittest.main()
