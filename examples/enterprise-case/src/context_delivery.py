"""Common, evidence-bound handoff for fixed and assistant-led investigations.

Only deterministic observations/calculations become findings here. A model's
explanation stays a proposal, even when it sounds certain. No business action.
"""
from copy import deepcopy
import hashlib
import json


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()[:20]


def sales_documents(platform, principal):
    """Read the server's fixed sales snapshot under today's source and object ACLs."""
    strategy = platform.strategy_context
    fixture = strategy.data["fixture"]
    if not platform.allowed({"tenant": strategy.data["tenant"], "acl": fixture["acl"]}, principal):
        return []
    return [doc for doc in platform.current_documents(
        principal, valid_at=fixture["as_of"], observed_at=fixture["as_of"])
        if doc.get("system") == "sales" and doc["id"] in strategy.by_id]


def deliver(package, *, conditions=None):
    """Attach a readable contract without removing existing machine fields."""
    package["delivery_schema"] = "northstar-context/2"
    package["task_conditions"] = deepcopy(conditions or package.get("task_conditions") or
                                          {"scope": package.get("context_kind", "investigation")})
    references, findings = {}, []

    def cite(kind, source, value):
        key = "ev-" + identity([kind, source] if kind == "source" else [kind, source, value])
        references[key] = {"id": key, "kind": kind, "source": source,
                           "record": deepcopy(value)}
        return key

    for doc in package.get("evidence", []):
        cite("source", doc["citation"], doc)
    for edge in package.get("relations", []):
        cite("relation", edge["evidence"], edge)
    for observation in package.get("observations", []):
        ref = cite("observation", "runtime://" + observation["resource"], observation)
        findings.append({"id": "finding-" + ref, "kind": "observed",
            "text": f"{observation['observed_at']} 的教学观察：队列深度 {observation.get('queue_depth')}，"
                    f"消费滞后 {observation.get('consumer_lag_seconds')} 秒。",
            "evidence_ids": [ref], "scope": "该观察的环境、采样时间和有效期；不证明根因"})
    business = package.get("business_records")
    if business:
        ref = cite("calculation", business["citation"], business)
        names = {"approval": "审批", "execution": "执行", "completed": "完成"}
        stages = "、".join(f"{names[stage]}阶段 {count} 笔" for stage, count in business["stages"].items())
        findings.append({"id": "finding-" + ref, "kind": "computed",
            "text": f"业务快照有 {business['applications']} 笔申请，{business['unfinished']} 笔未完成；"
                    f"按申请当前阶段统计：{stages}。",
            "evidence_ids": [ref], "scope": "按申请ID去重；处理尝试数和队列消息数不能当作申请数"})
    performance = package.get("performance")
    if performance:
        ref = cite("calculation", "fixture://northstar/sales/" + package["manifest"],
                   {"performance": performance, "definition": package.get("metric_definition"),
                    "query_contract": package.get("query_contract"),
                    "evidence": package.get("evidence", [])})
        findings.append({"id": "finding-" + ref, "kind": "computed",
            "text": "在本次已确认的指标口径下，H2与H1的差额为 "
                    + str(performance["total"]["delta"]) + "；差额不等于原因。",
            "evidence_ids": [ref], "scope": "Northstar固定经营快照及确认的统计范围"})
    package["findings"] = findings
    package["references"] = list(references.values())
    package["business_task_completed"] = False
    package["investigation_limits"] = ["来源及派生视图不计为独立佐证",
        "本次交付不证明根因，也不授予执行业务动作的权限"]
    if not any(package.get(key) for key in (
            "evidence", "relations", "observations", "wiki", "business_records", "performance")):
        gap = "本轮读取未取得可交付的证据，需要继续取证或澄清范围"
        missing = package.setdefault("missing", [])
        if gap not in missing:
            missing.append(gap)
    package["coverage"] = {"supported_findings": len(findings),
        "open_questions": deepcopy(package.get("missing", [])),
        "status": "partial" if package.get("missing") else "not_verified"}
    package["continuation_input"] = {"manifest": package.get("manifest"),
        "evidence": list({item["id"]: {"id": item["id"], "version": item.get("version")}
                          for item in package.get("evidence", [])}.values())}
    package["package_digest"] = identity({k: v for k, v in package.items() if k != "package_digest"})
    return package


def recheck_previous(previous, platform, principal):
    """Treat caller-supplied packages as hints, never import their text/authority.

    We deliberately re-read on every continuation. IDs do not grant access and a
    digest supplied by a client is not a signature. Historical snapshots remain
    in the caller's storage; this report contains no old source text.
    """
    if not isinstance(previous, dict):
        raise ValueError("上轮上下文包必须是对象")
    visible = {d["id"]: d for d in platform.current_documents(principal)
               if d.get("system") != "sales"}
    # Sales has a server-owned closed-period snapshot, independent of the runtime
    # clock. Never take its time, source ACL, or object ACL from the old package.
    visible.update({d["id"]: d for d in sales_documents(platform, principal)})
    checked = []
    evidence = previous.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) > 200:
        raise ValueError("上轮包证据列表超过限制")
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("上轮包证据格式不正确")
        current = visible.get(item["id"])
        # Do not echo an inaccessible identity supplied by another actor.
        if current:
            checked.append({"id": current["id"], "status": "reread_required",
                            "version_changed": current["version"] != item.get("version")})
    return {"mode": "reread_under_current_authority", "checked": checked,
            "unavailable_count": len(evidence) - len(checked),
            "manifest_changed": previous.get("manifest") != platform.manifest,
            "old_text_imported": False}
