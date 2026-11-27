"""Generalize projected river courses onto the pointy-top hex graph."""

import heapq
import math
from collections import defaultdict

from ..core.geo import MapProjection, Shape
from ..core.hexgrid import SQRT3, HexGrid
from ..india.hydrography import LAKE_ANCHORS, RIVER_ANCHORS
from ..india.open_rivers import CONTINUATIONS, JUNCTIONS, MEGHNA_INLETS, PARENTS
from .boundaries import overlaps

DELTA_NAMES = {"Ganga delta", "Godavari western distributary", "Krishna eastern distributary"}


def segment_distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2 if length2 else 0
    t = min(1, max(0, t))
    return math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)


class EdgeGraph:
    def __init__(self, grid, water):
        self.grid = grid
        self.points = []
        self.cells = defaultdict(list)
        self.neighbours = defaultdict(set)
        self.corners = []
        ids = {}
        for cell in range(grid.size):
            col, row = grid.col_row(cell)
            x, y = 2 * col + (row & 1), 3 * row
            ring = []
            for dx, dy in ((0, -2), (1, -1), (1, 1), (0, 2), (-1, 1), (-1, -1)):
                key = x + dx, y + dy
                if key not in ids:
                    ids[key] = len(self.points)
                    self.points.append((key[0] * SQRT3 * grid.radius / 2, key[1] * grid.radius / 2))
                ring.append(ids[key])
            self.corners.append(ring)
            for a, b in zip(ring, ring[1:] + ring[:1]):
                self.neighbours[a].add(b)
                self.neighbours[b].add(a)
                self.cells[tuple(sorted((a, b)))].append(cell)
        self.coast = set()
        for edge, cells in self.cells.items():
            classes = {water[cell] for cell in cells}
            if classes in ({0, 1}, {0, 2}):
                self.coast.update(edge)

    def snap(self, point, avoid=()):
        cell = self.grid.cell_at(*point)
        candidates = self.corners[cell] if cell >= 0 else range(len(self.points))
        if avoid:
            available = [v for v in candidates if v not in avoid]
            if not available and cell >= 0:
                available = [v for adjacent in self.grid.neighbours(cell)
                             for v in self.corners[adjacent] if v not in avoid]
            candidates = available or candidates
        return min(candidates, key=lambda v: (math.dist(point, self.points[v]), v))

    def _segment(self, start, end, a, b, avoid, forbidden):
        queue = [(0, start)]
        costs = {start: 0}
        previous = {}
        while queue:
            cost, u = heapq.heappop(queue)
            if u == end:
                break
            if cost != costs[u]:
                continue
            for v in sorted(self.neighbours[u]):
                if v in forbidden and v != end:
                    continue
                offset = segment_distance(self.points[v], a, b) / self.grid.radius
                if forbidden and v != end and offset > 2.5:
                    continue
                candidate = cost + 1 + offset * offset
                if tuple(sorted((u, v))) in avoid:
                    candidate += 3
                if candidate < costs.get(v, math.inf):
                    costs[v] = candidate
                    previous[v] = u
                    heapq.heappush(queue, (candidate, v))
        if end != start and end not in previous:
            return []
        path = [end]
        while path[-1] != start:
            path.append(previous[path[-1]])
        return path[::-1]

    def route(self, line, *, start=None, end=None, coast=False, avoid=frozenset(), forbidden=frozenset()):
        occupied = {v for edge in avoid for v in edge} | forbidden
        start = self.snap(line[0], forbidden) if start is None else start
        if end is None:
            end = self.snap(line[-1], forbidden)
            if coast and self.coast:
                shore = min(self.coast - occupied or self.coast,
                            key=lambda v: (math.dist(line[-1], self.points[v]), v))
                if math.dist(line[-1], self.points[shore]) <= 4 * self.grid.radius:
                    end = shore
        path = [start]
        visited = {start: 0}
        anchor = line[0]
        for i, b in enumerate(line[1:], 1):
            target = end if i == len(line) - 1 else self.snap(b, occupied)
            if i < len(line) - 1 and target == end:
                continue
            segment = self._segment(path[-1], target, anchor, b, avoid, forbidden)
            if not segment:
                if i == len(line) - 1:
                    return []
                continue
            anchor = b
            for v in segment[1:]:
                if v in visited:
                    keep = visited[v] + 1
                    for removed in path[keep:]:
                        del visited[removed]
                    del path[keep:]
                else:
                    visited[v] = len(path)
                    path.append(v)
        return self.shorten(path, line, avoid, forbidden)

    def shorten(self, path, line, avoid, forbidden=frozenset()):
        """Cut long wraps around hexes when the shortcut stays in the same corridor."""
        offsets = {}

        def offset(vertex):
            if vertex not in offsets:
                offsets[vertex] = min(segment_distance(self.points[vertex], a, b)
                                      for a, b in zip(line, line[1:]))
            return offsets[vertex]

        i = 0
        used = set(path)
        while i + 4 < len(path):
            start, *middle, end = path[i:i + 5]
            candidates = (self.neighbours[start] & self.neighbours[end]) - used - forbidden
            if candidates:
                shortcut = min(candidates, key=lambda v: (offset(v), v))
                edges = {tuple(sorted((start, shortcut))), tuple(sorted((shortcut, end)))}
                if not edges & avoid and offset(shortcut) <= max(map(offset, middle)):
                    used.difference_update(middle)
                    used.add(shortcut)
                    path[i + 1:i + 4] = [shortcut]
                    i = max(0, i - 3)
                    continue
            i += 1
        return path


def delta_courses(rivers):
    """Natural Earth distributaries outside the primary river network."""
    gorai = []
    for river in rivers:
        line = river["line"]
        lon, lat = line[0]
        end_lon, _ = line[-1]
        if river["name"] == "Ganges" and (
            (88.38 < lon < 88.45 and 24.35 < lat < 24.43 and 89.28 < end_lon < 89.32)
            or (89.28 < lon < 89.32 and 22.59 < lat < 22.65 and 89.33 < end_lon < 89.37)
        ):
            gorai.append(line)
        if river["name"] == "Godävari" and 81.6 < lon < 81.9 and 16.8 < lat < 17 and end_lon < lon:
            yield {"name": "Godavari western distributary", "line": line, "trunk": "Godavari",
                   "rank": 7, "mouth": True, "delta": True}
    upper, lower = sorted(gorai, key=lambda line: -line[0][1])
    yield {"name": "Ganga delta", "line": upper + lower[1:], "trunk": "Ganga",
           "rank": 7, "mouth": True, "delta": True}


# Connect the Padma and Lower Meghna through documented tidal stations.
ESTUARIES = (
    {"name": "Lower Meghna", "line": [(89.74928, 23.84801), (90.05, 23.63),
                                     (90.63125, 23.22292), (90.6492, 23.0843),
                                     (90.7483, 22.6038), (91.05, 22.216667)],
     "rank": 9, "mouth": True},
)


def build_edges(graph, courses, project, simplify, clip, width, height, legacy=(), junctions=None):
    edges = {}
    names = defaultdict(list)
    hydro_vertices = set()
    delta_endpoints = {}
    named_edges = defaultdict(set)
    occupied = set()
    mouths = {}
    heads = {}

    def nearest_on(name, point, available=False):
        candidates = {v for key in named_edges[name] for v in key}
        if available:
            candidates = {v for v in candidates if graph.neighbours[v] - occupied} or candidates
        return min(candidates,
                   key=lambda v: (math.dist(point, graph.points[v]), v))

    for course in courses:
        line = [project(*point) for point in course["line"]]
        for piece in clip(line, width, height):
            start = end = None
            avoid = frozenset()
            forbidden = occupied if junctions is not None and not course.get("delta") else frozenset()
            coast = course["mouth"] and math.dist(piece[-1], line[-1]) < 1e-6
            if course.get("delta"):
                def endpoint(point):
                    if point not in delta_endpoints:
                        nearest = min(hydro_vertices, key=lambda v: (math.dist(point, graph.points[v]), v))
                        delta_endpoints[point] = (
                            nearest if math.dist(point, graph.points[nearest]) < 1.5 * graph.grid.radius
                            else graph.snap(point)
                        )
                    return delta_endpoints[point]

                start = endpoint(piece[0])
                if not coast:
                    end = endpoint(piece[-1])
                if trunk := course.get("trunk"):
                    avoid = named_edges[trunk]
                    start = nearest_on(trunk, piece[0])
            if name := course.get("start_on"):
                start = nearest_on(name, piece[0], bool(forbidden))
            if course["name"] == "Lower Meghna":
                # The three arms need north, southwest and southeast edges at Goalundo.
                start = min((v for v, (x, y) in enumerate(graph.points)
                             if math.dist(piece[0], (x, y)) <= 2 * graph.grid.radius
                             and any(graph.points[u][1] < y - 0.9 * graph.grid.radius
                                     for u in graph.neighbours[v])),
                            key=lambda v: (math.dist(piece[0], graph.points[v]), v))
            if name := course.get("end_on"):
                junction = project(*course["junction"]) if "junction" in course else piece[-1]
                end = nearest_on(name, junction, bool(forbidden))
            line = simplify(piece, graph.grid.radius / 3)
            options = [end]
            if forbidden and course.get("end_on"):
                candidates = {v for key in named_edges[course["end_on"]] for v in key
                              if graph.neighbours[v] - occupied and math.dist(junction, graph.points[v]) < 2 * graph.grid.radius}
                options += sorted(candidates - {end}, key=lambda v: (math.dist(junction, graph.points[v]), v))
            if course["name"] == "Ganga":
                options = [heads["Lower Meghna"]]
            elif course["name"] == "Brahmaputra":
                options = [mouths["Ganga"]]
            for end in options:
                path = graph.route(line, start=start, end=end, coast=coast, avoid=avoid, forbidden=forbidden)
                if len(path) >= 2:
                    break
            if len(path) < 2:
                raise ValueError(f"Could not route {course['name']} to its endpoint")
            if junctions is not None and course.get("end_on"):
                junctions.append({"river": course["name"], "parent": course["end_on"], "vertex": end,
                                  "neighbor": path[-2], "at": "outlet"})
            if junctions is not None and course.get("start_on"):
                junctions.append({"river": course["name"], "parent": course["start_on"], "vertex": start,
                                  "neighbor": path[1], "at": "inlet"})
            mouths[course["name"]] = path[-1]
            heads[course["name"]] = path[0]
            if not course.get("delta"):
                hydro_vertices.update(path)
                occupied.update(path)
            for a, b in zip(path, path[1:]):
                key = tuple(sorted((a, b)))
                if key not in edges:
                    edges[key] = {
                        "corners": list(key), "cells": graph.cells[key], "rank": course["rank"],
                        "downstream": b,
                        "delta": bool(course.get("delta")),
                        "pts": [round(value, 3) for v in key for value in graph.points[v]],
                    }
                if course["name"] and course["name"] not in names[key]:
                    names[key].append(course["name"])
                    named_edges[course["name"]].add(key)
    label_unnamed(graph, edges, names, legacy)
    return [dict(edge, names=names[key]) for key, edge in edges.items()]


def label_unnamed(graph, edges, names, legacy):
    """Copy otherwise missing Natural Earth names only along nearby mapped courses."""
    radius = graph.grid.radius
    known_aliases = set(RIVER_ANCHORS) | {"Ganges", "Godävari", "Mahäna Nadï"}
    segments = defaultdict(list)
    for river in legacy:
        name, pts = river["name"], river["pts"]
        if not name or name in known_aliases:
            continue
        line = list(zip(pts[::2], pts[1::2]))
        for a, b in zip(line, line[1:]):
            for x in range(math.floor(min(a[0], b[0]) / radius) - 1, math.floor(max(a[0], b[0]) / radius) + 2):
                for y in range(math.floor(min(a[1], b[1]) / radius) - 1, math.floor(max(a[1], b[1]) / radius) + 2):
                    segments[x, y].append((a, b, name))
    for key in edges:
        if names[key]:
            continue
        a, b = (graph.points[v] for v in key)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        nearby = segments[math.floor(mid[0] / radius), math.floor(mid[1] / radius)]
        distance, name = min(((segment_distance(mid, a, b), name) for a, b, name in nearby),
                             default=(math.inf, ""))
        if distance < radius / 2:
            names[key].append(name)


def edge_masks(graph, edges):
    masks = [0] * graph.grid.size
    for edge in edges:
        for cell in edge["cells"]:
            ring = graph.corners[cell]
            for side, (a, b) in enumerate(zip(ring, ring[1:] + ring[:1])):
                if sorted((a, b)) == edge["corners"]:
                    masks[cell] |= 1 << side
    return masks


def build_lakes(grid, lakes, project, water):
    features = []
    majority = 3 * SQRT3 * grid.radius ** 2 / 4
    for lake in lakes:
        x, y = project(*lake["point"])
        cell = grid.cell_at(x, y)
        if cell < 0:
            continue
        areas = defaultdict(float)
        polygons = []
        for polygon in lake["polygons"]:
            rings = [[project(*point) for point in ring] for ring in polygon]
            for tile, area in overlaps(grid, Shape(rings)):
                areas[tile] += area
            polygons.append([[[round(a, 2), round(b, 2)] for a, b in ring] for ring in rings])
        tiles = sorted(tile for tile, area in areas.items() if area > majority)
        for tile in tiles:
            water[tile] = 3
        features.append({"name": lake["name"], "tiles": tiles, "cell": cell,
                         "point": [round(x, 2), round(y, 2)], "polygons": polygons})
    return features


def check_hydrography(world):
    grid = HexGrid(**world["grid"])
    graph = EdgeGraph(grid, world["water"])
    edges = world["river_edges"]
    seen = set()
    forest = {}
    by_name = defaultdict(lambda: defaultdict(set))
    directions = {}
    for edge in edges:
        a, b = key = tuple(edge["corners"])
        pts = [round(value, 3) for v in key for value in graph.points[v]] if key in graph.cells else None
        if (not pts or edge["pts"] != pts or edge["cells"] != graph.cells[key] or key in seen
                or edge.get("downstream") not in key):
            return [("FAIL", f"invalid or duplicate river edge {key}")]
        seen.add(key)
        directions[key] = edge["downstream"]
        if edge.get("delta") and not (DELTA_NAMES & set(edge["names"])):
            return [("FAIL", f"edge {key} claims an undeclared distributary")]
        if not edge.get("delta"):
            def root(v):
                while v in forest:
                    v = forest[v]
                return v

            ra, rb = root(a), root(b)
            if ra == rb:
                return [("FAIL", f"river cycle outside a declared distributary at {key}")]
            forest[ra] = rb
        for name in edge["names"]:
            by_name[name][a].add(b)
            by_name[name][b].add(a)
    if world["river_mask"] != edge_masks(graph, edges):
        return [("FAIL", "river_mask does not agree with the shared edge records")]
    required = RIVER_ANCHORS.keys() | CONTINUATIONS.keys() | {"Hooghly", "Ganga delta", "Lower Meghna", "Godavari western distributary",
                                      "Krishna eastern distributary"}
    results = []
    for name in sorted(required - by_name.keys()):
        results.append(("FAIL", f"must-include river missing: {name}"))
    for name in sorted(required & by_name.keys()):
        adjacency = by_name[name]
        pending = [next(iter(adjacency))]
        visited = set(pending)
        while pending:
            for v in adjacency[pending.pop()] - visited:
                visited.add(v)
                pending.append(v)
        if len(visited) != len(adjacency):
            results.append(("FAIL", f"river edges are disconnected: {name}"))
    tributaries = {
        "Indus": ["Zanskar", "Shyok", "Chenab"],
        "Chenab": ["Jhelum", "Ravi", "Sutlej"],
        "Sutlej": ["Beas"],
        "Ganga": ["Alaknanda", "Bhagirathi", "Yamuna", "Ramganga", "Gomti", "Ghaghara", "Gandak",
                  "Kosi", "Son", "Ganga delta", "Brahmaputra", "Lower Meghna"],
        "Hooghly": ["Damodar"],
        "Yamuna": ["Chambal", "Betwa", "Ken"],
        "Brahmaputra": ["Siang", "Dibang", "Lohit", "Subansiri", "Manas", "Teesta"],
        "Mahanadi": ["Tel"],
        "Brahmani": ["Baitarani"],
        "Godavari": ["Pranhita", "Indravati", "Godavari western distributary"],
        "Krishna": ["Bhima", "Tungabhadra", "Krishna eastern distributary"],
        "Kaveri": ["Kabini", "Bhavani"],
    }
    pairs = [(tributary, trunk) for trunk, branches in tributaries.items() for tributary in branches]
    for tributary, trunk in pairs:
        if by_name[tributary] and by_name[trunk] and not (by_name[tributary].keys() & by_name[trunk].keys()):
            results.append(("FAIL", f"no shared corner at {tributary} / {trunk} junction"))
    declared = {(item["river"], item["parent"]): item for item in world["river_junctions"]}
    expected = set(PARENTS.items()) | {(name, "Lower Meghna") for name in MEGHNA_INLETS} | {("Hooghly", "Ganga")}
    if declared.keys() != expected:
        results.append(("FAIL", f"missing or unexpected directed river junctions: {sorted(declared.keys() ^ expected)}"))
    project = MapProjection(**world["projection"])
    for tributary, trunk in sorted(expected & declared.keys()):
        item = declared[tributary, trunk]
        v = item["vertex"]
        branch, parent = by_name[tributary], by_name[trunk]
        at = "inlet" if tributary == "Hooghly" else "outlet"
        neighbor = item["neighbor"]
        receiving = by_name["Lower Meghna"] if tributary == "Brahmaputra" else parent
        incoming = at == "outlet"
        key = tuple(sorted((v, neighbor)))
        if (item["at"] != at or branch.keys() & parent.keys() != {v} or branch[v] != {neighbor} or
                math.dist(project(*JUNCTIONS[tributary]), graph.points[v]) > 2 * grid.radius or
                directions.get(key) != (v if incoming else neighbor) or
                not any(directions[tuple(sorted((v, peer)))] == (peer if incoming else v)
                        for peer in receiving[v])):
            results.append(("FAIL", f"directed junction differs from source: {tributary} / {trunk}"))
    if declared.get(("Brahmaputra", "Ganga"), {}).get("vertex") != declared.get(("Ganga", "Lower Meghna"), {}).get("vertex"):
        results.append(("FAIL", "Brahmaputra and Ganga do not flow into the same receiving corner"))
    if barak := declared.get(("Barak", "Kushiyara")):
        downstream = defaultdict(set)
        for edge in edges:
            if set(edge["names"]) & {"Kushiyara", "Upper Meghna", "Lower Meghna"}:
                a, b = edge["corners"]
                end = edge["downstream"]
                downstream[b if end == a else a].add(end)
        pending = [barak["vertex"]]
        reached = set(pending)
        while pending:
            for v in downstream[pending.pop()] - reached:
                reached.add(v)
                pending.append(v)
        lower_outlets = {v for v in by_name["Lower Meghna"] if v in graph.coast and not downstream[v]}
        if not (reached & lower_outlets):
            results.append(("FAIL", "Barak does not drain to the sea via the Lower Meghna"))
    outlets = ("Indus", "Narmada", "Tapti", "Mahi", "Sabarmati", "Periyar", "Sharavathi", "Mahanadi",
               "Subarnarekha", "Godavari", "Godavari western distributary", "Krishna",
               "Krishna eastern distributary", "Pennar", "Kaveri", "Vaigai", "Hooghly", "Ganga delta",
               "Lower Meghna")
    for name in outlets:
        if not (by_name[name].keys() & graph.coast):
            results.append(("FAIL", f"river has no coastal outlet: {name}"))
    for branch, trunk in (("Krishna eastern distributary", "Krishna"),
                          ("Godavari western distributary", "Godavari")):
        if not ((by_name[branch].keys() - by_name[trunk].keys()) & graph.coast):
            results.append(("FAIL", f"{branch} shares its coastal outlet with {trunk}"))
    lakes = world["lakes"]
    for name in sorted(LAKE_ANCHORS.keys() - {lake["name"] for lake in lakes}):
        results.append(("FAIL", f"must-include lake missing: {name}"))
    for lake in lakes:
        for cell in lake["tiles"]:
            if world["water"][cell] != 3 or world["cover"][cell] or any(pct[cell] for pct in world["pct"].values()):
                results.append(("FAIL", f"lake {lake['name']} tile {cell} retains land surface data"))
    if not results:
        results.append(("PASS", f"{len(edges)} unique river edges, {len(required)} connected named courses, "
                        f"{len(declared)} directed junctions and {len(lakes)} lake features"))
    return results
