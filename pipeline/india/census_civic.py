"""Prepare Census 2011 civic shares from the pinned ORGI workbooks."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from itertools import accumulate
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote
from urllib.request import urlopen

from ..core.store import load_interim, save_interim
from .census_civic_sources import INTERIM, PERIOD, TABLES, TENURE_PERIOD, workbook_manifest
from .orgi import Workbook, count, group_rows

BANDS = ("No travel", "0–1 km", "2–5 km", "6–10 km", "11–20 km", "21–30 km", "31–50 km", "51+ km")

MODES = ("On foot", "Bicycle", "Moped/Scooter/Motor Cycle", "Car/Jeep/Van",
         "Tempo/Autorickshaw/Taxi", "Bus", "Train", "Water transport", "Any other", "No travel")
BIRTHPLACES = ("Total Population", "Within the state of enumeration",
               "States in India beyond the state of enumeration", "Born Outside India", "Unclassifiable")
FAITHS = ("Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain", "Other religions and persuasions",
          "Religion not stated")
FAITH_FIELDS = ("hindu", "muslim", "christian", "sikh", "buddhist", "jain", "other", "not_stated")
ATTAINMENT = ("Below secondary", "Secondary or higher secondary", "Diploma below degree",
              "Graduate and above", "Unclassified")

def sum_vectors(vectors):
    if any(vector is None or None in vector for vector in vectors):
        return None
    return tuple(map(sum, zip(*vectors, strict=True))) if vectors else None


def sum_areas(rows, keys, residence):
    return sum_vectors([rows.get((code, residence)) for code in sorted(set(keys))])


def shares(labels, counts):
    if not counts or not counts[0]:
        return {}
    return {label: round(value / counts[0], 6) for label, value in zip(labels, counts[1:], strict=True)}


def median_band(counts):
    total = sum(counts)
    return next((label for label, cumulative in zip(BANDS, accumulate(counts), strict=True)
                 if total and 2 * cumulative >= total), None)


def known_age_median(districts):
    ages = sorted(label for label in districts[0] if label not in {"All ages", "Age not stated"})
    values = {int(float(label.rstrip("+"))): sum(row[label][0] for row in districts) for label in ages}
    total = sum(values.values())
    if not total or any(sum(counts[0] for label, counts in row.items() if label != "All ages") != row["All ages"][0]
                        for row in districts):
        raise ValueError("C-13 age counts do not reconcile")
    ordered = sorted(values)
    return next(age for age, cumulative in zip(ordered, accumulate(values[age] for age in ordered), strict=True)
                if 2 * cumulative >= total)


def district_or_state(row):
    return count(row[3]) == 0 and count(row[4]) == 0


def at_least_25(row):
    lower = str(row[5]).strip().rstrip("+").split("-", 1)[0]
    return lower.isdigit() and int(lower) >= 25


def extract(kind, rows, table):
    def group(**kwargs):
        return group_rows(rows, table, **kwargs)

    if kind == "commute":
        groups = group(residence=3, category=5, columns=(6, *range(9, 34, 3)))
        result = {}
        for key, entries in groups.items():
            total, *distances = entries["All Modes"]
            modes = tuple(entries[mode][0] for mode in MODES)
            if None not in (total, *modes, *distances):
                if sum(distances) != total or sum(modes) > total:
                    raise ValueError(f"B-28 counts do not reconcile for {key}")
                result[key] = (total, *modes, total - sum(modes), *distances)
        return result
    if kind in {"birthplace", "young"}:
        groups = group(residence=None, category=4, columns=(5, 8, 11),
                       include=lambda row: str(row[4]).strip() in BIRTHPLACES if kind == "birthplace"
                       else str(row[4]).strip() == "All ages" or isinstance(row[4], (int, float))
                       and 18 <= row[4] <= 34)
        result = {}
        for (code, _), entries in groups.items():
            for i, scope in enumerate(("Total", "Rural", "Urban")):
                if kind == "birthplace":
                    values = tuple(entries[label][i] for label in BIRTHPLACES)
                else:
                    ages = [entries[str(float(age))][i] for age in range(18, 35)]
                    values = (entries["All ages"][i], None if None in ages else sum(ages))
                if None not in values:
                    result[code, scope] = values
        return result
    if kind in {"education", "postgrad"}:
        columns = (6, 15) if kind == "postgrad" else (6, 9, *range(15, 43, 3))
        groups = group(residence=4, category=5, columns=columns, include=at_least_25)
        result = {}
        for key, entries in groups.items():
            values = sum_vectors(list(entries.values()))
            if values is None:
                continue
            if kind == "postgrad":
                result[key] = values
            else:
                total, illiterate, no_level, below_primary, primary, middle, secondary, higher, nontech, tech, degree, other = values
                result[key] = (total, illiterate + no_level + below_primary + primary + middle,
                               secondary + higher, nontech + tech, degree, other)
        return result
    if kind == "religion":
        groups = group(residence=6, category=None, columns=(7, *range(10, 32, 3)), include=district_or_state)
        return {key: entries[""] for key, entries in groups.items() if None not in entries[""]}
    if kind == "tenure":
        labels = ("Total", "Owned", "Rented", "Any Other")
        groups = group(residence=6, category=7, columns=(9,),
                       include=lambda row: district_or_state(row) and str(row[8]).strip() == "All Households")
        return {key: tuple(entries[label][0] for label in labels) for key, entries in groups.items()
                if all(label in entries and entries[label][0] is not None for label in labels)}
    raise ValueError(kind)


def observation(kind, counts, scope):
    if not counts or not counts[0]:
        return None
    record = {"source": f"orgi_civic_{kind}", "period": TENURE_PERIOD if kind == "tenure" else PERIOD,
              "vintage": "older", "scope": scope}
    if kind == "commute":
        values = shares((*MODES, "Mode not stated"), counts[:12])
        values["Bus and train"] = round((counts[6] + counts[7]) / counts[0], 6)
        values["Other published modes"] = round(sum(counts[i] for i in (2, 3, 5, 8, 9)) / counts[0], 6)
        values["Median distance band"] = median_band(counts[12:-1])
        values["Distance not stated"] = round(counts[-1] / counts[0], 6)
    elif kind == "religion":
        values = shares(FAITHS, counts)
        values["Religious affiliation reported"] = round((counts[0] - counts[-1]) / counts[0], 6)
    else:
        labels = {"birthplace": ("Born in census state", "Born in another Indian state", "Born outside India", "Birthplace unclassifiable"),
                  "tenure": ("Owned", "Rented", "Other tenure"), "young": ("Age 18–34",),
                  "education": ATTAINMENT,
                  "postgrad": ("Non-technical postgraduate degree",)}
        values = shares(labels[kind], counts)
    return {**record, "values": values}


def fetch_workbooks(directory, manifest=None):
    directory.mkdir(parents=True, exist_ok=True)

    def fetch(entry):
        _, _, name, checksum, url, _ = entry
        path = directory / name
        if path.exists():
            return
        with urlopen(quote(url, safe=":/%"), timeout=30) as response:
            data = response.read()
        if sha256(data).hexdigest() != checksum:
            raise ValueError(f"Unexpected SHA-256 for {name}")
        with TemporaryDirectory(dir=directory) as tmp:
            partial = Path(tmp) / name
            partial.write_bytes(data)
            partial.replace(path)

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(fetch, workbook_manifest() if manifest is None else manifest))


def validate_crosswalk(states, district_codes):
    expected = set(district_codes)
    if len(expected) != 640 or states.keys() != expected:
        raise ValueError("Crosswalk must cover exactly the 640 Census A-01 district codes")
    memberships = {
        "LA": {"01-003", "01-004"},  # Leh and Kargil
        "JK": {f"01-{i:03d}" for i in range(1, 23) if i not in (3, 4)},
        "TS": {f"28-{i:03d}" for i in range(532, 542)},
        "AP": {f"28-{i:03d}" for i in range(542, 555)},
        "DH": {"25-494", "25-495", "26-496"},  # Diu, Daman, Dadra and Nagar Haveli
    }
    for state, codes in memberships.items():
        if {code for code, owner in states.items() if owner == state} != codes:
            raise ValueError(f"Unexpected Census 2011 district membership for {state}")


def prepare(directory):
    from . import GHSL_UCDB
    from ..build.yields import district_state_map

    districts = load_interim("census_a01")["districts"]
    areas = load_interim("datameet")
    states = district_state_map(areas)
    validate_crosswalk(states, districts)
    try:
        profiles = load_interim(GHSL_UCDB)["profiles"]
    except FileNotFoundError:
        profiles = {}
    out = {"districts": {}, "states": {}, "cities": {}}
    manifest = workbook_manifest()
    for kind, table in TABLES.items():
        rows = {}
        for series, expected_state, name, checksum, _, _ in manifest:
            if series != kind:
                continue
            book = Workbook(name, checksum, table)
            workbook_rows = book.rows(directory / book.filename)
            if (kind, expected_state) == ("young", "01"):
                workbook_rows = list(workbook_rows)
                age_groups = group_rows(workbook_rows, table, residence=None, category=4, columns=(5,),
                                        include=lambda row: row[1:3] in (("01", "003"), ("01", "004")))
                ladakh = [age_groups[code, "Total"] for code in ("01-003", "01-004")]
                out["states"].setdefault("LA", {})["median_age"] = {
                    "value": known_age_median(ladakh), "period": PERIOD, "source": "orgi_civic_young",
                    "vintage": "older", "scope": "Leh and Kargil residents with stated age",
                }
            records = extract(kind, workbook_rows, book.table)
            if not records or any(not code.startswith(f"{expected_state}-") for code, _ in records):
                raise ValueError(f"Unexpected geographic coverage in {book.filename}")
            if rows.keys() & records.keys():
                raise ValueError(f"Duplicate geographic coverage in {book.filename}")
            rows.update(records)
        for (code, residence), values in rows.items():
            if residence == "Total" and not code.endswith("-000"):
                if code not in districts:
                    raise ValueError(f"Unexpected Census 2011 district: {code}")
                if kind in {"birthplace", "religion", "young"} and values[0] != districts[code]["population"]:
                    raise ValueError(f"{kind} population for {code} disagrees with Census A-01")
                if record := observation(kind, values, "Census 2011 district"):
                    out["districts"].setdefault(code, {})[kind] = record
        for state in sorted(set(states.values())):
            members = [code for code, abbr in states.items() if abbr == state and code in districts]
            # Khammam straddles the current AP/TS boundary.
            if state in {"AP", "TS"}:
                continue
            if record := observation(kind, sum_areas(rows, members, "Total"), "Census 2011 districts"):
                if kind == "birthplace" and state in {"JK", "LA", "DH"}:
                    for label in ("Born in census state", "Born in another Indian state"):
                        del record["values"][label]
                out["states"].setdefault(state, {})[kind] = record
        for city, profile in profiles.items():
            members = [district["id"] for district in profile["districts"]]
            if record := observation(kind, sum_areas(rows, members, "Urban"), "urban member districts"):
                out["cities"].setdefault(city, {})[kind] = record
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--fetch", action="store_true", help="Download missing workbooks from their pinned URLs")
    args = parser.parse_args()
    if args.fetch:
        fetch_workbooks(args.directory)
    save_interim(INTERIM, prepare(args.directory), vintage=PERIOD)
