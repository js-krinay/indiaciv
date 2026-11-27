"""Build historical civic lenses from Census district observations."""

from collections import Counter

from ..core.store import load_interim
from ..india.census_civic import BANDS, FAITH_FIELDS, FAITHS
from ..india.census_civic_sources import CATALOG, INTERIM


FAITH_TRADITION = "Largest reported religion"
REPORTED_FAITHS = tuple(sorted(FAITHS[:-1]))


LENS_FIELDS = (
    ("foreign_born", "Foreign-born residents", "birthplace", "Born outside India", ()),
    ("bachelors", "Graduate and above (age 25+)", "education", "Graduate and above", ()),
    ("commute", "Median commute distance band", "commute", "Median distance band", BANDS),
    ("homeownership", "Households owning their home", "tenure", "Owned", ()),
    ("faith", "Religious affiliation reported", "religion", "Religious affiliation reported", ()),
    ("faith_tradition", FAITH_TRADITION, "religion", FAITH_TRADITION, REPORTED_FAITHS),
    *((f"faith_{key}", f"{label} share", "religion", label, ())
      for key, label in zip(FAITH_FIELDS, FAITHS, strict=True)),
)
RAMP = ["#303045", "#516787", "#759f9e", "#d9c07f", "#fff3bd"]
CATEGORIES = ["#4ca39d", "#d0a654", "#7c7fd2", "#d17f6b", "#6b9dd4", "#a884b4", "#929887", "#d0bb9a"]

CITY_COLUMNS = (
    ("young", "Residents aged 18–34", "young", "Age 18–34"),
    ("transit", "Bus and train · Other workers", "commute", "Bus and train"),
    ("walk", "On foot · Other workers", "commute", "On foot"),
    ("home", "No travel · Other workers", "commute", "No travel"),
    ("commute_unstated", "Commute mode not stated · Other workers", "commute", "Mode not stated"),
    ("car", "Car, jeep or van · Other workers", "commute", "Car/Jeep/Van"),
    ("born_in_state", "Born in census state", "birthplace", "Born in census state"),
    ("foreign_born", "Born outside India", "birthplace", "Born outside India"),
    ("birthplace_unclassified", "Birthplace unclassifiable", "birthplace", "Birthplace unclassifiable"),
    ("education_unclassified", "Education unclassified (age 25+)", "education", "Unclassified"),
    ("graduate", "Non-technical postgraduate degrees (age 25+)", "postgrad", "Non-technical postgraduate degree"),
    ("degree", "Graduate and above (age 25+) · Citizens", "education", "Graduate and above"),
)


def advisor_columns(records, *, city=False):
    columns = {}
    for key, label, series, metric, categories in LENS_FIELDS:
        if city and key == "faith_tradition":
            continue
        if value := column_record(records, label, series, metric, categories, lens=key):
            columns[key] = value
    if city:
        for key, label, series, metric in CITY_COLUMNS:
            if value := column_record(records, label, series, metric):
                columns[f"cz_{key}"] = value
    return columns


def column_record(records, label, series, metric, categories=(), *, lens=None):
    record = records.get(series, {})
    value = civic_value(record, metric)
    if value is None:
        return None
    return {
        "label": label, "group": "Census civic measures", "format": "text" if categories else "pct",
        "unit": "" if metric == FAITH_TRADITION else "distance band" if categories else "%", "value": value,
        "period": record["period"], "vintage": record["vintage"], "source": record["source"],
        "scope": record["scope"], "coverage": record["scope"], "census_civic": True,
        "hide_rank": series == "religion", **({"lens": lens} if lens else {}),
    }


def civic_value(record, metric):
    values = record.get("values", {})
    if metric != FAITH_TRADITION:
        return values.get(metric)
    if any(values.get(name) is None for name in REPORTED_FAITHS):
        return None
    largest = max(values[name] for name in REPORTED_FAITHS)
    matches = [name for name in REPORTED_FAITHS if largest > 0 and values[name] == largest]
    return matches[0] if len(matches) == 1 else None


def civic_rows(level):
    try:
        return load_interim(INTERIM)[level]
    except FileNotFoundError:
        return {}


def civic_lenses(world, districts, census_a01):
    for key, label, series, metric, categories in LENS_FIELDS:
        records = [districts[code].get("census_civic", {}).get(series) for code in world["counties"]]
        if not any(records):
            continue
        sample = next(record for record in records if record)
        values = []
        for district, owner, water in zip(world["county"], world["owner"], world["water"], strict=True):
            record = records[district] if district >= 0 and owner >= 0 and not water else None
            value = civic_value(record, metric) if record else None
            values.append(categories.index(value) if categories and value is not None else value)
        if all(value is None for value in values):
            continue
        categories_meta = [{"id": str(i), "name": name, "color": CATEGORIES[i]}
                           for i, name in enumerate(categories)]
        if key == "faith_tradition":
            population = Counter()
            for code, record in zip(world["counties"], records, strict=True):
                if name := civic_value(record or {}, metric):
                    population[name] += census_a01[code]["population"]
            for category in categories_meta:
                category["population"] = population[category["name"]]
        yield {
            "id": key, "group": "census_civic",
            "name": f"{label} · {sample['period']}" if key == "faith_tradition" else label,
            "icon": "l-faith-tradition" if key == "faith_tradition" else "l-people", "emoji": "",
            "unit": "" if categories else "%", "format": "category" if categories else "pct",
            "scale": "linear", "domain": [0, len(categories) - 1 if categories else 1],
            "ramp": CATEGORIES[:len(categories)] if categories else RAMP, "higher_is": "neutral",
            **({"categories": categories_meta} if categories else {}),
            "source": sample["source"], "period": sample["period"], "vintage": "older",
            **({"sources": ["census_a01"]} if key == "faith_tradition" else {}),
            "source_line": f"ORGI · {CATALOG[series][0]}",
            "description": "Derived from published Census counts for the district assigned to each land hex.",
            "note": ("The category is the largest reported share for the district. Unstated responses are excluded "
                     "from the comparison. Districts with tied shares or missing observations are blank."
                     if key == "faith_tradition" else "Only districts with a verified source workbook have values."),
            "values": values,
        }
