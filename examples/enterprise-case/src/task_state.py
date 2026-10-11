"""Task identity and per-task memory, independent of platform adapters."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy

@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str
    tenant: str = "northstar"


@dataclass
class TaskMemory:
    events: dict[tuple[str, str], list[dict]] = field(default_factory=lambda: defaultdict(list))
    owners: dict[tuple[str, str], Principal] = field(default_factory=dict)

    def register(self, task_id: str, principal: Principal) -> None:
        key = (principal.tenant, task_id)
        if key in self.owners:
            raise ValueError("task already registered")
        self.owners[key] = principal

    def append(self, task_id: str, event: dict, principal: Principal) -> dict:
        key = (principal.tenant, task_id)
        if self.owners.get(key) != principal:
            raise PermissionError("task memory requires membership")
        record = {**deepcopy(event), "sequence": len(self.events[key]) + 1}
        self.events[key].append(record)
        return deepcopy(record)

    def read(self, task_id: str, principal: Principal) -> list[dict]:
        key = (principal.tenant, task_id)
        if self.owners.get(key) != principal:
            return []
        return deepcopy(self.events.get(key, []))
