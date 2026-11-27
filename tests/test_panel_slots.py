import unittest

from pipeline.build.city_people import resident_industries
from pipeline.build.disasters import advisor_inventory
from pipeline.build.infrastructure import coastal_port_slots
from pipeline.build.states import unemployment_slot


class PanelSlotTests(unittest.TestCase):
    def test_unemployment_keeps_quarterly_period_and_older_provenance(self):
        self.assertEqual(unemployment_slot({"value": .049, "source": "plfs_q3"})["period"],
                         "1 Jul – 30 Sep 2026")
        older = {"value": .08, "source": "plfs_annual_2025", "period": "PLFS 2025", "vintage": "older"}
        self.assertEqual(unemployment_slot(older), older)
        self.assertEqual(unemployment_slot(None), {})

    def test_resident_industry_counts_reconcile_with_chart_denominator(self):
        jobs, meta = resident_industries(101, [30.1, 29.9, 39.9], {"period": "PLFS 2025", "vintage": "older"})
        self.assertEqual(jobs, {"agriculture": 31, "industry": 30, "services": 40})
        self.assertEqual((meta["employed"], meta["vintage"], meta["estimated"]), (101, "older", True))

    def test_coastal_observation_preserves_all_cargo_and_rank(self):
        port = {"id": "mumbai", "tons": 8, "rank": 3, "year": 2026}
        unmeasured = {"id": "other"}
        coastal_port_slots([port, unmeasured], {"branches": [{"port_id": "mumbai", "tonnes": 20}]})
        self.assertEqual((port["tons"], port["rank"]), (8, 3))
        self.assertEqual(port["coastal_cargo"]["tons"], 20)
        self.assertEqual(port["coastal_cargo"]["year"], 2026)
        self.assertEqual(port["coastal_cargo"]["period"], "1 Apr 2026 – 31 Oct 2026")
        self.assertNotIn("rank", port["coastal_cargo"])
        self.assertNotIn("coastal_cargo", unmeasured)

    def test_latest_report_keeps_sortable_date_and_display_caption(self):
        inventory = {
            "events": [], "period": "2026", "coverage": "", "states": {},
            "districts": {"1": {"count": 1, "last_date": "2026-08-01",
                                "last_caption": "Reported 2026-08-01", "by_type": {}}},
        }
        counties = advisor_inventory(inventory)["fema"]["counties"]
        row = dict(zip(counties["columns"], counties["rows"][0]))
        self.assertEqual(row["last_date"], "2026-08-01")
        self.assertEqual(counties["last_captions"]["1"], "Reported 2026-08-01")
