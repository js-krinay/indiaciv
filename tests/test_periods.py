import unittest

from pipeline.check import Report, check_periods


class PeriodTest(unittest.TestCase):
    def test_accepts_2026_and_reporting_years_ending_in_2026(self):
        for period in ("2026", "mid-2026", "Projected for mid-2026", "Jan–Oct 2026", "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)",
                       "1 Mar 2025 – 1 Mar 2026", "Crop year 2025-26 (1 Jul 2025 – 30 Jun 2026)"):
            with self.subTest(period=period):
                report = Report(quiet=True)
                check_periods(report, {"example.json": {"period": period}})
                self.assertFalse(report.failed)

    def test_composite_periods_need_every_part_to_qualify(self):
        good = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) · GEM snapshots (Aug–Sep 2026) · 27 Nov 2026 wonders"
        for period, fails in ((good, False), ("FY 2025-26 · 2026–30 average", True)):
            with self.subTest(period=period):
                report = Report(quiet=True)
                check_periods(report, {"example.json": {"period": period}})
                self.assertEqual(report.failed, fails)

    def test_rejects_a_multiyear_projection(self):
        report = Report(quiet=True)
        check_periods(report, {"example.json": [{"period": "2026–30"}]})
        self.assertTrue(report.failed)

    def test_rejects_legacy_growth_years_in_the_india_build(self):
        report = Report(quiet=True)
        check_periods(report, {"nation.json": {"profile": {}, "year": 2026},
                               "cities.json": [{"growth_years": [2021, 2026]}]})
        self.assertTrue(report.failed)
