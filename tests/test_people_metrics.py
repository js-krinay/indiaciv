import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from pipeline import check
from pipeline.build import state_metrics

from pipeline.build.state_metrics import estimate_gsdp

from pipeline.india.people_metrics import (
    parse_cea, parse_delhi, parse_gdp, parse_gsdp, parse_gsdp_supplement, parse_jjm,
    parse_plfs, parse_plfs_rates, parse_urban, parse_wage, parse_wage_average,
)


class PeopleMetricsTests(unittest.TestCase):
    def test_plfs_uses_adult_person_and_female_columns(self):
        rows = parse_plfs_rates("age group: 15 years and above\nAssam  1 2 3 4 5 6 7 8 9")
        self.assertEqual(rows["Assam"], ([.03, .06, .09], [.02, .05, .08]))

    def test_tap_water_uses_published_percentage(self):
        self.assertEqual(parse_jjm([["1", "Assam", "10", "0", "0", "0", "8", "82.09"]]), {"Assam": .8209})

    def test_supply_skips_dvc_and_reads_availability(self):
        text = "Annex-II\nAssam  13,616 13,615 1 0.0\nDamodar Valley Corporation  20 19 1 5.0\nAnnex-III"
        self.assertEqual(parse_cea(text), {"Assam": 13615})

    def test_gsdp_prefers_latest_non_null_nominal_value(self):
        def row(year, value):
            return {"state": "Assam", "year": year, "current_price": value}
        self.assertEqual(parse_gsdp({"data": [row("2025-26", None), row("2024-25", "120")]}), {"Assam": (2024, 120)})

    def test_estimate_compounds_growth_over_gap(self):
        self.assertAlmostEqual(estimate_gsdp(100, 2023, .1), 121)
        self.assertEqual(estimate_gsdp(100, 2025, .1), 100)

    def test_urban_reads_person_columns_for_2026(self):
        text = "TABLE - 10\n    INDIA                  JAMMU & KASHMIR (UT)\nPerson Male Female Person Male Female\n2026  36.19 36.61 35.76 31.31 32.46 30.05"
        self.assertEqual(parse_urban(text, 10), {"INDIA": 36.19, "JAMMU & KASHMIR (UT)": 31.31})

    def test_wages_leave_substate_schedules_blank(self):
        rows = parse_wage("State-wise wage rate for unskilled manual workers\n"
                          "1.  Andhra Pradesh  Rs. 312.00\n"
                          "9.  Non-scheduled areas  Rs. 300.00\n"
                          "10.  Jammu and Kashmir  Rs. 300.00")
        self.assertEqual(rows, {"Andhra Pradesh": 312, "Jammu and Kashmir": 300})

    def test_national_gdp_extracts_current_price_amount_and_growth(self):
        self.assertEqual(parse_gdp("Statement 1: Constant Prices\n13 GDP 1 2 3 4 1.0 1.0 1.0\n"
                                   "Statement 2: Current Prices\n13 GDP 2,61,17,627 2,89,83,909 3,18,07,309 3,46,35,638 11.0 9.7 8.9"),
                         (34635638, .089))

    def test_delhi_advance_estimate_extracts_nominal_crore(self):
        self.assertEqual(parse_delhi("likely to attain a level of ₹ 13,27,055 crore which is at a growth"), 1327055)

    def test_components_supplement_uses_latest_year(self):
        self.assertEqual(parse_gsdp_supplement("date,Assam: GSDP\n2023-04-01,90\n2024-04-01,110\n2025-04-01,"),
                         {"Assam": (2024, 110)})

    def test_plfs_agriculture_combined_header_has_no_spaces(self):
        names = ["State " + chr(65 + i) for i in range(22)] + ["all-India"]
        rates = "\n".join(f"{name}  1 2 3 4 5 6 7 8 9" for name in names)
        agriculture = "\n".join(f"{name}  10 20 70 100" for name in names)
        pages = [f"Table ({n}): rate\nage group: 15 years and above\n{rates}" for n in (2, 3, 5)]
        pages.extend(f"Table (4): employment\n{sector}  person$\n{agriculture}"
                     for sector in ("rural", "urban", "rural+urban"))
        self.assertEqual(parse_plfs("\f".join(pages))["agri_worker_share"]["all-India"], [.1, .1, .1])

    def test_wage_average_reads_newly_notified_rate(self):
        self.assertEqual(parse_wage_average("from ₹298.8 per day under MGNREGA to ₹327.4 per day under VB–G RAM G"), 327.4)


    def test_missing_source_interim_stops_state_metrics_build(self):
        def load(name):
            if name == "plfs_q3":
                raise FileNotFoundError(name)
            return {}

        with patch.object(state_metrics, "load_interim", side_effect=load):
            with self.assertRaisesRegex(FileNotFoundError, "plfs_q3"):
                state_metrics.build()

    def test_india_check_rejects_missing_lens_and_source(self):
        with TemporaryDirectory() as tmp:
            interim = Path(tmp)
            for name in state_metrics.INPUTS:
                if name != "plfs_q3":
                    (interim / f"{name}.json").write_text("{}")
            expected = state_metrics.definitions()
            lenses = {"lenses": [{"id": key, "values": [None if key == "wpr" else 0]}
                                 for key in expected if key != "lfpr_rural"]}
            report = check.Report(quiet=True)
            check.quality_india_state_lenses(report, lenses, interim)
            failures = [message for level, message in report.lines if level == "FAIL"]
            self.assertTrue(any("plfs_q3" in message for message in failures))
            self.assertTrue(any("lfpr_rural" in message and "wpr" in message for message in failures))

            (interim / "plfs_q3.json").write_text("{}")
            lenses["lenses"] = [{"id": key, "values": [0]} for key in expected]
            complete = check.Report(quiet=True)
            check.quality_india_state_lenses(complete, lenses, interim)
            self.assertFalse(complete.failed)
            self.assertEqual(complete.count("PASS"), 1)
