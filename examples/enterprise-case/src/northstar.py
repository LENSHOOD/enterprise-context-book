#!/usr/bin/env python3
"""Runnable Northstar context platform using only the Python standard library.

The implementation is deliberately small, but its contracts mirror the book:
ACL-before-retrieval, immutable citations, lexical/semantic fusion, evidence-backed
graph traversal, generated Wiki pages, task memory, and a structured Context API.

``context_demo.py`` deliberately repeats the minimal BM25 scorer to remain a
single-file chapter example. Keep its ranking behavior aligned with this teaching
platform; a production package should share one retrieval implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).parents[1]
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*|[\u4e00-\u9fff]")
SYNONYMS = {
    "退款": {"refund", "create_refund", "退回"},
    "取消": {"cancel", "cancelled", "order.cancelled"},
    "积压": {"backlog", "lag", "queue"},
    "影响": {"impact", "consumer", "依赖"},
    "代码": {"code", "symbol", "实现"},
}

READ_TOOLS = {
    "support": ["search_context", "get_evidence"],
    "developer": ["search_context", "get_evidence", "trace_dependency"],
    "sre": ["search_context", "get_evidence", "trace_dependency", "get_current_status"],
    "incident_commander": ["search_context", "get_evidence", "trace_dependency", "get_current_status"],
}
ACTION_ROLES = {"sre", "incident_commander"}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def semantic_terms(text: str) -> set[str]:
    terms = set(tokenize(text))
    for key, values in SYNONYMS.items():
        if key in text or terms.intersection(values):
            terms.add(key)
            terms.update(values)
    return terms


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str
    tenant: str = "northstar"


@dataclass
class TaskMemory:
    events: dict[str, list[dict]] = field(default_factory=lambda: defaultdict(list))

    def append(self, task_id: str, event: dict) -> dict:
        record = {"sequence": len(self.events[task_id]) + 1, **event}
        self.events[task_id].append(record)
        return record

    def read(self, task_id: str) -> list[dict]:
        return list(self.events.get(task_id, []))


class NorthstarPlatform:
    def __init__(self, data_dir: Path = ROOT / "data") -> None:
        self.documents = json.loads((data_dir / "knowledge.json").read_text(encoding="utf-8"))
        self.edges = json.loads((data_dir / "relations.json").read_text(encoding="utf-8"))
        self.architecture_claims = json.loads(
            (data_dir / "architecture-claims.json").read_text(encoding="utf-8")
        )
        self.runtime = json.loads((data_dir / "runtime.json").read_text(encoding="utf-8"))
        self.by_id = {doc["id"]: doc for doc in self.documents}
        self.memory = TaskMemory()
        canonical = json.dumps(
            {
                "documents": self.documents,
                "edges": self.edges,
                "architecture_claims": self.architecture_claims,
            },
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode()
        self.manifest = f"northstar-{hashlib.sha256(canonical).hexdigest()[:12]}"
        self.task_states: dict[str, str] = defaultdict(lambda: "opened")
        self.previews: dict[str, dict] = {}
        self.tokens: dict[str, dict] = {}
        self.receipts: dict[str, dict] = {}
        self.execution_count = 0

    @staticmethod
    def allowed(doc: dict, principal: Principal) -> bool:
        return doc.get("tenant", "northstar") == principal.tenant and principal.role in doc["acl"]

    def visible_documents(self, principal: Principal, kinds: set[str] | None = None) -> list[dict]:
        return [
            doc for doc in self.documents
            if self.allowed(doc, principal) and (not kinds or doc["kind"] in kinds)
        ]

    @staticmethod
    def _parse_instant(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def documents_as_of(
        self,
        principal: Principal,
        valid_at: str,
        observed_at: str,
        kinds: set[str] | None = None,
    ) -> list[dict]:
        """Filter by business validity and first observation.

        This fixture does not preserve every historical transaction-time mutation;
        exact replay still requires the immutable Manifest published at that time.
        """
        valid_instant = self._parse_instant(valid_at)
        observed_instant = self._parse_instant(observed_at)
        selected = []
        for doc in self.visible_documents(principal, kinds):
            envelope = doc["time"]
            valid_from = self._parse_instant(envelope["valid_from"])
            valid_to = (
                self._parse_instant(envelope["valid_to"])
                if envelope.get("valid_to")
                else None
            )
            first_observed = self._parse_instant(envelope["observed_at"])
            if valid_from <= valid_instant and (valid_to is None or valid_instant < valid_to):
                if first_observed <= observed_instant:
                    selected.append(doc)
        return selected

    @staticmethod
    def _bm25(question: str, documents: list[dict]) -> list[tuple[str, float]]:
        query_terms = tokenize(question)
        tokenized = [tokenize(f"{d['title']} {d['text']}") for d in documents]
        avg = sum(map(len, tokenized)) / max(len(tokenized), 1)
        df = Counter(term for terms in tokenized for term in set(terms))
        scores: list[tuple[str, float]] = []
        for doc, terms in zip(documents, tokenized):
            frequencies = Counter(terms)
            score = 0.0
            for term in query_terms:
                frequency = frequencies[term]
                if not frequency:
                    continue
                inverse = math.log(1 + (len(documents) - df[term] + 0.5) / (df[term] + 0.5))
                denominator = frequency + 1.2 * (0.25 + 0.75 * len(terms) / max(avg, 1))
                score += inverse * frequency * 2.2 / denominator
            if score:
                scores.append((doc["id"], score))
        return sorted(scores, key=lambda item: (-item[1], item[0]))

    @staticmethod
    def _semantic(question: str, documents: list[dict]) -> list[tuple[str, float]]:
        query = semantic_terms(question)
        scores = []
        for doc in documents:
            terms = semantic_terms(f"{doc['title']} {doc['text']}")
            union = query | terms
            score = len(query & terms) / len(union) if union else 0
            if score:
                scores.append((doc["id"], score))
        return sorted(scores, key=lambda item: (-item[1], item[0]))

    def search(
        self, question: str, principal: Principal, limit: int = 5,
        kinds: set[str] | None = None, disabled_channels: set[str] | None = None,
    ) -> list[dict]:
        # Security invariant: unauthorized objects never enter either scorer.
        visible = self.visible_documents(principal, kinds)
        disabled_channels = disabled_channels or set()
        lexical = [] if "bm25" in disabled_channels else self._bm25(question, visible)
        semantic = [] if "semantic_proxy" in disabled_channels else self._semantic(question, visible)
        fused: dict[str, float] = defaultdict(float)
        channels: dict[str, list[str]] = defaultdict(list)
        for channel, ranking in (("bm25", lexical), ("semantic_proxy", semantic)):
            for rank, (doc_id, _) in enumerate(ranking, start=1):
                fused[doc_id] += 1 / (60 + rank)
                channels[doc_id].append(channel)
        ranked = sorted(fused, key=lambda doc_id: (-fused[doc_id], doc_id))[:limit]
        return [self._hit(self.by_id[doc_id], fused[doc_id], channels[doc_id]) for doc_id in ranked]

    @staticmethod
    def _hit(doc: dict, score: float, channels: list[str]) -> dict:
        return {
            "id": doc["id"], "kind": doc["kind"], "title": doc["title"],
            "version": doc["version"], "citation": doc["citation"],
            "evidence": doc["text"], "score": round(score, 6), "channels": channels,
            "authority": doc.get("authority", "informative"),
        }

    def trace(self, start: str, principal: Principal, max_hops: int = 2) -> list[dict]:
        """Traverse only edges whose endpoints are both authorized."""
        visible = {doc["id"] for doc in self.visible_documents(principal)}
        if start not in visible:
            return []
        adjacency: dict[str, list[dict]] = defaultdict(list)
        for edge in self.edges:
            if edge["from"] in visible and edge["to"] in visible:
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

    def architecture_consistency(self, principal: Principal) -> dict[str, list[dict]]:
        """Compare declared EA relations with implementation and runtime evidence.

        Absence of evidence is reported for review; it is not treated as proof that a
        declared path is dead. ACL filtering happens before either side is compared.
        """
        visible = {doc["id"] for doc in self.visible_documents(principal)}
        scope = self.architecture_claims["scope"]
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
            for claim in self.architecture_claims["claims"]
            if in_scope(claim)
            and claim["from"] in visible
            and claim["to"] in visible
        }
        evidence: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
        for edge in self.edges:
            key = (edge["from"], edge["type"], edge["to"])
            if (
                in_scope(edge)
                and edge["evidence_tier"] in {"deterministic", "resolved", "observed"}
                and edge["from"] in visible
                and edge["to"] in visible
            ):
                evidence[key].append(edge)

        declared = set(claims)
        evidenced = set(evidence)
        source = self.architecture_claims["source"]

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
            "declared_not_evidenced": [
                claim_record(key) for key in sorted(declared - evidenced)
            ],
            "evidenced_not_declared": [
                evidence_record(key) for key in sorted(evidenced - declared)
            ],
        }

    def build_wiki(self, principal: Principal) -> list[dict]:
        """Compile deterministic pages; inputs double as lineage."""
        visible = self.visible_documents(principal)
        grouped: dict[str, list[dict]] = defaultdict(list)
        for doc in visible:
            grouped[doc.get("system", "business")].append(doc)
        pages = []
        for system, docs in sorted(grouped.items()):
            docs.sort(key=lambda doc: (doc["kind"], doc["id"]))
            pages.append({
                "page_id": f"wiki:system:{system}:{principal.role}",
                "title": f"{system} 系统知识页",
                "status": "ready",
                "acl_role": principal.role,
                "inputs": [doc["citation"] for doc in docs],
                "sections": [{"title": doc["title"], "summary": doc["text"]} for doc in docs],
            })
        return pages

    def get_status(self, resource: str, principal: Principal) -> dict | None:
        status = self.runtime.get(resource)
        if not status or principal.role not in status["acl"] or principal.tenant != status["tenant"]:
            return None
        return {key: value for key, value in status.items() if key != "acl"}

    def allowed_tools(self, principal: Principal, task_id: str) -> list[str]:
        tools = list(READ_TOOLS.get(principal.role, []))
        state = self.task_states[task_id]
        if principal.role in ACTION_ROLES and state in {"diagnosing", "action_proposed"}:
            tools.append("prepare_replay")
        if principal.role in ACTION_ROLES and state == "approved":
            tools.append("execute_replay")
        if principal.role in ACTION_ROLES and state == "verifying":
            tools.append("verify_replay")
        return tools

    def prepare_replay(
        self, task_id: str, queue: str, principal: Principal,
        now: datetime | None = None,
    ) -> dict:
        if principal.role not in ACTION_ROLES:
            raise PermissionError("replay preview requires an operations role")
        status = self.get_status(queue, principal)
        if status is None:
            raise PermissionError("queue is not visible to this principal")
        now = now or datetime.now(timezone.utc)
        params = {
            "task_id": task_id,
            "tool": "replay_dead_letters",
            "target_queue": queue,
            "tenant_scope": principal.tenant,
            "message_count": min(status["queue_depth"], 100),
            "queue_depth": status["queue_depth"],
        }
        params_hash = hashlib.sha256(
            json.dumps(params, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        preview = {
            **params,
            "preview_id": f"preview:{task_id}:{params_hash[:12]}",
            "params_hash": params_hash,
            "side_effects": ["messages may be delivered more than once"],
            "expires_at": (now + timedelta(seconds=60)).isoformat(),
        }
        self.previews[preview["preview_id"]] = preview
        self.task_states[task_id] = "action_proposed"
        self.memory.append(task_id, {"type": "action_preview", "preview_id": preview["preview_id"]})
        return preview

    def confirm(
        self, preview_id: str, principal: Principal,
        now: datetime | None = None,
    ) -> str:
        preview = self.previews.get(preview_id)
        if not preview or principal.role != "incident_commander":
            raise PermissionError("confirmation requires the incident commander")
        now = now or datetime.now(timezone.utc)
        if now >= datetime.fromisoformat(preview["expires_at"]):
            raise ValueError("preview expired")
        payload = f"{principal.user_id}:{preview['tool']}:{preview['params_hash']}:{preview['task_id']}:{now.isoformat()}"
        token = hashlib.sha256(payload.encode()).hexdigest()
        self.tokens[token] = {
            "preview_id": preview_id,
            "user_id": principal.user_id,
            "tenant": principal.tenant,
            "expires_at": preview["expires_at"],
        }
        self.task_states[preview["task_id"]] = "approved"
        self.memory.append(preview["task_id"], {"type": "confirmed", "preview_id": preview_id})
        return token

    def execute_replay(
        self, token: str, idempotency_key: str, principal: Principal,
        now: datetime | None = None,
    ) -> dict:
        if idempotency_key in self.receipts:
            return self.receipts[idempotency_key]
        grant = self.tokens.get(token)
        if not grant or grant["user_id"] != principal.user_id or grant["tenant"] != principal.tenant:
            raise PermissionError("invalid confirmation token")
        now = now or datetime.now(timezone.utc)
        if now >= datetime.fromisoformat(grant["expires_at"]):
            raise ValueError("confirmation token expired")
        preview = self.previews[grant["preview_id"]]
        status = self.get_status(preview["target_queue"], principal)
        if not status or status["queue_depth"] != preview["queue_depth"]:
            raise ValueError("queue state changed; prepare and confirm again")
        self.task_states[preview["task_id"]] = "executing"
        self.runtime[preview["target_queue"]]["queue_depth"] -= preview["message_count"]
        self.execution_count += 1
        receipt = {
            "receipt_id": f"receipt:{idempotency_key}",
            "task_id": preview["task_id"],
            "target_queue": preview["target_queue"],
            "replayed": preview["message_count"],
            "before_queue_depth": preview["queue_depth"],
            "baseline_error_rate": status["provider_error_rate"],
        }
        self.receipts[idempotency_key] = receipt
        self.task_states[preview["task_id"]] = "verifying"
        self.memory.append(preview["task_id"], {"type": "executed", "receipt_id": receipt["receipt_id"]})
        return receipt

    def verify_replay(self, receipt: dict, principal: Principal) -> dict:
        status = self.get_status(receipt["target_queue"], principal)
        if status is None:
            raise PermissionError("queue is not visible to this principal")
        verified = (
            status["queue_depth"] < receipt["before_queue_depth"]
            and status["provider_error_rate"] <= receipt["baseline_error_rate"]
        )
        result = {"receipt_id": receipt["receipt_id"], "verified": verified, "observation": status}
        self.task_states[receipt["task_id"]] = "resolved" if verified else "needs_human"
        self.memory.append(receipt["task_id"], {"type": "verified", "result": verified})
        return result

    def context(
        self, question: str, principal: Principal, task_id: str,
        graph_seed: str | None = None, runtime_resource: str | None = None,
        disabled_channels: set[str] | None = None,
    ) -> dict:
        disabled_channels = disabled_channels or set()
        evidence = self.search(question, principal, disabled_channels=disabled_channels)
        relations = self.trace(graph_seed, principal) if graph_seed else []
        observation = self.get_status(runtime_resource, principal) if runtime_resource else None
        missing = []
        if runtime_resource and observation is None:
            missing.append(runtime_resource)
        return {
            "trace_id": f"ctx:{task_id}:{len(self.memory.read(task_id)) + 1}",
            "manifest": self.manifest,
            "principal": {"user_id": principal.user_id, "role": principal.role, "tenant": principal.tenant},
            "task_id": task_id,
            "evidence": evidence,
            "relations": relations,
            "observations": [observation] if observation else [],
            "memories": self.memory.read(task_id),
            "missing": missing,
            "degraded_channels": sorted(disabled_channels),
            "allowed_tools": self.allowed_tools(principal, task_id),
            "task_state": self.task_states[task_id],
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", default="")
    parser.add_argument("--role", default="developer")
    parser.add_argument("--task", default="demo")
    parser.add_argument("--graph-seed")
    parser.add_argument("--runtime-resource")
    parser.add_argument("--architecture-consistency", action="store_true")
    args = parser.parse_args()
    platform = NorthstarPlatform()
    principal = Principal("demo-user", args.role)
    if args.architecture_consistency:
        result = platform.architecture_consistency(principal)
    else:
        result = platform.context(
            args.question, principal, args.task,
            graph_seed=args.graph_seed, runtime_resource=args.runtime_resource,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
