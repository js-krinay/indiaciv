import unittest

from pipeline.build.cities import add_headline_ranks


class CityHeadlineTests(unittest.TestCase):
    def test_ranks_use_only_available_values_and_break_ties_by_population_order(self):
        cities = [
            {"population": 200, "projected_growth": 0, "yields": {"gold": 1000}},
            {"population": 100, "projected_growth": -0.01, "yields": {"gold": 1000}},
            {"population": 50, "projected_growth": None, "yields": {}},
        ]
        add_headline_ranks(cities)
        self.assertEqual(cities[0]["ranks"],
                         {"population": 1, "growth": 1, "gdp": 1, "gdp_per_capita": 2})
        self.assertEqual(cities[1]["ranks"]["gdp"], 2)
        self.assertEqual(cities[1]["ranks"]["gdp_per_capita"], 1)
        self.assertEqual(cities[2]["ranks"],
                         {"population": 3, "growth": None, "gdp": None, "gdp_per_capita": None})
        self.assertEqual(cities[2]["rank_counts"],
                         {"population": 3, "growth": 2, "gdp": 2, "gdp_per_capita": 2})
        self.assertEqual(cities[1]["gdp_per_capita"], 10)

    def test_resource_membership_uses_exact_point_and_review_exclusions(self):
        from pipeline.build.city_view import footprint_resources

        rings = [[(0, 0), (10, 0), (10, 10), (0, 10)]]
        inside = dict(type="solar", name="Inside", x=20, y=20, site_x=5, site_y=5)
        outside = dict(inside, name="Outside", x=5, y=5, site_x=20)
        excluded = dict(inside, name="Excluded")
        approximate = dict(type="solar", name="Approximate", x=5, y=5)
        self.assertEqual(footprint_resources(rings, [inside, outside, excluded, approximate], {"Excluded"}),
                         [["solar", "Inside", 20, 20]])
        self.assertEqual(footprint_resources(None, [inside], set()), [])
