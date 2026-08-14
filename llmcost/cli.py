"""llmcost CLI — query LLM API pricing and rate limits from the local dataset."""
import argparse
import sys
from collections import Counter
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "prices.json"

COLS = [
    ("model", 30), ("provider", 14), ("in $/M", 9),
    ("out $/M", 9), ("ctx", 10), ("tpm", 9), ("rpm", 7),
]


def load() -> dict:
    if not DATA_PATH.exists():
        print(f"error: {DATA_PATH} not found — run `python -m llmcost.fetch` first",
              file=sys.stderr)
        sys.exit(1)
    return __import__("json").loads(DATA_PATH.read_text())


def _money(x):
    return "—" if x is None else f"{x:,.2f}"


def _int(x):
    return "—" if x is None else f"{x:,}"


def _fmt_cell(text, width):
    text = str(text)[: width - 1]
    return text + " " * (width - len(text))


def print_table(models):
    header = "".join(_fmt_cell(name, w) for name, w in COLS)
    print(header)
    print("-" * len(header))
    for m in models:
        row = [
            m["model"][:COLS[0][1]],
            m["provider"][:COLS[1][1]],
            _money(m["input_usd_per_mtok"]),
            _money(m["output_usd_per_mtok"]),
            _int(m["max_input_tokens"]),
            _int(m["tpm"]),
            _int(m["rpm"]),
        ]
        print("".join(_fmt_cell(c, w) for c, (_, w) in zip(row, COLS)))
    print(f"\n{len(models)} model(s)")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="llmcost",
        description="Query LLM API pricing, context windows, and rate limits.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("providers", help="list providers and their model counts")

    ls = sub.add_parser("list", help="list models (filterable)")
    ls.add_argument("--provider", help="filter by provider tag")
    ls.add_argument("--vision", action="store_true", help="vision-capable only")
    ls.add_argument("--reasoning", action="store_true", help="reasoning-capable only")
    ls.add_argument("--limit", type=int, help="cap the number of rows")

    find = sub.add_parser("find", help="search by model or provider substring")
    find.add_argument("query")

    cmp_ = sub.add_parser("compare", help="compare specific models")
    cmp_.add_argument("models", nargs="+", help="model ids or substrings")

    args = p.parse_args(argv)
    data = load()
    models = data["models"]

    if args.cmd == "providers":
        counts = Counter(m["provider"] for m in models)
        for prov, n in sorted(counts.items()):
            print(f"{prov:22s} {n:5d}")
        return 0

    if args.cmd == "list":
        selected = models
        if args.provider:
            selected = [m for m in selected if m["provider"] == args.provider]
        if args.vision:
            selected = [m for m in selected if m["supports_vision"]]
        if args.reasoning:
            selected = [m for m in selected if m["supports_reasoning"]]
        if args.limit:
            selected = selected[: args.limit]
        print_table(selected)
        return 0

    if args.cmd == "find":
        q = args.query.lower()
        selected = [
            m for m in models
            if q in m["model"].lower() or q in m["provider"].lower()
        ]
        print_table(selected)
        return 0

    if args.cmd == "compare":
        wanted = [x.lower() for x in args.models]
        selected = []
        for m in models:
            key = m["model"].lower()
            if any(w == key or w in key for w in wanted):
                selected.append(m)
        # Fall back to showing every distinct match, de-duplicated by model id.
        seen, dedup = set(), []
        for m in selected:
            if m["model"] not in seen:
                seen.add(m["model"])
                dedup.append(m)
        if not dedup:
            print("no matches for: " + ", ".join(args.models))
            return 1
        print_table(dedup)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
