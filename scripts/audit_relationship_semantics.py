#!/usr/bin/env python3
"""Protect LINEAiGE relationship semantics from accidental causal overclaiming."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"

CAUSAL_TYPES = {"ancestor", "descendant", "influenced", "enabled"}
NON_CAUSAL_TYPES = {"chronological", "navigation"}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    data = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = data.get("events", [])
    errors: list[str] = []

    ids = {event.get("id") for event in events}

    for event in events:
        event_id = event.get("id", "<missing-id>")
        for index, rel in enumerate(event.get("relationships", [])):
            prefix = f"{event_id}.relationships[{index}]"
            rel_type = rel.get("type")
            state = rel.get("evidenceState")
            note = (rel.get("evidenceNote") or "").lower()
            sources = rel.get("sourceUrls") or []
            target = rel.get("targetId")

            if target is not None and target not in ids:
                fail(f"{prefix}: unresolved targetId {target!r}", errors)

            if rel_type == "chronological":
                if state != "contextual":
                    fail(f"{prefix}: chronological links must use evidenceState='contextual'", errors)
                if sources:
                    fail(f"{prefix}: chronological links must not carry causal-looking sourceUrls", errors)
                if "chronolog" not in note and "causal" not in note and "influence" not in note:
                    fail(f"{prefix}: chronological link needs an explicit non-causal evidenceNote", errors)

            if rel_type == "navigation":
                if state != "navigation-only":
                    fail(f"{prefix}: navigation links must use evidenceState='navigation-only'", errors)
                if sources:
                    fail(f"{prefix}: navigation links must not carry evidentiary sourceUrls", errors)

            if rel_type in CAUSAL_TYPES:
                if state == "navigation-only":
                    fail(f"{prefix}: causal relationship types cannot be navigation-only", errors)
                if state == "verified" and not sources:
                    fail(f"{prefix}: verified {rel_type} relationship requires sourceUrls", errors)
                if state == "verified" and not rel.get("evidenceNote"):
                    fail(f"{prefix}: verified {rel_type} relationship requires an evidenceNote", errors)

            if rel_type in NON_CAUSAL_TYPES and state == "verified":
                fail(f"{prefix}: {rel_type} links cannot be promoted to verified causal evidence", errors)

    if errors:
        print("Relationship semantics audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Relationship semantics audit passed for {len(events)} canonical records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
