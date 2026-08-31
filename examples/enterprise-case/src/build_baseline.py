#!/usr/bin/env python3
"""Compile the smallest Northstar source fixture into governed knowledge objects.

This is intentionally a teaching compiler, not a generic connector framework. It
shows the first irreversible boundary in the case: human-readable sources become
objects with identity, version, ACL, time, lineage, and a navigable citation.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
RAW_ROOT = ROOT / "data" / "raw"
DEFAULT_OUTPUT = ROOT / "generated" / "baseline-knowledge.json"


def normalise_markdown(source: str) -> str:
    return " ".join(
        line.lstrip("#").strip()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def parse_python_symbol(source: str, symbol: str) -> str:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            docstring = ast.get_docstring(node) or ""
            segment = ast.get_source_segment(source, node) or ""
            return f"{symbol} {docstring} {segment}".strip()
    raise ValueError(f"symbol {symbol!r} was not found in source fixture")


def parse_source(source_path: Path, parser: str, symbol: str | None = None) -> str:
    source = source_path.read_text(encoding="utf-8")
    if parser == "markdown":
        return normalise_markdown(source)
    if parser == "json":
        value = json.loads(source)
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if parser == "python_symbol" and symbol:
        return parse_python_symbol(source, symbol)
    raise ValueError(f"unsupported parser configuration for {source_path}")


def compile_documents(manifest_path: Path = RAW_ROOT / "manifest.json") -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "northstar-raw-fixture/1":
        raise ValueError("unsupported raw fixture manifest")

    documents = []
    for item in manifest["sources"]:
        source_path = manifest_path.parent / item["path"]
        text = parse_source(source_path, item["parser"], item.get("symbol"))
        source_uri = f"fixture://northstar/{item['path']}@{item['version']}"
        content_hash = f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"
        documents.append({
            "id": item["id"],
            "entity_type": item["entity_type"],
            "title": item["title"],
            "kind": item["kind"],
            "tenant": item["tenant"],
            "system": item["system"],
            "acl": item["acl"],
            "version": item["version"],
            "authority": item["authority"],
            "citation": item["citation"],
            "text": text,
            "version_id": f"kv:{content_hash[:23]}",
            "content_hash": content_hash,
            "source": {"uri": source_uri, "revision": item["version"], "path": item["path"]},
            "time": {
                "valid_from": item["valid_from"],
                "valid_to": None,
                "observed_at": item["observed_at"],
            },
            "lineage": {
                "derived_from": [source_uri],
                "transform": "baseline-compiler@1",
            },
        })
    return documents


def write_documents(output_path: Path, manifest_path: Path = RAW_ROOT / "manifest.json") -> list[dict]:
    documents = compile_documents(manifest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=RAW_ROOT / "manifest.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    documents = write_documents(args.output, args.manifest)
    print(json.dumps({"output": str(args.output), "object_count": len(documents)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
