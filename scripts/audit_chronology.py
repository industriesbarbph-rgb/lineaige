#!/usr/bin/env python3
import calendar
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"
MONTH_RE = re.compile(r"^([0-9]{4})-(0[1-9]|1[0-2])$")
YEAR_RE = re.compile(r"^[0-9]{4}$")


def fail(message):
    raise SystemExit(f"CHRONOLOGY AUDIT FAILED: {message}")


def temporal_bounds(record):
    """Return inclusive (earliest, latest, precision) bounds without inventing precision."""
    record_id = record.get("id", "<unknown>")
    precision = record.get("datePrecision")
    event_date = record.get("eventDate")
    event_month = record.get("eventMonth")
    event_year = record.get("eventYear")

    # Backward-compatible migration behavior for the existing canonical corpus.
    if precision is None and event_date:
        precision = "day"

    if precision == "day":
        if not event_date:
            fail(f"{record_id}: day precision requires eventDate")
        try:
            parsed = date.fromisoformat(event_date)
        except ValueError:
            fail(f"{record_id}: eventDate is not ISO YYYY-MM-DD")
        if event_month is not None or event_year is not None:
            fail(f"{record_id}: day precision may not also set eventMonth/eventYear")
        return parsed, parsed, precision

    if precision == "month":
        if event_date is not None:
            fail(f"{record_id}: month precision may not carry synthetic eventDate")
        if not isinstance(event_month, str):
            fail(f"{record_id}: month precision requires eventMonth YYYY-MM")
        match = MONTH_RE.fullmatch(event_month)
        if not match:
            fail(f"{record_id}: eventMonth is not YYYY-MM")
        if event_year is not None:
            fail(f"{record_id}: month precision may not also set eventYear")
        year = int(match.group(1))
        month = int(match.group(2))
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day), precision

    if precision == "year":
        if event_date is not None or event_month is not None:
            fail(f"{record_id}: year precision may not carry synthetic eventDate/eventMonth")
        if not isinstance(event_year, str) or not YEAR_RE.fullmatch(event_year):
            fail(f"{record_id}: year precision requires eventYear YYYY")
        year = int(event_year)
        return date(year, 1, 1), date(year, 12, 31), precision

    if precision == "unknown":
        if event_date is not None or event_month is not None or event_year is not None:
            fail(f"{record_id}: unknown precision may not carry a synthetic temporal value")
        return None, None, precision

    fail(f"{record_id}: recorded canonical record requires an explicit or inferable date precision")


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
bounds_by_id = {}
for record in recorded:
    earliest, latest, precision = temporal_bounds(record)
    if earliest is None or latest is None:
        fail(f"{record.get('id')}: unknown date precision cannot participate in canonical recorded chronology")
    bounds_by_id[record["id"]] = (earliest, latest, precision)

# Canonical array order follows earliest possible date. Precision may create overlapping
# intervals; overlap is allowed in storage but cannot support an asserted chronological edge.
for previous, current in zip(recorded, recorded[1:]):
    previous_earliest, _, _ = bounds_by_id[previous["id"]]
    current_earliest, _, _ = bounds_by_id[current["id"]]
    if current_earliest < previous_earliest:
        fail(
            f"canonical array is out of order: {current.get('id')} ({current_earliest}) "
            f"precedes {previous.get('id')} ({previous_earliest})"
        )

by_id = {record["id"]: record for record in events}
for record in recorded:
    source_earliest, source_latest, _ = bounds_by_id[record["id"]]
    for relationship in record.get("relationships", []):
        if relationship.get("type") != "chronological":
            continue
        target_id = relationship.get("targetId")
        target = by_id.get(target_id)
        if target is None:
            fail(f"{record['id']}: chronological target {target_id!r} does not exist")
        if target.get("recordType") == "living_edge":
            fail(f"{record['id']}: use navigation, not chronological, for NOW")
        target_earliest, target_latest, _ = bounds_by_id[target_id]
        deterministically_ordered = source_latest < target_earliest or target_latest < source_earliest
        if not deterministically_ordered:
            fail(
                f"{record['id']}: chronological relationship to {target_id} is not deterministically "
                "ordered at the stored date precision; use greater verified precision or a contextual relationship"
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
    previous_earliest, previous_latest, _ = bounds_by_id[previous["id"]]
    current_earliest, current_latest, _ = bounds_by_id[current["id"]]
    deterministically_ordered = previous_latest < current_earliest or current_latest < previous_earliest
    if deterministically_ordered and not (previous_to_current and current_to_previous):
        fail(
            f"adjacent deterministically ordered records {previous['id']} and {current['id']} must remain "
            "bidirectionally traversable by chronological relationships"
        )

precision_counts = {"day": 0, "month": 0, "year": 0}
for _, _, precision in bounds_by_id.values():
    precision_counts[precision] += 1

print(
    f"OK: canonical chronology is precision-aware and ordered across {len(recorded)} recorded records plus NOW "
    f"(day={precision_counts['day']}, month={precision_counts['month']}, year={precision_counts['year']})"
)
