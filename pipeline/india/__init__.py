"""India inputs prepared separately from the managed downloads (see README).

Each step writes data/interim/<id>.json. LOCAL_SOURCES describes them for the Almanac (build/catalog.py).
"""

from ..core.source import SourceInfo
from .city_sources import ANNUAL_LABOUR_INFO, GOVERNMENT_SITE_INFO
from .advisor_sources import SOURCES as ADVISOR_SOURCES
from .military_sources import SOURCES as MILITARY_SOURCES
from .census_civic_sources import SOURCES as CENSUS_CIVIC_SOURCES
from .census_work_sources import PCA_SOURCE, SOURCES as CENSUS_WORK_SOURCES
from .city_economy_sources import SOURCES as GSVA_SOURCES
from .explorer_sources import SOURCES as EXPLORER_SOURCES
from .household_cost_sources import SOURCES as HOUSEHOLD_COST_SOURCES
from .people_sources import SOURCES as PEOPLE_SOURCES
from .historical_sources import (INPUTS as WORKPLACE_INPUTS, INDEX_URL, PORT_SOURCE as PORT_DIRECTION_SOURCE,
                                 PORT_URL as PORT_DIRECTION_URL, PORT_SHA256 as PORT_DIRECTION_SHA256,
                                 WORKPLACE_LICENSE, WORKPLACE_SOURCE, UA_URL, VILLAGE_LAND_INFO)
from .civic_sources import SOURCES as CIVIC_SOURCES
from .yield_sources import SOURCES as YIELD_SOURCES
from .protected_land_catalog import SOURCES as PROTECTED_SOURCES
from .terrain_assets import ARCHIVES, ELEVATION, REEFS
from .transport_analogue_sources import SOURCES as TRANSPORT_ANALOGUE_SOURCES

IFI_SOURCE = "ifi_flood_impacts"
IFI_CHECKSUM = "ef9ab2cd0db7bf917dcc22c7cb094ec599f5013ef1b96ba525d816f26ff1b108"

# Current spellings for names the sources still carry in an older form (cities and districts).
DISPLAY_NAMES = {
    "Ahmadabad": "Ahmedabad",
    "Ahmadnagar": "Ahilyanagar",
    "Allahabad": "Prayagraj",
    "Aurangabad": "Chhatrapati Sambhajinagar",
    "Bangalore": "Bengaluru",
    "Bangalore Rural": "Bengaluru Rural",
    "Barddhaman": "Bardhaman",
    "Belgaum": "Belagavi",
    "Bellary": "Ballari",
    "Bijapur": "Vijayapura",
    "Chennai (Madras)": "Chennai",
    "Dehra Dun": "Dehradun",
    "Durg-Bhilainagar": "Durg-Bhilai",
    "English Bazar": "Malda",
    "Faizabad": "Ayodhya",
    "Gulbarga": "Kalaburagi",
    "Guwahati (Gauhati)": "Guwahati",
    "Gurgaon": "Gurugram",
    "Haldwani-cum-kathgodam": "Haldwani-Kathgodam",
    "Hardwar": "Haridwar",
    "Hoshangabad": "Narmadapuram",
    "Hubli-Dharwad": "Hubballi-Dharwad",
    "Jyotiba Phule Nagar": "Amroha",
    "Karimganj": "Sribhumi",
    "Kochi (Cochin)": "Kochi",
    "Kolkata (Calcutta)": "Kolkata",
    "Kozhikode (Calicut)": "Kozhikode",
    "Mahamaya Nagar": "Hathras",
    "Mangalore": "Mangaluru",
    "Maunath Bhanjan": "Mau",
    "Mewat": "Nuh",
    "Morvi": "Morbi",
    "Muktsar": "Sri Muktsar Sahib",
    "Mumbai (Bombay)": "Mumbai",
    "Mysore": "Mysuru",
    "Osmanabad": "Dharashiv",
    "Pune (Poona)": "Pune",
    "Rajahmundry": "Rajamahendravaram",
    "Ramanagara": "Bengaluru South",
    "Raurkela": "Rourkela",
    "Sant Ravi Das Nagar(bhadohi)": "Bhadohi",
    "Shimoga": "Shivamogga",
    "Thoothukkudi (Tuticorin)": "Thoothukudi",
    "Tumkur": "Tumakuru",
    "Varanasi (Benares)": "Varanasi",
}

WUP_SOURCE = "un_wup_cities"
WUP_CHECKSUM = "4366cc15ecdda4d9ab420adfe730da6a7e35a8334615f50172a08d60b121c11c"
LAKES_SHA256 = "9ef63498569dd7ccd0b8d8852da026e009a75f42d293f00e483f3b9fcfe8e1f9"
KRISHNA_SHA256 = "bb854a900ecbd3b408df46d5e16e3e0f974ba55993f9d8b5c26e855273c0905a"
PULICAT_SHA256 = "d846b2fc14c338c3946cb77acbf1c1787666a9e699f53e98175bf8ef7d8ff62f"

ESTUARY_SOURCES = [
    SourceInfo(
        id="meghna_stations",
        title="Bangladesh Water Development Board tide station locations",
        publisher="Bangladesh Water Development Board and Permanent Service for Mean Sea Level",
        homepage="https://www.hydrology.bwdb.gov.bd/includes/water_level_data_available_print.php",
        license="Station positions cited as geographic facts.",
        description="Lower Meghna route anchors at Nilkamal (SW277.3) and Daulatkhan (SW278) from the "
        "September 2026 station inventory, plus PSMSL station 1496 (Charchanga). No tide readings are used.",
        used_for=["Lower Meghna estuary course"],
    ),
    SourceInfo(
        id="damodar_junction",
        title="Geographic Concerns on Flood Climate and Flood Hydrology in Monsoon-Dominated Damodar River Basin",
        publisher="Sandipan Ghosh and Biswaranjan Mistri",
        homepage="https://doi.org/10.1155/2015/486740",
        license="CC BY (open-access article)",
        description="The article identifies the Lower Damodar junction with the Hooghly at Falta. "
        "Confirms the receiving course for the mapped OSM Damodar reaches.",
        used_for=["Lower Damodar confluence"],
    ),
]
TERRAIN_SITES_SHA256 = "b704f72dc3a47a2d355fdaadfc596c4ec4bcef78193f0f7bb19877553ea45cee"
GHSL_UCDB = "city_footprints"
GHSL_CHECKSUM = "1caac92f2cadb641fa933001fbc8e412864d71c5e7318e5004de5532e6c16851"
CITY_POPULATION_GRID = "city_population_grid"
CITY_POPULATION_CHECKSUM = "717fb3f533e1f079f9f5d9dc288936c9694e9f27a14c733ec13053fe1dff338e"

AIR_WEATHER_PINS = {
    "aqi": "80874781fde98b22b722a3c8db9bdbf47e5d9447360f959a07b11d034bc11856",
    "pm25": "a27404f1c17ff6f7242db8de8a75fe5d3fbcc87d313d34d53aec59fca6fd22cf",
    "stations": "25c5b858a24f76022242deafd18134a8d71e3cc5596e5b59f488f934b450ca63",
    "rainfall": "245be1b10d885ab2ce41e602b503b0caf7e25a47c53b5e3d5fb9f5f9dd304628",
    "geometry": "64d5a06eb9d7eec9b085f19362443b3374d89cb704365267533c452083701829",
}
AIR_PORTAL = "https://airquality.aqmsat.com/downloads"
AIR_TERMS = "Free to use with source credit under India Air Quality Portal's download terms."

LOCAL_SOURCES = [
    GOVERNMENT_SITE_INFO,
    ANNUAL_LABOUR_INFO,
    SourceInfo(
        id=WORKPLACE_SOURCE, title="Sixth Economic Census via SHRUG v2.2 Pakora",
        publisher="MoSPI and Development Data Lab", homepage=INDEX_URL,
        license=WORKPLACE_LICENSE,
        description="January 2013 – April 2014. Compare local and India employment shares over non-farm "
                    "workplace jobs after excluding defence-mixed groups. "
                    "The 50-job minimum accommodates small Indian districts. "
                    "Requiring a 0.5% local share and a 1.25 location quotient as well keeps a small cluster "
                    "or a common industry from qualifying on job count alone. "
                    "The derived workplace.json is available under CC BY-NC-SA 4.0 (ShareAlike). "
                    + " ".join(f"{name} SHA-256 {WORKPLACE_INPUTS[name]}." for name in ("ec13.zip", "keys.zip", "shric.zip")),
        used_for=["Historical non-farm workplace jobs and civilian specialisation"], download_path="data/workplace.json",
    ),
    SourceInfo(
        id="census_2011_ua_keys", title="Primary Census Abstract, Urban Agglomerations 2011",
        publisher="Office of the Registrar General & Census Commissioner, India", homepage=UA_URL,
        license="Census of India publication. Used as a geography crosswalk.",
        description="Census 2011, PCA11-UA-0000. Towns and outgrowths are matched by location code. "
                    f"Workbook SHA-256 {WORKPLACE_INPUTS['ua.xlsx']}.",
        used_for=["Economic Census urban agglomeration matching"],
    ),
    SourceInfo(
        id=PORT_DIRECTION_SOURCE, title="Basic Port Statistics of India 2024–25",
        publisher="Ministry of Ports, Shipping and Waterways", homepage=PORT_DIRECTION_URL,
        license="Ministry copyright policy permits credited, accurate reuse of the published port tonnage figures.",
        description="Divide loaded and unloaded tonnes by total overseas tonnes at the same port or reporting state "
                    "using tables 2.1.3, 2.2.1, 3.1.3 and 3.1.4. For matched non-major ports, "
                    "divide coastal tonnes by the sum of coastal and overseas tonnes in Table 2.2.1. "
                    f"FY 2024-25 (1 Apr 2024 – 31 Mar 2025). PDF SHA-256 {PORT_DIRECTION_SHA256}.",
        used_for=["Port map tonnage tooltips, Explorer non-major port cargo shares and Commerce overseas cargo direction"],
    ),
    SourceInfo(
        id="esri_land_cover",
        title="Sentinel-2 10 m Land Use/Land Cover, v003",
        publisher="Esri, Impact Observatory and Microsoft",
        homepage="https://livingatlas.arcgis.com/landcoverexplorer/",
        license="CC BY 4.0",
        description="1 Jan – 31 Dec 2025. Tally native classified pixels on a 5 km equal-area lattice by mapped "
                    "state and Census 2011 district, excluding water, clouds and nodata.",
        used_for=["Historical tree cover, cropland, built-up land and land-cover composition"],
    ),
    SourceInfo(
        id="worldcover_history",
        title="ESA WorldCover 10 m v200",
        publisher="ESA WorldCover consortium",
        homepage="https://doi.org/10.5281/zenodo.7254221",
        license="CC BY 4.0. © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) "
                "processed by ESA WorldCover consortium.",
        description="1 Jan – 31 Dec 2021. Tally native classified pixels on a 5 km equal-area lattice, excluding "
                    "permanent water and combining herbaceous wetlands and mangroves.",
        used_for=["Historical grassland, shrubland and mapped wetlands"],
    ),
    SourceInfo(
        id=IFI_SOURCE,
        title="India Flood Inventory with Impacts v3",
        publisher="HydroSense Lab, IIT Delhi (IMD event records)",
        homepage="https://doi.org/10.5281/zenodo.11275211",
        license="CC BY 4.0",
        description="1967–2023. Sum reported deaths and injuries for unambiguous single-district events; "
                    "retain only unambiguous counts and show a lower bound when one component is missing. "
                    f"CSV SHA-256 {IFI_CHECKSUM}.",
        used_for=["City View historical flood impacts"],
    ),
    *GSVA_SOURCES,
    *PEOPLE_SOURCES,
    *YIELD_SOURCES,
    *PROTECTED_SOURCES,
    SourceInfo(
        id="soi_boundary_chart",
        title="Survey of India Political Map of India, English 13th edition (2026)",
        publisher="Survey of India, Government of India",
        homepage="https://surveyofindia.gov.in/UserFiles/files/POL_MAP_4M_ENGLISH_13thEdn2026%281%29.pdf",
        license="Government of India copyright. The extracted chart vectors are for local reference.",
        description="Area of charted Indian land, neighbouring land and water in each hex. "
        "PDF SHA-256 62f46ae5c7444048ee58920f14f80ba1aa60a3db344be7502d11f146abefe8ca.",
        used_for=["Land, water and national ownership decisions"],
    ),
    SourceInfo(
        id="open_rivers",
        title="OpenStreetMap regional river snapshots",
        publisher="© OpenStreetMap contributors",
        homepage="https://www.openstreetmap.org/copyright",
        license="Open Database Licence (ODbL) 1.0",
        description="Named river ways and waterway relations from November 2026 Overpass snapshots. "
        "The reproducibility manifest records each exact query, base timestamp and SHA-256.",
        used_for=["Named river courses and junction locations"],
    ),
    SourceInfo(
        id="hydrolakes",
        title="HydroLAKES v1",
        publisher="HydroSHEDS / Messager et al.",
        homepage="https://www.hydrosheds.org/products/hydrolakes",
        license="CC BY 4.0",
        description="Lake and reservoir outlines selected and simplified for the map. Messager et al. (2016), "
        f"doi:10.1038/ncomms13603. Global archive SHA-256 {LAKES_SHA256}.",
        used_for=["Inland standing water"],
    ),
    SourceInfo(
        id="krishna_delta",
        title="Natural Earth 1:10m rivers v5.1.2",
        publisher="Natural Earth",
        homepage="https://www.naturalearthdata.com/",
        license="Public domain",
        description=f"Shared baseline linework and eastern Krishna delta channel. GeoJSON SHA-256 {KRISHNA_SHA256}.",
        used_for=["River courses and the Krishna delta distributary"],
    ),
    SourceInfo(
        id="pulicat",
        title="OpenStreetMap Pulicat Lake (relation 1624070, revision 58)",
        publisher="© OpenStreetMap contributors",
        homepage="https://www.openstreetmap.org/copyright",
        license="Open Database Licence (ODbL) 1.0",
        description="Lagoon extent with islands removed from the footprint. "
        f"Full relation snapshot SHA-256 {PULICAT_SHA256}.",
        used_for=["Pulicat Lake footprint"],
    ),
    SourceInfo(
        id=GHSL_UCDB,
        title="GHS Urban Centre Database R2024A v1.2",
        publisher="European Commission Joint Research Centre · GHSL",
        homepage="https://doi.org/10.2905/1A338BE6-7EAF-480C-9664-3A8ADE88CBCD",
        license="CC BY 4.0 · © European Union",
        description="The reference-epoch urban-centre shapes are matched by UN point, name and state, "
        "then clipped to the Survey of India outline and intersected with the grid and DataMeet districts. "
        "The 2025 reference epoch serves as a spatial proxy for the 2026 urban areas. "
        f"Central and Southern Asia archive SHA-256 {GHSL_CHECKSUM}.",
        used_for=["City View urban footprint proxy and district overlap", "Military layer civil town centroids"],
    ),
    SourceInfo(
        id=CITY_POPULATION_GRID,
        title="WorldPop 2026 constrained population grid, R2025A v1",
        publisher="WorldPop · University of Southampton",
        homepage="https://hub.worldpop.org/geodata/listing?id=136",
        license="CC BY 4.0",
        description="IndiaCiv estimates use the 2026 WorldPop 30 arc-second population at pixel centres inside "
        "each footprint fragment to weight the allocation of the UN mid-2026 projection. Largest remainders "
        "preserve the UN total. District shares divide WorldPop mass inside the footprint by the district's mass. "
        "Missing hex densities divide area-weighted mid-2026 WorldPop mass by Indian land area where at least "
        "80% of that area has valid raster coverage. "
        f"India GeoTIFF SHA-256 {CITY_POPULATION_CHECKSUM}.",
        used_for=["Mid-2026 city residents per hex", "2026 district population and share inside each urban area",
                  "Mid-2026 density in hexes without district estimates"],
    ),
    SourceInfo(
        id="cpcb_city_aqi",
        title="CPCB National AQI daily bulletin",
        publisher="Central Pollution Control Board · EnviroCatalysts, India Air Quality Portal",
        homepage=AIR_PORTAL,
        license=AIR_TERMS,
        description="Reported daily city AQI from January through October 2026, transcribed by EnviroCatalysts. "
        "Madurai shows 1 Jan 2026 – 31 Jan 2026 where 25 of 31 days qualify. The shorter period has no Jan–Oct rank. "
        f"Input snapshot SHA-256 {AIR_WEATHER_PINS['aqi']}.",
        used_for=["City share of reported days with AQI rated Poor or worse"],
    ),
    SourceInfo(
        id="cpcb_station_pm25",
        title="CPCB CAAQMS station PM₂.₅ observations",
        publisher="Central Pollution Control Board · EnviroCatalysts, India Air Quality Portal · XKDR Forum",
        homepage=AIR_PORTAL,
        license=AIR_TERMS + " Station coordinates from XKDR Forum's India Air Quality Database (CC BY 4.0).",
        description="Local hourly PM₂.₅ readings from January through October 2026, averaged into station means, "
        "then interpolated to district centroids. Coordinates use the 23 November 2026 CPCB portal snapshot. "
        f"Hourly archive SHA-256 {AIR_WEATHER_PINS['pm25']}. "
        f"Coordinate CSV SHA-256 {AIR_WEATHER_PINS['stations']}. City View takes an area-weighted mean "
        "over the parts of its footprint in districts with estimates and reports that area coverage.",
        used_for=["IndiaCiv estimate of January–October 2026 district PM₂.₅"],
    ),
    SourceInfo(
        id="imd_monsoon",
        title="2026 southwest monsoon seasonal rainfall",
        publisher="India Meteorological Department · India by Numbers (transcription)",
        homepage="https://indiabynumbers.org/charts/monsoon-2026-by-subdivision/",
        license="India by Numbers transcription (CC BY 4.0). Upstream IMD terms apply to the source data.",
        description="IMD Special Daily Weather Report, 30 September 2026, Table 2, transcribed by India by Numbers. "
        "IndiaCiv groups the signed departures from the long-period average into five bands and maps those bands "
        "at hex centres and district reference points. "
        f"Rainfall CSV SHA-256 {AIR_WEATHER_PINS['rainfall']}. "
        f"IMD subdivision geometry SHA-256 {AIR_WEATHER_PINS['geometry']}.",
        used_for=["June–September 2026 rainfall departure by meteorological subdivision"],
    ),
    SourceInfo(
        id="soi_outline",
        title="Outline of India (national boundary)",
        publisher="Survey of India, Government of India",
        homepage="https://surveyofindia.gov.in/documents/OUTLINE_OF_INDIA.zip",
        license="© Survey of India. Generalised hex map prepared under the 2021 geospatial guidelines.",
        description="Supplies the national outline for detached islands and for tiles with incomplete political-map coverage. "
        "The site displays the resulting cell ownership and water class. "
        "Archive SHA-256 9e657f0c20ac4f4168e261b2c7d3fed4ed927a638a2fd411be9f6257463faf45.",
        used_for=["India's land hexes and coastline"],
    ),
    SourceInfo(
        id="india_terrain",
        title="ESA WorldCover 2021 v200",
        publisher="ESA WorldCover consortium",
        homepage="https://esa-worldcover.org/",
        license="CC BY 4.0. © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) "
        "processed by ESA WorldCover consortium.",
        description="Zanaga et al., ESA WorldCover 10 m 2021 v200 (doi:10.5281/zenodo.7254221). "
        "Copernicus GLO-90 is a preparation input. Land-cover class at points 5 km apart inside India (about 34 per fully land hex), read from the 10 m maps. "
        "Each hex's land-cover mix and dominant cover come from these points. A finer window shows the "
        "forest on Narcondam (sample SHA-256 d35d624d179b9a3cd1ddf4df45ff931f9bb0fb88b0b7a813e9e289d074ac80a3).",
        used_for=["Land cover (forest, cropland, scrub, wetland, built-up…)"],
    ),
    SourceInfo(
        id=WUP_SOURCE,
        title="World Urbanization Prospects: The 2018 Revision, File 22",
        publisher="United Nations DESA, Population Division",
        homepage="https://population.un.org/wup/",
        license="CC BY 3.0 IGO",
        description="Indian urban agglomeration coordinates and UN midyear population projections. "
        "IndiaCiv estimates calendar-2026 endpoints by linear interpolation by day between adjacent 1 July projections. "
        "Million-plus status uses the 1 million boundary in UN DESA's urban settlement size classes (Table III.1). "
        f"Workbook SHA-256 {WUP_CHECKSUM}.",
        used_for=["City positions", "City population (2026 projection)", "Projected city growth",
                  "Calendar-2026 city population change", "Agglomeration size class"],
    ),
    SourceInfo(
        id="tg_projections",
        title="Population projections for India and states (Technical Group, National Commission on Population)",
        publisher="Ministry of Health and Family Welfare, Government of India",
        homepage="https://nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf",
        license="NHM copyright policy (prominent attribution)",
        description="Projected population on 1 March 2026 for India and every state and union territory (Table 21), "
        "2026 characteristics such as sex ratio, age shares and median age (T-17) and annual growth from 1 March 2025 to "
        "1 March 2026 (Table 8). Table 17A supplies the five-year health averages used for interpolation. Report SHA-256 "
        "9a9031c9c75d609e03ab94ce0ac6115cb9d8a9ab82d1b18a47b78e90ae01331b. "
        "For city shares of India’s population, IndiaCiv interpolates the March national projections "
        "to 1 July 2026 to match the UN city estimates.",
        used_for=["National and state population (2026 projection)", "District, state and health lenses"],
    ),
    SourceInfo(
        id="census_a01",
        title="Census of India, table A-01 (district totals)",
        publisher="Office of the Registrar General & Census Commissioner, India",
        homepage="https://censusindia.gov.in/nada/index.php/catalog/42526",
        license="ORGI copyright policy (permission required for reproduction of the source table)",
        description="District population counts are joined to DataMeet by district code (all 640 match) "
        "and scaled by projected state population growth to estimate 2026 district populations. "
        "Density uses areas calculated from DataMeet polygons. "
        "Workbook SHA-256 6b649697ed5993da834b674173dab68e1ef9abb97e234155a80884c2fa4584f5.",
        used_for=["District share of each state's 2026 population"],
    ),
]


TERRAIN_SOURCES = [
    SourceInfo("koppen_geiger", "Köppen–Geiger v3", "Beck et al. / GloH2O",
               "https://doi.org/10.6084/m9.figshare.21789074.v2", "CC BY 4.0",
               f"Climate normals (1991–2020) for the atlas's terrain categories. Archive SHA-256 {ARCHIVES['climate.zip'][1]}.",
               ["Climate base", "Wet tropical forest proxy"]),
    SourceInfo("etopo_2022", "ETOPO 2022 15 arc-second surface", "NOAA NCEI",
               "https://doi.org/10.25921/fd45-gt74", "CC0 1.0",
               "Mixed-epoch global relief, sampled at 500 m for Indian land. Nine tile SHA-256 values, by tile: "
               + ", ".join(f"{tile} {digest}" for tile, digest in ELEVATION.items()) + ".",
               ["Surface elevation", "Terrain relief"]),
    SourceInfo("glwd_v2", "Global Lakes and Wetlands Database v2.0", "Lehner et al. / HydroSHEDS",
               "https://doi.org/10.6084/m9.figshare.28519994.v1", "CC BY 4.0",
               "Mixed-epoch combined main classes from the 2025 release. "
               f"Archive SHA-256 {ARCHIVES['wetlands.zip'][1]}.", ["Marshes", "Salt pans"]),
    SourceInfo("gfplain", "GFPLAIN250m v1", "Nardi et al.",
               "https://doi.org/10.6084/m9.figshare.6665165.v1", "CC BY 4.0",
               f"Geomorphic floodplains derived from SRTM, released in 2018. Archive SHA-256 {ARCHIVES['flood.rar'][1]}.",
               ["Floodplain extent"]),
    SourceInfo("global_mangrove_watch", "Global Mangrove Watch v3.0", "Bunting et al. / Global Mangrove Watch",
               "https://doi.org/10.5281/zenodo.6894273", "CC BY 4.0",
               f"2020 mangrove extent from the v3.0 tiled GeoTIFF release. Archive SHA-256 {ARCHIVES['mangroves.zip'][1]}.",
               ["Mangrove extent"]),
    SourceInfo("allen_coral_atlas", "Allen Coral Atlas v2.0 geomorphic habitat map", "Allen Coral Atlas Partnership",
               "https://allencoralatlas.org/resources/", "CC BY 4.0; Allen Coral Atlas Partnership",
               "Mapped reef extent from the public map service, based on imagery composites from 2018–2020. "
               "Regional response SHA-256 values: "
               + ", ".join(f"{region} {spec[3]}" for region, spec in REEFS.items()) + ".",
               ["Reef extent"]),
    SourceInfo("gvp_vents", "Global Volcanism Program: Volcanoes of the World", "Smithsonian Institution",
               "https://volcano.si.edu/gvp_termsofuse.cfm", "Smithsonian terms permit credited non-commercial use",
               "Holocene inventory points for Barren Island (260010) and Narcondam (260001), transcribed in November 2026. "
               f"Site file SHA-256 {TERRAIN_SITES_SHA256}.", ["Volcano vents"]),
    SourceInfo("varkala_geoheritage", "Natural Heritage of Varkala", "Government of India / UNESCO World Heritage Centre",
               "https://whc.unesco.org/en/tentativelists/6895/", "Publisher terms; factual location and feature type only",
               "Tentative-list nomination and atlas digitization of representative cliff and beach segments. "
               f"Site file SHA-256 {TERRAIN_SITES_SHA256}.", ["Varkala cliff and beach"]),
    SourceInfo("chennai_marina", "Marina Beach", "Chennai District, Government of Tamil Nadu",
               "https://chennai.nic.in/tourist-place/marina/", "Publisher terms; factual location and feature type only",
               "Chennai District's beach listing and atlas digitization of a representative sandy shoreline segment. "
               f"Site file SHA-256 {TERRAIN_SITES_SHA256}.", ["Marina Beach"]),
    SourceInfo("chilika_saltmarsh", "Chilika Lake Health Report (2023–24)", "Chilika Development Authority",
               "https://www.chilika.com/documents/CDA%20Health%20Report%282023-24%29.pdf",
               "Publisher terms; factual location and feature type only",
               "Confirms saltmarsh vegetation on Nalabana Island. "
               "Report SHA-256 fedb548c7e4d29307c7a7e5641e1037d5504c597aea1e767a10cc81457c59bf6. "
               f"Site file SHA-256 {TERRAIN_SITES_SHA256}.", ["Nalabana salt marsh"]),
]
LOCAL_SOURCES.extend(TERRAIN_SOURCES)
LOCAL_SOURCES.extend(ADVISOR_SOURCES)
LOCAL_SOURCES.extend(MILITARY_SOURCES)
LOCAL_SOURCES.extend(EXPLORER_SOURCES)
LOCAL_SOURCES.extend(CIVIC_SOURCES)
LOCAL_SOURCES.extend(CENSUS_CIVIC_SOURCES)
LOCAL_SOURCES.extend(CENSUS_WORK_SOURCES)
LOCAL_SOURCES.append(PCA_SOURCE)
LOCAL_SOURCES.extend(HOUSEHOLD_COST_SOURCES)
LOCAL_SOURCES.append(VILLAGE_LAND_INFO)

LOCAL_SOURCES.extend(TRANSPORT_ANALOGUE_SOURCES)


SOI_POLITICAL_MAP = SourceInfo(
    id="soi_political_map",
    title="Political Map of India, English 13th edition",
    publisher="Survey of India, Government of India",
    homepage="https://surveyofindia.gov.in/UserFiles/files/POL_MAP_4M_ENGLISH_13thEdn2026%281%29.pdf",
    license="© Government of India, 2026. Used as a reference for ownership checks.",
    description="English 13th edition at 1:4,000,000. "
    "PDF SHA-256 62f46ae5c7444048ee58920f14f80ba1aa60a3db344be7502d11f146abefe8ca.",
    used_for=["2026 map ownership conformity checks"],
)

PORT_CARGO_URL = "https://shipmin.gov.in/sites/default/files/Cargo%20handled%20at%20Major%20Ports%20March%202026.pdf"
PORT_PLANNING_URL = "https://cwprs.gov.in/storage/pdf-uploads/Technical%20_Memorandum_Port_planning_CWPRS.pdf"
OSM_TRANSPORT_LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"

COASTAL_CARGO_URL = ("https://shipmin.gov.in/sites/default/files/"
                     "Cargo%20handled%20at%20Major%20Ports%20October%2C%202026.pdf")
DFC_COMPLETION_URL = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2307800&lang=1&reg=48"

TRANSPORT_SOURCES = [
    SourceInfo(
        id="adani_port_addresses_fy25", title="Adani Ports and SEZ FY 2024-25 annual report",
        publisher="Adani Ports and Special Economic Zone Limited",
        homepage="https://www.adaniports.com/-/media/Project/Ports/Investor/Investor-Downloads/Annual-Report/FY25.pdf",
        license="Publisher copyright retained. Uses facility addresses as factual reference.",
        description="FY 2024-25 annual report, subsidiary locations for the operating Krishnapatnam and Gangavaram ports.",
        used_for=["Krishnapatnam and Gangavaram localities"],
    ),
    SourceInfo(
        id="aai_vejh_20260806", title="AAI eAIP VEJH (6 August 2026)",
        publisher="Airports Authority of India",
        homepage="https://aim-india.aai.aero.in/eAIP_Archive/06-08-2026/eAIP/IN-AD%202.1VEJH-en-GB.html",
        license="AAI publication used as a reference for a factual civil airport locality.",
        description="Archived 6 August 2026 edition, VEJH airport name and locality.",
        used_for=["Jharsuguda civil airport locality"],
    ),
    SourceInfo(
        id="mopsw_coastal_cargo", title="Cargo handled at Major Ports, October 2026",
        publisher="Ministry of Ports, Shipping and Waterways", homepage=COASTAL_CARGO_URL,
        license="Ministry copyright policy permits accurate reproduction with prominent credit, excluding third-party material.",
        description="Table 1, coastal cargo, column 9, in metric tonnes. Advance estimates for "
                    "Apr–Oct 2026 (1 Apr 2026 – 31 Oct 2026).",
        used_for=["Coastal trade branch widths and cargo tooltips"],
    ),
    SourceInfo(
        id="pib_dfc_completion", title="Dedicated Freight Corridor completion, 8 September 2026",
        publisher="Prime Minister’s Office via Press Information Bureau", homepage=DFC_COMPLETION_URL,
        license="PIB copyright policy permits accurate reproduction with prominent credit, excluding third-party material.",
        description="PIB release 2307800, published 8 September 2026, confirms completion of both corridors.",
        used_for=["Dedicated Freight Corridor operating status"],
    ),
    SourceInfo(
        id="osm_transport", title="OpenStreetMap transport snapshot, 26 November 2026",
        publisher="© OpenStreetMap contributors",
        homepage="https://www.openstreetmap.org/copyright",
        license="Open Database Licence (ODbL) 1.0. Attribution and licence at openstreetmap.org/copyright.",
        license_url=OSM_TRANSPORT_LICENSE_URL,
        download_path="data/infrastructure.json",
        download_label="Download OSM-derived data (ODbL)",
        description="Operating rail and road geometry, tagged way names and networks, and named port facilities. "
                    "Regional Overpass queries, source timestamps and response SHA-256 pins are listed below.",
        used_for=["Railways", "Expressways and national highways", "Mapped port locations"],
    ),
    SourceInfo(
        id="ourairports", title="OurAirports airport database, 26 November 2026",
        publisher="OurAirports", homepage="https://ourairports.com/data/",
        license="Public domain",
        description="Indian airport locations, municipalities and size classes. Data commit a537e082ac8c8fe6ab509df1f128cc6704fe73c1.",
        used_for=["Airport locations, municipalities and size classes"],
    ),
    SourceInfo(
        id="aai_civil_airport_reference", title="AAI operational airport inventory",
        publisher="Airports Authority of India",
        homepage="https://www.aai.aero/sites/default/files/rtidir/RTI%20Reply%20-%20Offline%20-%20Sanjay%20Jayakumar%20Patravali.pdf",
        license="AAI reference marked for academic use. Used to verify civilian classification.",
        description="16 Jan 2026 edition. IndiaCiv verifies a subset of standalone civilian airports against this inventory.",
        used_for=["Civil airport publication gate"],
    ),
    SourceInfo(
        id="mopsw_port_cargo", title="Cargo handled at Major Ports, March 2026",
        publisher="Ministry of Ports, Shipping and Waterways",
        homepage=PORT_CARGO_URL,
        license="Ministry copyright policy permits accurate reproduction with prominent credit, excluding third-party material.",
        description="Table 1 advance estimates in metric tonnes for FY 2025-26 (1 Apr 2025 – 31 Mar 2026). "
                    "Across all 12 major-port authorities, 23.33% of cargo was coastal and 76.67% was overseas. "
                    "PDF SHA-256 c069102893a29ed6913e8c89461d8c21a8f22e134807969791122f4f31a17b6f.",
        used_for=["Major port cargo ranks, shares and marker sizes"],
    ),
    SourceInfo(
        id="pib_rail_freight", title="Railway-wise freight loading, 1 April 2026 release",
        publisher="Ministry of Railways via Press Information Bureau",
        homepage="https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=287291",
        license="PIB copyright policy permits accurate reproduction with prominent credit, excluding third-party material.",
        description="Originating freight loading in million metric tonnes by railway for "
                    "FY 2025-26 (1 Apr 2025 – 31 Mar 2026). Table image SHA-256 "
                    "f9fdf5add5743860fc2c3cac322f616c8d28dd564424f03db319d0e0dedbc83d.",
        used_for=["Railways Almanac table"],
    ),
    SourceInfo(
        id="cwprs_port_locations", title="Technical Memorandum on Port Planning",
        publisher="Central Water and Power Research Station",
        homepage=PORT_PLANNING_URL,
        license="Government of India publication. Used as a reference for facility locations.",
        description="Major port facility positions, checked against map locations. PDF SHA-256 "
                    "f1d08452944b24cc946855f31dd17574fb32f82bb73aed9314b71acb68005545.",
        used_for=["Major port map placement"],
    ),
]

TRANSPORT_SOURCES.append(SourceInfo(
    id="featured_port_locations", title="Selected non-major port facility coordinates",
    publisher="Adani Ports, Gujarat Maritime Board, Odisha Commerce and Transport Department and Puducherry DSTE",
    homepage="https://www.adaniports.com/ports-and-terminals",
    license="Publisher materials used as references for geographic facts.",
    description="Published positions for Mundra, Hazira, Dahej, Dhamra and Karaikal.",
    used_for=["Non-major port locations"],
))

FEATURED_PORT_REFERENCES = [
    ("Mundra compliance report", "https://www.adaniports.com/-/media/Project/Ports/PortsAndTerminals/Mundra-Documents/Environment-Compliance-Report/Previous-Environment-Compliance-Report/5-EC-Compliance-ReportApr22-to-Sep22WFDP-APSEZ-Mundra.pdf", "8b85b4a4b97bebcbb48e9ff5c85876b8f84f709ad57315bbbf04d3c2f94cc1a6", 24953304),
    ("Hazira facility profile", "https://gmbports.org/adani-hazira-port-pvt-ltd?lang=Gujarati", "c603f036a27e507504ff269fddd21baae3c193f42c63283a456aab2b85d29418", 25927),
    ("Dahej solid-cargo terminal profile", "https://gmbports.org/solid-cargo-port-terminal-dahej", "e30fdf5b64f4c6b78c185dc8962113b1e8a76f54cef734edd806853bfd19b459", 25925),
    ("Odisha Annual Activities Report", "https://ct.odisha.gov.in/sites/default/files/2026-02/Annual%20Activities%20Report%282024-25%29%20.pdf", "479d88dc22326f744e0f8df4e675886d874417433b45c21468f24de44004df27", 7439004),
    ("Karaikal port EIA", "https://dste.py.gov.in/sites/default/files/karaikalportdrafteia.pdf", "bfffa0885214e38d9ce6f8d03a123aa90b09e868f6c83f0fdd0b286a7c94a4db", 20035343),
]

TRANSPORT_REFERENCE_FILES = {
    "aai_civil_airport_reference": (
        "AAI operational airport inventory.pdf",
        "https://www.aai.aero/sites/default/files/rtidir/RTI%20Reply%20-%20Offline%20-%20Sanjay%20Jayakumar%20Patravali.pdf",
        "b0af09457f8acd0638cf76859dc3f03be7425bae37bec3d7215e6f4e5c237172", 2_413_367,
    ),
    "ourairports": (
        "airports.csv",
        "https://raw.githubusercontent.com/davidmegginson/ourairports-data/"
        "a537e082ac8c8fe6ab509df1f128cc6704fe73c1/airports.csv",
        "87a8ff07a823702153d4e5d4caa72148633812fb8c9a9cd81fca610ff3c112bf", 12_764_821,
    ),
    "mopsw_coastal_cargo": (
        "Cargo handled at Major Ports October 2026.pdf", COASTAL_CARGO_URL,
        "683209ad2ee3600d2152a82fac2fd7cd09134464c71accf220a7c7d5b15fb590", 2_447_042,
    ),
    "mopsw_port_cargo": (
        "Cargo handled at Major Ports March 2026.pdf", PORT_CARGO_URL,
        "c069102893a29ed6913e8c89461d8c21a8f22e134807969791122f4f31a17b6f", 1_053_038,
    ),
    "pib_rail_freight": (
        "image004U4Q0.jpg", "https://static.pib.gov.in/WriteReadData/userfiles/image/image004U4Q0.jpg",
        "f9fdf5add5743860fc2c3cac322f616c8d28dd564424f03db319d0e0dedbc83d", 66_635,
    ),
    "cwprs_port_locations": (
        "Technical Memorandum Port planning CWPRS.pdf", PORT_PLANNING_URL,
        "f1d08452944b24cc946855f31dd17574fb32f82bb73aed9314b71acb68005545", 8_774_559,
    ),
}
