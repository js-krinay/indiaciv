import unittest

from pipeline.build.city_conditions import air_rankings, city_conditions, footprint_pm25, member_events, housing_market


class CityConditionsTest(unittest.TestCase):
    def test_aqi_ranks_all_covered_reporting_cities_and_keeps_zero(self):
        def row(city, poor, days):
            return dict(city=city, state="Delhi", poor=poor, days=days)
        ranks = air_rankings([row("A", 122, 244), row("B", 150, 300), row("C", 0, 304), row("D", 243, 243)])
        self.assertEqual([(r["rank"], r["covered_cities"]) for r in ranks.values()], [(1, 3), (1, 3), (3, 3)])
        self.assertEqual(ranks["c", "delhi"]["bad_days"], 0)
        self.assertNotIn(("d", "delhi"), ranks)

    def test_pm25_weights_district_area_and_reports_partial_coverage(self):
        districts = [dict(id="a", footprint_share=0.25), dict(id="b", footprint_share=0.5),
                     dict(id="c", footprint_share=0.25)]
        self.assertEqual(footprint_pm25(districts, {"a": 30, "b": 60, "c": None})["value"], 50)
        self.assertEqual(footprint_pm25(districts, {"a": 30, "b": 60})["footprint_coverage"], 0.75)
        self.assertIsNone(footprint_pm25(districts, {}))
        self.assertIsNone(footprint_pm25([], {"a": 30}))

    def test_events_match_canonical_member_ids_once_and_keep_matched_districts(self):
        events = [dict(id="storm", districts=["21-388", "21-389", "21-390"]),
                  dict(id="slide", districts=["32-590"])]
        self.assertEqual(member_events({"21-388", "21-390"}, events),
                         [dict(id="storm", districts=["21-388", "21-390"])])
        self.assertEqual(member_events(set(), events), [])

    def test_housing_preserves_published_market_and_leaves_missing_values_blank(self):
        markets = {"Bangalore": {"index": "118.40"}}
        self.assertEqual(housing_market("Bengaluru", markets)["index"], "118.40")
        self.assertNotIn("base", housing_market("Bengaluru", markets))
        self.assertIsNone(housing_market("Bengaluru", markets)["yoy_pct"])
        self.assertIsNone(housing_market("Surat", markets))

    def test_shipped_hazards_match_patna_and_vijayawada_footprints(self):
        cases = (
            ("Patna", "Bihar", ["10-230", "10-220", "10-219"],
             ("pib_2311105", "Flood", "September flooding in Bihar", ["10-220"])),
            ("Vijayawada", "Andhra Pradesh", ["28-547", "28-548"],
             ("pib_2332675", "Cyclone", "Cyclone Arnab", ["28-547"])),
        )
        for name, state, members, expected in cases:
            with self.subTest(city=name):
                profile = {"districts": [{"id": district} for district in members]}
                conditions = city_conditions({"name": name}, profile, state, {}, {})
                self.assertEqual([
                    (event["source"], event["type"], event["label"], event["districts"])
                    for event in conditions["hazards"]
                ], [expected])
