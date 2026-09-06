#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
index = (ROOT / "index.html").read_text(encoding="utf-8")
css = (ROOT / "lineaige.css").read_text(encoding="utf-8")
js = (ROOT / "lineaige.js").read_text(encoding="utf-8")
media_js = (ROOT / "media.js").read_text(encoding="utf-8")
courses_js = (ROOT / "courses.js").read_text(encoding="utf-8")


def fail(message):
    raise SystemExit(f"FRONTEND AUDIT FAILED: {message}")


def require(haystack, needle, message):
    if needle not in haystack:
        fail(message)


require(index, '<html lang="en">', "document language must be declared")
require(index, 'name="viewport"', "responsive viewport meta tag is required")
require(index, '<title>LINEAiGE', "document title must identify LINEAiGE")
require(index, 'name="description"', "meta description is required")
require(index, 'aria-label="LINEAiGE"', "main stage needs an accessible name")
require(index, 'aria-live="polite"', "record drawer must announce updates politely")
require(index, 'aria-hidden="true"', "drawer must start hidden from assistive technology")
require(index, 'id="close" aria-label="Close"', "drawer close control needs an accessible label")
require(index, 'data-event="now" aria-label="Enter the living present"', "NOW must remain keyboard-addressable and labelled")
require(index, '<script src="lineaige.js"></script>', "canonical interaction script must be loaded")
require(index, '<script src="media.js"></script>', "media layer script must be loaded")
require(index, '<script src="courses.js"></script>', "course layer script must be loaded")

for match in re.finditer(r'<button\b([^>]*)>', index):
    attrs = match.group(1)
    if 'data-event=' in attrs and 'aria-label=' not in attrs:
        fail("every beam data-event button requires an aria-label")

if re.search(r'(?:src|href)="http://', index):
    fail("index.html must not load insecure http resources")

require(css, ':focus-visible', "visible keyboard focus styling is required")
require(css, '@media(prefers-reduced-motion:reduce)', "reduced-motion support is required")
require(css, '@media(max-width:700px)', "mobile layout breakpoint is required")

require(js, "event.key==='Escape'", "Escape must close the record drawer")
require(js, "event.key==='ArrowRight'", "beam keyboard traversal must support ArrowRight")
require(js, "event.key==='ArrowLeft'", "beam keyboard traversal must support ArrowLeft")
require(js, "lastTrigger.focus", "closing the drawer must restore focus to the triggering beam point")
require(js, "lineaige:record-opened", "canonical record-open event is required for supplemental layers")
require(js, "lineaige:record-closed", "canonical record-close event is required for supplemental cleanup")
require(media_js, "lineaige:record-opened", "media layer must synchronize with canonical record traversal")
require(media_js, "lineaige:record-closed", "media layer must clean up when records close")
require(courses_js, "lineaige:record-opened", "course layer must synchronize with canonical record traversal")
require(courses_js, "lineaige:record-closed", "course layer must clean up when records close")

print("OK: frontend accessibility, responsive, graceful-failure integration, and static deployment checks passed")
