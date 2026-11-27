"""Build the air, hazard and housing fields of each City View profile."""

from fractions import Fraction
from math import fsum

from ..core.geo import MapProjection
from ..core.store import load_interim
from ..india.air_weather import AIR_PERIOD, DAYS, MIN_DAYS
from ..india.city_conditions_sources import EVENTS, HPI_PERIOD, HPI_SOURCE, HPI_TABLE_URL, MARKETS
from ..india.disaster_sources import COVERAGE, PERIOD as HAZARD_PERIOD
from .air_weather import AQI_ALIASES, AQI_STATE_OVERRIDES, district_pm25
from .disasters import event_summary

HPI_ALIASES = {"Bengaluru": "Bangalore"}


def air_rankings(observations):
    eligible = {
        (row["city"].casefold(), row["state"].casefold()): row
        for row in observations if MIN_DAYS <= row["days"] <= DAYS
    }
    shares = {key: Fraction(row["poor"], row["days"]) for key, row in eligible.items()}
    ranks = {}
    for rank, share in enumerate(sorted(shares.values(), reverse=True), 1):
        ranks.setdefault(share, rank)
    return {
        key: {
            "bad_days": row["poor"], "valid_days": row["days"], "calendar_days": DAYS,
            "rank": ranks[shares[key]],
            "covered_cities": len(shares), "period": AIR_PERIOD, "source": "cpcb_city_aqi",
        }
        for key, row in eligible.items()
    }


def footprint_pm25(districts, estimates):
    covered = [(estimates[row["id"]], row["footprint_share"])
               for row in districts if estimates.get(row["id"]) is not None]
    coverage = fsum(share for _, share in covered)
    if not coverage:
        return None
    return {
        "value": round(fsum(value * share for value, share in covered) / coverage, 1),
        "footprint_coverage": min(1, coverage), "period": AIR_PERIOD,
        "source": "cpcb_station_pm25", "estimated": True,
    }


def member_events(member_ids, events):
    joined = []
    for event in events:
        matched = sorted(member_ids.intersection(event["districts"]))
        if matched:
            row = {**event, "districts": matched}
            if row.get("impact") and row["impact"]["district"] not in matched:
                del row["impact"]
            joined.append(row)
    return joined


def housing_market(city_name, markets):
    label = HPI_ALIASES.get(city_name, city_name)
    if label not in markets:
        return None
    row = markets[label]
    return {
        "market": label, "index": row.get("index"), "yoy_pct": row.get("yoy_pct"),
        "period": HPI_PERIOD, "provisional": True,
        "source": HPI_SOURCE, "url": HPI_TABLE_URL,
    }


def load_air(world):
    try:
        observations = load_interim("cpcb_city_aqi")
    except FileNotFoundError:
        observations = {"cities": []}
    aqi = air_rankings(observations["cities"])
    for row in observations.get("monthly", []):
        aqi.setdefault((row["city"].casefold(), row["state"].casefold()), {
            "bad_days": row["poor"], "valid_days": row["days"], "calendar_days": row["calendar_days"],
            "period": row["period"], "source": "cpcb_city_aqi", "vintage": row["vintage"],
        })
    try:
        station_rows = load_interim("cpcb_station_pm25")["stations"]
    except FileNotFoundError:
        return aqi, {}
    projection = MapProjection(**world["projection"])
    stations = [(*projection(row["lon"], row["lat"]), row["mean"]) for row in station_rows.values()]
    districts = load_interim("datameet")["districts"]
    values = district_pm25(districts, projection, stations)
    return aqi, {
        f"{row['state_code']:02d}-{row['code']:03d}": value
        for row, value in zip(districts, values)
    }


def explorer_condition_columns(profile):
    from .city_view_contract import metadata

    columns = {}
    if events := profile.get("hazards"):
        ordered = sorted(events, key=lambda row: row["start_date"] or row["reported_on"], reverse=True)
        captions = []
        for event in ordered:
            date = event["start_date"] or "reported " + event["reported_on"]
            captions.append(f'{event["type"]} ({date})')
        columns["city_hazard_events"] = {
            "label": "Documented hazard events by type and date", "unit": "event or report date",
            "group": "Hazards", "format": "text", "period": HAZARD_PERIOD, "description": COVERAGE,
            "source": list(dict.fromkeys(event["source"] for event in ordered)),
            "value": " · ".join(captions),
        }
    for key, label, unit, fmt, series, metric, estimated, description in (
        ("city_bad_air_days", "Bad-air days", "days with AQI ≥201", "int", "aqi", "bad_days", False, ""),
        ("city_air_valid_days", "Valid AQI days", "reported days", "int", "aqi", "valid_days", False, ""),
        ("city_air_coverage_days", "AQI reporting window", "calendar days", "int", "aqi", "calendar_days", False, ""),
        ("city_air_rank", "Bad-air rank", "national rank among eligible series", "int", "aqi", "rank", False,
         "Highest share of bad-air days ranks first. Equal shares tie."),
        ("city_air_rank_cities", "Cities in AQI ranking", "eligible city series", "int", "aqi", "covered_cities", False, ""),
        ("city_footprint_pm25", "Urban footprint PM₂.₅", "µg/m³", "decimal1", "pm25", "value", True,
         "Area-weighted mean over footprint districts with PM₂.₅ estimates."),
        ("city_footprint_pm25_coverage", "Footprint PM₂.₅ coverage", "share of footprint area", "pct",
         "pm25", "footprint_coverage", True, ""),
    ):
        record = (profile.get("air") or {}).get(series)
        if record:
            columns[key] = {**metadata(record), "label": label, "unit": unit, "format": fmt,
                            "group": "Air & weather", "value": record.get(metric), "description": description,
                            "estimated": record.get("estimated", estimated)}
    if housing := profile.get("housing"):
        common = {**metadata(housing), "group": "Housing", "description": "RBI registration-market index (base = 100).",
                  "status": "Provisional" if housing.get("provisional") else housing.get("status")}
        for key, label, unit, fmt, item, divisor in (
            ("market", "RBI housing market", "registration market", "text", "market", None),
            ("index", "House Price Index", "index points", "decimal2", "index", 1),
            ("yoy", "Annual house price change", "% change from a year earlier", "signed", "yoy_pct", 100),
        ):
            value = housing.get(item)
            if divisor is not None and value is not None:
                value = float(value) / divisor
            columns[f"city_housing_{key}"] = {**common, "label": label, "format": fmt, "unit": unit, "value": value}
    return columns


def city_conditions(city, profile, state_name, aqi, pm25, inventory=EVENTS):
    name = city["name"]
    key = (AQI_ALIASES.get(name, name).casefold(), AQI_STATE_OVERRIDES.get(name, state_name).casefold())
    districts = profile["districts"]
    events = member_events({row["id"] for row in districts}, inventory)
    return {
        "air": {"aqi": aqi.get(key), "pm25": footprint_pm25(districts, pm25)},
        "hazards": events,
        "hazard_summary": event_summary(events),
        "housing": housing_market(name, MARKETS),
    }
