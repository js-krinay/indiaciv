"""Prepare period-labelled measures from pinned MoSPI household surveys."""

import argparse
import hashlib
import re
import subprocess
from datetime import datetime
from pathlib import Path
from statistics import median

from ..core.store import load_interim, save_interim
from .household_cost_sources import HCES, INTERIM, NFHS, PERIODS, PILOT, PILOT_INTERIM, POVERTY, RENT, REPORTS, TELECOM
from .people_metrics import HtmlRows

ALIASES = {
    "andaman & n. island": "Andaman & Nicobar",
    "a & n islands": "Andaman & Nicobar",
    "andaman and nicobar islands": "Andaman & Nicobar",
    "jammu and kashmir": "Jammu & Kashmir",
    "nct of delhi": "Delhi",
    "dadra & nagar haveli and daman & diu": "Dadra and Nagar Haveli and Daman and Diu",
    "all-india": "India",
}
FACT_SHEET = re.compile(r"^ *(.+?) - Key Indicators\s*$", re.M)
HEALTH_ROW = re.compile(r"^ *7\. Households with any usual member covered.*?\(%\) *(.*)$", re.M)

def table_rows(text, width):
    combined_ut = "Dadra & Nagar Haveli and Daman & Diu"
    text = re.sub(r"Dadra & Nagar\nHaveli & Daman &(.*)\nDiu", combined_ut + r"\1", text)
    text = re.sub(r"Dadra & Nagar Haveli\n(.*)\nand Daman & Diu", combined_ut + r"  \1", text)
    suffix = rf"(?:\s+[\d,]+(?:\.\d+)?){{{width}}}"
    rows = {}
    for line in text.splitlines():
        match = re.fullmatch(rf"\s*([A-Za-z][A-Za-z &.\-]*?)({suffix})\s*", line)
        if match:
            label, cells = match.groups()
            name = ALIASES.get(label.casefold(), label)
            if name in rows:
                raise ValueError(f"Duplicate survey geography {name}")
            rows[name] = [float(cell.replace(",", "")) for cell in cells.split()]
    return rows


def fixed_wifi(internet, fixed_among_connected):
    return round(internet * fixed_among_connected / 100, 4)


def sector_index(value, reference):
    return round(100 * value / reference, 2)


def rental_indexes(text):
    page, = [page for page in text.split("\f") if "Statement 24.5: Average monthly rent" in page]
    rows = table_rows(page, 3)
    excluded = {"Jammu & Kashmir", "Dadra & Nagar Haveli", "Daman & Diu", "Group of NE States", "Group of UTs"}
    return {
        f"rent_index_{sector}": {name: sector_index(cells[i], rows["India"][i])
                                 for name, cells in rows.items() if name not in excluded}
        for i, sector in enumerate(("rural", "urban", "all"))
    }


def health_financing(text):
    rows = {}
    for page in text.split("\f"):
        label = FACT_SHEET.search(page)
        match = HEALTH_ROW.search(page)
        if label and match:
            cells = match[1].split()
            if len(cells) == 4 and re.fullmatch(r"\d+\.\d+", cells[2]):
                name = ALIASES.get(label[1].casefold(), label[1])
                if name in rows:
                    raise ValueError(f"Duplicate factsheet geography {name}")
                rows[name] = round(100 - float(cells[2]), 1)
    return rows


def fact_sheet_pages(text):
    pages = {}
    for number, page in enumerate(text.split("\f"), 1):
        if label := FACT_SHEET.search(page):
            name = ALIASES.get(label[1].casefold(), label[1])
            pages.setdefault(name, number)
    return pages


def health_periods(text):
    periods = {}
    for page in text.split("\f"):
        if "Duration of Survey Fieldwork" not in page:
            continue
        lines = page.splitlines()[1:]
        names = " ".join(line[14:30].strip() for line in lines).split()
        names = " ".join(names).removeprefix("State Name ")
        dates = []
        for start, end in ((58, 77), (77, 94)):
            column = " ".join(line[start:end].strip() for line in lines)
            dates.append(re.findall(r"\b\d{1,2} [A-Za-z]+,\s+\d{4}\b", column))
        # A long state name wraps into subsequent lines within the state column.
        names = re.findall(
            r"Andaman and Nicobar Islands|Andhra Pradesh|Arunachal Pradesh|"
            r"Dadra & Nagar Haveli and Daman & Diu|Himachal Pradesh|Jammu & Kashmir|"
            r"Madhya Pradesh|Tamil Nadu|Uttar Pradesh|West Bengal|NCT of Delhi|[A-Z][a-z]+",
            names,
        )
        for name, start_date, end_date in zip(names, *dates, strict=True):
            start = datetime.strptime(start_date, "%d %B, %Y")
            end = datetime.strptime(end_date, "%d %B, %Y")
            if start > end:
                raise ValueError(f"Reversed NFHS-6 dates for {name}")
            name = ALIASES.get(name.casefold(), name)
            periods[name] = f"NFHS-6 ({start.day} {start:%b %Y} to {end.day} {end:%b %Y})"
    return periods


def extract_health_financing(path):
    text = report_text(path, NFHS)
    rates = health_financing(text)
    for name, page in fact_sheet_pages(text).items():
        if name in rates:
            continue
        # Some indicator tables in the pinned factsheets are raster images.
        image = subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "180", "-png",
                                "-x", "0", "-y", "50", "-W", "1500", "-H", "540", "-singlefile", str(path)],
                               check=True, capture_output=True).stdout
        extracted = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "6"], input=image,
                                   check=True, capture_output=True).stdout.decode()
        rows = health_financing(f"{name} - Key Indicators\n{extracted}")
        if name not in rows:
            raise ValueError(f"Missing NFHS-6 indicator 7 for {name} on page {page}")
        rates.update(rows)
    if len(rates) != 36:
        raise ValueError("Expected NFHS-6 coverage for 35 states/UTs and India")
    periods = health_periods(text)
    periods["India"] = PERIODS[NFHS]
    if periods.keys() != rates.keys():
        raise ValueError("NFHS-6 appendix and factsheets cover different geographies")
    return {name: {"value": rate, "period": periods[name]} for name, rate in rates.items()}


def poverty_indexes(rows):
    header = ["State", "Rural 2009-10", "Urban 2009-10", "Rural 2011-12", "Urban 2011-12",
              "Rural 2022-23", "Urban 2022-23"]
    start = rows.index(header) + 1
    estimates = {}
    aliases = {"Chattisgarh": "Chhattisgarh", "Uttar Prdesh": "Uttar Pradesh"}
    for row in rows[start:]:
        if len(row) != len(header):
            break
        name = row[0]
        if name not in {"Andhra Pradesh", "Jammu & Kashmir"}:
            estimates[aliases.get(name, name)] = [float(cell) for cell in row[-2:]]
    indexes = {}
    for i, sector in enumerate(("rural", "urban")):
        reference = median(values[i] for values in estimates.values())
        indexes[f"rangarajan_poverty_{sector}"] = {
            name: sector_index(values[i], reference) for name, values in estimates.items()
        }
    return indexes


def district_pilot(rows, districts, reference):
    aliases = {
        "Amroha": "Jyotiba Phule Nagar", "Badaun": "Budaun", "Bagpat": "Baghpat", "Balliya": "Ballia",
        "Barabanki": "Bara Banki", "Behraich": "Bahraich", "Bhadohi": "Sant Ravi Das Nagar(bhadohi)",
        "Gb Nagar": "Gautam Buddha Nagar", "Hathras": "Mahamaya Nagar", "Kasganj": "Kansiram Nagar",
        "Prayagraj": "Allahabad", "Sk Nagar": "Sant Kabir Nagar",
    }
    changed = {"Moradabad", "Budaun", "Muzaffarnagar", "Ghaziabad", "Sultanpur", "Rae Bareli"}
    unmapped = {"Sambhal", "Shamli", "Hapur", "Amethi"}
    names = {d["name"]: f"09-{d['code']:03d}" for d in districts if d["state_code"] == 9}
    start = rows.index(["District", "MPCE (Rural)", "MPCE (Urban)"]) + 2
    indexes = {}
    for row in rows[start:]:
        if len(row) != 5:
            break
        reported, _, rural, _, urban = row
        name = aliases.get(reported, reported)
        if reported in unmapped or name in changed:
            continue
        indexes[names[name]] = {
            "rural": sector_index(int(rural), reference[0]),
            "urban": sector_index(int(urban), reference[1]),
        }
    return indexes


def verified_bytes(path, source):
    contents = path.read_bytes()
    if hashlib.sha256(contents).hexdigest() != REPORTS[source][1]:
        raise ValueError(f"Unexpected report edition: {path}")
    return contents


def report_text(path, source):
    verified_bytes(path, source)
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                          capture_output=True, text=True).stdout


def extract(hces, telecom):
    measures = {}
    pages = hces.split("\f")
    for sector in ("rural", "urban"):
        suffix = sector[0].upper()
        page, = [page for page in pages if f"Statement 2{suffix}: Average MPCE over 12 fractile" in page]
        rows = table_rows(page, 13)
        reference = rows["India"][-1]
        measures[f"mpce_index_{sector}"] = {name: sector_index(cells[-1], reference)
                                           for name, cells in rows.items()}
    page, = [page for page in telecom.split("\f")
             if "Table 14: Percentage of households with internet facility" in page
             and re.search(r"\ball\s*\n\s+Percentage of", page)]
    rows = table_rows(page, 4)
    measures["fixed_wifi_households"] = {name: fixed_wifi(*cells[:2]) for name, cells in rows.items()}
    for key, values in measures.items():
        if len(values) != 37:
            raise ValueError(f"Expected 36 states/UTs and India for {key}, found {len(values)}")
    return measures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hces", type=Path)
    parser.add_argument("telecom", type=Path)
    parser.add_argument("rent", type=Path)
    parser.add_argument("nfhs", type=Path)
    parser.add_argument("poverty", type=Path)
    parser.add_argument("pilot", type=Path)
    args = parser.parse_args()
    hces = report_text(args.hces, HCES)
    measures = extract(hces, report_text(args.telecom, TELECOM))
    measures.update(rental_indexes(report_text(args.rent, RENT)))
    measures["no_household_health_financing"] = extract_health_financing(args.nfhs)
    html = HtmlRows()
    html.feed(verified_bytes(args.poverty, POVERTY).decode("utf-8"))
    indexes = poverty_indexes(html.rows)
    if any(len(values) != 18 for values in indexes.values()):
        raise ValueError("Unexpected RBI Table 3 reporting cohort")
    measures.update(indexes)
    html = HtmlRows()
    html.feed(verified_bytes(args.pilot, PILOT).decode("utf-8"))
    page, = [page for page in hces.split("\f") if "Table 3.2: Average MPCE and urban-rural differences" in page]
    rural, urban, *_ = table_rows(page, 6)["Uttar Pradesh"]
    pilot = district_pilot(html.rows, load_interim("datameet")["districts"], (rural, urban))
    if len(pilot) != 65:
        raise ValueError(f"Expected 65 boundary-compatible Uttar Pradesh districts, found {len(pilot)}")
    save_interim(PILOT_INTERIM, {
        "districts": {code: {**row, "source": PILOT, "period": PERIODS[PILOT], "vintage": "older"}
                      for code, row in pilot.items()},
    })
    save_interim(INTERIM, measures)


if __name__ == "__main__":
    main()
