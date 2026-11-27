import shutil
import subprocess
import unittest
from pathlib import Path

from pipeline.build.city_economy import city_finances, city_sector_output, gateway_records, segment_distance
from pipeline.core.hexgrid import HexGrid


class CityEconomyTests(unittest.TestCase):
    def test_rank_uses_cohort_and_preserves_ties_and_missing(self):
        cities = {
            "a": {"population": 10, "yields": {"gold": 1000}},
            "b": {"population": 20, "yields": {"gold": 1000}},
            "c": {"population": 10, "yields": {"gold": None}},
            "outside": {"population": 1, "yields": {"gold": 9000}},
        }
        rows = city_finances({key: cities[key] for key in ("a", "b", "c")})
        self.assertEqual(rows["a"]["gdp_per_resident"], 100)
        self.assertEqual(rows["a"]["ranks"]["gdp"], 1)
        self.assertEqual(rows["b"]["ranks"]["gdp"], 1)
        self.assertEqual(rows["b"]["ranks"]["gdp_per_resident"], 2)
        self.assertIsNone(rows["c"]["ranks"]["gdp"])
        self.assertTrue(rows["a"]["estimated"])

    def test_sector_output_weights_each_state_and_requires_full_coverage(self):
        mixes = {
            "A": {"shares": {"agriculture": .2, "industry": .3, "services": .5}, "source": "a"},
            "B": {"shares": {"agriculture": .5, "industry": .1, "services": .4}, "source": "b"},
        }
        result = city_sector_output({"A": 100, "B": 300}, mixes)
        self.assertEqual(result["values"], {"agriculture": 170, "industry": 60, "services": 170})
        self.assertIsNone(city_sector_output({"A": 100, "C": 300}, mixes))

    def test_gateway_types_and_distance_use_mapped_points(self):
        city = {"x": 10, "y": 0, "cell": 0}
        point = {"x": 20, "y": 0, "id": "p", "name": "Major", "category": "Major port", "cargo": 50}
        airport = {"x": 7, "y": 0, "id": "a", "name": "Airport", "size": "large"}
        closed = dict(airport, id="unscheduled", x=10, scheduled_service=False)
        infra = {"ports": [dict(point, x=11, category="Non-major port"), point], "airports": [airport, closed]}
        rails = {"Eastern DFC": [0, 1], "Distant route": [8, 9]}
        result = gateway_records(city, {"cells": [{"cell": 0}]}, infra, rails, HexGrid(18, 5, 2))
        self.assertEqual(result["port"]["distance_km"], 10)
        self.assertNotIn("cargo", result["port"])
        self.assertEqual(result["airports"]["large"]["distance_km"], 3)
        self.assertEqual([(r["name"], r["distance_km"]) for r in result["rail"]], [("Eastern DFC", 0)])
        self.assertEqual(segment_distance((3, 4), (0, 0), (10, 0)), 4)

    def test_bengaluru_uses_nearby_main_line_when_no_corridor_is_mapped(self):
        city = {"name": "Bengaluru", "x": 1145.8, "y": 2878, "cell": 11699}
        unnamed = [11591, 11699, None]
        mysuru = [11699, 11808, "Mysuru–Bengaluru line"]
        infra = {"main_lines": [unnamed, mysuru, [0, 1, "Distant main line"]]}
        grid = HexGrid(18, 109, 139)
        profile = {"cells": [{"cell": index} for index in (11590, 11591, 11699, 11700, 11809)]}
        result = gateway_records(city, profile, infra, {}, grid)
        self.assertEqual([(r["main_line"], r["name"], r["distance_km"]) for r in result["rail"]],
                         [(True, "Main line", 1)])
        named_main = gateway_records(city, profile, {"main_lines": [mysuru]}, {}, grid)
        self.assertEqual(named_main["rail"][0]["name"], "Mysuru–Bengaluru line")
        named = gateway_records(city, profile, infra, {"Named corridor": mysuru[:2]}, grid)
        self.assertEqual([r["name"] for r in named["rail"]], ["Named corridor"])

    @unittest.skipUnless(shutil.which("node"), "Node is needed to test Compare")
    def test_compare_requires_compatible_series(self):
        subprocess.run(["node", "tests/city_compare.mjs"], cwd=Path(__file__).resolve().parents[1], check=True)
