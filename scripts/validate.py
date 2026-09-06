#!/usr/bin/env python3
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

RECORD_TYPES = {"event", "entry_point", "living_edge", "announced_future"}
TEMPORAL_STATES = {"recorded", "forming", "declared-unresolved"}
VERIFICATION_STATES = {"unreviewed", "developing", "verified", "disputed", "navigation-only"}
SOURCE_TYPES = {"paper", "official-announcement", "archive", "government-record", "book", "interview", "video", "news", "other"}
RELATIONSHIP_TYPES = {"ancestor", "descendant", "influenced", "enabled", "contextual", "chronological", "related", "source-path", "navigation"}
RELATIONSHIP_EVIDENCE = {"verified", "contextual", "disputed", "navigation-only"}
COURSE_PROVIDER_TYPES = {"university", "school", "online-platform", "technology-provider", "government", "nonprofit", "independent-provider", "other"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REQUIRED = {"id", "recordType", "title", "displayDate", "temporalState", "status", "summary", "verification", "sources", "relationships"}


def load_json(name):
    with (DATA / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_http_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def valid_date(value):
    if value is None:
        return True
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def valid_datetime(value):
    if value is None:
        return True
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (AttributeError, TypeError, ValueError):
        return False


def fail(message):
    raise SystemExit(f"VALIDATION FAILED: {message}")


def require_unique_id(item, seen, family):
    item_id = item.get("id") if isinstance(item, dict) else None
    if not isinstance(item_id, str) or not ID_RE.fullmatch(item_id):
        fail(f"{family}: invalid id {item_id!r}")
    if item_id in seen:
        fail(f"{family}: duplicate id {item_id}")
    seen.add(item_id)
    return item_id


events_doc = load_json("events.json")
media_doc = load_json("media.json")
courses_doc = load_json("courses.json")
schema_doc = load_json("event.schema.json")

if events_doc.get("schemaVersion") != "1.1.0":
    fail("data/events.json schemaVersion must be 1.1.0")
if media_doc.get("schemaVersion") != "1.0.0":
    fail("data/media.json schemaVersion must be 1.0.0")
if courses_doc.get("schemaVersion") != "1.0.0":
    fail("data/courses.json schemaVersion must be 1.0.0")
if schema_doc.get("additionalProperties") is not False:
    fail("event.schema.json must preserve additionalProperties=false")

events = events_doc.get("events")
if not isinstance(events, list) or not events:
    fail("data/events.json must contain a non-empty events array")

ids = []
for record in events:
    if not isinstance(record, dict):
        fail("every event must be an object")
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"{record.get('id', '<unknown>')}: missing required fields: {', '.join(missing)}")

    record_id = record["id"]
    if not isinstance(record_id, str) or not ID_RE.fullmatch(record_id):
        fail(f"invalid event id: {record_id!r}")
    if record_id in ids:
        fail(f"duplicate event id: {record_id}")
    ids.append(record_id)

    if record["recordType"] not in RECORD_TYPES:
        fail(f"{record_id}: invalid recordType")
    if record["temporalState"] not in TEMPORAL_STATES:
        fail(f"{record_id}: invalid temporalState")
    for field in ("title", "displayDate", "status", "summary"):
        if not isinstance(record[field], str) or not record[field].strip():
            fail(f"{record_id}: {field} must be a non-empty string")
    for field in ("eventDate", "endDate", "announcementDate", "targetDate"):
        if field in record and not valid_date(record[field]):
            fail(f"{record_id}: {field} must be an ISO date or null")

    verification = record["verification"]
    if not isinstance(verification, dict):
        fail(f"{record_id}: verification must be an object")
    if verification.get("state") not in VERIFICATION_STATES:
        fail(f"{record_id}: invalid verification state")
    if not isinstance(verification.get("factualClaim"), bool):
        fail(f"{record_id}: verification.factualClaim must be boolean")
    if "lastVerified" in verification and not valid_datetime(verification.get("lastVerified")):
        fail(f"{record_id}: verification.lastVerified must be ISO date-time or null")
    if record["recordType"] == "living_edge" and verification.get("factualClaim"):
        fail(f"{record_id}: living_edge may not be published as a factual historical claim")
    if verification.get("state") == "verified" and not record["sources"]:
        fail(f"{record_id}: verified records require at least one source")

    if not isinstance(record["sources"], list):
        fail(f"{record_id}: sources must be an array")
    source_urls_seen = set()
    for source in record["sources"]:
        if not isinstance(source, dict):
            fail(f"{record_id}: every source must be an object")
        if not isinstance(source.get("title"), str) or not source["title"].strip():
            fail(f"{record_id}: source title must be non-empty")
        if not is_http_url(source.get("url")):
            fail(f"{record_id}: every source needs a valid http(s) URL")
        if source["url"] in source_urls_seen:
            fail(f"{record_id}: duplicate source URL {source['url']}")
        source_urls_seen.add(source["url"])
        if source.get("sourceType") not in SOURCE_TYPES:
            fail(f"{record_id}: invalid sourceType")
        if not isinstance(source.get("primary"), bool):
            fail(f"{record_id}: source.primary must be boolean")
        if "publishedDate" in source and not valid_date(source.get("publishedDate")):
            fail(f"{record_id}: source publishedDate must be ISO date or null")
        for field in ("embedUrl", "archivedUrl"):
            value = source.get(field)
            if value is not None and not is_http_url(value):
                fail(f"{record_id}: source {field} must be http(s) URL or null")

    if not isinstance(record["relationships"], list):
        fail(f"{record_id}: relationships must be an array")
    for relationship in record["relationships"]:
        if not isinstance(relationship, dict):
            fail(f"{record_id}: relationship must be an object")
        if relationship.get("type") not in RELATIONSHIP_TYPES:
            fail(f"{record_id}: invalid relationship type")
        if not isinstance(relationship.get("label"), str) or not relationship["label"].strip():
            fail(f"{record_id}: relationship label must be non-empty")
        if relationship.get("evidenceState") not in RELATIONSHIP_EVIDENCE:
            fail(f"{record_id}: invalid relationship evidenceState")
        source_urls = relationship.get("sourceUrls", [])
        if not isinstance(source_urls, list) or any(not is_http_url(url) for url in source_urls):
            fail(f"{record_id}: relationship sourceUrls must contain valid http(s) URLs")

id_set = set(ids)
for record in events:
    record_id = record["id"]
    for relationship in record["relationships"]:
        target = relationship.get("targetId")
        if target is not None and target not in id_set:
            fail(f"{record_id}: unresolved relationship target {target}")
        if relationship["type"] in {"ancestor", "descendant", "influenced", "enabled"} and relationship["evidenceState"] == "verified" and not relationship.get("sourceUrls"):
            fail(f"{record_id}: verified causal relationship {relationship['type']} requires sourceUrls")

media_items = media_doc.get("items")
if not isinstance(media_items, list):
    fail("data/media.json items must be an array")
media_ids = set()
for item in media_items:
    item_id = require_unique_id(item, media_ids, "media")
    if item.get("eventId") not in id_set:
        fail(f"media {item_id}: unresolved eventId {item.get('eventId')}")
    if not isinstance(item.get("title"), str) or not item["title"].strip():
        fail(f"media {item_id}: title must be non-empty")
    if not isinstance(item.get("creator"), str) or not item["creator"].strip():
        fail(f"media {item_id}: creator must be non-empty")
    if not valid_date(item.get("publishedDate")) or item.get("publishedDate") is None:
        fail(f"media {item_id}: publishedDate must be an ISO date")
    if not is_http_url(item.get("watchUrl")) or not is_http_url(item.get("embedUrl")):
        fail(f"media {item_id}: watchUrl and embedUrl must be valid http(s) URLs")

course_items = courses_doc.get("items")
if not isinstance(course_items, list):
    fail("data/courses.json items must be an array")
course_ids = set()
for item in course_items:
    item_id = require_unique_id(item, course_ids, "course")
    event_ids = item.get("eventIds")
    if not isinstance(event_ids, list) or not event_ids:
        fail(f"course {item_id}: eventIds must be a non-empty array")
    if len(event_ids) != len(set(event_ids)):
        fail(f"course {item_id}: eventIds must not contain duplicates")
    unresolved = [event_id for event_id in event_ids if event_id not in id_set]
    if unresolved:
        fail(f"course {item_id}: unresolved eventIds {', '.join(unresolved)}")
    for field in ("title", "provider", "institution", "level", "access"):
        if not isinstance(item.get(field), str) or not item[field].strip():
            fail(f"course {item_id}: {field} must be non-empty")
    if item.get("providerType") not in COURSE_PROVIDER_TYPES:
        fail(f"course {item_id}: invalid providerType")
    if not is_http_url(item.get("courseUrl")):
        fail(f"course {item_id}: courseUrl must be a valid http(s) URL")
    if item.get("embedUrl") is not None and not is_http_url(item.get("embedUrl")):
        fail(f"course {item_id}: embedUrl must be a valid http(s) URL or null")
    topics = item.get("topics")
    if not isinstance(topics, list) or not topics or any(not isinstance(topic, str) or not topic.strip() for topic in topics):
        fail(f"course {item_id}: topics must be a non-empty array of strings")
    if not valid_datetime(item.get("verifiedAt")) or item.get("verifiedAt") is None:
        fail(f"course {item_id}: verifiedAt must be an ISO date-time")

index = (ROOT / "index.html").read_text(encoding="utf-8")
beam_ids = re.findall(r'data-event="([^"]+)"', index)
if len(beam_ids) != len(set(beam_ids)):
    fail("index.html contains duplicate data-event ids")
for record_id in ids:
    if record_id != "now" and record_id not in beam_ids:
        fail(f"canonical record {record_id} is not reachable from a beam data-event")
for beam_id in beam_ids:
    if beam_id not in id_set:
        fail(f"index.html beam references unknown canonical record {beam_id}")
if 'data-event="now"' not in index:
    fail("index.html must expose the NOW living edge")
if 'aria-label="Enter the living present"' not in index:
    fail("NOW control must retain its accessible label")

print(f"OK: {len(events)} canonical records, {len(media_items)} media items, {len(course_items)} courses, {len(beam_ids)} traversable beam controls")
