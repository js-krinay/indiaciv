"""Pinned City View source records and reviewed geographic crosswalks."""

from ..core.source import SourceInfo
from .city_sources import PIB, PIB_TERMS

HPI_SOURCE = "rbi_hpi_q1_2026"
HPI_TABLE_URL = "https://data.rbi.org.in/DBIE/#/dbie/reports/Statistics/Real%20Sector/Prices%20&%20Wages"
HPI_PERIOD = "Apr–Jun 2026"
# Reviewed transcription of the RBI DBIE House Price Index table, Base Year
# 2022-23 = 100, row Q1.2026-27(P), as retrieved on 27 November 2026.
MARKETS = {
    "Ahmedabad": {"index": "118.83"},
    "Bangalore": {"index": "127.08"},
    "Chandigarh": {"index": "147.26"},
    "Chennai": {"index": "166.85"},
    "Delhi": {"index": "96.22"},
    "Gautam Buddha Nagar": {"index": "103.08"},
    "Ghaziabad": {"index": "122.59"},
    "Hyderabad": {"index": "103.52"},
    "Jaipur": {"index": "145.41"},
    "Kanpur": {"index": "126.62"},
    "Kochi": {"index": "119.64"},
    "Kolkata": {"index": "108.07"},
    "Lucknow": {"index": "137.08"},
    "Mumbai": {"index": "108.24"},
    "Nagpur": {"index": "114.00"},
    "Pune": {"index": "112.44"},
    "Thane": {"index": "114.38"},
    "Thiruvananthapuram": {"index": "122.17"},
}

PIB_POLICY = "https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=19&reg=48"

# When a release only establishes occurrence by the publication date, use reported_on.
EVENTS = [
    {
        "id": "arnab-vijayawada", "type": "Cyclone", "label": "Cyclone Arnab",
        "start_date": "2026-10-28", "end_date": "2026-10-29", "reported_on": "2026-11-04",
        # Punnami Ghat, Vijayawada, falls in the map's Krishna district.
        "districts": ["28-547"], "source": "pib_2332675", "url": PIB + "2332675",
    },
    {
        "id": "arnab-odisha-flooding", "type": "Flood", "label": "Flooding after Cyclone Arnab",
        "start_date": None, "end_date": None, "reported_on": "2026-10-30",
        "districts": ["21-388", "21-389", "21-390"], "source": "pib_2330702", "url": PIB + "2330702",
    },
    {
        "id": "bihar-september-flooding", "type": "Flood", "label": "September flooding in Bihar",
        "start_date": None, "end_date": None, "reported_on": "2026-09-16",
        "districts": ["10-220", "10-224", "10-226"], "source": "pib_2311105", "url": PIB + "2311105",
    },
    {
        "id": "kalladi-landslide", "type": "Landslide", "label": "Kalladi landslide",
        "start_date": None, "end_date": None, "reported_on": "2026-07-08",
        "districts": ["32-590"], "source": "pib_2282492", "url": PIB + "2282492",
    },
]

EVENT_SOURCES = [
    SourceInfo(event["source"], event["label"], publisher + " via Press Information Bureau",
               event["url"], PIB_TERMS, description, ["City View hazard events"], license_url=PIB_POLICY)
    for event, publisher, description in zip(EVENTS, (
        "Ministry of Rural Development", "Ministry of Communications", "Ministry of Agriculture & Farmers Welfare",
        "Ministry of Home Affairs",
    ), (
        "PIB release 2332675, 4 November 2026. Dates of the temporary closure at Punnami Ghat.",
        "PIB release 2330702, 30 October 2026. Districts named in the Odisha floodwaters and telecom update.",
        "PIB release 2311105, 16 September 2026. Flood situation reviewed in Hajipur (Vaishali), Munger and Bhagalpur.",
        "PIB release 2282492, 8 July 2026. Confirmation of a landslide in Kalladi, Wayanad district.",
    ))
]

HOUSING_INFO = SourceInfo(
    HPI_SOURCE, "All-India House Price Index for Q1:2026-27", "Reserve Bank of India",
    HPI_TABLE_URL, "RBI copyright policy permits accurate, unmodified reproduction with RBI acknowledgement.",
    "RBI release 2026-2027/958, 24 August 2026. DBIE House Price Index table snapshot reviewed"
    " 27 November 2026. Public assets carry only the difference between the provisional index and the 2022-23 base of 100.",
    ["Explorer housing markets"], license_url="https://rbi.org.in/scripts/Disclaimer.aspx",
)
