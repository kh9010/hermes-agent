"""Run the deduplicated final regression selection; all paths recorded before execution."""
from pathlib import Path
import json
import subprocess
import sys

OUT = Path(__file__).parent
ROOT = OUT.resolve().parents[2]
paths = set(json.loads((OUT / 'broader-selection.json').read_text()))
paths.update(p for p in json.loads((OUT / 'display-surfaces.json').read_text())['command'] if p.startswith('tests/'))
paths.add('tests/gateway/test_oct07_compatibility.py')
paths = sorted(paths)
(OUT / 'final-selection.json').write_text(json.dumps(paths, indent=2) + '\n')
print(f'Final regression: {len(paths)} unique files', flush=True)
sys.exit(subprocess.call([str(ROOT / '.venv/bin/python'), str(OUT / 'run_isolated.py'),
    'regression-final-verified', '--broad', *paths, '-q', '-rfs', '--tb=short'], cwd=ROOT))
