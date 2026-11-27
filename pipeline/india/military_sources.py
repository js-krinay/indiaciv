"""Public city names and national strength evidence for the Military layer."""

from ..core.source import SourceInfo

COMMANDS = (
    ("Army Northern Command", "JK", "Udhampur", "2131197", "25 May 2025"),
    ("Army Western Command", "HR", "Chandimandir", "2131197", "25 May 2025"),
    ("Army Central Command", "UP", "Lucknow", "2051346", "3 Sep 2024"),
    ("Army Eastern Command", "WB", "Kolkata", "2032499", "11 Jul 2024"),
    ("Army Southern Command", "MH", "Pune", "2305146", "31 Aug 2026"),
    ("Army South Western Command", "RJ", "Jaipur", "2135957", "13 Jun 2025"),
    ("Army Training Command", "HP", "Shimla", "2257210", "1 May 2026"),
    ("Western Naval Command", "MH", "Mumbai", "2017311", "6 Apr 2024"),
    ("Eastern Naval Command", "AP", "Visakhapatnam", "2022124140401", "4 Dec 2022"),
    ("Southern Naval Command", "KL", "Kochi", "2259243", "9 May 2026"),
    ("Western Air Command", "DL", "New Delhi", "2089919", "3 Jan 2025"),
    ("Eastern Air Command", "ML", "Shillong", "2275985", "21 Jun 2026"),
    ("Central Air Command", "UP", "Prayagraj", "1755628", "17 Sep 2021"),
    ("South Western Air Command", "GJ", "Gandhinagar", "1497471", "27 Jul 2017"),
    ("Southern Air Command", "KL", "Thiruvananthapuram", "33946", "11 Dec 2007"),
    ("Air Force Training Command", "KA", "Bengaluru", "2021532", "24 May 2024"),
    ("Air Force Maintenance Command", "MH", "Nagpur", "2276230", "21 Jun 2026"),
    ("Andaman & Nicobar Command", "AN", "Sri Vijaya Puram", "2133190", "1 Jun 2025"),
)

PIB_POLICY = "https://www.pib.gov.in/content/186_2_Copyright-Policy.aspx?lang=1&reg=5"
PIB_RELEASE = "https://www.pib.gov.in/PressReleasePage.aspx?PRID="
NATURAL_EARTH_CHECKSUM = "cd149186f03d2603e0410da399b980a4357d0ac32d3a2305a49ed3dffcc41d7b"
GEONAMES_CHECKSUM = "6bb7148d23be7fe63693f7a24a6966331e2f78e265e0e5f89431128ed1cf20ba"
GEONAMES_EDITION = "27 Nov 2026"
GEONAMES_URL = "https://download.geonames.org/export/dump/IN.zip"
DISTRICT_EVIDENCE = {
    ("BR", "Danapur"): ("10-230", "India Post", "https://www.indiapost.gov.in/post-office-details?pincode=801503", "Post office directory checked 28 Nov 2026"),
    ("MH", "Khadki"): ("27-521", "Government of India Gazette", "https://egazette.gov.in/WriteReadData/2025/265847.pdf", "Gazette notification 14(E)"),
    ("UP", "Babina"): ("09-166", "Jhansi district", "https://jhansi.nic.in/deo-portal/form-9101111a-and-11b-for-displaying-list-of-claims-and-objections-ssr-2027/", "Electoral roll revision for 2027"),
    ("UP", "Fatehgarh"): ("09-159", "Farrukhabad district", "https://farrukhabad.nic.in/public-utility-category/municipality/", "Municipality directory checked 28 Nov 2026"),
    ("UK", "Ranikhet"): ("05-064", "Almora district", "https://almora.nic.in/divisions/district-administration/", "District administration directory checked 28 Nov 2026"),
}
RELEASE_URLS = {
    "2022124140401": "https://static.pib.gov.in/WriteReadData/specificdocs/documents/2022/dec/doc2022124140401.pdf",
    "33946": "https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=33946",
}
STRENGTH_SOURCE = "defence_committee_report_8"
# Held strength by published cohort, never a sum across observation dates.
STRENGTH = {
    "army_officers": (42_095, "Army officers", "1 Jul 2024", "Excludes medical, dental and nursing services."),
    "army_other_ranks": (1_105_110, "Army JCOs and other ranks", "1 Oct 2024", "Held strength of JCOs and other ranks."),
    "navy": (10_045 + 59_828 + 11_634, "Navy uniformed", "Reported to Parliament, 17 Mar 2025",
             "Officers, sailors and Agniveers. Headcount date unspecified. Excludes defence civilians."),
    "air_force": (11_916 + 139_876, "Air Force personnel", "1 Oct 2024",
                  "Officers excluding medical and dental branches, plus airmen including Agniveervayu. Excludes trainees."),
}

# Published home-port observations, at port-city granularity.
HOME_PORTS = (
    ("Kochi", "INS Sudarshini", "20 Jan 2026", "2223195", "4 Feb 2026"),
    ("Karwar", "INS Tushil", "28 Dec 2024", "2088564", "28 Dec 2024"),
    ("Visakhapatnam", "INS Sahyadri", "14 Oct 2025", "2179047", "14 Oct 2025"),
)

SOURCES = [
    SourceInfo("geonames_india", "GeoNames India populated places", "GeoNames", GEONAMES_URL,
               "CC BY 4.0", f"India extract, {GEONAMES_EDITION}. SHA-256 {GEONAMES_CHECKSUM}. "
               "Only civil populated-place records are used for town joins.",
               ["Military layer civil town points"], license_url="https://creativecommons.org/licenses/by/4.0/"),
    SourceInfo(STRENGTH_SOURCE, "Standing Committee on Defence, Eighth Report", "Lok Sabha",
               "https://sansad.in/getFile/app/lsscommittee/Defence/18_Defence_8.pdf?source=app",
               "Attributed national cohort facts and derived subtotals.",
               "Tabled 17 Mar 2025. Paragraphs 1.31, 2.33 and Part II paragraph 22. SHA-256 "
               "e7515f01f97153c7acc211bb907243c2118e2f243e282c9a598aad88e374724e.",
               ["National held strength"]),
    SourceInfo("ne_places", "Natural Earth Populated Places", "Natural Earth",
               "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-populated-places/",
               "Public domain", f"Version 5.1.2. SHA-256 {NATURAL_EARTH_CHECKSUM}. Civil town points.",
               ["Military layer town joins"]),
]
for release in dict.fromkeys(row[3] for row in COMMANDS):
    rows = [row for row in COMMANDS if row[3] == release]
    names = "; ".join(f"{name}, {town}" for name, _, town, _, _ in rows)
    SOURCES.append(SourceInfo(f"command_hq_{release}", names, "Government of India via PIB",
                              RELEASE_URLS.get(release, PIB_RELEASE + release),
                              "PIB first-party reuse with credit.", f"Release {release}, {rows[0][4]}.",
                              ["Published command headquarters cities"], license_url=PIB_POLICY))
for port, ship, period, release, published in HOME_PORTS:
    SOURCES.append(SourceInfo(f"ship_home_port_{release}", f"{ship} home port, {port}",
                              "Ministry of Defence via PIB", PIB_RELEASE + release,
                              "PIB first-party reuse with credit.",
                              f"Home port reported for {period}. Release {release}, {published}.",
                              ["Published ship home ports"], license_url=PIB_POLICY))
for (state, town), (_, publisher, url, edition) in DISTRICT_EVIDENCE.items():
    SOURCES.append(SourceInfo(f"civic_town_{town.lower()}", f"{town} civil district", publisher, url,
                              "Attributed public administrative geography facts.", f"{edition}.",
                              ["District corroboration for civil populated-place joins"]))
