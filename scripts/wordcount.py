#!/usr/bin/env python3
"""Count CJK characters in the manuscript while excluding fenced code blocks."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def prose(text: str) -> str:
    output: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            output.append(line)
    return "\n".join(output)


def count_manuscript() -> tuple[int, list[tuple[str, int]]]:
    files = sorted((ROOT / "book").glob("part-*/*.md"))
    files += [ROOT / "book" / "extras" / "full-linux-kernel.md", ROOT / "book" / "appendices.md"]
    counts = []
    for path in files:
        count = len(CJK.findall(prose(path.read_text(encoding="utf-8"))))
        counts.append((str(path.relative_to(ROOT)), count))
    return sum(count for _, count in counts), counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimum", type=int, default=0)
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()
    total, counts = count_manuscript()
    if args.details:
        for path, count in counts:
            print(f"{count:>6}  {path}")
    print(f"CJK prose characters: {total}")
    if total < args.minimum:
        raise SystemExit(f"length gate failed: {total} < {args.minimum}")


if __name__ == "__main__":
    main()
