#!/usr/bin/env python3
"""Runnable Northstar context platform using only the Python standard library.

The implementation is deliberately small, but its contracts mirror the book:
ACL-before-retrieval, immutable citations, lexical/semantic fusion, evidence-backed
knowledge-model validation, graph traversal, generated Wiki pages, task memory,
and a structured Context API.

``context_demo.py`` deliberately repeats the minimal BM25 scorer to remain a
single-file chapter example. Keep its ranking behavior aligned with this teaching
platform; a production package should share one retrieval implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).parents[1]
SRC = Path(__file__).parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from knowledge_views import build_role_scoped_wiki, compare_architecture_claims, trace_dependency
from modeling import compile_domain_model, semantic_slice, validate_knowledge_base
from retrieval import bm25, reciprocal_rank_fusion, semantic_proxy

READ_TOOLS = {
    "support": ["search_context", "get_evidence"],
    "developer": ["search_context", "get_evidence", "trace_dependency"],
    "sre": ["search_context", "get_evidence", "trace_dependency", "get_current_status"],
    "incident_commander": ["get_current_status"],
}
DIAGNOSIS_ROLE = "sre"
APPROVER_ROLE = "incident_commander"


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
        self.domain_model = compile_domain_model(data_dir / "modeling")
        self.model_validation = validate_knowledge_base(
            self.domain_model, self.documents, self.edges
        )
        self.by_id = {doc["id"]: doc for doc in self.documents}
        self.memory = TaskMemory()
        canonical = json.dumps(
            {
                "documents": self.documents,
                "edges": self.edges,
                "architecture_claims": self.architecture_claims,
                "domain_model": self.domain_model,
            },
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode()
        self.manifest = f"northstar-{hashlib.sha256(canonical).hexdigest()[:12]}"
        self.task_states: dict[str, str] = defaultdict(lambda: "opened")
        self.task_operators: dict[str, dict] = {}
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
        return bm25(question, documents)

    @staticmethod
    def _semantic(question: str, documents: list[dict]) -> list[tuple[str, float]]:
        return semantic_proxy(question, documents)

    def search(
        self, question: str, principal: Principal, limit: int = 5,
        kinds: set[str] | None = None, disabled_channels: set[str] | None = None,
    ) -> list[dict]:
        # Security invariant: unauthorized objects never enter either scorer.
        visible = self.visible_documents(principal, kinds)
        disabled_channels = disabled_channels or set()
        lexical = [] if "bm25" in disabled_channels else self._bm25(question, visible)
        semantic = [] if "semantic_proxy" in disabled_channels else self._semantic(question, visible)
        rankings = {"bm25": lexical, "semantic_proxy": semantic}
        ranked = reciprocal_rank_fusion(rankings, limit)
        return [self._hit(self.by_id[doc_id], score, channels) for doc_id, score, channels in ranked]

    @staticmethod
    def _hit(doc: dict, score: float, channels: list[str]) -> dict:
        return {
            "id": doc["id"], "kind": doc["kind"], "title": doc["title"],
            "version": doc["version"], "citation": doc["citation"],
            "evidence": doc["text"], "score": round(score, 6), "channels": channels,
            "authority": doc.get("authority", "informative"),
        }

    def competency_question(self, question_id: str) -> dict:
        question = next(
            (
                item for item in self.domain_model["competencyQuestions"]
                if item["id"] == question_id
            ),
            None,
        )
        if question is None:
            raise ValueError(f"unknown competency question {question_id}")
        return question

    def trace(
        self,
        start: str,
        principal: Principal,
        max_hops: int = 2,
        relation_types: set[str] | None = None,
        allow_inverse_navigation: bool = False,
    ) -> list[dict]:
        if relation_types is not None:
            unknown = relation_types - set(self.domain_model["relations"])
            if unknown:
                raise ValueError(f"unknown relation types {sorted(unknown)}")
        visible = {doc["id"] for doc in self.visible_documents(principal)}
        return trace_dependency(
            self.edges,
            visible,
            start,
            max_hops,
            allowed_relation_types=relation_types,
            allow_inverse_navigation=allow_inverse_navigation,
        )

    def architecture_consistency(self, principal: Principal) -> dict[str, list[dict]]:
        visible = {doc["id"] for doc in self.visible_documents(principal)}
        return compare_architecture_claims(self.architecture_claims, self.edges, visible)

    def build_wiki(self, principal: Principal) -> list[dict]:
        return build_role_scoped_wiki(self.visible_documents(principal), principal.role)

    def get_status(self, resource: str, principal: Principal) -> dict | None:
        status = self.runtime.get(resource)
        if not status or principal.role not in status["acl"] or principal.tenant != status["tenant"]:
            return None
        return {key: value for key, value in status.items() if key != "acl"}

    def begin_diagnosis(self, task_id: str, principal: Principal) -> str:
        """Bind an incident to the SRE responsible for diagnosis and execution."""
        if principal.role != DIAGNOSIS_ROLE:
            raise PermissionError("diagnosis requires the SRE role")
        if self.task_states[task_id] != "opened":
            raise ValueError("task has already started")
        self.task_states[task_id] = "diagnosing"
        self.task_operators[task_id] = {
            "user_id": principal.user_id,
            "role": principal.role,
            "tenant": principal.tenant,
        }
        self.memory.append(task_id, {"type": "diagnosis_started", "actor": principal.user_id})
        return self.task_states[task_id]

    def _is_task_operator(self, task_id: str, principal: Principal) -> bool:
        return self.task_operators.get(task_id) == {
            "user_id": principal.user_id,
            "role": principal.role,
            "tenant": principal.tenant,
        }

    def allowed_tools(self, principal: Principal, task_id: str) -> list[str]:
        tools = list(READ_TOOLS.get(principal.role, []))
        state = self.task_states[task_id]
        if principal.role == DIAGNOSIS_ROLE and self._is_task_operator(task_id, principal) and state == "diagnosing":
            tools.append("prepare_replay")
        has_visible_preview = any(
            preview["task_id"] == task_id and preview["tenant_scope"] == principal.tenant
            for preview in self.previews.values()
        )
        if principal.role == APPROVER_ROLE and state == "action_proposed" and has_visible_preview:
            tools.extend(["confirm_replay", "reject_replay"])
        if self._is_task_operator(task_id, principal) and state == "approved":
            tools.append("execute_replay")
        if self._is_task_operator(task_id, principal) and state == "verifying":
            tools.append("verify_replay")
        return tools

    def prepare_replay(
        self, task_id: str, queue: str, principal: Principal,
        now: datetime | None = None,
    ) -> dict:
        if principal.role != DIAGNOSIS_ROLE or not self._is_task_operator(task_id, principal):
            raise PermissionError("replay preview requires the assigned SRE")
        if self.task_states[task_id] != "diagnosing":
            raise ValueError("replay preview requires an active diagnosis")
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
            "prepared_by": self.task_operators[task_id],
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
        if (
            not preview
            or principal.role != APPROVER_ROLE
            or principal.tenant != preview["tenant_scope"]
        ):
            raise PermissionError("confirmation requires the incident commander")
        if self.task_states[preview["task_id"]] != "action_proposed":
            raise ValueError("confirmation requires a proposed action")
        now = now or datetime.now(timezone.utc)
        if now >= datetime.fromisoformat(preview["expires_at"]):
            raise ValueError("preview expired")
        payload = f"{principal.user_id}:{preview['tool']}:{preview['params_hash']}:{preview['task_id']}:{now.isoformat()}"
        token = hashlib.sha256(payload.encode()).hexdigest()
        self.tokens[token] = {
            "preview_id": preview_id,
            "approved_by": principal.user_id,
            "tenant": principal.tenant,
            "executor": preview["prepared_by"],
            "expires_at": preview["expires_at"],
        }
        self.task_states[preview["task_id"]] = "approved"
        self.memory.append(preview["task_id"], {"type": "confirmed", "preview_id": preview_id})
        return token

    def reject(self, preview_id: str, principal: Principal) -> None:
        """Record that the designated approver rejected this specific action preview."""
        preview = self.previews.get(preview_id)
        if (
            not preview
            or principal.role != APPROVER_ROLE
            or principal.tenant != preview["tenant_scope"]
        ):
            raise PermissionError("rejection requires the incident commander")
        if self.task_states[preview["task_id"]] != "action_proposed":
            raise ValueError("rejection requires a proposed action")
        self.task_states[preview["task_id"]] = "needs_human"
        self.memory.append(preview["task_id"], {"type": "rejected", "preview_id": preview_id})

    def execute_replay(
        self, token: str, idempotency_key: str, principal: Principal,
        now: datetime | None = None,
    ) -> dict:
        grant = self.tokens.get(token)
        if not grant or grant["tenant"] != principal.tenant or grant["executor"] != {
            "user_id": principal.user_id,
            "role": principal.role,
            "tenant": principal.tenant,
        }:
            raise PermissionError("invalid confirmation token")
        preview = self.previews[grant["preview_id"]]
        now = now or datetime.now(timezone.utc)
        if now >= datetime.fromisoformat(grant["expires_at"]):
            raise ValueError("confirmation token expired")
        # A valid executor may safely retry a completed request, but no caller sees
        # a cached receipt until the token, expiry, and executor binding are checked.
        existing = self.receipts.get(idempotency_key)
        if existing:
            if (
                existing["task_id"] != preview["task_id"]
                or existing["target_queue"] != preview["target_queue"]
                or existing["tenant"] != principal.tenant
            ):
                raise ValueError("idempotency key conflicts with another action")
            return existing
        if self.task_states[preview["task_id"]] != "approved":
            raise ValueError("task is not approved for execution")
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
            "executed_by": principal.user_id,
            "tenant": principal.tenant,
        }
        self.receipts[idempotency_key] = receipt
        self.task_states[preview["task_id"]] = "verifying"
        self.memory.append(preview["task_id"], {"type": "executed", "receipt_id": receipt["receipt_id"]})
        return receipt

    def verify_replay(self, receipt: dict, principal: Principal) -> dict:
        if not self._is_task_operator(receipt["task_id"], principal):
            raise PermissionError("verification requires the assigned SRE")
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
        competency_question_id: str | None = None,
    ) -> dict:
        disabled_channels = disabled_channels or set()
        evidence = self.search(question, principal, disabled_channels=disabled_channels)
        competency_question = (
            self.competency_question(competency_question_id)
            if competency_question_id else None
        )
        relation_types = (
            set(competency_question["requiredRelations"])
            if competency_question else None
        )
        relations = (
            self.trace(
                graph_seed,
                principal,
                relation_types=relation_types,
                allow_inverse_navigation=competency_question is not None,
            )
            if graph_seed else []
        )
        evidence_documents = [self.by_id[item["id"]] for item in evidence]
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
            "semantic_contract": semantic_slice(
                self.domain_model,
                evidence_documents,
                relations,
                competency_question=competency_question,
            ),
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
    parser.add_argument("--competency-question")
    parser.add_argument("--architecture-consistency", action="store_true")
    parser.add_argument("--wiki", action="store_true")
    args = parser.parse_args()
    platform = NorthstarPlatform()
    principal = Principal("demo-user", args.role)
    if args.architecture_consistency:
        result = platform.architecture_consistency(principal)
    elif args.wiki:
        result = platform.build_wiki(principal)
    else:
        result = platform.context(
            args.question, principal, args.task,
            graph_seed=args.graph_seed,
            runtime_resource=args.runtime_resource,
            competency_question_id=args.competency_question,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
