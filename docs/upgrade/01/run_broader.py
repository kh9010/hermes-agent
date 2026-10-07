"""Explicit discovery for upgrade-relevant broader regression; fail if a pattern is empty."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
patterns = [
    'tests/gateway/test_whatsapp*.py', 'tests/gateway/test_*auth*.py',
    'tests/gateway/test_display*.py', 'tests/gateway/test_run_progress_topics.py',
    'tests/gateway/test_config_driven_access_policy.py',
    'tests/gateway/test_oct07_upgrade_contracts.py',
    'tests/agent/test_*prompt*.py', 'tests/agent/test_*skills*.py',
    'tests/agent/test_*oneshot*.py',
]
files = set()
for pattern in patterns:
    matches = list(ROOT.glob(pattern))
    if not matches:
        raise SystemExit(f'Empty discovery pattern: {pattern}')
    files.update(str(p.relative_to(ROOT)) for p in matches)
files = sorted(files)
(Path(__file__).parent / 'broader-selection.json').write_text(json.dumps(files, indent=2) + '\n')
print(f'Broader regression: {len(files)} files', flush=True)
label = sys.argv[1] if len(sys.argv) > 1 else 'broader'
sys.exit(subprocess.call([str(ROOT / '.venv/bin/python'), 'docs/upgrade/01/run_isolated.py',
                         label, '--broad', *files, '--tb=short', '-q'], cwd=ROOT))
