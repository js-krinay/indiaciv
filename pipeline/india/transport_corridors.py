"""Ordered geographic checkpoints for the operating railway corridors."""

import math
from collections import defaultdict

# Ordered checkpoints keep a connected but unrelated route from satisfying a long corridor.
RAIL_CORRIDORS = {
    "Delhi–Mumbai": [(77.22, 28.64), (75.88, 25.22), (73.20, 22.31), (72.83, 18.94)],
    "Delhi–Kolkata": [(77.22, 28.64), (80.35, 26.45), (83.12, 25.28), (85.00, 24.80),
                      (86.43, 23.80), (88.34, 22.58)],
    "Mumbai–Chennai": [(72.83, 18.94), (73.88, 18.53), (76.93, 17.28), (77.37, 15.17),
                       (79.51, 13.64), (80.28, 13.08)],
    "Kolkata–Chennai": [(88.34, 22.58), (87.32, 22.34), (86.93, 21.49), (85.84, 20.26),
                        (83.21, 17.72), (80.62, 16.52), (80.28, 13.08)],
    "Delhi–Chennai": [(77.22, 28.64), (78.56, 25.45), (79.09, 21.15), (80.62, 16.52), (80.28, 13.08)],
    "Mumbai–Kolkata": [(72.83, 18.94), (73.79, 19.95), (75.79, 21.05), (79.09, 21.15),
                      (82.16, 22.08), (86.18, 22.77), (88.34, 22.58)],
    "Mumbai–Mangaluru (Konkan)": [(73.12, 18.99), (73.37, 17), (73.98, 15.27), (74.88, 12.88)],
    "Ludhiana–Sonnagar (Eastern DFC)": [(75.90, 30.86), (77.64, 29.95), (80.21, 26.41), (84.22, 24.86)],
    "Dadri–JNPA (Western DFC)": [(77.58, 28.54), (76.60, 28.20), (75.24, 26.87), (73.60, 25.81),
                                (72.43, 24.15), (72.38, 22.99), (73.19, 22.24), (72.86, 19.57), (72.94, 18.95)],
    "Jammu–Srinagar–Baramulla": [(74.88, 32.71), (74.94, 32.99), (74.88, 33.15), (74.89, 34.03), (74.40, 34.20)],
    "New Jalpaiguri–Guwahati–Dibrugarh": [(88.44, 26.68), (90.57, 26.47), (91.75, 26.18),
                                          (93.13, 26.35), (94.94, 27.45)],
    "Guwahati–Silchar": [(91.75, 26.18), (93.17, 25.76), (92.80, 24.83)],
    "Silchar–Agartala": [(92.80, 24.83), (92.16, 24.37), (91.28, 23.80)],
}

FREIGHT_CORRIDORS = {
    "Ludhiana–Sonnagar (Eastern DFC)": "EDFC",
    "Dadri–JNPA (Western DFC)": "WDFC",
}


class RailTopology:
    """Connected groups of ways, joined by shared OSM node IDs."""

    def __init__(self):
        self.parent = {}
        self.node_way = {}

    def root(self, way):
        while way != self.parent[way]:
            self.parent[way] = self.parent[self.parent[way]]
            way = self.parent[way]
        return way

    def add(self, way, nodes):
        self.parent[way] = way
        root = way
        for node in nodes:
            other = self.node_way.setdefault(node, way)
            if other != way:
                self.parent[self.root(other)] = root

    def connects(self, checkpoints):
        groups = [{self.root(self.node_way[node]) for node in nodes if node in self.node_way}
                  for nodes in checkpoints]
        return bool(set.intersection(*groups))


def source_connections(topologies, node_points):
    """Check that a single component reaches within 30 km of every corridor checkpoint."""
    bins = defaultdict(list)
    for node, (lon, lat) in node_points.items():
        bins[math.floor(lon), math.floor(lat)].append((node, lon, lat))

    def nearby(lon, lat):
        x_scale = 111 * math.cos(math.radians(lat))
        return {
            node
            for x in range(math.floor(lon - 30 / x_scale), math.floor(lon + 30 / x_scale) + 1)
            for y in range(math.floor(lat - 30 / 111), math.floor(lat + 30 / 111) + 1)
            for node, a, b in bins.get((x, y), ())
            if math.hypot((a - lon) * x_scale, (b - lat) * 111) <= 30
        }

    return {name: topologies[FREIGHT_CORRIDORS.get(name, "rail")].connects([nearby(*point) for point in points])
            for name, points in RAIL_CORRIDORS.items()}
