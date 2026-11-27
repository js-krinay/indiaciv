import shutil
import subprocess
import unittest
from pathlib import Path

from pipeline.build.almanac import make_entries, terrain_captions
from pipeline.build.catalog import release_credits


class AlmanacTests(unittest.TestCase):
    def test_transport_inventory_preserves_names_references_and_networks(self):
        entries = make_entries(
            world={"grid": {"cols": 3, "rows": 2, "radius": 5}},
            infrastructure={"vintage": {"network": "November 2026"},
                            "roads": [[0, 1, 0, "NH 1", "Example Highway", "National"],
                                      [1, 2, 0, "NH 1", "Example Highway", "National"]],
                            "rail": [[0, 1, 0, "", "Example Railway", "Main"]]},
        )
        roads = entries["About this map"]["Highways"]
        self.assertEqual(len(roads), 1)
        self.assertEqual(roads[0]["name"], "Example Highway · NH 1")
        self.assertIn("National · November 2026", roads[0]["rule"])
        self.assertEqual(roads[0]["sources"], ["osm_transport"])
        self.assertEqual(entries["About this map"]["Railway lines"][0]["name"], "Example Railway")

    @unittest.skipUnless(shutil.which("node"), "Node is needed to exercise the Almanac")
    def test_map_share_state(self):
        subprocess.run(
            ["node", "tests/almanac.mjs"],
            cwd=Path(__file__).resolve().parents[1], check=True,
        )

    def test_relief_examples_and_feature_membership(self):
        tables, labels = terrain_captions({
            "features": [[1], []],
            "tables": {
                "relief": [{"id": 0, "name": "Flat", "rule": "Low slopes"}],
                "features": [{"id": 1, "name": "Woods"}],
                "feature_cells": {"1": [0, 1]},
                "terrain_examples": [{"name": "Punjab plain", "relief": 0}],
            },
        })
        self.assertIn("Punjab plain", tables["relief"][0]["rule"])
        self.assertIn("ETOPO", tables["relief"][0]["rule"])
        self.assertEqual(tables["relief"][0]["sources"], ["etopo"])
        self.assertEqual(labels, {"0": ["Woods"], "1": ["Woods"]})

    def test_solar_credit_retains_deed_and_uncertain_period(self):
        entry = release_credits({"id": "gem_power", "description": "Power", "license": "CC BY 4.0"})
        self.assertIn("unresolved", entry["description"])
        self.assertIn("https://creativecommons.org/licenses/by-nc/4.0/",
                      [link["url"] for link in entry["credit_links"]])

    def test_inventory_entries_keep_provenance(self):
        entries = make_entries(
            world={"grid": {"cols": 3, "rows": 2, "radius": 5}},
            states=[{"abbr": "UP", "name": "Uttar Pradesh", "population": 2000,
                     "provenance": {"population": {"period": "1 March 2026", "source": "tg"}},
                     "metrics": {"civic": {"value": 0.1, "period": "Census 2011",
                                           "vintage": "older", "source": "orgi"}}}],
            cities=[{"id": "agra", "name": "Agra", "population": 1000}],
            wonders={"wonders": [{"id": "fort", "name": "Agra Fort", "rule": "heritage",
                                  "description": "Fort on the Yamuna"}],
                     "rules": [{"id": "heritage", "text": "World Heritage"}]},
            lenses={"lenses": [{"id": "civic", "name": "Civic measure", "unit": "share"}]},
            protected=({"sites": [{"id": "park", "name": "Park", "source": "relation/123",
                                   "authority_source": "wii_protected"}]},),
        )
        state = entries["States"]["States and union territories"][1]
        self.assertEqual(state["name"], "Uttar Pradesh")
        self.assertEqual(state["facts"][1]["period"], "Census 2011")
        self.assertEqual(state["facts"][1]["source"], "orgi")
        self.assertEqual(state["facts"][1]["vintage"], "older")
        city = entries["About this map"]["Cities"][1]
        self.assertEqual(city["name"], "Agra")
        self.assertEqual(city["facts"], [])
        wonder = entries["About this map"]["Wonders"][1]
        self.assertEqual(wonder["name"], "Agra Fort")
        self.assertIn("World Heritage", wonder["rule"])
        site = entries["Terrain"]["Protected land"][1]
        self.assertEqual(site["sources"], ["wii_protected", "osm_protected"])
