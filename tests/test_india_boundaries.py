import json
import unittest
from pathlib import Path

from pipeline.build.boundaries import (
    chart_owner, check_chart, guarantee_named_places, hex_overlap, india_area_majority,
    named_indian_cells, promote_islands, reserve_part,
)
from pipeline.build.resources import offshore_land_cell
from pipeline.build.world import conformity
from pipeline.core.geo import MapProjection, Shape, ShapeIndex
from pipeline.core.hexgrid import HexGrid


def square(x, y, radius):
    return [(x-radius, y-radius), (x+radius, y-radius),
            (x+radius, y+radius), (x-radius, y+radius)]


class IndiaBoundaryTests(unittest.TestCase):
    grid = HexGrid(18, 5, 5)

    def test_overlap_counts_holes(self):
        x, y = self.grid.center(2, 2)
        polygon = Shape([square(x, y, 3), square(x, y, 1)])
        self.assertAlmostEqual(hex_overlap(self.grid, 12, polygon), 32)

    def test_chart_compares_water_with_both_land_shares_together(self):
        self.assertEqual(chart_owner([320, 110, 410, 2]), "india")
        self.assertEqual(chart_owner([180, 190, 470, 2]), "water")
        self.assertEqual(chart_owner([210, 320, 310, 2]), "foreign")
        self.assertIsNone(chart_owner([80, 100, 120, 542]))

    def test_only_localities_restore_lost_indian_land(self):
        centre = self.grid.center(2, 2)
        points = [("Town", *centre, "UK"), ("Frontier hex", *self.grid.center(3, 2), "UK")]
        localities = named_indian_cells(self.grid, lambda x, y: (x, y), points, {"UK": 0})
        owner, water = [-2] * self.grid.size, [0] * self.grid.size
        self.assertEqual(guarantee_named_places(owner, water, localities, 0), {12: ("Town",)})
        self.assertEqual((owner[12], owner[13]), (0, -2))

    def test_chart_checker_rejects_wrong_national_majorities(self):
        world = {"grid": {}, "projection": {}, "owner": [0, 0, -2]}
        chart = {"grid": {}, "projection": {}, "boundary": [0, 1, 2],
                 "shares": [[220, 620, 0, 0], [220, 620, 0, 0], [620, 220, 0, 0]]}
        decisions = {"islands": [], "ut_parts": [], "named": [{"cell": 1}]}
        rows, errors = check_chart(world, chart, decisions, {1: [("Town", 0)]})
        self.assertEqual([r["rule"] for r in rows],
                         ["charted national land majority", "named Indian locality",
                          "charted national land majority"])
        self.assertEqual(len(errors), 2)

    def test_inland_border_uses_outline_area_even_when_centre_is_foreign(self):
        x, y = self.grid.center(2, 2)
        # The mainland stops just short of the centre; an Indian part on the
        # other side makes the combined Indian area larger than half the tile.
        west = Shape([[(x-40, y-40), (x-1, y-40), (x-1, y+40), (x-40, y+40)]])
        east = Shape([square(x+7, y, 4)])
        outline = ShapeIndex([west, east])
        self.assertTrue(india_area_majority(self.grid, 12, outline))

    def test_inland_border_uses_outline_area_even_when_centre_is_indian(self):
        outline = ShapeIndex([Shape([square(*self.grid.center(2, 2), 4)])])
        self.assertFalse(india_area_majority(self.grid, 12, outline))

    def test_missing_part_gets_maximum_overlap_and_keeps_other_part(self):
        owners = [0] * self.grid.size
        owners[11] = 1
        x, y = self.grid.center(2, 2)
        part = Shape([square(x, y, 3), square(*self.grid.center(3, 2), 1)])
        self.assertEqual(reserve_part(self.grid, owners, 1, part), 12)
        self.assertEqual([i for i, owner in enumerate(owners) if owner == 1], [11, 12])

    def test_represented_part_keeps_its_cell(self):
        owners = [0] * self.grid.size
        owners[13] = 1
        part = Shape([square(*self.grid.center(2, 2), 3), square(*self.grid.center(3, 2), 1)])
        self.assertEqual(reserve_part(self.grid, owners, 1, part), 13)
        self.assertEqual(owners[12], 0)


    def test_only_uncovered_detached_island_is_promoted(self):
        owners = [-1] * self.grid.size
        owners[12] = 0
        water = [int(owner < 0) for owner in owners]
        x, y = self.grid.center(2, 2)
        mainland = Shape([square(x, y, 24)])
        covered = Shape([square(x, y, 1)])
        island = Shape([square(*self.grid.center(4, 4), 1)])
        states = ShapeIndex([mainland])
        self.assertEqual(promote_islands(self.grid, owners, water, [mainland, covered, island], states, 0), 1)
        self.assertEqual([cell for cell, value in enumerate(water) if value == 0], [12, 24])

    def test_mainland_touching_polygon_does_not_get_a_tile(self):
        owners = [-1] * self.grid.size
        water = [1] * self.grid.size
        x, y = self.grid.center(2, 2)
        mainland = Shape([square(x, y, 20)])
        touching = Shape([square(x + 24, y, 4)])
        states = ShapeIndex([mainland])
        self.assertEqual(promote_islands(self.grid, owners, water, [mainland, touching], states, 0), 0)

    def test_conformity_reports_wrong_owner_from_emitted_grid(self):
        project = MapProjection(-20, 20, 0)
        world = {"grid": self.grid.to_dict(), "projection": project.to_dict(),
                 "states": [{"abbr": "JK"}, {"abbr": "LA"}], "owner": [0] * self.grid.size}
        point = ("Example", 82, 22, "LA")
        cell = self.grid.cell_at(*project(82, 22))
        self.assertEqual(conformity(world, [point]), [f"Example (cell {cell}): expected LA, got JK"])
        world["owner"][cell] = 1
        self.assertEqual(conformity(world, [point]), [])

    def test_conformity_fixture_has_unique_named_points(self):
        fixture = Path(__file__).parents[1] / "pipeline" / "build" / "soi_conformity.json"
        points = json.loads(fixture.read_text())["points"]
        self.assertGreaterEqual(len(points), 40)
        self.assertEqual(len({row[0] for row in points}), len(points))


class ResourceSnapTests(unittest.TestCase):
    def test_offshore_distance_is_independent_of_hex_radius(self):
        for radius in (18, 25):
            with self.subTest(radius=radius):
                grid = HexGrid(radius, 20, 5)
                cell = grid.index(10, 2)
                owner = [-1] * grid.size
                owner[cell] = 0
                x, y = grid.center(10, 2)
                self.assertEqual(offshore_land_cell(grid, owner, x - 125, y), cell)
                self.assertEqual(offshore_land_cell(grid, owner, x - 135, y), -1)
