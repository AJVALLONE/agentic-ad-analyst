"""CLI: python -m analyst --data sample_data/ad_performance.csv [--as-of YYYY-MM-DD]"""
import argparse
from datetime import date, timedelta
from pathlib import Path

from . import agent, anomalies, metrics, report
from .data import load_csv


def main(argv=None):
    p = argparse.ArgumentParser(description="Daily agentic ad performance brief")
    p.add_argument("--data", default="sample_data/ad_performance.csv")
    p.add_argument("--as-of", help="Day to analyse (defaults to the latest day in the data)")
    p.add_argument("--out", default="reports")
    args = p.parse_args(argv)

    rows = load_csv(args.data)
    as_of = date.fromisoformat(args.as_of) if args.as_of else max(r.day for r in rows)
    window = [r for r in rows if as_of - timedelta(days=6) <= r.day <= as_of]

    totals = metrics.summarize(window)
    by_brand = metrics.group(window, lambda r: r.brand)
    flags = anomalies.detect(rows, as_of)
    hooks = metrics.hook_leaderboard(window)

    facts = agent.build_facts(as_of, totals, by_brand, flags, hooks)
    brief, engine = agent.write_brief(facts)

    Path(args.out).mkdir(parents=True, exist_ok=True)
    path = Path(args.out) / f"brief-{as_of.isoformat()}.md"
    path.write_text(report.render(as_of, totals, by_brand, flags, hooks, brief, engine))
    print(f"Wrote {path} ({len(flags)} anomalies, engine={engine})")


if __name__ == "__main__":
    main()
