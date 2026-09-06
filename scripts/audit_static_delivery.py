#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        for key in ("src", "href"):
            value = data.get(key)
            if value and not value.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                self.refs.append((tag, key, value.split("?", 1)[0].split("#", 1)[0]))

index = ROOT / "index.html"
if not index.exists():
    errors.append("index.html is missing")
else:
    parser = AssetParser()
    parser.feed(index.read_text(encoding="utf-8"))
    for tag, attr, ref in parser.refs:
        if not ref:
            continue
        target = (ROOT / ref.lstrip("/")).resolve()
        if ROOT not in target.parents and target != ROOT:
            errors.append(f"{tag}[{attr}] escapes repository root: {ref}")
        elif not target.exists():
            errors.append(f"missing local asset referenced by index.html: {ref}")

for js_name in ("lineaige.js", "media.js", "courses.js"):
    path = ROOT / js_name
    if not path.exists():
        errors.append(f"missing runtime script: {js_name}")
        continue
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"fetch\(\s*['\"]([^'\"]+)['\"]", text):
        ref = match.group(1)
        if ref.startswith(("http://", "https://")):
            errors.append(f"runtime script uses network fetch instead of bundled data: {js_name}: {ref}")
            continue
        target = (ROOT / ref.lstrip("./")).resolve()
        if ROOT not in target.parents and target != ROOT:
            errors.append(f"fetch target escapes repository root: {js_name}: {ref}")
        elif not target.exists():
            errors.append(f"missing bundled fetch target: {js_name}: {ref}")

required = [
    "data/events.json",
    "data/event.schema.json",
    "data/media.json",
    "data/courses.json",
]
for ref in required:
    if not (ROOT / ref).exists():
        errors.append(f"required production data file is missing: {ref}")

if errors:
    print("STATIC DELIVERY AUDIT FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("STATIC DELIVERY AUDIT PASSED")
print("All index assets, runtime scripts, and bundled data dependencies resolve inside the repository.")
