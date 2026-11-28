"""Schematic coastal network and port throughput on the atlas grid."""

import math
from collections import deque

from ..core.geo import MapProjection
from ..india.coastal_shipping import SOURCE as COASTAL_OBSERVATION_SOURCE
from ..india.transport_corridors import FREIGHT_CORRIDORS
from .world import COAST, OCEAN

CARGO_PERIOD = "1 Apr 2026 – 31 Oct 2026"
PERIOD = dict(period_start="2026-04-01", period_end="2026-10-31",
              label=f"Apr–Oct 2026 ({CARGO_PERIOD})", status="Advance estimate")
CARGO_SOURCE = "mopsw_coastal_cargo"
DFC_SOURCE = "pib_dfc_completion"
OBSERVATION_PERIOD = "FY 2024-25 (1 Apr 2024 – 31 Mar 2025)"


def great_circle(a, b):
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return round(2 * 6371 * math.asin(min(1, math.sqrt(h))))


def coastal_observations(ports, positions, cities, report):
    """Join directed observations by exact port ID, preserving grouped endpoints."""
    by_id = {port["id"]: port for port in ports}
    zones, routes = {}, []
    provenance = dict(period=OBSERVATION_PERIOD, vintage="older", source=COASTAL_OBSERVATION_SOURCE)
    for order, loading, unloading, band, commodities in report["rows"]:
        if not all(key in by_id and key in positions for key in (*loading, *unloading)):
            continue
        for endpoint in (loading, unloading):
            key = "+".join(endpoint)
            if key in zones:
                continue
            members = [by_id[port_id] for port_id in endpoint]
            anchor = None
            if len(members) == 1 and cities:
                port = members[0]
                closest = min(cities, key=lambda city: (
                    math.dist((port["x"], port["y"]), (city["x"], city["y"])), city["id"]))
                anchor = dict(city=closest["id"], name=closest["name"], cell=closest["cell"],
                              x=closest["x"], y=closest["y"])
            zones[key] = dict(id=key, name=" / ".join(port["name"] for port in members),
                              kind="Port" if len(members) == 1 else "Reported port group",
                              states=sorted({port["state"] for port in members}), ports=list(endpoint),
                              anchor=anchor, partners=[], **provenance)
        a, b = "+".join(loading), "+".join(unloading)
        route = dict(a=a, b=b, report_order=order, band=band, top_mode="water",
                     commodities=list(commodities), **provenance)
        if len(loading) == len(unloading) == 1:
            route["dist_km"] = great_circle(positions[loading[0]], positions[unloading[0]])
        routes.append(route)
        zones[a]["partners"].append(dict(id=b, direction="Unloading"))
        zones[b]["partners"].append(dict(id=a, direction="Loading"))
    return dict(
        **provenance, zones=list(zones.values()), routes=routes,
        title="Reported domestic coastal shipping",
        rule=f"{len(routes)} of {report['reported_entries']} published entries with matched endpoints. "
             "Grouped ports share a single entry. Report order follows the source.",
        labels=dict(a="Reported coastal loading port or port group",
                    b="Reported coastal unloading port or port group",
                    order="Report order among published coastal cargo entries",
                    band="Reported coastal cargo band relative to largest published entry",
                    distance="Straight-line separation between verified port points",
                    mode="Documented mode", commodities="Commodities named for reported coastal entry",
                    partners="Counterpart ports in the published coastal subset",
                    anchor="Atlas agglomeration nearest a verified port", state="State/UT of matched port"),
        units=dict(distance="km"),
        modes=[dict(id="water", name="Coastal shipping")],
        commodities=dict(coal="Coal", pol="Petroleum, oil and lubricants (POL)", iron_ore="Iron ore",
                         fertilizers="Fertilizers", container="Container cargo", steel="Steel"))

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
    observed = network.get("observed_coastal")
    return dict(literal_paths=True, sources=[CARGO_SOURCE, DFC_SOURCE] + ([observed["source"]] if observed else []),
                zones=[], routes=routes, **({"observed_coastal": observed} if observed else {}))
