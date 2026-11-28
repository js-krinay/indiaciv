"""Write the independently licensed historical workplace aggregates."""

import json

from ..core.paths import WEB_DATA
from ..core.store import load_interim, write_web
from ..india import DISPLAY_NAMES
from ..india.historical_sources import WORKPLACE_LICENSE as LICENSE, WORKPLACE_LICENSE_URL as LICENSE_URL
from ..india.workplace import (COLUMNS, INDUSTRIES, MIN_JOBS, MIN_LQ, MIN_SHARE, PERIOD, SOURCE,
                              combined, normalized, observation)

REQUIRES = ["cities.json", "census_a01", SOURCE]
PRODUCES = ["workplace.json"]

# Historic Census state codes. Andhra Pradesh's 2014 split moved subdistricts across
# the new state line, so the district-only source cannot reconstruct either state.
STATE_CODES = dict(enumerate(
    "JK HP PB CH UK HR DL RJ UP BR SK AR NL MN MZ TR ML AS WB JH OD CG MP GJ DH DH MH AP KA GA LD KL TN PY AN".split(),
    start=1))
CITY_STATE_CODES = {state: f"{code:02d}" for code, state in STATE_CODES.items() if state != "DH"}
CITY_STATE_CODES.update(TS="28", LA="01")
CITY_ALIASES = {"greatermumbai": "mumbai", "bruhatbangalore": "bengaluru"}


def state_for_district(code):
    state = STATE_CODES[int(code[:2])]
    if state == "JK" and code in {"01-003", "01-004"}:
        return "LA"
    return None if state == "AP" else state


def advisor_definitions(national, thresholds):
    common = {"group": "Workplace", "period": national["period"], "source": national["source_id"],
              "vintage": "older"}
    qualification = (f"Qualifies at {thresholds['jobs']} jobs, {100 * thresholds['share']:g}% local share "
                     f"and {thresholds['lq']:g}× India share. Highest location quotient wins, "
                     "with excess jobs breaking ties.")
    fields = []
    for key, label, format, unit, description in (
        ("jobs", "Workplace jobs excluding defence-mixed groups", "int", "civilian non-farm jobs", ""),
        ("top_industry", "Top workplace specialisation", "text", "civilian industry", qualification),
        ("top_lq", "Top workplace location quotient", "lq", "times the India share", qualification),
        ("manufacturing_share", "Harmonised manufacturing share", "pct", "% of civilian non-farm jobs",
         "SHRUG harmonised manufacturing jobs divided by non-farm jobs, excluding defence-mixed groups from both."),
    ):
        fields.append({**common, "key": f"workplace_{key}", "label": label, "format": format,
                       "unit": unit, "description": description, "path": [key]})
    for index, industry in enumerate(national["industries"]):
        for key, label, format, unit in (
            ("lq", "location quotient", "lq", "times the India share"),
            ("local_share", "local workplace share", "pct", "% of civilian non-farm jobs"),
            ("national_share", "India workplace share", "pct", "% of civilian non-farm jobs"),
            ("excess_jobs", "excess jobs vs India share", "int", "civilian jobs"),
        ):
            suffix = "" if key == "lq" else f"_{key}"
            fields.append({**common, "key": f"workplace_industry_{index}{suffix}", "label": f"{industry} {label}",
                           "format": format, "unit": unit, "path": ["industries", industry, key]})
    from ..india.workplace import DETAILS
    for index, label in enumerate((*DETAILS, "Civilian-filtered manufacturing")):
        fields.append({**common, "key": f"workplace_matched_share_{index}",
                       "label": f"{label} · Share of matched civilian workplace workers",
                       "format": "pct", "unit": "%", "path": ["industry_shares", label], "hide_rank": True})
    return fields


def build():
    try:
        data = load_interim(SOURCE)
    except FileNotFoundError:
        write_web("workplace.json", None)
        return
    district_inputs = data["district_inputs"]
    expected = load_interim("census_a01")["districts"]
    if district_inputs.keys() != expected.keys():
        raise ValueError("Workplace district IDs do not match Census 2011 A-01")
    national_input = combined(district_inputs.values(), len(COLUMNS))
    state_inputs = {}
    for key, measures in district_inputs.items():
        state = state_for_district(key)
        if state:
            state_inputs.setdefault(state, []).append(measures)
    states = {state: observation(combined(rows, len(COLUMNS)), national_input)
              for state, rows in state_inputs.items()}

    cohort = {}
    for key, record in data["uas"].items():
        code, name = key.split(":", 1)
        display = CITY_ALIASES.get(name, next((new for old, new in DISPLAY_NAMES.items() if normalized(old) == name), name))
        cohort.setdefault((code, normalized(display)), []).append(record)
    cities = {}
    for city in json.loads((WEB_DATA / "cities.json").read_text()):
        if len(city.get("states", [])) != 1:
            continue
        state = CITY_STATE_CODES.get(city["states"][0])
        matches = cohort.get((state, normalized(city["name"])), [])
        if len(matches) == 1:
            record = matches[0]
            cities[city["id"]] = {**record, "industry_shares": {
                label: round(share, 3 if share < .1 else 2)
                for label, share in record.get("industry_shares", {}).items()
            }}

    thresholds = {"jobs": MIN_JOBS, "share": MIN_SHARE, "lq": MIN_LQ}
    write_web("workplace.json", {
        "license": LICENSE, "license_url": LICENSE_URL,
        "attribution": "MoSPI Sixth Economic Census via Development Data Lab, SHRUG v2.2 Pakora",
        "thresholds": thresholds,
        "advisor_fields": advisor_definitions(data["national"], thresholds),
        "districts": data["districts"], "cities": cities, "states": states, "national": data["national"],
    })


def check(web_dir):
    path = web_dir / "workplace.json"
    if not path.exists() or (data := json.loads(path.read_text())) is None:
        return []
    world = json.loads((web_dir / "world.json").read_text())
    cities = json.loads((web_dir / "cities.json").read_text())
    sources = json.loads((web_dir / "sources.json").read_text())
    known = {"districts": {row["geoid"] for row in world["counties"]},
             "states": {row["abbr"] for row in world["states"]},
             "cities": {row["id"] for row in cities}}
    if (data["license"] != LICENSE or data["license_url"] != LICENSE_URL
            or not any(row["id"] == SOURCE and row["license"] == LICENSE for row in sources)):
        return [("FAIL", "Derived workplace file needs its ShareAlike licence and registered source")]
    if data["districts"].keys() != known["districts"] or any(
            not data[scope].keys() <= ids for scope, ids in known.items()):
        return [("FAIL", "Workplace geography keys do not match the map")]
    records = [data["national"], *(record for scope in known for record in data[scope].values())]
    for record in records:
        if (record["vintage"] != "older" or record["period"] != PERIOD or record["source_id"] != SOURCE
                or not record["industries"].keys() <= INDUSTRIES.keys()):
            return [("FAIL", "Workplace record has an invalid vintage, source or civilian industry")]
    return [("PASS", f'{len(data["cities"])} matched UAs, {len(data["districts"])} districts and '
                     f'{len(data["states"])} states and UTs carry the historical workplace period')]
