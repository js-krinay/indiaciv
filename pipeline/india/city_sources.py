"""Source and qualitative evidence registry for City View."""

from ..core.source import SourceInfo

AGE_SOURCE = "city_worldpop_age"
AGE_API_SOURCE = "city_worldpop_age_api"
DISTRICT_AGE_SOURCE = "district_worldpop_age"
AGE_RELEASE = "R2025A v1"
HEX_GEOGRAPHY = "_hex_geography"
AGE_API_URL = "https://api.worldpop.org/v3/agesex"
LABOUR_SOURCE = "plfs_2026_q3"
LABOUR_PERIOD = "1 Jul – 30 Sep 2026"
LABOUR_URL = ("https://mospi.gov.in/uploads/publications_reports/publications_reports1794297172776"
              "_05eae330-7f2d-45ec-84c5-07031201ecf1_PLFS_QB_July-Sept_2026_m.pdf")
LABOUR_SHA256 = "16fee8073720fedff1f4fcfed661faf702f655fd7aeaf3585aadba276c8a083a"
ANNUAL_LABOUR_SOURCE = "plfs_annual_2025"
ANNUAL_LABOUR_PERIOD = "PLFS 2025"
ANNUAL_LABOUR_SHA256 = "134bf2de5e4b1142d3bae4899c90ec5be3bf5ec03a2ff4b3f7b0bba34eee0da7"
ANNUAL_LABOUR_URL = ("https://www.mospi.gov.in/uploads/publications_reports/"
                     "publications_reports1780040415321_0624fb13-fb47-40bc-b470-7c7e9635c3ef_PLFS_2025_F_REV_29052026.pdf")
ANNUAL_LABOUR_METHOD = ("IndiaCiv estimate: multiply 2026 resident population by the Annual PLFS 2025 all-age "
                       "CWS worker-population ratio, using the state/UT rate for states and its urban rate for cities.")
ANNUAL_LABOUR_INFO = SourceInfo(
    ANNUAL_LABOUR_SOURCE, "Annual Periodic Labour Force Survey 2025, revised May 2026", "NSO / MoSPI", ANNUAL_LABOUR_URL,
    "MoSPI Category A published aggregates with attribution",
    f"{ANNUAL_LABOUR_PERIOD} (1 Jan 2025 – 31 Dec 2025). Appendix A Tables 1 and 31–33. "
    f"{ANNUAL_LABOUR_METHOD} Unemployment rates are 15+ benchmarks. "
    f"Industry shares describe CWS workers in the published survey universe. SHA-256 {ANNUAL_LABOUR_SHA256}.",
    ["Residents and work"],
)
PIB = "https://www.pib.gov.in/PressReleasePage.aspx?PRID="
PIB_TERMS = "PIB copyright policy: credited, accurate reuse of government material."
FY26 = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"

GOVERNMENT_SITE_SOURCE = "wikidata_government_sites"
GOVERNMENT_SITES = {
    "DL": ("Central Secretariat", 77.205833, 28.615, "Q15275798", 2469898092),
    "KA": ("Vidhana Soudha", 77.590556, 12.979722, "Q283257", 2459550822),
    "WB": ("West Bengal Legislative Assembly", 88.344219, 22.566769, "Q108598529", 2276383252),
}
GOVERNMENT_SITE_INFO = SourceInfo(
    GOVERNMENT_SITE_SOURCE, "Reviewed civilian government building locations", "Wikidata contributors",
    "https://www.wikidata.org/", "CC0",
    "November 2026 inventory. P625 facility coordinates from pinned Wikidata item revisions: "
    + ", ".join(f"{item} (oldid {rev})" for _, _, _, item, rev in GOVERNMENT_SITES.values()) + ".",
    ["City View Government Plaza"], license_url="https://creativecommons.org/publicdomain/zero/1.0/",
)

# The district IDs are reviewed against the frozen footprint. A badge describes
# the named economic cluster in its city or district, without locating a site.
CLUSTER_REPORTS = {
    "stpi_2026": ("STPI IT Export Awards", "MeitY / STPI", "17 Nov 2026", PIB + "2337647", [
        ("21176", "29-572", "software", "Software and IT",
         "Bengaluru hosts STPI’s main Karnataka centre and its software export ecosystem."),
    ]),
    "footwear_2026": ("QCI–FDDI leather and footwear partnership", "Ministry of Commerce & Industry",
                      "12 Jun 2026", PIB + "2272310", [
        ("21296", "09-164", "footwear", "Leather and footwear", "QCI and FDDI identify Kanpur as a footwear cluster."),
        ("21151", "09-146", "footwear", "Leather and footwear", "QCI and FDDI identify Agra as a footwear cluster."),
        ("21321", "33-603", "footwear", "Leather and footwear", "QCI and FDDI identify Chennai as a footwear cluster."),
        ("21313", "32-592", "footwear", "Leather and footwear", "QCI and FDDI identify Kozhikode as a footwear cluster."),
    ]),
    "south_gujarat_2026": ("Vibrant Gujarat Regional Conference, South Gujarat", "PIB Ahmedabad",
                           "2 May 2026", PIB + "2257570", [
        ("21412", "24-492", "diamond", "Diamond processing", "The conference identifies Surat as a global diamond industry hub."),
        ("21412", "24-492", "textile", "Textiles", "The conference identifies Surat as a global textile industry hub."),
    ]),
    "pune_industry_2026": ("Pune Metro inauguration", "Prime Minister’s Office",
                           "3 Nov 2026", PIB + "2332011", [
        ("21371", "27-521", "automotive", "Automotive", "The Prime Minister identifies automobiles as a Pune industry strength."),
    ]),
    "steel_zones_2026": ("Major steel zones and logistics infrastructure", "Ministry of Steel",
                         "May 2026", "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/may/doc202655864101.pdf", [
        ("21286", "20-357", "steel", "Steelmaking", "The Ministry of Steel identifies Jamshedpur as a major steel zone."),
    ]),
    "bharat_tex_2026": ("Bharat Tex cluster showcase", "Ministry of Textiles", "Jul 2026", PIB + "2280341", [
        ("21152", "24-474", "textile", "Textiles", "Bharat Tex identifies Ahmedabad’s textile cluster."),
    ]),
    "tiruppur_knitwear_2026": ("Districts as Export Hubs (2 Sep 2026)", "Press Information Bureau",
                             FY26, "https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=159804&lang=1&reg=3", [
        ("21420", "33-633", "textile", "Knitwear", "PIB identifies Tiruppur as a major centre for knitwear exports."),
    ]),
    "upeida_lucknow_cluster": (
        "UPEIDA Lucknow cluster inventory", "Uttar Pradesh Expressways Industrial Development Authority",
        "27 Nov 2026", "https://upeida.up.gov.in/updic/en/page/land-banks", [
            ("21318", "09-157", "textile", "Lucknow Chikankari Cluster",
             "UPEIDA lists the embroidery cluster among existing Lucknow MSME clusters."),
        ]),
}

CLUSTER_SOURCES = [
    SourceInfo(id=key, title=title, publisher=publisher,
               homepage=url, license=("Publisher copyright retained. Factual cluster attribution only."
                                      if key == "upeida_lucknow_cluster" else PIB_TERMS),
               description="Qualitative plaques require a named city or district in dated government evidence "
               "and a reviewed link to a City View member district. Up to five plaques per city."
               + (" 27 Nov 2026 HTML SHA-256 ff4df4348d4e0e0f69b58c30e82c4876eb531f94d7a7a3d0ad167d85cde8e011."
                  if key == "upeida_lucknow_cluster" else ""),
               used_for=["City View industry specialisations"],
               license_url=None if key == "upeida_lucknow_cluster"
               else "https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=19&reg=48")
    for key, (title, publisher, _, url, _) in CLUSTER_REPORTS.items()
]

CITY_PEOPLE_SOURCES = [
    SourceInfo(id=DISTRICT_AGE_SOURCE, title=f"WorldPop age and sex, 1 km · {AGE_RELEASE}", publisher="WorldPop",
               homepage="https://doi.org/10.5258/SOTON/WP00842", license="CC BY 4.0",
               description="IndiaCiv sums both sexes at the centres of the 2026 constrained grid cells inside "
               "DataMeet atlas districts and interpolates uniformly within the age band crossing half the population. "
               "Overlapping district pixels are assigned once in atlas code order.",
               used_for=["Explorer district median age"]),
    SourceInfo(id=AGE_SOURCE, title=f"WorldPop age and sex, 1 km · {AGE_RELEASE}", publisher="WorldPop",
               homepage="https://doi.org/10.5258/SOTON/WP00842", license="CC BY 4.0",
               description="IndiaCiv estimates sum male and female 2026 age counts at pixel centres within "
               "each clipped GHSL footprint, then scale three age groups to the mid-2026 UN city total "
               "by largest remainders. City View displays the age band containing the median. In hex and state gaps, "
               "IndiaCiv estimates interpolate the median within that band over Indian land with at least 80% valid "
               "pixel centres in every raster.",
               used_for=["City View age groups, median age band and age 15+ denominator", "Hex and state median age"]),
    SourceInfo(id=AGE_API_SOURCE, title="WorldPop Global2 R2025A · API v3 age and sex",
               publisher="WorldPop · University of Southampton",
               homepage="https://api.worldpop.org/v3/documentation", license="CC BY 4.0",
               description="WorldPop sums its 2026 100 m population grid inside the clipped city footprint "
               "and applies WorldPop administrative-unit age and sex shares. IndiaCiv scales the returned "
               "age distribution to the mid-2026 UN city total by largest remainders.",
               used_for=["City View age groups, median age band and age 15+ denominator"]),
    SourceInfo(id=LABOUR_SOURCE, title="Periodic Labour Force Survey · Jul–Sep 2026", publisher="NSO / MoSPI",
               homepage=LABOUR_URL, license="MoSPI Category A published aggregates, with source credit.",
               description="IndiaCiv estimates multiply the UN total and WorldPop-based 15+ population by "
               "the matching state urban worker-population ratios. Multi-state cities apply the city adult age "
               "share uniformly across footprint fragments and require published rates for all fragments. "
               "Urban industry shares weight adult worker counts and icons. Multi-state unemployment uses "
               "estimated labour-force weights. For Explorer, Table 4 reports rural+urban persons "
               "age 15+ under Current Weekly Status: agriculture sector (NIC-2008 codes 01–03), secondary sector "
               "along with mining and quarrying (05–43), and tertiary sector (45–99). "
               "State employed residents are estimated by applying the combined all-ages worker-population "
               "ratio in Table 3 to the projected 1 March 2026 population. State panel industry counts "
               "allocate estimated workers age 15+ (projected 1 March residents age 15+ times the matching "
               "worker-population ratio) by the quarterly Table 4 shares. Where the quarter is unavailable, "
               "the panel allocates projected all-age employment using the annual PLFS 2025 industry shares. "
               "The national urban unemployment benchmark is the all-India urban persons rate, age 15+. "
               f"Appendix A Tables 3–5. SHA-256 {LABOUR_SHA256}.",
               used_for=["City View employed residents, broad industry mix and state benchmark",
                         "State employed residents and Explorer state industry shares"]),
]
