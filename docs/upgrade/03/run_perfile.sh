#!/bin/bash
# Re-run each file that failed in the single-process gateway run in its OWN process (ulimit -n 8192):
# the single process hit EMFILE (macOS default 256 fds). Usage: run_perfile.sh <tree> <listfile> <out>
if [ "${1:-}" = --one ]; then   # worker: --one <tree> <out> <file>
  tree=$2; out=$3; f=$4; H=$(mktemp -d /tmp/hpf.XXXX); cd "$tree"
  r=$(env -i PATH=/usr/bin:/bin HOME=$H HERMES_HOME=$H/.hermes "$HOME/Dev/hermes-candidate-0.22.x/venv/bin/python" -B -m pytest -q -p no:cacheprovider -rfE "$f" 2>&1)
  echo "$r" | grep -E "^(FAILED|ERROR) " | sed -E "s/ - .*//" >> "$out.ids"
  echo "$f :: $(echo "$r" | tail -1)" >> "$out"
  rm -rf "$H"; exit 0
fi
tree=$1; list=$2; out=$3
ulimit -n 8192
: > "$out"; : > "$out.ids"
xargs -P 6 -n 1 "$0" --one "$tree" "$out" < "$list"
