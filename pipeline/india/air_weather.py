"""Prepare checksum-pinned local air and monsoon inputs for 2026."""

from argparse import ArgumentParser
from collections import defaultdict
import csv
from datetime import date, datetime, timedelta
from hashlib import file_digest
import json
from math import isfinite
from pathlib import Path
import re
from statistics import mean
from zipfile import ZipFile

from . import AIR_WEATHER_PINS
from ..core.geo import geojson_rings
from ..core.store import save_interim

START = date(2026, 1, 1)
END = date(2026, 10, 31)
DAYS = (END - START).days + 1
MIN_DAYS = (4 * DAYS + 4) // 5
AIR_PERIOD = "Jan–Oct 2026"
MONSOON_PERIOD = "Jun–Sep 2026"
SUBDIVISION_ALIASES = {
    "ANDAMAN & NICOBAR ISLANDS": "A & N ISLAND",
    "COASTAL ANDHRA PRADESH & YANAM": "CO AP AND YANAM",
    "HARYANA, CHANDIGARH & DELHI": "HAR. CHD & DELHI",
    "JAMMU, KASHMIR & LADAKH": "JAMMU & KASHMIR AND LADAKH",
    "NAGALAND, MANIPUR, MIZORAM & TRIPURA": "N M M T",
    "NORTH INTERIOR KARNATAKA": "N. I. KARNATAKA",
    "ODISHA": "ORISSA",
    "SOUTH INTERIOR KARNATAKA": "S. I. KARNATAKA",
    "SUB-HIMALAYAN WEST BENGAL & SIKKIM": "SHWB & SIKKIM",
    "TAMIL NADU, PUDUCHERRY & KARAIKAL": "TN PUDU AND KKL",
}


def aqi_summary(rows, start=START, end=END):
    daily = {}
    for stamp, aqi, *_ in rows:
        day = date.fromisoformat(stamp)
        if start <= day <= end and type(aqi) is int and 0 <= aqi <= 500:
            if day in daily and daily[day] != aqi:
                raise ValueError(f"Conflicting AQI for {day}")
            daily[day] = aqi
    if len(daily) >= (4 * ((end - start).days + 1) + 4) // 5:
        return {"days": len(daily), "poor": sum(aqi >= 201 for aqi in daily.values())}
    return None


def station_summary(data):
    if data["unit"] != "µg/m³" or data["pollutant"] != "PM2.5":
        raise ValueError("Expected hourly PM2.5 in µg/m³")
    daily = defaultdict(dict)
    for row in data["rows"]:
        # EnviroCatalysts uses CPCB local hour-ending labels, serialized with a Z suffix.
        end = datetime.fromisoformat(row["dateTime"])
        if (end.minute and (end.hour, end.minute) != (23, 59)) or end.second or end.microsecond:
            raise ValueError(f"Expected an hour-ending label, got {end}")
        # Some end-of-day readings use 23:59 in place of 00:00 the next day.
        slot = end - timedelta(minutes=1)
        day = slot.date()
        if START <= day <= END:
            if slot.hour in daily[day]:
                raise ValueError(f"Duplicate hour ending {end}")
            daily[day][slot.hour] = row
    summary = {}
    for name in data["stations"]:
        if name == "City_Average":
            continue
        days = []
        for hours in daily.values():
            values = [row.get(name) for row in hours.values()]
            values = [v for v in values if type(v) in (int, float) and isfinite(v) and v >= 0]
            if len(values) >= 18:
                days.append(mean(values))
        if len(days) >= MIN_DAYS:
            summary[name] = {"days": len(days), "mean": mean(days)}
    return summary


def monsoon_departures(csv_file):
    departures = {}
    for row in csv.DictReader(csv_file):
        key = row["entity"].strip().upper()
        value = int(row["value"])
        if row["period"] != "2026-06-01/2026-09-30" or row["unit"] != "% from normal" or value < -100:
            raise ValueError(f"Invalid June–September 2026 departure for {key}")
        if key in departures:
            raise ValueError(f"Duplicate subdivision {key}")
        departures[key] = value
    return departures


def station_key(name):
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def prepare_aqi(path):
    cities = []
    monthly = []
    with ZipFile(path) as archive:
        for name in archive.namelist():
            entry = json.loads(archive.read(name))
            summary = aqi_summary(entry["days"])
            if summary is not None:
                cities.append({"city": entry["city"], "state": entry["state"], **summary})
            elif (entry["city"], entry["state"]) == ("Madurai", "Tamil Nadu"):
                january = aqi_summary(entry["days"], START, date(2026, 1, 31))
                if january is not None:
                    monthly.append({"city": entry["city"], "state": entry["state"], **january,
                                    "calendar_days": 31, "period": "1 Jan 2026 – 31 Jan 2026", "vintage": "2026 observed"})
    return {"cities": cities, "monthly": monthly}


def prepare_pm25(path, stations_path):
    locations = defaultdict(list)
    with stations_path.open(encoding="utf-8", newline="") as rows:
        for row in csv.DictReader(rows):
            if row["latitude"] and row["longitude"]:
                locations[station_key(row["station_name"])].append(row)
    stations = {}
    missed = 0
    with ZipFile(path) as archive:
        for name in archive.namelist():
            entry = json.loads(archive.read(name))
            for monitor, summary in station_summary(entry).items():
                matches = locations[station_key(monitor)]
                if len(matches) != 1:
                    missed += 1
                    continue
                location, = matches
                station_id = location["station_id"]
                record = {
                    "name": location["station_name"], "lat": float(location["latitude"]),
                    "lon": float(location["longitude"]), **summary,
                }
                if station_id in stations and stations[station_id] != record:
                    raise ValueError(f"Conflicting daily input for {station_id}")
                stations[station_id] = record
    print(f"    {len(stations)} PM2.5 stations matched; {missed} eligible station series lacked a unique location")
    return {"stations": stations}


def prepare_monsoon(rainfall_path, geometry_path):
    with rainfall_path.open(encoding="utf-8", newline="") as rows:
        departures = monsoon_departures(rows)
    subdivisions = {}
    names = {geometry: name for name, geometry in SUBDIVISION_ALIASES.items()}
    features = json.loads(geometry_path.read_text(encoding="utf-8"))["features"]
    for feature in features:
        key = feature["properties"]["name"].upper()
        key = names.get(key, key)
        if key in subdivisions:
            raise ValueError(f"Duplicate subdivision geometry {key}")
        subdivisions[key] = {"departure": departures[key], "rings": geojson_rings(feature["geometry"])}
    if len(subdivisions) != 36 or subdivisions.keys() != departures.keys():
        raise ValueError("Expected matching records for all 36 IMD subdivisions")
    return {"subdivisions": subdivisions}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--aqi", type=Path)
    parser.add_argument("--pm25", type=Path)
    parser.add_argument("--stations", type=Path)
    parser.add_argument("--rainfall", type=Path)
    parser.add_argument("--geometry", type=Path)
    args = parser.parse_args()
    if bool(args.pm25) != bool(args.stations) or bool(args.rainfall) != bool(args.geometry):
        parser.error("Pass --pm25 with --stations and --rainfall with --geometry")
    if not (args.aqi or args.pm25 or args.rainfall):
        parser.error("Pass at least one input group")
    for key, path in vars(args).items():
        if path is not None:
            with path.open("rb") as raw:
                actual = file_digest(raw, "sha256").hexdigest()
            if actual != AIR_WEATHER_PINS[key]:
                parser.error(f"{key} SHA-256 mismatch for {path}: {actual}")
    if args.aqi:
        save_interim("cpcb_city_aqi", prepare_aqi(args.aqi), vintage=AIR_PERIOD)
    if args.pm25:
        save_interim("cpcb_station_pm25", prepare_pm25(args.pm25, args.stations), vintage=AIR_PERIOD)
    if args.rainfall:
        save_interim("imd_monsoon", prepare_monsoon(args.rainfall, args.geometry), vintage=MONSOON_PERIOD)


if __name__ == "__main__":
    main()
