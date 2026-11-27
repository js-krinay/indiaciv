"""Prepare Annual PLFS 2025 CWS benchmarks for missing labour observations."""

import argparse
import re
import subprocess
from fractions import Fraction
from hashlib import file_digest
from pathlib import Path

from ..build.world import STATE_ABBR
from ..core.store import load_interim, save_interim
from .city_sources import ANNUAL_LABOUR_METHOD as METHOD
from .city_sources import ANNUAL_LABOUR_PERIOD as PERIOD, ANNUAL_LABOUR_SHA256 as SHA256
from .city_sources import ANNUAL_LABOUR_SOURCE as SOURCE


def table_rows(text, number, heading, codes, width, number_pattern, convert):
    pages = [page for page in text.split("\f")
             if f"Table ({number}):" in page and f"\n{heading}\n" in page]
    if len(pages) != 1:
        raise ValueError(f"Expected one PLFS table {number} page for {heading}")
    rows = {}
    for line in pages[0].splitlines():
        name, _, columns = line.strip().partition("  ")
        if name not in codes:
            continue
        code = codes[name]
        values = columns.split()
        expected = 6 if code == "CH" and number in (31, 32) else width
        if code in rows or len(values) != expected or not all(
            re.fullmatch(number_pattern, value) for value in values
        ):
            raise ValueError(f"Unexpected PLFS table {number} row for {name}: {values}")
        rows[code] = [None] * (width - expected) + [convert(value) for value in values]
    if rows.keys() != set(codes.values()):
        raise ValueError(f"Missing PLFS table {number} rows: {set(codes.values()) - rows.keys()}")
    return rows


def rate_rows(text, number, heading, codes):
    rows = table_rows(text, number, heading, codes, 9, r"\d+\.\d", float)
    if any(not 0 <= value <= 100 for row in rows.values() for value in row if value is not None):
        raise ValueError(f"PLFS table {number} rate outside 0–100")
    return rows


def extract(text):
    codes = {**STATE_ABBR, "Andaman & N. Island": "AN", "Dadra & Nagar Haveli & Daman & Diu": "DH"}
    adult_heading = "age group: 15 years and above"
    wpr = rate_rows(text, 31, "age group: all ages", codes)
    adult_wpr = rate_rows(text, 31, adult_heading, codes)
    unemployment = rate_rows(text, 32, adult_heading, codes)
    rows = {code: {} for code in STATE_ABBR.values()}
    for scope, index, heading in (("rural", 2, "rural"), ("urban", 5, "urban"),
                                  ("combined", 8, "rural+urban")):
        scope_codes = {name: code for name, code in codes.items() if scope != "rural" or code != "CH"}
        industries = table_rows(text, 33, heading, scope_codes, 12, r"\d+\.\d", float)
        for code, industry in industries.items():
            *shares, total = industry[-4:]
            if total != 100 or abs(sum(shares) - total) > .11:
                raise ValueError(f"PLFS industry shares do not reconcile for {code} ({scope})")
            rows[code][scope] = {
                "wpr_all_ages": wpr[code][index],
                "wpr_15_plus": adult_wpr[code][index],
                "unemployment_15_plus": unemployment[code][index],
                "industry_shares": shares,
            }
    for scope in ("rural", "urban"):
        scope_codes = {name: code for name, code in codes.items() if scope != "rural" or code != "CH"}
        samples = table_rows(text, 1, scope, scope_codes, 21, r"[\d,]+",
                             lambda value: int(value.replace(",", "")))
        for code, counts in samples.items():
            if not 0 < counts[-5] <= counts[-1] or counts[0] <= 0:
                raise ValueError(f"Invalid PLFS sample for {code} ({scope})")
            rows[code][scope].update(sample_persons=counts[-1], sample_persons_15_plus=counts[-5],
                                     sample_clusters=counts[0])
    for scopes in rows.values():
        for field in ("sample_persons", "sample_persons_15_plus", "sample_clusters"):
            scopes["combined"][field] = scopes.get("rural", {}).get(field, 0) + scopes["urban"][field]
    return rows


def read_survey(path):
    with path.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != SHA256:
            raise ValueError("Annual PLFS SHA-256 differs from the pinned release")
    text = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          check=True, capture_output=True, text=True).stdout
    return extract(text)


def fallback_records(population, population_source, population_period, scope, rates):
    older = {"source": SOURCE, "period": PERIOD, "vintage": "older", "estimated": False,
             "scope": scope, "sample_clusters": rates["sample_clusters"]}
    return {
        "employed": {
            "value": round(population * Fraction(str(rates["wpr_all_ages"])) / 100),
            "source": [population_source, SOURCE], "period": population_period, "vintage": population_period,
            "estimated": True, "description": METHOD, "age": "All ages", "scope": scope,
            "benchmark": {**older, "value": rates["wpr_all_ages"] / 100,
                          "sample_persons": rates["sample_persons"]},
        },
        "unemployment": {
            **older, "value": rates["unemployment_15_plus"] / 100, "age": "15+",
            "sample_persons": rates["sample_persons_15_plus"],
        },
        "industry": {**older, "value": rates["industry_shares"], "status": "Current Weekly Status"},
    }


def annual_rates():
    try:
        return load_interim(SOURCE)["states"]
    except FileNotFoundError:
        return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    save_interim(SOURCE, {"states": read_survey(args.report), "period": PERIOD, "vintage": "older"},
                 vintage=PERIOD)


if __name__ == "__main__":
    main()
