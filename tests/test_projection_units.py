import unittest

from pipeline.build.projection import district_growth, state_population, state_profile, state_vitals

TG = {
    "population": {
        "INDIA": {"2011": [100, 0, 0], "2026": [120, 0, 0]},
        "NCT of Delhi": {"2011": [10, 0, 0], "2026": [15, 0, 0]},
        "Dadra & Nagar Haveli": {"2011": [2, 0, 0], "2026": [5, 3, 2], "2031": [6, 4, 2]},
        "Daman Diu": {"2011": [1, 0, 0], "2026": [3, 2, 1], "2031": [4, 3, 1]},
        "Goa": {"2011": [4, 0, 0], "2026": [1000, 500, 500], "2031": [1100, 560, 540]},
    },
    "annual_population": {"Goa": {"2025": 990, "2026": 1000}, "Dadra & Nagar Haveli": {"2025": 4, "2026": 5},
                          "Daman Diu": {"2025": 2, "2026": 3}},
    "profile": {"NCT OF DELHI": {"sex_ratio": 880}, "NORTH-EAST STATES (EXCLUDING ASSAM)": {"sex_ratio": 972}},
    "indicators": {"NCT OF DELHI": {"tfr": 1.5}, "NORTH-EAST STATES (EXCLUDING ASSAM)": {"tfr": 1.62}},
}
DH = "Dadra and Nagar Haveli and Daman and Diu"


class ProjectionUnitsTest(unittest.TestCase):
    def test_vitals_cover_every_unit_and_merge_units(self):
        goa = state_vitals(TG, "Goa")
        self.assertEqual(goa["sex_ratio"], 1000)
        self.assertAlmostEqual(goa["growth"], 1000 / 990 - 1)
        dh = state_vitals(TG, DH)
        self.assertEqual(dh["sex_ratio"], 600)  # (2 + 1) women per (3 + 2) men
        self.assertAlmostEqual(dh["growth"], 8 / 6 - 1)

    def test_state_population_is_in_people_and_sums_merged_units(self):
        self.assertEqual(state_population(TG, "Delhi"), 15_000)
        self.assertEqual(state_population(TG, DH), 8_000)
        self.assertEqual(state_population(TG, "Goa"), 1_000_000)

    def test_a_district_grows_at_its_own_unit_rate(self):
        self.assertEqual(district_growth(TG, "Delhi", 7), 1.5)
        self.assertEqual(district_growth(TG, DH, 26), 2.5)  # Dadra & Nagar Haveli
        self.assertEqual(district_growth(TG, DH, 25), 3.0)  # Daman & Diu

    def test_profiles_by_report_name_north_east_combined_and_none_for_the_rest(self):
        self.assertEqual(state_profile(TG, "Delhi"), {"sex_ratio": 880, "tfr": 1.5, "health": {"period": "2026", "estimated": True}})
        self.assertEqual(state_profile(TG, "Mizoram"), {"sex_ratio": 972, "tfr": 1.62, "health": {"period": "2026", "estimated": True}})
        self.assertIsNone(state_profile(TG, "Goa"))


if __name__ == "__main__":
    unittest.main()
