"""Read a refund business explanation, then discover its runtime evidence."""
import json
from northstar import NorthstarPlatform, Principal


def investigate_refund(platform, principal):
    hits = platform.search("消费者退款能力", principal, limit=20)
    seeds = [hit["id"] for hit in hits if platform.by_id[hit["id"]]["entity_type"] == "BusinessCapability"]
    if len(seeds) != 1:
        return {"missing": ["需要明确退款业务范围"], "observations": []}
    edges = platform.trace(seeds[0], principal, max_hops=8, allow_inverse_navigation=True,
        relation_types={"NEEDS_REFUND_CAPABILITY", "USES_PROCESS", "HAS_STEP", "NEXT_STEP",
                        "CHECKS_POLICY", "USES_REFUND_SERVICE", "DEPLOYED_AS", "CONSUMES_QUEUE",
                        "MONITORED_AT", "HANDLED_WITH"})
    ids = {seeds[0]} | {edge[side] for edge in edges for side in ("from", "to")}
    docs = [platform.by_id[identity] for identity in sorted(ids)]
    endpoints = [doc for doc in docs if doc["entity_type"] == "MonitoringEndpoint"]
    observations = [platform.get_status(doc["attributes"]["runtime_resource"], principal) for doc in endpoints]
    return {"manifest": platform.manifest, "entry": seeds[0],
            "path": [{"id": d["id"], "title": d["title"], "citation": d["citation"]} for d in docs],
            "relations": edges, "observations": [o for o in observations if o],
            "runbooks": [d["id"] for d in docs if d["entity_type"] == "Runbook"],
            "missing": [] if endpoints and all(observations) else ["当前角色没有取得新鲜的运行观察"],
            "next_step": "按手册检查，另走动作预览、审批和验证流程"}


def main():
    platform = NorthstarPlatform()
    print(json.dumps({"build": platform.resources.report,
                      "investigation": investigate_refund(platform, Principal("new-reader", "sre"))},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
