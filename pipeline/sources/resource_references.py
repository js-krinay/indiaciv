"""References for curated 2026 location facts. No source maps or documents are bundled."""

from ..core.source import SourceInfo

PIB_POLICY = "https://www.pib.gov.in/content/186_2_Copyright-Policy.aspx"
CROP_PERIOD = "Crop year 2025-26 (1 Jul 2025 – 30 Jun 2026)"
MINE_PERIOD = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
FIELD_CROPS = {"rice", "wheat", "millets", "sugarcane", "cotton", "jute"}


def pib(id, title, release, description, date):
    return SourceInfo(id, f"{title} ({date})", "Press Information Bureau, Government of India",
                      f"https://www.pib.gov.in/PressReleasePage.aspx?PRID={release}",
                      "PIB copyright policy (reproduction with attribution)",
                      description, ["resources"], license_url=PIB_POLICY)


REFERENCES = [
    SourceInfo("hcl_mines", "Hindustan Copper 58th Annual Report FY 2025-26", "Hindustan Copper",
               "https://tcp.hindustancopper.com/Upload/Reports/0-639233596169693750-AnnualReport.pdf",
               "Operator copyright. Uses site and operating facts with attribution.",
               "Confirms Malanjkhand and Khetri production. Approximate positions from HCL tender "
               "0-638141401373666250 and MoEFCC 11th EAC mining meeting item 2.28.", ["resources"]),
    SourceInfo("hzl_mines", "Hindustan Zinc Integrated Annual Report FY 2025-26", "Hindustan Zinc",
               "https://integratedreport.hzlindia.com/annual-integrated-report-fy-2025-26/mines-performance-overview/index.html",
               "Operator copyright. Uses site, commodity and operating facts with attribution.",
               "Confirms production at five complexes. Locations are approximate, based on mine clearance "
               "documents (20th EAC mining meeting, Sindesar Khurd PFR, Rajpura Dariba PFR, Zawar PFR and Kayad EIA). "
               "The Sindesar Khurd mine profile verifies silver as a by-product.", ["resources"]),
    SourceInfo("seci_battery", "Rajnandgaon battery project tender SECI000240 (6 Aug 2026)", "Solar Energy Corporation of India",
               "https://www.seci.co.in/tenders/archive",
               "Operator copyright. Uses project identity and status facts with attribution.",
               "The operating project is listed as commissioned by SECI. The mapped point represents the shared "
               "solar and battery site using the pinned GEM power export (CC BY 4.0; solar precaution CC BY-NC 4.0). "
               "Ministry of Power release 2291650 confirms the installation as of 30 Jun 2026. "
               "Map statistics count verified projects.", ["resources"]),
    SourceInfo("cea_pumping", "CEA pumped-storage development status (2026)", "Central Electricity Authority",
               "https://www.cea.nic.in/api/dashboardReports/view-pdf/en/055c36d3-284e-4aeb-9b29-4f310477a0eb",
               "Derived-only use. CEA report tables are reserved to their rights holder.",
               "Status cross-check for GEM. Kadana and Sardar Sarovar river-bed generation remain in the hydro category. "
               "Rated power comes from the checksum-pinned GEM export.", ["resources"]),
    pib("crop_advance", "Third Advance Estimates of major crops", "2265965",
        "The May release establishes crop-year national context. It supplies no state production quantities to this build.",
        "27 May 2026"),
    pib("pilibhit_rice", "Pilibhit Basmati growing area", "2308493",
        "Identifies the Pilibhit Basmati growing area and the APEDA trial farm.", "9 Sep 2026"),
    pib("punjab_wheat", "Wheat production and procurement in Punjab", "2255618",
        "Confirms wheat cultivation in Punjab in the current crop year. Procurement figures are excluded.",
        "26 Apr 2026"),
    SourceInfo("rajasthan_millets", "Rajasthan Economic Review 2025-26", "Government of Rajasthan",
               "https://finance.rajasthan.gov.in/docs/budget/statebudget/2026-2027/Economicreviewe.pdf",
               "Factual district identifications only. Report text, tables and maps are reserved to their rights holders.",
               "Barmer and Jodhpur are named Bajra scheme districts for the current crop year.", ["resources"]),
    pib("up_sugarcane", "India's sugarcane growing states", "2303478",
        "Confirms Uttar Pradesh as a leading growing state in the crop year. The National Atlas thematic sugarcane report identifies the Bijnor district belt.",
        "Aug 2026"),
    pib("vidarbha_cotton", "Cotton procurement districts in Maharashtra", "2245994",
        "Confirms current cotton-farmer activity in Yavatmal, Akola and Amravati. Purchase quantities are excluded.",
        "Mar 2026"),
    pib("rajkot_cotton", "Cotton cultivation in Rajkot", "2286497",
        "Identifies growers in Rajkot district in the Cotton Productivity project.", "Jul 2026"),
    SourceInfo("bengal_jute", "Nadia jute field visit (Jun 2026)", "ICAR–CIFRI",
               "https://www.icar.gov.in/hi/node/25372",
               "Factual cultivation observation only. Article text and photos remain with their rights holders.",
               "Field observers found jute growing in Haringhata block, Nadia district.", ["resources"]),
    SourceInfo("tea_regions", "International Tea Day overview (May 2026)", "Press Information Bureau",
               "https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=158446",
               "PIB copyright policy (reproduction with attribution)",
               "Operating tea regions in Assam, Darjeeling and the Nilgiris.", ["resources"], license_url=PIB_POLICY),
    SourceInfo("coffee_regions", "Coffee Annual IN2026-0026 (2026)", "USDA Foreign Agricultural Service",
               "https://apps.fas.usda.gov/newgainapi/api/Report/DownloadReportByFileName?fileName=Coffee+Annual_New+Delhi_India_IN2026-0026.pdf",
               "US government public-domain report text",
               "Growing regions named in the report, including Kodagu, Chikkamagaluru and Wayanad.", ["resources"]),
    pib("rubber_regions", "Assam rubber sector briefing", "2270804",
        "Identifies Kerala and Tripura as leading rubber producers. Districts corroborated by Kerala Tourism and Rubber Board jurisdictions.", "9 Jun 2026"),
    pib("idukki_spices", "Idukki spice growers", "2291378",
        "Identifies cardamom cultivation in Idukki district.", "29 Jul 2026"),
    pib("thrissur_crops", "Thrissur coconut growing clusters", "2211783",
        "Identifies coconut, pepper and ginger in the Velur and Puliyannur farmer clusters.", "5 Jan 2026"),
    SourceInfo("ratnagiri_mango", "Alphonso harvest report (May 2026)", "Jain Farm Fresh",
               "https://www.jainfarmfresh.com/crop-reports/alphonso-mango-crop-report-may-2026",
               "Factual growing-region identification only. Report text, data tables and images are reserved to their rights holders.",
               "Confirms Alphonso cultivation in Ratnagiri.", ["resources"]),
    pib("kalaburagi_silk", "Kalaburagi cocoon producers", "2217473",
        "Identifies cocoon production in Kalaburagi district.", "22 Jan 2026"),
    pib("veraval_fish", "Veraval fishing harbour cluster", "2230714",
        "Operating harbour confirmed in February. Approximate landing-side point from Gujarat Maritime Board’s Veraval Port facts.",
        "20 Feb 2026"),
    SourceInfo("kochi_fish", "Cochin Fisheries Harbour modernization status (2026)", "Cochin Port Authority",
               "https://cochinport.gov.in/projectsstatus/ZW4~ZIp34I8-",
               "Uses the harbour identity, operating status and approximate coordinates as facts. Source text, maps and imagery are reserved to their rights holders.",
               "Fishing harbour at Thoppumpady. Approximate harbour point corroborated by CSIR-NIO study 113423.",
               ["resources"]),
    SourceInfo("panna_diamond", "Majhgawan mining proposal IA/MP/MIN/562764/2026",
               "Ministry of Environment, Forest and Climate Change",
               "https://environmentclearance.nic.in/writereaddata/Form-1A/Minutes/12032026678931981stEAC%28NCM%29Minutes.pdf",
               "Uses the reported lease bounds and confirmed operating status as facts. Report text and drawings are reserved to their rights holders.",
               "Panna diamond mine. Marker uses the midpoint of the 2026 main lease's reported bounds. "
               "Operation corroborated by NMDC’s FY 2025-26 annual report.", ["resources"]),
    SourceInfo("panchpatmali_bauxite", "Panchpatmali Central and North Block 07ORI09001 (Oct 2026)",
               "Indian Bureau of Mines / NALCO",
               "https://ibm.gov.in/writereaddata/files/177608893569dcf7676a10c_MiningPlanDisposedAndInprogress.pdf?v=08112026",
               "Uses documented lease bounds and confirmed operating status as facts. Source documents and maps are reserved to their rights holders.",
               "Panchpatmali bauxite mine; active per NALCO. Marker represents the Central and North Block lease "
               "bounds documented in the National Green Tribunal Appeal 01-2025 record.", ["resources"]),
    SourceInfo("jamul_limestone", "Jamul Limestone Mine compliance report JL/ENV/MoEFCC/26/74 (Apr 2026)",
               "ACC Limited",
               "https://www.acclimited.com/-/media/Project/ACC-Limited/Sustainability-pdfs/"
               "Environment-Data/2026/EC-Report-Jamul-Limestone-Mine-1.ashx",
               "Uses operating status and lease coordinates from the operator report as facts. Report text and scans are reserved to their rights holders.",
               "Operating limestone mine and lease bounds at Jamul, Durg. "
               "Report SHA-256 7363ff0c1c8cc56a348d9832491502778cd818602f07ca3884b9bab804deb2e0.",
               ["resources"]),
]

# District codes are checked against the map's existing DataMeet crosswalk.
GROWING_REGIONS = [
    ("tea", "Assam Valley · Dibrugarh", "AS", "18-310", "tea_regions", "May 2026"),
    ("tea", "Assam Valley · Jorhat", "AS", "18-312", "tea_regions", "May 2026"),
    ("tea", "Darjeeling hills", "WB", "19-327", "tea_regions", "May 2026"),
    ("tea", "Nilgiris", "TN", "33-611", "tea_regions", "May 2026"),
    ("coffee", "Kodagu", "KA", "29-576", "coffee_regions", "Coffee year 2025-26 (1 Oct 2025 – 30 Sep 2026)"),
    ("coffee", "Chikkamagaluru", "KA", "29-570", "coffee_regions", "Coffee year 2025-26 (1 Oct 2025 – 30 Sep 2026)"),
    ("coffee", "Wayanad", "KL", "32-590", "coffee_regions", "Coffee year 2025-26 (1 Oct 2025 – 30 Sep 2026)"),
    ("cardamom", "Idukki", "KL", "32-596", "idukki_spices", "Jul 2026"),
    ("coconut", "Velur and Puliyannur · Thrissur", "KL", "32-594", "thrissur_crops", "Jan 2026"),
    ("pepper", "Velur and Puliyannur · Thrissur", "KL", "32-594", "thrissur_crops", "Jan 2026"),
    ("ginger", "Velur and Puliyannur · Thrissur", "KL", "32-594", "thrissur_crops", "Jan 2026"),
    ("mango", "Ratnagiri", "MH", "27-528", "ratnagiri_mango", "May 2026"),
    ("rubber", "Kottayam", "KL", "32-597", "rubber_regions", "Jun 2026"),
    ("rubber", "West Tripura growing area", "TR", "16-289", "rubber_regions", "Jun 2026"),
    ("silk", "Kalaburagi", "KA", "29-579", "kalaburagi_silk", "Jan 2026"),
    ("wheat", "Punjab wheat belt · Ludhiana", "PB", "03-041", "punjab_wheat", CROP_PERIOD),
    ("wheat", "Punjab wheat belt · Sangrur", "PB", "03-053", "punjab_wheat", CROP_PERIOD),
    ("rice", "Pilibhit Basmati belt", "UP", "09-151", "pilibhit_rice", "Sep 2026"),
    ("cotton", "Yavatmal", "MH", "27-510", "vidarbha_cotton", "Mar 2026"),
    ("cotton", "Akola", "MH", "27-501", "vidarbha_cotton", "Mar 2026"),
    ("cotton", "Rajkot", "GJ", "24-476", "rajkot_cotton", "Jul 2026"),
    ("jute", "Nadia", "WB", "19-336", "bengal_jute", "Jun 2026"),
    ("millets", "Barmer", "RJ", "08-115", "rajasthan_millets", CROP_PERIOD),
    ("millets", "Jodhpur", "RJ", "08-113", "rajasthan_millets", CROP_PERIOD),
    ("sugarcane", "Bijnor", "UP", "09-134", "up_sugarcane", CROP_PERIOD),
]

# The two named cluster villages share a map-scale neighbourhood. Anchor at Velur.
GROWING_ANCHORS = {"thrissur_crops": [(10.6393, 76.1558)]}

SITES = [
    ("copper", "Malanjkhand copper mine", "MP", 22.0167, 80.7167, "hcl_mines", MINE_PERIOD),
    ("copper", "Khetri copper mine", "RJ", 28.0800, 75.8218, "hcl_mines", MINE_PERIOD),
    ("lead_zinc", "Rampura Agucha mine", "RJ", 25.8375, 74.7375, "hzl_mines", MINE_PERIOD),
    ("lead_zinc", "Sindesar Khurd mine", "RJ", 25.0000, 74.1583, "hzl_mines", MINE_PERIOD),
    ("lead_zinc", "Rajpura Dariba mine", "RJ", 24.9458, 74.1304, "hzl_mines", MINE_PERIOD),
    ("lead_zinc", "Zawar group of mines", "RJ", 24.3468, 73.7125, "hzl_mines", MINE_PERIOD),
    ("lead_zinc", "Kayad mine", "RJ", 26.5276, 74.6918, "hzl_mines", MINE_PERIOD),
    ("battery", "Rajnandgaon battery storage", "CG", 21.0964, 81.0125, "seci_battery", "Aug 2026"),
    ("diamond", "Majhgawan diamond mine · Panna", "MP", 24.6355, 80.0252, "panna_diamond", "Feb 2026"),
    ("bauxite", "Panchpatmali bauxite mine", "OD", 18.8653, 83.0231, "panchpatmali_bauxite", "Oct 2026"),
    ("limestone", "Jamul limestone mine", "CG", 21.2548, 81.3658, "jamul_limestone", "Apr 2026"),
    ("fish", "Veraval fishing harbour", "GJ", 20.910, 70.369, "veraval_fish", "Feb 2026"),
    ("fish", "Cochin Fisheries Harbour", "KL", 9.940, 76.263, "kochi_fish", "2026 snapshot"),
]
