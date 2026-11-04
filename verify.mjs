// Read-only evidence verifier. Does not start Hermes, import Python, or contact a channel.
import assert from 'node:assert/strict';
import {readFileSync, statSync, existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root = path.dirname(fileURLToPath(import.meta.url));
const read = p => readFileSync(path.join(root, p));
const json = p => JSON.parse(read(p));
const sha = p => createHash('sha256').update(read(p)).digest('hex');
const git = (...args) => execFileSync('git', args, {cwd: root, encoding: 'utf8'}).trim();

const rail = json('versions.json');
assert.deepEqual(rail.map(v => v.n), [1, 2]);
const latest = rail[rail.length - 1];
for (const v of rail) {
  assert.equal(v.base_commit, 'f97608f178d1ffeca59860195ab7da295f7c8e5f');
  assert(existsSync(path.join(root, v.evidence)), `missing evidence ${v.evidence}`);
  assert(existsSync(path.join(root, v.requirements)));
  if (v.commit) git('cat-file', '-e', v.commit);
}
console.log(`PASS rail: versions 01-02 on release f97608f178; latest "${latest.title}" (${latest.status})`);

for (const v of rail) {
  const manifest = json(v.evidence);
  for (const [p, hash] of Object.entries(manifest.evidence)) {
    assert.equal(sha(p), hash, `evidence changed: ${p}`);
    assert.equal(statSync(path.join(root, p)).mode & 0o222, 0, `evidence writable: ${p}`);
  }
  assert.equal(statSync(path.join(root, v.evidence)).mode & 0o222, 0);
}
const m2 = json(latest.evidence);
for (const [p, hash] of Object.entries(m2.candidate)) assert.equal(sha(p), hash, `runtime/test file changed since 02: ${p}`);
assert.equal(Object.keys(m2.candidate).length, 13);
console.log('PASS integrity: 01 and 02 evidence sealed read-only; 9 runtime + 4 test files match 02');

const old = json('docs/upgrade/01/source-inventory.json');
assert.equal(old.old_local_files.length, 16);
assert.equal(old.old_local_commits.length, 6);
const oldHashes = json('docs/upgrade/01/snapshot-sha256.json');
for (const [p, hash] of Object.entries(oldHashes)) assert.equal(sha('docs/upgrade/01/' + p), hash);
console.log('PASS archive: 6 old local commits; 16 changed paths including tests');

const live = json('docs/upgrade/01/live-gate-sanitized.json');
assert.equal(live.group_policy, 'allowlist');
assert.equal(live.require_mention, true);
assert.equal(live.family_group_allowlisted, true);
assert.equal(live.local_address_classifier_enabled, false);
assert(!existsSync(path.join(root, 'gateway/platforms/whatsapp_local_address.py')));
console.log('PASS requirements: explicit family group + reply gate recorded; inferred addressing absent');

const r1 = json('docs/upgrade/01/test-results.json');
const final = r1['regression-final-verified'];
assert.equal(final.exit_code, 1);
assert.match(final.summary[0], /^122 files, 1351 tests passed, 9 failed, 6 skipped /);
const baseline = [...new Set([...r1['baseline-environment'].failed_tests, ...r1['baseline-socket'].failed_tests])].sort();
assert.deepEqual(final.failed_tests, baseline);
assert.equal(r1.bridge.exit_code, 0);
assert(r1.bridge.summary.includes('ℹ pass 19'));
console.log('PASS differential (01): 122-file run; all 9 failures reproduced with release bytes; 19 bridge tests');

const r2 = json('docs/upgrade/02/test-results.json');
assert.equal(r2.focused.exit_code, 0);
assert.match(r2.focused.summary, /^111 passed/);
assert.equal(r2.plugins_compat.exit_code, 0);
assert.match(read('docs/upgrade/02/compat.log').toString(), /No enabled plugin imports paths scheduled for removal/);
assert.equal(r2.ruff.exit_code, 0);
assert.match(read('docs/upgrade/02/ruff.log').toString(), /All checks passed/);
git('diff', '--check');
console.log('PASS focused evidence (02): 111 Python tests; kMini plugins compat clean; Ruff clean; git diff --check');
console.log(`STATUS deployment: ${latest.status}`);
