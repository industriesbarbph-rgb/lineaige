#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SOURCE_ROLES = {"claim-evidence", "corroboration", "archive-copy", "context", "relationship-evidence"}
REGIONS = {"Africa", "Asia", "Europe", "Latin America and the Caribbean", "Middle East", "North America", "Oceania"}
GEO_CONTEXTS = {"organization-base", "research-location", "announcement-location", "deployment-location", "multi-region"}


def fail(message):
    raise SystemExit(f"EVIDENCE CONTEXT AUDIT FAILED: {message}")


def is_http_url(value):
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


with (DATA / "event.schema.json").open(encoding="utf-8") as handle:
    schema = json.load(handle)
with (DATA / "events.json").open(encoding="utf-8") as handle:
    events = json.load(handle).get("events", [])

properties = schema.get("properties", {})
if "geography" not in properties:
    fail("event schema must expose geography context")
source_role = properties.get("sources", {}).get("items", {}).get("properties", {}).get("sourceRole", {})
if set(value for value in source_role.get("enum", []) if value is not None) != SOURCE_ROLES:
    fail("event schema sourceRole taxonomy does not match production audit")

geo_records = 0
role_tagged_sources = 0

for record in events:
    record_id = record.get("id", "<unknown>")
    sources = record.get("sources", [])
    source_urls = []

    for source in sources:
        url = source.get("url")
        if not is_http_url(url) or not url:
            fail(f"{record_id}: every canonical source requires an http(s) URL")
        if url in source_urls:
            fail(f"{record_id}: duplicate canonical source URL {url}")
        source_urls.append(url)

        role = source.get("sourceRole")
        if role is not None:
            role_tagged_sources += 1
            if role not in SOURCE_ROLES:
                fail(f"{record_id}: invalid sourceRole {role}")
        if role == "claim-evidence" and not source.get("primary"):
            fail(f"{record_id}: claim-evidence source must be marked primary")

    geography = record.get("geography")
    if geography is not None:
        geo_records += 1
        if not isinstance(geography, dict):
            fail(f"{record_id}: geography must be object or null")
        region = geography.get("region")
        context = geography.get("context")
        geo_source_url = geography.get("sourceUrl")
        if region is not None and region not in REGIONS:
            fail(f"{record_id}: invalid geography.region")
        if context is not None and context not in GEO_CONTEXTS:
            fail(f"{record_id}: invalid geography.context")
        if not is_http_url(geo_source_url):
            fail(f"{record_id}: geography.sourceUrl must be http(s) URL or null")
        if any(geography.get(key) for key in ("country", "region", "context")) and not geo_source_url:
            fail(f"{record_id}: geographic factual context requires a sourceUrl")
        if geo_source_url and geo_source_url not in source_urls:
            fail(f"{record_id}: geography.sourceUrl must also appear in canonical sources")
        if geo_source_url:
            matching = [source for source in sources if source.get("url") == geo_source_url]
            if not matching or not any(source.get("primary") for source in matching):
                fail(f"{record_id}: geography source must be represented by a primary canonical source")
            if not any(source.get("sourceRole") in {"claim-evidence", "corroboration"} for source in matching):
                fail(f"{record_id}: geography source must declare claim-evidence or corroboration role")

print(
    "OK: evidence-role/geography schema protected across "
    f"{len(events)} canonical records; {geo_records} geography records and "
    f"{role_tagged_sources} role-tagged sources provenance-checked"
)
