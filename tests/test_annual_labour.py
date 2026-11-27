import shutil
import unittest
from pathlib import Path

from pipeline.india import annual_labour


class AnnualLabourTest(unittest.TestCase):
    def test_carry_forward_keeps_the_observed_benchmark_in_2025(self):
        rates = {"wpr_all_ages": 38.8, "unemployment_15_plus": 10.2, "industry_shares": [0.4, 17.6, 82],
                 "sample_persons": 2153, "sample_persons_15_plus": 1750, "sample_clusters": 48}
        records = annual_labour.fallback_records(1293582, "population", "1 July 2026", "urban", rates)
        self.assertEqual(records["employed"]["value"], 501910)
        self.assertEqual(records["employed"]["period"], "1 July 2026")
        self.assertEqual(records["employed"]["vintage"], "1 July 2026")
        self.assertTrue(records["employed"]["estimated"])
        self.assertEqual(records["unemployment"]["value"], .102)
        self.assertEqual(records["unemployment"]["vintage"], "older")
        self.assertEqual(records["unemployment"]["period"], annual_labour.PERIOD)
        self.assertEqual(records["unemployment"]["sample_persons"], 1750)
        self.assertEqual(records["industry"]["value"], [0.4, 17.6, 82])

    def test_chandigarh_urban_numbers_stay_in_the_urban_columns(self):
        row = annual_labour.rate_rows(
            "Table (31): WPR\n\nage group: all ages\n"
            "Chandigarh       53.9 21.5 38.8 53.9 21.5 38.8\n",
            31, "age group: all ages", {"Chandigarh": "CH"},
        )["CH"]
        self.assertEqual(row, [None, None, None, 53.9, 21.5, 38.8, 53.9, 21.5, 38.8])

    @unittest.skipUnless(Path(".cache/ic76-annual-plfs.pdf").exists() and shutil.which("pdftotext"),
                         "requires the pinned Annual PLFS and pdftotext")
    def test_reads_pinned_annual_survey(self):
        rows = annual_labour.read_survey(Path(".cache/ic76-annual-plfs.pdf"))
        self.assertEqual(len(rows), 36)
        self.assertEqual(rows["CH"]["urban"]["wpr_all_ages"], 38.8)
        self.assertEqual(rows["CH"]["urban"]["unemployment_15_plus"], 10.2)
        self.assertEqual(rows["CH"]["urban"]["sample_persons"], 2153)
        self.assertEqual(rows["DH"]["combined"]["industry_shares"], [10.9, 67.6, 21.5])
        self.assertEqual(rows["AR"]["combined"]["wpr_all_ages"], 47.9)
