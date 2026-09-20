from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT / 'config/alw-sources.json').read_text())

assert cfg['policy']['canonicalAdmission'] == 'never-from-scanner'
assert cfg['officialRoots']

for p in [ROOT / 'data/alw/inbox.json', ROOT / 'data/alw/source-state.json']:
    json.loads(p.read_text())

# The scheduled scanner is discovery-only. If its execution changes anything
# outside data/alw/, fail before the workflow can commit or push. This keeps
# canonical history, candidates, learning resources, contextual media, and
# other production data behind their normal evidence/admission paths.
changed = subprocess.run(
    ['git', 'diff', '--name-only'],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
for path in changed:
    assert path.startswith('data/alw/'), f'ALW scanner write-boundary violation: {path}'

print('LINEAiGE automation contracts: PASS')
