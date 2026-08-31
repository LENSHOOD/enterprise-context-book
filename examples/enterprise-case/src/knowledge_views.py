"""C3 graph, Wiki, and architecture-consistency views for Northstar."""

from __future__ import annotations

from collections import defaultdict, deque


def trace_dependency(edges: list[dict], visible_ids: set[str], start: str, max_hops: int = 2) -> list[dict]:
    """Traverse only evidence edges whose endpoints are already authorized."""
    if start not in visible_ids:
        return []
    adjacency: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        if edge["from"] in visible_ids and edge["to"] in visible_ids:
            adjacency[edge["from"]].append(edge)
    found, queue = [], deque([(start, 0)])
    visited = {start}
    while queue:
        node, depth = queue.popleft()
        if depth == max_hops:
            continue
        for edge in adjacency[node]:
            found.append(edge)
            if edge["to"] not in visited:
                visited.add(edge["to"])
                queue.append((edge["to"], depth + 1))
    return found


def build_role_scoped_wiki(documents: list[dict], role: str) -> list[dict]:
    """Compile deterministic, role-scoped pages whose inputs are their lineage."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for document in documents:
        grouped[document.get("system", "business")].append(document)
    pages = []
    for system, group in sorted(grouped.items()):
        group.sort(key=lambda document: (document["kind"], document["id"]))
        pages.append({
            "page_id": f"wiki:system:{system}:{role}",
            "title": f"{system} 系统知识页",
            "status": "ready",
            "acl_role": role,
            "inputs": [document["citation"] for document in group],
            "sections": [
                {"title": document["title"], "summary": document["text"]}
                for document in group
            ],
        })
    return pages


def compare_architecture_claims(
    claims_document: dict,
    edges: list[dict],
    visible_ids: set[str],
) -> dict[str, list[dict]]:
    """Keep architecture assertions distinct from implementation and runtime evidence."""
    scope = claims_document["scope"]
    relation_types = set(scope["relation_types"])
    from_ids = set(scope.get("from_ids", []))
    to_ids = set(scope.get("to_ids", []))

    def in_scope(item: dict) -> bool:
        return (
            item["type"] in relation_types
            and (not from_ids or item["from"] in from_ids)
            and (not to_ids or item["to"] in to_ids)
        )

    claims = {
        (claim["from"], claim["type"], claim["to"]): claim
        for claim in claims_document["claims"]
        if in_scope(claim) and claim["from"] in visible_ids and claim["to"] in visible_ids
    }
    evidence: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for edge in edges:
        key = (edge["from"], edge["type"], edge["to"])
        if (
            in_scope(edge)
            and edge["evidence_tier"] in {"deterministic", "resolved", "observed"}
            and edge["from"] in visible_ids
            and edge["to"] in visible_ids
        ):
            evidence[key].append(edge)

    declared = set(claims)
    evidenced = set(evidence)
    source = claims_document["source"]

    def claim_record(key: tuple[str, str, str]) -> dict:
        return {**claims[key], "claim_source": source}

    def evidence_record(key: tuple[str, str, str]) -> dict:
        return {
            "from": key[0],
            "type": key[1],
            "to": key[2],
            "evidence": sorted(
                evidence[key], key=lambda edge: (edge["evidence_tier"], edge["evidence"])
            ),
        }

    return {
        "declared_and_evidenced": [
            {**claim_record(key), "evidence": evidence_record(key)["evidence"]}
            for key in sorted(declared & evidenced)
        ],
        "declared_not_evidenced": [claim_record(key) for key in sorted(declared - evidenced)],
        "evidenced_not_declared": [
            evidence_record(key) for key in sorted(evidenced - declared)
        ],
    }
