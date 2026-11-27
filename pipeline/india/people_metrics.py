"""Prepare the pinned state metrics used by the 2026 map and Explorer."""

import csv
import json
import re
import subprocess
import sys
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path

from ..core.store import save_interim
from .people_sources import JJM_RESEARCH_SHA, PINS
from .projections import CHECKSUM as TG_SHA


LABOUR = ("lfpr", "wpr", "unemployment", "female_lfpr", "agri_worker_share")
NUM = r"[\d,]+"
DEC = r"\d+(?:\.\d+)?"
RATE = rf"(?:{DEC}|[-–*]+)"


def table_rows(text, count, number=RATE):
    pattern = rf"^[ \t]*([A-Za-z].*?)[ \t]{{2,}}((?:{number}[ \t]+){{{count-1}}}{number})[ \t]*$"
    for match in re.finditer(pattern, text, re.M):
        yield match[1].strip(), match[2].split()


def fraction(text):
    return round(float(text) / 100, 6) if re.fullmatch(DEC, text) else None


def parse_plfs_rates(page):
    if "age group: 15 years and above" not in page:
        return {}
    return {name: ([fraction(v) for v in cells[2::3]], [fraction(v) for v in cells[1::3]])
            for name, cells in table_rows(page, 9)}


def parse_plfs(text):
    metrics = {key: {} for key in LABOUR}
    for page in text.split("\f"):
        match = re.search(r"^Table \(([2345])\):", page, re.M)
        if not match:
            continue
        if match[1] == "4":
            sector = re.search(r"^(rural\s*\+\s*urban|rural|urban)\s+person\b", page, re.M)
            if sector:
                index = ("rural", "urban", "rural+urban").index(re.sub(r"\s+", "", sector[1]))
                for name, cells in table_rows(page, 4):
                    metrics["agri_worker_share"].setdefault(name, [None] * 3)[index] = fraction(cells[0])
            continue
        key = {"2": "lfpr", "3": "wpr", "5": "unemployment"}[match[1]]
        for name, (persons, women) in parse_plfs_rates(page).items():
            metrics[key][name] = persons
            if key == "lfpr":
                metrics["female_lfpr"][name] = women
    if any(len(rows) != 23 or any(v is None for v in rows.get("all-India", [None])) for rows in metrics.values()):
        raise ValueError(f"Unexpected PLFS coverage: { {key: len(rows) for key, rows in metrics.items()} }")
    return metrics


class HtmlRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def parse_jjm(rows):
    return {name: fraction(pct.strip("%")) for serial, name, total, *_, pct in
            (row for row in rows if len(row) in (8, 9))
            if (serial.rstrip(".").isdigit() or name.casefold() == "total")
            and re.fullmatch(DEC, total.replace(",", "")) and float(total.replace(",", "")) > 0}


def parse_cea(text):
    annex = next(page for page in text.split("\f") if re.search(r"^\s*Annex-II\s*$", page, re.M))
    annex = annex.split("Annex-III")[0]
    return {name: int(cells[1].replace(",", "")) for name, cells in table_rows(annex, 4, rf"(?:{NUM}|{DEC})")
            if not name.endswith("Region") and name != "Damodar Valley Corporation"}


def parse_gsdp(payload):
    latest = {}
    for row in payload["data"]:
        name, year, value = row["state"], int(row["year"][:4]), row["current_price"]
        if value is not None and year <= 2025 and year > latest.get(name, (0,))[0]:
            latest[name] = (year, float(value))
    return latest


def parse_gsdp_supplement(text):
    wanted = {"Assam", "Haryana", "Ladakh", "Nagaland"}
    latest = {}
    for row in csv.DictReader(text.splitlines()):
        year = int(row["date"][:4])
        for column, value in row.items():
            name = column.split(":")[0]
            if name in wanted and value and year < 2025:
                latest[name] = (year, float(value))
    return latest


def parse_delhi(text):
    match = re.search(r"likely to attain a level of ₹\s*([\d,]+) crore which is at a growth", text)
    return int(match[1].replace(",", ""))


def parse_gdp(text):
    text = text.split("Statement 2:", 1)[1]
    match = re.search(rf"^\s*13\s+GDP\s+{NUM}\s+{NUM}\s+{NUM}\s+({NUM})\s+{DEC}\s+{DEC}\s+({DEC})\s*$", text, re.M)
    return int(match[1].replace(",", "")), fraction(match[2])


def parse_wage(text):
    schedule = text.split("State-wise wage rate for unskilled manual workers", 1)[1]
    rows = {name: int(value) for name, value in re.findall(
        r"^ *\d+\. +([A-Z][A-Za-z&]*(?: [A-Za-z&]+)*) +Rs\. (\d+)\.00 *$", schedule, re.M)}
    # The merged UT spans several lines. The three other schedules split by sub-state area.
    for name in ("Non-scheduled areas", "Andaman District", "Sikkim", "Himachal Pradesh"):
        rows.pop(name, None)
    if merged := re.search(r"Dadra and Nagar Haveli +Rs\. (\d+)\.00", schedule):
        rows["Dadra and Nagar Haveli and Daman and Diu"] = int(merged[1])
    return rows


def parse_wage_average(html):
    return float(re.search(r"to ₹(\d+\.\d+) per day under VB", html)[1])


def parse_urban(text, table):
    rows = {}
    for page in text.split("\f"):
        if not re.search(rf"^\s*TABLE - {table}(?:\s|$)", page):
            continue
        header = re.search(r"^.*\bPerson[s]?\s+Male\b.*$", page, re.M)
        values = re.search(r"^\s*2026\s+([^\n]+)$", page, re.M)
        if not header or not values:
            continue
        numbers = values[1].split()[::3]
        if "NICOBAR" in page[:header.start()]:
            rows.update(zip(("LAKSHADWEEP", "PUDUCHERRY", "ANDAMAN & NICOBAR ISLANDS"),
                            (float(v.replace(",", "")) for v in numbers)))
            continue
        lines = page[:header.start()].splitlines()[-2:] + [header[0].split("Person")[0]]
        names = [name.strip() for line in lines for name in re.split(r"\s{2,}", line.strip())
                 if re.fullmatch(r"[A-Z][A-Z &()]+", name) and name.strip() != "ISLANDS"]
        if len(names) != len(numbers):
            raise ValueError(f"Urban table {table}: {names} for {numbers}")
        if table == 9 and "HAVELI" in names:
            names = ["DAMAN & DIU", "DADRA & NAGAR HAVELI", "GOA"]
        elif table == 9 and "PRADESH" in names:
            names = ["ARUNACHAL PRADESH", "NAGALAND", "MANIPUR"]
        rows.update(zip(names, (float(v.replace(",", "")) for v in numbers)))
    return rows


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                          capture_output=True, text=True).stdout


def prepare(directory, tg_path):
    paths = {name: directory / name for name in PINS}
    for name, path in paths.items():
        allowed = {PINS[name], JJM_RESEARCH_SHA} if name == "jjm" else {PINS[name]}
        if sha256(path.read_bytes()).hexdigest() not in allowed:
            raise ValueError(f"Unexpected edition of {path}")
    if sha256(tg_path.read_bytes()).hexdigest() != TG_SHA:
        raise ValueError(f"Unexpected edition of {tg_path}")
    html = HtmlRows()
    html.feed(paths["jjm"].read_text())
    jjm = parse_jjm(html.rows)
    tg = pdf_text(tg_path)
    urban = parse_urban(tg, 10)
    urban_counts = parse_urban(tg, 9)
    supply = parse_cea(pdf_text(paths["cea"]))
    gsdp = parse_gsdp(json.loads(paths["gsdp"].read_text()))
    gsdp["Delhi"] = (2025, parse_delhi(pdf_text(paths["delhi"])))
    gdp, growth = parse_gdp(pdf_text(paths["gdp"]))
    if len(urban) != 38 or len(urban_counts) != 38 or len(supply) != 36 or len(jjm) < 34:
        raise ValueError(f"Unexpected coverage: urban {len(urban)}/{len(urban_counts)}, CEA {len(supply)}, JJM {len(jjm)}")
    wage = parse_wage(pdf_text(paths["wage-schedule"]))
    if len(wage) != 31:
        raise ValueError(f"Unexpected statutory wage coverage: {len(wage)}")
    payloads = {
        "public_works_wage": (wage, "Effective 1 Jul 2026"),
        "public_works_wage_india": ({"India": parse_wage_average(paths["wage"].read_text())},
                                   "Effective 1 Jul 2026"),
        "plfs_q3": (parse_plfs(pdf_text(paths["plfs"])), "1 Jul – 30 Sep 2026"),
        "jjm_july": (jjm, "18 Jul 2026"),
        "tg_urban": ({"share": urban, "counts": urban_counts}, "1 Mar 2026"),
        "gsdp_fy26": (gsdp, "FY 2025-26 and estimate inputs"),
        "gsdp_components": (parse_gsdp_supplement(paths["gsdp-mirror"].read_text()), "October 2026 edition"),
        "gdp_fy26": ({"crore": gdp, "growth": growth}, "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"),
        "cea_fy26": (supply, "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"),
    }
    for key, (data, vintage) in payloads.items():
        save_interim(key, data, vintage=vintage)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))
