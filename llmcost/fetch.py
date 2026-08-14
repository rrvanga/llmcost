"""Fetch and normalize LLM pricing data into llmcost's schema.

The primary source is LiteLLM's model_prices_and_context_window.json — the
community-standard machine-readable model metadata file. We normalize it into
a friendlier schema (USD per million tokens, human-readable capability flags)
and optionally merge any manual extra_providers.json entries.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
EXTRA_PATH = DATA_DIR / "extra_providers.json"
OUT_PATH = DATA_DIR / "prices.json"


def _num(x):
    """Return a float if the value is numeric, else None."""
    if isinstance(x, bool):  # bool is subclass of int; exclude it
        return None
    if isinstance(x, (int, float)):
        return float(x)
    return None


def _per_mtok(x):
    """Convert per-token USD to per-million-token USD."""
    n = _num(x)
    if n is None:
        return None
    return round(n * 1e6, 4)


def normalize(model: str, entry: dict) -> dict:
    return {
        "model": model,
        "provider": entry.get("litellm_provider") or "unknown",
        "input_usd_per_mtok": _per_mtok(entry.get("input_cost_per_token")),
        "output_usd_per_mtok": _per_mtok(entry.get("output_cost_per_token")),
        "max_input_tokens": entry.get("max_input_tokens"),
        "max_output_tokens": entry.get("max_output_tokens"),
        "mode": entry.get("mode") or "chat",
        "supports_vision": bool(entry.get("supports_vision")),
        "supports_function_calling": bool(entry.get("supports_function_calling")),
        "supports_reasoning": bool(entry.get("supports_reasoning")),
        "supports_prompt_caching": bool(entry.get("supports_prompt_caching")),
        "supports_web_search": bool(entry.get("supports_web_search")),
        "tpm": entry.get("tpm"),
        "rpm": entry.get("rpm"),
    }


def fetch_source() -> dict:
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "llmcost/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def build() -> dict:
    raw = fetch_source()
    models = []
    for name, entry in raw.items():
        if name == "sample_spec" or not isinstance(entry, dict):
            continue
        m = normalize(name, entry)
        # Keep anything with at least one useful signal (price or context size).
        if any(
            m[k] is not None
            for k in ("input_usd_per_mtok", "output_usd_per_mtok",
                      "max_input_tokens", "max_output_tokens")
        ):
            models.append(m)

    # Merge manual extras (gateways/vendors LiteLLM doesn't track).
    if EXTRA_PATH.exists():
        extra = json.loads(EXTRA_PATH.read_text())
        models.extend(extra.get("models", []))

    models.sort(key=lambda m: (m["provider"], m["model"]))

    out = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE_URL,
        "model_count": len(models),
        "models": models,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    result = build()
    print(f"wrote {result['model_count']} models to data/prices.json")
    sys.exit(0)
