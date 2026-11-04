"""Offline candidate test launcher. No inherited credentials; network denied by macOS sandbox."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent

def main():
    label, *args = sys.argv[1:]
    assert label.replace('-', '').isalnum()
    with tempfile.TemporaryDirectory(prefix='upgrade-test-', dir=ROOT) as temp:
        home = Path(temp)
        hermes = home / '.hermes'
        hermes.mkdir()
        env = {'HOME': str(home), 'HERMES_HOME': str(hermes),
               'PATH': f'{ROOT}/.venv/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
               'TMPDIR': str(home), 'TZ': 'UTC', 'LANG': 'en_US.UTF-8',
               'PYTHONHASHSEED': '0', 'HERMES_TEST_WORKERS': '4',
               'HERMES_TEST_FILE_TIMEOUT': '120', 'HERMES_TEST_FILE_RETRIES': '0'}
        if args and args[0] == '--baseline':
            args.pop(0)
            env['PYTHONPATH'] = str(OUT) + ':' + str(ROOT)
            env['PYTEST_PLUGINS'] = 'baseline_plugin'
        # Child processes inherit these restrictions. No bridge, live credentials,
        # live-home writes, or channel/network access even on a faulty test path.
        profile = home / 'offline.sb'
        profile.write_text('(version 1)\n(allow default)\n(deny network*)\n'
                           '(deny file-read* file-write* (subpath "/Users/kahransingh/.hermes"))\n'
                           '(deny file-write* (subpath "/Users/kahransingh/Sync"))\n')
        if args and args[0] == '--node':
            command = ['/opt/homebrew/bin/node', '--test', *args[1:]]
        elif args and args[0] == '--broad':
            command = [str(ROOT / '.venv/bin/python'), 'docs/upgrade/01/broad_runner.py', *args[1:]]
        else:
            command = [str(ROOT / '.venv/bin/python'), '-m', 'pytest', '-q', '--tb=short', *args]
        wrapped = ['/usr/bin/sandbox-exec', '-f', str(profile), *command]
        log = OUT / f'{label}.log'
        with log.open('w') as stream:
            stream.write('COMMAND: ' + ' '.join(command) + '\nISOLATION: empty env; disposable HOME/HERMES_HOME; sandbox deny network and live Hermes reads/writes\n')
            stream.flush()
            result = subprocess.run(wrapped, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
            stream.write(f'\nEXIT_CODE: {result.returncode}\n')
        print(log.read_text()[-10000:])
        (OUT / f'{label}.json').write_text(json.dumps({'command': command, 'exit_code': result.returncode, 'log': log.name}, indent=2) + '\n')
        return result.returncode

if __name__ == '__main__':
    sys.exit(main())
