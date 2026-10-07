"""Run offline regressions in disposable worktree-local HOME; preserve exact logs.
Usage: .venv/bin/python docs/upgrade/01/run_checks.py LABEL [pytest paths/args ...]
Use --parallel as first pytest arg for the upstream per-file runner, --node for Node tests.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).parent

def main():
    label, *args = sys.argv[1:]
    assert label.replace('-', '').isalnum(), 'safe log label required'
    sandbox = tempfile.mkdtemp(prefix='.upgrade-test-', dir=ROOT)
    home = Path(sandbox)
    try:
        (home / '.hermes').mkdir()
        (home / 'tmp').mkdir()
        policy = home / 'offline.sb'
        policy.write_text('(version 1)\n(allow default)\n(deny network*)\n'
                          '(deny file-read* file-write* (subpath "/Users/kahransingh/.hermes"))\n')
        env = {'PATH': f'{ROOT}/.venv/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
               'HOME': str(home), 'HERMES_HOME': str(home / '.hermes'), 'TMPDIR': str(home / 'tmp'),
               'TZ': 'UTC', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'PYTHONHASHSEED': '0',
               'PYTHONUTF8': '1', 'HERMES_TEST_WORKERS': '4', 'HERMES_TEST_FILE_TIMEOUT': '90',
               'HERMES_TEST_FILE_RETRIES': '0'}
        if args and args[0] == '--parallel':
            cmd = [str(ROOT / '.venv/bin/python'), 'scripts/run_tests_parallel.py', *args[1:]]
        elif args and args[0] == '--node':
            cmd = ['/opt/homebrew/bin/node', '--test', *args[1:]]
        else:
            cmd = [str(ROOT / '.venv/bin/python'), '-m', 'pytest', '-q', '--tb=short', *args]
        actual = ['/usr/bin/sandbox-exec', '-f', str(policy), *cmd]
        logfile = EVIDENCE / f'{label}.log'
        with logfile.open('w') as stream:
            stream.write('COMMAND: ' + ' '.join(cmd) + '\nISOLATION: empty environment; disposable HOME/HERMES_HOME; macOS sandbox denies all network and live Hermes reads/writes.\n')
            stream.flush()
            result = subprocess.run(actual, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
            stream.write(f'\nEXIT_CODE: {result.returncode}\n')
        (EVIDENCE / f'{label}.json').write_text(json.dumps({'command': cmd, 'exit_code': result.returncode, 'log': logfile.name}, indent=2) + '\n')
        print(logfile.read_text()[-14000:])
        return result.returncode
    finally:
        shutil.rmtree(home)

if __name__ == '__main__':
    sys.exit(main())
