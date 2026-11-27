"""Extract the pinned PLFS quarterly bulletin's state urban persons rows."""

import argparse
import re
import subprocess
from hashlib import file_digest
from pathlib import Path

from ..build.world import STATE_ABBR
from ..core.store import save_interim
from .city_sources import LABOUR_PERIOD, LABOUR_SHA256, LABOUR_SOURCE


def table(text, number, heading, width, codes, expected):
    pages = [p for p in text.split("\f") if f"Table ({number}):" in p and heading in p]
    if len(pages) != 1:
        raise ValueError(f"Expected one page for PLFS Table {number}, {heading!r}")
    rows = {}
    for line in pages[0].splitlines():
        name, separator, columns = line.strip().partition("  ")
        if separator and name in codes:
            values = columns.split()
            if (codes[name] in rows or len(values) != width
                    or not all(re.fullmatch(r"\d+\.\d", value) for value in values)):
                raise ValueError(f"Unexpected PLFS values for {name}: {values}")
            rows[codes[name]] = list(map(float, values))
    if len(rows) != expected:
        raise ValueError(f"Expected {expected} rows in PLFS Table {number}, found {len(rows)}")
    return rows


def broad_industry(text, expected_states=22):
    codes = {**STATE_ABBR, "all-India": "IN"}
    rows = table(text, 4, "rural+urban             person$", 4, codes, expected_states + 1)
    if "IN" not in rows or any(total != 100 or abs(sum(parts) - total) > 0.11
                               for *parts, total in rows.values()):
        raise ValueError("PLFS industry distributions do not reconcile")
    return {state: row[:3] for state, row in rows.items()}


def national_urban_unemployment(text):
    rows = table(text, 5, "age group: 15 years and above", 9, {"all-India": "IN"}, 1)
    return rows["IN"][5] / 100


def extract(text):

    adults = "age group: 15 years and above"
    all_age_wpr = table(text, 3, "age group: all age", 9, STATE_ABBR, 22)
    adult_wpr = table(text, 3, adults, 9, STATE_ABBR, 22)
    unemployment = table(text, 5, adults, 9, STATE_ABBR, 22)
    industries = table(text, 4, "\nurban              person$", 4, STATE_ABBR, 22)
    if not all(rows.keys() == all_age_wpr.keys() for rows in (adult_wpr, unemployment, industries)):
        raise ValueError("PLFS tables have different jurisdiction coverage")
    return {
        state: [row[5], adult_wpr[state][5], unemployment[state][5], *industries[state][:3]]
        for state, row in all_age_wpr.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bulletin", type=Path)
    args = parser.parse_args()
    with args.bulletin.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != LABOUR_SHA256:
            raise ValueError("PLFS bulletin SHA-256 differs from the pinned release")
    text = subprocess.run(["pdftotext", "-layout", str(args.bulletin), "-"],
                          check=True, capture_output=True, text=True).stdout
    save_interim(LABOUR_SOURCE, {"states": extract(text), "broad_industry": broad_industry(text),
                                "national_urban_unemployment_15_plus": national_urban_unemployment(text)},
                 vintage=LABOUR_PERIOD)


if __name__ == "__main__":
    main()
