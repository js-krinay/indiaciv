"""2026 projections from the Technical Group on Population Projections (MoHFW / National Commission on Population,
report of November 2019, base Census 2011): Table 21 (population by sex, 1 March 2011 and 2026, India and every
state and UT), and for India, 22 states and the North-East states excluding Assam (combined): Table T-17
(population characteristics: sex ratio, age shares, median age), Table 8 (annual population) and Table 17A
(health estimates interpolated to 2026). Table 18 is not
used: the report heads Uttarakhand's Table 18 "PUNJAB".

Needs `pdftotext` (poppler). Save the report as .cache/tg-projections-2019.pdf (see README) and run:
    python3 -m pipeline.india.projections .cache/tg-projections-2019.pdf
"""

from __future__ import annotations

import re
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

from pipeline.core.store import save_interim

URL = "https://nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf"
CHECKSUM = "9a9031c9c75d609e03ab94ce0ac6115cb9d8a9ab82d1b18a47b78e90ae01331b"
INDICATORS = {
    "Infant Mortality Rate (IMR)": "imr", "Total Fertility Rate (TFR)": "tfr",
    "Life expectancy of males": "life_male", "Life expectancy of females": "life_female",
}
# Table 8 persons columns, in their printed order, using the corresponding Table 21 names.
ANNUAL_UNITS = (
    "INDIA", "Jammu & Kashmir (UT)", "Himachal Pradesh", "Punjab", "Haryana", "NCT of Delhi",
    "Rajasthan", "Uttar Pradesh", "Bihar", "Assam", "West Bengal", "Jharkhand",
    "Odisha", "Chhattisgarh", "Madhya Pradesh", "Gujarat", "Maharashtra", "Andhra Pradesh",
    "Karnataka", "Kerala", "Tamil Nadu", "Chandigarh *", "Uttaranchal", "Sikkim",
    "Arunachal Pradesh", "Nagaland", "Manipur", "Mizoram", "Tripura", "Meghalaya",
    "Daman Diu", "Dadra & Nagar Haveli", "Goa", "Lakshadweep", "Puducherry",
    "Andaman & Nicobar Islands", "Telangana", "Ladakh",
)
NUM = r"[\d,]+"
ROW21 = re.compile(rf"^\s*(?:\d\d\s+)?(.*?[A-Za-z].*?)\s{{2,}}((?:{NUM}\s+){{8}}{NUM})\s*$")  # 3 years × P, M, F
# T-17 rows (section, label) → key; the 2026 value is the 4th of 2011, 2016, 2021, 2026, 2031, 2036.
PROFILE = {
    ("population", "Total"): "population", (None, "Sex Ratio"): "sex_ratio", ("percent", "0-14"): "age_0_14",
    ("percent", "60+"): "age_60", (None, "Median age (years)"): "median_age",
}
SECTIONS = {"Population (000')": "population", "Population by broad age-group": "ages", "Proportion (percent)": "percent",
            "Dependency Ratio": "dependency"}


def _int(s: str) -> int:
    return int(s.replace(",", ""))


def _heading(s: str) -> bool:
    """An all-capitals state heading such as "JAMMU & KASHMIR (UT)" or "INDIA" (a bracketed note may be mixed case:
    "NORTH-EAST STATES (Excluding Assam)")."""
    s = re.sub(r"\(.*?\)", "", s).strip()
    return s == s.upper() and bool(re.search(r"[A-Z]{3}", s)) and not s.startswith("TABLE") and not re.search(r"\d", s)


def parse(text: str) -> dict:
    population: dict[str, dict] = {}
    annual: dict[str, dict] = {}
    indicators: dict[str, dict] = {}
    profile: dict[str, dict] = {}
    table = year = name = section = annual_columns = None
    for line in text.splitlines():
        s = line.strip()
        if m := re.match(r"(?:TABLE|T)\s*[-–]\s*(\w+)", s, re.IGNORECASE):
            table, name, year, section = m.group(1), None, None, None
            annual_columns = None
            if table == "21":
                year = ("2026", "2031", "2036") if "contd" in s else ("2011", "2016", "2021")
            continue
        if s.startswith("Projected Population Characteristics"):  # T-17 (India's own marker is garbled in the PDF)
            table, name, section = "17", None, None
            continue
        if table == "8":
            cells = s.split()
            if cells and cells[0] == "1" and len(cells) in (7, 10) and all(c.isdecimal() for c in cells):
                annual_columns = [ANNUAL_UNITS[(int(c) - 2) // 3] for c in cells[1::3]]
            elif cells and cells[0] in ("2025", "2026") and annual_columns:
                if len(cells) != 1 + 3 * len(annual_columns):
                    raise ValueError(f"Table 8: malformed row {s}")
                for unit, total in zip(annual_columns, cells[1::3]):
                    annual.setdefault(unit, {})[cells[0]] = _int(total)
        elif table == "21" and (m := ROW21.match(line)):
            nums = [_int(v) for v in m.group(2).split()]
            row = population.setdefault(m.group(1).strip(), {})
            for k, y in enumerate(year):
                if y in ("2011", "2026", "2031"):
                    row[y] = nums[3 * k:3 * k + 3]
        elif table in ("17", "17A") and name is None and _heading(s):
            name = s.upper()
            if table == "17A":
                indicators.setdefault(name, {})
        elif table == "17A" and name:
            for label, key in INDICATORS.items():
                if s.startswith(label):
                    cells = s[len(label):].split()
                    if len(cells) == 5 and all(re.fullmatch(r"\d+(?:\.\d+)?", c) for c in cells[2:4]):
                        earlier, later = map(float, cells[2:4])
                        indicators[name][key] = round(earlier + (later - earlier) * (2026 - 2023) / (2028 - 2023), 5)
        elif table == "17" and name:
            section = next((v for k, v in SECTIONS.items() if s.startswith(k)), section)
            if s.startswith("Population (000')") and re.search(r"\d", s[17:]):
                s = "Total " + s[17:]  # Rajasthan's table puts the totals on the section line
            for (sec, label), key in PROFILE.items():
                rest = s[len(label):]
                if s.startswith(label) and (sec is None or sec == section) and re.match(r"\s+\d", rest):
                    v = float(re.findall(r"\d+\.?\d*", rest.replace(",", ""))[3])
                    profile.setdefault(name, {})[key] = int(v) if key in ("population", "sex_ratio") else v
    return {"population": population, "annual_population": annual, "indicators": indicators, "profile": profile}


def check(data: dict) -> None:
    """Fail loudly if the extraction drifted: every unit has 2011 and 2026, age totals equal Table 21's."""
    pop = data["population"]
    if len(pop) != 38 or any(set(v) != {"2011", "2026", "2031"} for v in pop.values()):
        raise ValueError(f"Table 21: expected India + 37 units with 2011, 2026 and 2031, got {len(pop)}")
    annual = data["annual_population"]
    if set(annual) != set(pop) or any(set(row) != {"2025", "2026"} or min(row.values()) <= 0 for row in annual.values()):
        raise ValueError("Table 8: expected positive 2025 and 2026 populations for all Table 21 units")
    for name, v in pop.items():
        if any(abs(p - m - f) > 2 for p, m, f in v.values()):
            raise ValueError(f"Table 21 {name}: persons ≠ males + females")
    by_upper = {k.upper().rstrip(" *").replace("UTTARANCHAL", "UTTARAKHAND"): v for k, v in pop.items()}
    for state, row in data["profile"].items():
        ref = by_upper.get(state)
        if ref and abs(row["population"] - ref["2026"][0]) > 2:
            raise ValueError(f"T-17 {state}: population {row['population']} ≠ Table 21 {ref['2026'][0]}")
        if set(row) != set(PROFILE.values()):
            raise ValueError(f"T-17 {state}: missing {set(PROFILE.values()) - set(row)}")
    if len(data["indicators"]) != 24 or set(data["profile"]) != set(data["indicators"]):
        raise ValueError(f"T-17/17A: {len(data['profile'])}/{len(data['indicators'])} blocks, expected the same 24")


if __name__ == "__main__":
    path = Path(sys.argv[1])
    if sha256(path.read_bytes()).hexdigest() != CHECKSUM:
        raise ValueError("Unexpected population projections report")
    data = parse(subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True).stdout)
    check(data)
    save_interim("tg_projections", data, vintage="Technical Group population projections (2019 report), 1 March 2026")
