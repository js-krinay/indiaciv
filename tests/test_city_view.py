import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pipeline.core.paths import WEB_DATA
from pipeline.core.store import load_interim
from pipeline.india import GHSL_UCDB

from pipeline.build import city_view


class CityViewTests(unittest.TestCase):
    def test_cohort_is_frozen(self):
        path = WEB_DATA / "cities.json"
        if not path.exists():
            self.skipTest("build cities.json first")
        cities = json.loads(path.read_text())
        ranked = sorted(cities, key=lambda city: (-city["population"], int(city["id"])))
        self.assertEqual(city_view.cohort(), [city["id"] for city in ranked[:50]])

    def test_entry_points_include_point_only_agglomerations(self):
        cities = {"1": {"id": "1"}, "2": {"id": "2"}}
        self.assertEqual(city_view.entry_points(cities.values()), {"1", "2"})

    def test_ambiguous_new_centre_matches_stay_point_only(self):
        self.assertEqual(city_view.select_centres("Pune", "MH", [
            {"id": 1, "name": "Pune", "contains": True, "states": ["MH"]},
            {"id": 2, "name": "Pune", "contains": True, "states": ["MH"]},
        ], {}), [])

    def test_cross_border_memberships_in_prepared_profiles(self):
        try:
            profiles = load_interim(GHSL_UCDB)["profiles"]
        except FileNotFoundError:
            self.skipTest("prepare City View footprints first")
        self.assertIn("09-156", {row["id"] for row in profiles["21296"]["districts"]})
        self.assertEqual(set(profiles["21228"]["states"]), {"DL", "HR", "UP"})
        self.assertEqual(profiles["21325"]["method"], "point")

    def test_grid_fingerprint_detects_water_change(self):
        world = {"grid": {"radius": 18, "cols": 2, "rows": 1},
                 "projection": {"min_x": 0, "max_y": 0, "margin": 0},
                 "owner": [0, -1], "water": [0, 2]}
        previous = city_view.grid_fingerprint(world)
        world["water"][1] = 1
        self.assertNotEqual(city_view.grid_fingerprint(world), previous)
        with TemporaryDirectory() as tmp:
            web_dir = Path(tmp)
            (web_dir / "cities.json").write_text("[]")
            (web_dir / "world.json").write_text(json.dumps(world))
            (web_dir / "city_view.json").write_text(json.dumps({
                "grid_fingerprint": previous, "profiles": {"1": {"method": "ghsl"}},
            }))
            self.assertIn("stale City View geometry", city_view.check(web_dir)[0][1])

    def test_population_conserved_with_deterministic_ties(self):
        self.assertEqual(city_view.apportion(11, {9: 1, 3: 1, 5: 1}), {3: 4, 5: 4, 9: 3})

    def test_cross_border_match_and_point_fallback(self):
        candidates = [
            {"id": 1, "name": "New Delhi", "states": ["DL", "HR", "UP"], "contains": True},
            {"id": 2, "name": "Delhi", "states": ["RJ"], "contains": True},
            {"id": 3, "name": "Delhi", "states": ["DL"], "contains": False},
        ]
        self.assertEqual(city_view.select_centres("Delhi", "DL", candidates, {"aliases": ["New Delhi"]}), [1])
        self.assertEqual(city_view.select_centres("Kanpur", "UP", candidates, {}), [])
        self.assertEqual(city_view.point_profile({"cell": 4, "population": 11})["cells"],
                         [{"cell": 4, "population": 11, "hex_fraction": None, "footprint_share": None}])
