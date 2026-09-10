#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CANDIDATES = DATA / "candidates"


def fail(message):
    raise SystemExit(f"CANDIDATE SOURCE-TYPE AUDIT FAILED: {message}")


with (DATA / "event.schema.json").open("r", encoding="utf-8") as handle:
    schema = json.load(handle)

source_type_schema = (
    schema.get("properties", {})
    .get("sources", {})
    .get("items", {})
    .get("properties", {})
    .get("sourceType", {})
)
allowed_source_types = set(source_type_schema.get("enum", []))
if not allowed_source_types:
    fail("canonical event schema must define sourceType enum values")

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

    for index, source in enumerate(sources, start=1):
        source_count += 1
        if not isinstance(source, dict):
            fail(f"{rid}: source #{index} must be an object")
        source_type = source.get("sourceType")
        if source_type not in allowed_source_types:
            allowed = ", ".join(sorted(allowed_source_types))
            fail(
                f"{rid}: source #{index} sourceType {source_type!r} is not canonical-compatible; "
                f"allowed values: {allowed}"
            )

print(
    f"OK: {source_count} candidate sources use canonical-compatible sourceType values "
    f"across {len(files)} candidate records"
)
