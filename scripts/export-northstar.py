"""Build source-bound snippets and explicitly labelled sample results for the book."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "examples/enterprise-case/src"
sys.path.insert(0, str(SRC))
from tutorial_catalog import LESSONS
from workbench import Workspace, SCENARIOS, source_revision
from intelligence import ContextAssistant, DEMO_SOURCE
from model_gateway import fixture_decision


def assistant_samples():
    workspace = Workspace()
    assistant = ContextAssistant(workspace)
    actor = workspace.principal("product")
    source = workspace.dispatch({"op": "resource.register", "role": "product", "text": DEMO_SOURCE})
    draft = workspace.dispatch({"op": "resource.propose", "role": "product", "id": source["id"]})
    payload = {"id": draft["id"], "kind": "resource"}
    _, context = assistant.prepare(payload, actor)
    resource = assistant.apply(payload, actor, fixture_decision(context), {"mode": "fixture", "model": "authored-demo-v1"})
    actor = workspace.principal("sre")
    query = workspace.dispatch({"op": "assist.start", "role": "sre", "goal": "退款积压怎么查？"})
    payload = {"id": query["id"]}
    _, context = assistant.prepare(payload, actor)
    query = assistant.apply(payload, actor, fixture_decision(context), {"mode": "fixture", "model": "authored-demo-v1"})
    return {
        "resource": {"sample": resource, "sources": [snippet("intelligence.py", "ContextAssistant.resource_candidate"),
            snippet("intelligence.py", "materialize_resources"), snippet("intelligence.py", "ContextAssistant.dispatch")]},
        "query": {"sample": query, "sources": [snippet("intelligence.py", "ContextAssistant.prepare"),
            snippet("intelligence.py", "ContextAssistant.query_step"), snippet("workbench.py", "WorkspaceStore.model_step"),
            snippet("model_gateway.py", "ModelGateway.decide")]},
    }


def snippet(filename, symbol):
    path = (SRC / filename).resolve()
    text = path.read_text(encoding="utf-8")
    if symbol is None:
        return {"path": str(path.relative_to(ROOT)), "symbol": "来源文件",
                "start": 1, "end": len(text.splitlines()), "code": text}
    node = ast.parse(text)
    for part in symbol.split("."):
        node = next(item for item in node.body if getattr(item, "name", None) == part)
    return {"path": str(path.relative_to(ROOT)), "symbol": symbol,
            "start": node.lineno, "end": node.end_lineno,
            "code": "\n".join(text.splitlines()[node.lineno - 1:node.end_lineno])}


def build_catalog():
    lessons = deepcopy(LESSONS)
    for key, lesson in lessons.items():
        lesson["sources"] = [snippet(*pointer) for pointer in lesson["sources"]]
        workspace = Workspace()
        if "scenario" in lesson:
            kind = lesson["scenario"]
            task = workspace.dispatch({"op": "task.create", "kind": kind, **SCENARIOS[kind]})
            sample = workspace.dispatch({"op": "task.context", "role": lesson["role"], "task_id": task["id"]})
            # Samples describe a state; action workflows run stepwise only in the local service.
            lesson["sample"] = sample
        else:
            lesson["sample"] = workspace.dispatch({**lesson["request"], "role": lesson["role"]})
    return {"source_revision": source_revision(), "scenarios": SCENARIOS, "lessons": lessons,
            "assistants": assistant_samples(), "assistant_source": DEMO_SOURCE,
            "sample_notice": "构建时由同一份 Python 代码生成的教学示例，不是当前浏览器实际运行结果。"}


if __name__ == "__main__":
    output = ROOT / "book/.vitepress/theme/generated/northstar.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_catalog(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Northstar snippets + samples: {output.relative_to(ROOT)}")
