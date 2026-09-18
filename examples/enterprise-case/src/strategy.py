"""C7: a governed, read-only enterprise analysis fixture, not a causal model."""
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


class StrategicContext:
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

    def definition_confirmation(self) -> dict:
        """Return the exact contract a caller must acknowledge before calculation."""
        metric = self.data["metric_definitions"][0]
        return {
            "question_id": STRATEGY_QUESTION_ID,
            "metric": metric["id"],
            "periods": list(PERIODS),
            "scope": {},
            "scenario": metric["scenario"],
            "snapshot": self.manifest,
            "metric_definition": deepcopy(metric),
        }

    @staticmethod
    def _question_is_supported(question: str) -> bool:
        normalized = question.casefold()
        return ("h1" in normalized and "h2" in normalized
                and any(term in normalized for term in ("销售", "sales", "bookings", "订单")))

    @staticmethod
    def _question_scope(question: str) -> dict:
        normalized = question.casefold()
        matches = {}
        for dimension, terms in {
            "region": (("emea", "region-emea"), ("other region", "region-other")),
            "product": (("home & living", "product-home"), ("consumer electronics", "product-electronics")),
            "segment": (("enterprise", "segment-enterprise"), ("consumer", "segment-consumer")),
            "channel": (("direct", "channel-direct"), ("partner", "channel-partner")),
        }.items():
            found = [value for term, value in terms if term in normalized]
            if len(found) == 1:
                matches[dimension] = found[0]
            elif len(found) > 1:
                matches[dimension] = "ambiguous"
        return matches

    def _view(self, label: str, scope: dict) -> dict:
        h1, h2 = self._period_pair(scope)
        delta = h2["value"] - h1["value"]
        scope_labels = {
            dimension: self.by_id[value]["name"]
            for dimension, value in scope.items()
        }
        return {
            "label": next(iter(scope_labels.values()), label),
            "scope": scope, "scope_labels": scope_labels, "unit": h1["unit"],
            "h1": h1["value"], "h2": h2["value"], "delta": delta,
            "change_rate": round(delta / h1["value"], 4) if h1["value"] else None,
            "rate_note": None if h1["value"] else "基期为零，变化率未定义",
            "evidence": [h1["evidence"], h2["evidence"]],
            "sources": [h1["source"], h2["source"]],
        }

    def package(self, question: str, principal: dict, *, confirmation: dict | None = None) -> dict:
        if (principal.get("tenant") != self.data["tenant"]
                or principal.get("role") not in self.data["fixture"]["acl"]
                or not principal.get("user_id")):
            raise PermissionError("strategic analysis requires an authorized tenant and principal")
        metric = self.data["metric_definitions"][0]
        expected_confirmation = self.definition_confirmation()
        confirmed = confirmation == expected_confirmation
        base = {
            "mode": "strategic_analysis", "scope": "enterprise", "question": question,
            "principal": principal, "source_snapshot": self.data["fixture"],
            "strategy_manifest": self.manifest, "metric_definition": metric,
            "query_contract": {**expected_confirmation, "confirmed": confirmed},
            "allowed_tools": [], "allowed_actions": [],
            "agent_execution_context": {"read_only": True, "decision_owner": "org-revops",
                                        "next_step": "由经营责任人人工复核；不更改目标、定价或销售策略"},
        }
        missing = []
        requested_scope = self._question_scope(question)
        if not self._question_is_supported(question):
            missing.append("本教学切片只支持 H1/H2 销售订单额问题；请改用已定义的战略能力问题。")
        if requested_scope != expected_confirmation["scope"]:
            missing.append("问题包含区域、产品、客群或渠道范围；当前确认契约只覆盖全公司，不能用全公司快照代替该范围。")
        if confirmation is None:
            missing.append("请确认指标、自然年半年度、全公司范围、实际场景和固定教学快照。")
        elif not confirmed:
            missing.append("确认契约与指标、时间、范围、场景或快照不一致；不能计算。")
        if missing:
            return deepcopy({**base, "status": "needs_clarification",
                             "missing": missing})
        total = self._view("全公司净确认订单额", {})
        decompositions = []
        for dimension in DIMENSIONS:
            values = sorted({o["scope"][dimension] for o in self.data["observations"] if dimension in o["scope"]})
            decompositions.append({"dimension": dimension, "reconciles_to_total": True,
                                   "items": [self._view(value, {dimension: value}) for value in values]})
        layers = [
            ("L0", "外部环境与商业模式", ("enterprise_profiles", "external_factors")),
            ("L1", "战略意图", ("strategic_objectives",)),
            ("L2", "业务架构", ("business_capabilities", "value_streams", "products", "market_segments", "regions", "channels")),
            ("L3", "经营与组织", ("business_units",)),
            ("L4", "应用与数据架构", ("applications", "data_products", "metric_definitions")),
            ("L5", "业务运行", ("business_processes", "observations", "events")),
        ]
        objective = self.data["strategic_objectives"][0]
        result = {
            **base, "status": "ready_for_review", "strategic_objective": objective,
            "semantic_contract": {"schema": self.data["schema"], "relations": RELATIONS,
                                  "competency_question": STRATEGY_QUESTION_ID},
            "context_layers": [{"level": level, "name": name,
                                "object_ids": [o["id"] for bucket in buckets for o in self.data[bucket]]}
                               for level, name, buckets in layers]
                              + [{"level": "L6", "name": "Agent 执行", "read_only": True}],
            "enterprise_context": {bucket: self.data[bucket] for bucket in BUCKETS},
            "relations": self.data["relations"],
            "evidence": [{"id": o["id"], "citation": o["evidence"], "authority": "authored_fixture"}
                         for o in self.by_id.values()],
            "performance": {"total": total, "decomposition_views": decompositions,
                            "target_gap": total["h2"] - objective["target_value"],
                            "target_evidence": objective["evidence"]},
            "hypotheses": [
                {"id": "HYP-EVENT", "status": "unproven",
                 "text": "区域渠道冻结和品类促销调整值得核对，当前边只表达候选关联，不能证明因果。",
                 "evidence": [r["evidence"] for r in self.data["relations"] if r["type"] == "POTENTIALLY_RELATED_TO"],
                 "next_check": "检查客户级订单、时序和对照样本，并与业务责任人复核。"}
            ],
            "missing": ["客户/订单级联合明细", "Pipeline 转化漏斗", "价格与折扣变更明细",
                        "按销售团队的目标和实际", "季节性、上一年同期与可比对照"],
            "warnings": ["四个维度是同一批订单的不同投影，不能跨维度相加或推导联合分组。",
                         "差异分解说明在哪里下降，不等于解释为什么下降；当前证据不能证明因果。",
                         "净订单额变化不能直接当作利润、收入或回款变化。"],
        }
        return deepcopy(result)
