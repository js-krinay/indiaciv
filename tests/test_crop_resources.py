import unittest

from pipeline.build import crop_resources as crops
from pipeline.build.resources import TYPES, summarize
from pipeline.core.hexgrid import HexGrid
from pipeline.sources.resource_references import SITES


class CropResourceTests(unittest.TestCase):
    def test_hutti_is_a_named_gold_mine_without_a_production_unit(self):
        gold, = [definition for definition in TYPES if definition["id"] == "gold"]
        self.assertIsNone(gold["unit"])
        mine, = [site for site in SITES if site[0] == "gold"]
        self.assertEqual(mine[1:3], ("Hutti gold mine", "KA"))

    def test_field_marker_requires_threshold_and_avoids_city(self):
        grid = HexGrid(radius=10, cols=4, rows=1)
        world = {"owner": [0] * 4, "county": [0, 0, 0, 1],
                 "pct": {"crop": [8, 80, 20, 100], "forest": [0] * 4}}
        self.assertEqual(crops.growing_cell(grid, world, 0, 0, {1}, set(), canopy=False, crop_floor=10), 2)

    def test_presence_counts_have_no_numeric_total(self):
        data = summarize([{"type": "fish", "state": "GJ", "value": None}],
                         [{"id": "fish", "unit": None}])
        self.assertEqual(data["national"]["fish"], {"count": 1, "value": None, "unit": None})

    def test_coastal_snap_checks_state_coast_and_distance(self):
        grid = HexGrid(radius=10, cols=5, rows=1)
        world = {"owner": [-1, 1, 0, 0, 0], "water": [1, 0, 0, 0, 0]}
        x, y = grid.center(1, 0)
        self.assertEqual(crops.site_cell(grid, world, x, y, 1, coastal=True), 1)
        self.assertEqual(crops.site_cell(grid, world, x, y, 0, coastal=True), -1)
        self.assertEqual(crops.site_cell(grid, world, x, y, 0), -1)

    def test_thrissur_coconut_stays_near_cluster_and_avoids_closed_forest(self):
        grid = HexGrid(radius=10, cols=5, rows=1)
        world = {"owner": [0] * 5, "county": [0] * 5,
                 "pct": {"crop": [0, 15, 0, 0, 95], "forest": [100, 60, 0, 0, 0]}}
        anchor = grid.center(0, 0)
        self.assertEqual(crops.growing_cell(grid, world, 0, 0, set(), {0}, [anchor]), 1)

    def test_older_world_uses_rendered_elevation_on_same_grid(self):
        world = {"owner": [0, 0], "grid": {"radius": 10}, "projection": {}}
        rendered = dict(world, elev=[100, 900])
        self.assertEqual(crops.world_elevation(world, rendered), [100, 900])
        self.assertIsNone(crops.world_elevation(world, dict(rendered, projection={"different": True})))
