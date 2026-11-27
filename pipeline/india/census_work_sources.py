"""Provenance for the Census 2011 occupation and industry shares."""

import json
from pathlib import Path

from ..core.source import SourceInfo
from .census_civic_sources import CENSUS_URL, POLICY_URL
from .orgi import Workbook

INTERIM = "census_work"
CULTIVATION_INTERIM = "orgi_cultivation_pca"
CULTIVATION_SOURCE = CULTIVATION_INTERIM
PCA_WORKBOOK = Workbook("DDW_PCA0000_2011_Indiastatedist.xlsx",
                        "7a8f70d46c43b5dd30eefe920f251752f69f6af8589594c21ac06499074646f5", "PC11_PCA-SD")
PCA_SOURCE = SourceInfo(CULTIVATION_SOURCE, "Census 2011 · Primary Census Abstract, PCA SD",
                        "Office of the Registrar General & Census Commissioner, India",
                        f"{CENSUS_URL}/catalog/6191", "ORGI copyright policy · attributed derived measures only",
                        "Cultivators and agricultural labourers among main and marginal workers divided by all urban "
                        "workers in the historic district. Urban member-district observations use the sum of "
                        f"Census worker counts before division. Workbook SHA-256 {PCA_WORKBOOK.checksum}.",
                        ["Explorer city and district cultivation shares"], license_url=POLICY_URL)


def workbook_manifest():
    return json.loads(Path(__file__).with_name("census_work_workbooks.json").read_text())


SOURCES = [
    SourceInfo("orgi_work_occupations", "Census 2011 · B-25 A and B",
               "Office of the Registrar General & Census Commissioner, India",
               f"{CENSUS_URL}/catalog/13684", "ORGI copyright policy · attributed derived measures only",
               "Combines main and marginal workers in mutually exclusive NCO-2004 categories for urban member districts and compares shares with urban India.",
               ["Citizens", "Explorer"], license_url=POLICY_URL),
    SourceInfo("orgi_work_industries", "Census 2011 · B-18",
               "Office of the Registrar General & Census Commissioner, India",
               f"{CENSUS_URL}/catalog/43234", "ORGI copyright policy · attributed derived measures only",
               "Divides NIC-2008 industry counts by eligible urban member-district workers. "
               "Excludes 2029 (explosives), 2520 (weapons and ammunition), 2829 (military aircraft launching equipment), "
               "3011 (warships), 3030 (aircraft, spacecraft and missiles), 3040 (military vehicles), "
               "and 8422 (defence administration), covering 2,417,413 main and marginal workers nationwide in Census 2011. "
               "Also excludes the rest of group 842 and division 45. Hospital services (8610) and other specialist retail "
               "(4773) remain included because military activity is incidental to those classes.",
               ["Workforce"], license_url=POLICY_URL),
]
