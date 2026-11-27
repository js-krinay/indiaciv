import unittest

from pipeline.india.cities import parse_places


class ParsePlacesTest(unittest.TestCase):
    def test_uses_only_india_rows_with_a_2026_projection(self):
        rows = [
            ["World Urbanization Prospects"],
            ["Country Code", "City Code", "Urban Agglomeration", "Latitude", "Longitude", 2025, 2026, 2030],
            [356, 10, "Delhi", 28.66, 77.22, 900, 1000.125, 1200],
            [356, 11, "Town", 22, 82, 300, "", 400],
            [356, 12, "Other Town", 23, 83, "", 320, 400],
            [4, 13, "Kabul", 34, 69, 3000, 3300, 4000],
        ]
        delhi, town = parse_places(rows, lambda lon, lat: (lon * 1000, lat * 1000))
        self.assertEqual(delhi, {
            "id": "10", "name": "Delhi", "x": 77220, "y": 28660, "capital": True,
            "population": 1000125, "projected_growth": 1000.125 / 900 - 1, "growth_period": "1 Jul 2025 – 1 Jul 2026",
        })
        self.assertEqual(town["name"], "Other Town")
        self.assertFalse(town["capital"])
        self.assertIsNone(town["projected_growth"])

    def test_interpolates_only_calendar_2026(self):
        header = ["Country Code", "City Code", "Urban Agglomeration", "Latitude", "Longitude", 2025, 2026, 2027]
        rows = [header, [356, 10, "Delhi", 28, 77, 635, 1000, 1365]]
        city, = parse_places(rows, lambda lon, lat: (0, 0))
        self.assertEqual(city["population_2026"]["values"],
                         {"2026-01-01": 819000, "2026-07-01": 1000000, "2026-12-31": 1183000})
