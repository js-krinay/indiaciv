"""Source-backed inputs for state employment and Internet subscription estimates."""

from ..core.source import SourceInfo

INTERNET_SOURCE = "trai_internet_june_2026"
SOURCES = [
    SourceInfo(
        INTERNET_SOURCE, "Indian Telecom Services Performance Indicators, April–June 2026, Table 1.43",
        "Telecom Regulatory Authority of India",
        "https://www.trai.gov.in/sites/default/files/2026-10/QPIR_12102026.pdf",
        "TRAI website policy requires permission for reproduction. IndiaCiv publishes independently derived rates.",
        "June subscriptions divided by Technical Group projected 1 March 2026 residents. Rates are rounded "
        "to one decimal and can exceed 100 because residents may have multiple subscriptions. Report SHA-256 "
        "fefa37efa1565848cea8609f05f06b2e78cd2157ae09f5993d3ae2bc2e19762a.",
        ["State Internet subscription lens, Knowledge advisor and Explorer"],
        license_url="https://www.trai.gov.in/website-policy",
    ),
]

# Appendix A Table 3, all ages, rural + urban, persons. Same pinned bulletin as plfs_2026_q3.
ALL_AGES_WPR = {
    'AP': 42.4, 'AS': 43.6, 'BR': 30.0, 'CG': 41.1, 'DL': 31.1,
    'GJ': 44.3, 'HR': 35.4, 'HP': 50.3, 'JH': 34.1, 'KA': 46.2,
    'KL': 37.9, 'MP': 43.2, 'MH': 42.6, 'OD': 43.5, 'PB': 38.9,
    'RJ': 43.0, 'TN': 45.4, 'TS': 44.8, 'UK': 41.9, 'UP': 33.9,
    'WB': 43.5, 'JK': 41.2,
}

# Derived rates only. See the source entry above for the denominator and period.
INTERNET_PER_100 = {
    'AP': 75.8, 'AR': 76.7, 'AS': 67.2, 'BR': 51.2, 'CG': 67.2,
    'GA': 147.1, 'GJ': 86.9, 'HR': 112.7, 'HP': 97.8, 'JH': 57.0,
    'KA': 104.0, 'KL': 100.0, 'MP': 63.6, 'MH': 100.6, 'MN': 68.0,
    'ML': 74.7, 'MZ': 103.0, 'NL': 62.8, 'OD': 69.7, 'PB': 95.6,
    'RJ': 69.9, 'SK': 89.0, 'TN': 88.5, 'TS': 99.2, 'TR': 70.9,
    'UP': 64.0, 'UK': 89.0, 'WB': 70.0, 'AN': 113.3, 'CH': 121.5,
    'DH': 59.1, 'DL': 177.5, 'JK': 87.7, 'LA': 147.5, 'LD': 100.0,
    'PY': 77.4,
}
