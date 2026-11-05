// Read-only evidence verifier. Does not start Hermes, import Python, or contact a channel.
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root = path.dirname(fileURLToPath(import.meta.url));
const read = p => readFileSync(path.join(root, p));
const text = p => read(p).toString();
const json = p => JSON.parse(read(p));
const sha = p => createHash('sha256').update(read(p)).digest('hex');
const git = (...args) => execFileSync('git', args, {cwd: root, encoding: 'utf8'}).trim();

const R021 = 'f97608f178d1ffeca59860195ab7da295f7c8e5f';
const R022 = 'b200f5bc60e31588ba2cb60e288029c4a54ba5fa'; // upstream v0.22.7
const rail = json('versions.json');
assert.deepEqual(rail.map(v => v.n), [1, 2, 3]);
const latest = rail[rail.length - 1];
for (const v of rail) {
  assert.equal(v.base_commit, v.n < 3 ? R021 : R022);
  assert(existsSync(path.join(root, v.evidence)), `missing evidence ${v.evidence}`);
  assert(existsSync(path.join(root, v.requirements)));
  if (v.commit) git('cat-file', '-e', v.commit);
}
git('merge-base', '--is-ancestor', R022, 'HEAD');
console.log(`PASS rail: versions 01-02 on 0.21.5, 03 on v0.22.7 (ancestor of HEAD); latest "${latest.title}" (${latest.status})`);

// Evidence is sealed by hash (file modes do not survive git, so 01/02's read-only seal is checked by content).
for (const v of rail) {
  const manifest = json(v.evidence);
  for (const [p, hash] of Object.entries(manifest.evidence)) assert.equal(sha(p), hash, `evidence changed: ${p}`);
}
const m3 = json(latest.evidence);
for (const [p, hash] of Object.entries(m3.candidate)) assert.equal(sha(p), hash, `runtime/test file changed since 03: ${p}`);
assert.equal(Object.keys(m3.candidate).length, 15);
console.log('PASS integrity: 01-03 evidence matches its manifests; 11 runtime + 4 test files match 03');

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
assert.match(r1['regression-final-verified'].summary[0], /^122 files, 1351 tests passed, 9 failed, 6 skipped /);
const r2 = json('docs/upgrade/02/test-results.json');
assert.match(r2.focused.summary, /^111 passed/);
console.log('PASS history (01/02): 0.21.5 differential and focused evidence intact');

const d3 = 'docs/upgrade/03/';
assert.match(text(d3 + 'requirements-pristine.log'), /^26 failed, 9 passed/);
assert.match(text(d3 + 'requirements-candidate.log'), /^35 passed/);
const mut = text(d3 + 'mutation.log').trim().split('\n');
assert.equal(mut.filter(l => /^\[M[1-6] .*\] \d+ failed/.test(l)).length, 6, 'M1-M6 must each go red');
assert.equal(mut.filter(l => /^\[M[78] \((unpinned|unpinned, known)/.test(l)).length, 2);
assert.match(mut.at(-1), /^\[restored\] 35 passed/);
console.log('PASS requirements (03): 26/35 red on pristine v0.22.7, 35/35 green on 03; M1-M6 red when reverted, M7/M8 named unpinned');

assert.match(text(d3 + 'focused.log'), /^113 passed/);
assert.match(text(d3 + 'hermes-kmini.log'), /^6\d\d passed/);
assert(!/failed/.test(text(d3 + 'hermes-kmini.log')));
assert.match(text(d3 + 'bridge.log'), /ℹ pass 18\nℹ fail 0/);
const ruff = text(d3 + 'ruff.log');
assert(!/candidate=[1-9]/.test(ruff), 'ruff: a modified file gained findings');
assert.match(ruff, /All checks passed/);
const cfg = text(d3 + 'config-step-diff.txt');
assert.deepEqual(cfg.split('\n').filter(l => /^[<>] /.test(l)),
  ['< _config_version: 46', '> _config_version: 52', '<     model: qwen3.6:27b', '>     model: gemma4:26b', '<       - qwen3.6:27b']);
console.log('PASS focused (03): 113 Python tests; hermes-kmini suite on the candidate venv; 18 bridge tests; ruff no new findings; config step = stamp + qwen3.6:27b retirement only');

const diff = text(d3 + 'broad-differential.txt');
for (const area of ['gateway', 'cron', 'plugins']) assert.match(diff, new RegExp(`^${area}: .*candidate-only failures: 0$`, 'm'), `broad ${area}`);
console.log('PASS broad (03): tests/gateway, tests/cron, tests/plugins; every failure reproduces on pristine v0.22.7');
execFileSync('git', ['diff', '--check', R022, 'HEAD', '--', '.', ':!docs'], {cwd: root});
console.log('PASS hygiene: git diff --check clean on code paths');
console.log(`STATUS deployment: ${latest.status}`);
