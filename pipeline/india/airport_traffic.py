"""Prepare derived airport shares from AAI March 2026 annexures III and IV."""

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

from ..core.store import save_interim
from .transport_analogue_sources import AAI_ID as SOURCE, AAI_REPORTS as REPORTS

DISPLAY_VERSION = 1

# AAI total annexures publish names rather than IATA codes. Resolve exact printed
# facility names explicitly, including airports in cities with multiple facilities.
AAI_NAMES = {
    "AGX": "AGATTI", "AYJ": "AYODHYA", "BBI": "BHUBANESWAR", "BDQ": "VADODARA",
    "BHO": "BHOPAL", "BHU": "BHAVNAGAR", "BLR": "BENGALURU (BIAL)", "BOM": "MUMBAI (MIAL)",
    "CCJ": "KOZHIKODE", "CDP": "CUDDAPAH", "CJB": "COIMBATORE", "CNN": "KANNUR (KIAL)",
    "COK": "KOCHI", "DED": "DEHRADUN", "DGH": "DEOGHAR", "DMU": "DIMAPUR", "GAY": "GAYA",
    "GBI": "KALABURAGI (GULBARGA)", "GDB": "GONDIA", "GOX": "GOA (MOPA)", "HBX": "HUBBALI",
    "HGI": "ITANAGAR (HOLONGI)", "HJR": "KHAJURAHO", "HSR": "RAJKOT (HIRASAR)",
    "HYD": "HYDERABAD (GHIAL)", "IDR": "INDORE", "IMF": "IMPHAL", "IXE": "MANGALURU",
    "IXG": "BELAGAVI", "IXI": "LAKHIMPUR (LILABARI)", "IXK": "KESHOD (JUNAGARH)",
    "IXR": "RANCHI", "IXY": "KANDLA", "JAI": "JAIPUR", "JLG": "JALGAON", "JLR": "JABALPUR",
    "JRG": "JHARSUGUDA", "KJB": "KURNOOL", "KLH": "KOLHAPUR", "KQH": "KISHANGARH",
    "KUU": "BHUNTAR (KULLU MANALI)", "LKO": "LUCKNOW", "MAA": "CHENNAI", "MYQ": "MYSURU",
    "PAT": "PATNA", "PGH": "PANTNAGAR", "PNY": "PUDUCHERRY", "RJA": "RAJAHMUNDRY",
    "RPR": "RAIPUR", "SAG": "SHIRDI", "STV": "SURAT", "TCR": "TUTICORIN", "TIR": "TIRUPATI",
    "TRZ": "TIRUCHIRAPPALLI", "UDR": "UDAIPUR", "VGA": "VIJAYAWADA", "VNS": "VARANASI",
}


def report_totals(text, annexure):
    _, total = text.split(f"ANNEXURE-{annexure} C", 1)
    values = {}
    for line in total.splitlines():
        match = re.search(r"(Grand Total|[A-Z][A-Z ()./&'-]+?)\s+"
                          r"[\d.]+\s+[\d.]+\s+\S+\s+([\d.]+)\s+([\d.]+)\s+\S+\s*$", line)
        if match:
            name, current, previous = match.groups()
            name = " ".join(name.split())
            if name in values:
                raise ValueError(f"Duplicate airport name {name!r}")
            values[name] = float(current), float(previous)
    return values


def display_percent(fraction):
    percent = 100 * fraction
    if 0 < percent < 0.001:
        return "<0.001%"
    if -0.001 < percent < 0:
        return "<0.001% decrease"
    return f"{percent:.3f}%"


def airport_metrics(totals, names, *, passenger):
    national, previous_national = totals["Grand Total"]
    if national <= 0 or previous_national <= 0:
        raise ValueError("AAI national denominator must be positive")
    metrics = {}
    for code, name in names.items():
        if name not in totals:
            continue
        current, previous = totals[name]
        row = {"share": display_percent(current / national)}
        if passenger:
            row["previous_share"] = display_percent(previous / previous_national)
            if previous > 0:
                row["change"] = display_percent(current / previous - 1)
        metrics[code] = row
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory containing both pinned AAI PDFs")
    args = parser.parse_args()
    series = {}
    for annexure, (filename, checksum) in REPORTS.items():
        path = args.directory / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise ValueError(f"Unexpected SHA-256 for {filename}")
        text = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)
        passenger = annexure == "III"
        series["passengers" if passenger else "freight"] = airport_metrics(
            report_totals(text, annexure), AAI_NAMES, passenger=passenger)
    save_interim(SOURCE, dict(series, display_version=DISPLAY_VERSION))


if __name__ == "__main__":
    main()
