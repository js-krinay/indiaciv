"""Reviewed 2026 incident facts and their date-pinned source editions."""

from ..core.source import SourceInfo
from .city_conditions_sources import EVENTS, EVENT_SOURCES

PERIOD = "1 Jan – 27 Nov 2026"
COVERAGE = (
    "Selected documented 2026 events. Earthquake counts use the NCS January–October lists for epicentres "
    "of magnitude 5.0 or higher. Cyclone counts include "
    "documented landfall and observed weather. The May Uttar Pradesh thunderstorm uses districts "
    "confirmed by the state damage report reproduced by IMD. Districts are mapped to atlas boundaries. "
    "Coverage varies by type and area."
)
IMD = "https://mausam.imd.gov.in/"
NCS = "https://seismo.gov.in/sites/default/files/"
FACTS_ONLY = "Publisher copyright retained. IndiaCiv publishes attributed incident facts and derived counts."

SOURCES = [*EVENT_SOURCES]
INCIDENTS = [dict(event) for event in EVENTS]


def source(id, title, publisher, url, edition, *, terms=FACTS_ONLY, license_url=None):
    SOURCES.append(SourceInfo(id, title, publisher, url, terms, edition,
                              ["Disasters inventory and counts", "City View hazards"], license_url=license_url))
    return {"source": id, "url": url, "publisher": publisher}


arnab = source("imd_arnab_20261028", "Cyclone Arnab landfall", "India Meteorological Department",
               IMD + "Forecast/mcmarq/mcmarq_data/Press%20Release%20Dtd%2028.10.2026.pdf",
               "IMD press release, 28 October 2026, 13:00 IST.")
murasu = source("imd_murasu_20261105", "Observed passage of Cyclone Murasu", "India Meteorological Department",
                IMD + "Forecast/marquee_data/ERF%2005.11.26.pdf",
                "IMD extended-range release, 5 November 2026, observed weather through 4 November.")
akvan = source("imd_akvan_20261121", "Cyclone Akvan", "India Meteorological Department",
               IMD + "backend/assets/cyclone_pdf/42__National_Bulletin_No_42-20Nov2026_2330IST.pdf",
               "National bulletin 42, BOB/10/2026, issued 21 November 2026 at 01:15 IST.")
akvan_landfall = source("imd_akvan_20261120", "Akvan landfall and observed rainfall",
                        "India Meteorological Department",
                        IMD + "backend/assets/cyclone_pdf/11_Hourly_Bulletin_201126_0930IST.pdf",
                        "Hourly bulletin 11, issued 20 November 2026 at 10:20 IST.")
banda = source("imd_heat_20260518", "Observed heatwave at Banda", "India Meteorological Department",
               IMD + "Forecast/marquee_data/special%20Press%20Release%2018-05-2026.pdf",
               "IMD special press release, 18 May 2026, observed-weather section.")
mon = source("gsi_mon_landslide_20260719", "Mon town landslide field assessment",
             "Geological Survey of India",
             "https://bhusanket.gsi.gov.in/Output/LS_Incidence_Report/2026/Preliminary%20Assessment%20of%20the%20Landslide%20Incidence%20at%20Defense%20Colony%2C%20Tamnam%20Ward%2C%20Mon%20Town%2C%20Nagaland.pdf",
             "Field assessment of the 19 July 2026 Mon town slide, inventory NL/MON/83N02/2026/01.")
tizit = source("nagaland_tizit_flood_20260719", "Tizit flooding",
               "Nagaland Department of Information & Public Relations",
               "https://ipr.nagaland.gov.in/index.php/incessant-rainfall-causes-flood-like-situation-in-tizit",
               "Nagaland DIPR release of 19 July 2026.")
up_storm = source("imd_up_storm_20260513", "Uttar Pradesh thunderstorm of 13 May 2026",
                  "India Meteorological Department and Uttar Pradesh State Disaster Management Authority",
                  "https://internal.imd.gov.in/press_release/20260515_pr_4986.pdf",
                  "14 May 2026 report, including the Uttar Pradesh SDMA damage report (Table 1). "
                  "PDF SHA-256 486768e6d70f3e0f114fba1e96390c22177936ec284be03104c728f0e53c1d8d.")

INCIDENTS[0].update(id="cyclone-arnab", start_date="2026-10-26", end_date="2026-10-28",
                    landfall_date="2026-10-28", districts=["28-545", "28-547"],
                    state_names=["Puducherry"], area="Andhra Pradesh coast southwest of Yanam",
                    related_sources=[{"source": INCIDENTS[0]["source"], "url": INCIDENTS[0]["url"],
                                      "publisher": "Press Information Bureau"}], **arnab)
INCIDENTS.extend([
    # Table 1 names affected districts. Duplicate Varanasi entries count once.
    # Sambhal has no equivalent district in the atlas's Census 2011 geography.
    dict(id="up-thunderstorm-20260513", type="Thunderstorm", label="Uttar Pradesh thunderstorm",
         start_date="2026-05-13", reported_on="2026-05-14", vintage="2026",
         area="Uttar Pradesh districts identified in the state damage report",
         districts=["09-135", "09-149", "09-150", "09-152", "09-153", "09-154", "09-155",
                    "09-156", "09-158", "09-163", "09-172", "09-173", "09-174", "09-175",
                    "09-176", "09-178", "09-180", "09-181", "09-182", "09-185", "09-190",
                    "09-193", "09-196", "09-197", "09-198", "09-199", "09-200"], **up_storm),
    dict(id="cyclone-murasu", type="Cyclone", label="Cyclone Murasu", start_date="2026-11-01",
         end_date="2026-11-04", reported_on="2026-11-05", landfall_date="2026-11-03",
         districts=["28-549"], area="Landfall near Ongole", state_names=["Andhra Pradesh", "Telangana", "Andaman & Nicobar",
                                            "Tamil Nadu", "Puducherry"], **murasu),
    dict(id="cyclone-akvan", type="Cyclone", label="Cyclone Akvan", start_date="2026-11-15",
         end_date="2026-11-20", reported_on="2026-11-21", landfall_date="2026-11-20",
         districts=["21-378", "21-379", "21-380", "21-387", "21-388", "28-542"],
         area="Landfall near Gopalpur", related_sources=[akvan_landfall], **akvan),
    dict(id="banda-heatwave", type="Heatwave", label="Banda heatwave", start_date="2026-05-17",
         end_date=None, reported_on="2026-05-18", districts=["09-170"], **banda),
    dict(id="mon-town-landslide", type="Landslide", label="Mon town landslide", start_date="2026-07-19",
         end_date=None, reported_on=None, districts=["13-261"],
         impact={"district": "13-261", "deaths": 8, "houses_destroyed": 12}, **mon),
    dict(id="tizit-flooding", type="Flood", label="Tizit flooding", start_date="2026-07-19",
         end_date=None, reported_on="2026-07-19", districts=["13-261"], **tizit),
])

MONTHLY_REPORTS = [
    ("Jan", "Web-Report-JAN-2026_0"),
    ("Feb", "Web_Report_FEB_2026_0"),
    ("Mar", "monthly_report/WebReportMAR2026"),
    ("Apr", "Web-Report-APR-2026"),
    ("May", "Web-Report-MAY-2026"),
    ("Jun", "monthly_report/WebReportJUN2026"),
    ("Jul", "monthly_report/WebReportJUL2026"),
    ("Aug", "monthly_report/WebReportAUG2026"),
    ("Sep", "monthly_report/WebReportSEP2026"),
    ("Oct", "monthly_report/WebReportOCT2026"),
]
MONTHLY = {
    month: source(f"ncs_monthly_2026_{number:02d}", f"NCS monthly earthquake report · {month} 2026",
                  "National Center for Seismology", NCS + filename + ".pdf",
                  f"Technical report NCS/2026/{number:02d}, table 1.",
                  terms="NCS copyright policy allows accurate reproduction with attribution, "
                        "subject to third-party exclusions. The atlas uses selected event facts.",
                  license_url="https://seismo.gov.in/copyright-policy")
    for number, (month, filename) in enumerate(MONTHLY_REPORTS, 1)
}
# Domestic epicentres reported in the reviewed monthly M ≥ 5.0 tables.
# Match the coordinates to the atlas polygons during the build.
for month, day, area, state, magnitude, lon, lat in [
    ("Jan", "2026-01-05", "Morigaon", "Assam", 5.1, 92.29, 26.37),
    ("Jan", "2026-01-19", "Leh", "Ladakh", 5.7, 74.32, 36.71),
    ("Jan", "2026-01-22", "Changlang", "Arunachal Pradesh", 5.0, 96.86, 27.45),
    ("Mar", "2026-03-27", "Leh", "Ladakh", 5.0, 74.352, 36.701),
    ("Apr", "2026-04-21", "Kamjong", "Manipur", 5.2, 94.415, 24.703),
    ("Jun", "2026-06-05", "Chamba", "Himachal Pradesh", 5.0, 76.423, 32.274),
    ("Aug", "2026-08-05", "Upper Siang", "Arunachal Pradesh", 5.4, 94.739, 29.008),
    ("Aug", "2026-08-06", "Upper Siang", "Arunachal Pradesh", 5.1, 94.856, 29.124),
    ("Aug", "2026-08-13", "Leh", "Ladakh", 5.5, 74.402, 36.881),
]:
    INCIDENTS.append(dict(id=f"earthquake-{day}", type="Earthquake", label=f"{area} earthquake",
                          start_date=day, end_date=None, reported_on=None, area=area, magnitude=magnitude,
                          districts=[], state_names=[state], lon_lat=(lon, lat), **MONTHLY[month]))

SOURCES.append(SourceInfo("india_disasters_2026", "IndiaCiv documented hazard inventory",
                          "IndiaCiv, based on NCS, IMD, PIB, GSI and Nagaland DIPR", "https://seismo.gov.in/monthly-report",
                          FACTS_ONLY, f"Snapshot through 27 November 2026. {COVERAGE}",
                          ["Disasters lens and geographic counts"]))
