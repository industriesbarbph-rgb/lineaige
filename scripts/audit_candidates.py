#!/usr/bin/env python3
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data" / "candidates"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
DATE_PRECISIONS = {"day", "month", "year", "unknown"}
SOURCE_ROLES = {"claim-evidence", "corroboration", "context", "learning-resource"}
GEOGRAPHY_CONTEXTS = {"event-location", "announcement-location", "organization-base", "research-location", "development-location", "release-geography"}


def fail(message):
    raise SystemExit(f"CANDIDATE AUDIT FAILED: {message}")


def http_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


files = sorted(CANDIDATES.glob("*.json"))
if not files:
    fail("data/candidates must contain at least one candidate record")

seen = set()
for path in files:
    with path.open("r", encoding="utf-8") as handle:
        record = json.load(handle)

    rid = record.get("id")
    if not isinstance(rid, str) or not ID_RE.fullmatch(rid):
        fail(f"{path.name}: invalid id {rid!r}")
    if rid in seen:
        fail(f"duplicate candidate id {rid}")
    seen.add(rid)

    if record.get("status") != "VERIFIED CANDIDATE":
        fail(f"{rid}: candidate status must be VERIFIED CANDIDATE")
    verification = record.get("verification")
    if not isinstance(verification, dict) or verification.get("state") != "verified":
        fail(f"{rid}: candidate verification.state must be verified")
    if verification.get("factualClaim") is not True:
        fail(f"{rid}: verified candidate must be a factual claim")
    if verification.get("confidence") not in {"medium", "high"}:
        fail(f"{rid}: verified candidate confidence must be medium or high")
    if not verification.get("lastVerified"):
        fail(f"{rid}: verification.lastVerified is required")

    precision = record.get("datePrecision", "day" if record.get("eventDate") else "unknown")
    if precision not in DATE_PRECISIONS:
        fail(f"{rid}: unsupported datePrecision {precision!r}")
    event_date = record.get("eventDate")
    publication_month = record.get("publicationMonth")
    event_year = record.get("eventYear")
    if precision == "day" and not isinstance(event_date, str):
        fail(f"{rid}: day precision requires eventDate")
    if precision == "month":
        if event_date is not None:
            fail(f"{rid}: month precision must not fabricate a day-level eventDate")
        if not isinstance(publication_month, str) or not MONTH_RE.fullmatch(publication_month):
            fail(f"{rid}: month precision requires publicationMonth YYYY-MM")
    if precision == "year":
        if event_date is not None:
            fail(f"{rid}: year precision must not carry a day-level eventDate")
        if not isinstance(event_year, int) or event_year < 1 or event_year > 9999:
            fail(f"{rid}: year precision requires integer eventYear 1..9999")
    if precision == "unknown" and event_date is not None:
        fail(f"{rid}: unknown precision must not carry a day-level eventDate")

    sources = record.get("sources")
    if not isinstance(sources, list) or not sources:
        fail(f"{rid}: verified candidate requires sources")
    urls = set()
    primary_claim = False
    for source in sources:
        url = source.get("url")
        if not http_url(url):
            fail(f"{rid}: invalid source URL")
        if url in urls:
            fail(f"{rid}: duplicate source URL {url}")
        urls.add(url)
        role = source.get("sourceRole")
        if role not in SOURCE_ROLES:
            fail(f"{rid}: sourceRole must be explicit and valid")
        if source.get("primary") is True and role == "claim-evidence":
            primary_claim = True
        if precision == "month" and source.get("publishedDate") is not None:
            fail(f"{rid}: month-precision source must not carry fabricated publishedDate")
    if not primary_claim:
        fail(f"{rid}: verified candidate requires primary claim-evidence")

    geography = record.get("geography")
    if geography is not None:
        if not isinstance(geography, dict):
            fail(f"{rid}: geography must be an object when present")
        context = geography.get("context")
        if context not in GEOGRAPHY_CONTEXTS:
            fail(f"{rid}: geography.context must use an explicit supported meaning")
        source_url = geography.get("sourceUrl")
        if not http_url(source_url):
            fail(f"{rid}: geography.sourceUrl must be a valid HTTP(S) URL")
        if source_url not in urls:
            fail(f"{rid}: geography.sourceUrl must also appear in sources")
        if not any(isinstance(geography.get(field), str) and geography[field].strip() for field in ("city", "country", "region")):
            fail(f"{rid}: geography must include at least one concrete place field")

    relationships = record.get("relationships")
    if relationships != []:
        fail(f"{rid}: candidates must not assert relationships before canonical admission")

    meta = record.get("candidateMeta")
    if not isinstance(meta, dict):
        fail(f"{rid}: candidateMeta is required")
    for key in ("canonicalAdmission", "admissionReason", "nextStep"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            fail(f"{rid}: candidateMeta.{key} is required")

print(f"OK: {len(files)} evidence-controlled candidate records validated")
