import json
import shutil
import subprocess
import unittest
from pathlib import Path

from pipeline.build.advisor_statistics import veteran_columns
from pipeline.build.advisor_tables import advisor_tables, column_table
from pipeline.build.city_conditions import explorer_condition_columns
from pipeline.build.city_economy import explorer_gateway_columns
from pipeline.build.city_view_contract import explorer_output_columns, explorer_profile_columns, explorer_work_columns
from pipeline.build.disasters import advisor_definitions as hazard_definitions
from pipeline.build.state_metrics import advisor_columns
from pipeline.build.workplace import advisor_definitions
from pipeline.build.yields import advisor_definitions as yield_definitions


class AdvisorRegistryTests(unittest.TestCase):
    def test_mixed_unemployment_column_keeps_periods_and_disables_ranks(self):
        base = {"label": "Unemployment", "format": "pct"}
        table = column_table({
            "DL": {"unemployment": {**base, "period": "1 Jul – 30 Sep 2026", "value": .06}},
            "CH": {"unemployment": {**base, "period": "PLFS 2025", "vintage": "older", "value": .10}},
        }, "abbr")
        self.assertTrue(table["fields"][1]["hide_rank"])
        self.assertEqual(table["provenance"]["CH"]["unemployment"]["period"], "PLFS 2025")

    @unittest.skipUnless(shutil.which("node"), "Node is needed to exercise the browser registry")
    def test_registry_and_geography_joins(self):
        definitions = advisor_definitions({
            "period": "Sixth Economic Census (January 2013 – April 2014)",
            "source_id": "shrug_workplace", "industries": {"Electric power": {}},
        }, {"jobs": 50, "share": 0.005, "lq": 1.25})
        yields = yield_definitions([{
            "key": "food", "label": "Food", "unit": "t", "period": "Crop year 2025-26",
            "sources": ["foodgrains_fy26"], "description": "Projected food yield",
        }])
        specs = {
            "pmayu2_completions": {
                "name": "PMAY-Urban 2.0 houses completed or delivered", "unit": "houses per 1,000 residents",
                "group": "schemes", "format": "float", "precision": 3, "period": "3 August 2026",
                "source": "pmayu2_test", "denominator_source": "tg_projections",
            },
            "gsdp_pc": {"name": "GSDP per person", "unit": "₹ / person", "group": "economy",
                        "format": "int", "period": "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)", "source": "gsdp_fy26"},
        }
        metrics = {
            "JK": advisor_columns({"gsdp_pc": {"value": 120000, "source": "gsdp_estimate", "estimated": True}}, specs),
            "LA": advisor_columns({
                "gsdp_pc": {"value": 0, "source": "gsdp_fy26", "period": "Jul 2026"},
                "pmayu2_completions": {"value": 0, "source": "pmayu2_test", "estimated": True},
            }, specs),
        }
        hazards = hazard_definitions([{"type": "Flood"}], "1 Jan – 27 Nov 2026", "Test inventory")
        conditions = explorer_condition_columns({
            "air": {
                "aqi": {"bad_days": 0, "valid_days": 300, "calendar_days": 304, "rank": 57, "covered_cities": 102,
                        "period": "Jan–Oct 2026", "source": "test_aqi"},
                "pm25": {"value": 121.2, "footprint_coverage": 0.8, "period": "Jan–Oct 2026",
                         "source": "test_pm25", "estimated": True},
            },
            "housing": {"market": "Delhi", "index_difference": 14.00, "period": "Apr–Jun 2026",
                        "source": "test_hpi", "provisional": True},
        })
        fixture = {
            "workplace": definitions, "yields": yields, "metrics": metrics, "hazards": hazards,
            "district_veterans": veteran_columns(5, None, district=True), "conditions": conditions,
            "work": explorer_work_columns({"employed_all_ages": 0, "source": "plfs_2026_q3",
                                            "period": "1 Jul – 30 Sep 2026"}),
            "output": explorer_output_columns({
                "yields": {"gold": 250000}, "ranks": {"gdp": 2},
                "yield_meta": {"gold": {"source": "test_gdp", "period": "FY 2025–26"}},
            }),
            "profile": explorer_profile_columns({
                "method": "point", "citizens": {"age": {
                    "counts": {"0_14": 0}, "bands": {"midlife": 42}, "median_band": [35, 39],
                    "source": "worldpop_age", "period": "mid-2026", "estimated": True,
                }},
            }, {}),
            "gateways": explorer_gateway_columns({
                "port": {"name": "Example Port", "distance_km": 0, "source": "test_ports", "period": "November 2026"},
                "airports": {}, "rail": [],
            }),
            "modelled_profile": explorer_profile_columns({
                "method": "ghsl", "citizens": {}, "districts": [{"id": "01-003"}],
                "industry_plaques": [{"label": "Textiles", "period": "Jul 2026", "source": "bharat_tex_2026"}],
            }, {"01-003": "Leh"}),
        }
        root = Path(__file__).resolve().parents[1]
        command = ["node", "tests/advisor_registry.mjs"]
        result = subprocess.run([*command, "--inputs"], input=json.dumps({"fixture": fixture}),
                                cwd=root, check=True, text=True, capture_output=True)
        tables = {}
        for name, data in json.loads(result.stdout).items():
            infrastructure = {"ports": [], "airports": [], "roads": [], "rail": [], **data["infrastructure"]}
            tables[name] = advisor_tables(
                data["world"], data.get("lenses", {"lenses": [], "places": {"counties": {}}}),
                data.get("workplace", {}), data["cities"], data.get("city_view", {"profiles": {}}),
                data.get("states", []), data.get("nation", {}), {"columns": ["geoid"], "rows": []},
                {"types": [], "items": []}, data.get("wonders", {"wonders": []}), infrastructure,
                {"sites": []}, {"sites": []},
            )
        subprocess.run(command, input=json.dumps({"fixture": fixture, "tables": tables}),
                       cwd=root, check=True, text=True)
