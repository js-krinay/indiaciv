"""IndiaCiv yield formulas and geographic allocation."""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from ..core.geo import MapProjection, Shape
from ..core.hexgrid import HexGrid
from ..core.paths import WEB_DATA
from ..core.store import load_interim, save_interim
from ..india import CITY_POPULATION_GRID, GHSL_UCDB, WUP_SOURCE
from ..india.city_economy_sources import state_sector_mix
from ..india.science_sources import SOURCES as SCIENCE_SOURCES, research_points
from ..india.yield_sources import ASI_SOURCE, FOODGRAINS, PILGRIMAGE
from .city_view import footprint_extent, grid_fingerprint
from .projection import state_population
from .resources import GEM_SOURCES, TYPES, land_cell, mapped_gem_sites, summarize
from .science import RULE as SCIENCE_RULE, research_by_state, science_yield
from .state_metrics import ALIASES, FY
from .world import STATE_ABBR

REQUIRES = ["_world", "_state_metrics", "tg_projections", *GEM_SOURCES, "wonders.json", "cea_fy26", ASI_SOURCE]
PRODUCES = ["_yields"]

CROP_YEAR = "Crop year 2025-26 (1 Jul 2025 – 30 Jun 2026)"
SNAPSHOT = "27 Nov 2026"
CAPACITY = "GEM snapshots (Aug–Sep 2026)"


def definition(key, emoji, color, unit, scale, period, description, *sources):
    return dict(key=key, label=key.title(), icon=f"y-{key}", emoji=emoji, color=color,
                unit=unit, scale=scale, period=period, description=description, sources=sources)


YIELDS = [
    definition("food", "🌾", "#7fbf3f", "t", 100_000, CROP_YEAR,
               "Final national foodgrain tonnage, allocated locally by the share of mapped WorldCover cropland.",
               "foodgrains_fy26", "india_terrain"),
    definition("production", "⚙️", "#d9823b", "points", 1, f"{FY} · {CAPACITY}",
               "One point each per 1,000 GWh supplied, 1,000 MW of mapped power capacity or 10 Mt/yr of mapped mine capacity. "
               "Cities allocate electricity by clipped state area and count capacity at sites inside the footprint "
               "or centre hex where no footprint exists. The combined Jammu & Kashmir and Ladakh supply "
               "is split by population. Damodar Valley Corporation is included in the national figure.",
               "cea_fy26", "gem_power", "gem_coal", "gem_iron"),
    definition("gold", "💰", "#f2c94c", "INR", 10_000_000_000, FY,
               "Nominal GDP and GSDP. Earlier state figures are carried forward at India's nominal GDP growth. "
               "Where no state baseline exists, projected population is multiplied by India's GDP per person. "
               "City estimates compare UN mid-2026 agglomeration populations, split across states by footprint population, "
               "with the 1 Mar 2026 state urban projections. Shares are scaled down where mapped cities exceed the state projection.",
               "gdp_fy26", "gsdp_fy26", "gsdp_components", "delhi_gsdp_fy26", "tg_urban", "tg_projections",
               WUP_SOURCE, GHSL_UCDB, CITY_POPULATION_GRID),
    definition("science", "🔬", "#4fa3e0", "points", 1, SNAPSHOT, SCIENCE_RULE,
               *(source.id for source in SCIENCE_SOURCES)),
    definition("culture", "🎭", "#b07ce0", "points", 1, f"{FY} · {SNAPSHOT} wonders",
               "One point per mapped wonder plus one per 100,000 domestic and international ticketed entries "
               "at the ten ASI monuments with the most domestic entries. Cities count sites inside the clipped "
               "urban footprint or centre hex where no footprint exists.",
               ASI_SOURCE, "india_wonders"),
    definition("faith", "🪔", "#d5a3e6", "sites", 1, SNAPSHOT,
               "Count of selected major pilgrimage sites from the wonder inventory and named PRASHAD destinations. "
               "Cities count sites inside the clipped urban footprint or centre hex where no footprint exists.",
               "pilgrimage_sites", "india_wonders"),
]
KEYS = [row["key"] for row in YIELDS]
PERIODS = {row["key"]: row["period"] for row in YIELDS}


def allocate(total, part, whole):
    return total * part / whole if total is not None and whole > 0 else None


def gold_city_components(rows, population_by_state, mapped_population):
    components = {}
    for state, population in population_by_state.items():
        row = rows[state]
        urban = row["urban_population"]
        value = allocate(row["values"]["gold"], population, max(urban, mapped_population[state])) if urban else None
        if value is None:
            return None
        components[state] = value
    return components or None


def gold_city(rows, population_by_state, mapped_population):
    components = gold_city_components(rows, population_by_state, mapped_population)
    return None if components is None else round(sum(components.values()))


def production(gwh, mw, mine_capacity):
    return None if gwh is None else round(gwh / 1000 + mw / 1000 + mine_capacity / 10, 1)


def culture(entries, wonders):
    return round(wonders + entries / 100_000, 1)


def count_sites(sites, cells):
    return sum(row["cell"] in cells for row in sites)


def cropland_weights(world):
    return {i: share / 100 for i, share in enumerate(world["pct"]["crop"]) if world["owner"][i] >= 0}


def optional_interim(name):
    try:
        return load_interim(name)
    except FileNotFoundError:
        return {}


def point_sites(points, world):
    grid = HexGrid(**world["grid"])
    project = MapProjection(**world["projection"])
    rows = []
    for name, lon, lat in points:
        x, y = project(lon, lat)
        cell = land_cell(grid, world["owner"], x, y, 1)
        if cell < 0:
            raise ValueError(f"Yield site outside Indian land: {name}")
        rows.append({"name": name, "cell": cell, "x": x, "y": y})
    return rows


def inputs(world, metrics, electricity, resources, wonders, population, asi_entries):
    states = world["states"]
    names = dict(zip(world["state_names"], states))
    names["India"] = "IN"
    cells = defaultdict(list)
    for cell, owner in enumerate(world["owner"]):
        if owner >= 0:
            cells[states[owner]].append(cell)
    crop = cropland_weights(world)
    total_crop = sum(crop.values())
    available = {names[ALIASES.get(name, name)]: value for name, value in electricity.items()}
    split = [names["Jammu & Kashmir"], names["Ladakh"]]
    if split[0] in available:
        combined = available[split[0]]
        for state in split:
            available[state] = allocate(combined, population[state], sum(population[s] for s in split))
    power = resources["summary"]
    capacity_units = {group["id"]: group["unit"] for group in resources["types"]}
    capacity_sites = [
        {**site, "unit": capacity_units[site["type"]], "exact": "site_x" in site,
         "x": site.get("site_x", site["x"]), "y": site.get("site_y", site["y"])}
        for site in resources["items"] if capacity_units[site["type"]] in {"MW", "Mt/yr"}
    ]
    wonders = [w for w in wonders if not w["foreign_side"]]
    research = research_by_state()
    if unknown := research.keys() - set(states):
        raise ValueError(f"Research roster has unknown states: {', '.join(sorted(unknown))}")
    national_research = Counter()
    for counts in research.values():
        national_research.update(counts)
    research["IN"] = national_research
    faith = point_sites(PILGRIMAGE, world)
    faith += [w for w in wonders if w["id"] in {"golden-temple", "whc-1056", "whc-234", "whc-524", "whc-927",
                                              "whc-250", "whc-241", "whc-1670"}]
    if not asi_entries.keys() <= {w["id"] for w in wonders}:
        raise ValueError("Some ASI sites are missing from the wonder inventory")

    rows = {}
    for state in [*states, "IN"]:
        is_nation = state == "IN"
        covered = set(crop if is_nation else cells[state])
        capacity = power["national"] if is_nation else power["states"].get(state, {})
        mw = sum(row["value"] for row in capacity.values() if row["unit"] == "MW")
        mines = sum(row["value"] for row in capacity.values() if row["unit"] == "Mt/yr")
        visits = sum(asi_entries.get(w["id"], 0) for w in wonders if w["cell"] in covered)
        monuments = count_sites(wonders, covered)
        gsdp = metrics[state].get("gsdp_pc", {})
        if gsdp.get("nominal_inr") is None and not is_nation and (national_gdp := metrics["IN"].get("gsdp_pc")):
            gsdp = {"nominal_inr": round(allocate(national_gdp["nominal_inr"], population[state], population["IN"])),
                    "estimated": True, "source": national_gdp["source"]}
        share = metrics[state].get("urban_share", {}).get("value")
        crop_area = sum(crop[cell] for cell in covered)
        rows[state] = {
            "land": len(covered), "cropland": crop_area,
            "urban_population": population[state] * share if share is not None else None,
            "gold_estimated": gsdp.get("estimated", False), "gold_source": gsdp.get("source"),
            "values": {
                "food": FOODGRAINS if is_nation else allocate(FOODGRAINS, crop_area, total_crop),
                "production": production(available.get(state), mw, mines),
                "gold": gsdp.get("nominal_inr"),
                "science": science_yield(research[state]),
                "culture": culture(visits, monuments),
                "faith": count_sites(faith, covered),
            },
            "estimated": ["food", *(["production"] if state in split else [])] if not is_nation else [],
            "components": {"science": dict(research[state]), "culture": {"Mapped wonders": monuments}},
        }
    return {"rows": rows, "sites": {"faith": faith, "wonders": wonders, "capacity": capacity_sites},
            "asi_entries": asi_entries, "electricity": available}


def economy(values, estimated, components, gold_source=None, footprint=None):
    return {
        "yields": values,
        "yield_meta": {key: {"estimated": key in estimated, "period": PERIODS[key],
                             **({"components": components[key]} if key in components else {}),
                             **({"source": gold_source} if key == "gold" and gold_source else {}),
                             **({"derivation": "Derived from CEA electricity availability and GEM capacity"} if key == "production" else {}),
                             **({"derivation": "Derived from ASI ticketed entries and the IndiaCiv wonder inventory"} if key == "culture" else {}),
                             **({"coverage": footprint} if footprint and key != "gold" else {})}
                       for key in KEYS},
    }


def regional_economy(row):
    estimated = row["estimated"] + (["gold"] if row["gold_estimated"] else [])
    return economy(row["values"], estimated, row["components"], row["gold_source"])


def district_state_map(datameet):
    from .states import district_states

    districts, states = datameet["districts"], datameet["states"]
    return {f"{district['state_code']:02d}-{district['code']:03d}": STATE_ABBR[states[index]["name"]]
            for district, index in zip(districts, district_states(districts, states)) if index >= 0}


def footprint_overlaps(profile, district_state, hex_area):
    population, area = Counter(), Counter()
    for district in profile["districts"]:
        state = district_state[district["id"]]
        population[state] += (district["district_population"] or 0) * (district["population_share"] or 0)
        area[state] += district["footprint_share"] * hex_area
    return population, area


def sites_in_footprint(sites, shape, centre_cell):
    if shape is None:
        return [site for site in sites if site["cell"] == centre_cell]
    return [site for site in sites if shape.contains(site["x"], site["y"])]


def apply_city_yields(cities, world, data):
    from .city_economy import city_output_growth, city_sector_output

    prepared = optional_interim(GHSL_UCDB)
    profiles = (prepared.get("profiles", {}) if prepared
                and prepared.get("grid_fingerprint") == grid_fingerprint(world) else {})
    crop = cropland_weights(world)
    rows = data["rows"]
    mixes = {state: state_sector_mix(state, name, FY)
             for state, name in zip(world["states"], world["state_names"])}
    total_crop = rows["IN"]["cropland"]
    sites = data["sites"]
    exact_capacity = [site for site in sites["capacity"] if site["exact"]]
    datameet = load_interim("datameet")
    district_state = district_state_map(datameet)
    grid = HexGrid(**world["grid"])
    project = MapProjection(**world["projection"])
    research = []
    for point in research_points(datameet, district_state):
        x, y = project(point["lon"], point["lat"])
        research.append({"kind": point["kind"], "x": x, "y": y, "cell": grid.cell_at(x, y)})
    mapped_population = defaultdict(float)
    footprints = {}
    for city in cities:
        profile = profiles.get(city["id"], {})
        cells = [cell for cell in profile.get("cells", []) if cell["hex_fraction"] is not None]
        fractions = {cell["cell"]: cell["hex_fraction"] for cell in cells}
        coverage = "Mapped urban footprint" if fractions else "City centre hex proxy"
        shape = None
        if fractions:
            city["mapped_extent"] = footprint_extent(profile, grid)
            if not profile.get("yield_rings"):
                raise ValueError("City footprint polygons missing. Re-run the City View preparation in README.md.")
            shape = Shape(profile["yield_rings"])
            mass, area = footprint_overlaps(profile, district_state, sum(fractions.values()))
        else:
            fractions = {city["cell"]: 1}
            mass = area = {city["states"][0]: 1}
        population = {state: allocate(city["population"], weight, sum(mass.values()))
                      for state, weight in mass.items() if weight > 0}
        for state, value in population.items():
            mapped_population[state] += value
        footprints[city["id"]] = (fractions, coverage, area, population, shape)

    for city in cities:
        fractions, coverage, areas, population, shape = footprints[city["id"]]
        crop_area = sum(crop.get(cell, 0) * fraction for cell, fraction in fractions.items())
        city_wonders = sites_in_footprint(sites["wonders"], shape, city["cell"])
        entries = sum(data["asi_entries"].get(site["id"], 0) for site in city_wonders)
        wonders = len(city_wonders)
        city_research = Counter(site["kind"] for site in sites_in_footprint(research, shape, city["cell"]))
        components = {"culture": {"Mapped wonders": wonders},
                      "science": dict(city_research)}
        supply_shares = [allocate(data["electricity"].get(state), area, rows[state]["land"])
                             for state, area in areas.items()]
        supply = sum(supply_shares) if all(value is not None for value in supply_shares) else None
        capacity = sites_in_footprint(exact_capacity if shape else sites["capacity"], shape, city["cell"])
        gold_components = gold_city_components(rows, population, mapped_population)
        values = {
            "food": allocate(FOODGRAINS, crop_area, total_crop),
            "production": production(supply, sum(site["value"] for site in capacity if site["unit"] == "MW"),
                                     sum(site["value"] for site in capacity if site["unit"] == "Mt/yr")),
            "gold": None if gold_components is None else round(sum(gold_components.values())),
            "science": science_yield(city_research),
            "culture": culture(entries, wonders),
            "faith": len(sites_in_footprint(sites["faith"], shape, city["cell"])),
        }
        city.update(economy(values, {"food", "gold", "production"}, components, footprint=coverage))
        city["state_sector_mix"] = mixes[city["states"][0]]
        city["sector_output"] = city_sector_output(gold_components, mixes)
        city["output_growth"] = city_output_growth(gold_components)
    return profiles, {city_id: footprint[3] for city_id, footprint in footprints.items()}


def rank_yields(rows):
    for key in KEYS:
        for row in rows:
            row["ranks"][key] = None
        ranked = sorted((row for row in rows if row["yields"][key] is not None),
                        key=lambda row: -row["yields"][key])
        for rank, row in enumerate(ranked, 1):
            row["ranks"][key] = rank


def build():
    world = load_interim("_world")
    tg = load_interim("tg_projections")
    population = {state: state_population(tg, name) for state, name in zip(world["states"], world["state_names"])}
    population["IN"] = 1000 * tg["population"]["INDIA"]["2026"][0]
    items = mapped_gem_sites(world, HexGrid(**world["grid"]), MapProjection(**world["projection"]))
    types = [row for row in TYPES if row["unit"] in {"MW", "Mt/yr"}]
    included = {row["id"] for row in types}
    items = [item for item in items if item["type"] in included]
    resources = {"items": items, "types": types, "summary": summarize(items, types)}
    wonders = json.loads((WEB_DATA / "wonders.json").read_text())["wonders"]
    metrics = load_interim("_state_metrics")["geographies"]
    save_interim("_yields", inputs(world, metrics, load_interim("cea_fy26"), resources, wonders, population,
                                   load_interim(ASI_SOURCE)))
