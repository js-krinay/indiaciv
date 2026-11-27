"""Pinned public releases for the Knowledge and Defence & veterans advisors."""

from ..core.source import SourceInfo

FY = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
BOARDS_PERIOD = "Directory checked 27 Nov 2026"
VETERAN_PERIOD = "30 Jun 2026"
VETERAN_SOURCES = ["registered_veterans_pib", "registered_veterans_ksb"]
VETERAN_METHOD = "Carries forward the annual net change between two consecutive June registration snapshots."
PIB_POLICY = "https://www.pib.gov.in/content/186_2_Copyright-Policy.aspx?lang=1&reg=5"
BOARD_URL = "https://dgde.gov.in/en/autonomous-bodies-institutions-under-directorate-general-defence-estates/"


def pib(key, title, release, publisher, description, use):
    return SourceInfo(key, title, f"{publisher} via PIB",
                      f"https://www.pib.gov.in/PressReleasePage.aspx?PRID={release}&lang=1&reg=3",
                      "PIB reproduction policy for first-party material, with credit.",
                      description, [use], license_url=PIB_POLICY)


SOURCES = [
    pib("defence_budget_fy26", "Union defence budget estimate", 2098485, "Ministry of Defence",
        f"{FY}, Ministry of Defence Budget Estimate and four budget heads. "
        "IndiaCiv divides the allocation by projected national residents and by provisional nominal GDP for context.",
        "Defence & veterans"),
    pib("sainik_schools_2026", "Sainik Schools partnership programme", 2258892, "Ministry of Defence",
        "National count of affiliated and operational new partnership schools, 7 May 2026.", "Defence & veterans"),
    pib("veterans_welfare_rates", "Veteran welfare grant rates", 2179240, "Ministry of Defence",
        "Kendriya Sainik Board notified rates applicable to eligible applications in 2026.", "Defence & veterans"),
    pib("registered_veterans_pib", "Registered ex-servicemen by State/UT", 2155070, "Ministry of Defence",
        f"Registration snapshot for 30 Jun 2024. {VETERAN_METHOD}", "IndiaCiv estimates for 30 Jun 2026"),
    SourceInfo("registered_veterans_ksb", "Kendriya Sainik Board guidebook, Appendix B",
               "Kendriya Sainik Board / Meghalaya Directorate of Sainik Welfare",
               "https://sainikwelfare.meghalaya.gov.in/pub/KSB_Guidebook_2025_English.pdf",
               "Meghalaya DSW reproduction terms, with credit for the registration aggregates.",
               "Registration snapshot for 30 Jun 2025. SHA-256 "
               "de70904d04e25468a6562665cf551854fa98b9533c96ba37055b1efe42eee9dd.",
               ["IndiaCiv estimates for 30 Jun 2026"], license_url="https://sainikwelfare.meghalaya.gov.in/terms.html"),
    SourceInfo("cantonment_boards", "Cantonment board civic directory", "Directorate General Defence Estates",
               BOARD_URL, "DGDE reproduction policy for first-party material, with credit.",
               "DGDE civic board directory edition dated 8 Sep 2025 and in use on 27 Nov 2026.",
               ["Civic administration counts"], license_url="https://dgde.gov.in/en/website-policies/"),
    SourceInfo("civic_office_points", "Public cantonment board offices", "OpenStreetMap contributors",
               "https://www.openstreetmap.org/copyright", "ODbL 1.0",
               "Selected public offices from OpenStreetMap node 7972665139 v1 and way 106232276 v5. "
               "Coordinates are covered by ODbL 1.0.",
               ["Civic points and urban footprint matches"],
               license_url="https://opendatacommons.org/licenses/odbl/1-0/"),
    SourceInfo("hp_veterans_2026", "Himachal Pradesh Statistical Year Book, Table 2.22",
               "Department of Economics & Statistics, Government of Himachal Pradesh",
               "https://econstats.hp.gov.in/wp-content/uploads/2026/11/Statistical-Year-Book-2025-26.pdf",
               "Third-party administrative table. IndiaCiv serves derived rates only.",
               "Directorate of Sainik Welfare, Himachal Pradesh district counts on 31 Mar 2026. SHA-256 "
               "0f2517ca5c52e74586c956464123e2b4cf2f80903a3e79922af7eafc2862daf6.",
               ["Derived Himachal Pradesh district veteran rates"],
               license_url="https://econstats.hp.gov.in/copyright-policy/"),
]

# The directory has 61 civic boards. Groups use the board locality's State/UT.
BOARDS = {
    "BR": ("Danapur",), "DL": ("Delhi",), "GJ": ("Ahmedabad",), "HR": ("Ambala",),
    "HP": ("Bakloh", "Dagshai", "Dalhousie", "Jutogh", "Kasauli", "Subathu"),
    "JK": ("Badamibagh", "Jammu"), "JH": ("Ramgarh",), "KA": ("Belagavi",), "KL": ("Kannur",),
    "MP": ("Jabalpur", "Mhow", "Morar", "Pachmarhi", "Saugor"),
    "MH": ("Ahilyanagar", "Chhatrapati Sambhajinagar", "Dehuroad", "Deolali", "Kamptee", "Khadki", "Pune"),
    "ML": ("Shillong",), "PB": ("Amritsar", "Ferozepur", "Jalandhar"), "RJ": ("Ajmer", "Nasirabad"),
    "TN": ("St. Thomas Mount Cum Pallavaram", "Wellington"), "TS": ("Secunderabad",),
    "UP": ("Agra", "Ayodhya", "Babina", "Bareilly", "Fatehgarh", "Jhansi", "Kanpur", "Lucknow", "Mathura",
           "Meerut", "Prayagraj", "Shahjahanpur", "Varanasi"),
    "UK": ("Almora", "Chakrata", "Clement Town", "Dehradun", "Landour", "Lansdowne", "Nainital", "Ranikhet", "Roorkee"),
    "WB": ("Barrackpore", "Jalapahar", "Lebong"),
}

# Public municipal service offices. Coordinates are lon, lat, from the ODbL source above.
CIVIC_OFFICES = [
    ("Pune Cantonment Board", 73.87850, 18.50228),
    ("Secunderabad Cantonment Board", 78.5005707, 17.4436542),
]

# Aggregate registration stocks only (June 2024, June 2025).
# Punjab and Manipur are omitted pending reconciliation of abrupt changes.
REGISTRATIONS = {
    "AP": (78148, 80878), "AR": (986, 1003), "AS": (41656, 42111), "BR": (133526, 139651),
    "CG": (7355, 7445), "GA": (2389, 2418), "GJ": (33773, 34495), "HR": (177771, 184714),
    "HP": (129656, 131616), "JH": (30546, 31486), "KA": (94530, 94376), "KL": (182368, 183840),
    "MP": (58464, 59074), "MH": (201628, 206545), "ML": (3012, 3068), "MZ": (5975, 6355),
    "NL": (3284, 3451), "OD": (53025, 54598), "RJ": (212415, 215854), "SK": (1094, 1127),
    "TN": (123349, 124096), "TS": (27853, 28775), "TR": (2609, 2677), "UP": (426179, 436325),
    "UK": (139882, 140975), "WB": (107450, 111383), "AN": (1123, 1216), "CH": (8463, 8462),
    "DL": (63614, 64074), "JK": (78592, 80504), "LA": (6479, 6680), "PY": (2477, 2494),
}

# Table 2.22, aligned to the DataMeet district codes in Himachal Pradesh.
HP_REGISTRATIONS = {
    "02-023": 3933, "02-024": 55634, "02-025": 363, "02-026": 1202,
    "02-027": 16300, "02-028": 20212, "02-029": 12961, "02-030": 8930,
    "02-031": 4872, "02-032": 3866, "02-033": 4354, "02-034": 524,
}
VETERAN_POPULATION = "veteran_worldpop"
