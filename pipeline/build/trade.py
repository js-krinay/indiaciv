"""Schematic coastal network and port throughput on the atlas grid."""

import math
from collections import deque

from ..core.geo import MapProjection
from ..india.transport_corridors import FREIGHT_CORRIDORS
from .world import COAST, OCEAN

CARGO_PERIOD = "1 Apr 2026 – 31 Oct 2026"
PERIOD = dict(period_start="2026-04-01", period_end="2026-10-31",
              label=f"Apr–Oct 2026 ({CARGO_PERIOD})", status="Advance estimate")
CARGO_SOURCE = "mopsw_coastal_cargo"
DFC_SOURCE = "pib_dfc_completion"

# MoPSW October report, Table 1, Coastal, column 9, in metric tonnes.
COASTAL_CARGO = {
    "deendayal": 23_370_613,
    "mumbai": 14_548_102,
    "jnpa": 4_885_530,
    "mormugao": 1_703_540,
    "mangaluru": 9_567_880,
    "cochin": 7_461_968,
    "chidambaranar": 8_353_127,
    "chennai": 3_359_803,
    "kamarajar": 13_661_847,
    "visakhapatnam": 15_146_748,
    "paradip": 40_016_480,
    "kolkata": 3_510_138,
}

# Offshore schematic junctions, ordered around the peninsula. None marks a turn.
JUNCTIONS = [
    ("deendayal", 68.3, 22.3), ("mumbai", 71.5, 19.3), ("jnpa", 71.8, 18.45),
    ("mormugao", 72.55, 15.3), ("mangaluru", 73.65, 12.9), ("cochin", 75.05, 9.7),
    (None, 76.5, 7.6), ("chidambaranar", 78.4, 7.75),
    (None, 79.3, 5.55), (None, 81.8, 5.5), ("chennai", 81.25, 12.8), ("kamarajar", 81.45, 13.55),
    ("visakhapatnam", 84.1, 16.7), ("paradip", 87.25, 19.5), ("kolkata", 88.65, 20.75),
]


def connected_sea(grid, sea, start):
    connected = {start}
    frontier = [start]
    for cell in frontier:
        for neighbour in grid.neighbours(cell):
            if neighbour in sea and neighbour not in connected:
                connected.add(neighbour)
                frontier.append(neighbour)
    return connected


def sea_path(grid, sea, start, goals):
    """Shortest adjacent sea-cell path, or None when disconnected."""
    queue = deque([start])
    parents = {start: None}
    while queue:
        cell = queue.popleft()
        if cell in goals:
            path = []
            while cell is not None:
                path.append(cell)
                cell = parents[cell]
            return path[::-1]
        for other in grid.neighbours(cell):
            if other in sea and other not in parents:
                parents[other] = cell
                queue.append(other)
    return None


def coastal_network(grid, world, ports):
    project = MapProjection(**world["projection"])
    sea = {i for i, water in enumerate(world["water"]) if water in (OCEAN, COAST)}
    centres = {i: grid.center(*grid.col_row(i)) for i in sea}

    def nearest(point):
        return min(centres, key=lambda i: (math.dist(point, centres[i]), i))

    def path(start, end):
        route = sea_path(grid, sea, start, {end})
        if route is None:
            raise ValueError(f"Disconnected sea cells {start} and {end}")
        return route

    _, lon, lat = JUNCTIONS[0]
    sea = connected_sea(grid, sea, nearest(project(lon, lat)))
    centres = {i: centres[i] for i in sea}
    stations = [(port_id, nearest(project(lon, lat))) for port_id, lon, lat in JUNCTIONS]
    backbone = [stations[0][1]]
    for (_, a), (_, b) in zip(stations, stations[1:]):
        backbone.extend(path(a, b)[1:])

    by_id = {port["id"]: port for port in ports}
    branches = []
    approaches = set()
    for port_id, junction in stations:
        if port_id is None:
            continue
        port = by_id[port_id]
        # The Kolkata/Haldia authority shares one branch at the seaward mouth of the Hooghly.
        approach = project(88.08, 21.53) if port_id == "kolkata" else (port["x"], port["y"])
        start = min(centres.keys() - approaches, key=lambda i: (math.dist(approach, centres[i]), i))
        approaches.add(start)
        route = path(start, junction)
        branches.append(dict(port_id=port_id, cells=route, tonnes=COASTAL_CARGO[port_id]))
    return dict(**PERIOD, source_id=CARGO_SOURCE, backbone=backbone, branches=branches,
                corridors=list(FREIGHT_CORRIDORS))


def trade_check(doc, world, grid):
    trade = doc.get("trade")
    if not trade:
        return [("FAIL", "Missing coastal trade network")]
    backbone, branches = trade["backbone"], trade["branches"]

    def sea_route(cells):
        return (len(cells) > 1
                and all(0 <= c < grid.size and world["water"][c] in (OCEAN, COAST) for c in cells)
                and all(b in grid.neighbours(a) for a, b in zip(cells, cells[1:])))

    major = {p["id"] for p in doc["ports"] if p["category"] == "Major port"}
    valid = (all(trade[k] == v for k, v in PERIOD.items()) and trade["source_id"] == CARGO_SOURCE
             and sea_route(backbone) and len(branches) == len(major)
             and len({b["cells"][0] for b in branches}) == len(major)
             and {b["port_id"]: b["tonnes"] for b in branches} == COASTAL_CARGO
             and major == COASTAL_CARGO.keys()
             and all(set(b) == {"port_id", "tonnes", "cells"}
                     and sea_route(b["cells"]) and b["cells"][-1] in backbone for b in branches))
    freight = (trade["corridors"] == list(FREIGHT_CORRIDORS)
               and all(doc["rail_corridors"].get(name) for name in trade["corridors"]))
    return [("PASS" if valid else "FAIL", f"{len(branches)} single-port coastal cargo branches on a sea-only network"),
            ("PASS" if freight else "FAIL", "Trade uses the two operating rail corridor paths")]


def route_document(network, ports, corridors):
    """Publish literal paths in the trade route contract with observation metadata."""
    by_id = {port["id"]: port for port in ports}
    routes = [
        dict(path=branch["cells"], top_mode="water", name=by_id[branch["port_id"]]["name"],
             tons_k=branch["tonnes"] / 1000, period=CARGO_PERIOD,
             period_start=network["period_start"], period_end=network["period_end"],
             status=network["status"], source=CARGO_SOURCE)
        for branch in network["branches"]
    ]
    routes.extend(
        dict(path=corridors[name], top_mode="rail", name=name, period="8 Sep 2026", source=DFC_SOURCE)
        for name in network["corridors"] if corridors.get(name)
    )
    routes.insert(0, dict(path=network["backbone"], top_mode="water", schematic=True, source=CARGO_SOURCE))
    return dict(literal_paths=True, sources=[CARGO_SOURCE, DFC_SOURCE], zones=[], routes=routes)
