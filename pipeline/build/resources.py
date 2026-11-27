"""Map operating sites and representative growing areas on Indian hexes."""

import json
import math

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.paths import WEB_DATA
from ..core.store import load_interim, save_interim, write_web
from ..sources.resource_references import CROP_PERIOD, MINE_PERIOD
from .crop_resources import crop_items, world_elevation

GEM_SOURCES = ["gem_power", "gem_coal", "gem_iron", "gem_oil_gas"]
REQUIRES = ["_world", "world.json", *GEM_SOURCES, "cities.json"]
PRODUCES = ["resources.json", "_crop_production"]
GEM_PERIODS = {"gem_power": "Sep 2026", "gem_coal": "Aug 2026", "gem_iron": "Sep 2026",
               "gem_oil_gas": "Mar 2026"}
OFFSHORE_SNAP_KM = 130  # About three centre spacings on the former 25 km grid.

# In icon priority order. Thresholds are inclusive and use the displayed units.
POWER = [
    ("nuclear", "Nuclear plant", "☢️", "#e8d44d", 1),
    ("hydropower", "Hydroelectric plant", "💧", "#3fa7d6", 250),
    ("pumped_storage", "Pumped-storage hydro", "💧", "#5379bd", 1),
    ("coal", "Coal power plant", "🏭", "#5a5a5a", 1000),
    ("gas_plant", "Gas power plant", "⚡", "#f08a24", 500),
    ("oil_plant", "Oil power plant", "🛢️", "#59413b", 100),
    ("wind", "Wind farm", "🌬️", "#9fd8cb", 150),
    ("utility-scale solar", "Solar farm", "☀️", "#ffc93c", 150),
    ("bioenergy", "Bioenergy plant", "🌱", "#6fcf83", 50),
]

POWER_IDS = {"coal": "coal_plant", "hydropower": "hydro", "utility-scale solar": "solar"}


def resource(type_id, name, emoji, color, category, unit, description, source, icon=None):
    return dict(id=type_id, name=name, category=category, emoji=emoji, color=color, unit=unit,
                icon=icon or f"r-{type_id}", description=description, source=source)


TYPES = [
    resource(POWER_IDS.get(kind, kind), name, emoji, color, "energy", "MW",
             f"Operating plants with at least {minimum:,} MW of rated capacity in the September 2026 snapshot.",
             "gem_power", {"oil_plant": "r-oil", "bioenergy": "r-geothermal"}.get(kind))
    for kind, name, emoji, color, minimum in POWER
] + [
    resource("coal_mine", "Coal mine", "⛏️", "#4a4038", "mineral", "Mt/yr",
             "Operating coal mines with capacity of at least 2 million tonnes per year in the August 2026 snapshot.",
             "gem_coal"),
    resource("iron", "Iron ore mine", "⛓️", "#8a4b2a", "mineral", "Mt/yr",
             "Operating iron ore mines with design capacity of at least 2 million tonnes per year in the September "
             "2026 snapshot.", "gem_iron"),
] + [
    resource(kind, name, "🛢️", "#59413b", "energy", "field",
             "Operating fields in the March 2026 tracker. The tracker covers fields with annual production of at "
             "least 1 million barrels of oil equivalent or reserves of at least 25 million barrels of oil equivalent, "
             "plus previously tracked fields. Fields need a site coordinate. Offshore fields can snap to land within "
             f"{OFFSHORE_SNAP_KM} km of the land hex centre.",
             "gem_oil_gas", "r-oil")
    for kind, name in [("oil", "Oil field"), ("gas", "Gas field"), ("oil_gas", "Mixed or unspecified oil and gas field")]
]


CROP_TYPES = [
    ("tea", "Tea", "🍃", "#578b68", "luxury", "tea_regions", "Assam Valley, Darjeeling hills and Nilgiris."),
    ("coffee", "Coffee", "☕", "#865537", "luxury", "coffee_regions", "Kodagu, Chikkamagaluru and Wayanad."),
    ("cardamom", "Cardamom", "🌿", "#637a45", "luxury", "idukki_spices", "Idukki spice-growing country."),
    ("coconut", "Coconut", "🥥", "#4f826f", "luxury", "thrissur_crops", "Thrissur coconut clusters."),
    ("pepper", "Black pepper", "🌶️", "#6d5651", "luxury", "thrissur_crops", "Thrissur mixed farms."),
    ("ginger", "Ginger", "🫚", "#9b663b", "luxury", "thrissur_crops", "Thrissur mixed farms."),
    ("mango", "Mango", "🥭", "#ae6b24", "luxury", "ratnagiri_mango", "Ratnagiri Alphonso growing area."),
    ("rubber", "Rubber", "💧", "#485365", "strategic", "rubber_regions", "Major producing states."),
    ("silk", "Silk", "🧵", "#9e5976", "luxury", "kalaburagi_silk", "Kalaburagi cocoon-producing district."),
    ("rice", "Rice", "🌾", "#688738", "bonus", "pilibhit_rice", "Major producing districts."),
    ("wheat", "Wheat", "🌾", "#aa762d", "bonus", "punjab_wheat", "Major producing districts."),
    ("millets", "Millets", "🌾", "#8c6341", "bonus", "rajasthan_millets", "Shree Anna in major producing districts."),
    ("sugarcane", "Sugarcane", "🌿", "#487d55", "bonus", "up_sugarcane", "Major cane-producing districts."),
    ("cotton", "Cotton", "☁️", "#7d668f", "luxury", "vidarbha_cotton", "Major cotton-producing districts."),
    ("jute", "Jute", "🌿", "#607f7b", "luxury", "bengal_jute", "Documented jute growing areas."),
]

for kind, name, emoji, color, group, source, description in CROP_TYPES:
    TYPES.append(dict(resource(kind, name, emoji, color, "agri", None, description, source),
                      resource_class=group))
for kind, name, emoji, color, group, category, source, description in [
    ("diamond", "Diamonds", "💎", "#537b9d", "luxury", "mineral", "panna_diamond", "Majhgawan mine in Panna."),
    ("bauxite", "Bauxite", "⛏️", "#a45138", "strategic", "mineral", "panchpatmali_bauxite", "Panchpatmali mine in Odisha."),
    ("limestone", "Limestone", "⛏️", "#758378", "strategic", "mineral", "jamul_limestone", "Jamul mine in Chhattisgarh."),
    ("fish", "Fish", "🐟", "#3a7892", "bonus", "agri", "veraval_fish", "Named coastal fishing landing centres."),
    ("copper", "Copper mine", "⛏️", "#ad6544", "strategic", "mineral", "hcl_mines",
     "Selected civilian mines with operator-confirmed ore production."),
    ("lead_zinc", "Lead-zinc mine", "⛏️", "#7b8197", "strategic", "mineral", "hzl_mines",
     "Selected civilian mines with operator-confirmed production, including verified silver by-products."),
    ("battery", "Battery storage", "🔋", "#538b78", "strategic", "energy", "seci_battery",
     "Selected commissioned civilian battery projects with a 2026 operator record."),
]:
    TYPES.append(dict(resource(kind, name, emoji, color, category, None, description, source),
                      resource_class=group))
for definition in TYPES:
    definition.setdefault("resource_class", "strategic")

MINIMUM = {kind: minimum for kind, _, _, _, minimum in POWER} | {
    "coal_mine": 2, "iron": 2, "oil": 1, "gas": 1, "oil_gas": 1,
}
for definition in TYPES:
    kind = definition["id"]
    if kind in {"copper", "lead_zinc"}:
        definition["period"] = MINE_PERIOD
    elif kind == "battery":
        definition["period"] = "Aug 2026"
    original = next((k for k, v in POWER_IDS.items() if v == kind), kind)
    if kind in {"oil", "gas", "oil_gas"}:
        definition["threshold"] = "GEM tracker eligibility"
    elif original in MINIMUM:
        definition["threshold"] = f"≥ {MINIMUM[original]:,} {definition['unit']}"
    elif kind in {"copper", "lead_zinc", "bauxite", "limestone", "diamond", "battery"}:
        definition["threshold"] = "Verified operation in the stated period"
RANK = {t["id"]: i for i, t in enumerate(TYPES)}


def select_sites(sites):
    return [dict(site, type=POWER_IDS.get(site["type"], site["type"])) for site in sites
            if site["type"] in MINIMUM and site["value"] >= MINIMUM[site["type"]]]


def land_cell(grid, owner, x, y, rings):
    cell = grid.cell_at(x, y)
    if cell < 0:
        return -1
    frontier, seen = {cell}, {cell}
    for _ in range(rings + 1):
        land = [n for n in frontier if owner[n] >= 0]
        if land:
            def distance(n):
                cx, cy = grid.center(*grid.col_row(n))
                return (cx - x) ** 2 + (cy - y) ** 2, n

            return min(land, key=distance)
        frontier = {n for c in frontier for n in grid.neighbours(c)} - seen
        seen |= frontier
    return -1


def offshore_land_cell(grid, owner, x, y):
    cell = grid.cell_at(x, y)
    if cell < 0 or owner[cell] >= 0:
        return cell
    candidates = ((math.dist((x, y), grid.center(*grid.col_row(i))), i)
                  for i, state in enumerate(owner) if state >= 0)
    distance, closest = min(candidates, default=(math.inf, -1))
    return closest if distance <= OFFSHORE_SNAP_KM else -1


def summarize(items, types):
    units = {t["id"]: t["unit"] for t in types}

    def blank(kind):
        return {"count": 0, "value": None, "unit": units[kind]}

    national = {kind: blank(kind) for kind in units}
    states = {}
    for item in items:
        kind = item["type"]
        state = states.setdefault(item["state"], {}).setdefault(kind, blank(kind))
        for row in (national[kind], state):
            row["count"] += 1
            if item["value"] is not None:
                row["value"] = (row["value"] or 0) + item["value"]
    for group in [national, *states.values()]:
        for row in group.values():
            if row["value"] is not None:
                row["value"] = round(row["value"], 6)
    return {"note": "Counts of mapped markers. Numeric totals are for items with recorded values.",
            "national": national, "states": states}


def mapped_gem_sites(world, grid, project):
    items = []
    for source in GEM_SOURCES:
        data = load_interim(source)
        sites = data["sites"]
        if source == "gem_oil_gas" and data.get("technology_version", 1) < 2:
            sites = [dict(site, type="oil_gas") for site in sites]
        for site in select_sites(sites):
            kind = site["type"]
            x, y = project(site["lon"], site["lat"])
            if source == "gem_oil_gas":
                cell = offshore_land_cell(grid, world["owner"], x, y)
            else:
                cell = land_cell(grid, world["owner"], x, y, 1)
            if cell < 0:
                continue
            site_point = {"site_x": round(x, 6), "site_y": round(y, 6)} if site.get("location_accuracy") == "exact" else {}
            x, y = round(x, 1), round(y, 1)
            snapped = grid.cell_at(x, y) != cell
            if snapped:
                x, y = (round(v, 1) for v in grid.center(*grid.col_row(cell)))
            period = GEM_PERIODS[source]
            detail = f"Operating in the {period} snapshot"
            if snapped:
                detail += " · shown on the nearest land tile"
            items.append(dict(type=kind, name=site["name"], x=x, y=y, cell=cell,
                              value=site["value"], detail=detail, state=world["states"][world["owner"][cell]],
                              cbsa=None, source=source, period=period, **site_point))
    return items


def build():
    world = load_interim("_world")
    grid = HexGrid(**world["grid"])
    project = MapProjection(**world["projection"])
    items = mapped_gem_sites(world, grid, project)
    cities = {city["cell"] for city in json.loads((WEB_DATA / "cities.json").read_text())}
    rendered = None if "elev" in world else json.loads((WEB_DATA / "world.json").read_text())
    elevation = world_elevation(world, rendered)
    items.extend(crop_items(world, grid, project, cities, {item["cell"] for item in items}, elevation))
    items.sort(key=lambda it: (RANK[it["type"]], -(it["value"] or 0), it["name"], it["cell"]))
    save_interim("_crop_production", dict(version=1, grid=world["grid"], projection=world["projection"],
                                          period=CROP_PERIOD, unit="t", estimated=True, source=None,
                                          method=None, crops={}), vintage=CROP_PERIOD)
    present = {it["type"] for it in items}
    types = [t for t in TYPES if t["id"] in present]
    summary = summarize(items, types)
    write_web("resources.json", dict(types=types, items=items, summary=summary))
    print("    " + ", ".join(f"{kind} {row['count']}" for kind, row in summary["national"].items()))
