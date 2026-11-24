"""Turn computed facts into a decision brief with Claude.

The model never sees raw rows and never does arithmetic. It receives numbers computed in
Python and is asked to explain, prioritise, and propose tests. That split keeps the output
checkable: every figure in the brief traces back to metrics.py or anomalies.py.

Uses the Anthropic Messages API over plain HTTPS (no SDK dependency). Without an
ANTHROPIC_API_KEY it falls back to a deterministic template so the pipeline still runs.
"""
import json
import os
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("ANALYST_MODEL", "claude-sonnet-4-5")

SYSTEM = (
    "You are a senior performance marketing analyst. You receive pre-computed metrics. "
    "Do not recompute or invent numbers; quote only figures provided. Write a short brief with: "
    "1) what changed and the most likely cause, 2) budget actions (scale / hold / cut) with the "
    "figure that justifies each, 3) two creative test ideas built from the winning hooks, each "
    "with a hypothesis, the single variable changed, and a kill rule. Be direct. No filler."
)


def build_facts(as_of, totals, by_brand, flags, hooks):
    return {
        "as_of": as_of.isoformat(),
        "portfolio_totals_last_7d": totals,
        "by_brand_last_7d": by_brand,
        "anomalies_today": flags,
        "top_hooks_by_cpl": [{"hook": h, **m} for h, m in hooks[:3]],
        "worst_hooks_by_cpl": [{"hook": h, **m} for h, m in hooks[-2:]],
    }


def call_claude(facts, api_key):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1200,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": "Metrics (JSON):\n" + json.dumps(facts, default=str)}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    return "".join(block.get("text", "") for block in data.get("content", []))


def template_brief(facts):
    lines = ["**What changed**"]
    if facts["anomalies_today"]:
        for f in facts["anomalies_today"]:
            lines.append(f"- {f['group']}: {f['metric'].upper()} {f['today']} vs {f['baseline']} baseline "
                         f"({f['change_pct']:+}%). Check creative fatigue and audience overlap first.")
    else:
        lines.append("- No groups outside their normal range today.")
    lines.append("\n**Budget actions**")
    for brand, m in sorted(facts["by_brand_last_7d"].items(), key=lambda kv: (kv[1]["cpl"] or 1e9)):
        action = "Scale" if (m["roas"] or 0) >= 2.5 else "Hold" if (m["roas"] or 0) >= 1.5 else "Cut"
        cpl = f"${m['cpl']:.2f}" if m["cpl"] else "n/a"
        roas = f"{m['roas']:.2f}x" if m["roas"] else "n/a"
        lines.append(f"- {action} {brand}: CPL {cpl}, ROAS {roas}")
    lines.append("\n**Creative tests**")
    for h in facts["top_hooks_by_cpl"][:2]:
        lines.append(f"- Port the '{h['hook']}' hook (CPL ${h['cpl']:.2f}) to a new format. Variable: format only. "
                     "Kill if CPL is 30% above control after $150 spend.")
    return "\n".join(lines)


def write_brief(facts):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            return call_claude(facts, key), "claude"
        except Exception as exc:  # network or API failure must not break the daily run
            return template_brief(facts) + f"\n\n_(LLM call failed: {exc}; template fallback used)_", "template"
    return template_brief(facts), "template"
