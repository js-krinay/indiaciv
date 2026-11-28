import unittest

from pipeline.build.advisor_tables import column_table
from pipeline.build.household_analogues import consumption, district_columns, district_lens, state_columns


class HouseholdAnalogueTests(unittest.TestCase):
    def test_state_subscriptions_keep_their_scale_and_missing_values(self):
        definitions = {"internet_per_100": {"period": "30 June 2026", "source": "trai",
                                           "description": "All access types"}}
        metrics = {"internet_per_100": {"value": 126, "estimated": True}}
        column = state_columns(metrics, definitions, {})["internet_per_100"]
        self.assertEqual(column["value"], 126)
        self.assertTrue(column["hide_rank"])
        self.assertTrue(column["estimated"])
        self.assertNotIn("internet_per_100", state_columns({}, definitions, {}))

    def test_district_columns_keep_sectors_and_rangeland_separate(self):
        pilot = {"urban": 95, "rural": 112, "period": "HCES 2022-23", "vintage": "older", "source": "pilot"}
        cover = {"composition": {"shares": {"11": 0}, "samples": 45, "sparse": True,
                                 "period": "2025 annual land cover", "source": "esri", "vintage": "older"}}
        columns = district_columns(pilot, cover)
        self.assertEqual(columns["consumption_index"]["value"], 95)
        self.assertEqual(columns["consumption_index_rural"]["value"], 112)
        self.assertEqual(columns["pasture"]["value"], 0)
        self.assertTrue(columns["pasture"]["hide_rank"])
        self.assertEqual(district_columns({}, {}), {})

    def test_explorer_consumption_metadata_matches_for_blank_and_present_rows(self):
        for city, geography in ((False, "district"), (True, "member-district")):
            table = column_table({"a": {"consumption_index": consumption(None, city=city)},
                                  "b": {"consumption_index": consumption(102, city=city)}}, "id")
            spec = table["fields"][1]
            self.assertIn(f"Urban {geography} consumption", spec["label"])
            self.assertEqual(spec["unit"], "index points")
            self.assertTrue(spec["hide_rank"])

    def test_explorer_keeps_esri_sample_counts_on_rows(self):
        table = column_table({key: {"pasture": {"value": 0.25, "coverage": str(samples),
                                                "sparse": True}}
                              for key, samples in (("a", 30), ("b", 60))}, "geoid")
        self.assertNotIn("coverage", table["fields"][1])
        self.assertNotIn("sparse", table["fields"][1])
        self.assertEqual(table["provenance"]["b"]["pasture"]["coverage"], "60")

    def test_district_lens_leaves_missing_districts_water_and_foreign_blank(self):
        column = {"value": 94, "label": "Urban consumption", "period": "HCES 2022-23",
                  "source": "pilot", "vintage": "older", "unit": "index points", "format": "float"}
        world = {"counties": ["a", "b"], "county": [0, 1, 0, 0, -1],
                 "owner": [0, 0, 0, -1, 0], "water": [0, 0, 1, 0, 0]}
        lens = district_lens(world, {"a": {"advisor_columns": {"consumption_index": column}}}, "consumption_index")
        self.assertEqual(lens["values"], [94, None, None, None, None])
        self.assertEqual(lens["vintage"], "older")

class SurveyJoinTests(unittest.TestCase):
    def test_roster_agreement_is_required_for_same_name_districts(self):
        from pipeline.india.district_households import join_surveys

        atlas = {"UP": {"district a": "09-001"}, "GOA": {"district b": "30-001"},
                 "HP": {"district c": "02-001"}}
        survey = {"UP": {"district a": (38, 62), "split district": (42, 60)},
                  "GOA": {"district b": (20, 30), "split district": (40, 50)},
                  "HP": {"district c": (0, 100)}}
        rows = join_surveys(atlas, survey, {"09-001"})
        self.assertEqual(rows, {"09-001": (38, 62), "02-001": (0, 100)})

    def test_mpi_extracts_second_headcount_including_zero_and_missing(self):
        from pipeline.india.district_households import mpi_tables

        report = ("Goa: Overview of Districts\n"
                  "   North Goa   3.33%   40.92%   0.014   0.00%   –   0.000\n"
                  "   South Goa   4.37%   39.28%   0.017   –   –   –\n"
                  "   New Goa     –       –        –       12.2%   50%   0.061\n")
        self.assertEqual(mpi_tables(report), {"goa": {"northgoa": 0, "newgoa": 12.2}})

    def test_tap_coverage_requires_all_habitations_in_denominator(self):
        from pipeline.india.district_households import tap_counts

        bands = ["0", "0", "0"] * 5 + ["2", "25", "25"]
        self.assertEqual(tap_counts(["2", "0", *bands]), (25, 25))
        self.assertIsNone(tap_counts(["3", "1", *bands]))
        self.assertIsNone(tap_counts(["3", "0", *bands]))
