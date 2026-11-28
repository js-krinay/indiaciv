# IndiaCiv

India drawn like a turn-based strategy map: painted hex terrain, rivers, city tiles and banners, search, a minimap,
share links and an Almanac that cites every source. It is a fork of
[usaciv](https://karpathy.ai/usaciv) by Andrej Karpathy (MIT, see [LICENSE](LICENSE)): the engine, art and interface
are usaciv's; the data pipeline is rebuilt for India.

**So far.** Terrain, cities, the 36 states and union territories, district, state, health and city lenses, and
tile resources (press **R**) and wonders (in Map layers). The Map menu includes railways, highways, ports and
airports. Population figures are projected for 2026. City View opens for every mapped UN urban agglomeration.
Verified urban footprints add district membership and mapped area. Six yields appear in the top bar and map panels.
Choose Disasters in the lens picker for documented incident counts by district or state/UT and hazard type.
The Culture advisor and Explorer list the dated source records.
The inventory uses selected official event reports and NCS monthly tables for January–October 2026
at magnitude 5.0 or higher, with selected November notices checked through the 27 November cutoff.
Open Advisors to see seven India
dashboards and compare all mapped urban agglomerations, states and union territories, and districts in the
Explorer. Columns include the period and source, and ≈ marks an IndiaCiv estimate. State and
district borders are DataMeet's unofficial community maps, by the owner's decision
([boundary source decision](docs/boundary-sources.md)).

## Build and run

After building and checking the data, stage the public static site with
`uv run python -m pipeline release out/indiaciv`. Choose a new output directory
for each build. The command copies the map, its runtime assets, and the licence
notice. It reports raw bytes and the total after gzipping each file separately.
The release follows local scripts and stylesheets from `web/index.html`.
Use quoted literal paths in dynamic imports so those modules can be staged.
The same folder can be served locally using
`python3 -m http.server 8800 --bind 127.0.0.1 --directory out/indiaciv`.

The core pipeline is standard library only (`uv run python -m pipeline …`). Prepare the India inputs first with
`pipeline/india/*`. Each step writes `data/interim/<id>.json`. Download the
[UN DESA File 22 workbook](https://zenodo.org/records/10475196/files/WUP2018-F22-Cities_Over_300K_Annual.xls?download=1)
to `.cache/wup2018.xls` (CC BY 3.0 IGO).

```sh
# Survey of India national outline (save the archive linked in docs/boundary-sources.md as .cache/soi-outline.zip)
uv run --no-project --with pyproj --with pyshp --with 'shapely>=2.1' python -m pipeline.india.outline .cache/soi-outline.zip
# Survey of India political-map shares from the local IC-34 registered vector reference
uv run --no-project --with 'shapely>=2.1' python -m pipeline.india.boundary_chart .cache/ic34-audit --world .cache/ic34-audit/baseline.json
# ESA WorldCover land-cover samples inside the outline (reads public cloud-optimised GeoTIFFs; about 1.5 minutes)
uv run --no-project --with rasterio --with pyproj --with 'shapely>=2.1' python -m pipeline.india.terrain
# Native-pixel historical land cover (only fetch blocks containing lattice points)
uv run --no-project --with rasterio --with pyproj --with tifffile --with 'shapely>=2.1' python -m pipeline.india.terrain --esri
uv run --no-project --with rasterio --with pyproj --with tifffile --with 'shapely>=2.1' python -m pipeline.india.terrain --worldcover-history
# Climate, detailed relief, and terrain features (about 1.8 GB cached; requires bsdtar for GFPLAIN)
uv run --no-project --with rasterio --with pyproj --with 'shapely>=2.1' python -m pipeline.india.layered_terrain
# UN World Urbanization Prospects File 22
uv run --no-project --with pyproj --with xlrd python -m pipeline.india.cities .cache/wup2018.xls
# Census of India 2011 table A-01 (the publisher's workbook as .cache/census-a01.xlsx)
python3 -m pipeline.india.census .cache/census-a01.xlsx
# IC-8 research snapshot (save IC-8-wonders.json from the project issue materials in .cache)
python3 -m pipeline.india.wonders .cache/IC-8-wonders.json
# ASI visit ranks (save the pinned India Tourism Statistics 2026 PDF as .cache/ic75/asi.pdf)
uv run python -m pipeline.india.wonder_visitation .cache/ic75/asi.pdf
# Named OSM river ways and relations, with Natural Earth backup linework
uv run --no-project --with 'shapely>=2.1' python -m pipeline.india.open_rivers .cache/ne-10m-rivers.geojson .cache
# HydroLAKES polygons, Natural Earth Krishna distributary and OSM Pulicat Lagoon
uv run --no-project --with pyshp --with 'shapely>=2.1' python -m pipeline.india.hydrography \
  --lakes .cache/hydrolakes-global.zip --krishna .cache/ne-10m-rivers.geojson \
  --pulicat .cache/osm-pulicat.json
```

Save the [HydroLAKES v1 polygon archive](https://data.hydrosheds.org/file/hydrolakes/HydroLAKES_polys_v10_shp.zip),
[Natural Earth v5.1.2 1:10m river lines](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_10m_rivers_lake_centerlines.geojson)
and [the OpenStreetMap Pulicat Lake relation snapshot](https://api.openstreetmap.org/api/0.6/relation/1624070/full.json)
using the filenames above. Keep the regional OSM responses from
[`pipeline/india/open_river_sources.json`](pipeline/india/open_river_sources.json) in `.cache` as well. That manifest
records the public Overpass endpoint, exact queries, base timestamps and SHA-256 hashes. Reuse the pinned responses
when rebuilding. Replaying the queries against a newer OSM database yields a new edition.
HydroLAKES is CC BY 4.0, Natural Earth is public domain, and the OSM river data is available under ODbL 1.0
with credit to OpenStreetMap contributors.
Add `?rivers=legacy` to the preview URL to compare the original free-running Natural Earth river lines.

The IC-34 audit handoff documents how to reproduce the local political-map vector
reference. The preparation step writes charted areas for the registered grid to
`data/interim/soi_boundary_chart.json`. Keep the PDF and extracted vectors in the local cache.

The layered terrain step reuses the sampled grid and checks the pinned inputs in
`pipeline/india/terrain_assets.py`. It stores the archives in `.cache/terrain-layers/`.
Run it again after changing the grid or outline. Prepare the required
[state people and economy inputs](#state-people-and-economy-inputs) before building. Then:

```sh
uv run python -m pipeline all      # fetch and process data sources, build web/data/*.json, check
uv run python -m pipeline serve    # http://127.0.0.1:8765
uv run python -m unittest discover -s tests
```

The Military layer takes its points from the civil gazetteers. To reproduce the
optional town coverage, prepare Natural Earth Populated Places 5.1.2 from the
[pinned shapefile archive](https://naturalearth.s3.amazonaws.com/5.1.2/10m_cultural/ne_10m_populated_places.zip)
and use the existing City View GHSL archive. The GeoNames India extract for
27 Nov 2026 supplies additional civil populated places.

```sh
uv run --no-project --with pyproj --with pyshp python -m pipeline.india.military_gazetteer ne .cache/ne_10m_populated_places.zip
uv run --no-project --with pyproj --with pyshp python -m pipeline.india.military_gazetteer ghsl .cache/ic37-ghsl.zip
uv run --no-project --with pyproj --with pyshp python -m pipeline.india.military_gazetteer geonames .cache/IN.zip
```

### Historical Census civic measures

With the DataMeet, Census A-01 and City View inputs prepared, fetch the pinned
ORGI workbooks and rebuild the historical Citizens, Explorer and civic lenses.
Omit `--fetch` when the workbook cache is already populated.

```sh
uv run --no-project --with xlrd --with openpyxl python -m pipeline.india.census_civic .cache/census-civic --fetch
uv run python -m pipeline build states lenses city_view catalog --force
uv run python -m pipeline check
```

The build publishes derived shares, reported distance bands and categories from
Census 2011 and the 2010 Houselisting phase. City figures describe the urban
residents or households of the member districts of the mapped footprint.
State values sum District Census counts before dividing. Andhra Pradesh and
Telangana state comparisons have no value because the 2011 Khammam district
crosses the modern state line. Ladakh uses Census Leh and Kargil.

`web/data/` is generated and git-ignored: `world.json` is derived from the Survey of India outline, whose terms for
redistributing derived data are unresolved. No outline geometry is shipped, only each hex's land or water class.
Publishing is the owner's decision; there is no deploy package.

### Historical resident occupations and industries

With the DataMeet, Census A-01 and City View inputs prepared, run:

```sh
uv run --no-project --with openpyxl python -m pipeline.india.census_work .cache/census-work --fetch
uv run python -m pipeline build city_view catalog --force
uv run python -m pipeline check
```

Omit `--fetch` when the pinned workbooks are already cached. Citizens and
Explorer use B-25 A and B, with a matching urban India benchmark. Workforce
uses B-18. Each share describes the urban residents of all member districts,
using main and marginal workers, excluding cultivators and agricultural
labourers and the sensitive or inseparably mixed categories excluded by the
crosswalk. The two tables have independent denominators.
The B-18 exclusions follow the [MoSPI NIC 2008 classification](https://www.mospi.gov.in/sites/default/files/main_menu/national_industrial_classification/nic_2008_17apr09.pdf)
(SHA-256 `bedd891d8ab05305e1fde4cf125fbbc2c42e58395070622a67d6329c56bd6d37`).

### Protected land

Build the map once to register its grid. Place the checksum-pinned snapshots listed in
[`pipeline/india/protected_land_sources.json`](pipeline/india/protected_land_sources.json)
in `.cache/ic27/`. The manifest includes each publisher URL and the Overpass queries.
Replaying a query against a later database gives a new snapshot. The national park
inventory PDF is read with Poppler's `pdftotext`.

```sh
uv run --no-project --with 'shapely>=2.1' python -m pipeline.india.protected_land .cache/ic27
uv run python -m pipeline build almanac --deps
uv run --with 'shapely>=2.1' python -m unittest discover -s tests -p test_protected_land.py
```

Reprepare after changes to the grid or DataMeet boundaries. The October 2026 Ramsar
list and published GIS extents are from the Secretariat of the Convention on Wetlands
(CC BY 4.0). The national park and tiger reserve names and designations are credited
to WII and NTCA. OpenStreetMap contributors provide matched extents and fallback
positions (ODbL 1.0). Wikidata provides additional point locations (CC0 1.0).
Unmatched roster entries remain unlocated.

The Wonders Almanac records the five largest national parks by area in the pinned WII
inventory. Park and Ramsar wonder footprints use the accepted protected land hexes.
Research wonders use verified IISc, IIT and IISER locations from the Science roster. The class
order is alphabetical and the count refers to mapped sites in that class.

### Crop resources

In an existing checkout with a built map, refresh the resource markers and source catalogue with:

```sh
uv run python -m pipeline build resources catalog
```

Crop markers represent documented growing areas. The [Food input contract](docs/DATA_CONTRACTS.md#_crop_production-interim)
currently carries no tile tonnage. The Ministry's crop-year release provides national totals and the OGD district
download was unavailable during verification.

### City View footprints

For historical flood impacts, save [IFI-Impacts v3](https://zenodo.org/records/11275211/files/India_Flood_Inventory_v3.csv)
as `.cache/ic66-flood-inventory.csv` and prepare the dated district records before building City View.

```sh
uv run python -m pipeline.india.historical_floods .cache/ic66-flood-inventory.csv
```

The regular build enables City View with point locations if the optional spatial inputs have not been prepared.
For the full view, build the atlas once, then save the [GHSL Central and Southern Asia archive](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_REGION_R2024A/GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A/V1-2/GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A_V1_2.zip)
as `.cache/ic37-ghsl.zip` and the [WorldPop India GeoTIFF](https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2026/IND/v1/1km_ua/constrained/ind_pop_2026_CN_1km_R2025A_UA_v1.tif)
as `.cache/ic37-worldpop.tif`. Run the preparation again after changing the grid, source layers or match rules.

```sh
uv run python -m pipeline process gem_power gem_coal gem_iron gem_oil_gas
uv run python -m pipeline build resources
uv run --no-project --with pyogrio --with rasterio --with pyproj --with 'shapely>=2.1' \
  python -m pipeline.india.city_view .cache/ic37-ghsl.zip .cache/ic37-worldpop.tif
uv run python -m pipeline build
uv run python -m pipeline check
```

The preparation verifies both SHA-256 pins and prints the match and district audit. A new match requires a unique
GHSL centre covering the UN point, a matching name and overlap with the primary state. New matches that overlap
another matched footprint stay point-only. GHSL uses a 2025 reference epoch as a spatial proxy for the UN
agglomerations. The Survey of India outline and the atlas lake mask bound the
land intersections. IndiaCiv estimates use WorldPop pixel-centre population mass to distribute the mid-2026 UN
total across hexes, with largest-remainder rounding. The member district table uses the 1 March 2026 district projections and mapped densities. Explorer also retains
the WorldPop district and footprint population crosswalk. The schematic district plaques use workplace concentrations. City View matches resource sites tagged exact in the processed GEM inputs. For an existing cache,
rerun the GEM process command above with `--offline` and rebuild to refresh resource coordinates and joins.

The same preparation audits empty district assignments using the largest positive-area intersection of
Indian land with an in-state Census district. Hex density gaps use area-weighted WorldPop population divided by
Indian land area where valid pixels cover at least 80% of that land. Neither repair replaces populated cells.
Ladakh's state-level median uses the Census 2011 single-year age counts for Leh and Kargil when WorldPop does
not cover enough of the mapped UT. Regenerate it with the Census civic preparation above.

### City View citizens and industry

Download the checksum-pinned [Jul–Sep 2026 PLFS bulletin](https://mospi.gov.in/uploads/publications_reports/publications_reports1794297172776_05eae330-7f2d-45ec-84c5-07031201ecf1_PLFS_QB_July-Sept_2026_m.pdf)
to `.cache/ic38-plfs.pdf`. The extractor uses Poppler's `pdftotext` and reads Appendix A Tables 3–5.
For the city age profiles, extract the 40 age-band GeoTIFFs from the
[WorldPop India 2026 constrained age and sex 1 km release](https://data.worldpop.org/GIS/AgeSex_structures/Global_2015_2030/R2025A/2026/IND/v1/1km_ua/ind_agesex_structures_2026_CN_1km_R2025A_UA_v1.zip)
into `.cache/ic38-age/`.

To add Explorer district median ages from those same grids, run:

```sh
uv run --no-project --with rasterio --with pyproj --with pyogrio --with 'shapely>=2.1' \
  python -m pipeline.india.district_age .cache/ic38-age
uv run python -m pipeline build lenses catalog
```

IndiaCiv sums the male and female age-band estimates at grid pixel centres inside DataMeet districts.
It estimates the median by interpolating within the band that contains half the population.
Districts without populated grid pixels have a blank value.

```sh
uv run python -m pipeline.india.city_labour .cache/ic38-plfs.pdf
uv run --no-project --with pyogrio --with rasterio --with pyproj --with 'shapely>=2.1' \
  python -m pipeline.india.city_view .cache/ic37-ghsl.zip .cache/ic37-worldpop.tif --age-dir .cache/ic38-age
uv run python -m pipeline build
```

For gaps in the quarterly labour coverage, save the revised
[Annual PLFS 2025 report](https://www.mospi.gov.in/uploads/publications_reports/publications_reports1780040415321_0624fb13-fb47-40bc-b470-7c7e9635c3ef_PLFS_2025_F_REV_29052026.pdf)
as `.cache/ic76-annual-plfs.pdf` and run
`uv run python -m pipeline.india.annual_labour .cache/ic76-annual-plfs.pdf`. The preparation
checks the report checksum and reads Appendix A Tables 1 and 31–33 for calendar 2025
sample sizes, employment rates, unemployment rates and broad industry shares.

For a smaller download, pass `--age-api-cache .cache/ic38-age-api` in place of `--age-dir`. This sends the
clipped footprints to the public WorldPop v3 service without an account and caches the responses by query
hash. The service uses its 2026 100 m population grid and administrative-unit age shares. The Almanac
records which WorldPop method supplied the estimate. Pass both `--age-dir` and `--age-api-cache` to use
the cached API series for previously reviewed cities and offline rasters for the expanded cohort. For
the median-age lens, each raster band needs 80% valid land pixel centres. A cached API observation can
fill that gap if WorldPop reports complete age coverage for its counted population. State medians
additionally require 80% population raster coverage over the mapped state or UT land.

Citizens uses WorldPop age estimates and dated Census 2011 occupation, education, birthplace and commute shares.
Workforce shows IndiaCiv resident workforce estimates using PLFS urban rates. Districts uses civilian workplace
specialisations from the Sixth Economic Census (January 2013 – April 2014) where a checked UA match exists.

The Explorer uses the [Air & weather inputs](#air--weather-inputs), City View footprints and selected
district-linked 2026 reports. The House Price Index uses the provisional Apr–Jun 2026
row of the RBI's [DBIE House Price Index table](https://data.rbi.org.in/DBIE/#/dbie/reports/Statistics/Real%20Sector/Prices%20&%20Wages),
issued with the [24 August release](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63436).
The builder uses the publisher's market labels and preserves the published index precision.

### City View economy and gateways

Economy shows GDP, GDP per resident and six yields with ranks across the mapped urban agglomerations. City GDP is the
Gold estimate, which allocates state output by projected urban population and uses footprint population
for cross-state splits. GDP per resident divides by the UN mid-2026 population. The sector bars use
published advance estimates of nominal state GSVA for Delhi, Maharashtra and Andhra Pradesh. The state
panel also uses published advance estimates for Odisha and Telangana.
For the compatible RBI series, IndiaCiv estimates apply the national nominal growth rates to each
historical state sector and recompute sector shares. Agriculture includes allied activities and
industry includes mining.

After refreshing IC-23 transport, rebuild `city_view` to update its nearest major port, nearest scheduled-service
airport in each size class and rail gateway distances. Named rail paths qualify when they enter a footprint
cell or one of its neighbours. With no nearby named path, City View shows the closest mapped main line
in the same area and its OpenStreetMap name when available. Compare uses the recorded periods, survey
definitions and Science coverage basis for both cities, and shows the valid reporting-day denominator
for each AQI count.

### Air & weather inputs

Prepare any of the three lens inputs locally before building. The November 27 snapshot archives are in the IC-24
handoff's `inputs/` folder. The command checks each input against the checksum in `pipeline/india/__init__.py`.

```sh
uv run python -m pipeline.india.air_weather \
  --aqi .cache/aqi-jan-oct-2026.zip \
  --pm25 .cache/pm25-jan-oct-2026.zip --stations .cache/air-stations.csv \
  --rainfall .cache/monsoon-2026.csv --geometry .cache/imd-subdivisions.json
uv run python -m pipeline build --force
```

- The city AQI and hourly station archives are JSON exports from the
  [India Air Quality Portal](https://airquality.aqmsat.com/downloads). City AQI uses the National AQI Bulletin's
  city daily series. The fraction counts reported AQI days at 201 or higher, with at least 244 of the period's 304
  days. Station PM₂.₅ uses the portal's CAAQMS hourly exports for the same window. Each station day needs at least
  18 valid hourly readings and each station needs 244 valid days. The district value uses inverse-distance-squared
  weighting of eligible stations within 150 km of the largest district polygon's area centroid, with distance in
  projected map km. Station coordinates come from [XKDR Forum's 23 November snapshot](https://github.com/xKDR/Air-Quality-Database/blob/main/stations/station_coordinates_portal_2026-11-23.csv)
  (CC BY 4.0). Districts without an eligible station within 150 km stay blank.
- The monsoon input comes from [IMD Table 2, 30 September 2026](https://mausam.imd.gov.in/backend/assets/pdf_to_img_nwfc_monsoon/14_IMD%20SDWR%2030%20September%202026_6abce82b302f8.png)
  via the [India by Numbers CSV transcription](https://indiabynumbers.org/charts/monsoon-2026-by-subdivision.csv).
  The [IMD subdivision GeoJSON](https://mausam.imd.gov.in/imd_latest/contents/district_shapefiles/sd_boundary_rainfall.json)
  determines the subdivision at each Indian hex centre. The browser receives only the rainfall departure per hex.
### State people and economy inputs

Save these pinned releases under `.cache/ic25/` using the filenames in the table. The checksums
are in [people_sources.py](pipeline/india/people_sources.py). Use the existing MoHFW projection PDF
at `.cache/tg-projections-2019.pdf`. The preparation step uses Poppler's `pdftotext`.

| Filename | Release |
| --- | --- |
| `plfs` | [MoSPI quarterly PLFS bulletin, Jul–Sep 2026](https://mospi.gov.in/uploads/publications_reports/publications_reports1794297172776_05eae330-7f2d-45ec-84c5-07031201ecf1_PLFS_QB_July-Sept_2026_m.pdf) |
| `jjm` | [PIB JJM annex, 18 July 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2290048&lang=1&reg=3) |
| `gsdp` | [MoSPI nominal GSDP API, indicator 23](https://api.mospi.gov.in/api/nas/getNASData?base_year=2011-12&series=Current&frequency_code=1&account_code=2&indicator_code=23&limit=100&page=1) |
| `gsdp-mirror` | [Measure of India nominal GSDP CSV](https://measure.thisindianlife.today/data/states-gsdp-current.csv), October 2026 edition |
| `delhi` | [Economic Survey of Delhi, FY 2025-26](https://delhiplanning.delhi.gov.in/sites/default/files/2026-03/economic_survey_english_0.pdf) |
| `gdp` | [MoSPI provisional GDP release, FY 2025-26](https://www.mospi.gov.in/uploads/latestReleases/latest_release_1780655857536_5ac01869-ca4a-422d-b7a7-57b81da60932_Press_Note_on_GDP_Estimates_for_Q4_2025-26_and_PE_FY_2025-26_F.pdf) |
| `cea` | [CEA Load Generation Balance Report, Annex II](https://cea.nic.in/api/dashboardReports/download-pdf/en/db851876-390a-48c4-b450-d3ce66b64a89) |
| `wage-schedule` | [Rural jobs guarantee wage schedule, effective 1 July 2026](https://egazette.gov.in/WriteReadData/2026/273958.pdf) |
| `wage` | [PIB release with the notified national wage average](https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2279660&lang=2&reg=48) |

Save the historical household sources in `.cache/ic75/` under the names below. The
[source registry](pipeline/india/household_cost_sources.py) records the report tables and checksums.
Install Tesseract for the NFHS-6 pages with raster indicator tables. The preparation step uses
Poppler's `pdftoppm` for those pages.

| Filename | Release |
| --- | --- |
| `hces.pdf` | [MoSPI Household Consumption Expenditure Survey 2023–24, Report 592](https://mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf) |
| `telecom.pdf` | [MoSPI Comprehensive Modular Survey Telecom 2025, Report 593](https://mospi.gov.in/sites/default/files/publication_reports/CMST_report_m.pdf) |
| `rent.pdf` | [MoSPI NSS 76, Report 584, Statement 24.5](https://mospi.gov.in/sites/default/files/NSS7612dws/Report_584_final.pdf) |
| `nfhs6.pdf` | [MoHFW and IIPS NFHS-6 state factsheets](https://www.mohfw-dohfw.gov.in/static/uploads/2026/05/111ff4a13ca36b5cabb7f94aec5bb0ce.pdf) |
| `poverty.html` | [RBI Bulletin Rangarajan-method estimates, Table 3](https://www.rbi.org.in/scripts/BS_ViewBulletin.aspx?Id=23647) |
| `up.html` | [MoSPI Uttar Pradesh district consumption pilot, PIB Release 2201360](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2201360&lang=1&reg=3) |

```sh
uv run python -m pipeline.india.people_metrics .cache/ic25 .cache/tg-projections-2019.pdf
uv run python -m pipeline.india.household_costs .cache/ic75/hces.pdf .cache/ic75/telecom.pdf \
  .cache/ic75/rent.pdf .cache/ic75/nfhs6.pdf .cache/ic75/poverty.html .cache/ic75/up.html
uv run python -m pipeline build --force
```

To add the district household observations, save the pinned [NFHS-5 workbook mirror](https://raw.githubusercontent.com/databandar/Stutnting_vs_tobacco/885b123efec9bfd1d3041ad17a614600074e71ae/NFHS_5_India_Districts_Factsheet_Data.xls)
as `.cache/ic75/nfhs5-mirror.xls` and the [NITI MPI report](https://niti.gov.in/sites/default/files/2023-07/National-Multidimentional-Poverty-Index-2023-Final-17th-July.pdf) as `.cache/ic92/niti-mpi.pdf`. The optional Goa tap-share pilot uses the archived 27 Nov 2026 J5 district page
as `.cache/ic92/jjm-goa.html`. Omit the last option when that exact snapshot is unavailable.

```sh
uv run --no-project --with xlrd python -m pipeline.india.district_households \
  .cache/ic75/nfhs5-mirror.xls .cache/ic92/niti-mpi.pdf --jjm-goa .cache/ic92/jjm-goa.html
```

To prepare Census 2011 urban-district cultivation shares, save the
[PCA SD workbook](https://censusindia.gov.in/nada/index.php/catalog/6191/download/9268/DDW_PCA0000_2011_Indiastatedist.xlsx)
as `.cache/ic75/pca-district.xlsx` and run
`uv run --no-project --with openpyxl python -m pipeline.india.census_cultivation .cache/ic75/pca-district.xlsx`.

To add the Varanasi rural grazing share, save the
[ORGI Village Directory PDF](https://censusindia.gov.in/nada/index.php/catalog/1300/download/4214/DH_2011_0966_PART_A_DCHB_VARANASI.pdf)
as `.cache/ic75/varanasi.pdf` and run
`uv run python -m pipeline.india.village_land_use .cache/ic75/varanasi.pdf`.

If a live source has moved to a new revision, use the matching cached edition. The public files
contain state metrics. Publisher PDFs, tables and historical state output amounts stay in the
local source preparation workflow.

### Transport inputs

Airport points come from the pinned OurAirports snapshot and must match the
standalone civilian subset verified against AAI's 16 Jan 2026 inventory.
Re-run transport preparation to refresh way names and network tags or airport municipalities,
and after updating the civilian gate.

Save the [pinned OurAirports CSV](https://raw.githubusercontent.com/davidmegginson/ourairports-data/a537e082ac8c8fe6ab509df1f128cc6704fe73c1/airports.csv)
to `.cache/ic23-airports.csv`. Copy the archived, uncompressed OpenStreetMap regional Overpass responses listed in
`pipeline/india/transport_overpass.json` to `.cache/ic23-overpass/`. The manifest records the exact queries,
response timestamps and SHA-256 pins. Keep the archived responses with the other local source inputs.
The project coordinator approved these regional Overpass queries as the substitute for the planned Geofabrik
India extract.

```sh
uv run python -m pipeline.india.transport .cache/ic23-airports.csv --overpass-dir .cache/ic23-overpass
uv run python -m pipeline build almanac --deps
uv run python -m pipeline check
```

The national rail view follows 13 named corridors, including both dedicated freight corridors. Other mapped
main lines appear at regional zoom and secondary lines appear closer in. The highway layer shows open motorways
and Golden Quadrilateral routes first, followed by other mapped national highways. Geometry is sampled on the 18 km grid, and parallel
ways can share a link. Hover over tagged links at local zoom to see the names, refs and network tags.
The ports layer and Commerce show cargo ranks and shares derived from MoPSW Table 1 advance estimates for
FY 2025-26 (1 Apr 2025 – 31 Mar 2026). The Railways Almanac uses the PIB freight loading table for the same period.
The map credits © OpenStreetMap contributors. Use **Download OSM-derived data (ODbL)** in the Almanac’s
Sources entry to save the served transport JSON. Its `osm_license` field identifies the parts covered by the
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
To decode a rail or road link, take its first two values as cell indices into the matching `world.json` grid.
For each index, compute `row = floor(index / cols)` and `col = index % cols`. Join the two hex centres
at `x = sqrt(3) * radius * (col + 0.5 * (row % 2))` and `y = 1.5 * radius * row` in map kilometres.

### Trade layer

The infrastructure build reuses the two Dedicated Freight Corridor paths and puts IndiaCiv’s
schematic coastal network on connected sea hexes. Table 1, coastal cargo, column 9 in the
[October 2026 MoPSW report](https://shipmin.gov.in/sites/default/files/Cargo%20handled%20at%20Major%20Ports%20October%2C%202026.pdf)
supplies each authority’s advance estimate for Apr–Oct 2026 (1 Apr 2026 – 31 Oct 2026).
The checksum and credit appear in the Almanac. Port branch widths follow individual throughput.
The shared dashed sea lane has no weight.

### IndiaCiv yields

The yield builder uses the [state metrics inputs](#state-people-and-economy-inputs) for nominal GDP, projected urban population
and electricity supplied. Food uses the final national foodgrain figure with an ESA WorldCover cropland allocation.
IC-26 maps crop presence, so Food uses this allocation until tile tonnage is available. Culture uses the ten ASI
monuments with the most domestic entries. Download [India Tourism Statistics 2026](https://www.tourism.gov.in/static/uploads/2026/09/a1ff37713ad3922f69778dca13aa65ab.pdf)
and prepare its pinned table locally with Poppler. The website shows derived CEA and ASI scores.

```sh
uv run python -m pipeline.india.yield_data .cache/india-tourism-statistics-2026.pdf
uv run python -m pipeline build --force
```

Science weights public IIT, IISc, IISER, NIT, AIIMS, CSIR and Department of Space institutions by class. State and
national scores use the full rosters. City scores use points from official maps, Wikidata (CC0) or OpenStreetMap
(ODbL), checked against the published locality's DataMeet district. The pinned points and their URLs live in
`pipeline/india/config/science_points.json`. Faith counts selected pilgrimage destinations.
Re-run the City View footprint preparation to add the clipped rings and rebuild the yields.
The Almanac lists periods and source credits. Each yield tooltip shows its underlying value or derived score and
the local estimate status.

### Advisor statistics

Knowledge uses the Science inventory. Defence & veterans draws on
public budget, civic and welfare sources. The 61-board DGDE directory provides state counts. The map can locate
verified public board offices in Pune and Secunderabad (© OpenStreetMap contributors, ODbL 1.0). State veteran
figures carry forward the last comparable annual change in registrations. Himachal Pradesh district rates use
registrations from the state's Statistical Year Book, Table 2.22, divided by WorldPop population.

The existing PLFS preparation adds Appendix A Table 4 rural+urban worker shares to Explorer for the 22 published
States/UTs. Prepare it again if your local interim predates these fields. The veteran population step uses the
pinned WorldPop grid and DataMeet polygons to total mid-2026 residents for the rate denominators.

```sh
uv run python -m pipeline.india.city_labour .cache/ic38-plfs.pdf
uv run --no-project --with rasterio --with pyogrio --with pyproj --with 'shapely>=2.1' \
  python -m pipeline.india.advisor_population .cache/ic37-worldpop.tif
uv run python -m pipeline build --force
uv run python -m pipeline check
```

## Historical workplace specialisation and overseas port cargo

Download the CSV archives for **2013 Economic Census**, **Population Census keys** and **Shric to NIC08**
from the [SHRUG download index](https://www.devdatalab.org/shrug_download/data). Save them as
`ec13.zip`, `keys.zip` and `shric.zip` in `.cache/ic67`. In the same folder save the Census 2011
[Urban Agglomeration workbook](https://censusindia.gov.in/nada/index.php/catalog/45261/download/48987/PCA11-UA-0000.xlsx)
as `ua.xlsx` and [Basic Port Statistics of India 2024–25](https://shipmin.gov.in/sites/default/files/BPS%202024-25_compressed.pdf)
as `ports.pdf`. The preparation steps verify pinned checksums. Port extraction uses Poppler's `pdftotext`.

```sh
uv run python -m pipeline.india.workplace .cache/ic67
uv run python -m pipeline.india.port_directions .cache/ic67/ports.pdf
uv run python -m pipeline build workplace almanac --deps
uv run python -m pipeline check
```

Workplace counts describe the Sixth Economic Census (January 2013 – April 2014). Matched Census 2011 UA
components are counted once, and UAs with missing or ambiguous components stay blank. State totals use
whole compatible Census districts. Jobs and LQ use total non-farm employment less the defence-mixed SHRIC 72
group. Employment in that group is also removed from the publisher's harmonised manufacturing total.
The source cannot isolate establishment counts where excluded employment is present. The separate
`workplace.json` adaptation carries SHRUG's CC BY-NC-SA 4.0 licence.

The Almanac displays each port's share of overseas cargo loaded and unloaded.
The FY 2024-25 edition supplies all-commodity port totals in tables 2.1.3 and 2.2.1, and state totals in
tables 3.1.3 and 3.1.4. Unmatched port rows stay blank.
The standard build uses the reviewed Table 2.2.1 transcription for 11 non-major
ports. The map tooltip reports metric tonnes with the reporting period. Explorer
reports the coastal and overseas shares. The existing port preparation command
also verifies the transcription against the pinned PDF.

For the March AAI traffic annexures and the DGMA directed coastal subset, download the
following reports into a local cache. The prep commands use Poppler and verify SHA-256
before extraction.

- AAI [Annexure III](https://www.aai.aero/sites/default/files/traffic-news/Mar2k26Annex3_0.pdf)
  and [Annexure IV](https://www.aai.aero/sites/default/files/traffic-news/Mar2k26Annex4.pdf),
  keeping the filenames from the download URLs.
- DGMA [Coastal Shipping Committee report, table 7](https://dgma.gov.in/download/1769691524_697b598415456_coastal-committee-report-final-jan2026.pdf),
  saved locally as `dgma.pdf`.

```sh
uv run python -m pipeline.india.port_directions .cache/ic67/ports.pdf
uv run python -m pipeline.india.airport_traffic .cache/ic94/aai
uv run python -m pipeline.india.coastal_shipping .cache/ic94/dgma.pdf
uv run python -m pipeline build --force
```

Repeat these prep steps when upgrading an older cache. The build rejects earlier
interim versions, including the 15-port direction extract.

The Almanac shows airport shares against each fiscal column's national total.
Passenger growth uses the two airport measurements from the same annexure.
These observations publish only display text at 0.001 percentage-point precision,
with positive values below the threshold shown as `<0.001%`. Airport analogues
have no rank or score.

The Almanac's DGMA entries preserve direction and groups with matched port IDs.
Relative cargo categories divide the entry's low by the reference high and
its high by the reference low, then round outward in 25-percentage-point steps.
The reference is 100% by identity. Single-port pairs include great-circle separation.
The 2026 schematic carries its original geometry and single-port observations.

## Data period rule (owner decisions, 27 Nov 2026)

The map prefers 2026 measurements, estimates and projections. These also count as 2026,
and are labelled with their exact start and end dates wherever they are shown:

- **FY 2025-26:** 1 April 2025 – 31 March 2026.
- **Any other 12-month reporting year ending in 2026**, e.g. crop year 2025-26 (1 July 2025 – 30 June 2026) and
  coffee year 2025-26 (1 October 2025 – 30 September 2026).
- **IndiaCiv estimates**, computed from real inputs by a method stated in the Almanac and marked as estimates.

When no 2026 value or sound 2026 estimate exists, show the newest older official or reputable figure.
Carry its real period in the data and display it wherever the value appears.

## How the India data fits usaciv

- **Projection.** Lambert azimuthal equal-area (WGS 84) centred on 22° N, 82° E (`pipeline/core/geo.py`), snapped so
  the cells of IndiaCiv's 18 km-radius axial grid (`pipeline/india/grid.py`) fall exactly on the map's odd-r hex centres.
- **Land.** India's extent and detached islands follow the Survey of India outline. Natural Earth supplies
  neighbouring countries and rivers.
- **States and districts.** DataMeet's current state outlines decide each Indian hex's state, and its Census 2011
  district outlines the hex's district (the `county` of usaciv), joined to Census table A-01 by district code.
  Every UT and each detached part of the two multipart UTs gets a tile.
  State populations come from the Technical Group projections for 1 March 2026. The age lenses also use the
  checksum-pinned [WorldPop R2025A v1](https://doi.org/10.5258/SOTON/WP00841) age and sex estimates for 2026
  (CC BY 4.0) for Goa and five union territories. The density lens averages
  the districts under a hex's 7 sample points and blends in, by area, the small city districts between the points.
- **Terrain.** Relief and elevation from ETOPO1; land cover from ESA WorldCover 2021 mapped onto usaciv's fixed cover
  ids (`pipeline/build/world.py`). WorldCover has one tree class: forest is drawn as conifer at 2,000 m and above.
- **Cities.** UN DESA supplies the coordinates and projected mid-2026 populations of Indian urban agglomerations.
  When two fall in a hex, the larger one is shown. Delhi carries the capital star. The city lenses show projected
  population and projected growth from 1 July 2025 to 1 July 2026 on city hexes. Rerun the UN workbook and
  Technical Group PDF preparation steps to refresh older interim files.
- **Art.** US-specific stamps are off: no centre pivots, mesas, barns, cacti, churches or Capitol complex.

- **Resources.** The pipeline uses checksum-pinned public map exports from Global Energy Monitor's [Global
  Integrated Power Tracker](https://globalenergymonitor.org/projects/global-integrated-power-tracker) (September
  2026), [Global Coal Mine Tracker](https://globalenergymonitor.org/projects/global-coal-mine-tracker) (August
  2026), [Global Iron Ore Mines Tracker](https://globalenergymonitor.org/projects/global-iron-ore-mines-tracker)
  (September 2026 V1), and [Global Oil and Gas Extraction Tracker](https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker)
  (March 2026). The exports are CC BY 4.0, with TransitionZero's Solar Asset Mapper records under CC BY-NC 4.0.
  The power map export has no row-level license flags, so treat the solar layer as noncommercial. Rated power
  capacity is summed by plant and technology. Mine sizes use capacity in the snapshot. Oil and gas markers count
  operating fields. Sites are placed on Indian land hexes, with a limited snap to nearby land.
  Pumped storage uses GEM's unit technology and a CEA pumping-status cross-check. Named oil-only and gas-only
  fields are classified by the tracker name. Mixed and unspecified fields retain a shared category. The curated
  inventory counts verified civilian mines and battery projects. Silver appears as a by-product of the host mine.
  Refresh existing GEM interims from the cached raw exports with
  `uv run python -m pipeline process gem_power gem_oil_gas` before rebuilding.

- **Wonders.** The pinned November 2026 IC-8 inventory supplies 55 built and 26 natural features.
  The build projects their coordinates onto the current grid. The layer includes point markers for
  small islands and Mount Kailash in Tibet. Source credits and the CC BY-SA 4.0 licence for
  `wonders.json` appear in the Almanac.
