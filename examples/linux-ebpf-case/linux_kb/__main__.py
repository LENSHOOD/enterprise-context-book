from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import build_wiki, ingest, query
from .full_kernel import ingest_full, query_full, report_full


def main() -> None:
    parser = argparse.ArgumentParser(prog="linux_kb")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest_parser = commands.add_parser("ingest")
    ingest_parser.add_argument("--repo", type=Path, required=True)
    ingest_parser.add_argument("--ref", default="v6.12")
    ingest_parser.add_argument("--output", type=Path, required=True)
    ingest_parser.add_argument("--scope", action="append", default=[])
    ingest_parser.add_argument("--fixture", action="store_true", help="read local sample files without Git (explicit opt-in)")
    query_parser = commands.add_parser("query")
    query_parser.add_argument("question")
    query_parser.add_argument("--snapshot", type=Path, required=True)
    query_parser.add_argument("--limit", type=int, default=5)
    wiki_parser = commands.add_parser("build-wiki")
    wiki_parser.add_argument("--snapshot", type=Path, required=True)
    full_parser = commands.add_parser("ingest-full")
    full_parser.add_argument("--repo", type=Path, required=True)
    full_parser.add_argument("--ref", default="v6.12")
    full_parser.add_argument("--database", type=Path, required=True)
    full_parser.add_argument("--without-docs", action="store_true")
    full_parser.add_argument("--fixture", action="store_true", help="read local sample files without Git (explicit opt-in)")
    full_query = commands.add_parser("query-full")
    full_query.add_argument("question")
    full_query.add_argument("--database", type=Path, required=True)
    full_query.add_argument("--limit", type=int, default=10)
    full_query.add_argument("--subsystem")
    full_report = commands.add_parser("report-full")
    full_report.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "ingest":
        scope = args.scope or ["kernel/bpf/**/*.c", "kernel/bpf/*.c", "include/uapi/linux/bpf.h", "Documentation/bpf/**/*.rst"]
        result = ingest(args.repo, args.ref, args.output, scope, fixture=args.fixture)
    elif args.command == "query":
        result = query(args.snapshot, args.question, args.limit)
    elif args.command == "build-wiki":
        result = {"wiki": str(args.snapshot / "wiki.md"), "characters": len(build_wiki(args.snapshot))}
    elif args.command == "ingest-full":
        result = ingest_full(args.repo, args.ref, args.database, not args.without_docs, fixture=args.fixture)
    elif args.command == "query-full":
        result = query_full(args.database, args.question, args.limit, args.subsystem)
    else:
        result = report_full(args.database)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
