"""Source pins and public display terms for transport analogues."""

from ..core.source import SourceInfo

AAI_ID = "aai_march_2026_traffic"
AAI_TRAFFIC_URL = "https://www.aai.aero/sites/default/files/traffic-news/"
AAI_REPORTS = {
    "III": ("Mar2k26Annex3_0.pdf", "cf694f01fc623695298beb51aa09444f6131f6246792ee2a7e85c0b7f50e05b0"),
    "IV": ("Mar2k26Annex4.pdf", "41de21ac38cf1d38e9ec64f562625e54a65a8ed546155a0435bf10a459543cf3"),
}

DGMA_ID = "dgma_coastal_shipping_fy25"
DGMA_URL = "https://dgma.gov.in/download/1769691524_697b598415456_coastal-committee-report-final-jan2026.pdf"
DGMA_CHECKSUM = "73ca2533cdd30725f995a2f722b04680dd0bb7215350fb91e90783bed9ab7311"

SOURCES = [
    SourceInfo(
        AAI_ID, "March 2026 Traffic News, Annexures III and IV", "Airports Authority of India",
        AAI_TRAFFIC_URL + AAI_REPORTS["III"][0],
        "AAI requires permission for table reproduction. IndiaCiv publishes attributed derived shares and growth.",
        "Domestic plus international totals for FY 2025-26 (1 Apr 2025 – 31 Mar 2026) and "
        "FY 2024-25 (1 Apr 2024 – 31 Mar 2025). PDF SHA-256: "
        + "; ".join(f"{file} {checksum}" for file, checksum in AAI_REPORTS.values()) + ".",
        ["Almanac airport traffic at 0.001 percentage-point display precision"],
        license_url="https://www.aai.aero/en/disclaimer",
    ),
    SourceInfo(
        DGMA_ID, "Coastal Shipping in India, January 2026, table 7", "Directorate General of Maritime Administration",
        DGMA_URL, "Public government report with no explicit open redistribution licence identified. "
        "The Almanac cites factual port relationships and independently calculated coarse categories. "
        "The Ministry website policy permits accurate credited reuse of its own site material and excludes third-party material.",
        f"Selected directed coastal entries for FY 2024-25 (1 Apr 2024 – 31 Mar 2025). PDF SHA-256 {DGMA_CHECKSUM}.",
        ["Almanac directed coastal relationships and coarse relative cargo categories"],
        license_url="https://shipmin.gov.in/en/footer/copyrightpolicy",
    ),
]
