"""Use upstream per-file isolation, with every scratch write inside this worktree."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts import run_tests_parallel as runner

scratch = Path(os.environ['TMPDIR']) / 'per-file'
scratch.mkdir()
runner._runner_scratch_root = lambda: str(scratch)
# Duration cache is an optimization, not test evidence. Do not mutate it.
runner._save_durations = lambda *a, **kw: None
if __name__ == '__main__':
    sys.exit(runner.main())
