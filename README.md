# IndiaCiv

India drawn like a turn-based strategy map: painted hex terrain, rivers, city tiles and banners, search, a minimap,
share links and an Almanac that cites every source. It is a fork of
[usaciv](https://karpathy.ai/usaciv) by Andrej Karpathy (MIT, see [LICENSE](LICENSE)): the engine, art and interface
are usaciv's; the data pipeline is rebuilt for India.

**So far.** Terrain, cities, the 36 states and union territories, district, state, health and city lenses, and
tile resources (press **R**) and wonders (press **W**). The Map menu includes railways, highways, ports and
airports. Population figures are projected for 2026. City View opens
for the 50 largest urban agglomerations in the frozen UN cohort. Six yields appear in the top bar and map panels.
Choose Disasters in the lens picker for documented incident counts by district or state/UT and hazard type.
The Culture advisor lists the dated source records. City View Conditions shows incidents in member districts.
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
# Climate, detailed relief, and terrain features (about 1.8 GB cached; requires bsdtar for GFPLAIN)
uv run --no-project --with rasterio --with pyproj --with 'shapely>=2.1' python -m pipeline.india.layered_terrain
# UN World Urbanization Prospects File 22
uv run --no-project --with pyproj --with xlrd python -m pipeline.india.cities .cache/wup2018.xls
# Census of India 2011 table A-01 (the publisher's workbook as .cache/census-a01.xlsx)
python3 -m pipeline.india.census .cache/census-a01.xlsx
# IC-8 research snapshot (save IC-8-wonders.json from the project issue materials in .cache)
python3 -m pipeline.india.wonders .cache/IC-8-wonders.json
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

`web/data/` is generated and git-ignored: `world.json` is derived from the Survey of India outline, whose terms for
redistributing derived data are unresolved. No outline geometry is shipped, only each hex's land or water class.
Publishing is the owner's decision; there is no deploy package.

### Protected land

Build the map once to register its grid. Place the checksum-pinned snapshots listed in
[`pipeline/india/protected_land_sources.json`](pipeline/india/protected_land_sources.json)
in `.cache/ic27/`. The manifest includes each publisher URL and the Overpass queries.
Replaying a query against a later database gives a new snapshot. The national park
inventory PDF is read with Poppler's `pdftotext`.

```sh
uv run --no-project --with 'shapely>=2.1' python -m pipeline.india.protected_land .cache/ic27
uv run python -m pipeline build protected_land wonders catalog
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

The regular build enables City View with point locations if the optional spatial inputs have not been prepared.
For the full view, build the atlas once, then save the [GHSL Central and Southern Asia archive](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_UCDB_GLOBE_R2024A/GHS_UCDB_REGION_R2024A/GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A/V1-2/GHS_UCDB_REGION_CENTRAL_AND_SOUTHERN_ASIA_R2024A_V1_2.zip)
as `.cache/ic37-ghsl.zip` and the [WorldPop India GeoTIFF](https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/2026/IND/v1/1km_ua/constrained/ind_pop_2026_CN_1km_R2025A_UA_v1.tif)
as `.cache/ic37-worldpop.tif`. Run the preparation again after changing the grid, source layers or match rules.

```sh
uv run python -m pipeline process gem_power gem_coal gem_iron gem_oil_gas
uv run python -m pipeline build resources
uv run --no-project --with pyogrio --with rasterio --with pyproj --with 'shapely>=2.1' \
  python -m pipeline.india.city_view .cache/ic37-ghsl.zip .cache/ic37-worldpop.tif
uv run python -m pipeline build city_view catalog
uv run python -m pipeline check
```

The preparation verifies both SHA-256 pins and prints the match and district audit. The GHSL urban centres
provide a spatial proxy for UN agglomerations. The Survey of India outline and the atlas lake mask bound the
land intersections. IndiaCiv estimates use WorldPop pixel-centre population mass to distribute the mid-2026 UN
total across hexes, with largest-remainder rounding. The district table uses WorldPop for both the 2026 district
total and the share within the footprint. The schematic buildings use the atlas relief, water and cover as their
setting. City View matches resource sites tagged exact in the processed GEM inputs. For an existing cache,
rerun the GEM process command above with `--offline` and rebuild to refresh resource coordinates and joins.

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
uv run python -m pipeline build city_view catalog
```

For a smaller download, pass `--age-api-cache .cache/ic38-age-api` in place of `--age-dir`. This sends the
clipped footprints to the public WorldPop v3 service without an account and caches the responses by query
hash. The service uses its 2026 100 m population grid and administrative-unit age shares. The Almanac
records which WorldPop method supplied the estimate.

The Citizens tab shows the state urban unemployment benchmark and IndiaCiv resident workforce estimates
using the primary state's matching all-age and 15+ urban rates. The age bands use the footprint's
WorldPop distribution scaled to the UN total. The Districts tab cites dated government evidence for
workplace clusters. Both tabs are available throughout the frozen City View cohort.

The Conditions tab uses the [Air & weather inputs](#air--weather-inputs), City View footprints and
selected district-linked 2026 reports. The House Price Index uses the provisional Apr–Jun 2026
row of the RBI's [DBIE House Price Index table](https://data.rbi.org.in/DBIE/#/dbie/reports/Statistics/Real%20Sector/Prices%20&%20Wages),
issued with the [24 August release](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63436).
The builder uses the publisher's market labels and preserves the published index precision.

### City View economy and gateways

Economy ranks GDP, GDP per resident and six yields within the 50 City View cities. City GDP is the
Gold estimate, which allocates state output by projected urban population and uses footprint population
for cross-state splits. GDP per resident divides by the UN mid-2026 population. The sector bars use
published advance estimates of nominal state GSVA for Delhi, Maharashtra and Andhra Pradesh.
Agriculture includes allied activities and industry includes mining.

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

```sh
uv run python -m pipeline.india.people_metrics .cache/ic25 .cache/tg-projections-2019.pdf
uv run python -m pipeline build --force
```

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
uv run python -m pipeline build infrastructure catalog
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

## Data period rule (owner decisions, 27 Nov 2026)

Every number shown is for 2026: a 2026 measurement, or an estimate or projection for 2026. These also count as 2026,
and are labelled with their exact start and end dates wherever they are shown:

- **FY 2025-26:** 1 April 2025 – 31 March 2026.
- **Any other 12-month reporting year ending in 2026**, e.g. crop year 2025-26 (1 July 2025 – 30 June 2026) and
  coffee year 2025-26 (1 October 2025 – 30 September 2026).
- **IndiaCiv estimates**, computed from real inputs by a method stated in the Almanac and marked as estimates.

Older figures are never shown or relabelled as 2026.

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
