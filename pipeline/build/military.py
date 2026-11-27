"""Public civic boards, headquarters cities and national strength."""

import json
from collections import defaultdict

from ..core.geo import MapProjection, Shape
from ..core.hexgrid import HexGrid
from ..core.paths import WEB_DATA
from ..core.store import load_interim, write_web
from ..india import GHSL_UCDB
from ..india.advisor_sources import (BOARDS, BOARDS_PERIOD, FY, OLDER_REGISTRATION_PERIOD, RMS_BY_STATE,
                                    RMS_PERIOD, RMS_SOURCE, VETERAN_PERIOD)
from ..india.military_sources import COMMANDS, DISTRICT_EVIDENCE, HOME_PORTS, STRENGTH, STRENGTH_SOURCE
from .city_view import grid_fingerprint, name_key

REQUIRES = ["nation.json", "world.json", "datameet", "un_wup_cities"]
TOWN_SOURCES = ("ne_places", "ghsl_town_centres", "un_wup_cities", "geonames_india")
OPTIONAL_REQUIRES = ["ne_places", "ghsl_town_centres", GHSL_UCDB, "geonames_india"]
PRODUCES = ["military.json"]

CIVIC = "Cantonment Board (civic body)"
HQ = "Command HQ"
BOARD_SOURCE = "cantonment_boards"
COMPONENTS = [{"id": "army", "name": "Army"}, {"id": HQ, "name": HQ}]
RULES = {"tier": "Town and city markers for DGDE Cantonment Boards and published Command HQs."}
CAVEATS = "National veteran registrations cover states and union territories with comparable snapshots."
VETERANS_NOTE = (f"State and UT estimates are for {VETERAN_PERIOD}. Manipur and Punjab use the "
                 f"{OLDER_REGISTRATION_PERIOD} counts. Himachal Pradesh district registrations are for "
                 "31 Mar 2026. Shares use mid-2026 population.")

# Reviewed equivalents in the civil gazetteers, scoped to the directory state.
TOWN_ALIASES = {
    ("AN", "Sri Vijaya Puram"): "Port Blair",
    ("AP", "Visakhapatnam"): "Vishakhapatnam",
    ("HP", "Shimla"): "Simla",
    ("MH", "Ahilyanagar"): "Ahmednagar",
    ("MH", "Chhatrapati Sambhajinagar"): "Aurangabad",
    ("MP", "Saugor"): "Sagar",
    ("PB", "Ferozepur"): "Firozpur",
    ("PB", "Jalandhar"): "Jullundur",
    ("UP", "Ayodhya"): "Faizabad",
    ("UP", "Prayagraj"): "Allahabad",
    ("UK", "Dehradun"): "Dehra Dun",
}

PUBLIC_INDICATORS = (
    "cantonment_boards", "legacy_sainik_schools", "sainik_schools",
    "rashtriya_military_schools", "defence_psu_turnover",
)


def town_record(name, state, town, component, tier, period, source, places, cell_at):
    options = places.get((state, name_key(town))) or places.get(
        (state, name_key(TOWN_ALIASES.get((state, town), town))), [])
    evidence = DISTRICT_EVIDENCE.get((state, town))
    if evidence:
        options = [point for point in options if point[2] == evidence[0]]
    if not options or len(options) != 1:
        return None
    x, y, district, city, gazetteer_source, place_id = options[0]
    cell = cell_at(x, y)
    if cell < 0:
        return None
    return {"id": f"{state.lower()}-{name_key(name)}", "name": name, "town": town,
            "state": state, "x": x, "y": y, "cell": cell, "county": district, "cbsa": city,
            "component": component, "tier": tier, "period": period, "source": source,
            "gazetteer": {"source": gazetteer_source, "id": place_id,
                          **({"district_source": f"civic_town_{town.lower()}"} if evidence else {})},
            **({"vintage": "older"} if "2026" not in period else {})}


def cantonment_records(boards, places, cell_at):
    return [row for state, towns in boards.items() for town in dict.fromkeys(towns)
            if (row := town_record(f"{town} Cantonment Board", state, town, "army", CIVIC,
                                   BOARDS_PERIOD, BOARD_SOURCE, places, cell_at))]


def command_records(places, cell_at):
    return [row for name, state, town, release, period in COMMANDS
            if (row := town_record(name, state, town, HQ, HQ, period, f"command_hq_{release}", places, cell_at))]


def home_port_records():
    return {port: {"ship": ship, "period": period, "source": f"ship_home_port_{release}",
                   **({"vintage": "older"} if "2026" not in period else {})}
            for port, ship, period, release, _ in HOME_PORTS}


def gazetteer(world, datameet, footprints, place_sources):
    """Index civil town points, preferring Natural Earth over UN agglomeration centres."""
    project = MapProjection(**world["projection"])
    state_codes = {row["name"]: row["abbr"] for row in world["states"]}
    states = {state_codes[row["name"]]: Shape([[project(*p) for p in ring] for ring in row["rings"]])
              for row in datameet["states"]}
    districts = {f"{row['state_code']:02d}-{row['code']:03d}":
                 Shape([[project(*p) for p in ring] for ring in row["rings"]])
                 for row in datameet["districts"] if row["code"]}
    cities = {key: Shape(profile["yield_rings"]) for key, profile in footprints.items()
              if profile.get("method") == "ghsl" and profile.get("yield_rings")}
    result = {}
    for source, places in place_sources:
        source_id = GHSL_UCDB if source == "ghsl_town_centres" else source
        matches = defaultdict(list)
        for place in places:
            x, y = project.from_projected(place["x"] / 1000, place["y"] / 1000)
            state_hits = [code for code, shape in states.items() if shape.contains(x, y)]
            if len(state_hits) != 1:
                continue
            district_hits = [code for code, shape in districts.items() if shape.contains(x, y)]
            city_hits = [key for key, shape in cities.items() if shape.contains(x, y)]
            matches[state_hits[0], name_key(place["name"])].append(
                (round(x, 3), round(y, 3),
                 district_hits[0] if len(district_hits) == 1 else None,
                 city_hits[0] if len(city_hits) == 1 else None, source_id, str(place["id"])))
        for key, values in matches.items():
            if key not in result or (len(result[key]) != 1 and len(values) == 1):
                result[key] = values
    return result


def civil_installations(world, read):
    footprints = read(GHSL_UCDB)
    if footprints and footprints["grid_fingerprint"] != grid_fingerprint(world):
        raise ValueError("Stale City View geometry. Re-run pipeline.india.city_view (see README).")
    places = gazetteer(world, read("datameet"), footprints.get("profiles", {}),
                       [(source, read(source).get("places", [])) for source in TOWN_SOURCES])
    cell_at = HexGrid(**world["grid"]).cell_at
    return cantonment_records(BOARDS, places, cell_at) + command_records(places, cell_at)


def public_statistics(statistics):
    national = {}
    periods = {}
    sources = []
    spending = statistics.get("defence_budget")
    if spending:
        national["spending"] = {"total": round(spending["total"] * 10_000_000)}
        periods["spending"] = spending["period"]
        sources.append(spending["source"])
        if share := statistics.get("defence_budget_share_gdp"):
            national["spending"]["pct_gdp"] = share["value"]
            sources.extend(share["source"])
    if veterans := statistics.get("veterans"):
        national["veterans"] = veterans["value"]
        periods["veterans"] = veterans["period"]
        sources.extend(veterans["source"])
    for key in PUBLIC_INDICATORS:
        if observation := statistics.get(key):
            national[key] = observation["value"]
            periods[key] = observation["period"]
            sources.append(observation["source"])
    return {"national": national, "vintage": periods, "sources": list(dict.fromkeys(sources))}


def build():
    nation = json.loads((WEB_DATA / "nation.json").read_text())
    statistics = {**nation["advisor_statistics"],
                  "cantonment_boards": {"value": sum(map(len, BOARDS.values())),
                                        "period": BOARDS_PERIOD, "source": "cantonment_boards"},
                  "legacy_sainik_schools": {"value": 33, "period": "7 May 2026", "source": "sainik_schools_2026"},
                  "rashtriya_military_schools": {"value": sum(RMS_BY_STATE.values()), "period": RMS_PERIOD,
                                               "source": RMS_SOURCE},
                  "defence_psu_turnover": {"value": 129_000 * 10_000_000, "period": FY,
                                           "source": "dpsu_turnover_fy26"}}
    doc = public_statistics(statistics)
    active = {key: value for key, (value, _, _, _) in STRENGTH.items()}
    doc["national"]["personnel"] = {"active": active}
    doc["personnel_provenance"] = {
        key: {"label": label, "period": period, "description": desc, "vintage": "older", "source": STRENGTH_SOURCE}
        for key, (_, label, period, desc) in STRENGTH.items()
    }
    world = json.loads((WEB_DATA / "world.json").read_text())
    doc["installations"] = civil_installations(world, optional_interim)
    doc["components"] = COMPONENTS
    doc["flagship_provenance"] = home_port_records()
    doc["flagships"] = list(doc["flagship_provenance"])
    doc["vintage"]["installations"] = "DGDE directory and dated Government of India releases"
    doc["rules"] = RULES
    doc["caveats"] = CAVEATS
    doc["veterans_note"] = VETERANS_NOTE
    doc["sources"] = list(dict.fromkeys([*doc["sources"], STRENGTH_SOURCE, "ne_places", "un_wup_cities",
                                        "datameet", GHSL_UCDB, *(row["source"] for row in doc["installations"]),
                                        *(row["gazetteer"]["source"] for row in doc["installations"]),
                                        *(row["gazetteer"]["district_source"] for row in doc["installations"]
                                          if "district_source" in row["gazetteer"]),
                                        *(row["source"] for row in doc["flagship_provenance"].values())]))
    write_web("military.json", doc)


def optional_interim(source):
    try:
        return load_interim(source)
    except FileNotFoundError:
        return {}
