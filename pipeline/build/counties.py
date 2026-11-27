"""District profiles in the upstream Explorer's column-oriented format."""

import json

from ..core.paths import WEB_DATA
from ..core.store import write_web
from .census_civic import FAITH_TRADITION, REPORTED_FAITHS, civic_value

REQUIRES = ["world.json", "lenses.json", "workplace.json", "cities.json"]
PRODUCES = ["counties.json"]


def field(key, label, format, unit=None):
    return {"key": key, "label": label, "format": format, "unit": unit,
            "higher_is": "neutral", "description": label, "source": ""}


LAND = {"forest": "Tree cover", "crop": "Cropland", "developed": "Built-up cover",
        "grass": "Grassland", "shrub": "Shrubland", "wetland": "Mapped wetlands"}
CIVIC = {
    "foreign_born": ("birthplace", "Born outside India", "pct"),
    "bachelors": ("education", "Graduate and above", "pct"),
    "commute": ("commute", "Median distance band", "text"),
    "homeownership": ("tenure", "Owned", "pct"),
    "faith": ("religion", "Religious affiliation reported", "pct"),
    "faith_tradition": ("religion", FAITH_TRADITION, "text"),
}
FIELDS = [
    field("geoid", "Census district code", "text"),
    field("name", "District", "text"),
    field("state", "State or UT", "text"),
    field("population", "Population", "int", "people"),
    field("land_km2", "Referenced district area", "km2", "km²"),
    field("density", "Population density", "float", "people / km²"),
    field("median_age", "Median age", "years", "years"),
    field("cbsa", "Urban agglomeration ID", "text"),
    field("cell", "Map hex", "int"),
    *[field(key, label, "pct", "share of land") for key, label in LAND.items()],
    *[field(key, label, format) for key, (_, label, format) in CIVIC.items()],
    field("veterans", "Registered ex-servicemen", "int", "people"),
    field("veterans_pct", "Registered ex-servicemen share", "pct", "share of residents"),
    field("qcew_jobs", "Workplace jobs", "int", "civilian non-farm jobs"),
]


def district_table(world, places, workplace, cities=()):
    representative = {}
    for cell, district in enumerate(world["county"]):
        if district >= 0:
            representative.setdefault(district, cell)
    for cell, district in places.get("district_fallbacks", {}).items():
        representative.setdefault(district, int(cell))
    memberships = {}
    for city in cities:
        for geoid in city.get("counties", []):
            memberships.setdefault(geoid, []).append(city["id"])

    columns = [f["key"] for f in FIELDS]
    rows = []
    provenance = {}
    for index, ident in enumerate(world["counties"]):
        geoid = ident["geoid"]
        district = places["counties"].get(geoid, {})
        members = memberships.get(geoid, [])
        values = {**district, **ident, "cell": representative.get(index),
                  "land_km2": district.get("area_km2"),
                  "cbsa": members[0] if len(members) == 1 else None}
        meta = {"name": {"source": "datameet"}, "state": {"source": "datameet"},
                "land_km2": {"source": "datameet"},
                **district.get("provenance", {})}
        for key in LAND:
            item = (district.get("historical_land") or {}).get(key)
            if item:
                values[key] = item["value"]
                meta[key] = {k: v for k, v in item.items() if k != "value"}
        for key, (series, metric, _) in CIVIC.items():
            item = (district.get("census_civic") or {}).get(series)
            if item:
                value = civic_value(item, metric)
                if key == "faith_tradition":
                    if value is None:
                        continue
                    value = str(REPORTED_FAITHS.index(value))
                values[key] = value
                meta[key] = {k: v for k, v in item.items() if k != "values"}
        if district.get("registered_veterans") is not None:
            values.update(veterans=district["registered_veterans"], veterans_pct=district.get("veteran_share"))
            meta["veterans"] = {"source": "hp_veterans_2026", "period": "31 Mar 2026"}
            meta["veterans_pct"] = {
                "source": ["hp_veterans_2026", "city_population_grid", "datameet"],
                "period": "31 Mar 2026 registrations · mid-2026 residents", "estimated": True,
            }
        if local_jobs := workplace.get(geoid):
            values["qcew_jobs"] = local_jobs["jobs"]
            meta["qcew_jobs"] = {"source": local_jobs["source_id"], "period": local_jobs["period"],
                                 "vintage": local_jobs["vintage"]}
        rows.append([values.get(key) for key in columns])
        provenance[geoid] = meta
    return {"vintage": None, "period": "1 March 2026", "estimated": True, "columns": columns, "fields": FIELDS,
            "rows": rows, "provenance": provenance}


def build():
    world, lenses, workplace, cities = [json.loads((WEB_DATA / name).read_text()) for name in REQUIRES]
    write_web("counties.json", district_table(world, lenses["places"], workplace["districts"], cities))
