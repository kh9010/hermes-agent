"""Produce and seal Version 02 evidence. Run from the candidate root with the candidate .venv."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
VENV = ROOT / '.venv' / 'bin'
RUNTIME = ['agent/prompt_builder.py', 'gateway/authz_mixin.py', 'gateway/display_config.py',
           'gateway/platforms/whatsapp_common.py', 'gateway/run.py', 'gateway/run_busy.py',
           'gateway/run_turn.py', 'gateway/run_turn_runner.py', 'gateway/warning_notifications.py']
TESTS = ['tests/gateway/test_oct07_compatibility.py', 'tests/gateway/test_oct07_upgrade_contracts.py',
         'tests/agent/test_oct07_prompt_contracts.py', 'tests/gateway/test_oct07_chat_scope_propagation.py']
FOCUSED = TESTS + ['tests/gateway/test_display_config.py', 'tests/gateway/test_config_driven_access_policy.py',
                   'tests/gateway/test_whatsapp_group_gating.py']

def git(*a):
    return subprocess.check_output(['git', *a], cwd=ROOT).decode()

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

assert not (OUT / 'manifest.json').exists(), 'Version already sealed; make a new version'
assert sorted(git('diff', '--name-only').split()) == sorted(RUNTIME), git('diff', '--name-only')
results = {}
with tempfile.TemporaryDirectory(prefix='hermes-02-') as scratch:
    env = {'PATH': '/opt/homebrew/bin:/usr/bin:/bin', 'HOME': scratch, 'HERMES_HOME': f'{scratch}/.hermes'}
    Path(env['HERMES_HOME']).mkdir()
    def run(name, cmd, log):
        p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
        (OUT / log).write_text(p.stdout + p.stderr)
        results[name] = {'command': cmd, 'exit_code': p.returncode,
                         'summary': (p.stdout.strip().splitlines() or [''])[-1]}
        return p
    run('focused', [str(VENV / 'python'), '-m', 'pytest', '-q', '-rfs', '-p', 'no:cacheprovider', *FOCUSED], 'focused.log')
    run('ruff', [str(VENV / 'ruff'), 'check', *RUNTIME, *TESTS], 'ruff.log')
    (Path(env['HERMES_HOME']) / 'config.yaml').write_text(
        'plugins:\n  enabled:\n    - day-header\n    - hanuman-capture\n    - privacy-logging\n')
    run('plugins_compat', [str(VENV / 'hermes'), 'plugins', 'compat'], 'compat.log')
(OUT / 'candidate.patch').write_text(git('diff', '--binary'))
(OUT / 'candidate-diffstat.txt').write_text(git('diff', '--stat'))
(OUT / 'test-results.json').write_text(json.dumps(results, indent=2) + '\n')
for p in list(OUT.rglob('__pycache__')):
    shutil.rmtree(p)
files = sorted(p for p in OUT.rglob('*') if p.is_file())
manifest = {
    'version': 2,
    'release': git('rev-parse', 'HEAD').strip(),
    'candidate': {n: sha(ROOT / n) for n in RUNTIME + TESTS},
    'evidence': {str(p.relative_to(ROOT)): sha(p) for p in files},
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
for p in files + [OUT / 'manifest.json']:
    p.chmod(0o444)
OUT.chmod(0o555)
print(f"SEALED version 02: focused={results['focused']['summary']} ruff={results['ruff']['summary']} "
      f"compat={results['plugins_compat']['summary']}")
