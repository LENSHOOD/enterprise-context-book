"""C2 retrieval channels for the Northstar teaching platform.

The module intentionally has no storage or authorization dependency. Callers must
first pass only the objects a principal is allowed to inspect, then use these
functions to rank that already-authorized collection.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict


TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*|[\u4e00-\u9fff]")
SYNONYMS = {
    "退款": {"refund", "create_refund", "退回"},
    "取消": {"cancel", "cancelled", "order.cancelled"},
    "积压": {"backlog", "lag", "queue"},
    "影响": {"impact", "consumer", "依赖"},
    "代码": {"code", "symbol", "实现"},
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def semantic_terms(text: str) -> set[str]:
    terms = set(tokenize(text))
    for key, values in SYNONYMS.items():
        if key in text or terms.intersection(values):
            terms.add(key)
            terms.update(values)
    return terms


def bm25(question: str, documents: list[dict]) -> list[tuple[str, float]]:
    query_terms = tokenize(question)
    tokenized = [tokenize(f"{document['title']} {document['text']}") for document in documents]
    average_length = sum(map(len, tokenized)) / max(len(tokenized), 1)
    document_frequency = Counter(term for terms in tokenized for term in set(terms))
    scores: list[tuple[str, float]] = []
    for document, terms in zip(documents, tokenized):
        frequencies = Counter(terms)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency:
                continue
            inverse = math.log(
                1 + (len(documents) - document_frequency[term] + 0.5)
                / (document_frequency[term] + 0.5)
            )
            denominator = frequency + 1.2 * (0.25 + 0.75 * len(terms) / max(average_length, 1))
            score += inverse * frequency * 2.2 / denominator
        if score:
            scores.append((document["id"], score))
    return sorted(scores, key=lambda item: (-item[1], item[0]))


def semantic_proxy(question: str, documents: list[dict]) -> list[tuple[str, float]]:
    query = semantic_terms(question)
    scores = []
    for document in documents:
        terms = semantic_terms(f"{document['title']} {document['text']}")
        union = query | terms
        score = len(query & terms) / len(union) if union else 0.0
        if score:
            scores.append((document["id"], score))
    return sorted(scores, key=lambda item: (-item[1], item[0]))


def reciprocal_rank_fusion(rankings: dict[str, list[tuple[str, float]]], limit: int) -> list[tuple[str, float, list[str]]]:
    """Fuse rankings while retaining the channels that contributed each object."""
    fused: dict[str, float] = defaultdict(float)
    channels: dict[str, list[str]] = defaultdict(list)
    for channel, ranking in rankings.items():
        for rank, (document_id, _) in enumerate(ranking, start=1):
            fused[document_id] += 1 / (60 + rank)
            channels[document_id].append(channel)
    ordered = sorted(fused, key=lambda document_id: (-fused[document_id], document_id))[:limit]
    return [(document_id, fused[document_id], channels[document_id]) for document_id in ordered]
