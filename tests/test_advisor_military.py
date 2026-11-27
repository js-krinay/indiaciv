import unittest

from pipeline.build.advisor_statistics import state_explorer_columns, state_statistics
from pipeline.build.military import public_statistics
from pipeline.check import Report, check_military


class AdvisorMilitaryTests(unittest.TestCase):
    def test_contract_includes_only_public_national_headlines(self):
        report = public_statistics({
            "defence_budget": {"total": 12.25, "period": "FY 2025-26", "source": "budget"},
            "defence_budget_share_gdp": {"value": 0.02, "source": ["budget", "gdp"], "estimated": True},
            "veterans": {"value": 100, "period": "30 Jun 2026", "source": ["one", "two"], "estimated": True},
            "civic_offices": [{"name": "Civil office"}],
        })
        self.assertEqual(report["national"]["spending"]["total"], 122_500_000)
        self.assertEqual(report["national"]["veterans"], 100)
        self.assertEqual(report["vintage"]["veterans"], "30 Jun 2026")
        self.assertNotIn("installations", report)
        self.assertNotIn("personnel", report["national"])

    def test_state_explorer_lists_civic_boards_and_school_counts(self):
        columns = state_explorer_columns(state_statistics("RJ", {}, None))
        self.assertEqual(columns["cantonment_board_names"]["value"], "Ajmer, Nasirabad")
        self.assertEqual(columns["rashtriya_military_schools"]["value"], 2)
        self.assertEqual(columns["rashtriya_military_schools"]["period"], "2026")

    def test_explorer_company_financials_are_dated_and_join_to_headquarters_state(self):
        columns = state_explorer_columns(state_statistics("KA", {}, None))
        self.assertEqual(columns["hal_turnover"]["value"], 317_918_300_000)
        self.assertIn("Bengaluru", columns["hal_turnover"]["description"])
        self.assertIn("31 Mar 2026", columns["hal_turnover"]["period"])
        self.assertNotIn("hal_turnover", state_explorer_columns(state_statistics("RJ", {}, None)))

    def test_explorer_lists_traditional_school_roster(self):
        columns = state_explorer_columns(state_statistics("AP", {}, None))
        self.assertEqual(columns["traditional_sainik_school_roster"]["value"], "Korukonda, Kalikiri")
        self.assertEqual(columns["traditional_sainik_school_roster"]["period"], "2026")

    def test_explorer_labels_board_classes_and_census_counts_separately(self):
        columns = state_explorer_columns(state_statistics("RJ", {}, None))
        self.assertIn("Ajmer (III)", columns["cantonment_board_classes"]["value"])
        population = columns["cantonment_board_population"]
        self.assertIn("Ajmer (3530)", population["value"])
        self.assertEqual((population["period"], population["vintage"]), ("Census 2011", "older"))

    def test_explorer_lists_partnership_school_places(self):
        columns = state_explorer_columns(state_statistics("AP", {}, None))
        self.assertEqual(columns["partnership_sainik_school_places"]["value"],
                         "Krishnapatnam, Vijayawada, Tirupati")

    def test_contract_publishes_dated_public_indicators(self):
        doc = public_statistics({"sainik_schools": {
            "value": 79, "period": "7 May 2026", "source": "sainik_schools_2026",
        }})
        self.assertEqual(doc["national"]["sainik_schools"], 79)
        self.assertEqual(doc["vintage"]["sainik_schools"], "7 May 2026")
        self.assertIn("sainik_schools_2026", doc["sources"])
        report = Report()
        check_military(report, doc)
        self.assertFalse(report.failed)

    def test_checker_rejects_detail_in_public_indicators(self):
        for value in ({"total": 16, "coordinates": [1, 2]}, -1, True):
            with self.subTest(value=value):
                report = Report()
                check_military(report, {"national": {"defence_psu_turnover": value},
                                        "vintage": {"defence_psu_turnover": "FY 2025-26"}, "sources": []})
                self.assertTrue(report.failed)

    def test_checker_requires_period_for_public_indicators(self):
        report = Report()
        check_military(report, {"national": {"sainik_schools": 79}, "vintage": {}, "sources": []})
        self.assertTrue(report.failed)

    def test_checker_accepts_public_state_registrations(self):
        report = Report()
        check_military(report, {"national": {"veterans": 1000}, "states": {
            "HP": {"veterans": 100, "veterans_pct": 0.01},
        }, "vintage": {}, "sources": []})
        self.assertFalse(report.failed)

    def test_checker_rejects_operational_fields(self):
        for key in ("bases", "units", "installations", "troop_counts"):
            with self.subTest(key=key):
                report = Report()
                check_military(report, {"national": {}, "states": {
                    "HP": {"veterans": 100, key: 1},
                }, "vintage": {}, "sources": []})
                self.assertTrue(report.failed)
