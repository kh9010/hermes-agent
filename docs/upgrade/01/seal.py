"""Seal this candidate/evidence version once, after all runs and review are complete."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert git('branch', '--show-current').decode().strip() == 'kahran-oct07-hermes-upgrade'
assert git('rev-parse', 'HEAD').decode().strip() == 'f97608f178d1ffeca59860195ab7da295f7c8e5f'
assert not git('diff', '--cached', '--name-only').strip()
assert not (OUT / 'manifest.json').exists(), 'Version already sealed; make a new version'
changed = git('diff', '--name-only').decode().splitlines()
new_tests = ['tests/gateway/test_oct07_compatibility.py', 'tests/gateway/test_oct07_upgrade_contracts.py',
             'tests/agent/test_oct07_prompt_contracts.py']
assert len(changed) == 9, changed
candidate = changed + new_tests
for name in candidate:
    dest = OUT / 'candidate' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes((ROOT / name).read_bytes())
(OUT / 'candidate.patch').write_bytes(git('diff', '--binary'))
(OUT / 'candidate-diffstat.txt').write_bytes(git('diff', '--stat'))
(OUT / 'workspace-status.txt').write_bytes(git('status', '--short'))
# This evidence tree did not exist before this task. Its import caches are ours.
for p in list(OUT.rglob('__pycache__')):
    shutil.rmtree(p)
files = sorted(p for p in OUT.rglob('*') if p.is_file())
manifest = {
    'version': 1,
    'release': git('rev-parse', 'HEAD').decode().strip(),
    'candidate': {name: sha(ROOT / name) for name in candidate + ['HANDOFF.md', 'verify.mjs', 'versions.json']},
    'evidence': {str(p.relative_to(ROOT)): sha(p) for p in files},
    'deployment_approved': False,
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
for p in files + [OUT / 'manifest.json']:
    p.chmod(0o444)
for p in sorted((p for p in OUT.rglob('*') if p.is_dir()), reverse=True):
    p.chmod(0o555)
OUT.chmod(0o555)
print(f'SEALED version 01: {len(candidate)} source/test files, {len(files)} evidence files; no commit or deployment')
