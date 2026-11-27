"""Rasterise operating transport lines and place sites on the Indian hex grid."""

import json
import math
from collections import defaultdict, deque

from .cities import city_state_lookup
from .resources import land_cell
from .trade import CARGO_PERIOD, CARGO_SOURCE, DFC_SOURCE, coastal_network, route_document, trade_check
from .transport_statistics import (
    AAI_JHARSUGUDA, COASTAL, FEATURED_PORTS, FREIGHT, OPERATOR_LOCALITIES, PERIOD, PORT_CITIES,
    PORT_TOTAL, PORTS, VERIFIED_PORT_LOCALITIES, cargo_split,
)
from ..core.geo import MapProjection, Shape, ShapeIndex
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, load_interim_payload, write_web
from ..india import OSM_TRANSPORT_LICENSE_URL
from ..india.port_directions import NON_MAJOR_TOTALS, SOURCE as PORT_DIRECTION_SOURCE, non_major_cargo_record
from ..india.transport import MILITARY_FACILITY, is_civil_airport, public_label
from ..india.transport_corridors import FREIGHT_CORRIDORS, RAIL_CORRIDORS

REQUIRES = ["_world", "soi_outline", "osm_transport", "ourairports", "datameet"]
OPTIONAL_REQUIRES = [PORT_DIRECTION_SOURCE]
PRODUCES = ["infrastructure.json", "trade.json"]
SOURCES = ["datameet", "osm_transport", "ourairports", AAI_JHARSUGUDA, OPERATOR_LOCALITIES,
           "mopsw_port_cargo", "pib_rail_freight", "cwprs_port_locations",
           "featured_port_locations", "aai_civil_airport_reference", CARGO_SOURCE, DFC_SOURCE]


def links_of(grid, cells, protected):
    """Skip corner detours while preserving shared junctions and way ends."""
    run = []
    for cell in cells:
        if run and cell == run[-1]:
            continue
        while (len(run) >= 2 and run[-1] not in protected
               and cell in grid.neighbours(run[-2])):
            run.pop()
        run.append(cell)
    return [tuple(sorted((a, b))) for a, b in zip(run, run[1:])]


def sample_runs(grid, owner, points, snap_border=None):
    """Sample densely enough to follow the line and break at rejected cells."""
    run = []
    previous_snap = False
    for start, end in zip(points, points[1:] + points[-1:]):
        steps = max(1, math.ceil(math.dist(start, end) / 3))
        for i in range(steps):
            x, y = (a + (b - a) * i / steps for a, b in zip(start, end))
            cell = grid.cell_at(x, y)
            snapped = cell >= 0 and owner[cell] == -2
            if snapped:
                cell = snap_border(x, y) if snap_border else -1
            if cell < 0:
                if run:
                    yield run
                    run = []
            elif not run or cell != run[-1]:
                if run and cell not in grid.neighbours(run[-1]):
                    shared = set(grid.neighbours(run[-1])).intersection(grid.neighbours(cell))
                    detour = min((n for n in shared if owner[n] >= 0), default=-1)
                    if (snapped or previous_snap) and detour >= 0:
                        run.append(detour)
                    else:
                        yield run
                        run = []
                run.append(cell)
            previous_snap = snapped
    if run:
        yield run


def networks(grid, project, owner, osm, snap_border=None):
    edges = {"rail": {}, "roads": {}}
    freight = {"EDFC": set(), "WDFC": set()}
    main_lines = {}
    chenab = False
    protected = {grid.cell_at(*project(*point)) for point in osm["junctions"]}
    for kind, tier, ref, coords, facility, *metadata in osm["lines"]:
        name = public_label(metadata[0]) if metadata else None
        network = public_label(metadata[1]) if len(metadata) > 1 else None
        ref = public_label(ref)
        if kind == "roads" and tier == 1:
            numbers = {part.strip().upper().replace(" ", "").replace("-", "")
                       for part in (ref or "").split(";")}
            lon, lat = coords[0]
            if not (numbers & {"NH16", "NH19", "NH48"}
                    or ("NH44" in numbers and 77 <= lon <= 78.4 and 27.05 <= lat <= 28.75)):
                tier = 2
        points = [project(*point) for point in coords]
        for run in sample_runs(grid, owner, points, snap_border):
            if facility == "Chenab" and any(owner[cell] >= 0 for cell in run):
                chenab = True
            for a, b in links_of(grid, run, protected if kind == "rail" else set()):
                if owner[a] < 0 and owner[b] < 0:
                    continue
                link = (a, b)
                rank = tier, not bool(ref), ref or "", not bool(name), name or "", not bool(network), network or ""
                if link not in edges[kind] or rank < edges[kind][link]:
                    edges[kind][link] = rank
                if facility in freight:
                    freight[facility].add(link)
                if kind == "rail" and tier == 0 and not facility:
                    names = [label for label in (main_lines.get(link), name) if label]
                    main_lines[link] = min(names, default=None)
    rail = [[a, b, rank[0]] for (a, b), rank in sorted(edges["rail"].items())]
    main = link_graph((a, b) for a, b, tier in rail if tier == 0)
    dedicated = {name: link_graph(links) for name, links in freight.items()}
    corridors = {}
    trunks = set()
    for name, points in RAIL_CORRIDORS.items():
        path = corridor_path(grid, project, dedicated.get(FREIGHT_CORRIDORS.get(name), main), points)
        if path:
            corridors[name] = path
            trunks.update(tuple(sorted(pair)) for pair in zip(path, path[1:]))
    rail = [[a, b, 0 if (a, b) in trunks else rank[0] + 1,
             *([rank[2] or None, rank[4] or None, rank[6] or None] if any(rank[2::2]) else [])]
            for (a, b), rank in sorted(edges["rail"].items())]
    roads = [[a, b, rank[0], rank[2] or None, rank[4] or None, rank[6] or None]
             for (a, b), rank in sorted(edges["roads"].items())]
    return rail, roads, {**{key: sorted(links) for key, links in freight.items()}, "chenab": chenab}, corridors, [
        [a, b, name] for (a, b), name in sorted(main_lines.items())]


def port_tier(tonnes):
    if tonnes is None:
        return 3
    if tonnes >= 100_000_000:
        return 0
    return 1 if tonnes >= 25_000_000 else 2


def place(grid, project, owner, lon, lat, rings):
    x, y = project(lon, lat)
    cell = land_cell(grid, owner, x, y, rings)
    return None if cell < 0 else dict(x=round(x, 2), y=round(y, 2), cell=cell)


def airport_city(airport):
    city = public_label(airport.get("city"))
    if city is None and (airport["id"], airport["iata"]) == ("26505", "JRG"):
        return "Jharsuguda"
    return city


def port_tooltip_fields(port):
    fields = {"type": "inland" if port.get("id") == "w261074436" else "coastal"}
    cargo = port["cargo"] or port.get("historical_cargo_split")
    if cargo:
        fields.update(period=cargo.get("label") or cargo["period"], source_id=cargo["source_id"],
                      vintage=cargo.get("vintage", "2026"))
        if not port["cargo"]:
            domestic, foreign = cargo["domestic_tonnes"], cargo["foreign_tonnes"]
            fields.update(domestic=domestic, foreign=foreign, tons=domestic + foreign)
        if port["cargo"]:
            fields["year"] = 2026
    return fields


def coastal_port_slots(ports, trade):
    tonnage = {branch["port_id"]: branch["tonnes"] for branch in trade["branches"]}
    for port in ports:
        if port["id"] in tonnage:
            port["coastal_cargo"] = {
                "tons": tonnage[port["id"]], "year": 2026, "period": CARGO_PERIOD,
                "source_id": CARGO_SOURCE, "status": "Advance estimate",
            }


def ports_on_grid(grid, project, owner, candidates):
    ports = []
    for rank, (site_id, name, lon, lat, tonnes) in enumerate(sorted(PORTS, key=lambda row: -row[4]), 1):
        at = place(grid, project, owner, lon, lat, 2)
        if at is None:
            raise ValueError(f"Major port {name} has no nearby Indian land")
        ports.append(dict(id=site_id, name=name, category="Major port", tier=port_tier(tonnes), rank=rank,
                          geometry_source_id="cwprs_port_locations",
                          city=PORT_CITIES[site_id], tons=tonnes,
                          domestic=COASTAL[site_id], foreign=tonnes - COASTAL[site_id],
                          cargo=dict(share=round(tonnes / PORT_TOTAL, 8), **cargo_split(COASTAL[site_id], tonnes)), **at))
    # OSM often maps a named port as both a point and an area.
    seen = defaultdict(list)
    for site_id, name, lon, lat, source in FEATURED_PORTS:
        at = place(grid, project, owner, lon, lat, 2)
        if at is None:
            raise ValueError(f"Featured port {name} has no nearby Indian land")
        ports.append(dict(id=site_id, name=name, category="Non-major port", featured=True, tier=3,
                          rank=None, cargo=None, city=PORT_CITIES[site_id], geometry_source_id=source, **at))
        seen[site_id].append(project(lon, lat))
    major_positions = [project(p[2], p[3]) for p in PORTS] + [project(88.10, 22.03)]
    for site_id, name, lon, lat in sorted(candidates):
        if MILITARY_FACILITY.search(name):
            continue
        if name.casefold() == "nakkapalli port":  # Proposed greenfield project at the snapshot date.
            continue
        point = project(lon, lat)
        if any(math.dist(point, major) < 4 for major in major_positions):
            continue
        at = place(grid, project, owner, lon, lat, 1)
        key = " ".join(word for word in name.casefold().split() if word not in {"port", "harbour", "harbor"})
        if at is not None and all(math.dist(point, other) >= 12 for other in seen[key]):
            seen[key].append(point)
            ports.append(dict(id=site_id, name=name, category="Mapped port", tier=3, rank=None, cargo=None,
                              geometry_source_id="osm_transport", **at))
    return ports


def build():
    world = load_interim("_world")
    grid, project, owner = HexGrid(**world["grid"]), MapProjection(**world["projection"]), world["owner"]
    try:
        osm = load_interim_payload("osm_transport")
        airports = load_interim_payload("ourairports")
    except FileNotFoundError:
        print("    Transport inputs absent. See the preparation command in README.md.")
        write_web("infrastructure.json", None)
        write_web("trade.json", None)
        return
    outline = ShapeIndex([Shape([[project.from_projected(x / 1000, y / 1000) for x, y in ring]
                                 for ring in polygon]) for polygon in load_interim("soi_outline")["polygons"]])

    def snap_border(x, y):
        closest = land_cell(grid, owner, x, y, 1)
        return closest if closest >= 0 and outline.locate(x, y) >= 0 else -1

    rail, roads, facilities, corridors, main_lines = networks(grid, project, owner, osm["data"], snap_border)
    facilities["source_connections"] = osm["data"]["source_connections"]
    ports = ports_on_grid(grid, project, owner, osm["data"]["ports"])
    try:
        directions = load_interim(PORT_DIRECTION_SOURCE)
    except FileNotFoundError:
        directions = None
    for port in ports:
        if not port.get("city") and port["id"] in VERIFIED_PORT_LOCALITIES:
            port.update(city=VERIFIED_PORT_LOCALITIES[port["id"]],
                        city_provenance=dict(source_id=OPERATOR_LOCALITIES, period="FY 2024-25 (1 Apr 2024 – 31 Mar 2025)",
                                             vintage="older"))
        if directions and port["id"] in directions["ports"]:
            port["overseas_direction"] = directions["ports"][port["id"]]
        if port["cargo"] is None and port["id"] in NON_MAJOR_TOTALS:
            port["historical_cargo_split"] = non_major_cargo_record(*NON_MAJOR_TOTALS[port["id"]])
        port.update(port_tooltip_fields(port))
    airfields = []
    for airport in airports["data"]["airports"]:
        if not airport.get("civil_verified") or not is_civil_airport(airport):
            continue
        at = place(grid, project, owner, airport["lon"], airport["lat"], 1)
        if at is not None:
            city = airport_city(airport)
            site = {**{k: airport[k] for k in ("name", "iata", "size")}, **at,
                    "id": airport["iata"], "ourairports_id": airport["id"],
                    "city": city, "hub": f"{airport['size'].capitalize()} airport",
                    "year": 2026, "period": airports["vintage"], "scheduled_service": airport.get("scheduled_service", True)}
            if city and not public_label(airport.get("city")):
                site["city_provenance"] = dict(source_id=AAI_JHARSUGUDA, period="6 Aug 2026", vintage="2026")
            airfields.append(site)
    state_at = city_state_lookup(load_interim("datameet"), project)
    for site in ports + airfields:
        try:
            site["state_abbr"], site["state"] = state_at(site["x"], site["y"])
        except ValueError:
            # An offshore port point can be more than 10 km from a state polygon.
            site["state"] = world["state_names"][owner[site["cell"]]]
        site["state_source_id"] = "datameet"
    historical = {"overseas_direction_by_state": directions["states"]} if directions else {}
    trade = coastal_network(grid, world, ports)
    coastal_port_slots(ports, trade)
    write_web("trade.json", route_document(trade, ports, corridors))
    write_web("infrastructure.json", dict(version=2, sources=SOURCES + [PORT_DIRECTION_SOURCE],
                                         rail=rail, rail_corridors=corridors, **historical,
                                         main_lines=main_lines,
                                         trade=trade,
                                         roads=roads, ports=ports,
                                         port_split=cargo_split(sum(COASTAL.values()), PORT_TOTAL),
                                         airports=airfields, freight=FREIGHT, rail_facilities=facilities,
                                         lifecycle_audit=osm["data"]["lifecycle_audit"],
                                         osm_license=dict(attribution="© OpenStreetMap contributors",
                                                          license="ODbL 1.0", license_url=OSM_TRANSPORT_LICENSE_URL,
                                                          scope="Rail links and corridors, road links and port geometry with geometry_source_id osm_transport"),
                                         rules={"ports": "MoPSW advance estimates in metric tonnes for 12 major-port authorities. Domestic denotes coastal cargo. Overseas cargo lacks an import/export split."},
                                         vintage=dict(network=osm["vintage"], airports=airports["vintage"],
                                                      ports=PERIOD["label"])))


def nearby_rail(grid, graph, cell):
    return ({cell} | set(grid.neighbours(cell))) & graph.keys() if cell >= 0 else set()


def link_graph(links):
    graph = defaultdict(set)
    for a, b in links:
        graph[a].add(b)
        graph[b].add(a)
    return graph


def corridor_path(grid, project, graph, points):
    checkpoints = [nearby_rail(grid, graph, grid.cell_at(*project(*point))) for point in points]
    reached = {cell: [cell] for cell in checkpoints[0]}
    for start, end, targets in zip(points, points[1:], checkpoints[1:]):
        limit = math.ceil(math.dist(project(*start), project(*end)) / grid.radius * 1.35) + 2
        queue = deque((cell, 0) for cell in sorted(reached))
        previous = dict.fromkeys(reached)
        while queue:
            cell, steps = queue.popleft()
            if steps == limit:
                continue
            for other in sorted(graph[cell] - previous.keys()):
                previous[other] = cell
                queue.append((other, steps + 1))
        paths = {}
        for cell in targets & previous.keys():
            tail = []
            cur = cell
            while previous[cur] is not None:
                tail.append(cur)
                cur = previous[cur]
            paths[cell] = reached[cur] + tail[::-1]
        reached = paths
        if not reached:
            return None
    return min(reached.values(), key=lambda path: (len(path), path), default=None)


def corridor_connected(grid, project, graph, points):
    return corridor_path(grid, project, graph, points) is not None


def check(web_dir):
    path = web_dir / "infrastructure.json"
    doc = json.loads(path.read_text()) if path.exists() else None
    if doc is None:
        return [("NOTE", "Transport inputs absent")]
    if doc.get("version") != 2:
        return [("FAIL", "Expected India infrastructure version 2")]
    world = json.loads((web_dir / "world.json").read_text())
    grid, project = HexGrid(**world["grid"]), MapProjection(**world["projection"])
    owner = world["owner"]
    out = []
    audit = doc.get("lifecycle_audit")
    if audit is None:
        out.append(("FAIL", "Missing OSM lifecycle audit. Reprepare the pinned transport inputs."))
    elif audit["admitted_unresolved_way_ids"]:
        out.append(("FAIL", f"Unresolved lifecycle tags on admitted OSM ways: {audit['admitted_unresolved_way_ids']}"))
    else:
        out.append(("PASS", f"Excluded {audit['excluded']} lifecycle-conflicted OSM ways"))
    graph = defaultdict(set)
    for kind in ("rail", "roads"):
        seen = set()
        bad = 0
        for a, b, tier, *_ in doc[kind]:
            if not (0 <= a < b < grid.size and b in grid.neighbours(a) and tier in (0, 1, 2)
                    and (a, b) not in seen and min(owner[a], owner[b]) >= -1
                    and max(owner[a], owner[b]) >= 0):
                bad += 1
                continue
            seen.add((a, b))
            if kind == "rail" and tier == 0:
                graph[a].add(b)
                graph[b].add(a)
        out.append(("PASS" if seen and not bad else "FAIL", f"{kind}: {len(seen)} valid links, {bad} invalid"))
    facilities = doc["rail_facilities"]
    for name, points in RAIL_CORRIDORS.items():
        route_graph = graph
        if name in FREIGHT_CORRIDORS:
            route_graph = link_graph((a, b) for a, b in facilities[FREIGHT_CORRIDORS[name]]
                                     if b in graph.get(a, ()))
        rendered = corridor_connected(grid, project, route_graph, points)
        source = facilities["source_connections"][name]
        detail = "is connected in source and rendered main lines" if source else "is connected in rendered main lines"
        if not rendered:
            out.append(("FAIL", f"Rail corridor {name} has a rendered gap"))
        else:
            out.append(("PASS", f"Rail corridor {name} {detail}"))
            if not source:
                out.append(("WARN", f"{name}: tagged source ways split in the OSM node topology"))
    out.append(("PASS" if facilities["chenab"] else "FAIL", "Chenab rail bridge in the active rail source"))
    for kind in ("ports", "airports"):
        sites = doc[kind]
        valid = len({s["id"] for s in sites}) == len(sites) and all(
            0 <= s["cell"] < grid.size and owner[s["cell"]] >= 0 for s in sites)
        out.append(("PASS" if sites and valid else "FAIL", f"{len(sites)} {kind} on Indian land"))
    civil = (all(is_civil_airport(airport) for airport in doc["airports"])
             and not any(MILITARY_FACILITY.search(value)
                         for site in doc["ports"] + doc["airports"]
                         for key in ("name", "city", "state") if (value := site.get(key)))
             and all(public_label(value) == value for key in ("roads", "rail")
                     for *_, ref, name, network in (row for row in doc[key] if len(row) == 6)
                     for value in (ref, name, network)))
    out.append(("PASS" if civil else "FAIL", "Civilian publication gate for airport and port points"))
    measured = [p for p in doc["ports"] if p["cargo"] is not None]
    featured = {p["id"] for p in doc["ports"] if p.get("featured")}
    out.append(("PASS" if featured == {p[0] for p in FEATURED_PORTS} else "FAIL",
                f"{len(featured)} featured non-major ports"))
    valid_cargo = (len(measured) == len(PORTS)
                   and all(p["rank"] == rank and p["tier"] == port_tier(tonnes)
                           and p["city"] == PORT_CITIES[site_id] and p["id"] == site_id
                           and p["cargo"] == dict(share=round(tonnes / PORT_TOTAL, 8),
                                                  **cargo_split(COASTAL[site_id], tonnes))
                           for rank, (p, (site_id, _, _, _, tonnes)) in enumerate(zip(measured, PORTS), 1))
                   and all(p["rank"] is None and p["tier"] == 3 for p in doc["ports"] if p["cargo"] is None)
                   and doc.get("port_split") == cargo_split(sum(COASTAL.values()), PORT_TOTAL))
    out.append(("PASS" if valid_cargo else "FAIL", f"{len(measured)} major cargo markers ranked for {PERIOD['label']}"))
    older = {p["id"]: p for p in doc["ports"] if p.get("historical_cargo_split")}
    valid_older = set(older) == set(NON_MAJOR_TOTALS) and all(
        p["rank"] is None and p["cargo"] is None
        and p["historical_cargo_split"] == non_major_cargo_record(*NON_MAJOR_TOTALS[key])
        and all(p.get(field) == value for field, value in port_tooltip_fields(p).items())
        for key, p in older.items())
    out.append(("PASS" if valid_older else "FAIL", f"{len(older)} verified non-major port cargo records"))
    trade_path = web_dir / "trade.json"
    trade = json.loads(trade_path.read_text()) if trade_path.exists() else None
    matches = doc.get("trade") and trade == route_document(doc["trade"], doc["ports"], doc["rail_corridors"])
    out.append(("PASS" if matches else "FAIL", "Map trade paths preserve transport geometry and observation scope"))
    return out + trade_check(doc, world, grid)
