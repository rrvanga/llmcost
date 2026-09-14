#!/usr/bin/env bash
# Daily update: re-fetch pricing, normalize, and commit ONLY if content changed.
# Silent (exit 0, no output) when nothing changed — so the cron watchdog stays quiet.
set -euo pipefail
cd "$(dirname "$0")/.."

# Retry transient network failures (DNS/connectivity blips) up to 3 times.
# Observed 2026-09-11: single urllib fetch died on a temporary DNS resolution
# error and killed the whole cron run. Bounded retries absorb such blips while
# still failing loudly (exit 1) if the source is genuinely unreachable.
attempt=0
while :; do
    if out="$(python3 -m llmcost.fetch)"; then
        break
    fi
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 3 ]; then
        echo "llmcost.fetch failed after $attempt attempts" >&2
        exit 1
    fi
    echo "llmcost.fetch failed (attempt $attempt); retrying in $((attempt * 5))s..." >&2
    sleep "$((attempt * 5))"
done

# Compare ignoring the generated_at timestamp (which legitimately changes every run).
old="$(git show HEAD:data/prices.json 2>/dev/null | grep -v '"generated_at"' || true)"
new="$(grep -v '"generated_at"' data/prices.json || true)"

if [ "$old" = "$new" ]; then
    git restore data/prices.json
    exit 0
fi

git add data/prices.json
git commit -q -m "data: update model pricing ($(date +%Y-%m-%d))"
git push -q
echo "$out"
