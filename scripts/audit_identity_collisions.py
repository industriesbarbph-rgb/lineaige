#!/usr/bin/env python3
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data" / "events.json"
CANDIDATES = ROOT / "data" / "candidates"
YEAR_RE = re.compile(r"^(\d{4})")


def fail(message):
    raise SystemExit(f"IDENTITY AUDIT FAILED: {message}")


def normalize_identity(value):
    return " ".join(value.split()).casefold()


def record_year(record):
    event_date = record.get("eventDate")
    if isinstance(event_date, str):
        match = YEAR_RE.match(event_date)
        if match:
            return int(match.group(1))
    publication_month = record.get("publicationMonth")
    if isinstance(publication_month, str):
        match = YEAR_RE.match(publication_month)
        if match:
            return int(match.group(1))
    event_year = record.get("eventYear")
    if isinstance(event_year, int):
        return event_year
    return None


def record_time_key(record):
    """Return the record's explicit timeline value without inventing precision."""
    event_date = record.get("eventDate")
    if isinstance(event_date, str) and event_date.strip():
        return ("eventDate", event_date.strip())
    publication_month = record.get("publicationMonth")
    if isinstance(publication_month, str) and publication_month.strip():
        return ("publicationMonth", publication_month.strip())
    event_year = record.get("eventYear")
    if isinstance(event_year, int):
        return ("eventYear", str(event_year))
    return None


with EVENTS.open("r", encoding="utf-8") as handle:
    canonical_payload = json.load(handle)

canonical_by_identity_year = defaultdict(set)
for record in canonical_payload.get("events", []):
    rid = record.get("id")
    year = record_year(record)
    if not isinstance(rid, str) or year is None:
        continue
    for technology in record.get("technologies", []):
        if isinstance(technology, str) and technology.strip():
            canonical_by_identity_year[(normalize_identity(technology), year)].add(rid)

canonical_collisions = []
candidate_by_identity_time = defaultdict(set)
for path in sorted(CANDIDATES.glob("*.json")):
    with path.open("r", encoding="utf-8") as handle:
        record = json.load(handle)
    rid = record.get("id")
    year = record_year(record)
    time_key = record_time_key(record)
    if not isinstance(rid, str):
        continue
    for technology in record.get("technologies", []):
        if not isinstance(technology, str) or not technology.strip():
            continue
        normalized = normalize_identity(technology)
        if year is not None:
            canonical_ids = sorted(canonical_by_identity_year.get((normalized, year), set()))
            if canonical_ids:
                canonical_collisions.append((rid, technology, year, canonical_ids))
        if time_key is not None:
            candidate_by_identity_time[(normalized, time_key)].add(rid)

if canonical_collisions:
    details = "; ".join(
        f"candidate {rid!r} technology {technology!r} in {year} exactly matches canonical {canonical_ids}"
        for rid, technology, year, canonical_ids in canonical_collisions
    )
    fail(
        "candidate/canonical technology identity collision(s): "
        + details
        + ". Review the records explicitly; do not bypass this gate with title changes or fuzzy aliases."
    )

candidate_collisions = [
    (identity, time_key, sorted(ids))
    for (identity, time_key), ids in candidate_by_identity_time.items()
    if len(ids) > 1
]
if candidate_collisions:
    details = "; ".join(
        f"technology {identity!r} at {time_key[0]}={time_key[1]!r} appears in candidates {ids}"
        for identity, time_key, ids in candidate_collisions
    )
    fail(
        "candidate/candidate same-time technology identity collision(s): "
        + details
        + ". Review whether these are duplicate candidate identities before retaining both."
    )

print("OK: no exact same-year candidate/canonical technology identity collisions")
print("OK: no same-time candidate/candidate technology identity collisions")
