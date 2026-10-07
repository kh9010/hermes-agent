"""Load release bytes for changed modules without altering the candidate worktree.

All other modules are still untouched release files. Compiler filenames remain the
candidate paths so package-relative resource lookup behaves identically. This is
for differential diagnosis, not a replacement for an independent release CI run.
"""
import importlib.abc
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCES = json.loads((HERE / 'release-modules.json').read_text())

class ReleaseLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        filename = ROOT / (module.__name__.replace('.', '/') + '.py')
        module.__file__ = str(filename)
        exec(compile(SOURCES[module.__name__], str(filename), 'exec'), module.__dict__)

class ReleaseFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in SOURCES:
            return importlib.util.spec_from_loader(fullname, ReleaseLoader(),
                origin=str(ROOT / (fullname.replace('.', '/') + '.py')))
        return None

sys.meta_path.insert(0, ReleaseFinder())
