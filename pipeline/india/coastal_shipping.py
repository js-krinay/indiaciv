"""Prepare relative bands from table 7 of the January 2026 DGMA report."""

import argparse
import hashlib
import math
import re
import subprocess
from pathlib import Path

from ..core.store import save_interim
from .transport_analogue_sources import DGMA_CHECKSUM as CHECKSUM, DGMA_ID as SOURCE

DISPLAY_VERSION = 1

# Report order, exact atlas facility IDs and commodity presence. None identifies
# entries whose published endpoint lacks an exact match in the atlas inventory.
ENDPOINTS = [
    (("paradip",), ("kamarajar",), ("coal", "pol", "iron_ore")),
    (("paradip",), ("n3732668135",), ("coal", "pol", "iron_ore", "fertilizers")),
    (("paradip",), ("chidambaranar",), ("coal", "pol")),
    (("paradip", "visakhapatnam", "dhamra", "r14718755"), ("mumbai",), ("iron_ore",)),
    (("paradip",), ("hazira",), ("iron_ore",)),
    None,  # Vadinar and Sikka
    (("paradip",), ("mormugao",), ("coal", "pol", "iron_ore")),
    (("dhamra",), ("kamarajar",), ("coal",)),
    None,  # Vadinar
    (("paradip",), ("n3732746853",), ("coal", "pol")),
    (("mumbai",), ("mangaluru",), ("pol",)),
    (("mumbai",), ("mormugao", "hazira", "dahej"), ("pol",)),
    (("deendayal",), ("cochin",), ("container", "pol")),
    (("cochin",), ("kamarajar",), ("pol",)),
    (("paradip",), ("mumbai",), ("coal", "pol", "iron_ore", "fertilizers", "steel")),
    (("paradip",), ("karaikal",), ("coal", "iron_ore")),
    None,  # Andaman & Nicobar Islands is not an identified port group
    None,  # Pipavav
    (("r14718755",), ("chidambaranar",), ("coal",)),
    (("paradip",), ("w658557382",), ("coal",)),
]


def relative_band(low, high, reference, *, same_entry):
    if same_entry:
        return "100% (reference entry)"
    ref_low, ref_high = reference
    lower = 25 * math.floor(4 * low / ref_high)
    upper = 25 * math.ceil(4 * high / ref_low)
    if lower == 0 and low > 0:
        return f"Above 0% to {upper}%"
    return f"{lower}–{upper}%"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != CHECKSUM:
        raise ValueError(f"Unexpected SHA-256 for {args.pdf.name}")
    text = subprocess.check_output(["pdftotext", "-layout", str(args.pdf), "-"], text=True)
    table = text.split("Table 7: Top 20 OD pairs of coastal shipping in India (by cargo volume)")[-1]
    bands = [tuple(map(float, pair)) for pair in re.findall(
        r"\b(\d+(?:\.\d+)?)–(\d+(?:\.\d+)?)\b", table.split("Source:", 1)[0])]
    if len(bands) != len(ENDPOINTS):
        raise ValueError("Expected one volume interval per DGMA table 7 entry")
    rows = []
    for order, (endpoint, (low, high)) in enumerate(zip(ENDPOINTS, bands), 1):
        if endpoint is not None:
            a, b, commodities = endpoint
            rows.append([order, a, b, relative_band(low, high, bands[0], same_entry=order == 1), commodities])
    save_interim(SOURCE, {"reported_entries": len(ENDPOINTS), "rows": rows, "display_version": DISPLAY_VERSION})


if __name__ == "__main__":
    main()
