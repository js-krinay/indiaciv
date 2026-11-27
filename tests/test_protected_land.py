import unittest
from importlib.util import find_spec

from pipeline.build.protected_land import civilian_site, polygon_candidate, qualifying_cells


class ProtectedLandTests(unittest.TestCase):
    def test_military_tags_and_designations_are_excluded(self):
        self.assertTrue(civilian_site({"name": "Example National Park"}))
        self.assertFalse(civilian_site({"name": "Example National Park", "landuse": "military"}))
        self.assertFalse(civilian_site({"name:en": "Example Air Force Station"}))

    def test_kaziranga_park_extent_is_too_small(self):
        from pipeline.build.protected_land import official_area_matches

        self.assertFalse(official_area_matches(436, 889.51))

    def test_kuno_park_extent_is_too_small(self):
        from pipeline.build.protected_land import official_area_matches

        self.assertFalse(official_area_matches(395, 748.761))

    def test_manas_tiger_reserve_extent_is_too_small(self):
        from pipeline.build.protected_land import official_area_matches

        self.assertFalse(official_area_matches(1836, 2837))

    def test_area_tolerance_accepts_boundaries_and_requires_official_area(self):
        from pipeline.build.protected_land import official_area_matches

        self.assertTrue(official_area_matches(75, 100))
        self.assertTrue(official_area_matches(125, 100))
        self.assertFalse(official_area_matches(126, 100))
        self.assertFalse(official_area_matches(100, 0))

    def test_hex_threshold_includes_exactly_thirty_percent(self):
        self.assertEqual(qualifying_cells([(4, 29.9), (2, 30), (3, 80)], 100), [2, 3])

    def test_national_park_requires_park_designation(self):
        self.assertTrue(polygon_candidate("national_park", {"boundary": "national_park"}))
        self.assertFalse(polygon_candidate("national_park", {"leisure": "nature_reserve"}))

    def test_tiger_reserve_excludes_core_buffer_and_corridors(self):
        tags = {"boundary": "protected_area", "name": "Example Tiger Reserve"}
        self.assertTrue(polygon_candidate("tiger_reserve", tags))
        for zone in ("Core", "Buffer", "Corridor"):
            self.assertFalse(polygon_candidate("tiger_reserve", {**tags, "name": f"{tags['name']} {zone}"}))

    def test_wetland_requires_ramsar_designation(self):
        self.assertFalse(polygon_candidate("ramsar", {"natural": "water"}))
        self.assertTrue(polygon_candidate("ramsar", {"boundary": "protected_area", "designation": "Ramsar Site"}))


@unittest.skipUnless(find_spec("shapely"), "Geometry preparation uses the optional Shapely environment")
class ProtectedGeometryTests(unittest.TestCase):
    def test_coverage_subtracts_holes_and_omits_foreign_hexes(self):
        from shapely.geometry import box
        from shapely.strtree import STRtree

        from pipeline.india.protected_land import covered_cells

        cells = [box(0, 0, 10, 10), box(10, 0, 20, 10), box(20, 0, 30, 10)]
        extent = box(0, 0, 30, 4).difference(box(0.5, 0.5, 9.5, 2))
        self.assertEqual(covered_cells(extent, cells, STRtree(cells), [0, 0, -2]), [1])

    def test_area_shares_count_overlap_once(self):
        from shapely.geometry import box

        from pipeline.india.protected_land import area_shares

        result = area_shares([box(0, 0, 4, 10), box(3, 0, 7, 10)], {"district": box(0, 0, 10, 10)})
        self.assertEqual(result, {"district": 0.7})
