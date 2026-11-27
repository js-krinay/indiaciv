"""Source catalogue and checked workbook manifest for the civic Census series."""

import json
from pathlib import Path

from ..core.source import SourceInfo

INTERIM = "census_civic"
CENSUS_URL = "https://censusindia.gov.in/nada/index.php"
POLICY_URL = "https://censusindia.gov.in/census.website/en/node/286"
PERIOD = "Census 2011"
TENURE_PERIOD = "Census 2011 Houselisting (2010)"

TABLES = {
    "commute": "B0128", "birthplace": "D0101", "education": "C2308", "postgrad": "C2408A",
    "religion": "C0101", "tenure": "HH1604", "young": "C3713",
}


def workbook_manifest():
    return json.loads(Path(__file__).with_name("census_civic_workbooks.json").read_text())


CATALOG = {
    "commute": ("B-28", 13981, "Divides each mode by all Other workers and finds the median published distance band among workers with stated distance."),
    "birthplace": ("D-01", 10692, "Divides each reported birthplace category by people enumerated in the same area."),
    "education": ("C-08", 44810, "Sums the Census age bands 25+ before dividing Indian attainment categories by people in those bands."),
    "postgrad": ("C-08 Appendix", 2414, "Sums the non-technical postgraduate category and population across age bands 25+ before dividing."),
    "religion": ("C-01", 11381, "Divides each reported religious community and unstated responses by all residents."),
    "tenure": ("HL-04", 8266, "Divides owned, rented and other tenure counts by households excluding institutional households."),
    "young": ("C-13", 1457, "Sums single years of age 18–34 and divides by all persons in the same area. "
              "Ladakh's historical median pools Leh and Kargil residents with stated ages."),
}

SOURCES = [
    SourceInfo(f"orgi_civic_{series}", f"Census 2011 · {name}",
               "Office of the Registrar General & Census Commissioner, India",
               f"{CENSUS_URL}/catalog/{catalog}", "ORGI copyright policy · attributed derived measures only",
               method, ["Citizens", "Explorer"] + ([] if series in {"young", "postgrad"} else ["Census civic lenses"]),
               license_url=POLICY_URL)
    for series, (name, catalog, method) in CATALOG.items()
]
