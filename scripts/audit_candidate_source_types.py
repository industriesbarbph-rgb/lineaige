#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CANDIDATES = DATA / "candidates"


def fail(message):
    raise SystemExit(f"CANDIDATE SOURCE-CONTRACT AUDIT FAILED: {message}")


with (DATA / "event.schema.json").open("r", encoding="utf-8") as handle:
    schema = json.load(handle)

source_type_schema = (
    schema.get("properties", {})
    .get("sources", {})
    .get("items", {})
    .get("properties", {})
    .get("sourceType", {})
)
canonical_source_types = set(source_type_schema.get("enum", []))
if not canonical_source_types:
    fail("canonical event schema must define sourceType enum values")

files = sorted(CANDIDATES.glob("*.json"))
if not files:
    fail("data/candidates must contain at least one candidate record")

source_count = 0
canonical_compatible = 0
admission_mismatches = []
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

        title = source.get("title")
        if not isinstance(title, str) or not title.strip():
            fail(f"{rid}: source #{index} requires a non-empty title")

        source_type = source.get("sourceType")
        if not isinstance(source_type, str) or not source_type.strip():
            fail(f"{rid}: source #{index} requires an explicit non-empty sourceType")

        if not isinstance(source.get("primary"), bool):
            fail(f"{rid}: source #{index} primary must be boolean")

        if source_type in canonical_source_types:
            canonical_compatible += 1
        else:
            admission_mismatches.append(f"{rid} source #{index}: {source_type}")

if admission_mismatches:
    print(
        "ADMISSION COMPATIBILITY NOTICE: "
        f"{len(admission_mismatches)} candidate source type(s) are not yet in the canonical event taxonomy; "
        "they must be reviewed/normalized deliberately before canonical admission:"
    )
    for mismatch in admission_mismatches:
        print(f"- {mismatch}")

print(
    f"OK: structural source contract validated across {source_count} candidate sources in {len(files)} records; "
    f"{canonical_compatible} source type(s) are already canonical-compatible"
)
