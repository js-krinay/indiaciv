"""Source citations for the state metrics preparation step."""

from ..core.source import SourceInfo
from .projections import CHECKSUM as TG_SHA


PINS = {
    "wage-schedule": "6d94625a3a7e9b0b8fc78c1f09dbf1714183b4118bf60b4fdb84c6fc79336744",
    "wage": "a853dbe4897643c4bd95467e7e7a25454f45c942b051b0f64380ac3001c6183e",
    "plfs": "16fee8073720fedff1f4fcfed661faf702f655fd7aeaf3585aadba276c8a083a",
    "jjm": "a9993f65414de8bdaaced4c09757457ee39b67df6d2a245d42f4ef69a13c0bee",
    "gsdp": "bf31457ca2b7d32ff51557a3f2c69c4765c18e8ba940bc3cfe32827ab9c62fcd",
    "gsdp-mirror": "4ff1795f8f3cfc31da192a28eaebcbefe94fdbd397a873afe8650745f8b0e308",
    "delhi": "e180f689f94cf954f5712cdcd643a9e964d28a5b6d34c8aa03ed89c670e83509",
    "gdp": "2074d6eb285a446642749c535e4a57055b4b948a8d38509cf59bfdacf37fa0db",
    "cea": "f9e5faab4f6d485ecbe37276f0e037ae1acf981440b4e89825ba9534d3f9b8d8",
}
# The same dated PIB annex can be served with a different template.
JJM_RESEARCH_SHA = "4fc936bd8ef0a263189ef5b32aef3cddbdaca0e0b595aa82a37f107b4bae61dd"



SOURCES = [
    SourceInfo("public_works_wage", "Rural jobs guarantee wage schedule, S.O. 3518(E)",
               "Ministry of Rural Development / Gazette of India",
               "https://egazette.gov.in/WriteReadData/2026/273958.pdf",
               "Public statutory notification (attributed numeric rates)",
               "Effective 1 July 2026. SHA-256 " + PINS["wage-schedule"],
               ["Rural jobs guarantee wage"]),
    SourceInfo("public_works_wage_india", "Revised rural jobs guarantee wages",
               "Ministry of Rural Development / PIB",
               "https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2279660&lang=2&reg=48",
               "PIB Copyright Policy (attributed, accurate reuse)",
               "National notified wage average, effective 1 July 2026. SHA-256 " + PINS["wage"],
               ["India comparison for the rural jobs guarantee wage"]),
    SourceInfo("plfs_q3", "Periodic Labour Force Survey quarterly bulletin, July–September 2026",
               "NSO / MoSPI", "https://mospi.gov.in/uploads/publications_reports/publications_reports1794297172776_05eae330-7f2d-45ec-84c5-07031201ecf1_PLFS_QB_July-Sept_2026_m.pdf",
               "MoSPI Copyright Policy (NSO data, attribution required)",
               "Appendix A, Tables 2–5. Current Weekly Status, age 15 and over. SHA-256 " + PINS["plfs"],
               ["Labour lenses and India comparisons"]),
    SourceInfo("jjm_july", "Jal Jeevan Mission rural tap water coverage annex",
               "Ministry of Jal Shakti / PIB", "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2290048&lang=1&reg=3",
               "PIB Copyright Policy (attributed, accurate reuse)",
               "Reported connections on 18 July 2026. SHA-256 " + PINS["jjm"],
               ["Rural homes with tap water"]),
    SourceInfo("tg_urban", "Technical Group population projections, Tables 9 and 10",
               "MoHFW / National Commission on Population",
               "https://nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf",
               "NHM Copyright Policy (prominent attribution)",
               "Projected urban share on 1 March 2026. SHA-256 " + TG_SHA,
               ["Urban population share"]),
    SourceInfo("gsdp_fy26", "Nominal Gross State Domestic Product, regional accounts table SDPAFY26002ANN",
               "NSO / MoSPI", "https://api.mospi.gov.in/api/nas/getNASData?base_year=2011-12&series=Current&frequency_code=1&account_code=2&indicator_code=23&limit=100&page=1",
               "MoSPI Copyright Policy (NSO data, attribution required)",
               "Nominal state output from the regional accounts. IndiaCiv estimates city output growth from "
               "the matched state growth rates and fixed city allocation weights. SHA-256 " + PINS["gsdp"],
               ["GSDP per person", "City output growth"]),
    SourceInfo("delhi_gsdp_fy26", "Economic Survey of Delhi, FY 2025-26",
               "Delhi Planning Department", "https://delhiplanning.delhi.gov.in/sites/default/files/2026-03/economic_survey_english_0.pdf",
               "Delhi Planning Department Copyright Policy (attribution for references)",
               "One cited nominal GSDP figure used to compute a per-resident indicator. SHA-256 " + PINS["delhi"],
               ["GSDP per person in Delhi"]),
    SourceInfo("gsdp_components", "State GSDP derived from MoSPI components, October 2026 edition",
               "Measure of India / MoSPI", "https://measure.thisindianlife.today/data/states-gsdp-current/",
               "CC BY 4.0 (compilation)",
               "GSVA plus taxes less subsidies for Assam, Haryana, Ladakh and Nagaland. SHA-256 " + PINS["gsdp-mirror"],
               ["Base inputs for IndiaCiv estimates of nominal GSDP per person"]),
    SourceInfo("gdp_fy26", "Provisional annual GDP estimates, FY 2025-26",
               "NSO / MoSPI", "https://www.mospi.gov.in/uploads/latestReleases/latest_release_1780655857536_5ac01869-ca4a-422d-b7a7-57b81da60932_Press_Note_on_GDP_Estimates_for_Q4_2025-26_and_PE_FY_2025-26_F.pdf",
               "MoSPI Copyright Policy (NSO data, attribution required)",
               "Statement 2 reports nominal GDP and annual growth. SHA-256 " + PINS["gdp"],
               ["India GDP comparison and nominal growth for GSDP estimates"]),
    SourceInfo("cea_fy26", "Load Generation Balance Report, Annex II",
               "Central Electricity Authority", "https://cea.nic.in/api/dashboardReports/download-pdf/en/db851876-390a-48c4-b450-d3ce66b64a89",
               "CEA website policy (permission required for reproduction of source content)",
               "Actual electricity availability, FY 2025-26. IndiaCiv displays calculated per-resident ratios. SHA-256 " + PINS["cea"],
               ["Electricity supplied per person"]),
]
