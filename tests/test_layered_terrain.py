import json
import unittest

from pipeline.india.terrain_validation import FIXTURE, segment_distance, unexpected_fields
from pipeline.build.terrain_layers import BASE_TABLE, FEATURE_TABLE, base_for, features_for, layer_errors, relief_for
from pipeline.build.world import LAKE, cell_layers


class TerrainClassifierTests(unittest.TestCase):
    def test_owned_lake_ignores_land_observations(self):
        observation = {"climate": {"2": 20}, "mapped": {"marsh": .8}}
        self.assertEqual(cell_layers(LAKE, 4, observation, {40: 20}), (8, []))

    def test_documented_exception_does_not_hide_another_failure(self):
        site = {"allowed_unmet": ["base"]}
        self.assertEqual(unexpected_fields(site, ["base"]), [])
        self.assertEqual(unexpected_fields(site, ["base", "relief"]), ["relief"])

    def test_desert_requires_majority_of_valid_ice_free_climate(self):
        self.assertEqual(base_for(0, {4: 4, 5: 3, 6: 6}, {}), 3)
        self.assertEqual(base_for(0, {4: 4, 6: 6}, {}), 2)

    def test_monsoon_and_savanna_have_distinct_bases(self):
        self.assertEqual(base_for(0, {2: 10}, {}), 1)
        self.assertEqual(base_for(0, {3: 10}, {}), 2)

    def test_ice_has_priority_and_tundra_requires_polar_climate(self):
        self.assertEqual(base_for(0, {29: 10}, {70: 6, 60: 4}), 5)
        self.assertEqual(base_for(0, {29: 10}, {70: 4, 60: 6}), 4)

    def test_water_retains_water_class(self):
        self.assertEqual([base_for(i, {4: 10}, {}) for i in (1, 2, 3)], [6, 7, 8])

    def test_plateau_is_flat_and_rugged_land_is_mountainous(self):
        self.assertEqual(relief_for(90, 2), 0)
        self.assertEqual(relief_for(800, 4), 1)
        self.assertEqual(relief_for(800, 14), 2)

    def test_relief_distinguishes_a_gentle_valley_from_a_steep_massif(self):
        self.assertEqual(relief_for(239, 1.2), 0)
        self.assertEqual(relief_for(1071, 11.6), 2)
        self.assertEqual(relief_for(906, 11.3), 1)

    def test_independent_features_can_coexist(self):
        self.assertEqual(features_for(1, {2: 10}, {10: 5, 40: 3, 70: 2},
                                      {"marsh": 0.1, "floodplain": 0.2}), [2, 3, 4, 7, 8])

    def test_mangroves_do_not_make_rainforest(self):
        self.assertEqual(features_for(1, {2: 10}, {95: 9, 40: 1}, {}), [5])

    def test_no_data_has_neutral_base_and_no_features(self):
        self.assertEqual(base_for(0, {}, {}), 0)
        self.assertEqual(base_for(0, {2: 2}, {}), 0)
        self.assertEqual(features_for(0, {}, {}, {}), [])

    def test_validation_fixture_has_43_distinct_sites_and_known_classes(self):
        fixtures = json.loads(FIXTURE.read_text())
        self.assertEqual(len({site["name"] for site in fixtures}), 43)
        bases = {row["key"] for row in BASE_TABLE}
        features = {row["key"] for row in FEATURE_TABLE} | {"snow"}
        for site in fixtures:
            with self.subTest(site=site["name"]):
                self.assertTrue(set(site["base"]) <= bases)
                for requirement in site["features"]:
                    self.assertTrue(set(requirement.split("@")[0].split("/")) <= features)

    def test_distance_to_a_shore_segment_includes_its_endpoints(self):
        self.assertEqual(segment_distance((4, 3), (0, 0), (10, 0)), 3)
        self.assertEqual(segment_distance((-4, 3), (0, 0), (10, 0)), 5)

    def test_layered_contract_checks_water_base_and_unique_features(self):
        world = {"water": [2], "base": [7], "features": [[]],
                 "featureSites": [], "featureFootprints": [],
                 "tables": {"base": BASE_TABLE, "features": FEATURE_TABLE}}
        self.assertEqual(layer_errors(world), [])
        world["base"] = [3]
        world["features"] = [[1, 1]]
        self.assertEqual(len(layer_errors(world)), 2)
