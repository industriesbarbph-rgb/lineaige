#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def load(name):
    with (DATA / name).open(encoding="utf-8") as fh:
        return json.load(fh)

canonical = len(load("events.json")["events"])
candidates = len(list((DATA / "candidates").glob("*.json")))
research = len(load("research-ledger.json")["entries"])
learning = len(load("courses.json")["items"])
media = len(load("media.json")["items"])
total = canonical + candidates + research + learning + media

print(f"LINEAIGE_DATA_COUNTS canonical={canonical} candidates={candidates} research_ledger={research} learning_resources={learning} contextual_media={media} total={total}")
