"""Read a small business snapshot without counting retry attempts as refunds."""
from collections import Counter
from copy import deepcopy
from datetime import datetime
from context_delivery import identity


def validate_records(data):
    if data.get("fixture") is not True or not data.get("acl") or not data.get("tenant"):
        raise ValueError("业务教学数据需要明确身份与权限")
    if datetime.fromisoformat(data["as_of"]).tzinfo is None:
        raise ValueError("业务快照时间需要时区")
    ids = [x["id"] for x in data["applications"]]
    attempts = [x["id"] for x in data["attempts"]]
    if len(ids) != len(set(ids)) or len(attempts) != len(set(attempts)):
        raise ValueError("申请或尝试身份重复")
    if any(x["stage"] not in {"approval", "execution", "completed"} for x in data["applications"]):
        raise ValueError("未知申请阶段")
    if any(x["application_id"] not in ids for x in data["attempts"]):
        raise ValueError("尝试记录指向未知申请")
    return data


def read_records(platform, principal):
    data = platform.resources.refund_records
    if not platform.allowed(data, principal):
        return {"missing": ["当前身份没有可用的退款业务记录"]}
    validate_records(data)
    stages = dict(sorted(Counter(x["stage"] for x in data["applications"]).items()))
    return {"business_records": {"citation": "fixture://northstar/refund-records@" + identity(data),
        "as_of": data["as_of"], "environment": data["environment"], "grain": data["grain"],
        "applications": len(data["applications"]), "attempts": len(data["attempts"]),
        "unfinished": sum(n for stage, n in stages.items() if stage != "completed"),
        "stages": stages, "rows": deepcopy(data),
        "limits": "合成业务快照，不与队列842条消息一一对应，不证明根因"}}
