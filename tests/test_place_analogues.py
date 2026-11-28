import unittest

from pipeline.build import disasters, military, wonders
from pipeline.sources.gem_resources import parse_sites


class PlaceAnalogueTests(unittest.TestCase):
    def test_cold_wave_days_are_one_series(self):
        records = disasters.hazard_observations()
        cold, = [record for record in records if record["id"] == "delhi_cold_wave_days"]
        self.assertEqual(cold["value"], len(set(cold["dates"])))
        self.assertEqual(cold["value"], 6)

    def test_fire_joins_by_state_and_rejects_ambiguous_drought_parent(self):
        records = disasters.hazard_observations([
            {"state_code": 29, "name": "Bijapur", "code": 557},
            {"state_code": 29, "name": "Bijapur", "code": 559},
            {"state_code": 22, "name": "Bijapur", "code": 417},
        ])
        self.assertEqual(len(records), 2)
        fire = records[1]
        self.assertEqual((fire["district"], fire["vintage"], fire["unit"]), ("22-417", "older", "%"))
        self.assertEqual(fire["value"], round(100 * 5018 / 203544, 2))

    def test_budget_shares_keep_pensions_and_reject_incomplete_editions(self):
        budget = {"total": 100, "heads": {"Capital": 20, "Revenue": 45, "Pensions": 30,
                                         "Civil organisations": 5}, "source": "budget",
                  "period": "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"}
        shares = military.budget_heads(budget)
        self.assertEqual([row["value"] for row in shares], [20, 45, 5, 30])
        del budget["heads"]["Pensions"]
        self.assertEqual(military.budget_heads(budget), [])

    def test_kaziranga_bound_uses_exact_wonder_id(self):
        other = {"id": "other", "name": "Kaziranga National Park"}
        park = {"id": "whc-337", "metrics": None}
        wonders.attach_park_visits([other, park])
        self.assertNotIn("metrics", other)
        visit = park["metrics"]["park_visits"]
        self.assertEqual((visit["value"], visit["comparator"], visit["period"]), (22000, ">", "October 2026"))
        self.assertNotIn("rank", visit)

    def test_faith_distribution_keeps_unstated_responses_in_denominator(self):
        survey = wonders.national_faith_distribution()
        self.assertEqual((survey["period"], survey["vintage"]), ("Census 2011", "older"))
        self.assertAlmostEqual(sum(part["value"] for part in survey["parts"]), 100, places=1)
        self.assertEqual(survey["parts"][-1]["label"], "Religion not stated")

    def test_research_observation_has_unique_science_join_and_display_precision(self):
        point = {"name": "NIT Rourkela", "kind": "NIT", "district": "21-374"}
        self.assertIsNone(wonders.sponsored_research_observation([point, point]))
        row = wonders.sponsored_research_observation([point])
        self.assertEqual((row["value"], row["vintage"]), (897514, "older"))
        self.assertNotIn("rank", row)

    def test_park_designation_requires_verified_osm_extent(self):
        park = {"designation": "National park", "authority_source": "wii_protected", "source": "relation/123"}
        self.assertIsNone(wonders.mapped_park_designation(park))
        self.assertEqual(wonders.mapped_park_designation({**park, "cells": [1, 2]})["value"], "National park")

    def test_positive_gem_records_preserve_a_single_mixed_site(self):
        row = {"country-area1": "India", "status": "operating", "Latitude": 20, "Longitude": 80,
               "name": "Example Oil and Gas Field", "project-id": "p",
               "prod-oil": 12, "prod-year-oil": 2020, "prod-gas": 54, "prod-year-gas": 2019}
        site, = parse_sites([row, {**row, "unit-id": "different-unit"}], "oil")
        self.assertEqual(site["type"], "oil_gas")
        self.assertEqual(site["id"], "p")
        self.assertEqual(site["reported_products"], ["oil", "gas"])
