import unittest

from pipeline.sources import worldpop_age


class WorldPopAgeTest(unittest.TestCase):
    def test_parser_uses_both_sexes_and_only_selected_2026_units(self):
        bands = [{"class": f"{age:02d}", "female": female, "male": male}
                 for age, female, male in [(0, 1, 2), (1, 2, 3), (5, 3, 4), (10, 4, 5),
                                           (35, 21, 29), (60, 5, 11), (90, 6, 4)]]
        data = {"iso3": "IND", "data_year": 2026, "units": [
            {"unit_id": 1042, "agesex_pyramid": bands},
            {"unit_id": 1029, "agesex_pyramid": list(reversed(bands))},
        ]}
        self.assertEqual(worldpop_age.parse_profiles(data), {
            "Goa": {"age_0_14": 24.0, "age_60": 26.0, "median_age": 37.6},
        })

    def test_parser_rejects_a_different_reference_year(self):
        with self.assertRaises(ValueError):
            worldpop_age.parse_profiles({"iso3": "IND", "data_year": 2025, "units": []})

    def test_medians_match_the_six_published_indicators(self):
        # The research snapshot's total count, crossing band, count below it and count in it.
        cases = [
            ("Andaman & Nicobar", 420368.84, 30, 191656.67, 43191.39, 32.1),
            ("Chandigarh", 1145584.43, 30, 558011.23, 108185.12, 30.7),
            ("Dadra and Nagar Haveli and Daman and Diu", 1096996.82, 25, 477733.11, 137804.67, 27.6),
            ("Goa", 1644327.83, 35, 798204.89, 149230.93, 35.8),
            ("Lakshadweep", 71564.52, 30, 31407.41, 6622.04, 33.3),
            ("Puducherry", 1212076.66, 30, 500895.09, 111585.48, 34.7),
        ]
        for name, total, start, below, crossing, expected in cases:
            with self.subTest(name=name):
                counts = {start - 5: below, start: crossing, start + 5: total - below - crossing}
                self.assertAlmostEqual(worldpop_age.median_age(counts), expected, places=1)
