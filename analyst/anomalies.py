"""Flag same-day performance drops against each group's own trailing baseline."""
from datetime import timedelta
from statistics import mean, pstdev

from .metrics import by_day


def detect(rows, as_of, metric="cpl", baseline_days=7, z_threshold=2.0, min_spend=25.0,
           key=lambda r: r.campaign, higher_is_worse=True):
    """Return groups whose `metric` on `as_of` deviates from their trailing baseline.

    A z-score on a small, noisy baseline overreacts, so each flag also requires a minimum
    relative change (25%) and enough spend on the day to matter.
    """
    flags = []
    for grp, days in by_day(rows, key).items():
        today = days.get(as_of)
        if not today or today["spend"] < min_spend or today[metric] is None:
            continue
        hist = [days[as_of - timedelta(days=i)][metric]
                for i in range(1, baseline_days + 1)
                if (as_of - timedelta(days=i)) in days and days[as_of - timedelta(days=i)][metric] is not None]
        if len(hist) < 3:
            continue
        mu, sd = mean(hist), pstdev(hist) or 1e-9
        z = (today[metric] - mu) / sd
        change = (today[metric] - mu) / mu if mu else 0
        worse = z > z_threshold if higher_is_worse else z < -z_threshold
        if worse and abs(change) >= 0.25:
            flags.append({
                "group": " / ".join(grp) if isinstance(grp, tuple) else grp,
                "metric": metric,
                "today": round(today[metric], 2),
                "baseline": round(mu, 2),
                "change_pct": round(change * 100, 1),
                "z": round(z, 2),
                "spend_today": today["spend"],
            })
    return sorted(flags, key=lambda f: -abs(f["z"]))
