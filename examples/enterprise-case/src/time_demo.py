#!/usr/bin/env python3
"""Show C2 business-time and observation-time selection with a fixed fixture."""

from __future__ import annotations

import json

from northstar import NorthstarPlatform, Principal


def main() -> None:
    platform = NorthstarPlatform()
    support = Principal("support-demo", "support")
    checks = {
        "before_policy_change": {
            "valid_at": "2026-07-20T00:00:00Z",
            "observed_at": "2026-08-27T00:00:00Z",
        },
        "after_policy_change": {
            "valid_at": "2026-08-15T00:00:00Z",
            "observed_at": "2026-08-27T00:00:00Z",
        },
        "not_yet_ingested": {
            "valid_at": "2026-07-20T00:00:00Z",
            "observed_at": "2026-08-26T23:59:59Z",
        },
    }
    result = {
        label: [
            document["id"]
            for document in platform.documents_as_of(support, kinds={"policy"}, **window)
        ]
        for label, window in checks.items()
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
