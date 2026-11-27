"""Provenance for the locally prepared protected-land snapshots."""

from pathlib import Path

from ..core.source import SourceInfo

MANIFEST = Path(__file__).with_name("protected_land_sources.json")
PERIODS = {
    "rsis_protected": "October 2026 list",
    "wii_protected": "February 2025 inventory",
    "ntca_protected": "November 2026 register",
    "osm_protected": "November 2026 snapshot",
    "wikidata_protected": "November 2026 snapshot",
}

SOURCES = [
    SourceInfo(
        "rsis_protected", "RSIS map services", "Secretariat of the Convention on Wetlands",
        "https://rsis.ramsar.org/", "CC BY 4.0",
        "Published wetland locations, areas and available boundaries on the October 2026 India list.",
        ["Protected land"], "https://www.ramsar.org/licence-information",
        "data/protected_ramsar.json", "Download RSIS-derived data (CC BY 4.0)",
    ),
    SourceInfo(
        "wii_protected", "National Parks inventory", "Wildlife Institute of India / MoEFCC",
        "https://wii.gov.in/envis/database.html", "Designation and area facts",
        "National park identities and notified extent facts from the February 2025 inventory used for the November 2026 map.",
        ["Protected land", "Wonders"], "https://v1.wii.gov.in/copyright_policy",
    ),
    SourceInfo(
        "ntca_protected", "Tiger Reserves register", "National Tiger Conservation Authority",
        "https://ntca.gov.in/tiger-reserves/", "Designation and area facts",
        "Tiger reserve identities and published total areas from the 58-reserve register available in November 2026.",
        ["Protected land"], "https://redirect.ntca.gov.in/website-policy",
    ),
    SourceInfo(
        "osm_protected", "OpenStreetMap protected areas", "© OpenStreetMap contributors",
        "https://www.openstreetmap.org/", "ODbL 1.0",
        "Matched protection boundaries and fallback locations. Explorer coverage is derived from these boundaries "
        "and RSIS boundaries intersected with DataMeet administrative polygons.",
        ["Protected land", "Explorer"], "https://www.openstreetmap.org/copyright",
        "data/protected_land.json", "Download OSM-derived data (ODbL)",
    ),
    SourceInfo(
        "wikidata_protected", "Wikidata protected-area locations", "Wikidata contributors",
        "https://www.wikidata.org/", "CC0 1.0",
        "Reviewed coordinate claims used for point markers where an OSM match was unavailable.",
        ["Protected land"], "https://www.wikidata.org/wiki/Wikidata:Licensing",
    ),
]
