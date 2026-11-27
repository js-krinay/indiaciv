"""Pinned facts used by the IndiaCiv yield proxies."""

from ..core.source import SourceInfo
from .science_sources import SOURCES as SCIENCE_SOURCES

FOODGRAINS = 378_538_000  # 3,785.38 lakh tonnes, final estimate

ASI_SOURCE = "asi_yield_entries"
ASI_CHECKSUM = "5911dac3a48fec71b1136e45fb0ddd3da3628a7c8e4bfe292b05d97d710ec526"

# Named destinations in the PRASHAD annex, excluding entries already counted as wonders.
PILGRIMAGE = [
    ("Annavaram Temple", 82.41, 17.28),
    ("Kamakhya Temple", 91.71, 26.17),
    ("Guruvayur Temple", 76.04, 10.59),
    ("Chamundeshwari Temple", 76.67, 12.27),
    ("Renuka Yallamma Temple", 75.12, 15.77),
    ("Papnash Temple", 77.50, 17.90),
    ("Dharbaranyeswara Temple", 79.80, 10.93),
]

SOURCES = [
    SourceInfo("foodgrains_fy26", "Final production estimates of major agricultural crops",
               "Ministry of Agriculture & Farmers Welfare / PIB",
               "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2342093&lang=2&reg=48",
               "PIB Copyright Policy (attributed, accurate reuse)",
               "Release 2342093 dated 26 Nov 2026. Crop year 2025-26 (1 Jul 2025 – 30 Jun 2026).",
               ["National foodgrain tonnage and IndiaCiv cropland allocation"]),
    SourceInfo(ASI_SOURCE, "India Tourism Statistics 2026, 67th edition, Tables 4.2.2–3",
               "Ministry of Tourism / Archaeological Survey of India",
               "https://www.tourism.gov.in/static/uploads/2026/09/a1ff37713ad3922f69778dca13aa65ab.pdf",
               "© 2026 Ministry of Tourism. Cited numeric facts used in the Culture proxy.",
               f"FY 2025-26 (1 Apr 2025 – 31 Mar 2026). SHA-256 {ASI_CHECKSUM}.",
               ["Ticketed entries at ten ASI monuments"]),
    SourceInfo("pilgrimage_sites", "PRASHAD named destination selection, February 2026 snapshot",
               "Ministry of Tourism / PIB",
               "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2226964&lang=1&reg=6",
               "PIB Copyright Policy (attributed, accurate reuse)",
               "Release 2226964 dated 12 Feb 2026, supplemented by the PRASHAD annex in releases 2205885 and 2196921. "
               "Site locations counted in the 27 Nov 2026 inventory.",
               ["Selected pilgrimage destinations"]),
    *SCIENCE_SOURCES,
]
