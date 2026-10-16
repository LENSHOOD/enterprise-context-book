"""A fixed, read-only investigation route shared by C4 and the CLI demo."""
from copy import deepcopy
from context_flow import ContextFlow
from context_delivery import deliver, recheck_previous


def investigate_refund(platform, principal, previous=None):
    flow, reads, steps = ContextFlow(platform), [], []
    def read(tool, args, purpose):
        value = flow.read(tool, args, principal)
        steps.append({"tool": tool, "args": args, "purpose": purpose})
        reads.append(value)
        return value

    continuation = recheck_previous(previous, platform, principal) if previous is not None else None
    def finish(result):
        package = flow.assemble({"mode": "operational", "steps": steps,
            "competency_question": None}, reads, principal, "refund-discovery")
        package.update(result)
        if continuation is not None:
            package["continuation"] = continuation
        return deliver(package, conditions={"goal": "调查退款积压，交付依据与缺口，不执行处理",
            "scope": "当前角色可见的Northstar教学资料；业务数据使用固定快照"})

    question = "消费者退款能力"
    hits = read("search", {"question": question, "limit": 20}, "找到业务入口")["evidence"]
    seeds = [hit["id"] for hit in hits
             if platform.by_id[hit["id"]]["entity_type"] == "BusinessCapability"]
    result = {"manifest": platform.manifest, "entry": None, "path": [], "documents": [],
              "relations": [], "observations": [], "runbooks": [], "missing": [],
              "business_task_completed": False,
              "next_step": "结合已取得的材料与待补缺口继续核查；需要操作时另走 C6 的预览、审批和验证流程",
              "discovery_steps": [{"title": "找到退款业务入口", "tool": "search",
                  "purpose": "先找到退款能力，不预填业务对象或队列 ID。",
                  "args": {"question": question, "limit": 20},
                  "summary": f"检索返回 {len(hits)} 条材料，其中有 {len(seeds)} 个能力候选。",
                  "object_ids": seeds, "status": "complete" if len(seeds) == 1 else "missing"}]}
    if len(seeds) != 1:
        result["missing"].append("当前可见材料不能确定唯一退款业务入口，需要明确范围或补充资料")
        return finish(result)

    relation_types = {"NEEDS_REFUND_CAPABILITY", "USES_PROCESS", "HAS_STEP", "NEXT_STEP",
                      "CHECKS_POLICY", "USES_REFUND_SERVICE", "DEPLOYED_AS", "CONSUMES_QUEUE",
                      "MONITORED_AT", "HANDLED_WITH"}
    edges = read("trace", {"seed": seeds[0], "max_hops": 8, "allow_inverse_navigation": True,
                           "relation_types": sorted(relation_types)}, "沿业务和部署关系导航")["relations"]
    ids = {seeds[0]} | {edge[side] for edge in edges for side in ("from", "to")}
    selected = read("lookup", {"ids": sorted(ids)}, "读取关系端点的当前可见资料")["evidence"]
    docs = [platform.by_id[item["id"]] for item in selected]
    result.update(entry=seeds[0], documents=deepcopy(docs), relations=deepcopy(edges),
                  path=[{key: doc[key] for key in ("id", "title", "citation", "entity_type")} for doc in docs])
    result["discovery_steps"].append({"title": "沿关系找到业务与技术资料", "tool": "trace",
        "purpose": "连接价值流、流程、政策、服务、部署、队列和监控；只返回当前角色可见的关系。",
        "args": {"seed": seeds[0], "max_hops": 8, "allow_inverse_navigation": True,
                 "relation_types": sorted(relation_types)},
        "summary": f"本次找到 {len(docs)} 个对象、{len(edges)} 条关系。",
        "object_ids": sorted(ids), "status": "complete" if edges else "missing"})

    endpoints = [doc for doc in docs if doc["entity_type"] == "MonitoringEndpoint"]
    resources = sorted({doc["attributes"]["runtime_resource"] for doc in endpoints})
    observations = [next(iter(read("observe", {"resource": identity}, "核对运行观察")["observations"]), None)
                    for identity in resources]
    result["observations"] = [value for value in observations if value is not None]
    fresh = bool(resources) and all(value is not None for value in observations)
    if not fresh:
        result["missing"].append("未找到可见监控入口，或没有读取权限，或运行观察已过期；不能据此判断没有积压")
    result["discovery_steps"].append({"title": "通过发现的入口读取当前状态", "tool": "observe",
        "purpose": "使用监控对象给出的资源标识，另读有采样时间和有效期的观察。",
        "args": {"resources": resources}, "object_ids": [doc["id"] for doc in endpoints],
        "summary": f"取得 {len(result['observations'])} 份新鲜观察。" if fresh else result["missing"][-1],
        "status": "complete" if fresh else "missing"})

    result["runbooks"] = [doc["id"] for doc in docs if doc["entity_type"] == "Runbook"]
    if not result["runbooks"]:
        result["missing"].append("本次路径没有取得可见处置手册，需要继续查找或请求协助")
    result["discovery_steps"].append({"title": "整理处置依据，交给下一步工作", "tool": "select",
        "purpose": "从已取得的对象中选出处置手册，保留正文与引用；这一步不执行重放。",
        "args": {"entity_type": "Runbook"}, "object_ids": result["runbooks"],
        "summary": f"找到 {len(result['runbooks'])} 份手册；根因和业务处理结果仍需核实。",
        "status": "complete" if result["runbooks"] else "missing"})
    # Business rows are a separate fixed snapshot, not a conversion of queue depth.
    business = read("business", {}, "按申请粒度统计阶段，避免重试记录重复计数")
    if business.get("business_records"):
        result["business_records"] = business["business_records"]
    else:
        result["missing"].extend(business.get("missing", []))
    return finish(result)
