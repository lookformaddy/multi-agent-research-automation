#!/usr/bin/env bash
# End-to-end demo: run a research question through the CLI and the API.
set -euo pipefail

QUESTION="How can we reduce cloud infrastructure costs without hurting reliability?"

echo "== CLI =="
python -m research_system.cli "$QUESTION" --out out/ --trace

echo
echo "== API (expects the service on :8000) =="
curl -s -X POST localhost:8000/jobs \
  -H 'content-type: application/json' \
  -d "{\"question\": \"$QUESTION\"}" | head -c 400
echo
curl -s "localhost:8000/jobs/job-0001/report?format=md" | head -n 20
