#!/usr/bin/env python3
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"


def fail(message):
    raise SystemExit(f"CHRONOLOGY AUDIT FAILED: {message}")


def parse_event_date(record):
    value = record.get("eventDate")
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail(f"{record.get('id', '<unknown>')}: eventDate is not ISO YYYY-MM-DD")


with EVENTS_PATH.open(encoding="utf-8") as handle:
    events = json.load(handle).get("events", [])

if not events:
    fail("canonical event list is empty")

ids = [record.get("id") for record in events]
if any(not record_id for record_id in ids):
    fail("every canonical record must have an id")
if len(ids) != len(set(ids)):
    fail("canonical record ids must be unique")

living_edges = [record for record in events if record.get("recordType") == "living_edge"]
if len(living_edges) != 1 or living_edges[0].get("id") != "now":
    fail("exactly one living edge with id 'now' is required")
if events[-1].get("id") != "now":
    fail("NOW must remain the final canonical array entry")

recorded = [record for record in events if record.get("recordType") != "living_edge"]
recorded_dates = []
for record in recorded:
    parsed = parse_event_date(record)
    if parsed is None:
        fail(f"{record.get('id')}: recorded canonical records require eventDate")
    recorded_dates.append(parsed)

for previous, current in zip(recorded, recorded[1:]):
    previous_date = parse_event_date(previous)
    current_date = parse_event_date(current)
    if current_date < previous_date:
        fail(
            f"canonical array is out of order: {current.get('id')} ({current_date}) "
            f"precedes {previous.get('id')} ({previous_date})"
        )

by_id = {record["id"]: record for record in events}
for record in recorded:
    source_date = parse_event_date(record)
    for relationship in record.get("relationships", []):
        if relationship.get("type") != "chronological":
            continue
        target_id = relationship.get("targetId")
        target = by_id.get(target_id)
        if target is None:
            fail(f"{record['id']}: chronological target {target_id!r} does not exist")
        if target.get("recordType") == "living_edge":
            fail(f"{record['id']}: use navigation, not chronological, for NOW")
        target_date = parse_event_date(target)
        if target_date == source_date:
            fail(
                f"{record['id']}: chronological relationship to {target_id} has the same eventDate; "
                "use a more precise date or a non-chronological relationship type"
            )

for previous, current in zip(recorded, recorded[1:]):
    previous_to_current = any(
        rel.get("type") == "chronological" and rel.get("targetId") == current["id"]
        for rel in previous.get("relationships", [])
    )
    current_to_previous = any(
        rel.get("type") == "chronological" and rel.get("targetId") == previous["id"]
        for rel in current.get("relationships", [])
    )
    if not (previous_to_current and current_to_previous):
        fail(
            f"adjacent records {previous['id']} and {current['id']} must remain bidirectionally "
            "traversable by chronological relationships"
        )

print(
    f"OK: canonical chronology ordered and bidirectionally traversable across "
    f"{len(recorded)} dated records plus NOW"
)
