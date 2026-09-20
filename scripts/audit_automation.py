from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
cfg=json.loads((ROOT/'config/alw-sources.json').read_text())
assert cfg['policy']['canonicalAdmission']=='never-from-scanner'
assert cfg['officialRoots']
for p in [ROOT/'data/alw/inbox.json',ROOT/'data/alw/source-state.json']:json.loads(p.read_text())
print('LINEAiGE automation contracts: PASS')
