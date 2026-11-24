# Agentic Ad Analyst

A daily performance analyst for multi-brand paid media: it computes the numbers, flags what broke, ranks creative hooks, and has Claude write the decision brief a growth team would act on.

This is a public, sanitized reference version of a pipeline I run in production across a 30-brand consumer portfolio. The production version pulls from the Google Ads, Meta, and TikTok APIs; this one runs on synthetic data so anyone can clone it and see the output in under a minute.

![tests](https://img.shields.io/badge/tests-unittest-blue) ![deps](https://img.shields.io/badge/dependencies-zero-brightgreen) ![python](https://img.shields.io/badge/python-3.10%2B-blue)

## Why it exists

Before: one person reviewing three ad platforms by hand every morning across 30 brands, catching drops a day or two late.
After: a scheduled job that has the brief waiting before the team starts, with same-day anomaly flags and the next round of creative tests already proposed. In production it does the analytical work of a 3–4 person team.

## The design choice that matters

**The model never does the math.** Python computes every metric, baseline, and anomaly. Claude only receives those computed facts and is asked to explain, prioritise, and propose tests. Every number in the brief traces back to code you can test, which is what makes an LLM-written report trustworthy enough to act on.

```
CSV / ad platform APIs
        │
        ▼
 metrics.py      ──  CPL, CTR, CVR, ROAS by brand, campaign, hook
 anomalies.py    ──  same-day drops vs each campaign's own 7-day baseline
        │              (z-score + minimum % change + minimum spend, to avoid noise)
        ▼
 agent.py        ──  computed facts → Claude → brief (scale / hold / cut, test ideas)
        │              falls back to a deterministic template with no API key
        ▼
 report.py       ──  Markdown brief (see reports/example-brief.md)
```

## Run it

```bash
git clone https://github.com/AJVALLONE/agentic-ad-analyst
cd agentic-ad-analyst
python sample_data/generate_sample.py      # writes the CSV: 30 days, 3 brands, 3 platforms, 5 hooks
python -m analyst                          # writes reports/brief-<date>.md
python -m unittest discover -s tests -v    # 7 tests
```

To have Claude write the brief instead of the template, copy `.env.example`, set `ANTHROPIC_API_KEY`, and export it. No SDK needed; it calls the Messages API over HTTPS with the standard library.

## What the sample data is designed to show

The synthetic data includes weekday/weekend seasonality, one creative hook that fatigues over the month, and an injected conversion drop on Brand B's Meta campaign on the final day. The pipeline should:

1. Flag Brand B Meta's cost-per-lead spike as today's anomaly.
2. Rank "Before/after proof" and "Problem-first question" as the strongest hooks and "Myth bust" as fatigued.
3. Propose scale / hold / cut actions with the figure behind each.

See [`reports/example-brief.md`](reports/example-brief.md) for the actual output.

## Scheduling

`.github/workflows/daily-brief.yml` runs the tests and generates the brief every morning at 6:15 AM ET, uploading it as a build artifact. In production the same step posts to Slack.

## Anomaly logic, briefly

A z-score alone overreacts on small, noisy baselines. A campaign is flagged only when all three hold:

- today's metric is more than 2 standard deviations worse than its trailing 7-day baseline,
- the change is at least 25%, and
- today's spend is high enough to matter (default $25).

## Project layout

```
analyst/
  data.py        load rows from CSV or platform exports
  metrics.py     summaries, grouping, hook leaderboard
  anomalies.py   baseline comparison and flagging
  agent.py       Claude call (stdlib HTTPS) + template fallback
  report.py      Markdown rendering
sample_data/     synthetic data generator (CSV is generated, not committed)
tests/           unittest suite
reports/         example output
```

## Author

Anthony Vallone, growth leader who builds his own tooling. [LinkedIn](https://linkedin.com/in/ajvallone) · [Portfolio](https://anthonyvallone.netlify.app)
