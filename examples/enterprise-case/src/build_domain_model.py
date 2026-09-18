#!/usr/bin/env python3
"""Compile Northstar's authoring model and validate it against fixture instances."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from modeling import DEFAULT_MODEL_DIR, compile_domain_model, validate_knowledge_base
from build_knowledge import compile_knowledge


ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = ROOT / "generated" / "domain-model.json"
DEFAULT_REPORT = ROOT / "generated" / "model-validation.json"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(
    model_dir: Path = DEFAULT_MODEL_DIR,
    data_dir: Path = ROOT / "data",
    output: Path = DEFAULT_OUTPUT,
    report_output: Path = DEFAULT_REPORT,
) -> tuple[dict, dict]:
    model = compile_domain_model(model_dir)
    documents = compile_knowledge(data_dir)
    edges = json.loads((data_dir / "relations.json").read_text(encoding="utf-8"))
    report = validate_knowledge_base(model, documents, edges)
    write_json(output, model)
    write_json(report_output, report)
    return model, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    model, report = build(args.model_dir, args.data_dir, args.output, args.report)
    print(json.dumps({
        "output": str(args.output),
        "report": str(args.report),
        "model_id": model["modelId"],
        "version": model["version"],
        "valid": report["model"]["valid"] and report["instances"]["valid"],
        "glossary_terms": report["model"]["glossary_terms"],
        "entity_types": report["model"]["entity_types"],
        "relation_types": report["model"]["relation_types"],
        "supported_questions": sum(
            item["supported"] for item in report["instances"]["competency_questions"]
        ),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
