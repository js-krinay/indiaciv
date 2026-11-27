"""Build the air, hazard and housing fields of each City View profile."""

from fractions import Fraction
from math import fsum

from ..core.geo import MapProjection
from ..core.store import load_interim
from ..india.air_weather import AIR_PERIOD, DAYS, MIN_DAYS
from ..india.city_conditions_sources import EVENTS, HPI_PERIOD, HPI_SOURCE, HPI_TABLE_URL, MARKETS
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
        observations = load_interim("cpcb_city_aqi")["cities"]
    except FileNotFoundError:
        observations = []
    try:
        station_rows = load_interim("cpcb_station_pm25")["stations"]
    except FileNotFoundError:
        return air_rankings(observations), {}
    projection = MapProjection(**world["projection"])
    stations = [(*projection(row["lon"], row["lat"]), row["mean"]) for row in station_rows.values()]
    districts = load_interim("datameet")["districts"]
    values = district_pm25(districts, projection, stations)
    return air_rankings(observations), {
        f"{row['state_code']:02d}-{row['code']:03d}": value
        for row, value in zip(districts, values)
    }


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
