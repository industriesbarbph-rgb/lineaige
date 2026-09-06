#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_json(name):
    path = DATA / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_http_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def fail(message):
    raise SystemExit(f"VALIDATION FAILED: {message}")


events_doc = load_json("events.json")
media_doc = load_json("media.json")
courses_doc = load_json("courses.json")
load_json("event.schema.json")

events = events_doc.get("events")
if not isinstance(events, list) or not events:
    fail("data/events.json must contain a non-empty events array")

ids = []
for record in events:
    if not isinstance(record, dict):
        fail("every event must be an object")
    record_id = record.get("id")
    if not isinstance(record_id, str) or not record_id:
        fail("every event needs a non-empty string id")
    if record_id in ids:
        fail(f"duplicate event id: {record_id}")
    ids.append(record_id)
    if not isinstance(record.get("title"), str) or not isinstance(record.get("summary"), str):
        fail(f"{record_id}: title and summary must be strings")

id_set = set(ids)

for record in events:
    record_id = record["id"]
    for source in record.get("sources", []):
        if not isinstance(source, dict) or not is_http_url(source.get("url")):
            fail(f"{record_id}: every source needs a valid http(s) URL")
    for relationship in record.get("relationships", []):
        if not isinstance(relationship, dict):
            fail(f"{record_id}: relationship must be an object")
        target = relationship.get("targetId")
        if target is not None and target not in id_set:
            fail(f"{record_id}: unresolved relationship target {target}")

for item in media_doc.get("items", []):
    event_id = item.get("eventId")
    if event_id not in id_set:
        fail(f"media {item.get('id')}: unresolved eventId {event_id}")
    if not is_http_url(item.get("watchUrl")) or not is_http_url(item.get("embedUrl")):
        fail(f"media {item.get('id')}: watchUrl and embedUrl must be valid http(s) URLs")

for item in courses_doc.get("items", []):
    event_ids = item.get("eventIds")
    if not isinstance(event_ids, list) or not event_ids:
        fail(f"course {item.get('id')}: eventIds must be a non-empty array")
    unresolved = [event_id for event_id in event_ids if event_id not in id_set]
    if unresolved:
        fail(f"course {item.get('id')}: unresolved eventIds {', '.join(unresolved)}")
    if not is_http_url(item.get("courseUrl")):
        fail(f"course {item.get('id')}: courseUrl must be a valid http(s) URL")

index = (ROOT / "index.html").read_text(encoding="utf-8")
for record_id in ids:
    if record_id == "now":
        continue
    if f'data-event="{record_id}"' not in index:
        fail(f"canonical record {record_id} is not reachable from a beam data-event")

print(f"OK: {len(events)} canonical records, {len(media_doc.get('items', []))} media items, {len(courses_doc.get('items', []))} courses")
