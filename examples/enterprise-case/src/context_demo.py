#!/usr/bin/env python3
"""Dependency-free vertical slice: ingest JSON, lexical rank, ACL filter, cite evidence.

This file intentionally keeps a tiny BM25 implementation so chapter 15 can be read
and run as one file. The fuller teaching platform has a behavior-equivalent scorer
in ``northstar.py``; production code should place the scorer in a shared package.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def bm25(query: str, documents: list[dict]) -> list[tuple[float, dict]]:
    query_terms = tokenize(query)
    tokenized = [tokenize(f"{doc['title']} {doc['text']}") for doc in documents]
    average_length = sum(map(len, tokenized)) / max(len(tokenized), 1)
    document_frequency = Counter(term for terms in tokenized for term in set(terms))
    ranked: list[tuple[float, dict]] = []

    for doc, terms in zip(documents, tokenized):
        frequencies = Counter(terms)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency:
                continue
            inverse_frequency = math.log(1 + (len(documents) - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            denominator = frequency + 1.2 * (1 - 0.75 + 0.75 * len(terms) / average_length)
            score += inverse_frequency * frequency * 2.2 / denominator
        ranked.append((score, doc))
    return sorted(ranked, key=lambda item: item[0], reverse=True)


def query(data_path: Path, question: str, role: str, limit: int = 3) -> dict:
    documents = json.loads(data_path.read_text(encoding="utf-8"))
    allowed = [doc for doc in documents if role in doc["acl"]]
    hits = [
        {
            "score": round(score, 4),
            "id": doc["id"],
            "title": doc["title"],
            "kind": doc["kind"],
            "version": doc["version"],
            "evidence": doc["text"],
            "citation": doc.get("citation") or f"knowledge://northstar/{doc['id']}@{doc['version']}",
        }
        for score, doc in bm25(question, allowed)[:limit]
        if score > 0
    ]
    return {"question": question, "role": role, "authorized_documents": len(allowed), "hits": hits}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--role", default="developer")
    parser.add_argument("--data", type=Path, default=Path(__file__).parents[1] / "data" / "knowledge.json")
    args = parser.parse_args()
    print(json.dumps(query(args.data, args.question, args.role), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
