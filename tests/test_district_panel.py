import unittest

from pipeline.build.lenses import district_fallbacks, district_sites
from pipeline.core.geo import Shape, ShapeIndex
from pipeline.core.hexgrid import HexGrid


class DistrictPanelDataTest(unittest.TestCase):
    def setUp(self):
        self.grid = HexGrid(18, 4, 1)
        self.shapes = ShapeIndex([
            Shape([[(20, -2), (30, -2), (30, 2), (20, 2)]]),
            Shape([[(45, -2), (50, -2), (50, 2), (45, 2)]]),
        ])

    def test_unassigned_land_links_to_a_district_in_its_own_state(self):
        self.assertEqual(district_fallbacks(self.grid, [0, -1, 0, 1], [-1, -1, 0, -1],
                                            self.shapes, [1, 0]), {0: 1, 3: 0})

    def test_inventory_uses_original_points_and_excludes_foreign_wonders(self):
        sites = district_sites(self.shapes, [{"id": "1", "x": 25, "y": 0, "cell": 3}],
                               [{"id": "a", "x": 25, "y": 0, "foreign_side": True},
                                {"id": "b", "x": 46, "y": 0}],
                               [{"x": 46, "y": 0, "site_x": 25, "site_y": 0}])
        self.assertEqual(sites, [{"cities": ["1"], "wonders": [], "resources": [0]},
                                 {"cities": [], "wonders": ["b"], "resources": []}])
