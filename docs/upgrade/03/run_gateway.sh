#!/bin/bash
# Gateway suite only (re-run after a feishu optional-dep collection error aborted the first pass).
cd "$(dirname "$0")/../../.."
H=$(mktemp -d /tmp/hcand-home.XXXX)
env -i PATH=/usr/bin:/bin HOME=$H HERMES_HOME=$H/.hermes venv/bin/python -m pytest -q -p no:cacheprovider \
  --continue-on-collection-errors tests/gateway > docs/upgrade/03/broad-gateway.log 2>&1
echo "gateway(rerun) exit $?" >> docs/upgrade/03/broad-status.txt
rm -rf "$H"
