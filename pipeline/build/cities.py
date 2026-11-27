"""Place UN urban agglomerations and write city and national yield records."""

from __future__ import annotations

import math
from collections import deque
from typing import Callable

from ..core.geo import MapProjection, Shape, ShapeIndex
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, load_interim_payload, write_web
from ..india import DISPLAY_NAMES, GHSL_UCDB, WUP_SOURCE
from ..india.city_sources import LABOUR_SOURCE
from .advisor_statistics import civic_office_points, industry_shares, national_statistics
from ..core.source import osm_notice
from .boundaries import nearest_state
from .city_people import age_profile, footprint_workforce, qualitative_plaques
from .city_view import cohort
from .projection import CITY_GROWTH_PERIOD, state_profile, state_vitals
from .state_metrics import FY
from .world import STATE_ABBR
from .yields import YIELDS, apply_city_yields, rank_yields, regional_economy

REQUIRES = ["_world", WUP_SOURCE, "tg_projections", "datameet", "_yields", GHSL_UCDB, LABOUR_SOURCE]
PRODUCES = ["cities.json", "nation.json"]

PEERS = 5
CITY_STATE_SNAP_KM = 10
INDIA_AREA_KM2 = 3_287_263  # official area of India (includes areas under the occupation of Pakistan and China)
RANK_KEYS = ["population", "gdp", "gdp_per_capita", "growth"]
NO_ECONOMY = {
    "employed": None, "yields": {}, "jobs": {}, "median_income": None, "median_rent": None, "home_value": None,
    "unemployment": None, "rent_burden": None, "gdp": None, "gdp_year": None, "growth": None, "growth_years": None,
}


def nearest_land(grid: HexGrid, owner: list[int], start: int) -> int:
    """The closest land cell (owner >= 0) to `start` in hex steps, breadth first."""
    seen, todo = {start}, deque([start])
    while todo:
        i = todo.popleft()
        if owner[i] >= 0:
            return i
        for j in grid.neighbours(i):
            if j not in seen:
                seen.add(j)
                todo.append(j)
    raise ValueError("no land cell on the map")


def add_ranks(cities: list[dict]) -> None:
    """Population rank (list is sorted by population) and the PEERS cities closest in population by ratio."""
    for k, c in enumerate(cities):
        c["ranks"] = {key: None for key in RANK_KEYS} | {"population": k + 1}
        near = sorted((abs(math.log(c["population"] / o["population"])), j) for j, o in enumerate(cities) if o is not c)
        c["peers"] = [cities[j]["id"] for _, j in near[:PEERS]]


def add_headline_ranks(cities):
    """Rank the mapped cities with a value, preserving population order for ties."""
    counts = {}
    for city in cities:
        gdp = city["yields"].get("gold")
        city["gdp_per_capita"] = None if gdp is None else gdp / city["population"]
        city.setdefault("ranks", {}).update(dict.fromkeys(RANK_KEYS))
        city["rank_counts"] = counts
    fields = {
        "population": lambda c: c["population"],
        "growth": lambda c: c.get("projected_growth"),
        "gdp": lambda c: c["yields"].get("gold"),
        "gdp_per_capita": lambda c: c["gdp_per_capita"],
    }
    for key, value in fields.items():
        ranked = sorted((c for c in cities if value(c) is not None), key=value, reverse=True)
        counts[key] = len(ranked)
        for rank, city in enumerate(ranked, 1):
            city["ranks"][key] = rank


def city_state_lookup(datameet, project):
    names = [state["name"] for state in datameet["states"]]
    index = ShapeIndex([Shape([[project(lon, lat) for lon, lat in ring] for ring in state["rings"]])
                        for state in datameet["states"]])

    def lookup(x, y):
        state = index.locate(x, y)
        if state < 0:
            state = nearest_state(x, y, index, CITY_STATE_SNAP_KM)
        if state < 0:
            raise ValueError(f"No DataMeet state within {CITY_STATE_SNAP_KM} km of ({x:.1f}, {y:.1f})")
        name = names[state]
        return STATE_ABBR[name], name

    return lookup


def place_cities(
    places: list[dict], grid: HexGrid, owner: list[int], to_map: Callable[[float, float], tuple[float, float]],
    state_at: Callable[[float, float], tuple[str, str]], state_abbrs: list[str],
) -> tuple[list[dict], list[str]]:
    """Keep every populated agglomeration. Return city rows and names with relocated banners.

    Reserve every natural anchor before moving a collision, so a relocated banner never
    displaces another city from its own tile. Try the adjacent ring, then stack.
    """
    anchors = []
    for p in sorted(places, key=lambda p: -(p["population"] or 0)):
        if not p["population"] or p["population"] <= 0:
            continue
        x, y = to_map(p["x"] / 1000, p["y"] / 1000)
        cell = grid.cell_at(x, y)
        if cell < 0 or owner[cell] < 0:
            cell = nearest_land(grid, owner, max(cell, 0))
        anchors.append((p, x, y, cell))

    reserved = {cell for _, _, _, cell in anchors}
    occupied = set()
    cities, relocated = [], []
    for p, x, y, cell in anchors:
        abbr, region = state_at(x, y)
        if cell in occupied:
            free = [i for i in grid.neighbours(cell)
                    if i not in reserved and i not in occupied and owner[i] >= 0 and state_abbrs[owner[i]] == abbr]
            if free:
                cell = min(free, key=lambda i: (math.dist(grid.center(*grid.col_row(i)), (x, y)), i))
                relocated.append(p["name"])
        city = {
            "id": str(p["id"]),
            "name": (name := DISPLAY_NAMES.get(p["name"], p["name"])),
            "full": name if region == name else f"{name}, {region}",
            "states": [abbr],
            "metro": True,
            "capital": bool(p["capital"]),
            "x": round(x, 1),
            "y": round(y, 1),
            "cell": cell,
            "population": p["population"],
            **NO_ECONOMY,
            "projected_growth": p.get("projected_growth") if p.get("growth_period") == CITY_GROWTH_PERIOD else None,
            "growth_period": p.get("growth_period"),
            "counties": [],
            "footprint": [cell],
            "pop_series": None,
        }
        occupied.add(cell)
        cities.append(city)
    add_ranks(cities)
    return cities, relocated


def city_state_mismatches(cities, places, project, state_at):
    by_id = {str(place["id"]): place for place in places}
    mismatches = []
    for city in cities:
        place = by_id.get(city.get("id"))
        if place is None:
            mismatches.append(f"{city.get('name', 'Unnamed city')}: no matching UN location")
            continue
        x, y = project.from_projected(place["x"] / 1000, place["y"] / 1000)
        expected, _ = state_at(x, y)
        if city.get("states") != [expected]:
            mismatches.append(f"{city['name']}: expected {expected}, got {city.get('states')}")
    return mismatches


def build() -> None:
    world = load_interim("_world")
    wup = load_interim_payload(WUP_SOURCE)
    places = wup["data"]["places"]
    tg = load_interim_payload("tg_projections")
    proj = MapProjection(**world["projection"])
    grid = HexGrid(**world["grid"])

    state_at = city_state_lookup(load_interim("datameet"), proj)
    cities, relocated = place_cities(places, grid, world["owner"], proj.from_projected, state_at, world["states"])
    city_view_ids = set(cohort())
    for city in cities:
        city["provenance"] = {"population": {"period": wup["vintage"], "source": WUP_SOURCE}}
        if city["projected_growth"] is not None:
            city["provenance"]["projected_growth"] = {"period": CITY_GROWTH_PERIOD, "source": WUP_SOURCE}
        if city["id"] in city_view_ids:
            city["city_view"] = True
    stacked = len(cities) - len({c["cell"] for c in cities})
    print(f"    {len(cities)} cities; {len(relocated)} relocated ({', '.join(relocated)}); {stacked} stacked")
    yields = load_interim("_yields")
    profiles, state_populations = apply_city_yields(cities, world, yields)
    labour = load_interim(LABOUR_SOURCE)
    places_by_id = {str(place["id"]): place for place in places}
    for city in cities:
        profile = profiles.get(city["id"], {})
        ages = {int(age): mass for age, mass in profile.get("age_mass", {}).items()}
        age = age_profile(city["population"], ages)
        adults = None if age is None else city["population"] - age["counts"]["0_14"]
        series = places_by_id[city["id"]].get("population_2026")
        if series:
            city["population_2026"] = series
        work = footprint_workforce(city["population"], adults, state_populations[city["id"]], labour["states"])
        if work is not None:
            work["national_urban_unemployment_15_plus"] = labour.get("national_urban_unemployment_15_plus")
            city["resident_workforce"] = work
        city["industry_plaques"] = qualitative_plaques(city["id"], {d["id"] for d in profile.get("districts", [])})
    add_headline_ranks(cities)
    rank_yields(cities)
    national_population = 1000 * tg["data"]["population"]["INDIA"]["2026"][0]
    national_gdp = yields["rows"]["IN"]["values"]["gold"]
    # Technical Group projections are dated 1 March. Interpolate to the UN city reference date, 1 July.
    projected = tg["data"]["population"]["INDIA"]
    july_population = national_population + (122 / 1826) * (1000 * projected["2031"][0] - national_population)
    for city in cities:
        gdp = city["yields"]["gold"]
        city["national_shares"] = {
            "gdp": {"value": gdp / national_gdp, "period": FY, "source": ["gdp_fy26", "gsdp_fy26"],
                    "estimated": True} if gdp is not None and national_gdp else None,
            "population": {"value": city["population"] / july_population, "period": "1 July 2026",
                           "source": [WUP_SOURCE, "tg_projections"], "estimated": True},
        }
    statistics = national_statistics(industry_shares(), national_population, national_gdp)
    write_web("cities.json", cities)
    write_web(
        "nation.json",
        {
            "vintage": "Projected for 1 March 2026",  # short: the top bar shows it beside the year
            "year": 2026,
            "gdp_vintage": None,
            "nation": {"population": national_population,
                       **NO_ECONOMY, **regional_economy(yields["rows"]["IN"])},
            "profile": {**state_profile(tg["data"], "INDIA"), **state_vitals(tg["data"], "INDIA"),
                        "density": 1000 * tg["data"]["population"]["INDIA"]["2026"][0] / INDIA_AREA_KM2},
            "metrics": load_interim("_state_metrics")["geographies"]["IN"],
            "yields": YIELDS,
            "industries": {},
            "advisor_statistics": {**statistics, "civic_offices": civic_office_points(proj)},
            "osm_license": osm_notice("Civic office points in advisor_statistics"),
        },
    )
