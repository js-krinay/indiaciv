"""Derived shares from pinned official advance estimates of nominal GSVA."""

from math import prod

from ..core.source import SourceInfo
from .people_sources import PINS

RBI_SOURCE = "rbi_state_gsva"
NATIONAL_SOURCE = "mospi_national_gva_fy26"
HISTORICAL_DETAIL_PERIODS = dict.fromkeys(
    ("uttar_pradesh_gsva_detail", "kerala_gsva_detail", "tamil_nadu_gsva_detail", "bihar_gsva_detail"),
    "FY 2024-25 (1 Apr 2024 – 31 Mar 2025)"
)
RESIDUAL_METHOD = ("IndiaCiv estimates split the residual city industry output after manufacturing and "
                   "construction using the source's nominal mining and utilities proportions.")
METHOD = ("IndiaCiv estimate: carry each nominal state GSVA group forward using the corresponding "
          "national nominal growth rates, then divide by the estimated total across the three groups.")

SOURCES = [
    SourceInfo("delhi_gsva_fy26", "Economic Survey of Delhi 2025-26, Table 2.1",
               "Delhi Planning Department",
               "https://delhiplanning.delhi.gov.in/sites/default/files/2026-03/economic_survey_english_0.pdf",
               "Government publication, derived shares only",
               "City View uses agriculture, industry (including mining) and services as shares of Delhi's "
               "nominal GSVA. SHA-256 e180f689f94cf954f5712cdcd643a9e964d28a5b6d34c8aa03ed89c670e83509.",
               ["City View sector mix"]),
    SourceInfo("maharashtra_gsva_fy26", "Economic Survey of Maharashtra 2025-26 press note, Statement 2",
               "Directorate of Economics and Statistics, Maharashtra",
               "https://mahaces.maharashtra.gov.in/files/DES_MenuLinkPDF/PressNote_ARC_English_Final_05.03.2026.pdf",
               "Government publication, derived shares only",
               "City View uses agriculture, industry (including mining) and services as shares of Maharashtra's "
               "nominal GSVA. SHA-256 5e668597348acbe737aeabb06ad3d773950b1b9b4ac61aa7feec2315e80d1bce.",
               ["City View sector mix"]),
    SourceInfo("andhra_pradesh_gsva_fy26", "Andhra Pradesh FRBM Statement, Budget 2026-27, Form F-1",
               "Andhra Pradesh Finance Department",
               "https://s3.ap-south-1.amazonaws.com/apfinance.gov.in/uploads/frbmreport/FRBM_BE_2026-27_BookFinal.pdf",
               "Government publication, derived shares only",
               "Uses the first advance estimates of nominal GSVA in the Budget 2026-27 edition, Form F-1.",
               ["City View sector mix"]),
    SourceInfo("odisha_gsva_fy26", "Odisha Economic Survey 2025-26, Figure 1.3 and Table 1.2",
               "Directorate of Economics and Statistics, Odisha",
               "https://assembly.odisha.gov.in/WriteReadData/News/OES%202026%20WEB%20UPLOAD.pdf",
               "Government publication, attributed shares only",
               "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) nominal GSVA advance estimates. Mining is included in "
               "industry. For city output, IndiaCiv estimates split the residual industry share after "
               "manufacturing and construction using the published mining and utility proportions. "
               "SHA-256 1af94ebd625a031f4ffb93f2d5307dee91efd1b26b27fea7a98c40cf4677e65c.",
               ["State and City View sector mix"]),
    SourceInfo("andhra_pradesh_gsva_detail_fy26", "Andhra Pradesh Socio-Economic Survey 2025-26, Chart 3.11",
               "Planning Department, Andhra Pradesh",
               "https://www.ap.gov.in/assets/documents/socioeconomicsurvey/2025-26_Book.pdf",
               "Government publication, attributed shares only",
               "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) first advance estimates at current prices. "
               "SHA-256 d55e67b5c8c623c6fbe2ff07b08816856ad3e8ee17bbb667ab855d9bb088a3c1.",
               ["City View industry output"]),
    SourceInfo("telangana_gsva_fy26", "Telangana Socio Economic Outlook 2026, §6.1.1 and §7.2.1",
               "Directorate of Economics and Statistics, Telangana",
               "https://www.telangana.gov.in/wp-content/uploads/2026/08/Socio-Economic-Outlook-2026.pdf",
               "Government publication, derived shares only",
               "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) provisional advance estimates at current prices. "
               "For city output, IndiaCiv estimates split the residual industry share after manufacturing "
               "and construction using the published mining and utility proportions. "
               "SHA-256 b0001a02778cb04630ec1b7c5f18e6d71b54f111ac45c37e4db342db8cb1bf68.",
               ["State sector mix", "City View industry output"]),
    SourceInfo("karnataka_gsva_fy26", "Karnataka Economic Survey 2025-26, English final edition, Appendix 1.1",
               "Directorate of Economics and Statistics, Karnataka",
               "https://data.opencity.in/dataset/699b7b8d-3813-4e44-8d70-cfdf1414ee85/resource/"
               "ee584e22-2c78-4a54-9054-74db776a9a53/download/economic_survey_2025-26_english_finalmpdf_1772796504.pdf",
               "Government publication, derived shares only",
               "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) nominal advance estimates. " + RESIDUAL_METHOD,
               ["State sector mix", "City View industry output"]),
    SourceInfo("madhya_pradesh_gsva_fy26", "Madhya Pradesh Economic Survey 2025-26, Tables 1.2–1.4",
               "Government of Madhya Pradesh",
               "https://www.mpinfo.org/mpinfoNew/Uploads/PDF/Tuesday%2C%20February%2017%2C%202026/D-170226020441.pdf",
               "Government publication, derived shares only",
               "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) nominal advance estimates, 17 February 2026 edition. "
               + RESIDUAL_METHOD, ["State sector mix", "City View industry output"]),
    SourceInfo("rajasthan_gsva_fy26", "Rajasthan Economic Review 2025-26, Figure 13.3",
               "Directorate of Economics and Statistics, Rajasthan",
               "https://finance.rajasthan.gov.in/docs/budget/statebudget/2026-2027/Economicreviewe.pdf",
               "Government publication, derived shares only",
               "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) nominal advance estimates, 2026–27 budget edition. "
               + RESIDUAL_METHOD, ["State sector mix", "City View industry output"]),
    SourceInfo("jammu_kashmir_gsva_fy26", "Jammu and Kashmir Economic Survey 2025-26, Tables 1(ix)–1(xi)",
               "Directorate of Economics and Statistics, Jammu and Kashmir",
               "https://ecostatjk.nic.in/pdf/publications/ecosurvey/Economic%20Survey%202025-26_webCopy.pdf",
               "Government publication, derived shares only",
               "FY 2025-26 (1 Apr 2025 – 31 Mar 2026) first nominal advance estimates, 1 February 2026 edition. "
               + RESIDUAL_METHOD, ["State sector mix", "City View industry output"]),
]


def sector_mix(state, source, agriculture, industry, services, total):
    shares = {name: value / total for name, value in
              zip(("agriculture", "industry", "services"), (agriculture, industry, services))}
    return dict(state=state, source=source.id, publisher=source.publisher, status="Advance estimate", shares=shares)


SECTOR_MIX = {
    "DL": sector_mix("Delhi", SOURCES[0], 322_764, 637_029 + 15_424_468, 103_379_535, 119_763_796),
    "MH": sector_mix("Maharashtra", SOURCES[1], 473_089, 65_349 + 1_043_844, 2_855_198, 4_437_480),
    "AP": sector_mix("Andhra Pradesh", SOURCES[2], 539_454, 384_471, 700_717, 1_624_642),
    "OD": sector_mix("Odisha", SOURCES[3], 19.6, 41.3, 39.1, 100),
    "TS": sector_mix("Telangana", SOURCES[5], 1_648_613 - 304_217 - 1_130_596, 304_217, 1_130_596, 1_648_613),
    "KA": sector_mix("Karnataka", SOURCES[6], 322_756, 580_144, 2_093_564, 2_996_465),
    "MP": sector_mix("Madhya Pradesh", SOURCES[7], 40.13, 22.75, 37.12, 100),
    "RJ": sector_mix("Rajasthan", SOURCES[8], 25.74, 26.55, 47.71, 100),
    "JK": sector_mix("Jammu & Kashmir", SOURCES[9], 20.45 - .40, 18.52 + .40, 61.02, 100),
}

for state, components, total in (
    ("DL", (637_029, 5_014_381, 6_859_334, 3_550_753), 119_763_796),
    ("MH", (65_349, 657_015, 297_238, 89_591), 4_437_480),
    ("OD", (9.5, 18.8, 9.6, 3.3), 100),
    ("TS", (35_892, 137_229, 93_404, 37_692), 1_648_613),
):
    SECTOR_MIX[state]["detail"] = {
        key: value / total for key, value in zip(("mining", "manufacturing", "construction", "utilities"), components)
    }

SOURCES += [
    SourceInfo(RBI_SOURCE, "Handbook of Statistics on Indian States, tables 25, 33, 37, 41 and 49",
               "Reserve Bank of India",
               "https://www.rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook+of+Statistics+on+Indian+States",
               "Publisher copyright, derived shares only",
               "2024-25 edition, published 11 December 2025. The state baseline uses total nominal GSVA less industry and "
               "services for agriculture and allied activities. " + METHOD, ["Economy"]),
    SourceInfo(NATIONAL_SOURCE, "Provisional annual GDP estimates for 2025-26, Statement 4",
               "NSO / Ministry of Statistics and Programme Implementation",
               "https://www.mospi.gov.in/uploads/latestReleases/latest_release_1780655857536_5ac01869-ca4a-422d-b7a7-57b81da60932_Press_Note_on_GDP_Estimates_for_Q4_2025-26_and_PE_FY_2025-26_F.pdf",
               "MoSPI Category A aggregates, credited reuse",
               "5 June 2026 release. Current-price year-to-year ratios are used to project state sectors, "
               "with mining and quarrying added to the secondary sector. Statement 4 also supplies the national "
               "provisional FY 2025-26 (1 Apr 2025 – 31 Mar 2026) GVA levels. PDF SHA-256 " + PINS["gdp"],
               ["Economy"]),
    SourceInfo("uttar_pradesh_gsva_detail", "Uttar Pradesh State Economic Survey 2025-26, Table 1.1",
               "Government of Uttar Pradesh",
               "https://budget.up.nic.in/btn-survey/Economic_Survey_UP_2025_26.pdf",
               "Government publication, attributed derived shares only",
               "FY 2024-25 quick estimates at current prices. IndiaCiv estimates split the remaining "
               "FY 2025-26 city industry allocation using the prior-year mining and utilities proportions. "
               "SHA-256 2995e9f5b3a7740ea0c855bc08620a2dac3063719802b46f1a03aca57037875d.",
               ["City View industry output"]),
    SourceInfo("kerala_gsva_detail", "Kerala Economic Review 2025, Appendix 1.1.10",
               "Kerala State Planning Board / Directorate of Economics and Statistics",
               "https://spb.kerala.gov.in/economic-review/ER2025/appendix/01110.html",
               "Government publication, attributed derived shares only",
               "FY 2024-25 quick estimates at current prices. IndiaCiv estimates split the remaining "
               "FY 2025-26 city industry allocation using the prior-year mining and utilities proportions. "
               "SHA-256 fe2e02214bc5d5f0bd055499ecd83d15cba396b4956acbd25f6afbbb73596ffb.",
               ["City View industry output"]),
    SourceInfo("tamil_nadu_gsva_detail", "Tamil Nadu Estimates of State Domestic Product, Tables 18 and 20",
               "Department of Economics and Statistics, Tamil Nadu",
               "https://des.tn.gov.in/node/346",
               "Government publication, attributed derived shares only",
               "FY 2024-25 advance estimates at current prices. " + RESIDUAL_METHOD + " "
               "SHA-256 c3b445d76bdfb4f9c708ecda249fd419aae1acd34fb0ae2820d11b9799042b48.",
               ["City View industry output"]),
    SourceInfo("bihar_gsva_detail", "State Domestic Product of Bihar, November 2026 edition, Statements 4.2 and 5.2",
               "Directorate of Economics and Statistics, Bihar",
               "https://des.bihar.gov.in/viewStateIncomeDocument?file=si.pdf",
               "Government publication, attributed derived shares only",
               "FY 2024-25 quick estimates at current prices. " + RESIDUAL_METHOD,
               ["City View industry output"]),
]

# Relative weights within the city industry's remaining share, with only the split carried forward.
DETAIL_SPLITS = {
    "OD": ("odisha_gsva_fy26", 9.5, 3.3),
    "TS": ("telangana_gsva_fy26", 35_892, 37_692),
    "UP": ("uttar_pradesh_gsva_detail", 24_890, 73_145),
    "KL": ("kerala_gsva_detail", 299_377, 1_526_237),
    "TN": ("tamil_nadu_gsva_detail", 8_955, 80_127),
    "KA": ("karnataka_gsva_fy26", 19_598, 44_660),
    "MP": ("madhya_pradesh_gsva_fy26", 2.96, 3.35),
    "RJ": ("rajasthan_gsva_fy26", 3.30, 3.20),
    "JK": ("jammu_kashmir_gsva_fy26", .40, 4.57),
    "BR": ("bihar_gsva_detail", 3_691, 20_263),
}

SOURCES += [SourceInfo(
    "kerala_matched_gsdp_fy26", "Kerala Data Portal, Major Deficit Indicators, 3 February 2026 edition",
    "Government of Kerala",
    "https://datahub.kerala.gov.in/charts/"
    "eyJpdiI6IkN1ZXJsNk9XY1VzckxpSEk3SzEvSFE9PSIsInZhbHVlIjoiQUF5MHNXeTdlRlNzd1FZM0pNa0hEZz09IiwibWFjIjoi"
    "Yzg0MDNiZTMxYjU1ZjAwYmMwZGZiNDFkNDU5NTFjNGY0M2UxM2QyZTY4M2FmOWNmN2I0NzEyZmRiOTY0YjIwYSIsInRhZyI6IiJ9",
    "Government publication, derived growth only",
    "Nominal FY 2024-25 and FY 2025-26 GSDP from the same fiscal series. IndiaCiv estimates apply the same "
    "city urban population allocation shares to both years. "
    "Checked snapshot SHA-256 928a8f5216cc71f15639544bed94c508e87dba480eff31e848c046654915a378.",
    ["City output growth"],
), SourceInfo(
    "jharkhand_matched_gsdp_fy26", "Jharkhand Economic Survey 2025-26, Table 1.1 and §2.6.1",
    "Department of Finance, Government of Jharkhand",
    "https://finance.jharkhand.gov.in/pdf/JES_2025_26.pdf",
    "Government publication, derived growth only",
    "Current-price FY 2024-25 and 2025-26 GSDP. FY 2025-26 is the survey's budget estimate. "
    "IndiaCiv estimates use the same city allocation shares in both years. "
    "SHA-256 61784b9a0796e86b7aae4ba1d26f93ee712fa395d2581689ce4e0006c061a495.",
    ["City output growth"],
)]

# Published nominal pair in crore INR. The current-year fiscal estimate is source-provided.
MATCHED_GSDP = {
    "JH": (516_255, 556_286, "jharkhand_matched_gsdp_fy26"),
    "KL": (1_248_533.01, 1_427_145.23, "kerala_matched_gsdp_fy26"),
}

# Latest common nominal baseline in RBI Handbook tables 25, 33, 37, 41 and 49.
# Share of total GSVA. Agriculture & allied is total less industry and services.
# RBI industry includes construction. Table 29 alone covers a narrower activity.
# Columns: first FY year, industry, services, manufacturing, construction.
RBI_BASELINE = {
    "AN": (2023, 0.198159029, 0.681200026, 0.007224963, 0.142029156),
    "AR": (2024, 0.285955944, 0.486612506, 0.015927832, 0.087704338),
    "AS": (2024, 0.363069769, 0.420233628, 0.101368208, 0.098645969),
    "BR": (2024, 0.235660305, 0.540671661, 0.072058423, 0.138702081),
    "CH": (2023, 0.100278434, 0.894112957, 0.028556756, 0.054892763),
    "CG": (2024, 0.434822327, 0.364451372, 0.147004503, 0.156103579),
    "GA": (2023, 0.514284883, 0.423081019, 0.336287628, 0.042633761),
    "GJ": (2022, 0.482859688, 0.351406799, 0.352043120, 0.070000070),
    "HR": (2024, 0.284294457, 0.538629986, 0.170321023, 0.092000018),
    "HP": (2024, 0.392689481, 0.463915480, 0.265144226, 0.077268699),
    "JK": (2024, 0.189166833, 0.614567726, 0.061614182, 0.078171694),
    "JH": (2024, 0.386188735, 0.451857844, 0.196716037, 0.100272533),
    "KA": (2024, 0.201454219, 0.681317619, 0.123410923, 0.056495259),
    "KL": (2024, 0.239369629, 0.672795363, 0.091627139, 0.131383203),
    "LA": (2023, 0.176478414, 0.631121017, 0.016241170, 0.091055268),
    "MP": (2024, 0.222851639, 0.366071110, 0.070535398, 0.090263117),
    "MN": (2023, 0.098739112, 0.693874837, 0.015190706, 0.063729423),
    "ML": (2024, 0.194852108, 0.575626732, 0.078232336, 0.057394947),
    "MZ": (2023, 0.310611395, 0.493317246, 0.004062186, 0.087607353),
    "NL": (2023, 0.119310074, 0.605460522, 0.008565167, 0.083605279),
    "OD": (2024, 0.398708470, 0.384430734, 0.179078825, 0.091849658),
    "PY": (2024, 0.404353144, 0.545990319, 0.223837924, 0.160514038),
    "PB": (2024, 0.282539094, 0.484290045, 0.164550731, 0.082043689),
    "RJ": (2024, 0.271561048, 0.459181752, 0.115752602, 0.094719246),
    "SK": (2023, 0.616497596, 0.301981431, 0.331176128, 0.051642289),
    "TN": (2024, 0.333600645, 0.535972858, 0.182284472, 0.120520539),
    "TS": (2024, 0.186884568, 0.671632739, 0.084124168, 0.056392511),
    "TR": (2024, 0.172705397, 0.429077808, 0.024086954, 0.044091662),
    "UP": (2024, 0.267766431, 0.472590087, 0.103252709, 0.129736894),
    "UK": (2024, 0.458545948, 0.460152244, 0.261460663, 0.153222789),
    "WB": (2024, 0.216442104, 0.582714007, 0.125616493, 0.065274989),
}

# Statement 4, FY 2022-23 through FY 2025-26 (₹ crore, current prices).
NOMINAL_SERIES = {
    "agriculture": (4_756_194, 5_117_555, 5_589_683, 5_665_300),
    "industry": (6_181_147 + 506_017, 6_868_100 + 538_030, 7_434_059 + 572_560, 8_138_411 + 598_426),
    "services": (12_320_403, 13_792_418, 15_258_165, 17_084_704),
    "manufacturing": (3_482_190, 3_858_583, 4_179_232, 4_662_442),
    "construction": (2_109_100, 2_277_317, 2_449_208, 2_655_075),
}

# Nominal market-price FY 2025-26 growth from matched years in the pinned
# SDPAFY26002ANN snapshot. Delhi uses Economic Survey Table 2.1 instead.
GSDP_GROWTH = {
    "AP": .107546634, "AR": .118501615, "BR": .117699083, "CG": .115660649,
    "DL": 132_705_480 / 121_285_106 - 1, "GJ": .103913124, "JK": .088870932,
    "KA": .129041249, "MH": .103514651, "MP": .111367733, "OD": .094527809,
    "RJ": .102412429, "TN": .131617814, "TS": .107022663, "UK": .097442102, "WB": .098502956,
}


def carry_forward(year, key, share):
    series = NOMINAL_SERIES[key][year - 2022:]
    return share * prod(after / before for before, after in zip(series, series[1:]))


def state_sector_mix(state, name, period, *, for_city=False):
    if state in SECTOR_MIX and (state not in RBI_BASELINE or not for_city):
        record = {**SECTOR_MIX[state], "period": period, "vintage": period, "estimated": False}
        if state == "AP" and for_city:
            record["detail"] = {"mining": .0209, "manufacturing": .1084, "construction": .08, "utilities": .0273}
            record["detail_source"] = dict.fromkeys(record["detail"], "andhra_pradesh_gsva_detail_fy26")
        return record
    if state not in RBI_BASELINE:
        return None
    year, industry, services, manufacturing, construction = RBI_BASELINE[state]
    groups = {"agriculture": 1 - industry - services, "industry": industry, "services": services}
    projected = {key: carry_forward(year, key, share) for key, share in groups.items()}
    total = sum(projected.values())
    detail = {key: carry_forward(year, key, share) / total
              for key, share in {"manufacturing": manufacturing, "construction": construction}.items()}
    detail_source = {}
    residual = projected["industry"] / total - sum(detail.values())
    if for_city and state in DETAIL_SPLITS and residual > 0:
        source, mining, utilities = DETAIL_SPLITS[state]
        for key, weight in (("mining", mining), ("utilities", utilities)):
            detail[key] = residual * weight / (mining + utilities)
            detail_source[key] = source
    return {
        "state": name, "shares": {key: share / total for key, share in projected.items()},
        "detail": detail, **({"detail_source": detail_source} if detail_source else {}),
        "source": [RBI_SOURCE, NATIONAL_SOURCE], "period": period, "vintage": period,
        "status": "IndiaCiv estimate", "estimated": True, "description": METHOD,
    }
