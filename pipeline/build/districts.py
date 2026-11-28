"""Dated workplace observations for the existing City View district caption."""

from ..core.source import SourceInfo


NIRF_PERIOD = "Through AY 2023-24"
NIRF_SHA256 = "af4fe5758cbe8df23c5b088a8bc6b79e1b3ebeb93f642d789e2fc29266227a63"
NIRF_INFO = SourceInfo(
    "nirf_rourkela_doctoral", "India Rankings 2025, NIT Rourkela SDG submission",
    "National Institute of Technology Rourkela / Ministry of Education",
    "https://www.nitrkl.ac.in/docs/Documents/Ranking/NIRF2025/SDG.pdf",
    "Attributed derived factual subtotal",
    "Doctoral enrolment through AY 2023-24 sums 1,042 full-time and 365 part-time students. "
    f"PDF SHA-256 {NIRF_SHA256}.",
    ["Explorer campus enrolment"],
)
LAND_USE_PERIOD = "26 November 2026"
COMMERCIAL_API = "https://api.openstreetmap.org/api/0.6/way/126018393/full.json"
COMMERCIAL_SHA256 = "f59340a9e9f5bcb02a101e6308e259325b3034ed92dafd786c7b89371496c37d"
COMMERCIAL_INFO = SourceInfo(
    "osm_maker_maxity", "OpenStreetMap Maker Maxity land-use polygon, way 126018393 v6",
    "© OpenStreetMap contributors", "https://www.openstreetmap.org/way/126018393/history",
    "Open Database Licence (ODbL) 1.0",
    f"Official API full-way response SHA-256 {COMMERCIAL_SHA256}. "
    "Way version and all geometry node versions predate the 26 November 2026 snapshot. The reviewed "
    "interior point verifies overlap with the mapped UA and a member district.",
    ["City View commercial land-use site"], license_url="https://www.openstreetmap.org/copyright",
)
# Both interior points are inside the tagged polygon and the matching urban footprint.
LAND_USE_SITES = {
    "ICD CONCOR Kanpur": {
        "kind": "industrial_land_use", "source": "osm_transport", "way": 148465218,
        "label": "Mapped industrial land-use site", "short_label": "Industry land use",
        "point": (80.30642625, 26.4553731375),
    },
    "Maker Maxity": {
        "kind": "commercial_hub", "source": COMMERCIAL_INFO.id, "way": 126018393,
        "label": "Mapped commercial land-use site", "short_label": "Commerce land use",
        "point": (72.84928220833334, 19.053272075),
    },
}


def site_observation(city_id, site):
    if city_id == "21387" and (site["kind"], site["name"], site["district"]) == ("campus", "NIT Rourkela", "21-374"):
        return {"label": "Reported doctoral enrolment", "value": 1042 + 365, "unit": "students",
                "period": NIRF_PERIOD, "vintage": "older", "source": NIRF_INFO.id, "hide_rank": True}
    return None
