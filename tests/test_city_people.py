import unittest

from pipeline.build.city_people import age_profile, footprint_workforce, qualitative_plaques, workforce
from pipeline.india.city_labour import national_urban_unemployment


class CityPeopleTest(unittest.TestCase):
    def test_national_benchmark_uses_urban_persons_aged_fifteen_and_over(self):
        text = ("Table (5): age group: all age\n"
                "all-India  4.5 4.1 4.3 6.1 8.8 6.9 5.0 5.2 5.1\f"
                "Table (5): age group: 15 years and above\n"
                "all-India  4.5 4.1 4.3 6.1 8.8 6.8 5.0 5.2 5.1")
        self.assertEqual(national_urban_unemployment(text), 0.068)

    def test_age_scales_to_un_population_and_keeps_median_band(self):
        profile = age_profile(101, {0: 2, 15: 3, 35: 4, 60: 1})
        self.assertEqual(profile["counts"], {"0_14": 20, "15_59": 71, "60_plus": 10})
        self.assertEqual(profile["median_band"], [15, 19])

    def test_midlife_uses_exact_bins_without_double_counting_total(self):
        profile = age_profile(100, {age: 1 for age in [0, 1, *range(5, 91, 5)]})
        self.assertEqual(profile["bands"]["midlife"], 30)
        self.assertNotIn("young", profile["bands"])
        self.assertEqual(sum(profile["counts"].values()), 100)

    def test_worked_city_icon_rounding_and_separate_denominators(self):
        for population, adults, rates, headline, adult_headline, icons in [
            (14771658, 11849849, [41.7, 51.3, 3.6, 6.6, 28.8, 64.6], 6159781, 6078973, [1, 6, 13]),
            (3410917, 2444534, [31.9, 42.0, 9.3, 8.3, 33.6, 58.1], 1088083, 1026704, [2, 7, 11]),
        ]:
            profile = workforce(population, adults, rates, "TEST")
            self.assertEqual(profile["employed_all_ages"], headline)
            self.assertEqual(profile["employed_15_plus"], adult_headline)
            self.assertEqual([row["icons"] for row in profile["industries"]], icons)
            self.assertEqual(sum(row["employed"] for row in profile["industries"]), profile["employed_15_plus"])
        self.assertIsNone(workforce(1000, None, rates, "TEST")["employed_15_plus"])

    def test_qualitative_evidence_requires_a_reviewed_member_district(self):
        self.assertEqual(qualitative_plaques("21296", {"09-156"}), [])
        self.assertEqual([p["label"] for p in qualitative_plaques("21296", {"09-164"})], ["Leather and footwear"])

    def test_cross_state_workforce_weights_employment_and_requires_all_state_rates(self):
        rates = {"A": [20, 25, 0, 100, 0, 0], "B": [60, 75, 0, 0, 0, 100]}
        result = footprint_workforce(100, 80, {"A": 75, "B": 25}, rates)
        self.assertEqual(result["employed_all_ages"], 30)
        self.assertEqual([i["employed"] for i in result["industries"]], [15, 0, 15])
        self.assertIsNone(footprint_workforce(100, 80, {"A": 75, "C": 25}, rates))
