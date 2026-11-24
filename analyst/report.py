"""Render the daily brief as Markdown."""


def fmt_money(x):
    return f"${x:,.2f}" if x is not None else "n/a"


def fmt_pct(x):
    return f"{x * 100:.2f}%" if x is not None else "n/a"


def render(as_of, totals, by_brand, flags, hooks, brief, engine):
    out = [f"# Daily performance brief: {as_of.isoformat()}", ""]
    out.append(f"_Brief written by: {engine}. All figures computed in Python, not by the model._\n")
    out.append("## Portfolio, last 7 days\n")
    out.append("| Spend | Leads | CPL | CTR | ROAS |")
    out.append("| --- | --- | --- | --- | --- |")
    t = totals
    out.append(f"| {fmt_money(t['spend'])} | {t['leads']:,} | {fmt_money(t['cpl'])} | {fmt_pct(t['ctr'])} | "
               f"{(t['roas'] or 0):.2f}x |\n")
    out.append("## By brand, last 7 days\n")
    out.append("| Brand | Spend | Leads | CPL | ROAS |")
    out.append("| --- | --- | --- | --- | --- |")
    for b, m in sorted(by_brand.items()):
        out.append(f"| {b} | {fmt_money(m['spend'])} | {m['leads']:,} | {fmt_money(m['cpl'])} | {(m['roas'] or 0):.2f}x |")
    out.append("\n## Anomalies today\n")
    if flags:
        out.append("| Group | Metric | Today | 7-day baseline | Change | z |")
        out.append("| --- | --- | --- | --- | --- | --- |")
        for f in flags:
            out.append(f"| {f['group']} | {f['metric'].upper()} | {f['today']} | {f['baseline']} | {f['change_pct']:+}% | {f['z']} |")
    else:
        out.append("None.")
    out.append("\n## Hook leaderboard (by CPL, min $50 spend)\n")
    out.append("| Hook | Spend | Leads | CPL |")
    out.append("| --- | --- | --- | --- |")
    for h, m in hooks:
        out.append(f"| {h} | {fmt_money(m['spend'])} | {m['leads']} | {fmt_money(m['cpl'])} |")
    out.append("\n## Brief\n")
    out.append(brief)
    return "\n".join(out) + "\n"
