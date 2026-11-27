import unittest

from pipeline.india.village_land_use import grazing_share


class VillageLandUseTest(unittest.TestCase):
    def test_uses_reported_village_area_for_all_matching_blocks(self):
        self.assertAlmostEqual(grazing_share({"a": 80, "b": 20},
                                             {"a": (79.9, 4), "b": (20, 3)}), .07)

    def test_rejects_irreconcilable_or_incomplete_reporting(self):
        with self.assertRaises(ValueError):
            grazing_share({"a": 90, "b": 10}, {"a": (90, 4)})
        with self.assertRaises(ValueError):
            grazing_share({"a": 90}, {"a": (20, 4)})
