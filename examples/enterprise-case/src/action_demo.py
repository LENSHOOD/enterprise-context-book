#!/usr/bin/env python3
"""Run the deterministic preview-confirm-execute-verify teaching flow."""

from datetime import datetime, timezone
import json

from northstar import NorthstarPlatform, Principal


def main() -> None:
    platform = NorthstarPlatform()
    principal = Principal("incident-commander", "incident_commander")
    now = datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc)
    preview = platform.prepare_replay("INC-DEMO", "refund-queue", principal, now)
    token = platform.confirm(preview["preview_id"], principal, now)
    receipt = platform.execute_replay(token, "demo-replay-1", principal, now)
    verification = platform.verify_replay(receipt, principal)
    print(json.dumps({
        "preview": preview,
        "confirmation_token": token[:12] + "…",
        "receipt": receipt,
        "verification": verification,
        "task_state": platform.task_states["INC-DEMO"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
