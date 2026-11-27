import unittest

from pipeline.build.census_civic import advisor_columns, civic_lenses
from pipeline.india.census_civic import known_age_median, median_band, observation, shares, sum_areas, validate_crosswalk


class CensusCivicTests(unittest.TestCase):
    def test_ladakh_median_pools_known_ages_before_taking_median(self):
        leh = {"All ages": (11,), "19.0": (1,), "30.0": (8,), "100+": (1,), "Age not stated": (1,)}
        kargil = {"All ages": (7,), "19.0": (5,), "30.0": (2,), "100+": (0,), "Age not stated": (0,)}
        self.assertEqual(known_age_median([leh, kargil]), 30)

    def test_aggregates_counts_before_dividing(self):
        rows = {("01-001", "Urban"): (10, 5), ("01-002", "Urban"): (90, 9)}
        self.assertEqual(shares(("measure",), sum_areas(rows, ["01-001", "01-002"], "Urban")),
                         {"measure": .14})

    def test_requires_all_member_districts(self):
        self.assertIsNone(sum_areas({("01-001", "Urban"): (10, 5)}, ["01-001", "01-002"], "Urban"))

    def test_median_is_a_published_interval(self):
        self.assertEqual(median_band((4, 5, 11, 3, 0, 0, 0, 0)), "2–5 km")
        self.assertIsNone(median_band((0,) * 8))

    def test_faith_keeps_unstated_responses_without_a_largest_category(self):
        record = observation("religion", (10, 4, 4, 0, 0, 0, 0, 0, 2), "Census 2011 district")
        self.assertEqual((record["period"], record["vintage"]), ("Census 2011", "older"))
        self.assertNotIn("Largest stated tradition", record["values"])
        self.assertEqual(record["values"]["Religion not stated"], .2)
        self.assertEqual(record["values"]["Religious affiliation reported"], .8)
        self.assertNotIn("faith_tradition", advisor_columns({"religion": record}))

    def test_largest_reported_religion_excludes_unstated_responses(self):
        record = observation("religion", (100, 10, 29, 1, 0, 0, 0, 0, 60), "Census 2011 district")
        records = {"religion": record}
        column = advisor_columns(records)["faith_tradition"]
        self.assertEqual((column["value"], column["period"], column["vintage"], column["format"]),
                         ("Muslim", "Census 2011", "older", "text"))
        self.assertTrue(column["hide_rank"])
        world = {"counties": ["001"], "county": [0, 0, -1], "owner": [0, 0, -1], "water": [False, True, False]}
        lens = next(lens for lens in civic_lenses(world, {"001": {"census_civic": records}},
                                                 {"001": {"population": 100}})
                    if lens["id"] == "faith_tradition")
        self.assertEqual(lens["categories"][lens["values"][0]]["name"], column["value"])
        self.assertEqual(lens["categories"][lens["values"][0]]["population"], 100)
        self.assertEqual(lens["values"][1:], [None, None])

    def test_no_largest_religion_when_all_responses_are_unstated(self):
        record = observation("religion", (10, 0, 0, 0, 0, 0, 0, 0, 10), "Census 2011 state")
        self.assertNotIn("faith_tradition", advisor_columns({"religion": record}))

    def test_crosswalk_rejects_swapped_or_missing_special_districts(self):
        expected = {
            **{f"01-{i:03d}": "LA" if i in (3, 4) else "JK" for i in range(1, 23)},
            **{f"28-{i:03d}": "TS" if i <= 541 else "AP" for i in range(532, 555)},
            "25-494": "DH", "25-495": "DH", "26-496": "DH",
            **{f"27-{i:03d}": "MH" for i in range(592)},
        }
        validate_crosswalk(expected, expected.keys())
        for changes, removed in (
            ({"28-536": "AP", "28-542": "TS"}, None),
            ({"25-494": "GJ"}, None),
            ({}, "01-001"),
        ):
            mutated = expected | changes
            if removed:
                del mutated[removed]
            with self.subTest(changes=changes, removed=removed), self.assertRaises(ValueError):
                validate_crosswalk(mutated, expected.keys())
