"""Load daily ad performance rows from CSV (or an export from Meta / Google / TikTok)."""
import csv
from dataclasses import dataclass
from datetime import date


@dataclass
class Row:
    day: date
    platform: str
    brand: str
    campaign: str
    ad: str
    hook: str
    spend: float
    impressions: int
    clicks: int
    leads: int
    revenue: float


def load_csv(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append(Row(
                day=date.fromisoformat(r["date"]),
                platform=r["platform"],
                brand=r["brand"],
                campaign=r["campaign"],
                ad=r["ad"],
                hook=r["hook"],
                spend=float(r["spend"]),
                impressions=int(r["impressions"]),
                clicks=int(r["clicks"]),
                leads=int(r["leads"]),
                revenue=float(r["revenue"]),
            ))
    return rows
