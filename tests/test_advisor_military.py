import unittest

from pipeline.build.advisor_statistics import state_explorer_columns, state_statistics
from pipeline.build.military import cantonment_records, command_records, gazetteer, public_statistics
from pipeline.india.military_sources import COMMANDS
from pipeline.check import Report, check_military


class AdvisorMilitaryTests(unittest.TestCase):
    def test_cantonment_join_requires_unique_town_in_directory_state(self):
        points = {("MH", "pune"): [(1, 2, "27-521", "21228", "ne_places", "123")],
                  ("MH", "khadki"): [(3, 4, "27-521", None, "ne_places", "123"), (5, 6, "27-521", None, "ne_places", "123")],
                  ("GJ", "dehuroad"): [(7, 8, None, None, "ne_places", "123")]}
        rows = cantonment_records({"MH": ("Pune", "Pune", "Khadki", "Dehuroad")}, points, lambda x, y: 8)
        self.assertEqual([(r["name"], r["county"], r["cbsa"]) for r in rows],
                         [("Pune Cantonment Board", "27-521", "21228")])

    def test_command_list_uses_unique_government_releases_and_civil_centres(self):
        self.assertEqual(len(COMMANDS), len({row[0] for row in COMMANDS}))
        self.assertTrue(all(release.isdecimal() and period for _, _, _, release, period in COMMANDS))
        rows = command_records({("HP", "shimla"): [(1, 2, None, None, "ne_places", "123")]}, lambda x, y: 8)
        self.assertEqual([(r["name"], r["component"], r["tier"], r["source"]) for r in rows],
                         [("Army Training Command", "Command HQ", "Command HQ", "command_hq_2257210")])

    def test_checker_rejects_unapproved_markers(self):
        report = Report()
        rows = cantonment_records({"MH": ("Example",)}, {("MH", "example"): [(1, 2, None, None, "ne_places", "123")]},
                                  lambda x, y: 8)
        check_military(report, {"national": {}, "installations": rows,
                                "vintage": {}, "sources": ["cantonment_boards"]})
        self.assertTrue(report.failed)

    def test_checker_rejects_arbitrary_point_for_an_approved_town(self):
        places = {("MH", "pune"): [(1, 2, "27-521", "21228", "ne_places", "123")]}
        rows = cantonment_records({"MH": ("Pune",)}, places, lambda x, y: 8)
        doc = {"national": {}, "installations": rows,
               "vintage": {}, "sources": ["cantonment_boards", "ne_places"]}
        good = Report()
        check_military(good, doc, rows)
        self.assertFalse(good.failed)
        doc["installations"] = [{**rows[0], "x": 19, "cell": 11}]
        bad = Report()
        check_military(bad, doc, rows)
        self.assertTrue(bad.failed)

    def test_later_unique_civil_place_replaces_an_ambiguous_source(self):
        world = {"projection": {"min_x": -200, "max_y": 200, "margin": 0},
                 "states": [{"name": "Test state", "abbr": "TS"}]}
        bounds = {"states": [{"name": "Test state", "rings": [[(81, 21), (83, 21), (83, 23), (81, 23)]]}],
                  "districts": []}
        early = [{"name": "Test town", "id": str(x), "x": x, "y": 0} for x in (0, 1000)]
        later = [{"name": "Test town", "id": "unique", "x": 2000, "y": 0}]
        result = gazetteer(world, bounds, {}, [("first", early), ("later", later)])
        self.assertEqual(result["TS", "testtown"], [(202, 200, None, None, "later", "unique")])

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

    def test_unpaired_veteran_registration_keeps_its_observation_date(self):
        result = state_explorer_columns(state_statistics("MN", {}, 3_000_000))
        count = result["registered_veterans"]
        self.assertEqual((count["value"], count["period"], count["vintage"]), (8744, "30 Jun 2024", "older"))
        self.assertFalse(count["estimated"])
        share = result["veteran_share"]
        self.assertEqual((share["period"], share["vintage"]),
                         ("30 Jun 2024 registrations · mid-2026 residents", "older"))

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
