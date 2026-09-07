#!/usr/bin/env python3
"""Validate LINEAiGE's non-canonical research ledger.

The research ledger is intentionally separate from canonical history. This audit
prevents a held-back or under-review item from silently acquiring canonical
semantics while still preserving useful research, date uncertainty and sources.
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "research-ledger.json"

ALLOWED_RESEARCH_STATUS = {"investigating", "held-back", "canonical-review", "verified-candidate", "rejected"}
ALLOWED_ADMISSION = {"pending", "withheld", "review", "not-applicable"}
ALLOWED_PRECISION = {"day", "month", "year", "unknown"}
ALLOWED_SOURCE_ROLE = {"claim-evidence", "corroboration", "context"}
DATE_PATTERNS = {
    "day": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "month": re.compile(r"^\d{4}-\d{2}$"),
    "year": re.compile(r"^\d{4}$"),
    "unknown": re.compile(r"^unknown$"),
}

errors = []

def fail(message):
    errors.append(message)

def valid_http_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

try:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"RESEARCH LEDGER AUDIT FAILED: cannot parse {LEDGER}: {exc}")
    sys.exit(1)

if data.get("schemaVersion") != "1.0.0":
    fail("schemaVersion must be 1.0.0")

entries = data.get("entries")
if not isinstance(entries, list) or not entries:
    fail("entries must be a non-empty list")
    entries = []

ids = set()
for index, entry in enumerate(entries):
    prefix = f"entries[{index}]"
    if not isinstance(entry, dict):
        fail(f"{prefix} must be an object")
        continue

    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or not entry_id.strip():
        fail(f"{prefix}.id must be a non-empty string")
    elif entry_id in ids:
        fail(f"{prefix}.id duplicates {entry_id}")
    else:
        ids.add(entry_id)

    if entry.get("researchStatus") not in ALLOWED_RESEARCH_STATUS:
        fail(f"{prefix}.researchStatus is invalid")

    admission = entry.get("canonicalAdmission")
    if admission not in ALLOWED_ADMISSION:
        fail(f"{prefix}.canonicalAdmission is invalid")
    if admission == "admitted":
        fail(f"{prefix} may not use canonicalAdmission=admitted in the research ledger")

    for field in ("subject", "claimUnderReview", "evidenceSummary", "reasonWithheld"):
        if not isinstance(entry.get(field), str) or not entry[field].strip():
            fail(f"{prefix}.{field} must be a non-empty string")

    date = entry.get("date")
    if not isinstance(date, dict):
        fail(f"{prefix}.date must be an object")
    else:
        precision = date.get("precision")
        value = date.get("value")
        if precision not in ALLOWED_PRECISION:
            fail(f"{prefix}.date.precision is invalid")
        elif not isinstance(value, str) or not DATE_PATTERNS[precision].match(value):
            fail(f"{prefix}.date.value does not match precision={precision}")
        if not isinstance(date.get("meaning"), str) or not date["meaning"].strip():
            fail(f"{prefix}.date.meaning must explain what the date represents")

    if entry.get("researchStatus") == "canonical-review":
        target = entry.get("targetCanonicalId")
        if not isinstance(target, str) or not target.strip():
            fail(f"{prefix}.targetCanonicalId is required for canonical-review entries")
        if admission != "review":
            fail(f"{prefix} canonical-review entries must use canonicalAdmission=review")

    sources = entry.get("sources")
    if not isinstance(sources, list) or not sources:
        fail(f"{prefix}.sources must be a non-empty list")
        sources = []

    source_urls = set()
    primary_count = 0
    for sidx, source in enumerate(sources):
        sp = f"{prefix}.sources[{sidx}]"
        if not isinstance(source, dict):
            fail(f"{sp} must be an object")
            continue
        url = source.get("url")
        if not valid_http_url(url):
            fail(f"{sp}.url must be a valid HTTP(S) URL")
        elif url in source_urls:
            fail(f"{sp}.url duplicates another source in the same entry")
        else:
            source_urls.add(url)
        if source.get("sourceRole") not in ALLOWED_SOURCE_ROLE:
            fail(f"{sp}.sourceRole is invalid")
        if not isinstance(source.get("primary"), bool):
            fail(f"{sp}.primary must be boolean")
        elif source["primary"]:
            primary_count += 1
        for field in ("title", "publisher", "sourceType"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                fail(f"{sp}.{field} must be a non-empty string")
        published = source.get("publishedDate")
        if published is not None and not isinstance(published, str):
            fail(f"{sp}.publishedDate must be a string or null")

    if primary_count == 0:
        fail(f"{prefix} must retain at least one primary/first-party source")

    geography = entry.get("geography")
    if geography is not None:
        if not isinstance(geography, dict):
            fail(f"{prefix}.geography must be an object when present")
        else:
            gurl = geography.get("sourceUrl")
            if not valid_http_url(gurl):
                fail(f"{prefix}.geography.sourceUrl must be a valid HTTP(S) URL")
            elif gurl not in source_urls:
                fail(f"{prefix}.geography.sourceUrl must also appear in sources")
            if not isinstance(geography.get("context"), str) or not geography["context"].strip():
                fail(f"{prefix}.geography.context must be explicit")

    relationships = entry.get("relationships")
    if relationships not in (None, []):
        fail(f"{prefix}.relationships must remain empty until relationship-specific evidence handling is defined")

if errors:
    print("RESEARCH LEDGER AUDIT FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"RESEARCH LEDGER AUDIT PASSED: {len(entries)} preserved research entries; none admitted as canonical history.")
