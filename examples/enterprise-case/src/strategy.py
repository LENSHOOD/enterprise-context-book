"""Read-only metric queries over a validated resource snapshot."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from resource_pipeline import strategy_batch
from strategy_resources import (StrategyResources, ROOT, BUCKETS, RELATIONS, DIMENSIONS, PERIODS, STRATEGY_QUESTION_ID)


class StrategicContext(StrategyResources):
    def __init__(self, path: Path = ROOT / "data/strategy-context.json", *, resources=None):
        if resources is None:
            super().__init__(path)
        else:
            self.data = deepcopy(resources.data)
            self.by_id = {item["id"]: item for bucket in BUCKETS for item in self.data[bucket]}
            self.types = dict(resources.types)
            self.manifest = resources.manifest

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
            ("L1", "战略目标与经营安排", ("strategic_objectives", "metric_definitions")),
            ("L2", "业务能力、产品与流程", ("business_capabilities", "value_streams", "business_processes", "products", "market_segments", "regions", "channels")),
            ("L3", "组织、责任与资源", ("business_units",)),
            ("L4", "应用、数据与技术基础", ("applications", "data_products")),
            ("L5", "运行状态与工作历史", ("observations", "events")),
        ]
        objective = self.data["strategic_objectives"][0]
        # Reuse the canonical adapter rather than invent a second version scheme
        # for standalone metric reads outside the platform's ContextFlow.
        catalog = {doc["id"]: doc for doc in strategy_batch(self).documents}
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
            "evidence": [{"id": o["id"], "citation": o["evidence"], "authority": "authored_fixture",
                          "version": catalog[o["id"]]["version"]}
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
