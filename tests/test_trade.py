import unittest

from pipeline.build.trade import COASTAL_CARGO, PERIOD, route_document, sea_path
from pipeline.core.hexgrid import HexGrid


class TradeTests(unittest.TestCase):
    def test_coastal_rows_match_report_total_and_scope(self):
        self.assertEqual(len(COASTAL_CARGO), 12)
        self.assertEqual(sum(COASTAL_CARGO.values()), 145_585_776)
        self.assertEqual(COASTAL_CARGO["kolkata"], 3_510_138)
        self.assertEqual((PERIOD["period_start"], PERIOD["period_end"]), ("2026-04-01", "2026-10-31"))

    def test_sea_path_detours_around_land_and_lakes(self):
        grid = HexGrid(18, 5, 3)
        start, end = 5, 9
        sea = set(range(grid.size)) - {6, 7, 8}
        path = sea_path(grid, sea, start, {end})
        self.assertEqual((path[0], path[-1]), (start, end))
        self.assertTrue(set(path) <= sea)
        self.assertTrue(all(b in grid.neighbours(a) for a, b in zip(path, path[1:])))
        self.assertIsNone(sea_path(grid, {start, end}, start, {end}))


    def test_trade_routes_keep_path_and_single_port_observation(self):
        network = dict(**PERIOD, backbone=[1, 2, 3], corridors=["Eastern DFC"],
                       branches=[dict(port_id="port", cells=[4, 5, 2], tonnes=1234)])
        doc = route_document(network, [{"id": "port", "name": "Port"}], {"Eastern DFC": [9, 8, 7]})
        backbone, port, rail = doc["routes"]
        self.assertTrue(backbone["schematic"])
        self.assertEqual(port["path"], [4, 5, 2])
        self.assertEqual(port["tons_k"], 1.234)
        self.assertEqual(port["period"], "1 Apr 2026 – 31 Oct 2026")
        self.assertNotIn("a", port)
        self.assertNotIn("b", port)
        self.assertEqual(rail["path"], [9, 8, 7])
        self.assertNotIn("tons_k", rail)
