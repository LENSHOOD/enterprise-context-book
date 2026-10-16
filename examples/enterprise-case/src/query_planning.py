"""C5: compare two authored plans against one narrow refund evidence contract.

Costs are illustrative estimates, not measured money, latency or guarantees.
The comparison intentionally executes both plans; ordinary selection runs one.
"""
from copy import deepcopy

from context_flow import ContextFlow
from context_delivery import deliver


REQUIRED_EDGES = (
    ("service-refund-worker", "DEPLOYED_AS", "deployment-refund-eu"),
    ("deployment-refund-eu", "CONSUMES_QUEUE", "refund-queue"),
    ("refund-queue", "MONITORED_AT", "monitor-refund-queue"),
    ("refund-queue", "HANDLED_WITH", "runbook-refund-backlog"),
    ("step-request-refund", "USES_REFUND_SERVICE", "service-refund-worker"),
    ("step-check-refund", "NEXT_STEP", "step-request-refund"),
    ("step-check-refund", "CHECKS_POLICY", "product-cancellation-policy"),
)
REQUIRED_IDS = sorted({identity for source, _, target in REQUIRED_EDGES
                       for identity in (source, target)})
CONTRACT = {
    "id": "refund-preparation@1",
    "goal": "为退款积压调查准备最小依据，尚不确认根因或执行重放",
    "scope": {"queue": "refund-queue", "environment": "teaching-eu"},
    "requirements": ["适用政策与处置手册正文", "队列、部署、服务及业务步骤的联系",
                     "该队列的新鲜运行观察"],
    "not_covered": ["完整根因诊断", "批准重放", "确认退款到账"],
}


def candidate_plans():
    """Build physical alternatives for the fixed, reviewed fixture contract."""
    trace = {"tool": "trace", "args": {"seed": "refund-queue", "max_hops": 8,
             "allow_inverse_navigation": True}, "purpose": "核对队列与业务、部署及手册的联系"}
    lookup = {"tool": "lookup", "args": {"ids": ["refund-queue"]},
              "purpose": "读取关系端点的当前可见正文及引用"}
    observe = {"tool": "observe", "args": {"resource": "refund-queue"},
               "purpose": "读取同一队列的新鲜观察"}
    # Each step carries a transparent teaching estimate. No plan is executed to estimate it.
    broad = {"id": "broad", "label": "广泛检索后查关系", "mode": "operational",
             "competency_question": None, "steps": [
        {"tool": "search", "args": {"question": "退款积压政策部署处置",
          "disabled_channels": []}, "purpose": "先召回相关背景材料", "estimated_units": 12},
        {**deepcopy(trace), "estimated_units": 18},
        {**deepcopy(lookup), "relations_from": 1, "estimated_units": 12},
        {**deepcopy(observe), "estimated_units": 5}]}
    directed = {"id": "directed", "label": "从明确队列定向查证", "mode": "operational",
                "competency_question": None, "steps": [
        {**deepcopy(trace), "args": {**trace["args"],
          "relation_types": sorted({edge[1] for edge in REQUIRED_EDGES})}, "estimated_units": 8},
        {**deepcopy(lookup), "relations_from": 0, "estimated_units": 8},
        {**deepcopy(observe), "estimated_units": 5}]}
    return [broad, directed]


def choose_plan(plans, estimated_budget):
    """Filter by an estimated-cost budget, then select before executing either plan."""
    if type(estimated_budget) is not int or not 1 <= estimated_budget <= 1000:
        raise ValueError("教学估计预算必须为1—1000的整数")
    candidates = [{"id": plan["id"], "label": plan["label"],
                   "estimated_units": sum(step["estimated_units"] for step in plan["steps"])}
                  for plan in plans]
    for item in candidates:
        item["within_budget"] = item["estimated_units"] <= estimated_budget
    eligible = [item for item in candidates if item["within_budget"]]
    chosen = min(eligible, key=lambda item: (item["estimated_units"], item["id"])) if eligible else None
    return {"selected": chosen["id"] if chosen else None, "candidates": candidates,
            "estimated_budget": estimated_budget,
            "cost_basis": "手写教学估计单位：不是实际费用、耗时或生产成本上限；仅比较两个已审核模板"}


def check_refund_evidence(platform, principal, package):
    """Validate actual evidence, never infer completeness from a cheap plan."""
    current = {doc["id"]: doc for doc in platform.current_documents(principal)}
    evidence = {item["id"]: item for item in package["evidence"]}
    valid_docs = {identity for identity, item in evidence.items()
                  if identity in current and item["citation"] == current[identity]["citation"]
                  and item["version"] == current[identity]["version"]
                  and item["evidence"] == current[identity]["text"] and item["evidence"]}
    actual_edges = {(edge["from"], edge["type"], edge["to"])
                    for edge in package["relations"] if edge.get("evidence")}
    required_paths = set(REQUIRED_EDGES) <= actual_edges and set(REQUIRED_IDS) <= valid_docs
    scope_matches = (current.get("deployment-refund-eu", {}).get("attributes", {}).get("environment")
                     == CONTRACT["scope"]["environment"])
    monitor = current.get("monitor-refund-queue", {}).get("attributes", {})
    scope_matches = scope_matches and monitor.get("environment") == CONTRACT["scope"]["environment"]
    scope_matches = scope_matches and monitor.get("runtime_resource") == CONTRACT["scope"]["queue"]
    fresh = platform.get_status(CONTRACT["scope"]["queue"], principal)
    checks = [
        {"requirement": CONTRACT["requirements"][0], "met":
         {"product-cancellation-policy", "runbook-refund-backlog"} <= valid_docs},
        {"requirement": CONTRACT["requirements"][1], "met": bool(required_paths and scope_matches)},
        {"requirement": CONTRACT["requirements"][2], "met":
         bool(scope_matches and fresh is not None and fresh in package["observations"])},
    ]
    return {"complete": all(item["met"] for item in checks), "checks": checks,
            "meaning": "仅确认本轮教学取证要求，不代表根因或业务处理完成"}


def compare_refund_plans(platform, principal, estimated_budget=60):
    """Read-only teaching comparison; rejected plans are not executed."""
    plans = candidate_plans()
    selection = choose_plan(plans, estimated_budget)
    reports = []
    for plan, candidate in zip(plans, selection["candidates"]):
        if not candidate["within_budget"]:
            reports.append({**candidate, "status": "not_run", "reason": "超出本次教学估计预算"})
            continue
        package = ContextFlow(platform).execute(plan, principal, "query-plan-comparison")
        coverage = check_refund_evidence(platform, principal, package)
        # Deduplicate after execution, keeping measurement counts before compaction.
        package["evidence"] = list({item["id"]: item for item in package["evidence"]}.values())
        package["evidence_coverage"] = coverage
        package["status"] = "evidence_ready" if coverage["complete"] else "incomplete"
        package["missing"].extend(item["requirement"] for item in coverage["checks"] if not item["met"])
        deliver(package, conditions={"goal": CONTRACT["goal"], "scope": CONTRACT["scope"]})
        reports.append({**candidate, "status": package["status"], "coverage": coverage,
                        "execution": package["execution_report"], "package": package})
    selected = next((item for item in reports if item["id"] == selection["selected"]), None)
    return {"plan_comparison": {"logical_plan": deepcopy(CONTRACT), **selection, "plans": reports,
        "status": selected["status"] if selected else "budget_insufficient",
        "comparison_notice": "为教学对照，分别执行预算内的候选；预算逐条计划判断，不限制整次对照的总开销。正常请求只执行选中的计划。",
        "business_task_completed": False}}
