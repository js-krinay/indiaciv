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
from ..india import CITY_POPULATION_GRID, GHSL_UCDB, IFI_SOURCE
from ..india.census_work_sources import CULTIVATION_INTERIM, INTERIM as CENSUS_WORK
from ..india.city_sources import AGE_SOURCE, GOVERNMENT_SITES, GOVERNMENT_SITE_SOURCE
from ..india.science_sources import research_points
from ..india.transport import MILITARY_FACILITY, is_civil_airport
from .advisor_statistics import civic_office_columns, civic_office_points, civic_offices_in_footprint
from ..core.source import osm_notice
from .city_conditions import check_housing_output, city_conditions, explorer_condition_columns, load_air
from .districts import COMMERCIAL_INFO, LAND_USE_PERIOD, LAND_USE_SITES, site_observation

CAPITALS = {
    "BR": "Patna", "CH": "Chandigarh", "CG": "Raipur", "DL": "Delhi", "JH": "Ranchi",
    "JK": "Srinagar", "KA": "Bengaluru", "KL": "Thiruvananthapuram", "MH": "Mumbai", "MN": "Imphal",
    "MP": "Bhopal", "OD": "Bhubaneswar", "PY": "Puducherry", "RJ": "Jaipur", "TN": "Chennai",
    "TS": "Hyderabad", "TR": "Agartala", "UK": "Dehradun", "UP": "Lucknow", "WB": "Kolkata",
}
UT_CAPITALS = {"CH", "JK", "PY"}
BADGE_PERIOD = "November 2026"
BADGE_SOURCES = {
    "campus": {"research_points"}, "harbor": {"cwprs_port_locations", "featured_port_locations"},
    "aerodrome": {"ourairports"}, "government_plaza": {GOVERNMENT_SITE_SOURCE},
    "industrial_land_use": {"osm_transport"},
    "commercial_hub": {COMMERCIAL_INFO.id},
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
            site = {"district": district, "kind": kind, "name": name,
                    "source": source, "period": BADGE_PERIOD, "estimated": False}
            land_use = LAND_USE_SITES.get(name)
            if land_use and (land_use["kind"], land_use["source"]) == (kind, source):
                site.update(label=land_use["label"], short_label=land_use["short_label"], period=LAND_USE_PERIOD,
                            url=f'https://www.openstreetmap.org/way/{land_use["way"]}')
            badges.setdefault((district, kind), site)
    return sorted(badges.values(), key=lambda badge: (badge["district"], badge["kind"]))

REQUIRES = ["cities.json", "world.json", "infrastructure.json", "resources.json", "lenses.json",
            "workplace.json", "counties.json", "datameet"]
OPTIONAL_REQUIRES = [IFI_SOURCE, CULTIVATION_INTERIM, CENSUS_WORK]
PRODUCES = ["city_view.json", "citizens.json", "districts.json"]
CONFIG = Path(__file__).resolve().parents[1] / "india" / "config"


def cohort():
    """Original reviewed footprints, given priority over new automated matches."""
    return json.loads((CONFIG / "city_view_cohort.json").read_text())


def entry_points(cities):
    return {city["id"] for city in cities}


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
    return sorted(set(matches + rule.get("additional_centres", []))) if len(matches) == 1 else []


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
    from .census_civic import advisor_columns, civic_rows
    from .citizens import commute_analogues
    from .city_economy import city_finances, explorer_gateway_columns, gateway_records
    from .city_people import age_profile
    from .city_view_contract import (FIGURES, GROUPS, citizen_mix, cultivation_mix,
                                     explorer_finance_columns, explorer_profile_columns, explorer_resident_columns,
                                     explorer_work_columns, workplace_districts)
    from .yields import district_state_map

    cities = {c["id"]: c for c in json.loads((WEB_DATA / "cities.json").read_text())}
    world = json.loads((WEB_DATA / "world.json").read_text())
    district_names = {row["geoid"]: row["name"] for row in world["counties"]}
    project = MapProjection(**world["projection"])
    civic_offices = civic_office_points(project)
    grid = HexGrid(**world["grid"])
    try:
        transport = json.loads((WEB_DATA / "infrastructure.json").read_text()) or {}
    except FileNotFoundError:
        transport = {}
    paths = transport.get("rail_corridors", {})
    resources = json.loads((WEB_DATA / "resources.json").read_text())["items"]
    lenses = json.loads((WEB_DATA / "lenses.json").read_text())
    disasters = lenses["disasters"]
    matches = json.loads((CONFIG / "city_view_matches.json").read_text())
    finances = city_finances(cities, set(cohort()))
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
    try:
        historical_impacts = load_interim(IFI_SOURCE)["districts"]
    except FileNotFoundError:
        historical_impacts = {}
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
    badge_points.extend((site["kind"], name, site["source"], *project(*site["point"]))
                        for name, site in LAND_USE_SITES.items())
    profiles = {}
    citizen_records = {}
    civic = civic_rows("cities")
    try:
        historical_work = load_interim(CENSUS_WORK)
    except FileNotFoundError:
        historical_work = {}
    try:
        cultivation = load_interim(CULTIVATION_INTERIM)["districts"]
    except FileNotFoundError:
        cultivation = {}
    for city_id, city in cities.items():
        profile = source_profiles.get(city_id) or point_profile(city)
        rings = profile.pop("yield_rings", None)  # The clipped geometry stays local.
        profile["civic_offices"] = civic_offices_in_footprint(civic_offices, rings)
        profile["advisor_columns"] = civic_office_columns(profile["civic_offices"])
        profile["district_badges"] = district_badges(profile, rings, district_shapes, badge_points)
        for site in profile["district_badges"]:
            if observation := site_observation(city_id, site):
                profile["advisor_columns"]["nirf_rourkela_doctoral"] = {
                    **observation, "group": "Education", "format": "int", "scope": site["name"],
                }
        state = city["states"][0]
        if city.get("capital") or CAPITALS.get(state) == city["name"]:
            designation = "Union territory capital" if state in UT_CAPITALS else "State capital"
            profile["capital_designation"] = {
                "label": "National capital" if city.get("capital") else designation,
                "period": BADGE_PERIOD, "source": "soi_political_map",
            }
            if state in GOVERNMENT_SITES:
                name, lon, lat, item, revision = GOVERNMENT_SITES[state]
                sites = district_badges(profile, rings, district_shapes,
                                       [("government_plaza", name, GOVERNMENT_SITE_SOURCE, *project(lon, lat))])
                for site in sites:
                    site["url"] = f"https://www.wikidata.org/w/index.php?title={item}&oldid={revision}"
                profile["district_badges"].extend(sites)
        profile["resources"] = footprint_resources(rings, resources, set(matches.get(city_id, {}).get("excluded_resources", [])))
        ages = {int(age): mass for age, mass in profile.pop("age_mass", {}).items()}
        age = age_profile(city["population"], ages, profile.pop("age_source", AGE_SOURCE))
        profile["citizens"] = {"age": age, "workforce": city.get("resident_workforce")}
        profile["advisor_columns"].update(explorer_work_columns(profile["citizens"]["workforce"]))
        if city_id in civic:
            profile["citizens"]["census_civic"] = civic[city_id]
            profile["advisor_columns"].update(advisor_columns(civic[city_id], city=True))
            profile["advisor_columns"].update(commute_analogues(civic[city_id].get("commute", {})))
        if city_id in historical_work:
            work = historical_work[city_id]
            profile["citizens"]["census_work"] = {
                key: {k: v for k, v in record.items() if k != "details"} for key, record in work.items()
            }
            profile["advisor_columns"].update(explorer_resident_columns(work))
        if record := cultivation_mix([row["id"] for row in profile["districts"]], cultivation):
            profile["citizens"]["cultivation"] = record
        if mix := citizen_mix(profile["citizens"], ages, city):
            citizen_records[city_id] = mix
        profile["industry_plaques"] = city.get("industry_plaques", [])
        profile["advisor_columns"].update(explorer_profile_columns(profile, district_names))
        profile["economy"] = finances[city_id]
        profile["advisor_columns"].update(explorer_finance_columns(profile["economy"]))
        profile["gateways"] = gateway_records(city, profile, transport, paths, grid)
        profile["advisor_columns"].update(explorer_gateway_columns(profile["gateways"]))
        profile.update(city_conditions(city, profile, state_names[state], aqi, pm25, disasters["events"]))
        profile["advisor_columns"].update(explorer_condition_columns(profile))
        impacts = [event for district in profile["districts"] for event in historical_impacts.get(district["id"], [])]
        if impacts:
            profile["historical_flood_impacts"] = sorted(
                impacts, key=lambda event: (event["date"], event["id"]), reverse=True,
            )[:3]
        if profile["method"] != "point":
            weights = {row["cell"]: row["mass"] for row in profile["cells"]}
            counts = apportion(city["population"], weights)
            profile["cells"] = [
                {key: row[key] for key in ("cell", "hex_fraction", "footprint_share")}
                | {"population": counts[row["cell"]]}
                for row in profile["cells"]
            ]
            profile |= {"estimated": True, "period": "mid-2026", "vintage": "2026 estimate",
                        "source": CITY_POPULATION_GRID}
        profiles[city_id] = profile
    write_web("city_view.json", {"grid_fingerprint": fingerprint, "profiles": profiles,
                                "osm_license": osm_notice("Civic office names, rail proximity and land-use site "
                                                          "observations derived from OpenStreetMap")})
    benchmarks = [row["workforce"].pop("benchmark") for row in citizen_records.values()
                  if "benchmark" in row.get("workforce", {})]
    if benchmarks and any(row != benchmarks[0] for row in benchmarks):
        raise ValueError("City View occupation benchmarks must cover the same urban India cohort")
    national = {"workforce": {"shares": benchmarks[0]}} if benchmarks else {}
    write_web("citizens.json", {"cities": citizen_records, "figures": FIGURES, "national": national,
                               "groups": {row: [{"key": key, "label": label} for key, label in groups.items()]
                                          for row, groups in GROUPS.items()}})
    workplace = json.loads((WEB_DATA / "workplace.json").read_text())
    write_web("districts.json", workplace_districts(workplace, profiles))


def valid_census_work(records):
    """Accept only derived shares and the agreed civilian categories."""
    from ..india.census_work import INDUSTRIES, OCCUPATIONS
    from ..india.census_civic_sources import PERIOD

    expected = {"occupations": {*OCCUPATIONS, "other"}, "industries": {*INDUSTRIES, "public_admin"}}

    def valid_shares(values, families):
        return (isinstance(values, dict) and values.keys() == families
                and all(type(value) in (int, float) and 0 <= value <= 1 for value in values.values())
                and abs(sum(values.values()) - 1) <= 1e-6)

    if not isinstance(records, dict) or not records.keys() <= expected.keys():
        return False
    for series, record in records.items():
        allowed = {"values", "source", "vintage", "period", "scope"}
        if series == "occupations":
            allowed |= {"benchmark", "specialist"}
        else:
            from ..india.census_work import DETAIL_LABELS
            allowed.add("details")
        if (not isinstance(record, dict) or not record.keys() <= allowed
                or record.get("vintage") != "older" or record.get("period") != PERIOD
                or record.get("source") != f"orgi_work_{series}"
                or record.get("scope") != "urban member districts"
                or not valid_shares(record.get("values"), expected[series])):
            return False
        if series == "occupations" and not valid_shares(record.get("benchmark"), expected[series]):
            return False
        if series == "industries" and (details := record.get("details")) is not None:
            if (not isinstance(details, dict) or not details.keys() <= DETAIL_LABELS.keys()
                    or any(type(value) not in (int, float) or not 0 <= value <= 1 for value in details.values())):
                return False
        if "specialist" in record:
            specialist = record["specialist"]
            if (not isinstance(specialist, dict) or specialist.keys() != {"family", "ratio"}
                    or specialist["family"] not in OCCUPATIONS
                    or type(specialist["ratio"]) not in (int, float)
                    or not 1.5 <= specialist["ratio"] < float("inf")):
                return False
    return True


def check(web_dir):
    from ..india.annual_labour import SOURCE as ANNUAL_LABOUR_SOURCE

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
    if not set(profiles) == entry_points(cities.values()) == enabled:
        return [("FAIL", "profile and City View entry-point IDs must match the mapped UN IDs")]
    claimed = [gid for profile in profiles.values() for gid in profile.get("ghsl_ids", [])]
    if len(claimed) != len(set(claimed)):
        return [("FAIL", "City View profiles must have exclusive GHSL centre IDs")]
    failures = []
    workforce_cohort = set(cohort())
    age_coverage = labour_coverage = plaque_coverage = historical_coverage = 0
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
        if "census_work" in citizens:
            historical_coverage += 1
            if not profile["districts"] or not valid_census_work(citizens["census_work"]):
                failures.append(("FAIL", f"{city_id}: invalid or non-civilian historical workforce shares"))
        age, labour = citizens.get("age"), citizens.get("workforce")
        if age:
            age_coverage += 1
            valid &= profile["method"] == "ghsl" and sum(age["counts"].values()) == cities[city_id]["population"]
            if "midlife" in age.get("bands", {}):
                valid &= 0 <= age["bands"]["midlife"] <= cities[city_id]["population"]
        if labour:
            labour_coverage += 1
            annual = (labour.get("benchmark") or {}).get("source") == ANNUAL_LABOUR_SOURCE
            valid &= sum(row["icons"] for row in labour["industries"]) == (0 if annual else 20)
            benchmark = labour.get("national_urban_unemployment_15_plus")
            if benchmark is not None:
                valid &= isinstance(benchmark, (int, float)) and 0 <= benchmark <= 1
            if annual:
                valid &= labour.get("employed_15_plus") is None and labour.get("population_15_plus") is None
            elif age and city_id in workforce_cohort:
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
                     and row["period"] == (LAND_USE_PERIOD if row["kind"] in {"industrial_land_use", "commercial_hub"}
                                           else BADGE_PERIOD)
                     and not MILITARY_FACILITY.search(row["name"])
                     for row in badges)
        if any(row["kind"] == "government_plaza" for row in badges):
            facility = GOVERNMENT_SITES.get(cities[city_id]["states"][0])
            valid &= bool(facility and profile.get("capital_designation") and all(
                row["name"] == facility[0] and row.get("url", "").endswith(f"&oldid={facility[4]}")
                for row in badges if row["kind"] == "government_plaza"))
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
    result = check_display_contract(web_dir, profiles)
    if (web_dir / "advisor_tables.json").exists():
        result += check_housing_output(web_dir, cities, profiles)
    return result + [("PASS", f"{len(profiles)} profiles ({spatial} GHSL, {len(profiles) - spatial} point), conserved population and valid spatial shares"),
            ("PASS", f"Historical resident workforce shares: {historical_coverage} City View profiles"),
            ("PASS", f"City View coverage: {age_coverage} age, {labour_coverage} workforce, {plaque_coverage} industry plaques")]


def check_display_contract(web_dir, profiles):
    from .city_view_contract import DISTRICT_TYPES, FIGURES, SITE_DISTRICTS
    from ..india.historical_sources import WORKPLACE_PERIOD, WORKPLACE_SOURCE

    allowed = {*SITE_DISTRICTS, *(definition[0] for definition in DISTRICT_TYPES.values())}
    for name in ("citizens", "districts"):
        if not (web_dir / f"{name}.json").is_file():
            return [("FAIL", f"Missing City View runtime file: {name}.json")]
    citizen_rows = json.loads((web_dir / "citizens.json").read_text())["cities"]
    if not citizen_rows.keys() <= profiles.keys() or any(
        set(row) - {*FIGURES, "specialists"}
        or any(not record.get("source") or not record.get("period")
               or sum(record["figures"].values()) != FIGURES[key]
               or abs(sum(record["shares"].values()) - 1) > 1e-4
               for key, record in row.items() if key in FIGURES)
        for row in citizen_rows.values()
    ):
        return [("FAIL", "City View citizen mixes need a dated source and conserved civilian figure shares")]
    districts = json.loads((web_dir / "districts.json").read_text())
    district_rows = districts["cities"]
    if (not district_rows.keys() <= profiles.keys()
            or any(d["id"] not in allowed for d in districts["catalog"])
            or any(("emp" in row and (row.get("period") != WORKPLACE_PERIOD
                                      or row.get("source") != WORKPLACE_SOURCE or row.get("vintage") != "older"))
                   or any(d["id"] not in allowed
                          or (d["via"] == "specialty" and d.get("sub") not in DISTRICT_TYPES)
                          or (d["via"] == "site" and (not d.get("sites") or "sub_lq" in d or "lq" in d))
                          or any(site not in profiles[city_id]["district_badges"] or site["kind"] != d["id"]
                                 for site in d.get("sites", []))
                          for d in row["districts"])
                   or any(item.get("naics") not in DISTRICT_TYPES for item in row["top"])
                   or (row["badge"] and row["badge"].get("district") and row["badge"]["district"] not in allowed)
                   for city_id, row in district_rows.items())):
        return [("FAIL", "City View districts need civilian workplace specialties or verified sites")]
    return [("PASS", f"City View display files: {len(citizen_rows)} citizen mixes, "
                     f"{len(district_rows)} civilian district profiles")]
