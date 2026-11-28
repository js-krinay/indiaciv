import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pipeline.build.cities import city_gva, gva_columns, projected_population_history
from pipeline.build.city_conditions import check_housing_output, explorer_condition_columns, housing_market
from pipeline.build.city_view_contract import citizen_mix
from pipeline.india.city_conditions_sources import MARKETS
from pipeline.build.citizens import commute_analogues, resident_industries
from pipeline.build.districts import site_observation
from pipeline.india.census_work import member_industry_details
from pipeline.india.workplace import NIC, PLAQUE_NIC, detail_shares, observation


class CityAnaloguesTest(unittest.TestCase):
    def test_history_uses_only_matched_july_projections(self):
        place = {"population": 1000125, "population_midyear": {"2025": 900000, "2026": 1000125},
                 "growth_period": "1 Jul 2025 – 1 Jul 2026"}
        self.assertEqual(projected_population_history(place), {"2025": 900000, "2026": 1000125})
        self.assertIsNone(projected_population_history({**place, "growth_period": "2026"}))

    def test_commute_shares_keep_the_original_other_workers_denominator(self):
        record = {"period": "Census 2011", "vintage": "older", "source": "b28", "values": {
            "Car/Jeep/Van": .07, "Tempo/Autorickshaw/Taxi": .03, "No travel": .2}}
        result = commute_analogues(record)
        self.assertEqual([row["value"] for row in result.values()], [.07, .03, .2])
        self.assertTrue(all(row["vintage"] == "older" for row in result.values()))
        record["values"].update({"On foot": .2, "Bus and train": .15, "Bicycle": .04,
                                 "Moped/Scooter/Motor Cycle": .05, "Water transport": .01, "Any other": .05})
        mix = citizen_mix({"census_civic": {"commute": record}}, {}, {})
        self.assertAlmostEqual(mix["commute"]["shares"]["other"], .25 / .60)
        self.assertEqual(set(mix), {"commute"})

    def test_industries_keep_zero_and_omit_missing_codes(self):
        record = {"period": "Census 2011", "vintage": "older", "source": "b18",
                  "values": {"manufacturing": .27, "mining": 0}}
        rows = resident_industries(record)
        self.assertEqual({key: value["value"] for key, value in rows.items()},
                         {"mining": 0, "manufacturing": .27})
        self.assertTrue(all(row["hide_rank"] for row in rows.values()))

    def test_b18_detail_requires_every_member_and_uses_eligible_workers(self):
        records = {"a": {"701": 20, "06": 10}, "b": {"701": 30}}
        detail = member_industry_details(records, {"a", "b"}, {"published": 510, "excluded": 10})
        self.assertEqual(detail, {"701": .10})
        record = {"period": "Census 2011", "vintage": "older", "source": "b18",
                  "values": {"professional": .32}}
        rows = resident_industries(record, detail)
        self.assertEqual(rows["professional"]["value"], .32)
        self.assertEqual(rows["professional_excluding_head_offices"]["value"], .22)
        self.assertEqual(rows["management"]["value"], .10)

    def test_workplace_detail_keeps_each_shric_bucket_once_and_nulls_missing_inputs(self):
        groups = dict.fromkeys(NIC, 0)
        groups.update({73: 25, 35: None})
        values = (125, 100, 35, None, *groups.values())
        result = detail_shares(values)
        self.assertEqual(result["Software publishing, programming and hosting"], .25)
        self.assertNotIn("Electricity, gas, steam and water", result)
        self.assertEqual(result["Civilian-filtered manufacturing"], .35)
        original = values[:4 + len(PLAQUE_NIC)]
        self.assertEqual(observation(original, original), observation(values, values))

    def test_hpi_keeps_the_registration_market_and_signed_index_points(self):
        self.assertIsNone(housing_market("Surat", MARKETS))
        self.assertEqual(housing_market("Bengaluru", MARKETS)["market"], "Bangalore")
        profile = {"housing": housing_market("Delhi", MARKETS)}
        delhi = explorer_condition_columns(profile)["city_housing_index_difference"]
        self.assertEqual(delhi["value"], -3.78)
        self.assertTrue(delhi["hide_rank"])

    def test_campus_fact_requires_the_verified_campus(self):
        site = {"kind": "campus", "name": "NIT Rourkela", "district": "21-374"}
        result = site_observation("21387", site)
        self.assertEqual(result["value"], 1407)
        self.assertEqual(result["vintage"], "older")
        self.assertIsNone(site_observation("21387", {**site, "name": "Another campus"}))

    def test_housing_output_rejects_raw_index_in_either_public_asset(self):
        cities = {"delhi": {"name": "Delhi"}}
        housing = housing_market("Delhi", MARKETS)
        profiles = {"delhi": {"housing": housing}}
        columns = ["id", "city_housing_index_difference"]
        with TemporaryDirectory() as temp:
            path = Path(temp)
            table = path / "advisor_tables.json"
            table.write_text(json.dumps({"metros": {"columns": columns, "rows": [["delhi", -3.78]]}}))
            self.assertEqual(check_housing_output(path, cities, profiles)[0][0], "PASS")
            self.assertEqual(check_housing_output(path, cities, {
                "delhi": {"housing": {**housing, "index": 96.22}},
            })[0][0], "FAIL")
            table.write_text(json.dumps({"metros": {"columns": columns, "rows": [["delhi", 96.22]]}}))
            self.assertEqual(check_housing_output(path, cities, profiles)[0][0], "FAIL")

    def test_city_gva_requires_complete_matched_sector_partitions(self):
        shares = {"agriculture": .1, "industry": .2, "services": .7}
        mix = {"DL": {"source": "delhi_gsva_fy26", "shares": shares}}
        benchmark = {"agriculture": 100, "industry": 200, "services": 700}
        rows = {"DL": {"urban_population": 200}}
        result = city_gva({"DL": 100}, {"DL": 250}, rows, mix, benchmark)
        self.assertAlmostEqual(result["shares"]["agriculture"], .10)
        self.assertAlmostEqual(result["location_quotients"]["industry"], 1)
        column = gva_columns(result)["gva_industry_concentration"]
        self.assertIn("city share ÷ India share", column["label"])
        self.assertTrue(column["hide_rank"])
        self.assertTrue(column["estimated"])
        self.assertIsNone(city_gva({"DL": 100, "UP": 50}, {"DL": 250}, rows, mix, benchmark))
        self.assertIsNone(city_gva({"DL": 100}, {"DL": 250}, rows, mix, {**benchmark, "services": 0}))
