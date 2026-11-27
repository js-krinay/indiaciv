import unittest

from pipeline.build.infrastructure import corridor_connected, corridor_path, links_of, networks, port_tier, ports_on_grid, sample_runs
from pipeline.core.hexgrid import HexGrid
from pipeline.india.transport import line_class, port_name, rail_facility
from pipeline.india.transport_corridors import RailTopology


class InfrastructureTests(unittest.TestCase):
    def test_lifecycle_conflicts_exclude_pinned_ways(self):
        cases = {
            820508038: {"railway": "rail", "construction": "rail", "construction:railway": "rail"},
            217481368: {"highway": "trunk", "ref": "NH53", "construction:highway": "trunk"},
            387075563: {"highway": "trunk", "ref": "NH53", "construction:highway": "trunk"},
        }
        for way, tags in cases.items():
            with self.subTest(way=way):
                self.assertIsNone(line_class(tags))

    def test_only_explicit_operating_evidence_overrides_lifecycle_conflict(self):
        tags = {"railway": "rail", "usage": "main", "proposed:railway": "rail"}
        self.assertIsNone(line_class(tags))
        self.assertIsNone(line_class({**tags, "opening_date": "2026-11-27"}))
        self.assertEqual(line_class({**tags, "opening_date": "2026-11-25"}), ("rail", 0))
        self.assertEqual(line_class({**tags, "railway:status": "operational"}), ("rail", 0))
        for key in ("disused:railway", "abandoned:railway"):
            self.assertIsNone(line_class({"railway": "rail", key: "rail"}))

    def test_rail_filter_excludes_service_and_inactive_track(self):
        self.assertEqual(line_class({"railway": "rail", "usage": "main"}), ("rail", 0))
        self.assertEqual(line_class({"railway": "rail", "usage": "branch"}), ("rail", 1))
        for tags in ({"railway": "construction"}, {"railway": "subway"},
                     {"railway": "rail", "service": "yard"},
                     {"railway": "rail", "usage": "siding"},
                     {"railway": "rail", "disused": "yes"}):
            self.assertIsNone(line_class(tags), tags)

    def test_highways_require_operational_motorway_or_national_trunk(self):
        self.assertEqual(line_class({"highway": "motorway"}), ("roads", 0))
        self.assertEqual(line_class({"highway": "trunk", "ref": "NH 44"}), ("roads", 1))
        self.assertIsNone(line_class({"highway": "trunk", "ref": "SH 44"}))
        self.assertIsNone(line_class({"highway": "motorway", "access": "no"}))

    def test_hex_simplification_keeps_way_junctions(self):
        grid = HexGrid(18, 3, 3)
        self.assertEqual(links_of(grid, [0, 3, 1], set()), [(0, 1)])
        self.assertEqual(links_of(grid, [0, 3, 1], {3}), [(0, 3), (1, 3)])

    def test_port_cargo_publishes_shares_and_rank(self):
        grid = HexGrid(18, 3, 3)
        ports = ports_on_grid(grid, lambda x, y: grid.center(1, 1), [0] * 9, [])
        kandla = ports[0]
        self.assertEqual((kandla["id"], kandla["rank"], kandla["city"]), ("deendayal", 1, "Kandla"))
        self.assertNotIn("tonnes", kandla["cargo"])
        self.assertAlmostEqual(kandla["cargo"]["domestic"], 21_932_146 / 160_114_297, places=6)
        self.assertAlmostEqual(kandla["cargo"]["foreign"] + kandla["cargo"]["domestic"], 1)
        self.assertFalse(kandla["cargo"]["estimated"])

    def test_network_preserves_tagged_metadata_without_inventing_it(self):
        grid = HexGrid(18, 2, 1)
        points = [grid.center(0, 0), grid.center(1, 0)]
        osm = {"junctions": [], "lines": [
            ["roads", 0, "NE 1", points, None, "Example Expressway", "IN:NE"],
            ["rail", 1, None, points, None, "Army supply track", "Naval network"],
        ]}
        rail, roads, *_ = networks(grid, lambda x, y: (x, y), [0, 0], osm)
        self.assertEqual(roads, [[0, 1, 0, "NE 1", "Example Expressway", "IN:NE"]])
        self.assertEqual(rail, [[0, 1, 2]])

    def test_port_size_uses_tonnes_and_has_position_only_tier(self):
        self.assertEqual([port_tier(t) for t in (None, 24_999_999, 25_000_000, 100_000_000)],
                         [3, 2, 1, 0])

    def test_rejected_cells_break_a_sampled_line(self):
        grid = HexGrid(18, 5, 1)
        points = [grid.center(0, 0), grid.center(4, 0)]
        self.assertEqual(list(sample_runs(grid, [0, 0, -2, 0, 0], points)), [[0, 1], [3, 4]])

    def test_confirmed_border_track_can_snap_to_an_adjacent_indian_cell(self):
        grid = HexGrid(18, 5, 2)
        points = [grid.center(0, 0), grid.center(4, 0)]
        owner = [0, 0, -2, 0, 0] + [0] * 5
        self.assertEqual(list(sample_runs(grid, owner, points, lambda x, y: 7)),
                         [[0, 1, 6, 7, 3, 4]])

    def test_corridor_cannot_jump_between_components_at_a_waypoint(self):
        grid = HexGrid(18, 6, 1)
        graph = {0: {1}, 1: {0, 2}, 2: {1}, 3: {4}, 4: {3, 5}, 5: {4}}
        points = [grid.center(c, 0) for c in (0, 2, 5)]
        self.assertFalse(corridor_connected(grid, lambda x, y: (x, y), graph, points))

    def test_dedicated_freight_facilities_use_explicit_tags(self):
        self.assertEqual(rail_facility({"name": "Western Dedicated Freight Corridor"}), "WDFC")
        self.assertEqual(rail_facility({"ref": "EDFC"}), "EDFC")
        self.assertIsNone(rail_facility({"railway": "rail", "usage": "main"}))

    def test_ports_exclude_marinas_and_dry_ports(self):
        self.assertIsNone(port_name({"industrial": "port", "port:type": "dryport", "name": "Inland Container Depot"}))
        self.assertIsNone(port_name({"seamark:type": "harbour", "seamark:harbour:category": "marina",
                                     "name": "Marina"}))
        self.assertEqual(port_name({"industrial": "port", "name": "Pandu Port"}), "Pandu Port")

    def test_source_topology_requires_shared_osm_nodes(self):
        railway = RailTopology()
        railway.add(1, [10, 11])
        railway.add(2, [12, 13])
        self.assertFalse(railway.connects([{10}, {13}]))
        railway.add(3, [11, 12])
        self.assertTrue(railway.connects([{10}, {13}]))

    def test_trunk_path_omits_spurs(self):
        grid = HexGrid(18, 7, 2)
        graph = {i: {n for n in (i - 1, i + 1) if 0 <= n < 7} for i in range(7)}
        graph[3].add(10)
        graph[10] = {3}
        points = [grid.center(i, 0) for i in (0, 3, 6)]
        path = corridor_path(grid, lambda x, y: (x, y), graph, points)
        self.assertIsNotNone(path)
        self.assertNotIn(10, path)
        self.assertTrue(all(b in graph[a] for a, b in zip(path, path[1:])))
