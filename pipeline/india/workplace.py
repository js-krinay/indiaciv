"""Prepare historical workplace aggregates from SHRUG Pakora and Census 2011 UA keys."""

import argparse
import csv
from collections import defaultdict
from hashlib import file_digest
from io import TextIOWrapper
from pathlib import Path
import re
from zipfile import ZipFile

from .census import read_rows
from .historical_sources import INPUTS, WORKPLACE_PERIOD as PERIOD, WORKPLACE_SOURCE as SOURCE
from ..core.store import save_interim

MIN_JOBS, MIN_SHARE, MIN_LQ = 50, 0.005, 1.25

# This allowlist deliberately excludes broad or mixed SHRIC industries.
INDUSTRIES = {
    "Utilities (electricity, gas, steam and water)": {33, 34, 35},
    "Basic metals and casting": {25, 26, 27},
    "Air transport": {58},
    "Water transport": {56, 57},
    "Performing arts and entertainment": {86},
    "Accommodation": {51},
    "Electric power": {33},
    "Coke and refined petroleum": {19, 20},
    "Pharmaceutical manufacturing": {21},
    "Scientific research and development": {74},
}
NIC = {19: {191}, 20: {192}, 21: {210}, 25: {241}, 26: {242}, 27: {243}, 33: {351},
       34: {352, 353}, 35: {360}, 51: {551, 552, 559}, 56: {501}, 57: {502},
       58: {511, 512}, 74: {721, 722}, 86: {900}}
DEFENCE_NIC = {252, 303, 304, 842}
EXCLUDED = {72}
# SHRUG's harmonised manufacturing total sums these whole groups. Check
# the identity against the pinned district table before using the residual.
MANUFACTURING = {*range(5, 35), 72}
COLUMNS = ["non_farm_jobs", "civilian_jobs", "civilian_manufacturing", "civilian_establishments",
           *(f"ec13_emp_shric_{group}" for group in NIC)]
INDIA_NON_FARM_JOBS, INDIA_CIVILIAN_JOBS = 109_933_023, 101_463_171


def normalized(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def ua_members(rows):
    """Use the lowest-level PCA component. A town and its outgrowth subtotal overlaps its children."""
    groups = defaultdict(dict)
    parent = None
    for row in rows:
        code = row.get("E", "")
        level = row.get("G")
        if level == "0":
            parent = (row["A"], normalized(re.sub(r"\s+UA$", "", row["F"].strip(), flags=re.I)))
        elif parent and level in {"1", "2"} and row.get("D"):
            groups[parent][code] = row["D"]
    return {
        key: {town for code, town in members.items()
              if not (code.endswith("00") and any(other.startswith(code[:-2]) and other != code for other in members))}
        for key, members in groups.items()
    }


def combined(rows, width):
    """A missing constituent makes the combined measure unavailable."""
    rows = list(rows)
    if not rows:
        return (None,) * width
    return tuple(sum(values) if None not in values else None for values in zip(*rows, strict=True))


def industry_metrics(jobs, total, national_jobs, national_total):
    if jobs is None or not total or not national_jobs or not national_total:
        return None
    local = jobs / total
    national = national_jobs / national_total
    lq = local / national
    return dict(local_share=round(local, 8), national_share=round(national, 8), lq=round(lq, 4),
                excess_jobs=round(jobs - total * national),
                qualifies=jobs >= MIN_JOBS and local >= MIN_SHARE and lq >= MIN_LQ)


def csv_rows(book, name):
    with book.open(name) as raw, TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def value(row, key):
    raw = row[key]
    return float(raw) if raw not in {"", ".", "NA"} else None


def measures(row):
    total = value(row, "ec13_emp_all")
    excluded = [value(row, f"ec13_emp_shric_{group}") for group in EXCLUDED]
    jobs = None if total is None or None in excluded else total - sum(excluded)
    manufacturing = value(row, "ec13_emp_manuf")
    civilian_manufacturing = (manufacturing - sum(excluded)
                              if manufacturing is not None and jobs is not None else None)
    if civilian_manufacturing is not None and not 0 <= civilian_manufacturing <= jobs:
        civilian_manufacturing = None
    establishments = value(row, "ec13_count_all") if jobs is not None and total == jobs else None
    return (total, jobs, civilian_manufacturing, establishments,
            *(value(row, key) for key in COLUMNS[4:]))


def india_coverage(total, civilian):
    if (total, civilian) != (INDIA_NON_FARM_JOBS, INDIA_CIVILIAN_JOBS):
        raise ValueError("The pinned India workplace universe has changed")
    return total - civilian, civilian / total


def matched_ua(members, keys, owners, locations):
    if not members or not members <= keys.keys():
        return None
    ids = set().union(*(keys[town] for town in members))
    if not ids <= locations.keys() or any(not owners[key] <= members for key in ids):
        return None
    return combined((locations[key] for key in sorted(ids)), len(COLUMNS))


def observation(values, national):
    _, jobs, manufacturing, establishments, *local_groups = values
    national_total = national[1]
    if jobs is None:
        return None
    industry_values = dict(zip(NIC, local_groups, strict=True))
    benchmark = dict(zip(NIC, national[4:], strict=True))
    details = {}
    for label, groups in INDUSTRIES.items():
        counts = [industry_values[group] for group in groups]
        benchmarks = [benchmark[group] for group in groups]
        metrics = industry_metrics(sum(counts) if None not in counts else None, jobs,
                                   sum(benchmarks) if None not in benchmarks else None, national_total)
        if metrics is not None:
            details[label] = metrics
    top = max((label for label, metric in details.items() if metric["qualifies"]),
              key=lambda label: (details[label]["lq"], details[label]["excess_jobs"], label), default=None)
    result = dict(period=PERIOD, vintage="older", source_id=SOURCE, jobs=round(jobs),
                  industries=details, top_industry=top, top_lq=details[top]["lq"] if top else None)
    if jobs and manufacturing is not None:
        result["manufacturing_share"] = round(manufacturing / jobs, 8)
    if establishments is not None:
        result["establishments"] = round(establishments)
    return result


def prepare(economic, keys, concordance, workbook):
    crosswalk = defaultdict(set)
    for row in csv_rows(concordance, "shric_NIC08_3d_key.csv"):
        crosswalk[int(float(row["shric"]))].add(int(float(row["NIC08_3d"])))
    if any(crosswalk[group] != codes for group, codes in NIC.items()):
        raise ValueError("The verified civilian SHRIC concordance has changed")
    if {group for group, codes in crosswalk.items() if codes & DEFENCE_NIC} != EXCLUDED:
        raise ValueError("The defence-mixed SHRIC groups have changed")
    districts = {}
    for row in csv_rows(economic, "ec13_pc11dist.csv"):
        key = f"{int(row['pc11_state_id']):02d}-{int(row['pc11_district_id']):03d}"
        if key in districts:
            raise ValueError(f"Duplicate workplace district {key}")
        reproduced = sum(value(row, f"ec13_emp_shric_{group}") or 0 for group in MANUFACTURING)
        if abs(reproduced - value(row, "ec13_emp_manuf")) > 1e-6:
            raise ValueError("The harmonised manufacturing series no longer matches its source groups")
        districts[key] = measures(row)
    if len(districts) != 640:
        raise ValueError(f"Expected all 640 Census districts, found {len(districts)}")
    national = combined(districts.values(), len(COLUMNS))
    excluded_jobs, coverage = india_coverage(*national[:2])
    groups = ua_members(row for _, row in read_rows(workbook))
    wanted = set().union(*groups.values())
    town_keys = defaultdict(set)
    owners = defaultdict(set)
    for kind, column in (("u", "pc11_town_id"), ("r", "pc11_village_id")):
        for row in csv_rows(keys, f"pc11{kind}_shrid_key.csv"):
            shrid = row["shrid2"]
            town = row[column].zfill(6)
            owners[shrid].add(town)
            if town in wanted:
                town_keys[town].add(shrid)
    requested = set().union(*town_keys.values())
    locations = {row["shrid2"]: measures(row) for row in csv_rows(economic, "ec13_shrid.csv")
                 if row["shrid2"] in requested}
    uas = {}
    for (state, name), members in groups.items():
        values = matched_ua(members, town_keys, owners, locations)
        if values is not None and (record := observation(values, national)) is not None:
            uas[f"{state}:{name}"] = record
    return {"districts": {key: observation(value, national) for key, value in districts.items()},
            "uas": uas,
            "national": observation(national, national),
            "excluded_jobs": round(excluded_jobs), "civilian_coverage": coverage,
            "district_inputs": districts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    directory = parser.parse_args().input_dir
    paths = [directory / name for name in INPUTS]
    for path in paths:
        with path.open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != INPUTS[path.name]:
                parser.error(f"{path.name} does not match the pinned input")
    with ZipFile(paths[0]) as economic, ZipFile(paths[1]) as keys, ZipFile(paths[2]) as concordance, ZipFile(paths[3]) as workbook:
        data = prepare(economic, keys, concordance, workbook)
    save_interim(SOURCE, data, vintage=PERIOD)


if __name__ == "__main__":
    main()
