"""Aggregate rows into the metrics a growth team actually decides on."""
from collections import defaultdict


def safe_div(a, b):
    return a / b if b else None


def summarize(rows):
    spend = sum(r.spend for r in rows)
    imps = sum(r.impressions for r in rows)
    clicks = sum(r.clicks for r in rows)
    leads = sum(r.leads for r in rows)
    revenue = sum(r.revenue for r in rows)
    return {
        "spend": round(spend, 2),
        "impressions": imps,
        "clicks": clicks,
        "leads": leads,
        "revenue": round(revenue, 2),
        "ctr": safe_div(clicks, imps),
        "cvr": safe_div(leads, clicks),
        "cpl": safe_div(spend, leads),
        "roas": safe_div(revenue, spend),
    }


def group(rows, key):
    buckets = defaultdict(list)
    for r in rows:
        buckets[key(r)].append(r)
    return {k: summarize(v) for k, v in buckets.items()}


def by_day(rows, key):
    """{group: {day: summary}} for time-series checks."""
    out = defaultdict(lambda: defaultdict(list))
    for r in rows:
        out[key(r)][r.day].append(r)
    return {g: {d: summarize(v) for d, v in days.items()} for g, days in out.items()}


def hook_leaderboard(rows, min_spend=50.0):
    """Rank creative hooks by cost per lead, ignoring hooks without enough spend to judge."""
    hooks = group(rows, lambda r: r.hook)
    ranked = [(h, m) for h, m in hooks.items() if m["spend"] >= min_spend and m["cpl"] is not None]
    return sorted(ranked, key=lambda x: x[1]["cpl"])
