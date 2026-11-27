import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.build.wonders import attach_protection, place_wonders, select_parks, select_research
from pipeline.core.hexgrid import HexGrid
from pipeline.india.wonders import read_snapshot


class WonderTests(unittest.TestCase):
    def test_linked_protection_uses_only_accepted_hexes(self):
        wonders = [dict(id="wetland", cells=None), dict(id="point", cells=None)]
        sites = [
            dict(id="rsis-1", wonder="wetland", cells=None),
            dict(id="osm-rsis-1", ramsar_id="rsis-1", wonder=None, cells=[2, 3]),
            dict(id="wii-example", wonder="point", cells=[]),
        ]
        attach_protection(wonders, sites)
        self.assertEqual(wonders[0]["cells"], [2, 3])
        self.assertEqual(wonders[0]["extent_sources"], ["osm_protected"])
        self.assertIsNone(wonders[1]["cells"])

    def test_park_selection_orders_by_official_area_and_keeps_accepted_cells(self):
        sites = [
            dict(id="wii-rj-small", designation="National park", area_ha=50, cells=None),
            dict(id="ntca-1", designation="Tiger reserve", area_ha=1000, cells=[1]),
            dict(id="wii-la-large", designation="National park", area_ha=100, cells=[2, 5]),
            dict(id="wii-la-missing", designation="National park", area_ha=None, cells=None),
        ]
        self.assertEqual([(s["id"], s["cells"]) for s in select_parks(sites)],
                         [("wii-la-large", [2, 5]), ("wii-rj-small", None)])

    def test_research_inventory_orders_within_class_and_limits_wonders_to_iisc_iits_and_iisers(self):
        points = [dict(name=name, kind=kind) for name, kind in [
            ("IIT Z", "IIT"), ("IIT A", "IIT"), ("IPRC", "ISRO and DoS"),
            ("PRL", "ISRO and DoS"), ("AIIMS Example", "AIIMS"),
            ("NIT Example", "NIT"), ("CSIR Example", "CSIR"),
            ("IISc", "IISc"), ("IISER Example", "IISER"),
        ]]
        result = select_research(points)
        self.assertEqual([(p["name"], p["rank"], p["institution_count"]) for p in result],
                         [("IISER Example", 1, 1), ("IISc", 1, 1), ("IIT A", 1, 2), ("IIT Z", 2, 2)])

    def test_red_fort_collision_stays_in_delhi(self):
        grid = HexGrid(18, 10, 10)
        delhi = grid.index(4, 4)
        x, y = grid.center(4, 4)
        y += 13  # A southward offset from this anchor crosses the Delhi boundary.
        owner = [1] * grid.size  # Uttar Pradesh around a single Delhi cell
        owner[delhi] = 0
        common = dict(lat=0, lon=0, kind="built", state="Delhi", subtype="fort", motif_group="fort",
                      era="Mughal era", description="A Delhi landmark.", foreign_side=False)
        rows = [
            dict(common, id="india-gate", name="India Gate", selection_rules=["owner_named"]),
            dict(common, id="whc-231", name="Red Fort", selection_rules=["unesco_inscribed"]),
        ]
        named, fort = place_wonders(rows, grid, owner, lambda lon, lat: (x, y), {"Delhi": "DL"})
        self.assertNotEqual((fort["draw_x"], fort["draw_y"]), (named["draw_x"], named["draw_y"]))
        self.assertEqual(grid.cell_at(fort["draw_x"], fort["draw_y"]), delhi)
        self.assertEqual((fort["x"], fort["y"], fort["cell"]), (round(x, 6), y, delhi))

    def test_matching_snapshot_is_loaded(self):
        payload = b'{"as_of":"2026-11-27","wonders":[]}'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wonders.json"
            path.write_bytes(payload)
            with patch("pipeline.india.wonders.CHECKSUM", hashlib.sha256(payload).hexdigest()):
                self.assertEqual(read_snapshot(path), {"as_of": "2026-11-27", "wonders": []})

    def test_modified_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wonders.json"
            path.write_text("{}")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                read_snapshot(path)

    def test_island_and_foreign_points_keep_their_projected_cells(self):
        points = {1: (90, 76), 2: (184, 145)}
        for radius, island, foreign in ((25, 22, 44), (18, 32, 55)):
            grid = HexGrid(radius, 10, 10)
            owner = [0] * grid.size
            owner[island], owner[foreign] = -1, -2
            rows = [
                dict(id="island", name="Island", lat=0, lon=1, kind="natural", state="Goa",
                     subtype="volcano", motif_group="volcanic", era="Natural landscape",
                     description="Volcanic island.", selection_rules=["regional_sample"], foreign_side=False),
                dict(id="mount-kailash", name="Mount Kailash", lat=0, lon=2, kind="natural", state="Tibet",
                     subtype="peak", motif_group="mountain", era="Natural landscape",
                     description="Sacred summit.", selection_rules=["owner_named"], foreign_side=True),
            ]
            result = {row["id"]: row for row in place_wonders(rows, grid, owner, lambda lon, lat: points[lon], {"Goa": "GA"})}
            self.assertEqual(result["island"]["cell"], island)
            self.assertEqual(result["island"]["state"], "GA")
            self.assertEqual(result["mount-kailash"]["cell"], foreign)
            self.assertEqual(result["mount-kailash"]["name"], "Mount Kailash (Tibet)")
            self.assertIsNone(result["mount-kailash"]["state"])
