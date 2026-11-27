import unittest

from pipeline.build.yields import (
    allocate, gold_city, production, culture, count_sites, cropland_weights, district_state_map,
    footprint_overlaps, sites_in_footprint,
)
from pipeline.build.science import research_by_state, science_yield
from pipeline.core.geo import Shape
from pipeline.core.store import load_interim
from pipeline.india import GHSL_UCDB
from pipeline.india.science_sources import ROSTER


class YieldTests(unittest.TestCase):
    def test_gold_uses_urban_population_and_preserves_missing(self):
        states = {"AA": {"urban_population": 10, "values": {"gold": 1000}}}
        self.assertEqual(gold_city(states, {"AA": 2}, {"AA": 2}), 200)
        states["AA"]["values"]["gold"] = None
        self.assertIsNone(gold_city(states, {"AA": 2}, {"AA": 2}))

    def test_production_combines_commensurately_scaled_inputs(self):
        self.assertEqual(production(10_000, 1_000, 10), 12)
        self.assertIsNone(production(None, 1_000, 10))

    def test_gold_city_spans_states_and_caps_incompatible_urban_totals(self):
        states = {"AA": {"urban_population": 10, "values": {"gold": 1_000}},
                  "BB": {"urban_population": 40, "values": {"gold": 2_000}}}
        self.assertEqual(gold_city(states, {"AA": 3, "BB": 5}, {"AA": 12, "BB": 5}), 500)

    def test_delhi_ncr_uses_clipped_district_overlaps(self):
        try:
            profile = load_interim(GHSL_UCDB)["profiles"]["21228"]
        except FileNotFoundError:
            self.skipTest("prepare City View footprints first")
        district_states = district_state_map(load_interim("datameet"))
        footprint_hexes = sum(row["hex_fraction"] for row in profile["cells"])
        population, area = footprint_overlaps(profile, district_states, footprint_hexes)
        self.assertAlmostEqual(population["HR"] / population.total(), .11005, places=4)
        self.assertAlmostEqual(area["HR"] / area.total(), .217, places=2)

    def test_city_site_must_be_inside_clipped_footprint_even_in_same_hex(self):
        footprint = Shape([[(0, 0), (1, 0), (1, 1), (0, 1)]])
        sites = [{"cell": 8, "x": .5, "y": .5}, {"cell": 8, "x": 2, "y": 2}]
        self.assertEqual(sites_in_footprint(sites, footprint, 8), sites[:1])
        self.assertEqual(sites_in_footprint(sites, None, 8), sites)

    def test_food_excludes_foreign_and_water_and_weights_fractional_cells(self):
        world = {"owner": [0, 0, 1, -2], "pct": {"crop": [50, 25, 75, 100]}}
        weights = cropland_weights(world)
        self.assertEqual(weights, {0: .5, 1: .25, 2: .75})
        self.assertEqual(allocate(300, weights[1] * .5, sum(weights.values())), 25)

    def test_culture_combines_entries_and_wonders(self):
        self.assertEqual(culture(250_000, 3), 5.5)

    def test_science_weights_institutes_and_keeps_unmatched_places_in_states(self):
        by_state = research_by_state({
            "IIT": [("IIT A", "AA", "Metro"), ("IIT B", "AA", "Small town")],
            "NIT": [("NIT A", "AA", "Metro")],
            "AIIMS under development": [("AIIMS A", "AA", "Metro")],
        })
        self.assertEqual(science_yield({"IIT": 1, "NIT": 1, "AIIMS under development": 1}), 3)
        self.assertEqual(science_yield(by_state["AA"]), 5)

    def test_science_roster_covers_named_public_networks(self):
        self.assertEqual({"IIT": 23, "IISc": 1, "IISER": 7, "NIT": 31, "AIIMS": 20,
                          "AIIMS under development": 3, "CSIR": 37, "ISRO and DoS": 18},
                         {kind: len(rows) for kind, rows in ROSTER.items()})

    def test_faith_distinguishes_no_matched_site(self):
        self.assertEqual(count_sites([{"cell": 8}], {9}), 0)
