"""Audit the eight Varanasi village-directory block totals before deriving grazing share."""

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

from ..core.store import save_interim
from .historical_sources import VILLAGE_LAND_PERIOD, VILLAGE_LAND_SHA256, VILLAGE_LAND_SOURCE


def grazing_share(areas, land_use):
    if not areas or areas.keys() != land_use.keys():
        raise ValueError("Village area and land-use totals must cover the same blocks")
    for block, area in areas.items():
        used, grazing = land_use[block]
        if area <= 0 or not 0 <= grazing <= used or abs(used - area) > area * .002:
            raise ValueError(f"Inconsistent village land-use reporting in block {block}")
    return sum(grazing for _, grazing in land_use.values()) / sum(areas.values())


def varanasi_share(text):
    areas, land_use = {}, {}
    for page in text.split("\f"):
        block = re.search(r"Name of CD Block:.*?Location CodeNo:-(\d+)", page)
        total = re.search(r"Block T O T A L :([^\n]+)", page)
        if not (block and total):
            continue
        values = total[1].split()
        if "Total area of the village" in page:
            areas[block[1]] = float(values[0])
        if "Permanent Pastures and Other Grazing Lands" in page:
            # Columns 102 and 103 precede the nine exclusive area categories.
            categories = [float(value) for value in values[2:11]]
            if len(categories) != 9:
                raise ValueError(f"Incomplete area categories in block {block[1]}")
            land_use[block[1]] = (sum(categories), categories[3])
    if len(areas) != 8:
        raise ValueError("Expected all eight Varanasi blocks in the pinned handbook")
    return grazing_share(areas, land_use)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.report.read_bytes()).hexdigest() != VILLAGE_LAND_SHA256:
        raise ValueError(f"Unexpected handbook edition: {args.report}")
    text = subprocess.run(["pdftotext", "-layout", str(args.report), "-"], check=True,
                          capture_output=True, text=True).stdout
    save_interim(VILLAGE_LAND_SOURCE, {"09-197": {
        "value": round(varanasi_share(text), 8), "source": VILLAGE_LAND_SOURCE,
        "period": VILLAGE_LAND_PERIOD, "vintage": "older", "coverage": "Reporting rural villages",
    }})


if __name__ == "__main__":
    main()
