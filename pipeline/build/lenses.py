"""lenses.json: 2026 projections per hex.

Population density is estimated per district (its census count grown at its state's projected rate, divided by its
DataMeet mapped area); the other lenses are the state's projected 2026 characteristics or interpolated 2026 health estimates (Technical Group
projections, with WorldPop age estimates for six places), so a state's hexes share one value.
"""

from __future__ import annotations

import json

from ..core.geo import MapProjection, Shape, ShapeIndex
from ..core.hexgrid import HexGrid
from ..core.lens_values import encode
from ..core.paths import WEB_DATA
from ..core.store import load_interim, write_web
from ..india import WUP_SOURCE
from ..india.advisor_sources import HP_REGISTRATIONS, VETERAN_METHOD, VETERAN_PERIOD, VETERAN_POPULATION, VETERAN_SOURCES
from ..india.city_conditions_sources import EVENTS
from ..india.city_sources import DISTRICT_AGE_SOURCE
from .advisor_statistics import veteran_population
from .air_weather import GROUP as WEATHER_GROUP, INPUTS as WEATHER_INPUTS, weather_lenses
from .boundaries import nearest_state
from .city_conditions import member_events
from .disasters import COVERAGE, PERIOD, disaster_lenses, event_summary, index_events, inventory
from .district_values import district_sample_values, small_district_values
from .projection import CITY_GROWTH_PERIOD, STATE_GROWTH_PERIOD, district_growth
from .state_metrics import GROUPS as METRIC_GROUPS
from .states import district_states, mapped_area

REQUIRES = ["_world", "census_a01", "datameet", "tg_projections", "states.json", "cities.json",
            "wonders.json", "resources.json", *WEATHER_INPUTS, "_state_metrics", VETERAN_POPULATION, DISTRICT_AGE_SOURCE]
PRODUCES = ["lenses.json", "lens_catalog.json"]

SOURCE = "tg_projections"
DISTRICT_POPULATION_SOURCES = ("census_a01", "datameet", SOURCE)
PARTIAL_NOTE = "Every hex of a state shows the state's value. The seven smaller North-East states share one combined " \
               "projection; Goa, Ladakh and the smaller union territories have none."
AGE_NOTE = "The seven smaller North-East states share one combined projection. WorldPop supplies age estimates for Goa " \
           "and five union territories. Ladakh has no age data."
AGE_SOURCE_LINE = "Projected for 1 March 2026 (MoHFW) · 2026 estimate (WorldPop)"
HEALTH_CREDIT = "IndiaCiv estimate for 2026 (interpolated from Technical Group projections)"
FULL_NOTE = "Every hex of a state or union territory shows its value."
# id, group, name, icon, unit, format, scale, ramp, higher_is, states.json profile key, description, note
STATE_LENSES = [
    ("state_density", "states", "Density", "l-density", "people / km²", "int", "log",
     ["#1b1035", "#4b2377", "#9a3b8a", "#e0645e", "#f9b24a", "#fff3a8"], "neutral", "density",
     "Residents per km² of each state or union territory, projected for 1 March 2026.", FULL_NOTE),
    ("growth", "states", "Growth, Mar 2025 – Mar 2026", "l-people", "% a year", "pct", "linear", ["#3a1c32", "#7b2d5b", "#d2557a", "#f7b267", "#fde9b8"],
     "neutral", "growth", f"Projected population growth, {STATE_GROWTH_PERIOD}.", FULL_NOTE),
    ("sex_ratio", "states", "Sex ratio", "l-people", "women per 1,000 men", "int", "linear",
     ["#24305e", "#4b5fa8", "#a7b4e0", "#f0c2e0", "#c0508c"], "neutral", "sex_ratio",
     "Women per 1,000 men, projected for 1 March 2026.", FULL_NOTE),
    ("children", "states", "Children", "l-age", "% aged 0-14", "pct", "linear", ["#203a43", "#2c7a7b", "#68d391", "#c6f68d", "#f6e05e"],
     "neutral", "age_0_14", "Share of the population aged 0–14 in 2026.", AGE_NOTE),
    ("elderly", "states", "Aged 60+", "l-age", "% aged 60+", "pct", "linear", ["#1a2a4a", "#3d5a98", "#8fa8d8", "#c9d6ef", "#eef3fb"],
     "neutral", "age_60", "Share of the population aged 60 and over in 2026.", AGE_NOTE),
    ("median_age", "states", "Median age", "l-age", "years", "years", "linear", ["#2a1b3d", "#5b3c88", "#9f7ccf", "#d6c5f0", "#f5f0ff"],
     "neutral", "median_age", "Median age in years in 2026.", AGE_NOTE),
    ("fertility", "health", "Fertility", "l-people", "children per woman", "float", "linear",
     ["#123524", "#2f6b4f", "#7fb77e", "#c8e6a0", "#f2f9d8"], "neutral", "tfr",
     "Total fertility rate (children per woman).", PARTIAL_NOTE),
    ("infant_mortality", "health", "Infant mortality", "l-uninsured", "per 1,000 births", "float", "linear",
     ["#fff1d6", "#f6b26b", "#e07a5f", "#c0392b", "#6d1a26"], "bad", "imr",
     "Infant deaths per 1,000 live births.", PARTIAL_NOTE),
    ("life_female", "health", "Life expectancy (women)", "l-amenities", "years", "years", "linear",
     ["#3b2417", "#7a5a2a", "#b9a24a", "#cfe08a", "#eef7c8"], "good", "life_female",
     "Life expectancy at birth of women.", PARTIAL_NOTE),
    ("life_male", "health", "Life expectancy (men)", "l-amenities", "years", "years", "linear",
     ["#3b2417", "#7a5a2a", "#b9a24a", "#cfe08a", "#eef7c8"], "good", "life_male",
     "Life expectancy at birth of men.", PARTIAL_NOTE),
]
# Profile values in the report's units → lens values (pct lenses are 0..1 fractions).
SCALE = {"age_0_14": 1 / 100, "age_60": 1 / 100}
AGE_KEYS = {"age_0_14", "age_60", "median_age"}

def domain(values: list) -> list[float]:
    have = sorted(v for v in values if v is not None)
    lo, hi = have[int(0.02 * len(have))], have[int(0.98 * len(have)) - 1]  # 2nd-98th percentile, as in usaciv
    return [lo, hi] if lo < hi else [min(have), max(have)]


def district_fallbacks(grid, owner, county, shapes, homes):
    missing = [i for i, (state, district) in enumerate(zip(owner, county)) if state >= 0 and district < 0]
    indexes = {}
    for state in {owner[i] for i in missing}:
        districts = [i for i, home in enumerate(homes) if home == state]
        if not districts:
            raise ValueError(f"No mapped district in state {state}")
        indexes[state] = districts, ShapeIndex([shapes.shapes[i] for i in districts])
    fallbacks = {}
    for i in missing:
        ids, index = indexes[owner[i]]
        fallbacks[i] = ids[nearest_state(*grid.center(*grid.col_row(i)), index)]
    return fallbacks


def district_sites(shapes, cities, wonders, resources):
    sites = [{"cities": [], "wonders": [], "resources": []} for _ in shapes.shapes]
    for key, items in [("cities", cities), ("wonders", wonders), ("resources", resources)]:
        for i, item in enumerate(items):
            if item.get("foreign_side"):
                continue
            district = shapes.locate(item.get("site_x", item["x"]), item.get("site_y", item["y"]))
            if district >= 0:
                sites[district][key].append(i if key == "resources" else item["id"])
    return sites


def city_lenses(cities: list[dict], size: int) -> list[dict]:
    definitions = [
        ("city_population", "City population", "population", "people", "int", "log",
         ["#1b1035", "#4b2377", "#9a3b8a", "#e0645e", "#f9b24a", "#fff3a8"],
         "UN projected population of each urban agglomeration in mid-2026."),
        ("city_growth", "Growth, mid-2025 – mid-2026", "projected_growth", "% a year", "pct", "linear",
         ["#3a1c32", "#7b2d5b", "#d2557a", "#f7b267", "#fde9b8"],
         f"Projected population growth from UN estimates, {CITY_GROWTH_PERIOD}."),
    ]
    lenses = []
    for lid, name, key, unit, fmt, scale, ramp, description in definitions:
        values = [None] * size
        # The biggest city supplies the tile's value if its banners share a tile.
        for city in reversed(cities):
            for cell in city["footprint"]:
                values[cell] = city[key]
        limits = domain(values) if any(value is not None for value in values) else ([1, 10] if scale == "log" else [0, 1])
        lenses.append({
            "id": lid, "group": "cities", "name": name, "icon": "l-people", "emoji": "",
            "unit": unit, "format": fmt, "scale": scale, "domain": limits,
            "ramp": ramp, "higher_is": "neutral", "source": WUP_SOURCE,
            "period": CITY_GROWTH_PERIOD if key == "projected_growth" else "mid-2026",
            "description": description, "note": "Values appear on city hexes only.", "values": values,
        })
    return lenses


def build() -> None:
    world = load_interim("_world")
    a01 = load_interim("census_a01")["districts"]
    dm = load_interim("datameet")
    tg = load_interim("tg_projections")
    grid = HexGrid(**world["grid"])
    proj = MapProjection(**world["projection"])
    owner = world["owner"]

    # Use the same mapped areas for district density and for blending small districts.
    states = sorted(dm["states"], key=lambda st: st["name"])
    districts = sorted(dm["districts"], key=lambda d: (d["state_code"], d["code"]))  # world.json order
    homes = district_states(districts, states)
    density = []
    areas = []
    places = {}
    hp_population = veteran_population("districts")
    try:
        district_ages = load_interim(DISTRICT_AGE_SOURCE)["districts"]
    except FileNotFoundError:
        district_ages = {}
    for d, geoid, k in zip(districts, world["counties"], homes):
        grow = district_growth(tg, states[k]["name"], d["state_code"])
        population = round(a01[geoid]["population"] * grow)
        area = round(mapped_area(d["rings"], proj), 1)
        areas.append(area)
        density.append(population / area if area else None)
        ring = max(d["rings"], key=len)
        center = proj(sum(p[0] for p in ring[:-1]) / (len(ring) - 1),
                      sum(p[1] for p in ring[:-1]) / (len(ring) - 1))
        estimate = {"period": "1 March 2026", "source": list(DISTRICT_POPULATION_SOURCES), "estimated": True}
        places[geoid] = {
            "state": world["states"][k] if k >= 0 else None,
            "population": population, "area_km2": area,
            "density": density[-1], "center": center,
            "provenance": {"population": estimate, "density": estimate},
        }
        if geoid in district_ages:
            places[geoid]["median_age"] = district_ages[geoid]
            places[geoid]["provenance"]["median_age"] = {
                "period": "mid-2026", "source": [DISTRICT_AGE_SOURCE, "datameet"], "estimated": True,
            }
        if geoid in HP_REGISTRATIONS:
            places[geoid]["registered_veterans"] = HP_REGISTRATIONS[geoid]
            if residents := hp_population.get(geoid):
                places[geoid]["veteran_share"] = round(HP_REGISTRATIONS[geoid] / residents, 4)
        if events := member_events({geoid}, EVENTS):
            places[geoid]["hazards"] = events

    samples = world["county_samples"]
    extra = small_district_values(owner, samples, grid, proj, districts, areas, density)
    dens = [None if v is None else round(v) for v in district_sample_values(owner, samples, density, extra)]
    lo, hi = domain(dens)
    lenses = [{
        "id": "density", "group": "people", "name": "Population", "icon": "l-people", "emoji": "👥",
        "unit": "people / km²", "format": "int", "scale": "log", "domain": [max(1, lo), hi],
        "ramp": ["#1b1035", "#4b2377", "#9a3b8a", "#e0645e", "#f9b24a", "#fff3a8"], "higher_is": "neutral",
        "source": SOURCE, "sources": list(DISTRICT_POPULATION_SOURCES),
        "description": "Residents per km², projected for 1 March 2026: each district's census count grown at its state's "
        "projected rate, divided by its DataMeet mapped area. Each hex averages the districts under its 7 sample points; a small "
        "district between the points is blended into the hex holding its centre by its share of the hex's area.",
        "period": "1 Mar 2026", "estimated": True,
        "source_line": "IndiaCiv estimate for 1 March 2026",
        "note": "An estimate: every district of a state is assumed to grow at the state's projected rate.",
        "values": dens,
    }]

    state_rows = json.loads((WEB_DATA / "states.json").read_text())
    veterans = [row.get("advisor_statistics", {}).get("registered_veterans") for row in state_rows]
    if any(value is not None for value in veterans):
        values = [veterans[o] if o >= 0 and not water else None for o, water in zip(owner, world["water"])]
        lenses.append({
            "id": "registered_veterans", "group": "states", "name": "Registered ex-servicemen",
            "icon": "l-people", "emoji": "", "unit": "people", "format": "int", "scale": "linear",
            "domain": domain(values), "ramp": ["#222a33", "#557588", "#a2c0c8", "#f3e3c3"],
            "higher_is": "neutral", "source": "registered_veterans_ksb", "sources": VETERAN_SOURCES,
            "period": VETERAN_PERIOD, "estimated": True,
            "source_line": f"IndiaCiv estimate · {VETERAN_PERIOD} · KSB and Ministry of Defence via PIB",
            "description": VETERAN_METHOD,
            "note": "Each hex shows its State/UT registration estimate where comparable snapshots exist.",
            "values": values,
        })
    profiles = [st["profile"] for st in state_rows]
    for lid, group, name, icon, unit, fmt, scale, ramp, higher, key, desc, note in STATE_LENSES:
        f = SCALE.get(key, 1)
        values = [None if o < 0 or profiles[o].get(key) is None else round(profiles[o][key] * f, 5) for o in owner]
        if not any(value is not None for value in values):
            continue
        lo, hi = domain(values)
        lenses.append({
            "id": lid, "group": group, "name": name, "icon": icon, "emoji": "", "unit": unit, "format": fmt,
            "scale": scale, "domain": [max(lo, 1), hi] if scale == "log" else [lo, hi], "ramp": ramp, "higher_is": higher,
            "source": SOURCE, "description": desc, "note": note, "values": values,
            "period": STATE_GROWTH_PERIOD if key == "growth" else "2026",
            **({"sources": [SOURCE, "datameet"]} if key == "density" else {}),
            **({"source_line": HEALTH_CREDIT, "estimated": True} if group == "health" else {}),
            **({"source_line": AGE_SOURCE_LINE, "sources": [SOURCE, "worldpop_age"], "estimated": True}
               if key in AGE_KEYS else {}),
        })
    cities = json.loads((WEB_DATA / "cities.json").read_text())
    wonders = json.loads((WEB_DATA / "wonders.json").read_text())["wonders"]
    resources = json.loads((WEB_DATA / "resources.json").read_text())["items"]
    shapes = ShapeIndex([Shape([[proj(*point) for point in ring] for ring in d["rings"]]) for d in districts])
    for place, sites in zip(places.values(), district_sites(shapes, cities, wonders, resources), strict=True):
        place["sites"] = sites
    lenses.extend(city_lenses(cities, grid.size))
    weather = weather_lenses(world, grid, proj, districts, cities, areas,
                             centers=[place["center"] for place in places.values()])
    for lens in weather:
        if "district_values" in lens:
            for place, value in zip(places.values(), lens.pop("district_values"), strict=True):
                place[lens["id"]] = value
    lenses.extend(weather)
    groups = [{"id": "people", "name": "Districts"}, {"id": "states", "name": "States & UTs"},
              {"id": "cities", "name": "Cities"}, {"id": "health", "name": "Health"}]
    for key, definition in load_interim("_state_metrics")["definitions"].items():
        records = [st["metrics"].get(key) for st in state_rows]
        values = [None if o < 0 or water or records[o] is None else records[o]["value"]
                  for o, water in zip(owner, world["water"])]
        present = [r["value"] for r in records if r is not None]
        if not present:
            continue
        lo, hi = min(present), max(present)
        state_details = {str(i): {k: r[k] for k in ("estimated", "coverage") if r.get(k)}
                         for i, r in enumerate(records) if r and (r.get("estimated") or r.get("coverage"))}
        sources = {r["source"] for r in records if r is not None}
        if denominator_source := definition.get("denominator_source"):
            sources.add(denominator_source)
        if key in {"urban_share", "electricity_pc", "gsdp_pc"}:
            sources.add(SOURCE)
        if key == "gsdp_pc" and any(r and r.get("estimated") for r in records):
            sources.add("gdp_fy26")
        lenses.append({**definition, "values": values, "domain": [lo, hi if hi > lo else lo + 1],
                       "state_details": state_details, "sources": sorted(sources)})
    groups.extend({"id": key, "name": label} for key, label in METRIC_GROUPS.items()
                  if any(lens["group"] == key for lens in lenses))
    if weather:
        groups.append(WEATHER_GROUP)
    district_homes = {key: world["states"][home] for key, home in zip(world["counties"], homes, strict=True) if home >= 0}
    events = inventory(world, district_homes, shapes, proj)
    state_events, district_events = index_events(events, district_homes)
    hazard_group, hazards = disaster_lenses(world, state_events, district_events)
    groups.append(hazard_group)
    lenses.extend(hazards)
    catalog = {
        "vintage": "Projected for 2026",
        "groups": groups,
        "lenses": [{key: value for key, value in lens.items() if key != "values"} for lens in lenses],
    }
    write_web("lens_catalog.json", catalog)
    write_web("lenses.json", {
        **catalog,
        "lenses": [{**lens, "values": encode(lens["values"])} for lens in lenses],
        "disasters": {
            "period": PERIOD, "coverage": COVERAGE, "events": events,
            "states": {key: event_summary(rows) for key, rows in state_events.items()},
            "districts": {key: event_summary(rows) for key, rows in district_events.items()},
        },
        "places": {"counties": places, "district_fallbacks": district_fallbacks(grid, owner, world["county"], shapes, homes)},
    })
