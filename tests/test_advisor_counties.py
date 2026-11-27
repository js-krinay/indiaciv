import unittest

from pipeline.build.counties import district_table


class AdvisorCountiesTests(unittest.TestCase):
    def test_keeps_district_periods_and_missing_values(self):
        world = {
            "counties": [{"geoid": "01-001", "name": "Kupwara"},
                         {"geoid": "01-002", "name": "Jammu"}],
            "county": [-1, 0],
        }
        places = {"counties": {
            "01-001": {"state": "JK", "population": 100, "historical_land": {
                "forest": {"value": 0.0, "period": "Esri 2025", "vintage": "older", "source": "esri_land_cover"}
            }},
            "01-002": {"state": "JK"},
        }, "district_fallbacks": {"0": 1}}
        cities = [{"id": "one", "counties": ["01-001", "01-002"]},
                  {"id": "two", "counties": ["01-002"]}]
        result = district_table(world, places, {}, cities)
        rows = [dict(zip(result["columns"], row, strict=True)) for row in result["rows"]]
        self.assertEqual(rows[0]["forest"], 0)
        self.assertIsNone(rows[1]["forest"])
        self.assertEqual(rows[1]["cell"], 0)
        self.assertEqual(rows[0]["cbsa"], "one")
        self.assertIsNone(rows[1]["cbsa"])
        self.assertEqual(result["provenance"]["01-001"]["forest"]["period"], "Esri 2025")
        self.assertEqual(result["provenance"]["01-001"]["forest"]["vintage"], "older")
