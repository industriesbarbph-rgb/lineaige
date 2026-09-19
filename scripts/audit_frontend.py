#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
index = (ROOT / "index.html").read_text(encoding="utf-8")
css = (ROOT / "lineaige.css").read_text(encoding="utf-8")
js = (ROOT / "lineaige.js").read_text(encoding="utf-8")
data_js = (ROOT / "lineaige-data.js").read_text(encoding="utf-8")
media_js = (ROOT / "media.js").read_text(encoding="utf-8")
courses_js = (ROOT / "courses.js").read_text(encoding="utf-8")


def fail(message):
    raise SystemExit(f"FRONTEND AUDIT FAILED: {message}")


def require(haystack, needle, message):
    if needle not in haystack:
        fail(message)


require(index, '<html lang="en">', "document language must be declared")
require(index, 'name="viewport"', "responsive viewport meta tag is required")
require(index, '<title>BarbPH LINEAiGE', "document title must identify BarbPH LINEAiGE")
require(index, 'name="description"', "meta description is required")
require(index, 'aria-label="BarbPH LINEAiGE"', "main stage needs an accessible name")
require(index, 'id="lineaigeTimeline"', "canonical data-driven timeline mount is required")
require(index, 'id="timelineViewport"', "drag-through-time viewport is required")
require(index, 'id="todayMark"', "TODAY living-edge control is required")
require(index, 'aria-live="polite"', "record note must announce updates politely")
require(index, 'id="close" type="button" aria-label="Close record"', "record close control needs an accessible label")
require(index, 'href="/co-author/"', "permanent co-author doorway is required")
require(index, '>BE A CO-AUTHOR</a>', "co-author control must be words")
require(index, '>PAPER TRAIL</a>', "Paper Trail control must be words")
require(index, '>YOUTUBE</a>', "YouTube control must be words")
require(index, '>CONTACT US</a>', "Contact control must be words")
require(index, 'target="_blank" rel="noopener noreferrer">PAPER TRAIL', "Paper Trail must open safely in a new tab")
require(index, '<script src="lineaige-data.js"></script>', "canonical data adapter must load before renderer")
require(index, '<script src="lineaige.js"></script>', "canonical interaction script must be loaded")
require(index, '<script src="media.js"></script>', "media layer script must be loaded")
require(index, '<script src="courses.js"></script>', "course layer script must be loaded")

if re.search(r'data-event="', index):
    fail("history must not be hard-coded into index.html")

for forbidden in (
    "turing-1950",
    "dartmouth-1955",
    "rosenblatt-1958",
    "transformer-2017",
    "chatgpt-2022",
    "beam-wrap",
    "circuit-field",
    "future-particles",
):
    if forbidden in index.lower():
        fail(f"discarded or hard-coded frontend token remains in index.html: {forbidden}")

if re.search(r'(?:src|href)="http://', index):
    fail("index.html must not load insecure http resources")

require(css, ':focus-visible', "visible keyboard focus styling is required")
require(css, '@media(prefers-reduced-motion:reduce)', "reduced-motion support is required")
require(css, '@media(max-width:760px)', "mobile layout breakpoint is required")
require(css, '.history-line', "charcoal history line styling is required")
require(css, '.brand-emboss', "BarbPH embossed wordmark treatment is required")
require(css, '.timeline-viewport.dragging', "drag interaction state styling is required")

require(data_js, "canonicalTimelineRecords", "canonical data adapter must expose timeline derivation")
require(data_js, "learningTemporalValue", "learning/program temporal placement support is required")
require(data_js, "creatorTemporalValue", "creator release temporal placement support is required")

require(js, "event.key==='Escape'", "Escape must close the record note")
require(js, "event.key==='ArrowRight'", "keyboard traversal must support ArrowRight")
require(js, "event.key==='ArrowLeft'", "keyboard traversal must support ArrowLeft")
require(js, "lastTrigger", "record close must retain trigger context")
require(js, "focus({preventScroll:true})", "closing/opening must manage focus without moving timeline")
require(js, "lineaige:record-opened", "canonical record-open event is required for supplemental layers")
require(js, "lineaige:record-closed", "canonical record-close event is required for supplemental cleanup")
require(js, "function safeExternalUrl", "external source URLs must be protocol-checked")
require(js, "supportedRelationships", "TRACE EVOLUTION must be evidence-gated")
require(js, "traceButton.hidden=relationshipCount===0", "TRACE EVOLUTION must disappear when no defensible relationship exists")
require(js, "proofButton.hidden=sources.length===0", "proof action must disappear when no admitted source trail exists")
require(js, "record.contributions", "contribution-level marginalia rendering support is required")
require(js, "Intl.DateTimeFormat().resolvedOptions().timeZone", "TODAY must expose visitor-local timezone context")

require(media_js, "lineaige:record-opened", "media layer must synchronize with canonical traversal")
require(media_js, "lineaige:record-closed", "media layer must clean up when records close")
require(courses_js, "lineaige:record-opened", "learning layer must synchronize with canonical traversal")
require(courses_js, "lineaige:record-closed", "learning layer must clean up when records close")

coauthor = ROOT / "co-author" / "index.html"
if not coauthor.exists():
    fail("co-author/index.html is required")
coauthor_text = coauthor.read_text(encoding="utf-8")
require(coauthor_text, 'name="robots" content="noindex, follow"', "temporary co-author page must remain noindex until launch")

print("OK: official Pencil renderer, word-only controls, evidence-gated pathways, drag traversal, local TODAY, accessibility, and co-author doorway checks passed")
