#!/usr/bin/env python3
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates"
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def fail(message):
    raise SystemExit(f"SOURCE TEMPORAL AUDIT FAILED: {message}")


def valid_iso_day(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


files = sorted(CANDIDATES.glob("*.json"))
if not files:
    fail("data/candidates must contain at least one candidate record")

source_count = 0
for path in files:
    with path.open("r", encoding="utf-8") as handle:
        record = json.load(handle)

    rid = record.get("id", path.stem)
    sources = record.get("sources")
    if not isinstance(sources, list) or not sources:
        fail(f"{rid}: verified candidate requires a non-empty sources list")

    candidate_precision = record.get("datePrecision")
    candidate_month = record.get("publicationMonth")

    for index, source in enumerate(sources, start=1):
        source_count += 1
        if not isinstance(source, dict):
            fail(f"{rid}: source #{index} must be an object")

        published_date = source.get("publishedDate")
        published_month = source.get("publishedMonth")

        if published_date is not None and not valid_iso_day(published_date):
            fail(f"{rid}: source #{index} publishedDate must be a real ISO YYYY-MM-DD date or null")

        if published_month is not None:
            if not isinstance(published_month, str) or not MONTH_RE.fullmatch(published_month):
                fail(f"{rid}: source #{index} publishedMonth must be YYYY-MM or null")
            if published_date is not None and published_month != published_date[:7]:
                fail(f"{rid}: source #{index} publishedMonth contradicts publishedDate")

        if (
            candidate_precision == "month"
            and source.get("primary") is True
            and source.get("sourceRole") == "claim-evidence"
            and published_month is not None
            and published_month != candidate_month
        ):
            fail(f"{rid}: primary claim-evidence publishedMonth contradicts candidate publicationMonth")

print(f"OK: temporal metadata validated across {source_count} candidate sources")
