"""Pinned 2026 snapshots for civilian services and the national poverty nowcast."""

from ..core.source import SourceInfo

PMAYG = "pmayg_july_2026"
PMAYU2 = "pmayu2_august_2026"
ABHA = "abha_november_2026"
PMJAY = "pmjay_august_2026"
PMJAY_STATES = "pmjay_states_october_2026"
POVERTY = "pip_september_2026"

SOURCES = [
    SourceInfo(PMAYG, "Achievement of target under PMAY-G, Lok Sabha answer 447, Annexure II",
               "Ministry of Rural Development / PIB",
               "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2287309&lang=1&reg=48",
               "PIB Copyright Policy (attributed, accurate reuse)",
               "Cumulative completions as of 16 July 2026. SHA-256 "
               "26d58aa4ad9708fcaaa6dd4020575594eab8b6416092ad82f9ccab94a16ad37c.",
               ["PMAY-Gramin completions per 1,000 residents"]),
    SourceInfo(PMAYU2, "Implementation of PMAY-Urban 2.0, Rajya Sabha answer 158, Annexure",
               "Ministry of Housing and Urban Affairs / Parliament of India",
               "https://sansad.in/getFile/annex/271/AS158_kY67IG.pdf?source=pqars",
               "Digital Sansad copyright policy requires permission for reproduction. Derived rates only.",
               "Cumulative PMAY-U 2.0 completions or deliveries reported on 3 August 2026. SHA-256 "
               "0cfd1658754ae6a7af4d3dff1c3c19518b8c0ad4a6f3bed579ac8c8ffbe767b4.",
               ["PMAY-Urban 2.0 completions and deliveries per 1,000 residents"],
               license_url="https://sansad.in/ls/privacyPolicy"),
    SourceInfo(ABHA, "ABDM public dashboard, state and UT ABHA counts",
               "National Health Authority / MoHFW", "https://dashboard.abdm.gov.in/",
               "Public dashboard aggregates (attributed derived rates only)",
               "State ABHA counts as of 26 November 2026 divided by projected 1 March 2026 population. "
               "State series excludes accounts without a state assignment. State response SHA-256 "
               "6ed8215436842b0e6cda22723c75a6fd8615ae66d1a19af130a10ec2eca3e5a2. "
               "National response SHA-256 318698b42c5682d3a2460c04feed2411ad42565fa8b00fc0f3b0e79b5f4d86de.",
               ["ABHA IDs per 100 residents"]),
    SourceInfo(PMJAY, "Affordable and accessible healthcare for all",
               "Ministry of Health and Family Welfare / PIB",
               "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2298390&lang=1&reg=3",
               "PIB Copyright Policy (attributed, accurate reuse)",
               "More than 45.5 crore Ayushman cards issued as of 12 August 2026. SHA-256 "
               "2495c87cb56ee15f84f71d4925906a60ea74c5ece1796c58c4f2100e7609fa6b.",
               ["India PM-JAY cards per 100 residents"]),
    SourceInfo(PMJAY_STATES, "Top 15 states by Ayushman cards created",
               "Scheme Kosh / National Health Authority",
               "https://schemekosh.com/ayushman-bharat-pradhan-mantri-jan-arogya-yojana/statistics/",
               "Publisher permits sharing and embedding with a link back. IndiaCiv shows derived rates.",
               "16 October 2026 snapshot of the 15 highest card totals, including cards from integrated state schemes. "
               "CSV SHA-256 7869b1a6f90c8fd95c0a02deb34e2fb2afe3f66e412ddd83809a854c86fd021f.",
               ["PM-JAY state cards per 100 residents"]),
    SourceInfo(POVERTY, "Poverty and Inequality Platform, September 2026 projections",
               "World Bank", "https://datacatalog.worldbank.org/search/dataset/0067066/pip-poverty-projections",
               "CC BY 4.0",
               "Calendar 2026 national nowcast for the $3.00 per person per day line (2021 PPP). "
               "Edition 20260922, Country FGT CSV SHA-256 "
               "30b44cbb1c755ddd777f1eff45f8dc26bbf94cc697d7fbf35312271ee1c5f784.",
               ["India poverty nowcast"], license_url="https://creativecommons.org/licenses/by/4.0/"),
]

# Cumulative completions divided by the 1 March 2026 projected population.
PMAYG_PER_1000 = {
    "AN": 3.576, "AP": 1.687, "AR": 22.189, "AS": 62.33, "BR": 31.672,
    "CG": 64.624, "DH": 4.385, "GA": 0.152, "GJ": 9.678, "HP": 9.106,
    "HR": 1.319, "IN": 21.802, "JH": 39.991, "JK": 23.5, "KA": 2.492,
    "KL": 1.105, "LA": 9.849, "LD": 0.643, "MH": 15.349, "ML": 46.422,
    "MN": 17.194, "MP": 48.376, "MZ": 19.994, "NL": 16.574, "OD": 57.021,
    "PB": 1.773, "RJ": 24.065, "SK": 1.968, "TN": 8.663, "TR": 87.779,
    "TS": 0.0, "UK": 5.69, "UP": 15.0, "WB": 34.027,
}

# Cumulative completions divided by the 1 March 2026 projected population.
PMAYU2_PER_1000 = {
    "AN": 0.002, "AP": 0.037, "AR": 0.89, "AS": 0.002, "BR": 0.003,
    "CG": 0.121, "CH": 0.024, "DH": 0.496, "DL": 0.162, "GA": 0.021,
    "GJ": 0.531, "HP": 0.006, "HR": 0.044, "IN": 0.102, "JH": 0.003,
    "JK": 0.001, "KA": 0.016, "KL": 0.008, "LA": 0.102, "MH": 0.301,
    "ML": 0.003, "MN": 0.001, "MP": 0.122, "MZ": 0.002, "OD": 0.07,
    "PB": 0.086, "PY": 0.032, "RJ": 0.172, "TN": 0.03, "TR": 0.016,
    "TS": 0.105, "UK": 0.099, "UP": 0.03, "WB": 0.051,
}

# Cumulative cards from the 15-state snapshot divided by the 1 March 2026 projected population.
PMJAY_PER_100 = {
    "AP": 34.9, "AS": 48.2, "BR": 30.2, "CG": 79.6, "GJ": 40.0,
    "HR": 45.4, "JH": 34.8, "KA": 27.9, "MH": 34.0, "MP": 50.6,
    "OD": 77.2, "PB": 40.7, "RJ": 27.5, "UP": 25.2, "WB": 41.4,
}

# Derived rates. The national dashboard total includes accounts without a state assignment.
ABHA_PER_100 = {
    "AN": 75.6, "AP": 95.0, "AR": 42.7, "AS": 67.7, "BR": 51.6,
    "CG": 85.2, "CH": 71.3, "DH": 47.4, "DL": 51.2, "GA": 65.1,
    "GJ": 71.9, "HP": 91.0, "HR": 64.4, "IN": 69.5, "JH": 51.2,
    "JK": 82.7, "KA": 58.6, "KL": 69.6, "LA": 88.8, "LD": 103.3,
    "MH": 59.9, "ML": 50.1, "MN": 53.8, "MP": 67.4, "MZ": 70.4,
    "NL": 42.3, "OD": 97.6, "PB": 60.8, "PY": 52.9, "RJ": 87.5,
    "SK": 68.8, "TN": 40.3, "TR": 77.6, "TS": 79.3, "UK": 68.2,
    "UP": 65.8, "WB": 100.3,
}
