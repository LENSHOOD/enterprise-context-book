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
            "sample_notice": "构建时由同一份 Python 代码生成的教学示例，不是当前浏览器实际运行结果。"}


if __name__ == "__main__":
    output = ROOT / "book/.vitepress/theme/generated/northstar.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_catalog(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Northstar snippets + samples: {output.relative_to(ROOT)}")
