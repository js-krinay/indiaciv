"""Pinned sources for historical household metrics."""

from ..core.source import SourceInfo

INTERIM = "household_costs"
HCES = "mospi_hces_2023_24"
TELECOM = "mospi_cms_telecom_2025"
NFHS = "mohfw_nfhs6"
RENT = "mospi_nss76_rent"
POVERTY = "rbi_rangarajan_2022_23"
PILOT = "mospi_up_hces_pilot"
PILOT_INTERIM = "up_hces_pilot"
PERIODS = {
    HCES: "HCES 2023–24 (1 Aug 2023 to 31 Jul 2024)",
    TELECOM: "CMS Telecom 2025 (1 Jan – 31 Mar 2025)",
    RENT: "NSS 76 (1 Jul – 31 Dec 2018)",
    NFHS: "NFHS-6 (28 May 2023 to 31 Dec 2024)",
    POVERTY: "HCES 2022–23 (1 Aug 2022 to 31 Jul 2023)",
    PILOT: "HCES 2022–23 (1 Aug 2022 to 31 Jul 2023)",
}
REPORTS = {
    HCES: ("Final_Report_HCES_2023-24L.pdf",
           "368deb9c858dcc71c3bf0e6cad096a31b5b337a724cf92a113637f3302ea268e", 11_737_505),
    TELECOM: ("CMST_report_m.pdf",
              "7dab0b4f5882870d48a5ee8c3aaa0bf287790a5cbd414b6d4b273133aeabcd05", 5_985_281),
    NFHS: ("111ff4a13ca36b5cabb7f94aec5bb0ce.pdf",
           "6b7d4eef047ddc5f37b6afa3935dab997a3b7ffff51ceb609eead44c34e25994", 48_942_602),
    RENT: ("Report_584_final.pdf",
           "a2a655e4e2e0469db67645ce007e3e6e5951e1b35620b1889f518b5b2f00ea23", 45_081_366),
    POVERTY: ("BS_ViewBulletin.aspx",
              "0a541249e40562dc949338c02327897545d6e47bb76d5a3ca52401700edde3f9", 215_774),
    PILOT: ("PRID-2201360.html",
            "89f98f21b42999953d247d28b23ba62420b8c4c75fe3c6c37f1d14bee8c79aec", 596_497),
}
MOSPI_BASE = "https://mospi.gov.in/sites/default/files/publication_reports/"
SOURCES = [
    SourceInfo(
        id=PILOT, title="Uttar Pradesh district MPCE small-area estimation pilot",
        publisher="MoSPI via Press Information Bureau",
        homepage="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2201360&lang=1&reg=3",
        license="PIB copyright policy. Attributed derived comparisons.",
        license_url="https://www.pib.gov.in/content/186_2_Copyright-Policy.aspx",
        description="Use the official spatial Fay–Herriot estimates and divide each by the Uttar Pradesh "
                    "HCES 2022–23 mean for the same sector from MoSPI Report 592, Table 3.2. "
                    "Exclude historic districts affected by the four documented subdivisions.",
        used_for=["Explorer city and district household consumption comparisons"],
    ),
    SourceInfo(
        id=POVERTY, title="Is Consumption Inequality Declining? RBI Bulletin, 24 September 2025, Table 3",
        publisher="Reserve Bank of India Bulletin authors",
        homepage="https://www.rbi.org.in/scripts/BS_ViewBulletin.aspx?Id=23647",
        license="RBI Bulletin. Attributed derived comparisons only.",
        license_url="https://www.rbi.org.in/scripts/Disclaimer.aspx",
        description=f"HTML SHA-256 {REPORTS[POVERTY][1]}. Authors' estimates from HCES 2022–23 "
                    "using state and sector Rangarajan poverty lines re-priced with component indices. "
                    "IndiaCiv divides each state rate by the same-sector median across the "
                    "18 boundary-compatible states and multiplies by 100.",
        used_for=["Rural and urban monetary poverty indexes"],
    ),
    SourceInfo(
        id=RENT, title="NSS 76th round, Report 584, Statement 24.5",
        publisher="MoSPI", homepage="https://mospi.gov.in/sites/default/files/NSS7612dws/" + REPORTS[RENT][0],
        license="MoSPI copyright policy. Attributed derived comparisons.",
        license_url="https://www.mospi.gov.in/CopyrightPolicy",
        description=f"PDF SHA-256 {REPORTS[RENT][1]}. Divide the mean monthly rent among renter "
                    "households by the corresponding national mean and multiply by 100.",
        used_for=["Rental-cost indexes"],
    ),
    SourceInfo(
        id=HCES, title="Household Consumption Expenditure Survey, Report 592, Statements 2R and 2U",
        publisher="MoSPI", homepage=MOSPI_BASE + REPORTS[HCES][0],
        license="MoSPI copyright policy. Attributed derived comparisons.",
        license_url="https://www.mospi.gov.in/CopyrightPolicy",
        description=f"PDF SHA-256 {REPORTS[HCES][1]}. Divide mean monthly consumption per person by "
                    "the contemporaneous India mean for the same sector and multiply by 100.",
        used_for=["Rural and urban household consumption indexes"],
    ),
    SourceInfo(
        id=TELECOM, title="Comprehensive Modular Survey: Telecom, Report 593, Appendix A Table 14",
        publisher="MoSPI", homepage=MOSPI_BASE + REPORTS[TELECOM][0],
        license="MoSPI copyright policy. Attributed derived shares.",
        license_url="https://www.mospi.gov.in/CopyrightPolicy",
        description=f"PDF SHA-256 {REPORTS[TELECOM][1]}. Multiply the share of households with internet "
                    "at home by the share of connected households using fixed/Wi-Fi service.",
        used_for=["Fixed/Wi-Fi use among all households"],
    ),
    SourceInfo(
        id=NFHS, title="National Family Health Survey 6 provisional state factsheets, indicator 7",
        publisher="MoHFW and IIPS",
        homepage="https://www.mohfw-dohfw.gov.in/static/uploads/2026/05/" + REPORTS[NFHS][0],
        license="Government publication. Attributed derived complement.",
        description=f"PDF SHA-256 {REPORTS[NFHS][1]}. Subtract the reported share of households with "
                    "at least one usual member covered by a health financing scheme from 100%.",
        used_for=["Households without health insurance or financing coverage"],
    ),
]
