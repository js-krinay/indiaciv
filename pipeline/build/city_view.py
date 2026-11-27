"""Build the optional India City View profiles keyed by UN agglomeration ID."""

import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from unicodedata import normalize

from ..core.geo import MapProjection, Shape
from ..core.paths import WEB_DATA
from ..core.hexgrid import SQRT3, HexGrid
from ..core.store import load_interim, write_web
from ..india import CITY_POPULATION_GRID, GHSL_UCDB
from ..india.city_sources import AGE_SOURCE
from ..india.science_sources import research_points
from ..india.transport import MILITARY_FACILITY, is_civil_airport
from .advisor_statistics import civic_office_points, civic_offices_in_footprint
from ..core.source import osm_notice
from .city_conditions import city_conditions, load_air

CAPITALS = {
    "BR": "Patna", "CH": "Chandigarh", "CG": "Raipur", "DL": "Delhi", "JH": "Ranchi",
    "JK": "Srinagar", "KA": "Bengaluru", "KL": "Thiruvananthapuram", "MH": "Mumbai", "MN": "Imphal",
    "MP": "Bhopal", "OD": "Bhubaneswar", "PY": "Puducherry", "RJ": "Jaipur", "TN": "Chennai",
    "TS": "Hyderabad", "TR": "Agartala", "UK": "Dehradun", "UP": "Lucknow", "WB": "Kolkata",
}
BADGE_PERIOD = "November 2026"
BADGE_SOURCES = {
    "campus": {"research_points"}, "harbor": {"cwprs_port_locations", "featured_port_locations"},
    "aerodrome": {"ourairports"}, "government_plaza": {"soi_political_map"},
}


def district_badges(profile, rings, district_shapes, points):
    if not rings:
        return []
    footprint = Shape(rings)
    members = [row["id"] for row in profile["districts"]]
    badges = {}
    for kind, name, source, x, y in points:
        if not footprint.contains(x, y) or MILITARY_FACILITY.search(name):
            continue
        district = next((member for member in members if district_shapes[member].contains(x, y)), None)
        if district:
            badges.setdefault((district, kind), {"district": district, "kind": kind, "name": name,
                                                "source": source, "period": BADGE_PERIOD, "estimated": False})
    return sorted(badges.values(), key=lambda badge: (badge["district"], badge["kind"]))

REQUIRES = ["cities.json", "world.json", "infrastructure.json", "resources.json", "lenses.json", "datameet"]
PRODUCES = ["city_view.json"]
RUN_LAST = True
CONFIG = Path(__file__).resolve().parents[1] / "india" / "config"


def cohort():
    return json.loads((CONFIG / "city_view_cohort.json").read_text())


def grid_fingerprint(world):
    grid = world["grid"]
    projection = world["projection"]
    arrays = json.dumps([world["owner"], world["water"]], separators=(",", ":")).encode()
    return {
        "radius": grid["radius"], "cols": grid["cols"], "rows": grid["rows"],
        "origin": [projection["margin"] - projection["min_x"], projection["max_y"] + projection["margin"]],
        "owner_water_sha256": sha256(arrays).hexdigest(),
    }


def apportion(total, weights):
    """Round each quota down, then award remaining people by remainder and cell ID."""
    exact = {cell: Fraction(str(weight)) for cell, weight in weights.items()}
    denominator = sum(exact.values())
    quotas = {cell: total * weight / denominator for cell, weight in exact.items()}
    result = {cell: int(quota) for cell, quota in quotas.items()}
    remaining = total - sum(result.values())
    for cell in sorted(quotas, key=lambda i: (result[i] - quotas[i], i))[:remaining]:
        result[cell] += 1
    return result


def name_key(name):
    return "".join(ch for ch in normalize("NFKD", name.casefold()) if ch.isascii() and ch.isalnum())


def select_centres(name, state, candidates, rule):
    """Require point containment, a reviewed name, and overlap with the assigned state."""
    names = {name_key(n) for n in [name, *rule.get("aliases", [])]}
    matches = [c["id"] for c in candidates
               if c["contains"] and state in c["states"] and name_key(c["name"]) in names]
    return sorted(set(matches + rule.get("additional_centres", []))) if matches else []


def point_profile(city):
    return {
        "method": "point",
        "cells": [{"cell": city["cell"], "population": city["population"],
                   "hex_fraction": None, "footprint_share": None}],
        "districts": [], "wonders": [], "resources": [],
    }


def footprint_extent(profile, grid):
    fractions = [row["hex_fraction"] for row in profile["cells"] if row["hex_fraction"] is not None]
    if not fractions:
        return None
    return {"km2": round(sum(fractions) * 1.5 * SQRT3 * grid.radius ** 2, 2),
            "hexes": len(fractions), "source": GHSL_UCDB, "period": "2026 snapshot", "estimated": True}


def footprint_resources(rings, resources, excluded):
    if not rings:
        return []
    shape = Shape(rings)
    return [[item["type"], item["name"], item["x"], item["y"]] for item in resources
            if item["name"] not in excluded and "site_x" in item and "site_y" in item
            and shape.contains(item["site_x"], item["site_y"])]


def build():
    from .city_economy import city_finances, gateway_records
    from .city_people import age_profile
    from .yields import district_state_map

    cities = {c["id"]: c for c in json.loads((WEB_DATA / "cities.json").read_text())}
    world = json.loads((WEB_DATA / "world.json").read_text())
    project = MapProjection(**world["projection"])
    civic_offices = civic_office_points(project)
    grid = HexGrid(**world["grid"])
    try:
        transport = json.loads((WEB_DATA / "infrastructure.json").read_text()) or {}
    except FileNotFoundError:
        transport = {}
    paths = transport.get("rail_corridors", {})
    resources = json.loads((WEB_DATA / "resources.json").read_text())["items"]
    disasters = json.loads((WEB_DATA / "lenses.json").read_text())["disasters"]
    matches = json.loads((CONFIG / "city_view_matches.json").read_text())
    finances = city_finances({city_id: cities[city_id] for city_id in cohort()})
    state_names = {state["abbr"]: state["name"] for state in world["states"]}
    aqi, pm25 = load_air(world)
    try:
        prepared = load_interim(GHSL_UCDB)
    except FileNotFoundError:
        prepared = {}
    fingerprint = prepared.get("grid_fingerprint")
    if prepared and fingerprint != grid_fingerprint(world):
        raise ValueError("Stale City View geometry. Re-run pipeline.india.city_view (see README).")
    source_profiles = prepared.get("profiles", {})
    datameet = load_interim("datameet")
    member_ids = {district["id"] for profile in source_profiles.values() for district in profile["districts"]}
    district_shapes = {
        key: Shape([[project(*point) for point in ring] for ring in district["rings"]])
        for district in datameet["districts"]
        if (key := f"{district['state_code']:02d}-{district['code']:03d}") in member_ids
    }
    badge_points = [
        ("campus", point["name"], "research_points", *project(point["lon"], point["lat"]))
        for point in research_points(datameet, district_state_map(datameet))
        if point["kind"] in {"IIT", "IISc", "IISER", "NIT", "AIIMS"}
    ]
    badge_points.extend(("harbor", p["name"], p["geometry_source_id"], p["x"], p["y"])
                        for p in transport.get("ports", []) if p["category"] == "Major port" or p.get("featured"))
    badge_points.extend(("aerodrome", p["name"], "ourairports", p["x"], p["y"])
                        for p in transport.get("airports", []) if is_civil_airport(p))
    badge_points.extend(("government_plaza", city["name"], "soi_political_map", city["x"], city["y"])
                        for city in cities.values() if CAPITALS.get(city["states"][0]) == city["name"])
    profiles = {}
    for city_id in cohort():
        city = cities[city_id]
        profile = source_profiles.get(city_id) or point_profile(city)
        rings = profile.pop("yield_rings", None)  # The clipped geometry stays local.
        profile["civic_offices"] = civic_offices_in_footprint(civic_offices, rings)
        profile["district_badges"] = district_badges(profile, rings, district_shapes, badge_points)
        profile["resources"] = footprint_resources(rings, resources, set(matches.get(city_id, {}).get("excluded_resources", [])))
        ages = {int(age): mass for age, mass in profile.pop("age_mass", {}).items()}
        age = age_profile(city["population"], ages, profile.pop("age_source", AGE_SOURCE))
        state = city["states"][0]
        profile["citizens"] = {"age": age, "workforce": city.get("resident_workforce")}
        profile["industry_plaques"] = city.get("industry_plaques", [])
        profile["economy"] = finances[city_id]
        profile["gateways"] = gateway_records(city, profile, transport, paths, grid)
        profile.update(city_conditions(city, profile, state_names[state], aqi, pm25, disasters["events"]))
        if profile["method"] != "point":
            weights = {row["cell"]: row["mass"] for row in profile["cells"]}
            counts = apportion(city["population"], weights)
            profile["cells"] = [
                {k: v for k, v in row.items() if k != "mass"} | {"population": counts[row["cell"]]}
                for row in profile["cells"]
            ]
            profile |= {"estimated": True, "period": "mid-2026", "source": CITY_POPULATION_GRID}
        profiles[city_id] = profile
    write_web("city_view.json", {"grid_fingerprint": fingerprint, "profiles": profiles,
                                "osm_license": osm_notice("Civic office names, rail proximity and some campus "
                                                          "badge matches derived from OpenStreetMap")})


def check(web_dir):
    cities = {c["id"]: c for c in json.loads((web_dir / "cities.json").read_text())}
    path = web_dir / "city_view.json"
    enabled = {city_id for city_id, city in cities.items() if city.get("city_view") is True}
    if not enabled and not path.exists():
        return [("NOTE", "City View profiles are absent from this build")]
    data = json.loads(path.read_text())
    profiles = data["profiles"]
    world = json.loads((web_dir / "world.json").read_text())
    spatial = sum(profile["method"] == "ghsl" for profile in profiles.values())
    fingerprint = data.get("grid_fingerprint")
    if (spatial or fingerprint is not None) and fingerprint != grid_fingerprint(world):
        return [("FAIL", "stale City View geometry: re-run pipeline.india.city_view (see README)")]
    district_ids = {district["geoid"] for district in world["counties"]}
    if not set(profiles) == set(cohort()) == enabled or len(profiles) != 50:
        return [("FAIL", "profile and city entry-point IDs must match the 50 frozen UN IDs")]
    failures = []
    age_coverage = labour_coverage = plaque_coverage = 0
    for city_id, profile in profiles.items():
        cells = profile["cells"]
        valid = (len({row["cell"] for row in cells}) == len(cells)
                 and all(0 <= row["cell"] < len(world["owner"])
                         and type(row["population"]) is int and row["population"] >= 0 for row in cells)
                 and sum(row["population"] for row in cells) == cities[city_id]["population"])
        if profile["method"] == "point":
            valid &= {k: profile[k] for k in point_profile(cities[city_id])} == point_profile(cities[city_id])
        elif profile["method"] == "ghsl":
            valid &= abs(sum(row["footprint_share"] for row in cells) - 1) < 1e-6
            valid &= all(0 < row["hex_fraction"] <= 1 and 0 < row["footprint_share"] <= 1 for row in cells)
            valid &= all(row["id"] in district_ids and 0 < row["footprint_share"] <= 1
                         and (row["population_share"] is None or 0 <= row["population_share"] <= 1)
                         for row in profile["districts"])
        else:
            valid = False
        citizens = profile.get("citizens", {})
        age, labour = citizens.get("age"), citizens.get("workforce")
        if age:
            age_coverage += 1
            valid &= profile["method"] == "ghsl" and sum(age["counts"].values()) == cities[city_id]["population"]
            if "midlife" in age.get("bands", {}):
                valid &= 0 <= age["bands"]["midlife"] <= cities[city_id]["population"]
        if labour:
            labour_coverage += 1
            valid &= sum(row["icons"] for row in labour["industries"]) == 20
            benchmark = labour.get("national_urban_unemployment_15_plus")
            if benchmark is not None:
                valid &= isinstance(benchmark, (int, float)) and 0 <= benchmark <= 1
            if age:
                valid &= labour["population_15_plus"] == cities[city_id]["population"] - age["counts"]["0_14"]
                valid &= sum(row["employed"] for row in labour["industries"]) == labour["employed_15_plus"]
            else:
                valid &= labour["employed_15_plus"] is None
        plaques = profile.get("industry_plaques", [])
        plaque_coverage += bool(plaques)
        members = {row["id"] for row in profile["districts"]}
        valid &= len(plaques) <= 5 and all(plaque["district"] in members for plaque in plaques)
        badges = profile.get("district_badges", [])
        valid &= len({(row["district"], row["kind"]) for row in badges}) == len(badges)
        valid &= all(row["district"] in members and row["source"] in BADGE_SOURCES.get(row["kind"], ())
                     and row["period"] == BADGE_PERIOD and not MILITARY_FACILITY.search(row["name"])
                     for row in badges)
        if output := profile["economy"].get("sector_output"):
            values = output["values"]
            valid &= sum(values[key] for key in ("agriculture", "industry", "services")) == profile["economy"]["gdp"]
            valid &= all(value >= 0 for value in values.values())
            valid &= sum(values.get(key, 0) for key in ("mining", "manufacturing", "construction", "utilities")
                         ) <= values["industry"] + 2  # Independent detail rounding in INR.
        if not valid:
            failures.append(("FAIL", f"{cities[city_id]['name']} ({city_id}): invalid geometry, citizens or plaques"))
    if failures:
        return failures
    return [("PASS", f"50 frozen profiles ({spatial} GHSL, {50 - spatial} point), conserved population and valid spatial shares"),
            ("PASS", f"City View coverage: {age_coverage} age, {labour_coverage} workforce, {plaque_coverage} industry plaques")]
