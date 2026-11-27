import unittest

from pipeline.build.advisor_inventory import inventory_columns
from pipeline.build.infrastructure import airport_city, port_tooltip_fields
from pipeline.build.city_people import qualitative_plaques
from pipeline.india.port_directions import non_major_cargo_shares
from pipeline.india.disaster_sources import INCIDENTS


class InventoryFillTests(unittest.TestCase):
    def test_named_lucknow_cluster_requires_member_district(self):
        self.assertEqual(qualitative_plaques("21318", {"09-176"}), [])
        plaque, = qualitative_plaques("21318", {"09-157", "09-176"})
        self.assertEqual(plaque["label"], "Lucknow Chikankari Cluster")
        self.assertEqual(plaque["district"], "09-157")

    def test_thunderstorm_uses_atlas_district_ids_without_aggregate_casualties(self):
        event = next(row for row in INCIDENTS if row["id"] == "up-thunderstorm-20260513")
        self.assertEqual((event["type"], event["start_date"]), ("Thunderstorm", "2026-05-13"))
        self.assertIn("09-175", event["districts"])
        self.assertEqual(len(event["districts"]), len(set(event["districts"])))
        self.assertNotIn("impact", event)

    def test_port_split_uses_published_totals_and_excludes_mundra_old(self):
        row = "  ".join(["31549", "1944", "33492", "21066", "433", "21499"])
        prefix = "  ".join(["0"] * 12)
        report = f"Table 2.2.1\nKrishnapatnam  {prefix}  {row}\nMundra (Old)  {prefix}  {row}"
        records = non_major_cargo_shares(report)
        self.assertEqual(set(records), {"n3732668135"})
        split = records["n3732668135"]
        self.assertAlmostEqual(split["domestic"], 21499 / 54991)
        self.assertEqual(split["vintage"], "older")
        tooltip = port_tooltip_fields({"cargo": None, "historical_cargo_split": split})
        self.assertEqual(tooltip["foreign"], 33_492_000)
        self.assertEqual(tooltip["domestic"], 21_499_000)
        self.assertEqual(tooltip["period"], split["period"])
        self.assertEqual(tooltip["tons"], 54_991_000)
        self.assertNotIn("rank", tooltip)
        columns = inventory_columns({"ports": [{"name": "Krishnapatnam", "historical_cargo_split": split}]}, None, [])
        mix = columns["non_major_port_cargo_mix"]
        self.assertEqual(mix["value"], "Krishnapatnam · 39.10% coastal · 60.90% overseas")
        self.assertEqual((mix["vintage"], mix["period"]), ("older", split["period"]))

    def test_airport_locality_only_fills_missing_verified_id(self):
        self.assertEqual(airport_city({"id": "26505", "iata": "JRG", "city": None}), "Jharsuguda")
        self.assertEqual(airport_city({"id": "26505", "iata": "JRG", "city": "Existing"}), "Existing")
        self.assertIsNone(airport_city({"id": "26505", "iata": "DEL", "city": None}))
