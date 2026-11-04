"""Aggregate exact recorded summaries; never infer green from a subprocess exit alone."""
from pathlib import Path
import json
import re

OUT = Path(__file__).parent
labels = ('red', 'red-prompt', 'focused-first', 'focused-final', 'bridge',
          'broader', 'broader-messaging', 'display-surfaces', 'baseline-environment', 'baseline-socket',
          'baseline-contracts', 'regression-final', 'regression-final-verified')
result = {}
for label in labels:
    meta = json.loads((OUT / f'{label}.json').read_text())
    text = (OUT / meta['log']).read_text()
    summary = re.findall(r'^=== Summary: (.+?) ===$', text, re.M)
    if not summary:
        summary = re.findall(r'^\d+ (?:passed|failed).+$', text, re.M)
    if label == 'bridge':
        summary = re.findall(r'^ℹ (?:tests|pass|fail|skipped) .+$', text, re.M)
    result[label] = {**meta, 'summary': summary,
        'failed_tests': sorted(set(re.findall(r'^FAILED (\S+)', text, re.M)))}
assert result['focused-final']['exit_code'] == 0
assert result['bridge']['exit_code'] == 0
assert result['broader-messaging']['failed_tests'] == result['baseline-environment']['failed_tests']
assert result['display-surfaces']['failed_tests'] == result['baseline-socket']['failed_tests']
result['candidate_specific_failures_in_selected_suites'] = []
result['unique_recorded_remaining_failures'] = sorted(set(
    result['broader-messaging']['failed_tests'] + result['display-surfaces']['failed_tests']))
assert result['regression-final-verified']['failed_tests'] == result['unique_recorded_remaining_failures']
(OUT / 'test-results.json').write_text(json.dumps(result, indent=2) + '\n')
for label in labels:
    print(label + ': ' + '; '.join(result[label]['summary']))
print('Unique remaining baseline-reproduced failures:', len(result['unique_recorded_remaining_failures']))
