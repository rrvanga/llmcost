# llmcost

**Query LLM API pricing, context windows, and rate limits from a clean, open, machine-readable dataset.**

Every provider prices differently, caps contexts differently, and hides rate limits in docs pages that change weekly. `llmcost` is one JSON file + one CLI that answers the questions you actually ask when picking a model:

- *"What's the cheapest vision model right now?"*
- *"How much will 1M output tokens cost on this model?"*
- *"What's the context window on the latest DeepSeek?"*
- *"Which providers even offer reasoning models?"*

## Why

Pricing and limits change constantly, and they're scattered across every vendor's docs. `llmcost` normalizes ~1,500 models into a single schema and re-checks it daily. The data is a plain JSON file, so you can use it with `jq`, Python, a spreadsheet, or anything else — no SDK, no vendor lock-in.

## Install

```bash
git clone https://github.com/rrvanga/llmcost
cd llmcost
pip install -e .
```

Requires Python 3.9+. The CLI has **zero dependencies** — it reads the bundled JSON.

## Usage

```bash
# List all providers, sorted by model count
llmcost providers

# List every model from a provider
llmcost list --provider anthropic

# List only vision-capable models
llmcost list --vision

# List only reasoning models
llmcost list --reasoning

# Search by name or provider substring
llmcost find deepseek

# Compare specific models side by side
llmcost compare gpt-4o claude-sonnet-4-20250514 gemini-2.5-pro
```

Output is a fixed-width table: `model`, `provider`, `$ / 1M input`, `$ / 1M output`, `context`, `tpm`, `rpm`.

## The data

Everything lives in [`data/prices.json`](data/prices.json):

```json
{
  "schema_version": 1,
  "generated_at": "2026-08-14T00:00:00+00:00",
  "source": "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json",
  "model_count": 1500,
  "models": [
    {
      "model": "deepseek-v4-flash",
      "provider": "deepseek",
      "input_usd_per_mtok": 0.14,
      "output_usd_per_mtok": 0.28,
      "max_input_tokens": 131072,
      "max_output_tokens": 32768,
      "mode": "chat",
      "supports_vision": false,
      "supports_function_calling": true,
      "supports_reasoning": false,
      "supports_prompt_caching": false,
      "supports_web_search": false,
      "tpm": null,
      "rpm": null
    }
  ]
}
```

**Pricing is in USD per million tokens.** The raw source stores per-token values; `llmcost` multiplies by 1e6 so the numbers are human-readable.

### Schema fields

| Field | Meaning |
|---|---|
| `model` | Canonical model id (as providers/litellm name it) |
| `provider` | Provider tag (openai, anthropic, deepseek, gemini, …) |
| `input_usd_per_mtok` | Input price, USD per 1M tokens (`null` if not published) |
| `output_usd_per_mtok` | Output price, USD per 1M tokens |
| `max_input_tokens` | Context window (input) |
| `max_output_tokens` | Max output tokens per response |
| `mode` | `chat`, `embedding`, `image_generation`, `audio_transcription`, … |
| `supports_*` | Capability flags |
| `tpm` / `rpm` | Tokens/requests per minute (only where the vendor publishes them) |

## Where the data comes from

The primary source is [LiteLLM's `model_prices_and_context_window.json`](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json) — the de-facto community standard for model metadata, maintained by a large contributor base. `llmcost` fetches it, normalizes it into the schema above, and commits any change.

That means **the data is crowd-sourced upstream and re-verified daily**, not hand-typed here.

### Adding a provider not in the upstream source

Drop a file at `data/extra_providers.json` with the same model schema, and the fetcher will merge it in. Use this for gateways or vendors LiteLLM doesn't track yet (e.g. free rate-limited gateways like OpenCode Go).

## How it updates

A cron job runs [`scripts/update.sh`](scripts/update.sh) daily. It re-fetches, normalizes, and:

- **commits + pushes** only if pricing/limits/context actually changed, and
- **stays silent** otherwise (no empty commits).

You can run it manually:

```bash
./scripts/update.sh
```

## Roadmap

- [ ] `llmcost watch` — alert you when a tracked model's price or limit changes
- [ ] Historical price log (`data/history/`) for price-change analysis
- [ ] Per-model rate-limit detail page for the big five providers

## License

MIT — see [LICENSE](LICENSE).
