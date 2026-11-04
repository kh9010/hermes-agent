#!/bin/bash
# Broad upstream suites on the candidate, isolated HOME/HERMES_HOME, empty env. Writes logs beside this file.
cd "$(dirname "$0")/../../.."
D=docs/upgrade/03
for area in gateway cron plugins; do
  H=$(mktemp -d /tmp/hcand-home.XXXX)
  env -i PATH=/usr/bin:/bin HOME=$H HERMES_HOME=$H/.hermes venv/bin/python -m pytest -q -p no:cacheprovider --continue-on-collection-errors \
    tests/$area > $D/broad-$area.log 2>&1
  echo "$area exit $?" >> $D/broad-status.txt
  rm -rf "$H"
done
echo done >> $D/broad-status.txt
