"""Household and land observations with their own units and denominators."""

from ..india.household_cost_sources import (DISTRICT_HEALTH, DISTRICT_MPI, DISTRICT_PERIOD, DISTRICT_TAPS,
                                           PERIODS, PILOT, TAP_PERIOD)
from .advisor_inventory import column

URBAN_UP = "Urban district consumption per person (UP urban mean = 100)"
RURAL_UP = "Rural district consumption per person (UP rural mean = 100)"
RANGELAND = "Mapped rangeland share of sampled land"


def observation(label, fmt, unit, group, record, *, description="", **details):
    return column(label, fmt, unit, group, record["period"], record["source"], record["value"],
                  **{key: record[key] for key in ("vintage", "estimated") if key in record},
                  higher_is="neutral", hide_rank=True, description=description or label, **details)


def consumption(value, *, city=False, rural=False):
    label = RURAL_UP if rural else URBAN_UP
    if city:
        label = URBAN_UP.replace("district", "member-district")
    details = {"description": "Single boundary-compatible urban member district in Uttar Pradesh."} if city else {
        "lens": "consumption_index_rural" if rural else "consumption_index",
    }
    return observation(label, "float", "index points", "Prosperity",
                       {"value": value, "period": PERIODS[PILOT], "source": PILOT, "vintage": "older"},
                       **details)


def rangeland(land):
    cover = (land or {}).get("composition", {})
    value = cover.get("shares", {}).get("11")
    if value is not None:
        return observation(RANGELAND, "pct", "%", "Land", {**cover, "value": value},
                           description="Esri rangeland pixels divided by all classified land samples. "
                                       "Water, clouds and missing pixels are excluded.",
                           coverage=f'{cover["samples"]} classified Esri land samples',
                           sparse=cover["sparse"])


def state_columns(metrics, definitions, land):
    columns = {}
    for key, label, fmt, unit, group in (
        ("internet_per_100", "Internet subscriptions per 100 residents", "decimal1",
         "subscriptions per 100 people", "Daily life"),
        ("mpce_index_urban", "Urban household consumption per person (India urban mean = 100)",
         "float", "index points", "Prosperity"),
        ("rent_index_urban", "Mean urban renter-household rent (India urban renter mean = 100)",
         "float", "index points", "Prosperity"),
        ("no_household_health_financing", "Households with no usual member covered by a health insurance or financing scheme",
         "pct", "%", "Daily life"),
    ):
        if record := metrics.get(key):
            spec = definitions[key]
            source = record.get("source", spec["source"])
            if denominator := spec.get("denominator_source"):
                source = [source, denominator]
            columns[key] = observation(
                label, fmt, unit, group, {"period": spec["period"], **record, "source": source},
                lens=key, heading_caption=spec["period"], period_scope=spec.get("period_scope"),
                description=spec["description"])
    if record := rangeland(land):
        columns["land_pasture"] = record
    return columns


def district_columns(pilot, land, mpi=None, uninsured=None, taps=None):
    columns = {}
    if pilot:
        columns["consumption_index"] = consumption(pilot["urban"])
        columns["consumption_index_rural"] = consumption(pilot["rural"], rural=True)
    if record := rangeland(land):
        columns["pasture"] = record
    for key, value, label, source, fmt, unit in (
        ("multidimensional_poverty", mpi, "Multidimensional poverty headcount index (India = 100)",
         DISTRICT_MPI, "float", "index points"),
        ("no_household_health_financing", uninsured,
         "Households with no usual member covered by a health insurance or financing scheme",
         DISTRICT_HEALTH, "pct", "%"),
    ):
        if value is not None:
            columns[key] = observation(label, fmt, unit, "Daily life", {
                "value": round(value, 3) if fmt == "pct" else round(value, 0 if value >= 100 else 1 if value >= 10 else 2),
                "period": DISTRICT_PERIOD, "source": source, "vintage": "older",
            })
    if taps:
        columns["rural_district_tap_water"] = observation(
            "Rural households with a functional household tap connection", "pct", "%",
            "Daily life", {"value": round(taps["connected"] / taps["households"], 3),
                           "period": TAP_PERIOD, "source": DISTRICT_TAPS},
            scope="Rural households", coverage="Goa district pilot")
    return columns


def district_lens(world, places, key):
    records = [places.get(geoid, {}).get("advisor_columns", {}).get(key) for geoid in world["counties"]]
    values = [records[d]["value"] if owner >= 0 and not water and d >= 0 and records[d] else None
              for owner, water, d in zip(world["owner"], world["water"], world["county"], strict=True)]
    present = [value for value in values if value is not None]
    if not present:
        return None
    sample = next(record for record in records if record)
    lo, hi = min(present), max(present)
    return {**{name: sample[name] for name in ("period", "source", "vintage", "unit", "format")},
            "id": key, "name": sample["label"], "group": "prosperity", "icon": "l-income", "emoji": "",
            "scale": "linear", "domain": [lo, hi if hi > lo else lo + 1],
            "ramp": ["#27304f", "#2a6374", "#529a83", "#b0c882", "#f3e6a6"], "higher_is": "neutral",
            "description": "HCES small-area estimate divided by the Uttar Pradesh mean for the same sector.",
            "note": "Each mapped district shows its own reporting-sector index. Unmatched districts are blank.",
            "values": values}
