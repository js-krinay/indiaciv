import unittest

from pipeline.build.resources import select_sites
from pipeline.sources.gem_resources import parse_sites


class ResourceTests(unittest.TestCase):
    def test_location_accuracy_follows_selected_unit_coordinates(self):
        base = {"project-id": "plant", "name": "Test plant", "country-area1": "India",
                "status": "operating", "asset-type": "coal", "Latitude": "22", "Longitude": "82"}
        rows = [dict(base, capacity="500", **{"unit-id": "one", "location-accuracy": "exact"}),
                dict(base, capacity="600", Latitude="24", **{"unit-id": "two", "location-accuracy": "approximate"})]
        site, = parse_sites(rows, "power")
        self.assertEqual((site["lat"], site.get("location_accuracy")), (24, "approximate"))

    def test_power_sums_operating_units_once_per_project(self):
        base = {"project-id": "plant", "name": "Test plant", "country-area1": "India",
                "status": "operating", "asset-type": "coal", "Latitude": "22", "Longitude": "82",
                "capacity": "500", "units-of-m": "MW"}
        rows = [dict(base, **{"unit-id": "one"}), dict(base, **{"unit-id": "one"}),
                dict(base, **{"unit-id": "two"}),
                dict(base, status="construction", **{"unit-id": "three"}),
                dict(base, **{"country-area1": "Nepal", "unit-id": "four"})]
        sites = parse_sites(rows, "power")
        self.assertEqual([(s["type"], s["value"]) for s in select_sites(sites)], [("coal_plant", 1000)])

    def test_mine_threshold_uses_design_capacity_in_million_tonnes(self):
        base = {"country-area1": "India", "status": "operating", "Latitude": 22, "Longitude": 82,
                "name": "Iron mine", "units-of-m": "ttpa", "prod-year-iron": "2024"}
        sites = parse_sites([dict(base, capacity=1999, **{"project-id": "small"}),
                             dict(base, capacity=2000, **{"project-id": "large"})], "iron")
        self.assertEqual([s["value"] for s in select_sites(sites)], [2])

    def test_field_count_excludes_country_centroids_and_ignores_historical_production(self):
        row = {"country-area1": "India", "status": "operating", "Latitude": 22, "Longitude": 82,
               "name": "Field (India)", "project-id": "field", "capacity": 15, "prod-year-oil": 2018}
        centroid = dict(row, **{"project-id": "unknown", "location-accuracy": "country-level only"})
        self.assertEqual([s["value"] for s in parse_sites([centroid, row], "oil")], [1])
