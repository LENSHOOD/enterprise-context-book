"""Compile and validate the Northstar enterprise knowledge model.

The files in ``data/modeling`` are authoring artifacts: questions, language,
concepts, relation contracts, and source mappings.  This module turns them into
one executable domain-model contract and checks that the fixture instances can
actually satisfy it.  It is intentionally small and deterministic; production
model governance still needs review workflows, migrations, and durable stores.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).parents[1]
DEFAULT_MODEL_DIR = ROOT / "data" / "modeling"
EVIDENCE_TIERS = {"deterministic", "resolved", "observed", "asserted"}
CARDINALITIES = {"many_to_many", "one_to_many", "many_to_one_at_event_time"}


class ModelValidationError(ValueError):
    """Raised when the model or its fixture instances violate the contract."""


def _read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_format(payload: dict, expected: str, path: Path) -> None:
    if payload.get("format") != expected:
        raise ModelValidationError(f"{path.name} must use {expected}")


def compile_domain_model(model_dir: Path = DEFAULT_MODEL_DIR) -> dict:
    """Compile the four reviewable modeling inputs into one runtime contract."""
    questions = _read_json(model_dir / "competency-questions.json")
    glossary = _read_json(model_dir / "glossary.json")
    concepts = _read_json(model_dir / "concept-model.json")
    mappings = _read_json(model_dir / "source-mappings.json")
    _require_format(questions, "northstar-competency-questions/1", model_dir / "competency-questions.json")
    _require_format(glossary, "northstar-glossary/1", model_dir / "glossary.json")
    _require_format(concepts, "northstar-concept-model/1", model_dir / "concept-model.json")
    _require_format(mappings, "northstar-source-mappings/1", model_dir / "source-mappings.json")

    model = {
        "format": "northstar-domain-model/2",
        "modelId": concepts["modelId"],
        "version": concepts["version"],
        "status": concepts["status"],
        "boundedContexts": concepts["boundedContexts"],
        "competencyQuestions": questions["questions"],
        "glossary": glossary["terms"],
        "entityTypes": concepts["entityTypes"],
        "relations": concepts["relations"],
        "sourceMappings": mappings["mappings"],
    }
    validate_domain_model(model)
    return model


def validate_domain_model(model: dict) -> dict:
    """Validate language, type, relation, question, and source contracts."""
    errors: list[str] = []
    for field in ("modelId", "version", "status"):
        if not model.get(field):
            errors.append(f"domain model has no {field}")

    context_definitions = model.get("boundedContexts", {})
    contexts = set(context_definitions)
    for context_name, context in context_definitions.items():
        for field in ("label", "owner"):
            if not context.get(field):
                errors.append(f"bounded context {context_name} has no {field}")
    entity_types = model.get("entityTypes", {})
    relations = model.get("relations", {})
    glossary = model.get("glossary", [])
    terms = {term.get("id"): term for term in glossary}

    if len(terms) != len(glossary):
        errors.append("glossary term ids must be unique")

    language_owner: dict[tuple[str, str], str] = {}
    for term in glossary:
        term_id = term.get("id", "<missing>")
        bounded_context = term.get("boundedContext")
        if bounded_context not in contexts:
            errors.append(f"{term_id} references an unknown bounded context")
        for field in ("definition", "steward"):
            if not term.get(field):
                errors.append(f"{term_id} has no {field}")
        for label in [term.get("canonicalName"), term.get("preferredLabel"), *term.get("aliases", [])]:
            if not label:
                errors.append(f"{term_id} contains an empty language label")
                continue
            key = (bounded_context, " ".join(label.casefold().split()))
            previous = language_owner.get(key)
            if previous and previous != term_id:
                errors.append(
                    f"language label {label!r} is ambiguous inside {bounded_context} "
                    f"between {previous} and {term_id}"
                )
            language_owner[key] = term_id

    for name, definition in entity_types.items():
        term = terms.get(definition.get("glossaryTerm"))
        if not term:
            errors.append(f"entity type {name} has no glossary term")
        elif term.get("canonicalName") != name:
            errors.append(f"entity type {name} does not match glossary canonicalName")
        if definition.get("boundedContext") not in contexts:
            errors.append(f"entity type {name} references an unknown bounded context")
        elif term and term.get("boundedContext") != definition.get("boundedContext"):
            errors.append(f"entity type {name} and its glossary term use different bounded contexts")
        if not definition.get("identity"):
            errors.append(f"entity type {name} has no identity rule")

    for name, relation in relations.items():
        if relation.get("from") not in entity_types or relation.get("to") not in entity_types:
            errors.append(f"relation {name} references an unknown endpoint type")
        if not relation.get("allowedEvidence"):
            errors.append(f"relation {name} has no allowed evidence tier")
        else:
            unknown_tiers = set(relation["allowedEvidence"]) - EVIDENCE_TIERS
            if unknown_tiers:
                errors.append(f"relation {name} uses unknown evidence tiers {sorted(unknown_tiers)}")
        if relation.get("cardinality") not in CARDINALITIES:
            errors.append(f"relation {name} has an unsupported cardinality")
        for field in ("cardinality", "meaning", "positiveExample", "negativeExample"):
            if not relation.get(field):
                errors.append(f"relation {name} has no {field}")

    question_ids: set[str] = set()
    for question in model.get("competencyQuestions", []):
        question_id = question.get("id", "<missing>")
        if question_id in question_ids:
            errors.append(f"competency question id {question_id} is duplicated")
        question_ids.add(question_id)
        unknown_types = set(question.get("requiredEntityTypes", [])) - set(entity_types)
        unknown_relations = set(question.get("requiredRelations", [])) - set(relations)
        if unknown_types:
            errors.append(f"{question_id} references unknown entity types {sorted(unknown_types)}")
        if unknown_relations:
            errors.append(f"{question_id} references unknown relations {sorted(unknown_relations)}")
        for field in ("question", "decision", "requiredEntityTypes", "requiredRelations"):
            if not question.get(field):
                errors.append(f"{question_id} has no {field}")

    declared_products = set(entity_types) | set(relations)
    mapped_products: set[str] = set()
    mapped_sources: set[str] = set()
    for mapping in model.get("sourceMappings", []):
        source = mapping.get("source", "<missing>")
        if source in mapped_sources:
            errors.append(f"source mapping {source} is duplicated")
        mapped_sources.add(source)
        products = set(mapping.get("produces", []))
        if not products:
            errors.append(f"source {source} produces no model elements")
        unknown = products - declared_products
        if unknown:
            errors.append(f"source {source} produces unknown model elements {sorted(unknown)}")
        for field in ("owner", "identityRule", "refreshMode"):
            if not mapping.get(field):
                errors.append(f"source {source} has no {field}")
        mapped_products.update(products)
    unmapped = declared_products - mapped_products
    if unmapped:
        errors.append(f"model elements have no source mapping: {sorted(unmapped)}")

    if errors:
        raise ModelValidationError("; ".join(errors))
    return {
        "valid": True,
        "glossary_terms": len(glossary),
        "entity_types": len(entity_types),
        "relation_types": len(relations),
        "competency_questions": len(model.get("competencyQuestions", [])),
        "source_mappings": len(model.get("sourceMappings", [])),
    }


def validate_instances(model: dict, documents: list[dict], edges: list[dict]) -> dict:
    """Check that concrete objects and edges conform to and exercise the model."""
    errors: list[str] = []
    documents_by_id: dict[str, dict] = {}
    entity_types = model["entityTypes"]
    relations = model["relations"]

    def parse_instant(value: str | None, label: str) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            errors.append(f"{label} is not an ISO-8601 instant")
            return None

    def validate_time_envelope(envelope: dict, label: str) -> None:
        valid_from = parse_instant(envelope.get("valid_from"), f"{label}.valid_from")
        observed_at = parse_instant(envelope.get("observed_at"), f"{label}.observed_at")
        valid_to = parse_instant(envelope.get("valid_to"), f"{label}.valid_to")
        if not valid_from or not observed_at:
            errors.append(f"{label} has no complete time envelope")
        if valid_from and valid_to and valid_to <= valid_from:
            errors.append(f"{label}.valid_to must be after valid_from")

    for document in documents:
        document_id = document.get("id")
        if not document_id:
            errors.append("knowledge object has no id")
            continue
        if document_id in documents_by_id:
            errors.append(f"duplicate object id {document_id}")
            continue
        documents_by_id[document_id] = document
        if document.get("entity_type") not in entity_types:
            errors.append(f"object {document_id} has undeclared type {document.get('entity_type')}")
        else:
            entity_definition = entity_types[document["entity_type"]]
            required = set(entity_definition.get("requiredProperties", []))
            missing = required - set(document.get("attributes", {}))
            if missing:
                errors.append(f"object {document_id} lacks required properties {sorted(missing)}")
            if entity_definition.get("temporal"):
                validate_time_envelope(
                    document.get("time", {}), f"temporal object {document_id}"
                )

    instantiated_relations: dict[str, list[dict]] = {name: [] for name in relations}
    seen_edges: set[tuple[str, str, str, str]] = set()
    many_to_one_windows: dict[tuple[str, str], list[tuple[str, datetime, datetime | None]]] = {}
    for edge in edges:
        relation_name = edge.get("type")
        relation = relations.get(relation_name)
        if not relation:
            errors.append(f"edge uses undeclared relation {relation_name}")
            continue
        source = documents_by_id.get(edge.get("from"))
        target = documents_by_id.get(edge.get("to"))
        if not source or not target:
            errors.append(f"{relation_name} edge references a missing endpoint")
            continue
        if source.get("entity_type") != relation["from"]:
            errors.append(f"{relation_name} source must be {relation['from']}, got {source.get('entity_type')}")
        if target.get("entity_type") != relation["to"]:
            errors.append(f"{relation_name} target must be {relation['to']}, got {target.get('entity_type')}")
        if edge.get("evidence_tier") not in relation["allowedEvidence"]:
            errors.append(f"{relation_name} uses disallowed evidence tier {edge.get('evidence_tier')}")
        if not edge.get("evidence"):
            errors.append(f"{relation_name} edge has no evidence URI")
        edge_key = (edge.get("from"), relation_name, edge.get("to"), edge.get("evidence"))
        if edge_key in seen_edges:
            errors.append(f"duplicate relation edge {edge_key[:3]}")
        seen_edges.add(edge_key)
        if relation.get("temporal"):
            validate_time_envelope(
                edge.get("time", {}),
                f"temporal relation {relation_name} {edge.get('from')}->{edge.get('to')}",
            )
        if relation.get("cardinality") == "many_to_one_at_event_time":
            source_key = (relation_name, edge.get("from"))
            edge_time = edge.get("time", {})
            edge_from = parse_instant(
                edge_time.get("valid_from"), f"{relation_name}.valid_from"
            )
            edge_to = parse_instant(
                edge_time.get("valid_to"), f"{relation_name}.valid_to"
            )
            if edge_from:
                for previous_target, previous_from, previous_to in many_to_one_windows.get(
                    source_key, []
                ):
                    overlaps = (
                        (previous_to is None or edge_from < previous_to)
                        and (edge_to is None or previous_from < edge_to)
                    )
                    if previous_target != edge.get("to") and overlaps:
                        errors.append(
                            f"{relation_name} has overlapping targets for {edge.get('from')}"
                        )
                many_to_one_windows.setdefault(source_key, []).append(
                    (edge.get("to"), edge_from, edge_to)
                )
        if relation_name == "GOVERNED_BY":
            event = source.get("attributes", {})
            policy_regions = target.get("attributes", {}).get("regions", [])
            occurred_at = event.get("occurred_at")
            if event.get("region") not in policy_regions:
                errors.append("GOVERNED_BY policy does not cover the event region")
            if occurred_at:
                occurred = parse_instant(occurred_at, "RefundEvent.occurred_at")
                valid_from = parse_instant(
                    target.get("time", {}).get("valid_from"), "Policy.valid_from"
                )
                valid_to_value = target.get("time", {}).get("valid_to")
                valid_to = parse_instant(valid_to_value, "Policy.valid_to")
                if (
                    occurred
                    and valid_from
                    and not (
                        valid_from <= occurred
                        and (valid_to is None or occurred < valid_to)
                    )
                ):
                    errors.append("GOVERNED_BY policy is not valid at the event time")
        instantiated_relations[relation_name].append(edge)

    instantiated_types = {document.get("entity_type") for document in documents}
    missing_instantiated_types = sorted(set(entity_types) - instantiated_types)
    missing_instantiated_relations = sorted(
        name for name, items in instantiated_relations.items() if not items
    )
    if missing_instantiated_types:
        errors.append(f"entity types have no fixture instances: {missing_instantiated_types}")
    if missing_instantiated_relations:
        errors.append(f"relation types have no fixture instances: {missing_instantiated_relations}")
    question_results = []
    for question in model["competencyQuestions"]:
        missing_types = sorted(set(question["requiredEntityTypes"]) - instantiated_types)
        missing_relations = sorted(
            name for name in question["requiredRelations"] if not instantiated_relations.get(name)
        )
        required_edges = [
            edge for name in question["requiredRelations"]
            for edge in instantiated_relations.get(name, [])
        ]
        components: list[dict[str, set[str]]] = []
        for edge in required_edges:
            touching = [
                component for component in components
                if edge["from"] in component["nodes"] or edge["to"] in component["nodes"]
            ]
            merged = {
                "nodes": {edge["from"], edge["to"]},
                "relations": {edge["type"]},
            }
            for component in touching:
                merged["nodes"].update(component["nodes"])
                merged["relations"].update(component["relations"])
                components.remove(component)
            components.append(merged)
        answer_component = next(
            (
                component for component in components
                if set(question["requiredEntityTypes"]).issubset({
                    documents_by_id[document_id]["entity_type"]
                    for document_id in component["nodes"]
                })
                and set(question["requiredRelations"]).issubset(component["relations"])
            ),
            None,
        )
        connected = answer_component is not None
        supported = not missing_types and not missing_relations and connected
        question_results.append({
            "id": question["id"],
            "supported": supported,
            "missingEntityTypes": missing_types,
            "missingRelations": missing_relations,
            "connectedAnswerSubgraph": connected,
            "sampleObjectIds": sorted(answer_component["nodes"]) if answer_component else [],
            "sampleEvidence": {
                name: next(
                    edge["evidence"] for edge in instantiated_relations[name]
                    if answer_component
                    and edge["from"] in answer_component["nodes"]
                    and edge["to"] in answer_component["nodes"]
                )
                for name in question["requiredRelations"]
                if answer_component and instantiated_relations.get(name)
            },
        })
        if not supported:
            errors.append(
                f"{question['id']} lacks types {missing_types}, relations {missing_relations}, "
                f"or a connected answer subgraph"
            )

    if errors:
        raise ModelValidationError("; ".join(errors))
    return {
        "valid": True,
        "object_count": len(documents),
        "edge_count": len(edges),
        "instantiated_entity_types": len(instantiated_types),
        "instantiated_relation_types": sum(bool(items) for items in instantiated_relations.values()),
        "competency_questions": question_results,
    }


def validate_knowledge_base(model: dict, documents: list[dict], edges: list[dict]) -> dict:
    """Return one report suitable for a build gate or a teaching checkpoint."""
    return {
        "model": validate_domain_model(model),
        "instances": validate_instances(model, documents, edges),
    }


def semantic_slice(
    model: dict,
    documents: list[dict],
    edges: list[dict],
    competency_question: dict | None = None,
) -> dict:
    """Select the model contract needed to interpret a returned context package."""
    observed_type_names = {document["entity_type"] for document in documents}
    observed_relation_names = {edge["type"] for edge in edges}
    for relation_name in observed_relation_names:
        relation = model["relations"][relation_name]
        observed_type_names.update((relation["from"], relation["to"]))
    type_names = set(observed_type_names)
    relation_names = set(observed_relation_names)
    competency_coverage = None
    if competency_question:
        required_types = set(competency_question["requiredEntityTypes"])
        required_relations = set(competency_question["requiredRelations"])
        missing_types = sorted(required_types - observed_type_names)
        missing_relations = sorted(required_relations - observed_relation_names)
        competency_coverage = {
            "satisfied": not missing_types and not missing_relations,
            "observed_entity_types": sorted(required_types & observed_type_names),
            "observed_relations": sorted(required_relations & observed_relation_names),
            "missing_entity_types": missing_types,
            "missing_relations": missing_relations,
        }
        # A selected competency question is the query plan's semantic boundary.
        # Retrieved text may contribute evidence but must not widen the task
        # contract with unrelated schema. Coverage still records what the
        # authorized evidence and graph actually supplied.
        type_names = required_types
        relation_names = required_relations
    glossary_term_ids = {
        model["entityTypes"][name]["glossaryTerm"] for name in type_names
    }
    result = {
        "model_id": model["modelId"],
        "version": model["version"],
        "entity_types": {name: deepcopy(model["entityTypes"][name]) for name in sorted(type_names)},
        "relations": {name: deepcopy(model["relations"][name]) for name in sorted(relation_names)},
        "glossary": [
            deepcopy(term) for term in model["glossary"] if term["id"] in glossary_term_ids
        ],
    }
    if competency_question:
        result["competency_question"] = deepcopy(competency_question)
        result["competency_coverage"] = competency_coverage
    return result
