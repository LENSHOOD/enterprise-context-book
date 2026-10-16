"""Publish one checked resource snapshot from source-specific adapters.

Interpretation belongs to the author/assistant review process. This module
compiles accepted mappings and fixtures; validation does not approve a claim.
Nothing is published until every adapter and cross-source check succeeds.
"""
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path

from build_knowledge import compile_knowledge
from modeling import compile_domain_model, validate_knowledge_base
from strategy_resources import StrategyResources, BUCKETS, RELATIONS
from refund_records import validate_records

ROOT = Path(__file__).parents[1]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class ResourceBatch:
    name: str
    documents: list
    edges: list
    model: dict
    validation: dict


def record(identity, kind, title, text, citation, acl, instant, *, attributes=None,
           tenant="northstar", system="enterprise", authority="authored_fixture"):
    """Give a source-specific object the shared search/graph/Wiki envelope."""
    if not isinstance(acl, list) or not acl or any(not isinstance(role, str) or not role.strip() for role in acl):
        raise ValueError("resource needs an explicit ACL")
    content_hash = fingerprint([identity, kind, title, text, attributes, tenant, acl, instant, citation])
    return {"id": identity, "entity_type": kind, "title": title, "text": text,
            "kind": "enterprise", "tenant": tenant, "acl": list(acl), "system": system,
            "version": content_hash[:12], "citation": citation,
            "version_id": "kv:sha256:" + content_hash, "content_hash": "sha256:" + content_hash,
            "source": {"uri": citation, "revision": citation.split("@", 1)[-1].split("#", 1)[0]},
            "authority": authority, "attributes": attributes or {},
            "time": {"valid_from": instant, "valid_to": None, "observed_at": instant},
            "lineage": {"derived_from": [citation], "transform": "resource-adapter@1"}}


def operational_batch(data_dir):
    model = compile_domain_model(data_dir / "modeling")
    documents = compile_knowledge(data_dir)
    edges = read_json(data_dir / "relations.json")
    report = validate_knowledge_base(model, documents, edges)
    return ResourceBatch("operations", documents, edges, model, report)


def strategy_batch(resources):
    data = resources.data
    shared_types = {"business_capabilities": "BusinessCapability", "value_streams": "ValueStream",
                    "business_processes": "BusinessProcess"}
    def type_name(value):
        return shared_types.get(value, value)
    def endpoint(value):
        return [type_name(v) for v in value] if isinstance(value, tuple) else type_name(value)
    documents = [record(item["id"], type_name(bucket), item.get("name", item["id"]),
                        json.dumps(item, ensure_ascii=False), item["evidence"],
                        data["fixture"]["acl"], data["fixture"]["as_of"],
                        attributes=deepcopy(item), tenant=data["tenant"], system="sales")
                 for bucket in BUCKETS for item in data[bucket]]
    edges = [{**edge, "evidence_tier": "asserted",
              "review_status": "candidate" if edge["type"] == "POTENTIALLY_RELATED_TO" else "reviewed_fixture",
              "statement_kind": "hypothesis" if edge["type"] == "POTENTIALLY_RELATED_TO" else "description",
              "time": deepcopy(documents[0]["time"])} for edge in data["relations"]]
    model = {"entityTypes": {type_name(name): {"identity": ["id"], "meaning": type_name(name)} for name in BUCKETS},
             "relations": {name: {"from": endpoint(ends[0]), "to": endpoint(ends[1])}
                           for name, ends in RELATIONS.items()}, "glossary": []}
    return ResourceBatch("strategy", documents, edges, model,
                         {"valid": True, "snapshot": resources.manifest})


def refund_batch(data_dir):
    """Compile an explicit, reviewed teaching mapping of a raw business brief."""
    mapping = read_json(data_dir / "refund-map.json")
    raw_root = (data_dir / "raw").resolve()
    relative = Path(mapping["source"])
    source = (raw_root / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or raw_root not in source.parents:
        raise ValueError("refund source path must stay inside raw root")
    raw = source.read_text(encoding="utf-8")
    if mapping["status"] != "reviewed_fixture" or not mapping.get("reviewer"):
        raise ValueError("refund mapping needs a reviewed interpretation")
    citation = "fixture://northstar/refund-brief@" + hashlib.sha256(raw.encode()).hexdigest()[:12]
    parts = re.split(r"(?m)^## ([\w-]+)\s*$", raw)
    sections = dict(zip(parts[1::2], parts[2::2]))
    def check_passage(item):
        if not item.get("quote") or item["quote"] not in sections.get(item.get("anchor"), ""):
            raise ValueError("refund mapping has no exact source passage at its anchor")
    documents = []
    for item in mapping["objects"]:
        check_passage(item)
        description = item["quote"]
        for key, label in (("on_rejection", "条件不符时"), ("on_failure", "失败时")):
            if key in item.get("attributes", {}):
                description += "\n" + label + "：" + item["attributes"][key]
        documents.append(record(item["id"], item["type"], item["name"], description,
            citation + "#" + item["anchor"], item["acl"], mapping["as_of"],
            attributes={**item.get("attributes", {}), "content_scope": item["scope"]},
            system="refund-journey"))
    edges = []
    for edge in mapping["relations"]:
        check_passage(edge)
        edges.append({**edge, "evidence": citation + "#" + edge["anchor"],
                      "evidence_tier": "asserted", "statement_kind": "description",
                      "review_status": mapping["status"], "time": deepcopy(documents[0]["time"])})
    return ResourceBatch("refund-journey", documents, edges, mapping["model"],
                         {"valid": True, "reviewer": mapping["reviewer"],
                          "source_hash": hashlib.sha256(raw.encode()).hexdigest()})


def validate_catalog(documents, edges, model):
    """Common publication gate, including cross-adapter identity and endpoints."""
    by_id = {}
    for doc in documents:
        if doc["id"] in by_id:
            raise ValueError("duplicate resource identity: " + doc["id"])
        by_id[doc["id"]] = doc
        for field in ("tenant", "citation", "version", "title"):
            if not isinstance(doc.get(field), str) or not doc[field].strip():
                raise ValueError("missing resource governance: " + field)
        if not isinstance(doc.get("acl"), list) or not doc["acl"] or any(
                not isinstance(role, str) or not role.strip() for role in doc["acl"]):
            raise ValueError("resource needs an explicit ACL")
        if doc["entity_type"] not in model["entityTypes"]:
            raise ValueError("unknown resource type")
        for field in ("valid_from", "observed_at"):
            instant = datetime.fromisoformat(doc["time"][field].replace("Z", "+00:00"))
            if instant.tzinfo is None:
                raise ValueError("resource time needs timezone")
        if doc["time"].get("valid_to"):
            end = datetime.fromisoformat(doc["time"]["valid_to"].replace("Z", "+00:00"))
            start = datetime.fromisoformat(doc["time"]["valid_from"].replace("Z", "+00:00"))
            if end.tzinfo is None or end <= start:
                raise ValueError("resource time interval is invalid")
    seen = set()
    for edge in edges:
        contract = model["relations"].get(edge["type"])
        if not contract or not edge.get("evidence"):
            raise ValueError("relation needs a contract and evidence")
        key = (edge["from"], edge["type"], edge["to"], edge["evidence"])
        if key in seen:
            raise ValueError("duplicate resource relation")
        seen.add(key)
        for side in ("from", "to"):
            doc = by_id.get(edge[side])
            allowed = contract[side] if isinstance(contract[side], list) else [contract[side]]
            if not doc or doc["entity_type"] not in allowed:
                raise ValueError("resource relation endpoint violates contract: " + edge["type"])
        if by_id[edge["from"]]["tenant"] != by_id[edge["to"]]["tenant"]:
            raise ValueError("cross-tenant resource relation")
    return {"valid": True, "objects": len(documents), "relations": len(edges)}


class ResourceSnapshot:
    def __init__(self, batches, strategy, claims, runtime, refund_records):
        self.documents = [doc for batch in batches for doc in batch.documents]
        self.edges = [edge for batch in batches for edge in batch.edges]
        self.model = deepcopy(batches[0].model)
        for batch in batches[1:]:
            for section in ("entityTypes", "relations"):
                for name, definition in batch.model[section].items():
                    if name in self.model[section] and self.model[section][name] != definition:
                        raise ValueError("conflicting model definition: " + name)
                    self.model[section][name] = deepcopy(definition)
            self.model["glossary"].extend(deepcopy(batch.model.get("glossary", [])))
        self.validation = validate_catalog(self.documents, self.edges, self.model)
        self.model["version"] += "+resources." + fingerprint(self.model)[:12]
        self.model_validation = batches[0].validation
        self.strategy, self.claims, self.runtime = strategy, claims, runtime
        self.refund_records = validate_records(refund_records)
        self.manifest = "northstar-" + fingerprint({"documents": self.documents, "edges": self.edges,
            "model": self.model, "claims": claims, "runtime_source": runtime,
            "strategy": strategy.data, "refund_records": refund_records,
            "validation": [batch.validation for batch in batches]})[:12]
        self.report = {"manifest": self.manifest, "validation": self.validation,
            "sources": [{"adapter": batch.name, "objects": len(batch.documents),
                         "relations": len(batch.edges), "validation": batch.validation}
                        for batch in batches],
            "interpretation": "已编写并核对的教学定义；新候选需先经过资源维护者审阅",
            "stages": ["登记来源", "按来源解析", "应用已确认的映射", "校验领域及共同约定", "发布版本", "供检索与视图使用"]}


def compile_resources(data_dir=ROOT / "data"):
    """Shared entry for initial builds, assistant releases and source updates."""
    strategy = StrategyResources(data_dir / "strategy-context.json")
    batches = [operational_batch(data_dir), strategy_batch(strategy), refund_batch(data_dir)]
    snapshot = ResourceSnapshot(batches, strategy,
        read_json(data_dir / "architecture-claims.json"), read_json(data_dir / "runtime.json"),
        read_json(data_dir / "refund-records.json"))
    by_id = {doc["id"]: doc for doc in snapshot.documents}
    for identity, status in snapshot.runtime.items():
        resource = by_id.get(identity)
        if not resource or resource["tenant"] != status["tenant"] or status.get("resource") != identity:
            raise ValueError("runtime adapter needs a registered resource identity")
    return snapshot
