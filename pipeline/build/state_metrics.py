"""Join compatible state statistics to the map and retain national benchmarks."""

from ..core.store import load_interim, save_interim
from ..india.civic_sources import (
    ABHA, ABHA_PER_100, PMAYG, PMAYG_PER_1000, PMAYU2, PMAYU2_PER_1000, PMJAY_PER_100, PMJAY_STATES,
)
from ..india.explorer_sources import INTERNET_PER_100, INTERNET_SOURCE
from ..india.household_cost_sources import HCES, INTERIM as HOUSEHOLD_COSTS, NFHS, PERIODS, POVERTY, RENT, TELECOM
from .projection import state_population, units

INPUTS = [
    "tg_projections", "plfs_q3", "jjm_july", "tg_urban", "gsdp_fy26", "gsdp_components",
    "gdp_fy26", "cea_fy26", "public_works_wage", "public_works_wage_india", HOUSEHOLD_COSTS,
]
REQUIRES = ["_world", *INPUTS]
PRODUCES = ["_state_metrics"]

FY = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
QUARTER = "1 Jul – 30 Sep 2026"
GENERAL_NOTE = "Each state or union territory has one value. Grey indicates unavailable data."
GSDP_NOTE = ("IndiaCiv estimate: carry the latest available nominal state output forward at India's official 8.9% "
             "annual nominal GDP growth, then divide by the projected 1 Mar 2026 population.")
POWER_NOTE = ("CEA reports Damodar Valley Corporation separately. Its supply is included in the India total. "
              "The Jammu & Kashmir reporting area includes Ladakh. Ladakh has no separate reported figure.")
WORK_NOTE = "Current Weekly Status, age 15 and over. PLFS publishes figures for selected states and UTs."
GROUPS = {"labour": "People & Work", "daily_life": "Daily Life", "prosperity": "Prosperity",
          "energy": "Energy", "schemes": "Public schemes"}
RAMP = ["#27304f", "#2a6374", "#529a83", "#b0c882", "#f3e6a6"]
HEAT = ["#f5e7bc", "#e9b176", "#cf795e", "#a24854", "#591f45"]

# id, label, interpretation, denominator
WORK = [
    ("unemployment", "Unemployment", "bad", "Share of the labour force reporting unemployment."),
    ("lfpr", "Labour force participation", "neutral", "Share of residents in the labour force."),
    ("female_lfpr", "Women's labour force participation", "neutral", "Share of women in the labour force."),
    ("wpr", "Worker-population ratio", "neutral", "Share of residents who are employed."),
    ("agri_worker_share", "Workers in agriculture", "neutral", "Share of workers employed in agriculture."),
]
ALIASES = {
    "Jammu and Kashmir": "Jammu & Kashmir",
    "A & N Islands": "Andaman & Nicobar",
    "Andaman & Nicobar Islands": "Andaman & Nicobar",
    "D&NH and D&D": "Dadra and Nagar Haveli and Daman and Diu",
    "DDDNH": "Dadra and Nagar Haveli and Daman and Diu",
    "all-India": "India", "All India": "India", "Total": "India",
}
URBAN_NAMES = {"CHANDIGARH *": "CHANDIGARH", "UTTARANCHAL": "UTTARAKHAND", "DAMAN DIU": "DAMAN & DIU"}
POPULATION_NOTE = "IndiaCiv estimate using the projected 1 March 2026 resident population."


def civic_metrics(code):
    snapshots = (
        ("internet_per_100", INTERNET_SOURCE, INTERNET_PER_100),
        ("abha_ids", ABHA, ABHA_PER_100),
        ("pmjay_cards", PMJAY_STATES, PMJAY_PER_100),
        ("pmayg_completions", PMAYG, PMAYG_PER_1000),
        ("pmayu2_completions", PMAYU2, PMAYU2_PER_1000),
    )
    return {key: {"value": rates[code], "source": source, "estimated": True}
            for key, source, rates in snapshots if code in rates}


def estimate_gsdp(crore, base_year, annual_growth):
    return crore * (1 + annual_growth) ** (2025 - base_year)


def advisor_columns(records, definitions):
    groups = {"labour": "Work", "prosperity": "Prosperity", "daily_life": "Daily life",
              "energy": "Energy", "schemes": "Public schemes"}
    columns = {}
    for key, record in records.items():
        spec = definitions.get(key)
        if key == "internet_per_100" or not spec or not spec.get("period") or not spec.get("source"):
            continue
        unit, group = spec["unit"], spec["group"]
        format = ("inr" if "₹" in unit or "INR" in unit else
                  f"decimal{spec['precision']}" if group == "schemes" else spec["format"])
        source = record.get("source", spec["source"])
        if denominator := spec.get("denominator_source"):
            source = [source, denominator]
        columns[key] = {
            **record, "label": spec["name"], "group": groups.get(group, "State metrics"),
            "format": format, "unit": unit, "source": source, "lens": key,
            "period": record.get("period") or spec["period"], "vintage": record.get("vintage", spec.get("vintage")),
            "heading_caption": spec["period"], "period_scope": spec.get("period_scope"),
            "hide_rank": spec.get("vintage") == "older", "description": spec.get("description", ""),
        }
    return columns


def definitions():
    out = {}

    def add(key, name, group, source, publisher, period, start, end, unit, description, note="", higher="neutral"):
        out[key] = {
            "id": key, "name": name, "group": group, "icon": "l-people", "emoji": "",
            "unit": unit, "precision": 1 if group == "labour" else 2, "format": "pct" if unit == "%" else "int", "scale": "linear",
            "ramp": HEAT if higher == "bad" else RAMP, "higher_is": higher, "source": source,
            "source_line": f"{publisher} · {period}", "period": period,
            **({"period_start": start, "period_end": end} if start and end else {"vintage": "older"}),
            "description": description,
            "note": " ".join(x for x in (GENERAL_NOTE, note) if x),
        }

    for sector in ("rural", "urban"):
        add(f"mpce_index_{sector}", f"Monthly consumption per person ({sector}, index, India = 100)", "prosperity", HCES,
            "MoSPI", PERIODS[HCES], None, None, "index (India = 100)",
            f"Mean monthly per-person household consumption in {sector} areas, indexed to the corresponding India mean.")
    add("fixed_wifi_households", "Households using fixed/Wi-Fi internet at home", "daily_life", TELECOM,
        "MoSPI", PERIODS[TELECOM], None, None, "%",
        "Share of all households using fixed/Wi-Fi service at home.")
    for sector, label in (("rural", "rural"), ("urban", "urban"), ("all", "rural and urban")):
        add(f"rent_index_{sector}", f"Rental cost ({label}, index, India = 100)", "prosperity", RENT,
            "MoSPI", PERIODS[RENT], None, None, "index (India = 100)",
            f"Mean monthly rent among renter households ({label}), indexed to the corresponding India mean.")
    add("no_household_health_financing", "Households with no member covered by health financing", "daily_life",
        NFHS, "MoHFW and IIPS", PERIODS[NFHS], None, None, "%",
        "Share of households without a usual member covered by a health insurance or financing scheme.")
    out["no_household_health_financing"].update(source_line="MoHFW and IIPS", period_scope="per_state")
    for sector in ("rural", "urban"):
        add(f"rangarajan_poverty_{sector}",
            f"Poverty headcount index ({sector}, Rangarajan method, HCES 2022–23), median of 18 reporting states = 100",
            "prosperity", POVERTY, "RBI Bulletin authors", PERIODS[POVERTY], None, None,
            "index (reporting median = 100)",
            f"Share below the Rangarajan poverty line, divided by the median for {sector} areas "
            "in the 18 boundary-compatible reporting states.")
    for key, name, higher, description in WORK:
        for suffix, sector in (("", "Rural and urban"), ("_rural", "Rural"), ("_urban", "Urban")):
            label = name if not suffix else f"{name} ({sector.lower()})"
            add(key + suffix, label, "labour", "plfs_q3", "MoSPI / PLFS", QUARTER, "2026-07-01", "2026-09-30",
                "%", f"{sector}. {description}", WORK_NOTE, higher)
    add("rural_tap_water", "Rural homes with tap water", "daily_life", "jjm_july", "Jal Jeevan Mission",
        "18 Jul 2026", "2026-07-18", "2026-07-18", "%", "Rural households with a reported household tap connection.",
        "Coverage describes connections. Water quality and continuity are assessed separately.", "good")
    add("urban_share", "Urban population share", "daily_life", "tg_urban", "MoHFW projection",
        "1 Mar 2026", "2026-03-01", "2026-03-01", "%", "Projected share of residents living in urban areas.")
    add("gsdp_pc", "GSDP per person", "prosperity", "gsdp_fy26", "MoSPI, Delhi Economic Survey and IndiaCiv",
        FY, "2025-04-01", "2026-03-31", "₹ / person", "Nominal gross state domestic product per projected resident.",
        GSDP_NOTE, "good")
    add("electricity_pc", "Electricity supplied per person", "energy", "cea_fy26", "Central Electricity Authority",
        FY, "2025-04-01", "2026-03-31", "kWh / person", "Electricity available to the reported system per projected resident.",
        POWER_NOTE)
    add("public_works_daily_wage", "Rural jobs guarantee wage", "prosperity", "public_works_wage",
        "Ministry of Rural Development", "Effective 1 Jul 2026", "2026-07-01", "2026-07-01", "₹ / day",
        "Centrally notified daily wage for unskilled work under the rural jobs guarantee.",
        "States and UTs with multiple local rates are blank. The India comparison is the ministry’s published average.")
    out["public_works_daily_wage"]["format"] = "float"
    civic = [
        ("internet_per_100", "Internet subscriptions per 100 residents", "daily_life", INTERNET_SOURCE,
         "TRAI", "30 June 2026", "2026-06-30", "subscriptions per 100 residents", "l-broadband",
         "All access types. Multiple subscriptions per resident can push the rate above 100."),
        ("pmayg_completions", "PMAY-Gramin houses completed", "schemes", PMAYG,
         "Ministry of Rural Development", "16 July 2026", "2026-07-16", "houses per 1,000 residents",
         "l-home", "Cumulative completed rural scheme houses divided by total residents."),
        ("pmayu2_completions", "PMAY-Urban 2.0 houses completed or delivered", "schemes", PMAYU2,
         "Ministry of Housing and Urban Affairs", "3 August 2026", "2026-08-03",
         "houses per 1,000 residents", "l-home", "Cumulative phase 2.0 completions or deliveries reported to Parliament."),
        ("abha_ids", "ABHA IDs created", "schemes", ABHA, "National Health Authority",
         "26 November 2026", "2026-11-26", "IDs per 100 residents", "l-amenities",
         "Cumulative digital health IDs. State and UT rates use accounts assigned to those geographies."),
        ("pmjay_cards", "PM-JAY cards issued", "schemes", PMJAY_STATES, "Scheme Kosh / National Health Authority",
         "16 October 2026", "2026-10-16", "cards per 100 residents", "l-uninsured",
         "Cumulative cards in the 15 states with the highest card totals. Includes integrated state schemes."),
    ]
    for key, name, group, source, publisher, period, date, unit, icon, description in civic:
        add(key, name, group, source, publisher, period, date, date, unit, description, POPULATION_NOTE)
        out[key].update(format="float", precision=3 if key.endswith("_completions") else 1,
                        icon=icon, denominator_source="tg_projections", denominator_period="1 March 2026")
    return out


def urban_share(source, name, population):
    report_units = [u.upper() for u in units(name)]
    keys = [URBAN_NAMES.get(u, u) for u in report_units]
    if len(keys) == 1:
        return round(source["share"][keys[0]] / 100, 6)
    return round(sum(source["counts"][k] for k in keys) * 1000 / population, 6)


def build():
    try:
        inputs = {source: load_interim(source) for source in INPUTS}
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{exc}. Run the state people and economy preparation in README.md.") from exc
    world = load_interim("_world")
    tg = inputs["tg_projections"]
    state_ids = dict(zip(world["state_names"], world["states"]))
    state_ids["India"] = "IN"
    rows = {key: {} for key in state_ids.values()}
    meta = definitions()

    def put(name, key, value, source=None, **details):
        if value is None:
            return
        records = rows[state_ids[ALIASES.get(name, name)]]
        if key in records:
            raise ValueError(f"Duplicate state metric {key} for {name}")
        records[key] = {"value": value, "source": source or meta[key]["source"], **details}

    for key, table in inputs.get("plfs_q3", {}).items():
        for name, values in table.items():
            for suffix, value in zip(("_rural", "_urban", ""), values):
                put(name, key + suffix, value)
    for name, value in inputs.get("jjm_july", {}).items():
        put(name, "rural_tap_water", value)

    for source in ("public_works_wage", "public_works_wage_india"):
        for name, value in inputs.get(source, {}).items():
            put(name, "public_works_daily_wage", value, source)

    for key, values in inputs[HOUSEHOLD_COSTS].items():
        definition = meta[key]
        for name, record in values.items():
            value, period = (record["value"], record["period"]) if key == "no_household_health_financing" else (
                record, definition["period"])
            put(name, key, value / 100 if definition["format"] == "pct" else value,
                period=period, vintage="older")

    population = {name: state_population(tg, name) for name in world["state_names"]}
    population["India"] = 1000 * tg["population"]["INDIA"]["2026"][0]
    for code, records in rows.items():
        records.update(civic_metrics(code))
    if urban := inputs.get("tg_urban"):
        for name, pop in population.items():
            put(name, "urban_share", urban_share(urban, name, pop))
    for name, value in inputs.get("cea_fy26", {}).items():
        pop = population[ALIASES.get(name, name)]
        if name == "Jammu & Kashmir":
            put(name, "electricity_pc", round(value * 1_000_000 / (pop + population["Ladakh"])),
                coverage="Jammu & Kashmir and Ladakh reporting area")
        else:
            put(name, "electricity_pc", round(value * 1_000_000 / pop))
    if (gdp := inputs.get("gdp_fy26")) and (gsdp := inputs.get("gsdp_fy26")):
        supplement = inputs.get("gsdp_components", {})
        totals = {**supplement, **gsdp}
        for name, (year, value) in totals.items():
            canonical = ALIASES.get(name, name)
            source = ("delhi_gsdp_fy26" if name == "Delhi" else
                      "gsdp_fy26" if name in gsdp else "gsdp_components")
            value = estimate_gsdp(value, year, gdp["growth"])
            nominal = {} if source == "delhi_gsdp_fy26" else {"nominal_inr": round(value * 10_000_000)}
            put(canonical, "gsdp_pc", round(value * 10_000_000 / population[canonical]), source,
                estimated=year < 2025, base_fy_start=year, **nominal)
        national_inr = round(gdp["crore"] * 10_000_000)
        put("India", "gsdp_pc", round(national_inr / population["India"]), "gdp_fy26", nominal_inr=national_inr)
    save_interim("_state_metrics", {"definitions": meta, "geographies": rows})
