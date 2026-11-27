"""City View economy estimates and gateway distances."""

import math

from ..india.city_economy_sources import GSDP_GROWTH, HISTORICAL_DETAIL_PERIODS, MATCHED_GSDP, RESIDUAL_METHOD
from ..india.transport_corridors import FREIGHT_CORRIDORS
from .cities import older_city_value
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
    fields = {}
    historical_sources = set()
    for key in details:
        shares = {state: mixes[state].get("detail", {}).get(key) for state in gdp_by_state}
        if all(share is not None for share in shares.values()):
            values[key] = round(sum(gdp * shares[state] for state, gdp in gdp_by_state.items()))
            inputs = {mixes[state].get("detail_source", {}).get(key) for state in gdp_by_state}
            older = sorted(inputs.intersection(HISTORICAL_DETAIL_PERIODS))
            if older:
                historical_sources.update(older)
                fields[key] = {"source": older, "period": FY, "vintage": FY, "estimated": True,
                               "input_weights": {"period": HISTORICAL_DETAIL_PERIODS[older[0]],
                                                 "vintage": "older", "source": older},
                               "description": RESIDUAL_METHOD}
    if gdp_by_state.keys() == {"AP"} and all(key in values for key in details):
        values.update(apportion(values["industry"], {key: mixes["AP"]["detail"][key] for key in details}))
    sources = set()
    for state in gdp_by_state:
        source = mixes[state]["source"]
        sources.update(source if isinstance(source, list) else [source])
        sources.update(source for key, source in mixes[state].get("detail_source", {}).items() if key in values)
    result = {"values": values, "source": sorted(sources) + ["gsdp_fy26"], "period": FY, "vintage": FY,
              "estimated": True, "description": "Allocates each state’s contribution to city GDP using that "
              "state’s nominal GSVA shares."}
    if fields:
        for field in fields.values():
            field["source"] = result["source"]
        result.update(fields=fields, status="Mining and utilities use FY 2024-25 weights",
                      description=result["description"] + " " + RESIDUAL_METHOD,
                      input_weights={"source": sorted(historical_sources), "vintage": "older",
                                     "period": HISTORICAL_DETAIL_PERIODS[min(historical_sources)]})
    return result


def city_output_growth(gdp_by_state):
    if not gdp_by_state or any(state not in GSDP_GROWTH for state in gdp_by_state):
        return None
    prior = sum(value / (1 + GSDP_GROWTH[state])
                for state, value in gdp_by_state.items())
    if prior:
        return {"value": sum(gdp_by_state.values()) / prior - 1, "estimated": True, "period": FY,
                "source": sorted({"delhi_gsdp_fy26" if state == "DL" else "gsdp_fy26" for state in gdp_by_state}),
                "description": "Nominal output growth using the same city allocation weights in both years."}


def matched_city_output_growth(allocation):
    if not allocation or any(state not in MATCHED_GSDP for state in allocation):
        return None
    prior = current = 0
    sources = set()
    for state, weight in allocation.items():
        before, after, source = MATCHED_GSDP[state]
        prior += weight * before
        current += weight * after
        sources.add(source)
    if prior:
        description = ("Nominal growth from published state fiscal totals, separate from headline city GDP. "
                       "Uses the same city allocation weights for both years.")
        if "JH" in allocation:
            description += " Jharkhand uses its FY 2025-26 budget estimate."
        return {"value": current / prior - 1, "source": sorted(sources), "period": FY, "vintage": FY,
                "estimated": True, "status": "Separate fiscal series", "description": description}


def city_finances(cities, ranked_ids=None):
    gold = next(row for row in YIELDS if row["key"] == "gold")
    rows = {}
    for city_id, city in cities.items():
        yields = city["yields"]
        gdp = yields.get("gold")
        per_resident = None if gdp is None or older_city_value(city, "gdp_per_capita") else gdp / city["population"]
        rows[city_id] = dict(gdp=gdp, gdp_per_resident=per_resident,
                             period=FY, source=gold["sources"], estimated=True, ranks={},
                             sector_mix=city.get("state_sector_mix"),
                             sector_output=city.get("sector_output"),
                             output_growth=city.get("output_growth"),
                             national_shares=city.get("national_shares"))
    ranked_ids = cities.keys() if ranked_ids is None else ranked_ids
    for key in [*KEYS, "gdp", "gdp_per_resident"]:
        def value(city_id):
            return rows[city_id][key] if key in ("gdp", "gdp_per_resident") else cities[city_id]["yields"].get(key)

        ranked = sorted((v for city_id in ranked_ids if (v := value(city_id)) is not None), reverse=True)
        ranks = {}
        for rank, metric in enumerate(ranked, 1):
            ranks.setdefault(metric, rank)
        for city_id, row in rows.items():
            row["ranks"][key] = ranks.get(value(city_id)) if city_id in ranked_ids else None
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


def explorer_gateway_columns(gateways):
    snapshot = "November 2026"
    columns = {}
    nearest = [
        ("major_port", "major port", gateways["port"]),
        *((f"{size}_airport", f"{size} airport with scheduled service", airport)
          for size, airport in gateways["airports"].items()),
    ]
    main_line = next((row for row in gateways["rail"] if row.get("main_line")), None)
    for key, name, row in [*nearest, ("main_line", "main line near city", main_line)]:
        if row is None:
            continue
        common = {
            "group": "Commerce", "source": row["source"], "period": row.get("period") or snapshot,
            "description": "Nearest mapped gateway in this class, by straight-line map distance from the city centre.",
        }
        columns[f"nearest_{key}"] = {
            **common, "label": f"Nearest {name}" if key != "main_line" else "Main line near city",
            "format": "text", "unit": "gateway", "value": row["name"],
        }
        distance_label = f"Distance to nearest {name}" if key != "main_line" else "Distance to main line near city"
        columns[f"nearest_{key}_km"] = {
            **common, "label": distance_label, "format": "int", "unit": "km", "value": row["distance_km"],
        }
    for key, label, freight in (("rail", "Rail", False), ("freight", "Freight rail", True)):
        rows = [row for row in gateways["rail"] if not row.get("main_line") and row["freight"] == freight]
        if rows:
            columns[f"city_{key}_corridors"] = {
                "label": f"{label} corridors", "format": "text", "unit": "mapped corridors", "group": "Commerce",
                "source": rows[0]["source"], "period": rows[0].get("period") or snapshot,
                "value": " · ".join(f"{row['name']} ({row['distance_km']} km)" for row in rows),
                "description": ("Named corridors within one grid cell of the footprint. "
                                "Distances are measured from the city centre to the mapped alignment."),
            }
    return columns
