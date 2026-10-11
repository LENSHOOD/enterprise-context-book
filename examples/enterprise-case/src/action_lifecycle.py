"""Controlled action lifecycle used by NorthstarPlatform; no web persistence."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
import secrets
from task_state import Principal

READ_TOOLS = {
    "support": ["search_context", "get_evidence"],
    "developer": ["search_context", "get_evidence", "trace_dependency"],
    "sre": ["search_context", "get_evidence", "trace_dependency", "get_current_status"],
    "incident_commander": ["get_current_status"],
}
DIAGNOSIS_ROLE = "sre"
APPROVER_ROLE = "incident_commander"

class ActionLifecycle:
    @staticmethod
    def _task_key(task_id: str, principal: Principal) -> tuple[str, str]:
        return principal.tenant, task_id

    def task_state(self, task_id: str, principal: Principal) -> str:
        if not self._is_task_operator(task_id, principal):
            return "opened"
        return self.task_states.get(self._task_key(task_id, principal), "opened")

    def _record_event(self, task_id: str, principal: Principal, event: dict) -> None:
        # Only called after the action method's authorization/state gates. Approval
        # events belong to the operator's memory, without granting the IC access.
        operator = Principal(**self.task_operators[self._task_key(task_id, principal)])
        self.memory.append(task_id, {**event, "actor": principal.user_id}, operator)

    def begin_diagnosis(self, task_id: str, principal: Principal) -> str:
        """Bind an incident to the SRE responsible for diagnosis and execution."""
        if principal.role != DIAGNOSIS_ROLE:
            raise PermissionError("diagnosis requires the SRE role")
        key = self._task_key(task_id, principal)
        if key in self.task_states:
            raise ValueError("task has already started")
        self.task_states[key] = "diagnosing"
        self.task_operators[key] = {
            "user_id": principal.user_id,
            "role": principal.role,
            "tenant": principal.tenant,
        }
        self.memory.register(task_id, principal)
        self._record_event(task_id, principal, {"type": "diagnosis_started"})
        return self.task_states[key]

    def _is_task_operator(self, task_id: str, principal: Principal) -> bool:
        return self.task_operators.get(self._task_key(task_id, principal)) == {
            "user_id": principal.user_id,
            "role": principal.role,
            "tenant": principal.tenant,
        }

    def allowed_tools(self, principal: Principal, task_id: str) -> list[str]:
        tools = list(READ_TOOLS.get(principal.role, []))
        state = self.task_states.get(self._task_key(task_id, principal), "opened")
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
        key = self._task_key(task_id, principal)
        if self.task_states[key] != "diagnosing":
            raise ValueError("replay preview requires an active diagnosis")
        now = now or self.clock()
        status = self.get_status(queue, principal, now)
        if status is None:
            raise PermissionError("queue is not visible to this principal")
        params = {
            "task_id": task_id,
            "tool": "replay_dead_letters",
            "target_queue": queue,
            "tenant_scope": principal.tenant,
            "message_count": min(status["queue_depth"], 100),
            "queue_depth": status["queue_depth"],
            "prepared_by": deepcopy(self.task_operators[key]),
            "observation_revision": status["revision"],
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
        self.task_states[key] = "action_proposed"
        self._record_event(task_id, principal, {"type": "action_preview", "preview_id": preview["preview_id"]})
        return deepcopy(preview)

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
        key = self._task_key(preview["task_id"], principal)
        if self.task_states[key] != "action_proposed":
            raise ValueError("confirmation requires a proposed action")
        now = now or self.clock()
        if now >= datetime.fromisoformat(preview["expires_at"]):
            raise ValueError("preview expired")
        token = secrets.token_hex(32)
        self.tokens[token] = {
            "preview_id": preview_id,
            "approved_by": principal.user_id,
            "tenant": principal.tenant,
            "executor": preview["prepared_by"],
            "expires_at": preview["expires_at"],
        }
        self.task_states[key] = "approved"
        self._record_event(preview["task_id"], principal, {"type": "confirmed", "preview_id": preview_id})
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
        key = self._task_key(preview["task_id"], principal)
        if self.task_states[key] != "action_proposed":
            raise ValueError("rejection requires a proposed action")
        self.task_states[key] = "needs_human"
        self._record_event(preview["task_id"], principal, {"type": "rejected", "preview_id": preview_id})

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
        now = now or self.clock()
        if now >= datetime.fromisoformat(grant["expires_at"]):
            raise ValueError("confirmation token expired")
        # A valid executor may safely retry a completed request, but no caller sees
        # a cached receipt until the token, expiry, and executor binding are checked.
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("idempotency key is required")
        existing = self._receipts.get((principal.tenant, idempotency_key))
        if existing:
            if (
                existing["task_id"] != preview["task_id"]
                or existing["target_queue"] != preview["target_queue"]
                or existing["tenant"] != principal.tenant
            ):
                raise ValueError("idempotency key conflicts with another action")
            return deepcopy(existing)
        key = self._task_key(preview["task_id"], principal)
        if self.task_states[key] != "approved":
            raise ValueError("task is not approved for execution")
        status = self.get_status(preview["target_queue"], principal, now)
        if not status or status["queue_depth"] != preview["queue_depth"] or status["revision"] != preview["observation_revision"]:
            raise ValueError("queue state changed; prepare and confirm again")
        self.task_states[key] = "executing"
        self.runtime[preview["target_queue"]]["queue_depth"] -= preview["message_count"]
        self.runtime[preview["target_queue"]]["revision"] += 1
        self.runtime[preview["target_queue"]]["observed_at"] = now.isoformat()
        self.execution_count += 1
        receipt = {
            "receipt_id": f"receipt:{secrets.token_hex(16)}",
            "task_id": preview["task_id"],
            "target_queue": preview["target_queue"],
            "replayed": preview["message_count"],
            "before_queue_depth": preview["queue_depth"],
            "baseline_error_rate": status["provider_error_rate"],
            "executed_by": principal.user_id,
            "tenant": principal.tenant,
            "before_observation_revision": status["revision"],
            "executed_at": now.isoformat(),
        }
        self._receipts[(principal.tenant, idempotency_key)] = receipt
        self._receipts_by_id[receipt["receipt_id"]] = receipt
        self.task_states[key] = "verifying"
        self._record_event(preview["task_id"], principal, {"type": "executed", "receipt_id": receipt["receipt_id"]})
        return deepcopy(receipt)

    def verify_replay(self, receipt: dict | str, principal: Principal) -> dict:
        receipt_id = receipt if isinstance(receipt, str) else receipt.get("receipt_id")
        saved = self._receipts_by_id.get(receipt_id)
        if not saved or (isinstance(receipt, dict) and receipt != saved) or saved["tenant"] != principal.tenant:
            raise PermissionError("unknown or modified receipt")
        receipt = saved
        if not self._is_task_operator(receipt["task_id"], principal):
            raise PermissionError("verification requires the assigned SRE")
        key = self._task_key(receipt["task_id"], principal)
        if self.task_states[key] != "verifying":
            raise ValueError("verification requires verifying state")
        status = self.get_status(receipt["target_queue"], principal)
        if status is None:
            raise PermissionError("queue is not visible to this principal")
        verified = (
            status["queue_depth"] < receipt["before_queue_depth"]
            and status["provider_error_rate"] <= receipt["baseline_error_rate"]
            and status["revision"] > receipt["before_observation_revision"]
            and self._parse_instant(status["observed_at"]) >= self._parse_instant(receipt["executed_at"])
        )
        result = {"receipt_id": receipt["receipt_id"], "verified": verified, "observation": status}
        self.task_states[key] = "resolved" if verified else "needs_human"
        self._record_event(receipt["task_id"], principal, {"type": "verified", "result": verified})
        return result
