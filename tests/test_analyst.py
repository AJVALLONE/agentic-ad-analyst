import unittest
from datetime import date, timedelta

from analyst import agent, anomalies, metrics
from analyst.data import Row


def row(day, leads, spend=100.0, brand="B", campaign="C", hook="H"):
    return Row(day=day, platform="meta", brand=brand, campaign=campaign, ad="a", hook=hook,
               spend=spend, impressions=10000, clicks=200, leads=leads, revenue=leads * 20.0)


class MetricsTest(unittest.TestCase):
    def test_summary_ratios(self):
        m = metrics.summarize([row(date(2026, 1, 1), leads=10)])
        self.assertAlmostEqual(m["cpl"], 10.0)
        self.assertAlmostEqual(m["ctr"], 0.02)
        self.assertAlmostEqual(m["roas"], 2.0)

    def test_zero_division_is_none(self):
        m = metrics.summarize([row(date(2026, 1, 1), leads=0)])
        self.assertIsNone(m["cpl"])

    def test_hook_leaderboard_respects_min_spend(self):
        d = date(2026, 1, 1)
        rows = [row(d, 10, spend=100, hook="good"), row(d, 1, spend=10, hook="tiny")]
        ranked = [h for h, _ in metrics.hook_leaderboard(rows, min_spend=50)]
        self.assertEqual(ranked, ["good"])


class AnomalyTest(unittest.TestCase):
    def setUp(self):
        self.day = date(2026, 1, 10)
        self.rows = [row(self.day - timedelta(days=i), leads=10 + (i % 2)) for i in range(1, 8)]

    def test_flags_cpl_spike(self):
        rows = self.rows + [row(self.day, leads=3)]  # CPL roughly triples
        flags = anomalies.detect(rows, self.day)
        self.assertEqual(len(flags), 1)
        self.assertGreater(flags[0]["change_pct"], 25)

    def test_ignores_normal_day(self):
        rows = self.rows + [row(self.day, leads=10)]
        self.assertEqual(anomalies.detect(rows, self.day), [])

    def test_ignores_low_spend_day(self):
        rows = self.rows + [row(self.day, leads=1, spend=10)]
        self.assertEqual(anomalies.detect(rows, self.day), [])


class AgentTest(unittest.TestCase):
    def test_template_brief_without_api_key(self):
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        d = date(2026, 1, 1)
        rows = [row(d, 10)]
        facts = agent.build_facts(d, metrics.summarize(rows), metrics.group(rows, lambda r: r.brand), [],
                                  metrics.hook_leaderboard(rows))
        brief, engine = agent.write_brief(facts)
        self.assertEqual(engine, "template")
        self.assertIn("Budget actions", brief)


if __name__ == "__main__":
    unittest.main()
