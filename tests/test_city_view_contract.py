import unittest

from pipeline.build.city_people import age_profile
from pipeline.build.city_view_contract import (
    city_record, citizen_mix, cultivation_mix, explorer_output_columns, explorer_profile_columns, gdp_industry_fields,
    urban_consumption, workplace_districts,
)


class CityViewContractTests(unittest.TestCase):
    def test_explorer_member_shares_keep_their_denominators_and_missing_values(self):
        profile = {"citizens": {}, "method": "ghsl", "districts": [
            {"id": "a", "footprint_share": .25, "population_share": .8},
            {"id": "b", "footprint_share": .75, "population_share": None},
        ]}
        fields = explorer_profile_columns(profile, {"a": "Alpha", "b": "Beta"})
        self.assertEqual(fields["member_footprint_share"]["value"], "Alpha 25.0% · Beta 75.0%")
        self.assertEqual(fields["member_population_share"]["value"], "Alpha 80.0%")
        self.assertTrue(fields["member_population_share"]["estimated"])

    def test_verified_site_cards_and_role_badge_preserve_workplace_specialization(self):
        workplace = {"cities": {"c": {"jobs": 500, "industries": {
            "Scientific research and development": {"qualifies": True, "lq": 2, "local_share": .2},
        }}}}
        profile = {"district_badges": [
            {"kind": "campus", "name": "Research institute", "district": "a",
             "period": "November 2026", "source": "research_points"},
            {"kind": "harbor", "name": "Civil port", "district": "b",
             "period": "November 2026", "source": "cwprs_port_locations"},
        ], "industry_plaques": [{"label": "Chemical cluster", "period": "May 2026", "source": "report"}]}
        result = workplace_districts(workplace, {"c": profile})["cities"]["c"]
        campus, harbor = result["districts"]
        self.assertEqual(campus["sub_lq"], 2)
        self.assertEqual(campus["sites"][0]["name"], "Research institute")
        self.assertEqual(harbor["id"], "harbor")
        self.assertNotIn("sub_lq", harbor)
        self.assertEqual(result["badge"]["label"], "Research City")
        self.assertIn("Chemical cluster", result["roles"][0]["label"])

    def test_role_badge_can_show_without_workplace_counts(self):
        result = workplace_districts({}, {"c": {"capital_designation": {"label": "National capital",
            "period": "November 2026", "source": "soi_political_map"}}})
        row = result["cities"]["c"]
        self.assertNotIn("emp", row)
        self.assertEqual(row["badge"]["label"], "National capital")
        self.assertEqual(row["districts"], [])

    def test_site_preserves_diversified_workplace_badge(self):
        workplace = {"cities": {"c": {"jobs": 500, "industries": {}}}}
        profile = {"district_badges": [{"kind": "campus", "name": "Institute",
                                       "period": "November 2026", "source": "research_points"}],
                   "industry_plaques": [{"label": "Textiles", "period": "May 2026", "source": "report"}]}
        row = workplace_districts(workplace, {"c": profile})["cities"]["c"]
        self.assertIsNone(row["badge"])
        self.assertEqual(row["districts"][0]["via"], "site")
        self.assertEqual(row["roles"], profile["industry_plaques"])

    def test_city_resident_gdp_is_available_outside_city_view(self):
        city = {"gdp_per_capita": 450, "yield_meta": {"gold": {"period": "FY 2025-26", "source": "gsdp"}}}
        self.assertEqual(explorer_output_columns(city)["gdp_per_resident"]["value"], 450)

    def test_older_urban_benchmark_has_its_own_period(self):
        work = {"period": "1 July 2026", "employed_all_ages": 100, "industries": [],
                "state_urban_unemployment_15_plus": .08,
                "unemployment_benchmark": {"period": "PLFS 2025", "vintage": "older", "source": "plfs_annual_2025"}}
        row = city_record({"resident_workforce": work})
        self.assertEqual(row["provenance"]["unemployment"]["vintage"], "older")
        self.assertEqual(row["advisor_columns"]["employed_all_ages"]["period"], "1 July 2026")
        self.assertEqual(row["advisor_columns"]["state_urban_unemployment_15_plus"]["period"], "PLFS 2025")
        self.assertNotIn("jobs", row)

    def test_native_industry_provenance_matches_explorer_field_keys(self):
        record = {"period": "FY 2025-26", "vintage": "FY 2025-26", "estimated": True}
        weights = {"period": "FY 2024-25 (1 Apr 2024 – 31 Mar 2025)", "vintage": "older"}
        field = {**record, "input_weights": weights, "description": "Residual split."}
        city = {"sector_output": {**record, "input_weights": weights, "fields": {"mining": field},
                                  "description": "Industry allocation."}}
        provenance = city_record(city)["provenance"]
        self.assertEqual(provenance["gdp_mining"]["input_weights"], weights)
        self.assertEqual(provenance["gdp_mining"]["status"], "Uses FY 2024-25 weights")

    def test_gdp_detail_uses_the_industry_remainder(self):
        row = gdp_industry_fields({"values": {
            "agriculture": 50, "industry": 100, "services": 200, "mining": 30, "utilities": 20,
        }})
        self.assertEqual(row["gdp_by_industry"], {
            "agriculture": 50, "Other industry": 50, "services": 200, "mining": 30, "utilities": 20,
        })
        self.assertCountEqual(row["gdp_estimated"], row["gdp_by_industry"])

    def test_gdp_detail_reconciles_independent_rounding(self):
        row = gdp_industry_fields({"values": {
            "agriculture": 50, "industry": 100, "services": 200, "construction": 46, "manufacturing": 55,
        }})
        self.assertEqual(sum(row["gdp_by_industry"].values()), 350)
        self.assertNotIn("Other industry", row["gdp_by_industry"])

    def test_header_fields_keep_their_source_periods(self):
        city = {
            "cell": 6, "population": 300, "projected_growth": 0.04,
            "provenance": {"projected_growth": {"source": "un", "period": "2025–2026"}},
            "yields": {"gold": 900}, "yield_meta": {"gold": {"source": "gsdp", "period": "FY 2025-26"}},
        }
        row = city_record(city, {"cells": [{"cell": 6, "population": 300}], "districts": []})
        self.assertEqual(row["gdp"], 900)
        self.assertEqual(row["growth"], 0.04)
        self.assertEqual(row["provenance"]["growth"]["source"], "un")
        self.assertNotIn("unemployment", row)

    def test_citizen_shares_do_not_invent_occupation_counts(self):
        record = {"period": "Census 2011", "vintage": "older", "source": "orgi_work_occupations",
                  "values": {"engineer": 0.7, "other": 0.3}}
        row = citizen_mix({"census_work": {"occupations": record}}, {}, {})["workforce"]
        self.assertEqual(row["period"], "Census 2011")
        self.assertEqual(row["figures"], {"engineer": 20})
        self.assertNotIn("counts", row)

    def test_native_citizen_median_uses_dated_worldpop_bands(self):
        masses = {15: 40, 20: 60}
        row = citizen_mix({"age": age_profile(100, masses)}, masses, {"population": 100})["age"]
        self.assertAlmostEqual(row["median"], 20 + 5 / 6)
        self.assertEqual(row["period"], "mid-2026")

    def test_workplace_badge_uses_only_qualified_civilian_industries(self):
        data = {"cities": {"c": {"jobs": 1000, "industries": {
            "Scientific research and development": {"qualifies": True, "lq": 2.8, "local_share": 0.16},
            "Military": {"qualifies": True, "lq": 9, "local_share": 0.1},
        }}}}
        result = workplace_districts(data, {"c": {}})
        self.assertEqual(result["cities"]["c"]["badge"]["district"], "campus")
        self.assertEqual([d["id"] for d in result["cities"]["c"]["districts"]], ["campus"])
        self.assertEqual(result["vintage"], "older")

    def test_city_uses_year_key_and_native_workforce_denominator(self):
        city = {"population": 300, "population_2026": {"values": {"2026-07-01": 300}, "period": "mid-2026"},
                "resident_workforce": {"employed_all_ages": 102, "employed_15_plus": 100,
                                       "state_urban_unemployment_15_plus": .06,
                                       "industries": [{"sector": "services", "employed": 100}]}}
        result = city_record(city)
        self.assertEqual(result["pop_series"], {"2026": 300})
        self.assertEqual(result["employed"], sum(result["jobs"].values()))
        self.assertNotIn("tile_population", result)

    def test_mw_subtotal_ignores_other_units_and_requires_one_mw_period(self):
        from pipeline.build.resources import mark_mw_subtotals

        power = {"type": "power", "cbsa": "c", "value": 10, "period": "Sep 2026", "source": "power"}
        mine = {"type": "mine", "cbsa": "c", "value": 50, "period": "Aug 2026", "source": "mine"}
        types = [{"id": "power", "unit": "MW"}, {"id": "mine", "unit": "Mt/yr"}]
        mark_mw_subtotals([power, mine], types)
        self.assertEqual(power.pop("aggregate_mw")["period"], "Sep 2026")
        self.assertNotIn("aggregate_mw", mine)
        older_power = {**power, "period": "Aug 2026"}
        mark_mw_subtotals([power, older_power, mine], types)
        self.assertTrue(all("aggregate_mw" not in row for row in (power, older_power, mine)))
        self.assertEqual(older_power["period"], "Aug 2026")
class HistoricalConsumptionTest(unittest.TestCase):
    def test_cultivation_mix_weights_each_urban_district_by_census_workers(self):
        districts = {
            "a": {"workers": 10, "cultivation_workers": 5, "period": "Census 2011", "vintage": "older"},
            "b": {"workers": 90, "cultivation_workers": 5, "period": "Census 2011", "vintage": "older"},
        }
        self.assertEqual(cultivation_mix(["a", "b"], districts)["value"], 0.1)
        self.assertIsNone(cultivation_mix(["a", "c"], districts))

    def test_single_up_member_district_exposes_urban_index_with_scope(self):
        district = {"urban": 105, "period": "HCES 2022–23", "vintage": "older", "source": "pilot"}
        self.assertEqual(urban_consumption(["UP"], ["09-175"], {"09-175": district}),
                         {"value": 105, "period": district["period"], "vintage": "older",
                          "source": "pilot", "scope": "Urban member district"})

    def test_ambiguous_city_memberships_have_no_combined_survey_value(self):
        self.assertIsNone(urban_consumption(["UP", "DL"], ["09-175"], {"09-175": {"urban": 105}}))
        self.assertIsNone(urban_consumption(["UP"], ["09-175", "09-176"], {"09-175": {"urban": 105}}))
