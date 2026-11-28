"""Compile the documented incident inventory and geographic count lenses."""

import json
from collections import Counter, defaultdict
from datetime import date

from ..core.paths import WEB_DATA
from ..core.store import load_interim, write_web
from ..india.disaster_sources import COVERAGE, INCIDENTS, PERIOD

REQUIRES = ["lenses.json", "datameet"]
PRODUCES = ["disasters.json"]

COLD_PERIOD = "1 Jan – 31 Jan 2026"
COLD_SOURCE = "imd_delhi_january_2026"
DROUGHT_PERIOD = "1 Jun – 2 Sep 2026"
DROUGHT_SOURCE = "karnataka_drought_notification_ii_2026"
# Counts from the 23 distinct names in the notification annex, keyed by its published district.
DROUGHT_DISTRICTS = {
    "Tumakuru": 1, "Koppala": 1, "Raichur": 3, "Kalaburagi": 6, "Bidar": 1,
    "Vijayapura": 3, "Haveri": 1, "Dharwad": 4, "Chikkamagaluru": 1, "Kodagu": 2,
}
# Reviewed name equivalents in the unchanged Census 2011 district geography.
DROUGHT_ALIASES = {
    "Tumakuru": "Tumkur", "Koppala": "Koppal", "Kalaburagi": "Gulbarga",
    "Vijayapura": "Bijapur", "Chikkamagaluru": "Chikmagalur",
}
FIRE_PERIOD = "Forest fire season (Nov 2023 – Jun 2024)"
FIRE_SOURCE = "fsi_isfr_2023_fire_detections"
FIRE_TOTAL = 203_544  # ISFR Vol. I, table 4.4, national SNPP-VIIRS detections for the same season.
# Table 4.6 rows with exact Census 2011 district names. Omit reconfigured Prakasam
# and names that do not match a district on the map. Use state codes to disambiguate Bijapur.
FIRE_DISTRICTS = {
    (22, "Bijapur"): 5018, (5, "Nainital"): 3320, (5, "Garhwal"): 3193,
    (5, "Almora"): 2810, (21, "Rayagada"): 2646, (21, "Kandhamal"): 2591,
    (5, "Tehri Garhwal"): 2589, (21, "Malkangiri"): 2582, (5, "Uttarkashi"): 2457,
    (22, "Narayanpur"): 2316, (21, "Koraput"): 1994, (18, "Dima Hasao"): 1843,
    (2, "Shimla"): 1823,
}


def hazard_observations(districts=()):
    dates = [f"2026-01-{day}" for day in (11, 12, 13, 14, 15, 26)]
    observations = [{
        "id": "delhi_cold_wave_days", "label": "Delhi days with reported cold-wave conditions",
        "location": "Delhi IMD reporting area", "value": len(dates), "dates": dates,
        "unit": "days", "period": COLD_PERIOD, "source": COLD_SOURCE,
    }]
    identities = defaultdict(list)
    for row in districts:
        if row["code"]:
            identities[row["state_code"], row["name"]].append(row["code"])
    for name, count in DROUGHT_DISTRICTS.items():
        matches = identities[29, DROUGHT_ALIASES.get(name, name)]
        if len(matches) != 1:
            continue
        district = f"29-{matches[0]:03d}"
        observations.append({
            "id": f"karnataka_drought_taluks_{district}", "district": district,
            "label": "Taluks assessed as drought affected in Karnataka Kharif assessment",
            "location": name, "value": count, "unit": "taluks",
            "period": DROUGHT_PERIOD, "source": DROUGHT_SOURCE,
        })
    for (state, name), count in FIRE_DISTRICTS.items():
        matches = identities[state, name]
        if len(matches) != 1:
            continue
        district = f"{state:02d}-{matches[0]:03d}"
        observations.append({
            "id": f"forest_fire_detections_{district}", "district": district,
            "label": "Share of India’s reported SNPP-VIIRS forest fire detections",
            "location": name, "value": round(100 * count / FIRE_TOTAL, 2), "unit": "%",
            "period": FIRE_PERIOD, "vintage": "older", "source": FIRE_SOURCE,
        })
    return observations


def advisor_inventory(inventory):
    """Adapter for the upstream advisor's incident, state and district tables."""
    events = inventory["events"]
    counts = Counter(event["type"] for event in events)
    types = sorted(counts)
    recent = [{
        "disaster": event["id"], "date": event["start_date"] or event["reported_on"],
        "report_only": not event["start_date"], "state": " · ".join(event["states"]),
        "state_caption": "Mapped affected states and UTs",
        "date_caption": event["start_date"] or f"Reported {event['reported_on']}",
        "type": event["type"], "incident_type": event["type"], "title": event["label"],
        "areas": event.get("area"), "counties": event["districts"],
        "impact": event.get("impact"), "source": event["source"],
        **({"housing_impact": {
            "label": "Houses reported destroyed in Mon town landslide",
            "value": event["impact"]["houses_destroyed"], "unit": "houses",
            "period": "19 Jul 2026", "source": event["source"],
            "district": event["impact"]["district"], "comparator": "≥",
            "caption": f"At least {event['impact']['houses_destroyed']} houses reported destroyed · 19 Jul 2026",
        }} if event["id"] == "mon-town-landslide" else {}),
        **({"period": event["period"], "vintage": event["vintage"]} if "vintage" in event else {}),
    } for event in events]
    districts = inventory["districts"]
    return {
        "period": inventory["period"],
        "sources": sorted({event["source"] for event in events}),
        "fema": {
            "rule": inventory["coverage"], "total": len(events), "by_type": dict(counts),
            "types": [{"id": name, "name": name} for name in types],
            "states": {key: {"total": row["count"], "by_type": row["by_type"]}
                       for key, row in inventory["states"].items()},
            "counties": {
                "columns": ["geoid", "total", "last_date", *types],
                "rows": [[key, row["count"], row["last_date"], *(row["by_type"].get(name, 0) for name in types)]
                         for key, row in districts.items()],
                "last_captions": {key: caption for key, row in districts.items()
                                  if (caption := row.get("last_caption")) and caption != row["last_date"]},
            },
            "recent": recent,
        },
    }


def build():
    lenses = json.loads((WEB_DATA / "lenses.json").read_text())
    doc = advisor_inventory(lenses["disasters"])
    doc["observations"] = hazard_observations(load_interim("datameet")["districts"])
    doc["sources"] = sorted(set(doc["sources"]) | {row["source"] for row in doc["observations"]})
    write_web("disasters.json", doc)


def inventory(world, district_states, district_shapes, projection):
    state_ids = dict(zip(world["state_names"], world["states"], strict=True))
    events = []
    for incident in INCIDENTS:
        row = {k: v for k, v in incident.items() if k not in {"state_names", "lon_lat"}}
        states = {state_ids[name] for name in incident.get("state_names", [])}
        if "lon_lat" in incident:
            point = projection(*incident["lon_lat"])
            row["epicentre"] = [round(value, 1) for value in point]
            index = district_shapes.locate(*point)
            if index >= 0:
                district = world["counties"][index]
                if district_states.get(district) in states:
                    row["districts"] = [district]
        states.update(district_states[district] for district in row["districts"])
        row.update(states=sorted(states), estimated=False, period=PERIOD,
                   publisher=row.get("publisher", "Press Information Bureau"))
        events.append(row)
    return sorted(events, key=lambda row: (row["start_date"] or row["reported_on"], row["id"]), reverse=True)


def check_inventory(doc, source_ids, district_ids, state_ids):
    events = doc["events"]
    if doc["period"] != PERIOD:
        raise ValueError("invalid inventory period")
    if len({row["id"] for row in events}) != len(events):
        raise ValueError("duplicate incident IDs")
    groups = {"states": defaultdict(list), "districts": defaultdict(list)}
    for row in events:
        dates = {key: date.fromisoformat(row[key]) for key in ("start_date", "end_date", "reported_on", "landfall_date")
                 if row.get(key)}
        if (not (dates.keys() & {"start_date", "reported_on"})
                or any(not date(2026, 1, 1) <= day <= date(2026, 11, 27) for day in dates.values())
                or ("end_date" in dates and dates["end_date"] < dates["start_date"])):
            raise ValueError(f"Invalid dates for {row['id']}")
        kind = row["type"]
        if (kind not in {"Cyclone", "Earthquake", "Flood", "Heatwave", "Landslide", "Thunderstorm"}
                or (kind == "Earthquake" and row["magnitude"] < 5)
                or (kind == "Cyclone" and not dates["start_date"] <= dates["landfall_date"] <= dates["end_date"])):
            raise ValueError(f"Invalid hazard class or evidence for {row['id']}")
        sources = [row["source"], *(ref["source"] for ref in row.get("related_sources", []))]
        if (not set(sources) <= source_ids or not set(row["districts"]) <= district_ids
                or not row["states"] or not set(row["states"]) <= state_ids or row["estimated"] is not False
                or row["period"] != PERIOD):
            raise ValueError(f"Invalid geography or provenance for {row['id']}")
        if set(row) - {"id", "type", "label", "start_date", "end_date", "reported_on", "landfall_date",
                       "districts", "states", "source", "url", "publisher", "related_sources", "estimated",
                       "period", "vintage", "area", "magnitude", "epicentre", "impact"}:
            raise ValueError(f"Unexpected public incident fields for {row['id']}")
        if "impact" in row:
            impact = row["impact"]
            if (impact["district"] not in row["districts"] or set(impact) - {"district", "deaths", "houses_destroyed"}
                    or any(type(value) is not int or value < 0 for key, value in impact.items() if key != "district")):
                raise ValueError(f"Invalid incident impact for {row['id']}")
        for level, records in groups.items():
            for key in set(row[level]):
                records[key].append(row)
    for level, records in groups.items():
        if doc[level] != {key: event_summary(rows) for key, rows in records.items()}:
            raise ValueError(f"Invalid summary counts for {level}")


def index_events(events, district_states):
    states, districts = defaultdict(list), defaultdict(list)
    seen = set()
    for event in events:
        if event["id"] in seen:
            raise ValueError(f"Duplicate disaster incident {event['id']}")
        seen.add(event["id"])
        homes = set(event.get("states", []))
        for district in set(event["districts"]):
            homes.add(district_states[district])
            districts[district].append(event)
        for state in sorted(homes):
            states[state].append(event)
    return dict(states), dict(districts)


def event_summary(events):
    if not events:
        return None
    last, report_only = max(
        (event.get("end_date") or event["start_date"] or event["reported_on"], not event["start_date"])
        for event in events
    )
    return {
        "count": len(events), "by_type": dict(Counter(event["type"] for event in events)),
        "last_date": last, "last_report_only": report_only,
        "last_caption": f"Reported {last}" if report_only else last,
    }


def advisor_definitions(events, period, coverage):
    common = {"period": period, "source": "india_disasters_2026", "group": "Hazards", "description": coverage}
    specs = [
        ("disasters", "Documented hazard events", "int", ["count"]),
        ("disaster_last_date", "Latest hazard date", "text", ["last_caption"]),
        *((f"disaster_{name.lower()}_count", f"{name} events", "int", ["by_type", name])
          for name in sorted({event["type"] for event in events})),
    ]
    return [{**common, "key": key, "label": label, "format": fmt,
             "unit": "documented events" if fmt == "int" else "event or report date",
             "paths": {level: ["hazardSummary", *path] for level in ("states", "metros", "counties")}}
            for key, label, fmt, path in specs]


def disaster_lenses(world, states, districts):
    lenses = []
    group = {"id": "disasters", "name": "Disasters", "icon": "g-hazards"}
    for level, records, keys, owners in [
        ("state", states, world["states"], world["owner"]),
        ("district", districts, world["counties"], world["county"]),
    ]:
        types = sorted({event["type"] for events in records.values() for event in events})
        for kind in [None, *types]:
            selected = {key: [event for event in events if kind is None or event["type"] == kind]
                        for key, events in records.items()}
            counts = [len(selected.get(key, [])) or None for key in keys]
            if not any(counts):
                continue
            values = [counts[i] if i >= 0 and state >= 0 and not water else None
                      for i, state, water in zip(owners, world["owner"], world["water"], strict=True)]
            lenses.append({
                "id": f"disasters_{level}_{kind.lower() if kind else 'all'}", "group": group["id"],
                "name": f"{kind or 'All documented events'} · {level}", "icon": "l-disasters", "emoji": "",
                "unit": "documented events", "format": "int", "scale": "linear",
                "domain": [1, max(2, max(count for count in counts if count))],
                "ramp": ["#60475f", "#be6078", "#f2a071", "#fff0b1"], "higher_is": "neutral",
                "source": "india_disasters_2026",
                "period": PERIOD, "estimated": False, "description": COVERAGE,
                "note": "Blank areas have no matching record in this inventory.",
                "values": values,
            })
    return group, lenses
