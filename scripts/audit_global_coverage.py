#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"

REGIONS = (
    "Africa",
    "Asia",
    "Europe",
    "Latin America and the Caribbean",
    "Middle East",
    "North America",
    "Oceania",
)
MIN_DISTINCT_VERIFIED_REGIONS = 3


def fail(message):
    raise SystemExit(f"GLOBAL COVERAGE AUDIT FAILED: {message}")


with EVENTS_PATH.open(encoding="utf-8") as handle:
    records = json.load(handle).get("events", [])

verified = [
    record for record in records
    if record.get("recordType") == "event"
    and record.get("temporalState") == "recorded"
    and record.get("verification", {}).get("state") == "verified"
]

region_counts = Counter()
system_birth_counts = Counter()
country_counts = Counter()
records_without_geography = []

for record in verified:
    geography = record.get("geography")
    if not geography:
        records_without_geography.append(record.get("id", "<unknown>"))
        continue

    region = geography.get("region")
    country = geography.get("country")
    if region not in REGIONS:
        fail(f"{record.get('id')}: unsupported region {region!r}")

    region_counts[region] += 1
    if record.get("status") == "VERIFIED SYSTEM BIRTH":
        system_birth_counts[region] += 1
    if country:
        country_counts[country] += 1

covered_regions = {region for region, count in region_counts.items() if count}
if len(covered_regions) < MIN_DISTINCT_VERIFIED_REGIONS:
    fail(
        "verified geographic coverage regressed below "
        f"{MIN_DISTINCT_VERIFIED_REGIONS} distinct regions"
    )

print(
    f"OK: global coverage baseline protected across {len(verified)} verified recorded events; "
    f"{len(covered_regions)}/{len(REGIONS)} regions represented by source-backed geography"
)
for region in REGIONS:
    print(
        f"  {region}: {region_counts[region]} verified records; "
        f"{system_birth_counts[region]} verified system births"
    )

uncovered = [region for region in REGIONS if region_counts[region] == 0]
print("  uncovered regions: " + (", ".join(uncovered) if uncovered else "none"))
print(f"  source-backed countries represented: {len(country_counts)}")
print(f"  verified records still awaiting explicit geography annotation: {len(records_without_geography)}")
