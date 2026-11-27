"""Derived shares from pinned official advance estimates of nominal GSVA."""

from math import prod

from ..core.source import SourceInfo

RBI_SOURCE = "rbi_state_gsva"
NATIONAL_SOURCE = "mospi_national_gva_fy26"
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
]


def sector_mix(state, source, agriculture, industry, services, total):
    shares = {name: value / total for name, value in
              zip(("agriculture", "industry", "services"), (agriculture, industry, services))}
    return dict(state=state, source=source.id, publisher=source.publisher, status="Advance estimate", shares=shares)


SECTOR_MIX = {
    "DL": sector_mix("Delhi", SOURCES[0], 322_764, 637_029 + 15_424_468, 103_379_535, 119_763_796),
    "MH": sector_mix("Maharashtra", SOURCES[1], 473_089, 65_349 + 1_043_844, 2_855_198, 4_437_480),
    "AP": sector_mix("Andhra Pradesh", SOURCES[2], 539_454, 384_471, 700_717, 1_624_642),
}

for state, components, total in (
    ("DL", (637_029, 5_014_381, 6_859_334, 3_550_753), 119_763_796),
    ("MH", (65_349, 657_015, 297_238, 89_591), 4_437_480),
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
               "with mining and quarrying added to the secondary sector.", ["Economy"]),
]

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


def state_sector_mix(state, name, period):
    if state in SECTOR_MIX:
        return {**SECTOR_MIX[state], "period": period, "estimated": False}
    if state not in RBI_BASELINE:
        return None
    year, industry, services, manufacturing, construction = RBI_BASELINE[state]
    groups = {"agriculture": 1 - industry - services, "industry": industry, "services": services}
    projected = {key: carry_forward(year, key, share) for key, share in groups.items()}
    total = sum(projected.values())
    detail = {"manufacturing": manufacturing, "construction": construction}
    return {
        "state": name, "shares": {key: share / total for key, share in projected.items()},
        "detail": {key: carry_forward(year, key, share) / total for key, share in detail.items()},
        "source": [RBI_SOURCE, NATIONAL_SOURCE], "period": period,
        "status": "IndiaCiv estimate", "estimated": True, "description": METHOD,
    }
