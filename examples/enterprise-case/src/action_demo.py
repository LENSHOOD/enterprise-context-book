#!/usr/bin/env python3
"""Run the deterministic preview-confirm-execute-verify teaching flow."""

from datetime import datetime, timezone
import json

from northstar import NorthstarPlatform, Principal


def main() -> None:
    platform = NorthstarPlatform()
    sre = Principal("sre-oncall", "sre")
    commander = Principal("incident-commander", "incident_commander")
    now = datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc)
    platform.begin_diagnosis("INC-DEMO", sre)
    context = platform.context(
        "退款积压如何排查", sre, "INC-DEMO", runtime_resource="refund-queue"
    )
    preview = platform.prepare_replay("INC-DEMO", "refund-queue", sre, now)
    token = platform.confirm(preview["preview_id"], commander, now)
    receipt = platform.execute_replay(token, "demo-replay-1", sre, now)
    verification = platform.verify_replay(receipt, sre)
    print(json.dumps({
        "diagnostic_evidence": [item["id"] for item in context["evidence"]],
        "preview": preview,
        "confirmation_token": token[:12] + "…",
        "receipt": receipt,
        "verification": verification,
        "task_state": platform.task_states["INC-DEMO"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
