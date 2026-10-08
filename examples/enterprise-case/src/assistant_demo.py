"""Run both assistant workflows; fixture is authored, http calls a configured model."""
import argparse
import json
from pathlib import Path
import tempfile

from intelligence import DEMO_SOURCE
from workbench import WorkspaceStore


def demo(database: Path, mode: str = "fixture") -> dict:
    store = WorkspaceStore(database)
    space = store.create()

    def call(op, role="product", **values):
        return store.call(space, {"op": op, "role": role, **values})

    source = call("resource.register", text=DEMO_SOURCE)
    draft = call("resource.propose", id=source["id"], mode=mode)
    draft = call("assist.step", id=draft["id"], kind="resource")
    # In HTTP mode, never automatically approve a generated business meaning.
    if mode == "http":
        request = call("assist.start", "sre", goal="退款积压需要检查哪些材料？", mode=mode)
        request = call("assist.step", "sre", id=request["id"])
        return {"mode": mode, "note": "真实模型生成的资源和任务草案；尚未代替读者审核或批准", "draft": draft, "request": request}
    if draft["state"] != "needs_review":
        raise ValueError("演示资源候选没有通过检查")
    published = call("resource.publish", id=draft["id"], confirmation_hash=draft["confirmation_hash"],
                     note="演示脚本核对固定原文、类型和关系；真实模型候选须在工作台人工审核")
    request = call("assist.start", "sre", goal="退款积压需要检查哪些材料？", mode=mode)
    request = call("assist.step", "sre", id=request["id"])
    request = call("assist.confirm", "sre", id=request["id"], confirmation_hash=request["confirmation_hash"],
                   answer="只调查退款服务，整理材料和当前观察，不执行重放")
    while request["state"] == "ready":
        request = call("assist.step", "sre", id=request["id"])
    return {"mode": mode, "note": "手写脚本演示，不是大模型评测", "published": published, "request": request}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("fixture", "http"), default="fixture")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="northstar-assistant-") as folder:
        print(json.dumps(demo(Path(folder) / "lab.sqlite3", args.mode), ensure_ascii=False, indent=2))
