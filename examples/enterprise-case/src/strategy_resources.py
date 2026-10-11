"""Strategy source adapter: load and validate a governed metric snapshot."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).parents[1]
BUCKETS = (
    "enterprise_profiles", "external_factors", "metric_definitions",
    "strategic_objectives", "business_capabilities", "value_streams",
    "business_processes", "business_units", "products", "market_segments",
    "regions", "channels", "applications", "data_products", "observations", "events",
)
# Domain/range contracts keep business intent, responsibility and data lineage distinct.
RELATIONS = {
    "ALIGNS_WITH": ("enterprise_profiles", "strategic_objectives"),
    "MEASURED_BY": ("strategic_objectives", "metric_definitions"),
    "OWNED_BY": (("metric_definitions", "business_capabilities"), "business_units"),
    "USES_DATA_PRODUCT": ("metric_definitions", "data_products"),
    "SERVED_BY": ("data_products", "applications"),
    "SUPPORTED_BY": ("business_capabilities", "applications"),
    "REALIZED_THROUGH": (("strategic_objectives", "business_capabilities"),
                         ("value_streams", "business_processes")),
    "ENABLED_BY": ("value_streams", "business_capabilities"),
    "OPERATED_BY": ("business_processes", "business_units"),
    "DERIVED_FROM": ("data_products", "applications"),
    "POTENTIALLY_RELATED_TO": ("observations", "events"),
    "SCOPED_TO": ("observations", ("regions", "products", "market_segments", "channels")),
}
DIMENSIONS = ("region", "product", "segment", "channel")
DIMENSION_BUCKETS = {
    "region": "regions", "product": "products", "segment": "market_segments", "channel": "channels",
}
PERIODS = ("H1-2026", "H2-2026")
STRATEGY_QUESTION_ID = "CQ-STRATEGY-001"


class StrategyResources:
    def __init__(self, path: Path = ROOT / "data/strategy-context.json"):
        self.data = json.loads(path.read_text(encoding="utf-8"))
        self.by_id = {}
        self.types = {}
        for bucket in BUCKETS:
            for item in self.data[bucket]:
                if item["id"] in self.by_id:
                    raise ValueError("duplicate strategic object id")
                self.by_id[item["id"]] = item
                self.types[item["id"]] = bucket
        self._validate()
        canonical = json.dumps(self.data, sort_keys=True, ensure_ascii=False).encode()
        self.manifest = "strategy-" + hashlib.sha256(canonical).hexdigest()[:12]

    def _validate(self) -> None:
        if self.data.get("schema") != "northstar-strategy-context@1":
            raise ValueError("unsupported strategy context schema")
        fixture = self.data["fixture"]
        if not isinstance(fixture.get("acl"), list) or any(
            not isinstance(role, str) or not role.strip() for role in fixture["acl"]
        ):
            raise ValueError("strategy ACL must be a list of exact role strings")
        if fixture["synthetic"] is not True or not fixture["acl"] or not self.data["tenant"]:
            raise ValueError("fixture governance is required")
        if datetime.fromisoformat(fixture["as_of"].replace("Z", "+00:00")) < datetime.fromisoformat("2027-01-01T00:00:00+00:00"):
            raise ValueError("full H2 actuals require a closed-period snapshot")
        if len(self.data["metric_definitions"]) != 1 or len(self.data["strategic_objectives"]) != 1:
            raise ValueError("this teaching slice supports exactly one metric and objective")
        metric = self.data["metric_definitions"][0]
        if metric["periods"] != list(PERIODS) or metric["scenario"] != "actual":
            raise ValueError("unsupported comparison contract")
        for key in ("unit", "inclusion", "calendar", "grain", "scope", "definition_version", "fx_version"):
            if not metric.get(key):
                raise ValueError(f"missing metric semantics: {key}")
        for bucket in BUCKETS:
            for index, item in enumerate(self.data[bucket]):
                expected = f"fixture://northstar/strategy-context@1#/{bucket}/{index}"
                if item.get("evidence") != expected:
                    raise ValueError("fixture evidence must resolve to its JSON pointer")
                for field, kind in (("owner", "business_units"), ("quality_owner", "business_units"),
                                    ("source_data_product", "data_products"), ("system", "applications"),
                                    ("target_metric", "metric_definitions")):
                    if field in item and self.types.get(item[field]) != kind:
                        raise ValueError(f"invalid {field} reference")
                for field in ("supports", "capabilities"):
                    if any(self.types.get(ref) != "business_capabilities" for ref in item.get(field, [])):
                        raise ValueError(f"invalid {field} reference")
        source_data_product = self.by_id[metric["source_data_product"]]
        if not isinstance(source_data_product.get("snapshots"), list):
            raise ValueError("source data product snapshots are required")
        objective = self.data["strategic_objectives"][0]
        if (objective["unit"] != metric["unit"]
                or objective["target_period"] != PERIODS[1]
                or objective.get("scope") != metric["scope"]):
            raise ValueError("incompatible target metric")
        if type(objective["target_value"]) not in (int, float) or not math.isfinite(objective["target_value"]):
            raise ValueError("invalid target value")
        seen = set()
        for observation in self.data["observations"]:
            scope = observation["scope"]
            if len(scope) > 1 or set(scope) - set(DIMENSIONS):
                raise ValueError("only total or single-dimension marginals are available")
            key = (observation["period"], tuple(sorted(scope.items())))
            if key in seen:
                raise ValueError("duplicate period/scope observation")
            seen.add(key)
            if observation["metric"] != metric["id"] or observation["period"] not in PERIODS:
                raise ValueError("unknown metric or period")
            if observation["unit"] != metric["unit"]:
                raise ValueError("observation unit differs from metric definition")
            for dimension, value in scope.items():
                if self.types.get(value) != DIMENSION_BUCKETS[dimension]:
                    raise ValueError("observation scope must reference a governed dimension object")
            source = observation.get("source", "")
            source_product, separator, source_version = source.partition("@")
            if (not separator or source_product != metric["source_data_product"]
                    or source not in source_data_product["snapshots"]):
                raise ValueError("observation source must reference a registered data snapshot")
            try:
                source_time = datetime.fromisoformat(source_version)
            except ValueError as exc:
                raise ValueError("observation source version must be a date") from exc
            if source_time > datetime.fromisoformat(fixture["as_of"].replace("Z", "+00:00")).replace(tzinfo=None):
                raise ValueError("observation source is newer than fixture snapshot")
            if type(observation["value"]) not in (int, float) or not math.isfinite(observation["value"]):
                raise ValueError("observation must be a finite number")
        self._period_pair({})
        for dimension in DIMENSIONS:
            scopes = {o["scope"][dimension] for o in self.data["observations"] if dimension in o["scope"]}
            if len(scopes) < 2:
                raise ValueError("decomposition requires a complete partition")
            pairs = [self._period_pair({dimension: value}) for value in scopes]
            for i, total in enumerate(self._period_pair({})):
                if not math.isclose(sum(pair[i]["value"] for pair in pairs), total["value"], abs_tol=1e-9):
                    raise ValueError("dimension does not reconcile to company total")
        for index, relation in enumerate(self.data["relations"]):
            contract = RELATIONS.get(relation["type"])
            if not contract:
                raise ValueError("unknown strategic relation")
            for field, allowed in zip(("from", "to"), contract):
                allowed = (allowed,) if isinstance(allowed, str) else allowed
                if self.types.get(relation[field]) not in allowed:
                    raise ValueError("relation endpoint type violates contract")
            if relation.get("evidence") != f"fixture://northstar/strategy-context@1#/relations/{index}":
                raise ValueError("relation evidence must resolve to its JSON pointer")
            if relation["type"] == "SCOPED_TO":
                if relation["to"] not in self.by_id[relation["from"]]["scope"].values():
                    raise ValueError("scope relation disagrees with observation")
        scoped = {(r["from"], r["to"]) for r in self.data["relations"] if r["type"] == "SCOPED_TO"}
        expected_scoped = {(o["id"], value) for o in self.data["observations"] for value in o["scope"].values()}
        if scoped != expected_scoped:
            raise ValueError("every scoped observation needs its dimension relationship")

    def _period_pair(self, scope: dict) -> tuple[dict, dict]:
        pair = []
        for period in PERIODS:
            candidates = [o for o in self.data["observations"]
                          if o["period"] == period and o["scope"] == scope]
            if len(candidates) != 1:
                raise ValueError("each scope needs exactly one observation per period")
            pair.append(candidates[0])
        return pair[0], pair[1]
