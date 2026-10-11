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
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).parents[1]
SRC = Path(__file__).parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from knowledge_views import build_role_scoped_wiki, compare_architecture_claims, trace_dependency
from resource_pipeline import compile_resources
from retrieval import bm25, reciprocal_rank_fusion, semantic_proxy
from strategy import StrategicContext
from context_flow import ContextFlow
from task_state import Principal, TaskMemory
from action_lifecycle import ActionLifecycle, READ_TOOLS, DIAGNOSIS_ROLE, APPROVER_ROLE

DEFAULT_FIXTURE_TIME = datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc)


class NorthstarPlatform(ActionLifecycle):
    def __init__(self, data_dir: Path = ROOT / "data", clock: Callable[[], datetime] | None = None) -> None:
        # Keep the local fixture deterministic. A production adapter must inject
        # a real clock and obtain observations from the live system.
        self.clock = clock or (lambda: DEFAULT_FIXTURE_TIME)
        self.resources = compile_resources(data_dir)
        self.documents = deepcopy(self.resources.documents)
        self.edges = deepcopy(self.resources.edges)
        self.architecture_claims = deepcopy(self.resources.claims)
        self.runtime = deepcopy(self.resources.runtime)
        # runtime.json supplies simulated sensor values, not a live source's old
        # timestamps. Sample once at startup; cached observations then expire.
        for status in self.runtime.values():
            status["observed_at"] = self.clock().isoformat()
            status["revision"] = 0
        self.domain_model = deepcopy(self.resources.model)
        self.model_validation = deepcopy(self.resources.model_validation)
        self.strategy_context = StrategicContext(resources=self.resources.strategy)
        self.by_id = {doc["id"]: doc for doc in self.documents}
        self.memory = TaskMemory()
        self.manifest = self.resources.manifest
        self.task_states: dict[tuple[str, str], str] = {}
        self.task_operators: dict[tuple[str, str], dict] = {}
        self.previews: dict[str, dict] = {}
        self.tokens: dict[str, dict] = {}
        self._receipts: dict[tuple[str, str], dict] = {}
        self._receipts_by_id: dict[str, dict] = {}
        self.execution_count = 0

    @staticmethod
    def allowed(doc: dict, principal: Principal) -> bool:
        return (doc.get("tenant") == principal.tenant
                and isinstance(doc.get("acl"), list) and principal.role in doc["acl"])

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
        valid_at: str | None = None, observed_at: str | None = None,
    ) -> list[dict]:
        # Security invariant: unauthorized objects never enter either scorer.
        visible = self.current_documents(principal, kinds, valid_at, observed_at)
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
            "time": deepcopy(doc["time"]),
        }

    def current_documents(self, principal: Principal, kinds: set[str] | None = None,
                          valid_at: str | None = None, observed_at: str | None = None) -> list[dict]:
        now = self.clock().isoformat()
        return self.documents_as_of(principal, valid_at or now, observed_at or now, kinds)

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
        valid_at: str | None = None,
        observed_at: str | None = None,
    ) -> list[dict]:
        if relation_types is not None:
            unknown = relation_types - set(self.domain_model["relations"])
            if unknown:
                raise ValueError(f"unknown relation types {sorted(unknown)}")
        visible = {doc["id"] for doc in self.current_documents(principal, valid_at=valid_at, observed_at=observed_at)}
        instant = self._parse_instant(valid_at or self.clock().isoformat())
        known = self._parse_instant(observed_at or self.clock().isoformat())
        edges = [edge for edge in self.edges if self._valid_at(edge.get("time", {}), instant, known)]
        return trace_dependency(
            edges,
            visible,
            start,
            max_hops,
            allowed_relation_types=relation_types,
            allow_inverse_navigation=allow_inverse_navigation,
        )

    def architecture_consistency(self, principal: Principal) -> dict[str, list[dict]]:
        # Compare the explicitly authored architecture snapshot. Current online
        # search/trace filtering is separate from this fixed-snapshot audit.
        visible = {doc["id"] for doc in self.visible_documents(principal)}
        return compare_architecture_claims(self.architecture_claims, self.edges, visible)

    def build_wiki(self, principal: Principal, valid_at: str | None = None,
                   observed_at: str | None = None) -> list[dict]:
        return build_role_scoped_wiki(self.current_documents(principal, valid_at=valid_at, observed_at=observed_at), principal.role)

    def _valid_at(self, envelope: dict, instant: datetime, known: datetime) -> bool:
        return (not envelope or (
            self._parse_instant(envelope["valid_from"]) <= instant
            and (not envelope.get("valid_to") or instant < self._parse_instant(envelope["valid_to"]))
            and self._parse_instant(envelope["observed_at"]) <= known))

    def get_status(self, resource: str, principal: Principal, now: datetime | None = None) -> dict | None:
        status = self.runtime.get(resource)
        if not status or principal.role not in status["acl"] or principal.tenant != status["tenant"]:
            return None
        now = now or self.clock()
        observed = self._parse_instant(status["observed_at"])
        age = (now - observed).total_seconds()
        if not 0 <= age < status["ttl_seconds"]:
            return None
        return deepcopy({key: value for key, value in status.items() if key != "acl"})

    def context(
        self, question: str, principal: Principal, task_id: str,
        graph_seed: str | None = None, runtime_resource: str | None = None,
        disabled_channels: set[str] | None = None,
        competency_question_id: str | None = None,
        valid_at: str | None = None, observed_at: str | None = None,
        mode: str = "operational",
        definition_confirmation: dict | None = None,
    ) -> dict:
        return ContextFlow(self).run(question, principal, task_id, mode=mode,
            graph_seed=graph_seed, runtime_resource=runtime_resource,
            disabled_channels=disabled_channels, competency_question_id=competency_question_id,
            valid_at=valid_at, observed_at=observed_at, definition_confirmation=definition_confirmation)

    def strategic_context(
        self, question: str, principal: Principal, task_id: str = "strategy-review",
        *, confirmation: dict | None = None,
    ) -> dict:
        """Compatibility entry; strategic requests use the common context flow."""
        return self.context(question, principal, task_id, mode="strategic",
                            definition_confirmation=confirmation)


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
    parser.add_argument("--valid-at", help="business effective time (ISO 8601, timezone required)")
    parser.add_argument("--observed-at", help="knowledge observation cutoff (ISO 8601, timezone required)")
    parser.add_argument("--mode", choices=["operational", "strategic"], default="operational")
    parser.add_argument("--confirm-definition", action="store_true", help="accept the displayed C7 fixture comparison contract")
    args = parser.parse_args()
    platform = NorthstarPlatform()
    principal = Principal("demo-user", args.role)
    if args.architecture_consistency:
        result = platform.architecture_consistency(principal)
    elif args.wiki:
        result = platform.build_wiki(principal, args.valid_at, args.observed_at)
    else:
        result = platform.context(
            args.question, principal, args.task,
            graph_seed=args.graph_seed,
            runtime_resource=args.runtime_resource,
            competency_question_id=args.competency_question,
            valid_at=args.valid_at, observed_at=args.observed_at,
            mode=args.mode,
            definition_confirmation=(platform.strategy_context.definition_confirmation()
                                     if args.confirm_definition else None),
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
