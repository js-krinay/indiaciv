import unittest

from pipeline.build.rivers import EdgeGraph, check_hydrography
from pipeline.core.hexgrid import HexGrid


class RiverRoutingTests(unittest.TestCase):
    def setUp(self):
        self.graph = EdgeGraph(HexGrid(10, 12, 12), [0] * 120 + [1] * 24)

    def check_route(self, line, **kwargs):
        path = self.graph.route(line, **kwargs)
        self.assertGreater(len(path), 1)
        self.assertEqual(len(path), len(set(path)))
        self.assertTrue(all(b in self.graph.neighbours[a] for a, b in zip(path, path[1:])))
        return path

    def test_straight(self):
        line = [(25, 45), (135, 45)]
        self.assertEqual(self.check_route(line), self.graph.route(line))

    def test_bend(self):
        path = self.check_route([(30, 40), (80, 115), (130, 40)])
        self.assertGreater(max(self.graph.points[i][1] for i in path), 102)

    def test_confluence(self):
        trunk = self.check_route([(80, 40), (80, 120)])
        tributary = self.check_route([(30, 40), (80, 80)], end=trunk[len(trunk) // 2])
        self.assertEqual(tributary[-1], trunk[len(trunk) // 2])

    def test_delta(self):
        trunk = self.check_route([(80, 40), (80, 95)])
        left = self.check_route([(80, 95), (35, 151)], start=trunk[-1], coast=True)
        right = self.check_route([(80, 95), (140, 151)], start=trunk[-1], coast=True)
        self.assertNotEqual(left[-1], right[-1])

    def test_coast_exit(self):
        path = self.check_route([(80, 70), (120, 159)], coast=True)
        self.assertIn(path[-1], self.graph.coast)

    def test_distributary_stays_distinct_at_coast(self):
        line = [(95, 90), (115, 125), (120, 150)]
        main = self.check_route(line, coast=True)
        existing = {tuple(sorted(edge)) for edge in zip(main, main[1:])}
        branch = self.check_route(line, start=main[0], coast=True, avoid=existing)
        self.assertNotIn(branch[-1], main)
        self.assertIn(branch[-1], self.graph.coast)

    def test_shortcut_keeps_the_course_corridor(self):
        ring = self.graph.corners[30]
        start, end = ring[0], ring[4]
        straight = [self.graph.points[v] for v in (start, end)]
        self.assertEqual(self.graph.shorten(ring[:5], straight, set()), [start, ring[5], end])
        bend = [self.graph.points[v] for v in ring[:5]]
        self.assertEqual(self.graph.shorten(ring[:5], bend, set()), ring[:5])

    def test_cycle_outside_distributary_is_a_failure(self):
        ring = self.graph.corners[30]
        edges = []
        for u, v in zip(ring, ring[1:] + ring[:1]):
            key = tuple(sorted((u, v)))
            edges.append({"corners": list(key), "cells": self.graph.cells[key], "names": ["Kosi"], "downstream": v,
                          "pts": [round(value, 3) for vertex in key for value in self.graph.points[vertex]]})
        results = check_hydrography({"grid": self.graph.grid.to_dict(), "water": [0] * 144,
                                     "river_edges": edges})
        self.assertEqual(results[0][0], "FAIL")
        self.assertIn("cycle outside", results[0][1])
