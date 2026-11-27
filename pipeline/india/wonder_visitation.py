"""Prepare FY 2025-26 visit ranks from the Ministry of Tourism's Table 4.2.3."""

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

from ..core.store import save_interim

INTERIM = "wonder_visitation"
SOURCE = "wonders_asi"
PERIOD = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
SHA256 = "5911dac3a48fec71b1136e45fb0ddd3da3628a7c8e4bfe292b05d97d710ec526"

# Exact identities between the wonder inventory and this edition's serials.
MONUMENTS = {
    "whc-1711": 9, "whc-1502": 11, "whc-233": 17, "whc-231": 18, "whc-232": 19,
    "whc-922": 33, "whc-239": 44, "whc-241": 48, "whc-524": 62, "whc-243": 73,
    "whc-242": 76, "whc-244": 81, "whc-246": 94, "udayagiri-khandagiri": 95,
    "golconda-fort": 116, "charminar": 117, "whc-252": 120, "whc-251": 121,
    "whc-255": 123, "whc-927": 136,
}
COUNT = r"([\d,]+|[-–])"
ROW = re.compile(r"^ *(\d{1,3})\s+.*?" + (r"\s+" + COUNT) * 4
                 + r"(?:\s+(?:-?[\d.]+|[-–])){2}\s*$")


def ticketed_ranks(text, expected_rows=145):
    table = text.split("Table 4.2.3: Number of Visitors", 1)[1].split("Grand Total", 1)[0]
    totals = {}
    serials = set()
    for line in table.splitlines():
        match = ROW.fullmatch(line)
        if not match:
            continue
        serial = int(match[1])
        if serial in serials:
            raise ValueError(f"Duplicate monument at serial {serial}")
        serials.add(serial)
        visitors = match.group(4, 5)
        if all(value not in {"-", "–"} for value in visitors):
            totals[serial] = sum(int(value.replace(",", "")) for value in visitors)
    if serials != set(range(1, expected_rows + 1)):
        raise ValueError("Incomplete ASI monument cohort")
    ranks = {}
    previous_total = None
    for position, (serial, total) in enumerate(sorted(totals.items(), key=lambda item: -item[1]), 1):
        if total != previous_total:
            rank = position
        ranks[serial] = rank
        previous_total = total
    return ranks, len(totals)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.report.read_bytes()).hexdigest() != SHA256:
        raise ValueError(f"Unexpected report edition: {args.report}")
    text = subprocess.run(["pdftotext", "-layout", str(args.report), "-"], capture_output=True,
                          check=True, text=True).stdout
    ranks, size = ticketed_ranks(text)
    save_interim(INTERIM, {"ranks": {key: ranks[serial] for key, serial in MONUMENTS.items()}, "size": size})


if __name__ == "__main__":
    main()
