"""Dependency-free, syntax-only Linux source knowledge-base builder.

This parser intentionally emits candidate calls rather than pretending regular
expressions can reproduce a C compiler. A production adapter can replace the
extractor with Tree-sitter/clang/SCIP while retaining the snapshot contract.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from .source_tree import SourceTree, matches_scope


FUNCTION_RE = re.compile(
    r"(?m)^[\t ]*(?:static\s+)?(?:inline\s+)?(?:[A-Za-z_][\w\s*]*?\s+)?"
    r"(?P<name>[A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{"
)
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
ENUM_ITEM_RE = re.compile(r"(?m)^\s*(BPF_[A-Z0-9_]+)\s*(?:=|,)")
TYPE_RE = re.compile(r"(?m)^[\t ]*(?:struct|enum)\s+([A-Za-z_]\w*)[^;\n]*\{")
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*|[\u4e00-\u9fff]")
CONTROL_WORDS = {"if", "for", "while", "switch", "return", "sizeof", "defined"}


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _function_spans(text: str) -> list[tuple[str, int, int, str]]:
    spans = []
    for match in FUNCTION_RE.finditer(text):
        if match.group('name') in CONTROL_WORDS:
            continue
        depth, index = 1, match.end()
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        spans.append((match.group("name"), match.start(), index, text[match.end():index - 1]))
    return spans


def _citation(commit: str, relative: str, symbol: str, line: int) -> str:
    return f"code://linux/kernel@{commit}/{relative}#{symbol}:L{line}"


def ingest(repo: Path, ref: str, output: Path, scope: list[str], *, fixture: bool = False) -> dict:
    with SourceTree(repo, ref, fixture) as source:
        return _ingest(source, ref, output.resolve(), scope)


def _ingest(source: SourceTree, ref: str, output: Path, scope: list[str]) -> dict:
    repo, commit = source.repo, source.commit
    files = sorted(path for path in source.blobs
                   if Path(path).suffix in {".c", ".h", ".md", ".rst"}
                   and any(matches_scope(path, pattern) for pattern in scope))
    if not files:
        raise ValueError("scope contains no supported source files")
    nodes, edges, unresolved = [], [], []
    definitions: dict[str, list[str]] = defaultdict(list)

    for relative in files:
        suffix = Path(relative).suffix
        if suffix not in {".c", ".h", ".md", ".rst"}:
            continue
        text = source.read(relative)
        file_id = f"file:{relative}"
        nodes.append({
            "id": file_id, "kind": "file", "name": Path(relative).name, "path": relative,
            "text": text[:4000], "citation": _citation(commit, relative, "file", 1),
        })
        if suffix in {".md", ".rst"}:
            continue
        for type_match in TYPE_RE.finditer(text):
            type_name = type_match.group(1)
            line = _line(text, type_match.start(1))
            node_id = f"type:{relative}#{type_name}:L{line}"
            nodes.append({
                "id": node_id, "kind": "type", "name": type_name, "path": relative,
                "text": f"type {type_name} defined in {relative}",
                "citation": _citation(commit, relative, type_name, line),
            })
            edges.append({"from": file_id, "type": "DEFINES", "to": node_id, "certainty": "syntax"})
        for command_match in ENUM_ITEM_RE.finditer(text):
            command = command_match.group(1)
            line = _line(text, command_match.start(1))
            node_id = f"command:{relative}#{command}:L{line}"
            nodes.append({
                "id": node_id, "kind": "syscall_command", "name": command, "path": relative,
                "text": f"eBPF syscall command {command}",
                "citation": _citation(commit, relative, command, line),
            })
            edges.append({"from": file_id, "type": "DEFINES", "to": node_id, "certainty": "syntax"})
        for name, start, end, body in _function_spans(text):
            line = _line(text, start)
            node_id = f"symbol:{relative}#{name}:L{line}"
            nodes.append({
                "id": node_id, "kind": "function", "name": name, "path": relative,
                "text": text[start:min(end, start + 1500)],
                "citation": _citation(commit, relative, name, line),
            })
            definitions[name].append(node_id)
            edges.append({"from": file_id, "type": "DEFINES", "to": node_id, "certainty": "syntax"})
            for called in sorted(set(CALL_RE.findall(body)) - CONTROL_WORDS):
                edges.append({
                    "from": node_id, "type": "CALLS_CANDIDATE", "to_name": called,
                    "certainty": "syntax-candidate", "evidence": _citation(commit, relative, name, line),
                })

    for edge in edges:
        if "to_name" not in edge:
            continue
        targets = definitions.get(edge["to_name"], [])
        if len(targets) == 1:
            edge["to"] = targets[0]
            edge["type"] = "CALLS_RESOLVED_NAME"
            edge["certainty"] = "name-resolved"
        else:
            edge["to"] = f"unresolved:{edge['to_name']}"
            unresolved.append({
                "caller": edge["from"], "target_name": edge["to_name"],
                "reason": "not-found" if not targets else "ambiguous",
                "candidate_count": len(targets),
            })
        edge.pop("to_name")

    # Deduplicate repeated command nodes while preserving deterministic order.
    unique_nodes = {node["id"]: node for node in nodes}
    manifest = {
        "schema": "linux-kb-snapshot@2", "repository": str(repo), "ref": ref,
        "commit": commit, "mode": "syntax-only", "scope": scope,
        "source_mode": "fixture" if source.fixture else "git-blobs",
        "counts": {"files": len(files), "nodes": len(unique_nodes), "edges": len(edges), "unresolved": len(unresolved)},
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "nodes.json").write_text(json.dumps(list(unique_nodes.values()), indent=2), encoding="utf-8")
    (output / "edges.json").write_text(json.dumps(edges, indent=2), encoding="utf-8")
    (output / "unresolved.json").write_text(json.dumps(unresolved, indent=2), encoding="utf-8")
    return manifest


def load_snapshot(output: Path) -> dict:
    return {
        name: json.loads((output / f"{name}.json").read_text(encoding="utf-8"))
        for name in ("manifest", "nodes", "edges", "unresolved")
    }


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _rank(question: str, nodes: list[dict]) -> list[tuple[float, dict]]:
    query_terms, tokenized = _tokens(question), [_tokens(f"{n['name']} {n['text']}") for n in nodes]
    average = sum(map(len, tokenized)) / max(len(tokenized), 1)
    df = Counter(term for terms in tokenized for term in set(terms))
    ranked = []
    for node, terms in zip(nodes, tokenized):
        frequencies, score = Counter(terms), 0.0
        for term in query_terms:
            if not frequencies[term]:
                continue
            inverse = math.log(1 + (len(nodes) - df[term] + .5) / (df[term] + .5))
            score += inverse * frequencies[term] * 2.2 / (
                frequencies[term] + 1.2 * (.25 + .75 * len(terms) / max(average, 1))
            )
        if score:
            ranked.append((score, node))
    return sorted(ranked, key=lambda item: (-item[0], item[1]["id"]))


def query(output: Path, question: str, limit: int = 5, hops: int = 1) -> dict:
    snapshot = load_snapshot(output)
    hits = _rank(question, snapshot["nodes"])[:limit]
    seed_ids = {node["id"] for _, node in hits}
    adjacency: dict[str, list[dict]] = defaultdict(list)
    for edge in snapshot["edges"]:
        adjacency[edge["from"]].append(edge)
    relations, queue, visited = [], deque((node_id, 0) for node_id in seed_ids), set(seed_ids)
    while queue:
        node_id, depth = queue.popleft()
        if depth == hops:
            continue
        for edge in adjacency[node_id]:
            relations.append(edge)
            if edge["to"] not in visited:
                visited.add(edge["to"])
                queue.append((edge["to"], depth + 1))
    return {
        "manifest": snapshot["manifest"], "question": question,
        "hits": [{"score": round(score, 4), **node} for score, node in hits],
        "relations": relations,
        "warnings": ["syntax-only: calls are not compiler-proven"] if snapshot["manifest"]["mode"] == "syntax-only" else [],
    }


def build_wiki(output: Path) -> str:
    snapshot = load_snapshot(output)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for node in snapshot["nodes"]:
        grouped[node["path"]].append(node)
    lines = ["# eBPF 源码知识地图", "", f"快照：`{snapshot['manifest']['commit']}`", "", "> 模式：syntax-only；候选调用必须由编译信息复核。", ""]
    for path, nodes in sorted(grouped.items()):
        lines.extend([f"## `{path}`", ""])
        for node in sorted(nodes, key=lambda item: (item["kind"], item["name"])):
            if node["kind"] == "file":
                continue
            lines.append(f"- **{node['kind']} `{node['name']}`** — [{node['citation']}]({node['citation']})")
        lines.append("")
    text = "\n".join(lines)
    (output / "wiki.md").write_text(text, encoding="utf-8")
    return text
