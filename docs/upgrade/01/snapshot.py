"""Read-only Git evidence collector; writes only beside this script."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent
OLD = '130c0a8f7aa40fc407eea99656d7c3bce8ba4222'
BASE = 'd63f996a757f6255fc1454239616ab4b4435e0f5'
COMMITS = ['c7aef3e9e4', '9d374d4bba', '82da021cf7', '7b2cd84bbd', 'b53933bc0f', '27a221ce5f']
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def main():
    patches = OUT / 'old-local'
    patches.mkdir(exist_ok=True)
    for commit in COMMITS:
        (patches / f'{commit}.patch').write_bytes(git('show', '--format=fuller', '--binary', commit))
    (patches / 'combined.patch').write_bytes(git('diff', '--binary', BASE, OLD))
    files = git('diff', '--name-only', BASE, OLD).decode().splitlines()
    for name in files:
        target = patches / 'files' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git('show', f'{OLD}:{name}'))
    info = {'old_live': OLD, 'old_upstream_base': BASE, 'candidate_release': git('rev-parse', 'HEAD').decode().strip(),
            'old_local_files': files, 'old_local_commits': COMMITS,
            'upstream_breadth': git('diff', '--no-renames', '--shortstat', BASE, 'HEAD').decode().strip(),
            'upstream_commit_count': int(git('rev-list', '--count', f'{BASE}..HEAD'))}
    (OUT / 'source-inventory.json').write_text(json.dumps(info, indent=2) + '\n')
    sums = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(patches.rglob('*')) if p.is_file()}
    (OUT / 'snapshot-sha256.json').write_text(json.dumps(sums, indent=2) + '\n')
    print(json.dumps(info, indent=2))

if __name__ == '__main__':
    main()
