#!/usr/bin/env bash
# Daily update: re-fetch pricing, normalize, and commit ONLY if content changed.
# Silent (exit 0, no output) when nothing changed — so the cron watchdog stays quiet.
set -euo pipefail
cd "$(dirname "$0")/.."

out="$(python3 -m llmcost.fetch)"

# Compare ignoring the generated_at timestamp (which legitimately changes every run).
old="$(git show HEAD:data/prices.json 2>/dev/null | grep -v '"generated_at"' || true)"
new="$(grep -v '"generated_at"' data/prices.json || true)"

if [ "$old" = "$new" ]; then
    exit 0
fi

git add data/prices.json
git commit -q -m "data: update model pricing ($(date +%Y-%m-%d))"
git push -q
echo "$out"
