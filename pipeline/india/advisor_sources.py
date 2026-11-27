"""Pinned public releases for the Knowledge and Defence & veterans advisors."""

from ..core.source import SourceInfo

FY = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
BOARDS_PERIOD = "27 Nov 2026"
VETERAN_PERIOD = "30 Jun 2026"
PENURY_GRANT_INR = 8_000
PENURY_GRANT_PERIOD = "2026"
VETERAN_SOURCES = ["registered_veterans_pib", "registered_veterans_ksb"]
VETERAN_METHOD = "Carries forward the annual net change between two consecutive June registration snapshots."
PIB_POLICY = "https://www.pib.gov.in/content/186_2_Copyright-Policy.aspx?lang=1&reg=5"
BOARD_URL = "https://dgde.gov.in/en/autonomous-bodies-institutions-under-directorate-general-defence-estates/"
RMS_SOURCE = "rashtriya_military_schools_2026"
RMS_PERIOD = "2026"
RMS_TOWNS = {"HP": ("Chail",), "KA": ("Belagavi", "Bengaluru"), "RJ": ("Ajmer", "Dholpur")}
RMS_BY_STATE = {state: len(towns) for state, towns in RMS_TOWNS.items()}
SAINIK_ROSTER_SOURCE = "aissee_2026_traditional"
SAINIK_ROSTER = {
    "AP": ("Korukonda", "Kalikiri"), "AR": ("East Siang",), "AS": ("Goalpara",),
    "BR": ("Nalanda", "Gopalganj"), "CG": ("Ambikapur",), "GJ": ("Balachadi",),
    "HR": ("Kunjpura", "Rewari"), "HP": ("Sujanpur Tira",), "JK": ("Nagrota",),
    "JH": ("Tilaiya",), "KA": ("Bijapur", "Kodagu"), "KL": ("Kazhakootam",),
    "MP": ("Rewa",), "MH": ("Satara", "Chandrapur"), "MN": ("Imphal",),
    "MZ": ("Chhingchhip",), "NL": ("Punglwa",), "OD": ("Bhubaneswar", "Sambalpur"),
    "PB": ("Kapurthala",), "RJ": ("Chittorgarh", "Jhunjhunu"),
    "TN": ("Amaravathinagar",), "UP": ("Mainpuri", "Jhansi", "Amethi"),
    "UK": ("Ghorakhal",), "WB": ("Purulia",),
}

PARTNERSHIP_PLACES = {
    "AP": ("Krishnapatnam", "Vijayawada", "Tirupati"),
    "AR": ("Tawang",), "AS": ("Chirang",),
    "BR": ("Bataha", "Patna", "Bhagalpur", "Kishanganj"),
    "CG": ("Mandir Hasaud", "Rajnandgaon", "Sendri", "Bijabhat", "Kanker"),
    "DH": ("Silvassa",),
    "GJ": ("Chaparda", "Mehsana", "Moriya", "Rajkot", "Kera", "Jetalpur", "Madapur", "Umbhrat"),
    "HR": ("Khara Kheri", "Rohtak", "Lohar Majra", "Hansi", "Tepla"),
    "HP": ("Nalagarh", "Bani"),
    "KA": ("Sangolli", "Saragur", "Bidar", "Sindhanur"),
    "KL": ("Kozhikode", "Mavelikara", "Kalady", "Mala", "Thiruvananthapuram"),
    "MP": ("Mandsaur", "Paliya Pipariya", "Khargone", "Katni", "Morena"),
    "MH": ("Loni Khurd", "Retharedharan", "Akulgaon", "Nagpur", "Kolwad", "Sawantwadi",
           "Chhatrapati Sambhajinagar", "Nashik"),
    "OD": ("Balangir",), "PB": ("Nabha", "Amritsar", "Anandpur Sahib"),
    "RJ": ("Jaipur", "Dabli Rathan", "Sikar", "Jodhpur", "Kuchaman City"),
    "TN": ("Sawyerpuram", "Madurai", "Salem", "Tiruppur"),
    "UP": ("Vrindavan", "Etawah", "Prayagraj", "Mohanlalganj"),
}
PARTNERSHIP_SUPPLEMENT = {"TN": ("Namakkal",), "GA": ("Vasco da Gama",), "MH": ("Ambajogai",)}
PARTNERSHIP_SOURCE = "aissee_2026_partnerships"
PARTNERSHIP_SUPPLEMENT_SOURCE = "aissee_2026_partnerships_supplement"
BOARD_CENSUS_SOURCE = "dgde_civic_board_census"
BOARD_CLASS_PERIOD = "FY 2022-23 (1 Apr 2022 – 31 Mar 2023)"


BOARD_CENSUS = {
    "Agra": (53_137, "I"),
    "Ahmedabad": (14_345, "II"),
    "Ahilyanagar": (28_986, "II"),
    "Ajmer": (3_530, "III"),
    "Prayagraj": (39_684, "II"),
    "Almora": (2_231, "IV"),
    "Ambala": (55_370, "I"),
    "Amritsar": (10_410, "II"),
    "Chhatrapati Sambhajinagar": (18_051, "II"),
    "Babina": (27_852, "II"),
    "Badamibagh": (22_214, "II"),
    "Bakloh": (1_805, "IV"),
    "Bareilly": (30_005, "II"),
    "Barrackpore": (23_266, "II"),
    "Belagavi": (19_411, "II"),
    "Kannur": (4_798, "III"),
    "Chakrata": (5_117, "III"),
    "Clement Town": (22_577, "II"),
    "Dagshai": (2_904, "III"),
    "Dalhousie": (3_549, "III"),
    "Danapur": (28_723, "II"),
    "Dehradun": (52_716, "I"),
    "Dehuroad": (48_961, "II"),
    "Delhi": (110_351, "I"),
    "Deolali": (54_027, "I"),
    "Ayodhya": (12_391, "II"),
    "Fatehgarh": (14_793, "II"),
    "Ferozepur": (53_199, "I"),
    "Jabalpur": (72_257, "I"),
    "Jalandhar": (47_845, "II"),
    "Jalapahar": (1_711, "IV"),
    "Jammu": (28_396, "II"),
    "Jhansi": (28_343, "II"),
    "Jutogh": (2_062, "IV"),
    "Kamptee": (12_457, "II"),
    "Kanpur": (108_534, "I"),
    "Kasauli": (3_885, "III"),
    "Khadki": (70_399, "I"),
    "Landour": (3_543, "III"),
    "Lansdowne": (5_667, "III"),
    "Lebong": (1_397, "IV"),
    "Lucknow": (63_003, "I"),
    "Mathura": (25_603, "II"),
    "Meerut": (93_684, "I"),
    "Mhow": (69_281, "I"),
    "Morar": (48_464, "II"),
    "Nainital": (1_398, "IV"),
    "Nasirabad": (50_804, "I"),
    "Pachmarhi": (12_062, "II"),
    "Pune": (71_831, "I"),
    "Ramgarh": (88_781, "I"),
    "Ranikhet": (18_886, "II"),
    "Roorkee": (14_689, "II"),
    "Saugor": (40_513, "II"),
    "Secunderabad": (217_910, "I"),
    "Shahjahanpur": (18_116, "II"),
    "Shillong": (11_919, "II"),
    "St. Thomas Mount Cum Pallavaram": (43_795, "II"),
    "Subathu": (3_685, "III"),
    "Varanasi": (14_119, "II"),
    "Wellington": (19_462, "II"),
}

# Company-wide financial observations in INR. Registered or headquarters city only.
PSU_FINANCIALS = (
    ("bel_revenue", "Bharat Electronics Limited", "KA", "Bengaluru", "revenue from operations",
     274_796_300_000, "Integrated Annual Report 2025-26, standalone financial statements",
     "https://bel-india.in/wp-content/uploads/2026/08/Integrated-Annual-Report-2025-26.pdf"),
    ("hal_turnover", "Hindustan Aeronautics Limited", "KA", "Bengaluru", "turnover", 317_918_300_000,
     "Annual Report 2025-26, Board’s Report", "https://hal-india.co.in/backend/eechoogn/2026/07/HAL_AR-2025-26.pdf"),
    ("beml_revenue", "BEML Limited", "KA", "Bengaluru", "revenue from operations", 43_505_300_000,
     "5 Nov 2026 standalone filing, audited year ended 31 Mar 2026",
     "https://www.bemlindia.in/wp-content/uploads/2026/11/QR30299-001_20261105_161537.pdf"),
    ("midhani_revenue", "MIDHANI", "TS", "Hyderabad", "revenue from operations", 12_086_259_000,
     "30 May 2026 standalone filing, audited year ended 31 Mar 2026",
     "https://midhani-india.in/WordPress-content/uploads/2021/2025-26/Q4/MDN_NewspaperAd_Q4_30052026.pdf"),
    ("grse_revenue", "Garden Reach Shipbuilders & Engineers", "WB", "Kolkata", "revenue from operations",
     70_020_000_000, "FY 2026-27 Quarter 2 company release archive",
     "https://grse.in/press-releases-2026-27-quarter2/"),
    ("gsl_turnover", "Goa Shipyard Limited", "GA", "Vasco da Gama", "turnover (value of production)",
     37_166_878_000, "Annual Report 2025-26, Statement of Profit and Loss",
     "https://goashipyard.in/assets/front/public/financial-year-wise-annual-reports-pdf/Goa-Shipyard-Limited-Annual-Report-for-FY-2025-26.pdf"),
    ("bdl_turnover", "Bharat Dynamics Limited", "TS", "Hyderabad", "net sales turnover", 24_420_000_000,
     "Annual Report 2025-26, Corporate Overview",
     "https://bdl-india.in/sites/default/files/Annual-Report-2025-26.pdf"),
    ("mdl_revenue", "Mazagon Dock Shipbuilders Limited", "MH", "Mumbai",
     "consolidated revenue from operations", 130_063_100_000, "30 Apr 2026 audited financial results",
     "https://www.mazagondock.in/images/pdf/SE_Disclosure_Outcome_of_BM_30Apr2026.pdf"),
    ("avnl_revenue", "Armoured Vehicles Nigam Limited", "TN", "Chennai", "revenue from operations", 60_970_400_000,
     "Annual Report 2025-26, Board’s Report", "https://avnl.co.in/files/inline-documents/fifthAnnualReport.pdf"),
)


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
        "National counts for the traditional and new partnership programmes, 7 May 2026.", "Defence & veterans"),
    pib("dpsu_turnover_fy26", "Defence PSU annual performance review", 2304900, "Ministry of Defence",
        f"National turnover of the 16 defence PSUs, {FY}, released 31 August 2026.", "Defence & veterans"),
    SourceInfo(RMS_SOURCE, "Rashtriya Military Schools Common Entrance Test",
               "National Testing Agency",
               "https://exams.nta.nic.in/about-department/introduction-3/",
               "IndiaCiv uses city names and derived counts by state and nationally.",
               "Five residential schools listed in the RMS CET 2026 edition.",
               ["Defence & veterans"]),
    SourceInfo(SAINIK_ROSTER_SOURCE, "AISSEE 2026 Information Bulletin, Appendix I-A",
               "National Testing Agency",
               "https://cdnbbsr.s3waas.gov.in/s388a839f2f6f1427879fc33ee4acf4f66/uploads/2025/10/20251010937989896.pdf",
               "IndiaCiv uses factual place labels from the roster.",
               "The 33 traditional Sainik Schools listed for AISSEE 2026, grouped by state or UT.",
               ["Defence & veterans"]),
    SourceInfo(PARTNERSHIP_SOURCE, "AISSEE 2026 Information Bulletin, Appendix I-B",
               "National Testing Agency",
               "https://cdnbbsr.s3waas.gov.in/s388a839f2f6f1427879fc33ee4acf4f66/uploads/2025/10/20251010937989896.pdf",
               "IndiaCiv uses factual place names from the roster.",
               "The 69 partnership schools in the original AISSEE 2026 roster, grouped by state or UT. "
               "SHA-256 9b8b53a60ccfd3da8965eec8891100e45e12f2947a2000c23d92bb1a2e75906c.",
               ["Defence & veterans"]),
    SourceInfo(PARTNERSHIP_SUPPLEMENT_SOURCE, "AISSEE 2026 roster supplement, 24 October 2025",
               "Sainik Schools Society",
               "https://www.nta.ac.in/Download/Notice/Notice_20251025180445.pdf",
               "IndiaCiv uses factual place names from the roster.",
               "Three partnership schools added for consideration in the AISSEE 2026 admissions cycle.",
               ["Defence & veterans"]),
    pib("veterans_welfare_rates", "Veteran welfare grant rates", 2179240, "Ministry of Defence",
        f"Kendriya Sainik Board penury grant for eligible veterans in {PENURY_GRANT_PERIOD}: "
        f"₹{PENURY_GRANT_INR:,} per month per beneficiary.", "Defence & veterans"),
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
    SourceInfo(BOARD_CENSUS_SOURCE, "Cantonment administration report, Annexure I",
               "Directorate General Defence Estates",
               "https://cdnbbsr.s3waas.gov.in/s30f46c64b74a6c964c674853a89796c8e/uploads/2024/05/202405281860637049.pdf",
               "DGDE reproduction policy for first-party material, with credit.",
               f"Board classes in {BOARD_CLASS_PERIOD} and all residents as counted in Census 2011. "
               "SHA-256 c89dc5a208dc1e2804c85586a6bf7e00cc0b75a14eb3e34382d5dc7bbcbd70c2.",
               ["Civic board class and population"], license_url="https://dgde.gov.in/en/website-policies/"),
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
SOURCES.extend(
    SourceInfo(key, edition, company, url, "IndiaCiv uses the published financial fact and city name.",
               f"{company} {measure}, {FY}. Headquarters city: {city}.", ["Defence & veterans"])
    for key, company, _, city, measure, _, edition, url in PSU_FINANCIALS
)

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
# Punjab and Manipur lack comparable pairs; use the PIB observation below.
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

OLDER_REGISTRATIONS = {"MN": 8_744, "PB": 382_694}
OLDER_REGISTRATION_PERIOD = "30 Jun 2024"

# Table 2.22, aligned to the DataMeet district codes in Himachal Pradesh.
HP_REGISTRATIONS = {
    "02-023": 3933, "02-024": 55634, "02-025": 363, "02-026": 1202,
    "02-027": 16300, "02-028": 20212, "02-029": 12961, "02-030": 8930,
    "02-031": 4872, "02-032": 3866, "02-033": 4354, "02-034": 524,
}
VETERAN_POPULATION = "veteran_worldpop"
