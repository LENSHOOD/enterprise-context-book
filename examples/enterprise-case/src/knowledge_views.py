"""C4 graph, Wiki, and architecture-consistency views for Northstar."""

from __future__ import annotations

from collections import defaultdict, deque


def trace_dependency(
    edges: list[dict],
    visible_ids: set[str],
    start: str,
    max_hops: int = 2,
    allowed_relation_types: set[str] | None = None,
    allow_inverse_navigation: bool = False,
) -> list[dict]:
    """Navigate authorized edges while preserving their declared direction.

    The default follows declared relation direction, which keeps a generic trace
    from treating every incoming historical association as a downstream impact.
    A task plan may explicitly enable inverse navigation: an API-change question,
    for example, starts at the target of ``CALLS`` and ``IMPLEMENTS``.  Even then,
    returned edges always preserve their declared semantic direction.
    """
    if start not in visible_ids:
        return []
    adjacency: dict[str, list[tuple[dict, str]]] = defaultdict(list)
    for edge in edges:
        if (
            edge["from"] in visible_ids
            and edge["to"] in visible_ids
            and (
                allowed_relation_types is None
                or edge["type"] in allowed_relation_types
            )
        ):
            adjacency[edge["from"]].append((edge, edge["to"]))
            if allow_inverse_navigation:
                adjacency[edge["to"]].append((edge, edge["from"]))
    for neighbors in adjacency.values():
        neighbors.sort(
            key=lambda item: (
                item[0]["type"], item[0]["from"], item[0]["to"], item[0]["evidence"]
            )
        )
    found, queue = [], deque([(start, 0, frozenset())])
    visited_states = {(start, frozenset())}
    returned_edges: set[tuple[str, str, str, str]] = set()
    while queue:
        node, depth, path_relations = queue.popleft()
        if depth == max_hops:
            continue
        for edge, neighbor in adjacency[node]:
            # Repeating one semantic relation on a path commonly walks sideways
            # to a sibling object (API <-CALLS- Service -CALLS-> other API).
            # Production query plans should express stricter path patterns; this
            # teaching walker uses a deterministic no-repeat guard.
            if edge["type"] in path_relations:
                continue
            edge_key = (edge["from"], edge["type"], edge["to"], edge["evidence"])
            if edge_key not in returned_edges:
                returned_edges.add(edge_key)
                found.append(edge)
            next_relations = path_relations | {edge["type"]}
            state = (neighbor, next_relations)
            if state not in visited_states:
                visited_states.add(state)
                queue.append((neighbor, depth + 1, next_relations))
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
