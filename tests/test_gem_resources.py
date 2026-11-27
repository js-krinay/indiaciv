import unittest

from pipeline.sources.gem_resources import parse_sites


class GemTechnologyTest(unittest.TestCase):
    def test_only_explicit_field_names_split_commodities(self):
        base = {"country-area1": "India", "status": "operating", "Latitude": 20, "Longitude": 80}
        rows = [dict(base, name=name, **{"project-id": str(i)}) for i, name in enumerate([
            "Example Oil Field (India)", "Example Gas Field", "Example Oil and Gas Field", "Unknown Field",
        ])]
        self.assertEqual([site["type"] for site in parse_sites(rows, "oil")],
                         ["oil", "gas", "oil_gas", "oil_gas"])

    def test_pumped_storage_does_not_duplicate_hydropower(self):
        row = {"country-area1": "India", "status": "operating", "Latitude": 20, "Longitude": 80,
               "name": "Example", "project-id": "p", "asset-type": "hydropower",
               "tech-type": "pumped storage", "capacity": 100}
        self.assertEqual([site["type"] for site in parse_sites([row], "power")], ["pumped_storage"])
        row["project-id"] = "L100000601895"
        self.assertEqual([site["type"] for site in parse_sites([row], "power")], ["hydropower"])

    def test_military_owned_site_is_excluded(self):
        row = {"country-area1": "India", "status": "operating", "Latitude": 20, "Longitude": 80,
               "name": "Example solar farm", "project-id": "p", "asset-type": "utility-scale solar",
               "owner": "Indian Air Force", "capacity": 200}
        self.assertEqual(parse_sites([row], "power"), [])
