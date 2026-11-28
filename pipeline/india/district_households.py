"""Prepare pinned NFHS-5 and NITI MPI district observations."""

import argparse
from collections import defaultdict
import hashlib
from pathlib import Path
import re
import subprocess

from ..core.store import load_interim, save_interim
from .household_cost_sources import DISTRICT_HEALTH, DISTRICT_INTERIM, DISTRICT_MPI, DISTRICT_TAPS, PILOT_INTERIM, REPORTS
from .people_metrics import HtmlRows

# 2011 Census state codes. Admit complete district rosters only, except for the
# already audited UP pilot crosswalk. Omit states with changed survey geography.
STATES = {2: "Himachal Pradesh", 5: "Uttarakhand", 8: "Rajasthan", 9: "Uttar Pradesh",
          20: "Jharkhand", 30: "Goa", 32: "Kerala", 34: "Puducherry"}
NATIONAL_HEADCOUNT = 14.96
MPI_HEADER = re.compile(r"^\s*([^\n:]+): Overview of Districts\s*$", re.MULTILINE)
MPI_ROW = re.compile(r"^\s*(.+?) {2,}([\d.]+%|[–-]) +([\d.]+%|[–-]) +([\d.]+|[–-])"
                     r" +([\d.]+%|[–-]) +([\d.]+%|[–-]) +([\d.]+|[–-])\s*$")
MPI_NAMES = {
    "himachalpradesh": {"lahulandspiti": "lahulspiti"},
    "uttarakhand": {"garhwalpaurigarhwal": "garhwal", "haridwar": "hardwar"},
    "rajasthan": {"chittorgarh": "chittaurgarh", "dholpur": "dhaulpur",
                  "jalore": "jalor", "jhunjhunu": "jhunjhunun"},
    "jharkhand": {"koderma": "kodarma", "sahebganj": "sahibganj"},
    "uttarpradesh": {"allahabadprayagraj": "allahabad", "faizabadayodhya": "faizabad"},
}


def name_key(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def join_surveys(atlas, survey, verified_codes):
    joined = {}
    for state, places in atlas.items():
        observations = survey.get(state, {})
        complete = places.keys() == observations.keys()
        for name, code in places.items():
            if name in observations and (complete or code in verified_codes):
                joined[code] = observations[name]
    return joined


def mpi_tables(report):
    tables = defaultdict(dict)
    state = None
    for page in report.split("\f"):
        if header := MPI_HEADER.search(page):
            state = name_key(header[1])
            page = page[header.end():]
        elif not (state and "Headcount Ratio" in page and "Intensity" in page and "District" in page):
            state = None
        if not state:
            continue
        for line in page.splitlines():
            match = MPI_ROW.fullmatch(line)
            if not match or not match[5].endswith("%"):
                continue
            name = name_key(match[1])
            name = MPI_NAMES.get(state, {}).get(name, name)
            if not name:
                continue
            if name in tables[state]:
                raise ValueError(f"Duplicate MPI row for {state}/{name}")
            tables[state][name] = float(match[5][:-1])
    return dict(tables)


def verified(path, source):
    if hashlib.sha256(path.read_bytes()).hexdigest() != REPORTS[source][1]:
        raise ValueError(f"Unexpected checksum for {path}")
    return path


def tap_counts(cells):
    if len(cells) != 20 or any(not cell.isdecimal() for cell in cells):
        return None
    total, non_piped, *bands = map(int, cells)
    if non_piped or sum(bands[::3]) != total:
        return None
    households, connections = sum(bands[1::3]), sum(bands[2::3])
    if households > 0 and all(c <= h and (n or not h) for n, h, c in zip(bands[::3], bands[1::3], bands[2::3])):
        return connections, households


def goa_taps(path, atlas):
    text = verified(path, DISTRICT_TAPS).read_text()
    if "Reported Till 27/11/2026" not in text or "State: Goa,District: All District,Category: All Districts" not in text:
        raise ValueError("Expected 27 Nov 2026 Goa district coverage")
    table = HtmlRows()
    table.feed(text)
    rows = {}
    for row in table.rows:
        if len(row) != 22 or not row[0].isdigit():
            continue
        name, cells = row[1], row[2:]
        if name_key(name) in rows:
            raise ValueError(f"Duplicate Goa coverage row for {name}")
        rows[name_key(name)] = tap_counts(cells)
    if rows.keys() != atlas.keys():
        raise ValueError("Goa J5 districts must match the complete Census roster")
    return {atlas[name]: {"connected": counts[0], "households": counts[1]}
            for name, counts in rows.items() if counts is not None}


def main():
    import xlrd

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nfhs", type=Path)
    parser.add_argument("mpi", type=Path)
    parser.add_argument("--jjm-goa", type=Path)
    args = parser.parse_args()

    atlas = defaultdict(dict)
    for district in load_interim("datameet")["districts"]:
        state = district["state_code"]
        if state in STATES:
            atlas[name_key(STATES[state])][name_key(district["name"])] = f"{state:02d}-{district['code']:03d}"
    stable_up = set(load_interim(PILOT_INTERIM)["districts"])
    sheet = xlrd.open_workbook(verified(args.nfhs, DISTRICT_HEALTH)).sheet_by_index(0)
    insured = sheet.row_values(0).index(
        "Households with any usual member covered under a health insurance/financing scheme (%)")
    survey = defaultdict(dict)
    for row in range(1, sheet.nrows):
        name, state, *_ = sheet.row_values(row)
        value = sheet.cell_value(row, insured)
        key = name_key(name)
        records = survey[name_key(state)]
        if key in records:
            raise ValueError(f"Duplicate NFHS district {state}/{name}")
        records[key] = value if isinstance(value, (int, float)) and 0 <= value <= 100 else None
    text = subprocess.check_output(["pdftotext", "-layout", verified(args.mpi, DISTRICT_MPI), "-"], text=True)
    health = join_surveys(atlas, survey, stable_up)
    # The NFHS workbook verifies the roster. MPI uses the same survey districts
    # and may omit individual rows or print different spellings.
    mpi = join_surveys(atlas, mpi_tables(text), stable_up | health.keys())
    if not mpi or not health:
        raise ValueError("Pinned reports must have matched district observations")
    save_interim(DISTRICT_INTERIM, {
        "mpi": {code: round(100 * value / NATIONAL_HEADCOUNT, 2) for code, value in mpi.items()},
        "health": {code: round((100 - value) / 100, 6) for code, value in health.items() if value is not None},
    })
    if args.jjm_goa:
        save_interim(DISTRICT_TAPS, goa_taps(args.jjm_goa, atlas["goa"]))


if __name__ == "__main__":
    main()
