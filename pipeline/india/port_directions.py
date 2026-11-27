"""Derive FY 2024-25 overseas cargo direction shares from the pinned MoPSW report."""

import argparse
import hashlib
import re
import subprocess
from pathlib import Path
from .historical_sources import PORT_PERIOD as PERIOD, PORT_SHA256 as SHA256, PORT_SOURCE as SOURCE

from ..core.store import save_interim

MAJOR = {
    "SMPA Kolkata Dock": "kolkata", "SMPA Haldia Dock": "kolkata",
    "Paradip Port": "paradip", "Visakhapatnam Port": "visakhapatnam",
    "Kamarajar Port": "kamarajar", "Chennai Port": "chennai",
    "V.O. Chidambaranar Port": "chidambaranar", "Cochin Port": "cochin",
    "New Mangalore Port": "mangaluru", "Mormugao Port": "mormugao",
    "Jawahar Lal Nehru Port": "jnpa", "Mumbai Port": "mumbai",
    "Deendayal Port": "deendayal",
}
NON_MAJOR = {
    "Dahej": "dahej", "AHPPL (Magdala Adani Hazira Port)": "hazira", "Dhamra": "dhamra",
}
NON_MAJOR_SPLIT = NON_MAJOR | {
    "Krishnapatnam": "n3732668135", "Gangavaram": "r14718755",
    "Jakhau (Mandvi Jakhau)": "w1264420665", "Redi": "r15661798",
    "Dighi (Rajpuri)": "w1164626902", "Karanja": "w902549545",
    "Kattupali": "w369458014", "Gopalpur": "w684512907",
}
# Table 2.2.1 FY 2024-25 total overseas and coastal columns, in thousands of
# metric tonnes. The checksum-pinned PDF can independently validate this table.
NON_MAJOR_TOTALS = {
    "dahej": (32337, 3739),
    "w1264420665": (2617, 518),
    "hazira": (26231, 818),
    "r15661798": (510, 197),
    "w1164626902": (130, 255),
    "w902549545": (1306, 49),
    "n3732668135": (33492, 21499),
    "r14718755": (19672, 7293),
    "w369458014": (11215, 265),
    "dhamra": (37692, 8389),
    "w684512907": (5698, 297),
}
STATES = {
    "GUJARAT": "Gujarat", "MAHARASHTRA": "Maharashtra", "GOA": "Goa",
    "KARNATAKA": "Karnataka", "KERALA": "Kerala", "TAMIL NADU": "Tamil Nadu",
    "PONDICHERRY": "Puducherry", "ANDHRA PRADESH": "Andhra Pradesh",
    "ODISHA": "Odisha", "WEST BENGAL": "West Bengal", "ALL INDIA": "India",
}


def major_port_directions(report):
    records = {}
    for page in report.split("\f"):
        if not re.search(r"Table 2\.1\.3\b", page):
            continue
        for title, port in MAJOR.items():
            if title not in page:
                continue
            total = re.search(r"^\s*Total\s+((?:\d+\s+){17}\d+)\s*$", page, re.M)
            if total:
                unloaded, loaded = map(int, total[1].split()[12:14])
                previous = records.get(port, (0, 0))
                records[port] = (previous[0] + unloaded, previous[1] + loaded)
    return records


def non_major_port_directions(report):
    records = {}
    for page in report.split("\f"):
        if not re.search(r"Table 2\.2\.1\b", page):
            continue
        for line in page.splitlines():
            columns = re.split(r"\s{2,}", line.strip())
            port = NON_MAJOR.get(columns[0])
            if port and len(columns) == 19:
                records[port] = tuple(map(int, columns[13:15]))
    return records


def non_major_cargo_record(overseas, coastal):
    domestic = round(coastal / (overseas + coastal), 8)
    return dict(domestic=domestic, foreign=round(1 - domestic, 8),
                domestic_tonnes=coastal * 1000, foreign_tonnes=overseas * 1000,
                period=PERIOD, vintage="older", source_id=SOURCE)


def non_major_cargo_shares(report):
    records = {}
    for page in report.split("\f"):
        if not re.search(r"Table 2\.2\.1\b", page):
            continue
        for line in page.splitlines():
            columns = re.split(r"\s{2,}", line.strip())
            port = NON_MAJOR_SPLIT.get(columns[0])
            if port and len(columns) == 19:
                overseas, coastal = int(columns[15]), int(columns[18])
                if overseas + coastal > 0:
                    records[port] = non_major_cargo_record(overseas, coastal)
    return records


def state_directions(report):
    directions = [{}, {}]
    for page in report.split("\f"):
        table = re.search(r"Table 3\.1\.([34])\b", page)
        if not table:
            continue
        rows = directions[int(table[1]) - 3]
        state = None
        for line in page.splitlines():
            name = line.strip().rstrip(chr(96)).rstrip()
            if name in STATES:
                state = STATES[name]
            elif name in {"SEA-ISLAND", "SEA-ISLANDS"}:
                state = None
            elif state and re.fullmatch(r"Overseas(?:\s+\d+)+", name):
                rows[state] = int(name.split()[-1])
                state = None
    unloaded, loaded = directions
    return {state: (value, loaded[state]) for state, value in unloaded.items() if state in loaded}


def shares(records):
    return {
        key: dict(unloaded=round(unloaded / (loaded + unloaded), 8),
                  loaded=round(loaded / (loaded + unloaded), 8), period=PERIOD,
                  vintage="older", source_id=SOURCE)
        for key, (unloaded, loaded) in records.items() if unloaded + loaded > 0
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    pdf = parser.parse_args().pdf
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != SHA256:
        parser.error("The PDF does not match the pinned Basic Port Statistics edition")
    report = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    ports = major_port_directions(report) | non_major_port_directions(report)
    states = state_directions(report)
    if set(ports) != set(MAJOR.values()) | set(NON_MAJOR.values()) or set(states) != set(STATES.values()):
        parser.error("The report does not contain all expected overseas cargo rows")
    splits = non_major_cargo_shares(report)
    if splits != {key: non_major_cargo_record(*totals) for key, totals in NON_MAJOR_TOTALS.items()}:
        parser.error("The PDF port cargo splits differ from the build transcription")
    save_interim(SOURCE, {"ports": shares(ports), "states": shares(states)}, vintage=PERIOD)


if __name__ == "__main__":
    main()
