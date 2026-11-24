"""Generate 30 days of synthetic multi-brand, multi-platform ad data.

The data is synthetic so the repo can be shared publicly. It includes realistic noise,
weekly seasonality, a fatiguing creative, and an injected CPL spike on the final day
so the anomaly detector has something real to find.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
BRANDS = ["Brand A", "Brand B", "Brand C"]
PLATFORMS = ["meta", "google", "tiktok"]
HOOKS = ["Problem-first question", "Founder story", "Before/after proof", "Myth bust", "Price anchor"]
HOOK_QUALITY = {"Problem-first question": 1.25, "Founder story": 1.0, "Before/after proof": 1.35,
                "Myth bust": 0.9, "Price anchor": 0.75}
START = date(2026, 10, 25)
DAYS = 30


def main(out="sample_data/ad_performance.csv"):
    rows = []
    for d in range(DAYS):
        day = START + timedelta(days=d)
        weekend = day.weekday() >= 5
        for brand in BRANDS:
            for platform in PLATFORMS:
                for i, hook in enumerate(HOOKS[:3] if platform == "google" else HOOKS):
                    spend = random.uniform(40, 120) * (0.85 if weekend else 1.0)
                    cpm = {"meta": 14, "google": 22, "tiktok": 9}[platform] * random.uniform(0.85, 1.15)
                    imps = int(spend / cpm * 1000)
                    ctr = 0.012 * HOOK_QUALITY[hook] * random.uniform(0.8, 1.2)
                    if hook == "Myth bust":  # creative fatigue over the month
                        ctr *= max(0.45, 1 - d * 0.02)
                    clicks = int(imps * ctr)
                    cvr = 0.09 * random.uniform(0.75, 1.25)
                    leads = int(clicks * cvr)
                    if d == DAYS - 1 and brand == "Brand B" and platform == "meta":
                        leads = max(1, int(leads * 0.4))  # injected drop on the last day
                    revenue = leads * random.uniform(18, 26)
                    rows.append({
                        "date": day.isoformat(), "platform": platform, "brand": brand,
                        "campaign": f"{brand} - {platform.title()} - Prospecting",
                        "ad": f"{brand[:1]}{platform[:2]}-{i}", "hook": hook,
                        "spend": round(spend, 2), "impressions": imps, "clicks": clicks,
                        "leads": leads, "revenue": round(revenue, 2),
                    })
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
