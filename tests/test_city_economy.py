import shutil
import subprocess
import unittest
from pathlib import Path

from pipeline.build.city_economy import city_finances, city_sector_output, gateway_records, segment_distance
from pipeline.build import city_economy
from pipeline.core.hexgrid import HexGrid
from pipeline.build.state_metrics import FY
from pipeline.india.city_economy_sources import state_sector_mix


class CityEconomyTests(unittest.TestCase):
    def test_matched_nominal_growth_needs_a_published_pair_for_every_state(self):
        result = city_economy.matched_city_output_growth({"KL": .1})
        self.assertAlmostEqual(result["value"], 1427145.23 / 1248533.01 - 1)
        self.assertEqual(result["source"], ["kerala_matched_gsdp_fy26"])
        self.assertEqual(result["vintage"], FY)
        self.assertIn("separate from headline city GDP", result["description"])
        self.assertIsNone(city_economy.matched_city_output_growth({"KL": .1, "LD": .2}))

    def test_matched_nominal_growth_uses_the_same_state_weights_for_both_years(self):
        result = city_economy.matched_city_output_growth({"KL": .1, "JH": .2})
        before = .1 * 1_248_533.01 + .2 * 516_255
        after = .1 * 1_427_145.23 + .2 * 556_286
        self.assertAlmostEqual(result["value"], after / before - 1)
        self.assertEqual(result["source"], ["jharkhand_matched_gsdp_fy26", "kerala_matched_gsdp_fy26"])

    def test_andhra_pradesh_output_fills_detailed_sectors_without_changing_the_broad_mix(self):
        mix = state_sector_mix("AP", "Andhra Pradesh", FY, for_city=True)
        result = city_sector_output({"AP": 10000}, {"AP": mix})
        self.assertEqual(result["values"]["industry"], 2367)
        self.assertEqual(sum(result["values"][key] for key in ("mining", "manufacturing", "construction", "utilities")),
                         2367)
        self.assertIn("andhra_pradesh_gsva_detail_fy26", result["source"])
        self.assertEqual(result["vintage"], FY)

    def test_historical_split_keeps_input_period_and_method(self):
        output = city_sector_output({"UP": 10000}, {"UP": state_sector_mix("UP", "Uttar Pradesh", FY, for_city=True)})
        data = output["fields"]["mining"]
        self.assertEqual(data["period"], FY)
        self.assertEqual(data["input_weights"]["vintage"], "older")
        self.assertIn("FY 2024-25", data["input_weights"]["period"])
        self.assertIn("residual", data["description"])

    def test_odisha_city_keeps_previously_available_estimates(self):
        mix = state_sector_mix("OD", "Odisha", FY, for_city=True)
        self.assertTrue(mix["estimated"])
        self.assertEqual(mix["source"], ["rbi_state_gsva", "mospi_national_gva_fy26"])
        self.assertAlmostEqual(mix["detail"]["mining"] / mix["detail"]["utilities"], 9.5 / 3.3)
        self.assertNotEqual(mix["detail"]["construction"], .096)

    def test_telangana_detail_allocates_only_the_remaining_industry_share(self):
        mix = state_sector_mix("TS", "Telangana", FY, for_city=True)
        self.assertAlmostEqual(mix["detail"]["mining"] / mix["detail"]["utilities"], 35892 / 37692)
        self.assertAlmostEqual(sum(mix["detail"].values()), mix["shares"]["industry"])
        self.assertEqual(mix["detail_source"]["mining"], "telangana_gsva_fy26")
        self.assertEqual(state_sector_mix("TS", "Telangana", FY)["source"], "telangana_gsva_fy26")

    def test_older_nominal_industry_weights_can_split_the_current_residual(self):
        for state, mining, utilities in (("UP", 24890, 73145), ("KL", 299377, 1526237),
                                         ("TN", 8955, 80127), ("BR", 3691, 20263)):
            with self.subTest(state=state):
                mix = state_sector_mix(state, state, FY, for_city=True)
                self.assertAlmostEqual(mix["detail"]["mining"] / mix["detail"]["utilities"], mining / utilities)
                self.assertAlmostEqual(sum(mix["detail"].values()), mix["shares"]["industry"])

    def test_benchmarked_detail_preserves_the_existing_city_industry_total(self):
        for state, mining, utilities in (("KA", 19598, 44660), ("MP", 2.96, 3.35),
                                         ("RJ", 3.30, 3.20), ("JK", .40, 4.57)):
            with self.subTest(state=state):
                mix = state_sector_mix(state, state, FY, for_city=True)
                self.assertAlmostEqual(mix["detail"]["mining"] / mix["detail"]["utilities"], mining / utilities)
                self.assertAlmostEqual(sum(mix["detail"].values()), mix["shares"]["industry"])

    def test_rank_uses_cohort_and_preserves_ties_and_missing(self):
        cities = {
            "a": {"population": 10, "yields": {"gold": 1000}},
            "b": {"population": 20, "yields": {"gold": 1000}},
            "c": {"population": 10, "yields": {"gold": None}},
            "outside": {"population": 1, "yields": {"gold": 9000}},
        }
        rows = city_finances({key: cities[key] for key in ("a", "b", "c")})
        self.assertEqual(rows["a"]["gdp_per_resident"], 100)
        self.assertEqual(rows["a"]["ranks"]["gdp"], 1)
        self.assertEqual(rows["b"]["ranks"]["gdp"], 1)
        self.assertEqual(rows["b"]["ranks"]["gdp_per_resident"], 2)
        self.assertIsNone(rows["c"]["ranks"]["gdp"])
        self.assertTrue(rows["a"]["estimated"])

    def test_sector_output_weights_each_state_and_requires_full_coverage(self):
        mixes = {
            "A": {"shares": {"agriculture": .2, "industry": .3, "services": .5}, "source": "a"},
            "B": {"shares": {"agriculture": .5, "industry": .1, "services": .4}, "source": "b"},
        }
        result = city_sector_output({"A": 100, "B": 300}, mixes)
        self.assertEqual(result["values"], {"agriculture": 170, "industry": 60, "services": 170})
        self.assertIsNone(city_sector_output({"A": 100, "C": 300}, mixes))

    def test_gateway_types_and_distance_use_mapped_points(self):
        city = {"x": 10, "y": 0, "cell": 0}
        point = {"x": 20, "y": 0, "id": "p", "name": "Major", "category": "Major port", "cargo": 50}
        airport = {"x": 7, "y": 0, "id": "a", "name": "Airport", "size": "large"}
        closed = dict(airport, id="unscheduled", x=10, scheduled_service=False)
        infra = {"ports": [dict(point, x=11, category="Non-major port"), point], "airports": [airport, closed]}
        rails = {"Eastern DFC": [0, 1], "Distant route": [8, 9]}
        result = gateway_records(city, {"cells": [{"cell": 0}]}, infra, rails, HexGrid(18, 5, 2))
        self.assertEqual(result["port"]["distance_km"], 10)
        self.assertNotIn("cargo", result["port"])
        self.assertEqual(result["airports"]["large"]["distance_km"], 3)
        self.assertEqual([(r["name"], r["distance_km"]) for r in result["rail"]], [("Eastern DFC", 0)])
        self.assertEqual(segment_distance((3, 4), (0, 0), (10, 0)), 4)

    def test_bengaluru_uses_nearby_main_line_when_no_corridor_is_mapped(self):
        city = {"name": "Bengaluru", "x": 1145.8, "y": 2878, "cell": 11699}
        unnamed = [11591, 11699, None]
        mysuru = [11699, 11808, "Mysuru–Bengaluru line"]
        infra = {"main_lines": [unnamed, mysuru, [0, 1, "Distant main line"]]}
        grid = HexGrid(18, 109, 139)
        profile = {"cells": [{"cell": index} for index in (11590, 11591, 11699, 11700, 11809)]}
        result = gateway_records(city, profile, infra, {}, grid)
        self.assertEqual([(r["main_line"], r["name"], r["distance_km"]) for r in result["rail"]],
                         [(True, "Main line", 1)])
        named_main = gateway_records(city, profile, {"main_lines": [mysuru]}, {}, grid)
        self.assertEqual(named_main["rail"][0]["name"], "Mysuru–Bengaluru line")
        named = gateway_records(city, profile, infra, {"Named corridor": mysuru[:2]}, grid)
        self.assertEqual([r["name"] for r in named["rail"]], ["Named corridor"])

    @unittest.skipUnless(shutil.which("node"), "Node is needed to test Compare")
    def test_compare_labels_periods_and_omits_empty_columns(self):
        subprocess.run(["node", "tests/city_compare.mjs"], cwd=Path(__file__).resolve().parents[1], check=True)
