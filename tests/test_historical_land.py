import unittest

from pipeline.build import historical_land


class HistoricalLandTests(unittest.TestCase):
    def test_esri_tiles_cover_zone_and_band_boundaries(self):
        self.assertEqual(historical_land.esri_tile(74.9, 23.9), "43Q")
        self.assertEqual(historical_land.esri_tile(78, 24), "44R")

    def test_esri_shares_exclude_water_clouds_and_missing(self):
        result = historical_land.esri_summary({1: 5, 2: 2, 5: 4, 10: 1, 11: 2, 0: 5})
        self.assertEqual(result["shares"], {"2": .25, "4": 0, "5": .5, "7": 0,
                                             "8": 0, "9": 0, "11": .25})
        self.assertEqual(result["dominant"], "5")
        self.assertEqual(result["other"], .25)
        self.assertEqual(result["samples"], 8)

    def test_missing_land_does_not_become_zero(self):
        self.assertIsNone(historical_land.esri_summary({1: 5, 10: 1}))
        self.assertIsNone(historical_land.worldcover_summary({80: 4}))

    def test_worldcover_wetland_includes_mangroves(self):
        result = historical_land.worldcover_summary({20: 1, 30: 3, 80: 4, 90: 1, 95: 3})
        self.assertEqual(result["shares"], {"grass": .375, "shrub": .125, "wetland": .5})
        self.assertEqual(result["samples"], 8)

    def test_rollup_weights_samples_and_keeps_missing_products_separate(self):
        result = historical_land.rollup([
            ("MH", "27-001", {2: 30}, {30: 60}),
            ("MH", "27-002", {5: 90}, {20: 30}),
            ("GA", "30-001", {}, {90: 30}),
        ])
        self.assertEqual(result["states"]["MH"]["forest"]["value"], .25)
        self.assertEqual(result["states"]["MH"]["grass"]["value"], 2 / 3)
        self.assertEqual(result["districts"]["27-002"]["crop"]["value"], 1)
        self.assertNotIn("forest", result["states"]["GA"])
        self.assertEqual(result["states"]["GA"]["wetland"]["vintage"], "older")


    def test_region_floor_and_sparse_flags_are_independent_by_product(self):
        result = historical_land.rollup([
            ("MH", "27-001", {2: 29}, {30: 30}),
            ("GA", "30-001", {5: 99}, {20: 100}),
        ])
        self.assertNotIn("composition", result["states"]["MH"])
        self.assertEqual(result["states"]["MH"]["grass"]["samples"], 30)
        self.assertTrue(result["states"]["MH"]["grass"]["sparse"])
        self.assertTrue(result["districts"]["30-001"]["composition"]["sparse"])
        self.assertFalse(result["districts"]["30-001"]["grass"]["sparse"])
