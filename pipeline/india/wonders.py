"""Import the locally supplied IC-8 wonder inventory."""
import argparse
import hashlib
import json
from pathlib import Path

from ..core.source import SourceInfo
from ..core.store import save_interim

SOURCE = "india_wonders"
CHECKSUM = "75c811f4e83e598622adf6a7dadf2b052f4c9fc9276a3966087bccb55d0ac376"
LICENSE = "CC BY-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"


CREDITS = [
    SourceInfo(
        SOURCE, "IndiaCiv wonder inventory (wonders.json)", "IndiaCiv",
        "https://whc.unesco.org/en/statesparties/in", LICENSE,
        "IC-8's original descriptions and selected locations, with UNESCO inscription status and IDs. "
        f"Snapshot SHA-256 {CHECKSUM}.",
        ["Wonders layer"],
    ),
    SourceInfo(
        "wonders_unesco", "World Heritage List core data", "UNESCO",
        "https://data.unesco.org/explore/dataset/whc001/", LICENSE,
        "Inscribed property status and IDs. Catalogue version 2026-11-22T03:08:00Z, extract SHA-256 "
        "198a717142a140913764fdcd2c6fa8cd2f2a7672a1b5e2b820e78738a2233f8c. "
        "Separately, UNESCO property maps and India's Tentative List provide factual location references.",
        ["World Heritage wonder selection"],
    ),
    SourceInfo(
        "wonders_asi", "India Tourism Statistics 2026, table 4.2.2", "Ministry of Tourism, Government of India",
        "https://www.tourism.gov.in/static/uploads/2026/09/a1ff37713ad3922f69778dca13aa65ab.pdf",
        "© 2026 Ministry of Tourism. No open licence identified.",
        "67th edition. FY 2025-26 domestic visits inform site selection. PDF SHA-256 "
        "5911dac3a48fec71b1136e45fb0ddd3da3628a7c8e4bfe292b05d97d710ec526.",
        ["Ticketed monument selection"],
    ),
    SourceInfo(
        "wonders_wikidata", "Wikidata coordinates", "Wikidata contributors",
        "https://www.wikidata.org/", "CC0 1.0",
        "Coordinates captured in the pinned November 2026 IC-8 inventory.",
        ["Wonder locations"],
    ),
    SourceInfo(
        "wonders_wikipedia", "Wikipedia coordinate references", "Wikipedia contributors",
        "https://en.wikipedia.org/", "CC BY-SA 4.0",
        "Coordinate references captured in the pinned November 2026 IC-8 inventory.",
        ["Wonder locations"],
    ),
    SourceInfo(
        "wonders_osm", "Dzukou Valley resthouse", "OpenStreetMap contributors via Mapcarta",
        "https://www.openstreetmap.org/copyright", "ODbL 1.0",
        "Single resthouse location used as the Nagaland-side anchor in the pinned IC-8 inventory.",
        ["Dzukou Valley location"],
    ),
    SourceInfo(
        "wonders_ramsar", "Ramsar Sites Information Service", "Convention on Wetlands",
        "https://rsis.ramsar.org/", "See publisher terms. Factual references.",
        "Wetland designations cross-referenced with the 21 April 2026 MoEFCC inventory.",
        ["Wetland selection"],
    ),
    SourceInfo(
        "wonders_gvp", "Barren Island, volcano 260010", "Smithsonian Global Volcanism Program",
        "https://volcano.si.edu/volcano.cfm?vn=260010", "See publisher terms. Factual references.",
        "Barren Island summit point and volcano classification in the pinned November 2026 IC-8 inventory.",
        ["Barren Island location"],
    ),
]


def read_snapshot(path: Path) -> dict:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CHECKSUM:
        raise ValueError(f"{path}: SHA-256 does not match the pinned IC-8 snapshot")
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    snapshot = read_snapshot(args.snapshot)
    save_interim(SOURCE, snapshot, vintage=snapshot["as_of"])


if __name__ == "__main__":
    main()
