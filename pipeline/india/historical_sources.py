"""Pinned source references for workplace and overseas cargo observations."""

from ..core.source import SourceInfo

VILLAGE_LAND_SOURCE = "orgi_varanasi_village_land"
VILLAGE_LAND_PERIOD = "Village Directory land use as in 2009"
VILLAGE_LAND_SHA256 = "206a463c9b6ebad44d376d76295f7b00ee7a1cfe8d6f931bfd62b3fe53524193"
VILLAGE_LAND_INFO = SourceInfo(
    VILLAGE_LAND_SOURCE, "Varanasi District Census Handbook Part A, Village Directory", "ORGI",
    "https://censusindia.gov.in/nada/index.php/catalog/1300/download/4214/DH_2011_0966_PART_A_DCHB_VARANASI.pdf",
    "ORGI copyright policy. Attributed derived shares only.",
    "Sum permanent pasture and other grazing land across eight reporting rural blocks and divide by their "
    f"reported village area. Audit the nine exclusive land-use categories. PDF SHA-256 {VILLAGE_LAND_SHA256}.",
    ["District Explorer grazing land share"],
    license_url="https://censusindia.gov.in/census.website/en/node/286",
)

WORKPLACE_SOURCE = "shrug_workplace"
WORKPLACE_PERIOD = "Sixth Economic Census (January 2013 – April 2014)"
WORKPLACE_LICENSE = "CC BY-NC-SA 4.0"
WORKPLACE_LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
UA_URL = "https://censusindia.gov.in/nada/index.php/catalog/45261"
INDEX_URL = "https://www.devdatalab.org/shrug_download/data"
INPUTS = {
    "ec13.zip": "bcdac88c4e9f1101dd5f4c500d6d4c04d56953d35aca2c4ef9f0be74dcc4db22",
    "keys.zip": "e2d606c990d92ba8cedf207d2859162bcadde83a38917553bf23c83c1f5d660e",
    "shric.zip": "09b2c6b5574e4ef9e48a6c844917d6b25e6d5d45bd0c9fa43d046511569e8f2c",
    "ua.xlsx": "c38d96e0d1bd027ab141cd13a14d45f6410e72d90fbff8880941c62afce04c72",
}

PORT_SOURCE = "mopsw_basic_ports_2025"
PORT_URL = "https://shipmin.gov.in/sites/default/files/BPS%202024-25_compressed.pdf"
PORT_SHA256 = "c443531e8b7acd3d6912b25b99c97b2b2388fcba9d18d60123e2513fcd76e478"
PORT_PERIOD = "FY 2024-25 (1 Apr 2024 – 31 Mar 2025)"
