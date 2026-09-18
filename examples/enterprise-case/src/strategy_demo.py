#!/usr/bin/env python3
"""Run the read-only C7 strategic Context Package through Northstar."""
from __future__ import annotations
import argparse
import json
from northstar import NorthstarPlatform, Principal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default="H2 的销售情况为什么比 H1 差这么多？")
    parser.add_argument("--role", default="executive", choices=["executive", "strategy", "revops", "product"])
    parser.add_argument("--task", default="STRATEGY-REVIEW")
    parser.add_argument("--confirm-definition", action="store_true")
    args = parser.parse_args()
    platform = NorthstarPlatform()
    result = platform.context(
        args.question,
        Principal("strategy-demo", args.role),
        args.task,
        mode="strategic",
        definition_confirmation=(platform.strategy_context.definition_confirmation()
                                 if args.confirm_definition else None),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
