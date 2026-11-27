"""Compile the documented incident inventory and geographic count lenses."""

from collections import Counter, defaultdict
from datetime import date

from ..india.disaster_sources import COVERAGE, INCIDENTS, PERIOD


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
        if (kind not in {"Cyclone", "Earthquake", "Flood", "Heatwave", "Landslide"}
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
                       "period", "area", "magnitude", "epicentre", "impact"}:
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
    }


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
