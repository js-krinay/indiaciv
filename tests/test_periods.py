import shutil
import subprocess
import unittest

from pipeline.check import Report, check_periods


class PeriodTest(unittest.TestCase):
    def test_rejects_hidden_or_undated_older_observations(self):
        for record in (
            {"period": "Census 2011 (Jan 2026) · Jan 2026"},
            {"metrics": {"example": {"value": 1, "vintage": "Census 2011"}}},
            {"vintage": "older", "period": "Published 2024; observation year unknown"},
            {"vintage": "older", "period": "Released in 2024"},
        ):
            with self.subTest(record=record):
                report = Report(quiet=True)
                check_periods(report, {"nation.json": {"profile": {}}, "sample.json": record})
                self.assertTrue(report.failed)

    @unittest.skipUnless(shutil.which("node"), "Node is needed to test browser formatting")
    def test_period_label(self):
        subprocess.run(["node", "tests/period_label.mjs"], check=True)

    def test_older_period_requires_a_marker_and_an_explicit_year(self):
        for record, fails in (
            ({"vintage": "older", "period": "Census 2011"}, False),
            ({"vintage": "older", "period": "NFHS-5 (2019-21)"}, False),
            ({"vintage": "older", "period": "FY 2024-25 (1 Apr 2024 – 31 Mar 2025)"}, False),
            ({"vintage": "older", "period": "Sixth Economic Census (January 2013 – April 2014)"}, False),
            ({"vintage": "older", "period": "FY 2024-25 (1 Apr 2023 – 31 Mar 2025)"}, True),
            ({"vintage": "older", "period": "FY 2024-25 (1 Apr 2024 – 31 Mar 2026)"}, True),
            ({"period": "Census 2011"}, True),
            ({"vintage": "older", "period": "Census"}, True),
            ({"vintage": "older", "period": None}, True),
            ({"vintage": "older"}, True),
            ({"vintage": "older", "period": "2026–2030"}, True),
            ({"vintage": "older", "period": "2025–27"}, True),
            ({"vintage": "older", "period": "Census 2011", "growth_period": "2011"}, True),
        ):
            with self.subTest(record=record):
                report = Report(quiet=True)
                check_periods(report, {"nation.json": {"profile": {}}, "example.json": [record]})
                self.assertEqual(report.failed, fails)

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
