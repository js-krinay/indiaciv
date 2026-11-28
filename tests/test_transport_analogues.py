import unittest

from pipeline.build.almanac import make_entries
from pipeline.build.trade import coastal_observations
from pipeline.india.airport_traffic import airport_metrics, report_totals
from pipeline.india.coastal_shipping import relative_band
from pipeline.india.port_directions import non_major_port_directions, shares


class PortAlmanacTest(unittest.TestCase):
    def test_legacy_port_record_uses_canonical_labels_and_unit(self):
        port = {"name": "Example port", "overseas_direction": {
            "loaded": .25, "unloaded": .75, "period": "FY 2024-25 (1 Apr 2024 – 31 Mar 2025)",
            "vintage": "older", "source_id": "mopsw_basic_ports_2025",
        }}
        world = {"grid": {"cols": 1, "rows": 1, "radius": 18}}
        pages = make_entries(world=world, infrastructure={"ports": [port]})
        facts = pages["About this map"]["Ports · overseas cargo direction"][0]["facts"]
        self.assertEqual([fact["formatted"] for fact in facts], ["75 %", "25 %"])
        self.assertEqual(facts[0]["label"], "Share of this port’s overseas cargo unloaded")
        self.assertEqual(facts[0]["source"], "mopsw_basic_ports_2025")


class AirportTrafficTest(unittest.TestCase):
    def test_exact_match_uses_each_period_denominator_and_actual_growth(self):
        report = {"Grand Total": (200, 100), "GOA": (10, 10), "GOA (MOPA)": (20, 0)}
        rows = airport_metrics(report, {"GOI": "GOA", "GOX": "GOA (MOPA)", "XXX": "MOPA"}, passenger=True)
        self.assertEqual(rows["GOI"], {"share": "5.000%", "previous_share": "10.000%", "change": "0.000%"})
        self.assertEqual(rows["GOX"], {"share": "10.000%", "previous_share": "0.000%"})
        self.assertNotIn("XXX", rows)

    def test_small_positive_freight_is_not_zero(self):
        totals = {"Grand Total": (1000000, 1), "JHARSUGUDA": (3, 0), "ZERO": (0, 0)}
        rows = airport_metrics(totals, {"JRG": "JHARSUGUDA", "XXX": "ZERO"}, passenger=False)
        self.assertEqual(rows, {"JRG": {"share": "<0.001%"}, "XXX": {"share": "0.000%"}})

    def test_reads_total_section_with_fiscal_columns(self):
        report = "ANNEXURE-III A\n Grand Total 1 2 - 3 4 -\nANNEXURE-III C\n"
        report += "  1 नाम GOA (MOPA)  0  1  -  20  40  -50.0%\n Grand Total 1 2 - 100 200 -"
        self.assertEqual(report_totals(report, "III"), {"GOA (MOPA)": (20, 40), "Grand Total": (100, 200)})


class CoastalObservationsTest(unittest.TestCase):
    def test_preserves_direction_groups_and_unclamped_bounds(self):
        rows = [
            (1, ("a",), ("b",), relative_band(22, 25, (22, 25), same_entry=True), ("pol",)),
            (2, ("b", "c"), ("a",), relative_band(20, 23, (22, 25), same_entry=False), ("pol",)),
            (3, ("a",), ("missing",), "Above 0% to 25%", ()),
        ]
        ports = [{"id": key, "name": key, "x": i, "y": 0, "cell": i, "state": "S"}
                 for i, key in enumerate(("a", "b", "c"))]
        city = {"id": "ua", "name": "Closest UA", "x": 0.1, "y": 0, "cell": 12}
        dataset = coastal_observations(ports, {key: (i, 0) for i, key in enumerate(("a", "b", "c"))},
                                       [city], {"rows": rows, "reported_entries": 3})
        first, group = dataset["routes"]
        self.assertEqual(first["band"], "100% (reference entry)")
        self.assertEqual(group["band"], "75–125%")
        self.assertEqual(relative_band(4.8, 5.0, (22, 25), same_entry=False), "Above 0% to 25%")
        self.assertIn("dist_km", first)
        self.assertNotIn("dist_km", group)
        self.assertNotIn("value_musd", first)
        zones = {zone["id"]: zone for zone in dataset["zones"]}
        self.assertEqual(zones[first["a"]]["anchor"]["cell"], city["cell"])
        self.assertEqual(zones[group["a"]]["ports"], ["b", "c"])
        self.assertIsNone(zones[group["a"]]["anchor"])
        self.assertEqual(group["b"], first["a"])

    def test_non_major_port_directions_use_overseas_decimal_columns(self):
        totals = [0] * 12 + [25, 75.5, 101, 80, 20, 100]
        report = "Table 2.2.1\nRedi  " + "  ".join(map(str, totals))
        observation = shares(non_major_port_directions(report))["r15661798"]
        self.assertAlmostEqual(observation["unloaded"], 25 / 100.5)
        self.assertEqual(observation["vintage"], "older")
