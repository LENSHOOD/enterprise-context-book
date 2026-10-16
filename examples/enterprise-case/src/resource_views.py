"""Readable diagrams projected from the same authorized resource snapshot."""
import html

from northstar import NorthstarPlatform, Principal

LABELS = {
    "ALIGNS_WITH": "对齐目标", "MEASURED_BY": "用指标衡量", "OWNED_BY": "由组织负责",
    "USES_DATA_PRODUCT": "使用数据产品", "SERVED_BY": "由应用提供", "SUPPORTED_BY": "由应用支持",
    "REALIZED_THROUGH": "通过其落实", "ENABLED_BY": "需要能力", "OPERATED_BY": "由组织执行",
    "DERIVED_FROM": "数据来自", "POTENTIALLY_RELATED_TO": "候选关联，待查证",
    "SCOPED_TO": "限定观察范围", "CONSUMED_BY": "由代码消费", "TESTED_BY": "由测试覆盖",
    "PART_OF_REFUND_SERVICE": "属于退款服务", "PART_OF_APPLICATION": "属于服务",
    "DEPLOYED_AS": "部署为", "CONSUMES_QUEUE": "消费队列", "MONITORED_AT": "监控入口",
    "HANDLED_WITH": "积压处置参考", "DOCUMENTED_BY": "手册说明", "PUBLISHES_EVENT": "发布事件",
    "HAS_REFUND_CAPABILITY": "包含退款能力", "NEEDS_REFUND_CAPABILITY": "需要退款能力",
    "USES_PROCESS": "通过流程落实", "HAS_STEP": "包含步骤", "NEXT_STEP": "正常条件下下一步",
    "CHECKS_POLICY": "核对政策", "USES_REFUND_SERVICE": "由服务支持",
}

VIEWS = {
    "refund-business": ("sre", "2026-08-27T10:00:00Z", {
        "value-stream-consumer-sale", "cap-consumer-refund", "process-refund",
        "step-check-refund", "step-request-refund", "step-verify-refund",
        "product-cancellation-policy", "service-refund-worker"}),
    "refund-runtime": ("developer", "2026-08-27T10:00:00Z", {
        "service-order", "event-order-cancelled", "code-refund-consumer", "service-refund-worker",
        "deployment-refund-eu", "refund-queue", "monitor-refund-queue", "runbook-refund-backlog"}),
    "sales-structure": ("executive", "2027-01-02T00:00:00Z", {
        "enterprise-northstar", "objective-h2-growth", "metric-sales-bookings",
        "value-stream-acquire-expand", "cap-enterprise-sales", "process-pipeline-management",
        "org-enterprise-sales", "org-revops", "data-sales-facts", "app-sales-dwh", "app-erp", "app-crm"}),
    "sales-observations": ("executive", "2027-01-02T00:00:00Z", {
        "obs-emea-h1", "obs-emea-h2", "region-emea", "event-emea-channel-freeze",
        "obs-home-h1", "obs-home-h2", "product-home", "event-home-promotion"}),
}


def relationship_view(platform, principal, ids, instant):
    documents = {d["id"]: d for d in platform.current_documents(
        principal, valid_at=instant, observed_at=instant) if d["id"] in ids}
    edges = []
    for identity in sorted(documents):
        edges.extend(edge for edge in platform.trace(identity, principal, max_hops=1,
                     valid_at=instant, observed_at=instant) if edge["to"] in documents)
    return {"manifest": platform.manifest, "role": principal.role, "as_of": instant,
            "objects": list(documents.values()), "relations": edges}


def mermaid(view):
    nodes = {d["id"]: "n" + str(i) for i, d in enumerate(sorted(view["objects"], key=lambda d: d["id"]))}
    def label(value):
        return html.escape(value, quote=True).replace("\n", " ").replace("|", "&#124;")
    lines = ["flowchart " + view.get("direction", "TB")]
    for doc in sorted(view["objects"], key=lambda d: d["id"]):
        title = doc["title"]
        attrs = doc.get("attributes", {})
        if "period" in attrs and "value" in attrs:
            title = f'{attrs["period"]}：{attrs["value"]} {attrs["unit"]}'
        lines.append(f'  {nodes[doc["id"]]}["{label(title)}"]')
    for edge in sorted(view["relations"], key=lambda e: (e["from"], e["type"], e["to"])):
        meaning = label(LABELS.get(edge["type"], edge["type"]))
        arrow = f'-. "{meaning}" .->' if edge.get("review_status") == "candidate" else f'-->|"{meaning}"|'
        lines.append(f'  {nodes[edge["from"]]} {arrow} {nodes[edge["to"]]}')
    return "\n".join(lines)


def book_views(platform=None):
    platform = platform or NorthstarPlatform()
    return {name: {**relationship_view(platform, Principal("diagram", role), ids, instant),
                   "direction": "LR" if name == "sales-observations" else "TB"}
            for name, (role, instant, ids) in VIEWS.items()}
