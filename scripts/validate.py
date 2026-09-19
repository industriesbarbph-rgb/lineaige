#!/usr/bin/env python3
import json
import re
from collections import deque
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

RECORD_TYPES = {"event", "entry_point", "living_edge", "announced_future"}
TEMPORAL_STATES = {"recorded", "forming", "declared-unresolved"}
DATE_PRECISIONS = {"day", "month", "year", "unknown"}
VERIFICATION_STATES = {"unreviewed", "developing", "verified", "disputed", "navigation-only"}
SOURCE_TYPES = {"paper", "official-announcement", "archive", "government-record", "book", "interview", "video", "news", "other"}
RELATIONSHIP_TYPES = {"ancestor", "descendant", "influenced", "enabled", "contextual", "chronological", "related", "source-path", "navigation"}
RELATIONSHIP_EVIDENCE = {"verified", "contextual", "disputed", "navigation-only"}
COURSE_PROVIDER_TYPES = {"university", "school", "online-platform", "technology-provider", "government", "nonprofit", "independent-provider", "other"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MONTH_RE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
YEAR_RE = re.compile(r"^[0-9]{4}$")
REQUIRED = {"id", "recordType", "title", "displayDate", "temporalState", "status", "summary", "verification", "sources", "relationships", "entryOrigin"}


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


def validate_temporal_precision(record):
    record_id = record["id"]
    precision = record.get("datePrecision")
    event_date = record.get("eventDate")
    event_month = record.get("eventMonth")
    event_year = record.get("eventYear")

    if precision is None:
        # Backward-compatible migration behavior: existing canonical records with
        # eventDate are treated as day-precision until explicitly migrated.
        if event_date is not None:
            precision = "day"
        elif record.get("recordType") == "living_edge":
            return
        else:
            fail(f"{record_id}: recorded canonical record without eventDate requires datePrecision")

    if precision not in DATE_PRECISIONS:
        fail(f"{record_id}: invalid datePrecision")

    if precision == "day":
        if event_date is None or not valid_date(event_date):
            fail(f"{record_id}: day precision requires ISO eventDate")
        if event_month is not None or event_year is not None:
            fail(f"{record_id}: day precision may not also set eventMonth/eventYear")
    elif precision == "month":
        if event_date is not None:
            fail(f"{record_id}: month precision may not carry synthetic eventDate")
        if not isinstance(event_month, str) or not MONTH_RE.fullmatch(event_month):
            fail(f"{record_id}: month precision requires eventMonth YYYY-MM")
        if event_year is not None:
            fail(f"{record_id}: month precision may not also set eventYear")
    elif precision == "year":
        if event_date is not None or event_month is not None:
            fail(f"{record_id}: year precision may not carry synthetic eventDate/eventMonth")
        if not isinstance(event_year, str) or not YEAR_RE.fullmatch(event_year):
            fail(f"{record_id}: year precision requires eventYear YYYY")
    elif precision == "unknown":
        if event_date is not None or event_month is not None or event_year is not None:
            fail(f"{record_id}: unknown precision may not carry a synthetic temporal value")




def validate_future_target_precision(record):
    record_id = record["id"]
    precision = record.get("targetPrecision")
    target_date = record.get("targetDate")
    target_month = record.get("targetMonth")
    target_year = record.get("targetYear")

    if precision is None:
        if target_date is not None:
            precision = "day"
        elif target_month is not None:
            precision = "month"
        elif target_year is not None:
            precision = "year"
        else:
            precision = "unknown"

    if precision not in DATE_PRECISIONS:
        fail(f"{record_id}: invalid targetPrecision")

    if precision == "day":
        if target_date is None or not valid_date(target_date):
            fail(f"{record_id}: day targetPrecision requires targetDate")
        if target_month is not None or target_year is not None:
            fail(f"{record_id}: day targetPrecision may not also set targetMonth/targetYear")
    elif precision == "month":
        if target_date is not None:
            fail(f"{record_id}: month targetPrecision may not carry synthetic targetDate")
        if not isinstance(target_month, str) or not MONTH_RE.fullmatch(target_month):
            fail(f"{record_id}: month targetPrecision requires targetMonth YYYY-MM")
        if target_year is not None:
            fail(f"{record_id}: month targetPrecision may not also set targetYear")
    elif precision == "year":
        if target_date is not None or target_month is not None:
            fail(f"{record_id}: year targetPrecision may not carry synthetic targetDate/targetMonth")
        if not isinstance(target_year, str) or not YEAR_RE.fullmatch(target_year):
            fail(f"{record_id}: year targetPrecision requires targetYear YYYY")
    elif precision == "unknown":
        if target_date is not None or target_month is not None or target_year is not None:
            fail(f"{record_id}: unknown targetPrecision may not carry a synthetic target value")

events_doc = load_json("events.json")
media_doc = load_json("media.json")
courses_doc = load_json("courses.json")
creator_releases_doc = load_json("creator-releases.json")
schema_doc = load_json("event.schema.json")

if events_doc.get("schemaVersion") != "1.1.0":
    fail("data/events.json schemaVersion must be 1.1.0")
if media_doc.get("schemaVersion") != "1.0.0":
    fail("data/media.json schemaVersion must be 1.0.0")
if courses_doc.get("schemaVersion") != "1.0.0":
    fail("data/courses.json schemaVersion must be 1.0.0")
if creator_releases_doc.get("schemaVersion") != "1.0.0":
    fail("data/creator-releases.json schemaVersion must be 1.0.0")
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
    if "eventMonth" in record and record.get("eventMonth") is not None and not MONTH_RE.fullmatch(str(record.get("eventMonth"))):
        fail(f"{record_id}: eventMonth must be YYYY-MM or null")
    if "eventYear" in record and record.get("eventYear") is not None and not YEAR_RE.fullmatch(str(record.get("eventYear"))):
        fail(f"{record_id}: eventYear must be YYYY or null")
    if record.get("entryOrigin") not in {"lineaige", "co-author"}:
        fail(f"{record_id}: entryOrigin must be lineaige or co-author")

    contributor = record.get("contributor")
    if record.get("entryOrigin") == "co-author":
        if not isinstance(contributor, dict):
            fail(f"{record_id}: co-author records require contributor metadata")
        if not isinstance(contributor.get("name"), str) or not contributor["name"].strip():
            fail(f"{record_id}: co-author contributor.name must be non-empty")
    elif contributor is not None:
        fail(f"{record_id}: lineaige-authored records must not carry co-author contributor metadata")

    contributions = record.get("contributions", [])
    if not isinstance(contributions, list):
        fail(f"{record_id}: contributions must be an array when present")
    contribution_ids = set()
    for contribution in contributions:
        if not isinstance(contribution, dict):
            fail(f"{record_id}: every contribution must be an object")
        contribution_id = contribution.get("id")
        if not isinstance(contribution_id, str) or not ID_RE.fullmatch(contribution_id):
            fail(f"{record_id}: contribution has invalid id {contribution_id!r}")
        if contribution_id in contribution_ids:
            fail(f"{record_id}: duplicate contribution id {contribution_id}")
        contribution_ids.add(contribution_id)
        if contribution.get("origin") not in {"lineaige", "co-author"}:
            fail(f"{record_id}: contribution {contribution_id} has invalid origin")
        if contribution.get("type") not in {"factual-addition", "context", "interpretation", "question-research-lead", "correction"}:
            fail(f"{record_id}: contribution {contribution_id} has invalid type")
        if not isinstance(contribution.get("text"), str) or not contribution["text"].strip():
            fail(f"{record_id}: contribution {contribution_id} requires text")
        if not valid_datetime(contribution.get("admittedAt")):
            fail(f"{record_id}: contribution {contribution_id} requires admittedAt ISO date-time")
        contribution_sources = contribution.get("sources", [])
        if not isinstance(contribution_sources, list) or any(not is_http_url(url) for url in contribution_sources):
            fail(f"{record_id}: contribution {contribution_id} sources must be http(s) URLs")
        if contribution.get("origin") == "co-author":
            contribution_person = contribution.get("contributor")
            if not isinstance(contribution_person, dict):
                fail(f"{record_id}: co-author contribution {contribution_id} requires contributor metadata")
            public_name = contribution_person.get("name") or contribution_person.get("creditPreference")
            if not isinstance(public_name, str) or not public_name.strip():
                fail(f"{record_id}: co-author contribution {contribution_id} requires public credit")

    if record["recordType"] in {"event", "entry_point"}:
        validate_temporal_precision(record)
    elif record["recordType"] == "announced_future":
        if record.get("temporalState") != "declared-unresolved":
            fail(f"{record_id}: announced_future must use temporalState=declared-unresolved")
        if not valid_date(record.get("announcementDate")) or record.get("announcementDate") is None:
            fail(f"{record_id}: announced_future requires an ISO announcementDate")
        validate_future_target_precision(record)
    elif record["recordType"] == "living_edge" and record.get("temporalState") != "forming":
        fail(f"{record_id}: living_edge must use temporalState=forming")

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
    event_ids = item.get("eventIds", [])
    if not isinstance(event_ids, list):
        fail(f"course {item_id}: eventIds must be an array when present")
    if len(event_ids) != len(set(event_ids)):
        fail(f"course {item_id}: eventIds must not contain duplicates")
    unresolved = [event_id for event_id in event_ids if event_id not in id_set]
    if unresolved:
        fail(f"course {item_id}: unresolved eventIds {', '.join(unresolved)}")
    start_precision = item.get("startPrecision")
    if start_precision is not None and start_precision not in DATE_PRECISIONS:
        fail(f"course {item_id}: invalid startPrecision")
    if item.get("startDate") is not None and not valid_date(item.get("startDate")):
        fail(f"course {item_id}: startDate must be an ISO date")
    if item.get("startMonth") is not None and not MONTH_RE.fullmatch(str(item.get("startMonth"))):
        fail(f"course {item_id}: startMonth must be YYYY-MM")
    if item.get("startYear") is not None and not YEAR_RE.fullmatch(str(item.get("startYear"))):
        fail(f"course {item_id}: startYear must be YYYY")
    if item.get("endDate") is not None and not valid_date(item.get("endDate")):
        fail(f"course {item_id}: endDate must be an ISO date")
    if item.get("endMonth") is not None and not MONTH_RE.fullmatch(str(item.get("endMonth"))):
        fail(f"course {item_id}: endMonth must be YYYY-MM")
    if item.get("endYear") is not None and not YEAR_RE.fullmatch(str(item.get("endYear"))):
        fail(f"course {item_id}: endYear must be YYYY")
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

creator_release_items = creator_releases_doc.get("items")
if not isinstance(creator_release_items, list):
    fail("data/creator-releases.json items must be an array")
creator_release_ids = set()
for item in creator_release_items:
    item_id = require_unique_id(item, creator_release_ids, "creator release")
    if not isinstance(item.get("title"), str) or not item["title"].strip():
        fail(f"creator release {item_id}: title must be non-empty")
    release_url = item.get("projectUrl") or item.get("releaseUrl")
    if release_url is not None and not is_http_url(release_url):
        fail(f"creator release {item_id}: projectUrl/releaseUrl must be a valid http(s) URL")
    if item.get("releaseDate") is not None and not valid_date(item.get("releaseDate")):
        fail(f"creator release {item_id}: releaseDate must be an ISO date")
    if item.get("releaseMonth") is not None and not MONTH_RE.fullmatch(str(item.get("releaseMonth"))):
        fail(f"creator release {item_id}: releaseMonth must be YYYY-MM")
    if item.get("releaseYear") is not None and not YEAR_RE.fullmatch(str(item.get("releaseYear"))):
        fail(f"creator release {item_id}: releaseYear must be YYYY")

index = (ROOT / "index.html").read_text(encoding="utf-8")
runtime = (ROOT / "lineaige.js").read_text(encoding="utf-8")
data_adapter_path = ROOT / "lineaige-data.js"
data_adapter = data_adapter_path.read_text(encoding="utf-8") if data_adapter_path.exists() else ""

static_ids = re.findall(r'data-event="([^"]+)"', index)
if len(static_ids) != len(set(static_ids)):
    fail("index.html contains duplicate static data-event ids")
for static_id in static_ids:
    if static_id not in id_set:
        fail(f"index.html references unknown canonical record {static_id}")

# During the renderer transition, the legacy interface may expose static entry controls.
# The official Pencil renderer will instead generate the canonical inventory from
# data/events.json through lineaige-data.js. Both modes remain fail-closed here.
if static_ids:
    if "now" not in static_ids:
        fail("static renderer must expose the NOW living edge")
    graph = {
        record["id"]: [rel.get("targetId") for rel in record["relationships"] if rel.get("targetId")]
        for record in events
    }
    reachable = set()
    queue = deque(static_ids)
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        queue.extend(target for target in graph.get(current, []) if target not in reachable)

    unreachable = sorted(id_set - reachable)
    if unreachable:
        fail(f"canonical records unreachable through static traversal graph: {', '.join(unreachable)}")
    renderer_mode = f"static-transition ({len(static_ids)} entry controls)"
else:
    if not data_adapter_path.exists():
        fail("data-driven renderer requires lineaige-data.js")
    if "canonicalTimelineRecords" not in data_adapter or "data/events.json" not in data_adapter:
        fail("lineaige-data.js must derive the public timeline from data/events.json")
    if "data/candidates/" in runtime or "research-ledger.json" in runtime:
        fail("public runtime must not silently render candidates or research-ledger entries as canonical history")
    renderer_mode = "data-driven"

print(
    f"OK: {len(events)} canonical records, {len(media_items)} media items, {len(course_items)} learning/program records, {len(creator_release_items)} creator releases; "
    f"renderer mode: {renderer_mode}"
)
