import unittest

from pipeline.build.trade import COASTAL_CARGO, PERIOD, sea_path
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
