"""City View economy estimates and gateway distances."""

import math

from ..india.city_economy_sources import GSDP_GROWTH
from ..india.transport_corridors import FREIGHT_CORRIDORS
from .city_view import apportion
from .rivers import segment_distance
from .state_metrics import FY
from .yields import KEYS, YIELDS


def city_sector_output(gdp_by_state, mixes):
    if not gdp_by_state or any(not mixes.get(state) for state in gdp_by_state):
        return None
    sectors = ("agriculture", "industry", "services")
    details = ("mining", "manufacturing", "construction", "utilities")
    weights = {key: 0 for key in sectors}
    for state, gdp in gdp_by_state.items():
        shares = mixes[state]["shares"]
        for key in sectors:
            weights[key] += gdp * shares[key] / sum(shares.values())
    values = apportion(round(sum(gdp_by_state.values())), weights)
    for key in details:
        shares = {state: mixes[state].get("detail", {}).get(key) for state in gdp_by_state}
        if all(share is not None for share in shares.values()):
            values[key] = round(sum(gdp * shares[state] for state, gdp in gdp_by_state.items()))
    source = sorted({source for state in gdp_by_state
                     for source in (mixes[state]["source"] if isinstance(mixes[state]["source"], list)
                                    else [mixes[state]["source"]])})
    return {"values": values, "source": source + ["gsdp_fy26"], "period": FY, "estimated": True,
            "description": "Allocates each state’s contribution to city GDP using that state’s nominal GSVA shares."}


def city_output_growth(gdp_by_state):
    if not gdp_by_state or any(state not in GSDP_GROWTH for state in gdp_by_state):
        return None
    prior = sum(value / (1 + GSDP_GROWTH[state])
                for state, value in gdp_by_state.items())
    if prior:
        return {"value": sum(gdp_by_state.values()) / prior - 1, "estimated": True, "period": FY,
                "source": sorted({"delhi_gsdp_fy26" if state == "DL" else "gsdp_fy26" for state in gdp_by_state}),
                "description": "Nominal output growth using the same city allocation weights in both years."}


def city_finances(cities):
    gold = next(row for row in YIELDS if row["key"] == "gold")
    rows = {}
    for city_id, city in cities.items():
        yields = city["yields"]
        gdp = yields.get("gold")
        rows[city_id] = dict(gdp=gdp, gdp_per_resident=None if gdp is None else gdp / city["population"],
                             period=FY, source=gold["sources"], estimated=True, ranks={},
                             sector_mix=city.get("state_sector_mix"),
                             sector_output=city.get("sector_output"),
                             output_growth=city.get("output_growth"),
                             national_shares=city.get("national_shares"))
    for key in [*KEYS, "gdp", "gdp_per_resident"]:
        def value(city_id):
            return rows[city_id][key] if key in ("gdp", "gdp_per_resident") else cities[city_id]["yields"].get(key)

        ranked = sorted((v for city_id in cities if (v := value(city_id)) is not None), reverse=True)
        ranks = {}
        for rank, metric in enumerate(ranked, 1):
            ranks.setdefault(metric, rank)
        for city_id, row in rows.items():
            row["ranks"][key] = ranks.get(value(city_id))
    return rows


def gateway_records(city, profile, infrastructure, paths, grid):
    point = city["x"], city["y"]
    vintage = infrastructure.get("vintage", {})

    def distance(site):
        return math.dist(point, (site["x"], site["y"]))

    def nearest(sites, source, period):
        site = min(sites, key=lambda s: (distance(s), s["id"]), default=None)
        return None if site is None else dict(name=site["name"], distance_km=round(distance(site)),
                                               source=source, period=period)

    port = nearest((s for s in infrastructure.get("ports", []) if s["category"] == "Major port"),
                   "cwprs_port_locations", "November 2026")
    scheduled = [s for s in infrastructure.get("airports", []) if s.get("scheduled_service", True)]
    airports = {size: nearest((s for s in scheduled if s["size"] == size),
                              "ourairports", vintage.get("airports"))
                for size in ("large", "medium", "small")}
    local = {r["cell"] for r in profile["cells"]} | {city["cell"]}
    # One ring of nearby cells admits alignments just beyond the footprint at map resolution.
    nearby = local | {other for cell in local for other in grid.neighbours(cell)}

    def centre(cell):
        return grid.center(*grid.col_row(cell))

    rail = []
    for name, path in paths.items():
        if not nearby.intersection(path) or len(path) < 2:
            continue
        points = [centre(cell) for cell in path]
        km = min(segment_distance(point, a, b) for a, b in zip(points, points[1:]))
        rail.append(dict(name=name, distance_km=round(km), freight=name in FREIGHT_CORRIDORS,
                         source="osm_transport", period=vintage.get("network")))
    if not rail:
        candidates = [
            (segment_distance(point, centre(a), centre(b)), not bool(name), name or "Main line")
            for a, b, name in infrastructure.get("main_lines", [])
            if a in nearby or b in nearby
        ]
        if candidates:
            km, _, name = min(candidates)
            rail.append(dict(name=name, distance_km=round(km), freight=False, main_line=True,
                             source="osm_transport", period=vintage.get("network")))
    return dict(port=port, airports=airports, rail=sorted(rail, key=lambda r: (r["distance_km"], r["name"])))
