"""Prepare the pinned ASI table locally for the Culture yield."""

import argparse
from hashlib import sha256
from pathlib import Path
import re
import subprocess

from ..core.store import save_interim
from .yield_sources import ASI_CHECKSUM, ASI_SOURCE

# Table 4.2.3 row number to the corresponding mapped wonder.
ROWS = {
    120: "whc-252", 94: "whc-246", 17: "whc-233", 18: "whc-231", 73: "whc-243",
    121: "whc-251", 116: "golconda-fort", 102: "whc-247", 95: "udayagiri-khandagiri", 19: "whc-232",
}
VALUES = re.compile(r"^\s*(\d+)\s+.*?((?:[\d,]+\s+){4})[-\d.]+\s+[-\d.]+\s*$")


def parse_entries(text):
    table = text.split("Table 4.2.3: Number of Visitors", 1)[1].split("Source: Archaeological Survey of India", 1)[0]
    entries = {}
    for line in table.splitlines():
        match = VALUES.match(line)
        if match and (row := int(match[1])) in ROWS:
            entries[ROWS[row]] = sum(int(value.replace(",", "")) for value in match[2].split()[2:])
    if entries.keys() != set(ROWS.values()):
        raise ValueError("ASI table 4.2.3 is missing selected monument rows")
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    if sha256(args.pdf.read_bytes()).hexdigest() != ASI_CHECKSUM:
        raise ValueError("ASI statistics PDF does not match the pinned edition")
    text = subprocess.check_output(["pdftotext", "-layout", str(args.pdf), "-"], text=True)
    save_interim(ASI_SOURCE, parse_entries(text), vintage="FY 2025-26 (1 Apr 2025 – 31 Mar 2026)")


if __name__ == "__main__":
    main()
