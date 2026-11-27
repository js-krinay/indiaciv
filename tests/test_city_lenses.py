import unittest

from pipeline import check
from pipeline.build import lenses


class CityLensesTest(unittest.TestCase):
    def test_old_population_keeps_its_period_and_cannot_supply_2026_growth(self):
        older = {"period": "Census 2011", "vintage": "older"}
        cities = [{"population": 500_000, "projected_growth": 0.02, "footprint": [0, 2],
                   "provenance": {"population": older, "projected_growth": older}}]
        population, growth = lenses.city_lenses(cities, 4)
        self.assertEqual(growth["values"], [None] * 4)
        self.assertEqual(population["values"][2], 500_000)
        self.assertEqual(population["cell_details"]["2"], older)

    def test_checker_rejects_growth_values_from_older_city(self):
        cities = [{"id": "old", "footprint": [0], "population": 100,
                   "provenance": {"population": {"period": "Census 2011", "vintage": "older"}}}]
        report = check.Report(quiet=True)
        check.check_periods(report, {"cities.json": cities, "lenses.json": {
            "lenses": [{"id": "city_growth", "values": [0.02]}]}})
        self.assertTrue(report.failed)

    def test_city_values_cover_only_footprints(self):
        cities = [{"population": 500_000, "projected_growth": 0.02, "footprint": [0, 2]}]
        population, growth = lenses.city_lenses(cities, 4)
        self.assertEqual(population["values"], [500_000, None, 500_000, None])
        self.assertEqual(growth["values"], [0.02, None, 0.02, None])
        self.assertEqual(population["scale"], "log")
        self.assertEqual(growth["format"], "pct")

    def test_null_share_warns_for_districts_but_exempts_cities(self):
        report = check.Report(quiet=True)
        check.quality_lens_nulls(report, {"owner": [0, 0, -1], "n": 3}, {"lenses": [
            {"id": "city_population", "group": "cities", "values": [500_000, None, None]},
            {"id": "density", "group": "people", "values": [500, None, None]},
        ]})
        self.assertEqual([level for level, _ in report.lines], ["WARN", "NOTE"])
        self.assertIn("lens density", report.lines[0][1])
        self.assertIn("1 lens", report.lines[1][1])

    def test_known_coverage_groups_keep_warn_for_a_larger_gap(self):
        report = check.Report(quiet=True)
        check.quality_lens_nulls(report, {"owner": [0] * 100, "n": 100}, {"lenses": [
            {"id": "children", "values": [1] * 94 + [None] * 6},
            {"id": "elderly", "values": [1] * 94 + [None] * 6},
            {"id": "median_age", "values": [1] * 80 + [None] * 20},
        ]})
        self.assertEqual([level for level, _ in report.lines], ["WARN", "NOTE"])
        self.assertIn("median_age", report.lines[0][1])
        self.assertIn("2 lenses", report.lines[1][1])

    def test_modelled_zero_yields_are_expected_but_zero_gdp_warns(self):
        report = check.Report(quiet=True)
        check.quality_null_yields(report, "cities", [{
            "yields": {"faith": 0, "gold": 0},
            "yield_meta": {"faith": {"period": "2026"}, "gold": {"period": "2026"}},
        }])
        self.assertTrue(any(level == "NOTE" and "'faith': 1" in msg for level, msg in report.lines))
        self.assertEqual([msg for level, msg in report.lines if level == "WARN"],
                         ["cities yields exactly 0 (a stand-in for unknown?): {'gold': 1}"])
