# Data contracts (v2)

The pipeline (Python) and the browser (web/js) agree on these files in `web/data/`. Change a contract here first, then on
both sides. All coordinates are **map km**: Lambert azimuthal equal-area centred on India, origin top-left, y **down**
(see `pipeline/core/geo.py`).

**Observation periods.** An older fallback carries `vintage: "older"` and its own `period`, for example
`"Census 2011"` or `"NFHS-5 (2019-21)"`. Put both fields on the same value record, or together in its
per-field provenance when the value is stored as a scalar. A lens may carry the pair when all its values
share that period. For a state lens with mixed periods, carry the pair in each older value's
`state_details` entry. The legend lists the periods and the tooltip identifies the cell's period.
City population lenses carry older provenance in `cell_details`, keyed by cell index. Mixed Explorer
columns name their periods in the header and label each populated cell.
The fallback does not qualify for 2026 growth or ranks.

State profiles, City View profiles and district lens records can expose
additional Explorer observations through `advisor_columns`. Each entry uses the
column key and carries its label, group, format, unit, value, period and source.
Older entries carry `vintage: "older"`. Sparse observations can also include
`coverage` for the table caption. `nation.json` and `workplace.json` use
`advisor_fields` for columns whose values already have stable paths. The
`advisor_tables` builder resolves those declarations and spatial joins before
shipping `advisor_tables.json`.

`nation.national_gva` holds provisional national current-price GVA in rupees
for the Almanac. State Explorer columns retain GSVA shares. Economy's native
`nation.nation.jobs` and `employed` values use the national age-15+ PLFS
denominator, and national sector count estimates use the published rounded
shares. City `jobs` and `employed` use the age-15+ universe where sector counts
exist. Explorer retains the separate all-ages count.

`disasters.json` uses the upstream Culture advisor's incident tables. Its
`fema` key is the inherited contract name for the documented India inventory.
National totals count unique incidents. State totals count the incidents
affecting each state or UT, so state totals can overlap.

`counties.json` uses the upstream district-table shape. Its `rows` follow the
`world.json.counties` order and align with `columns` and `fields`. The table uses
the Census district code as `geoid` and keys per-value `provenance` by district
code and column key. Each observation carries its own period where applicable.
`cbsa` is blank when no unambiguous district-to-agglomeration assignment exists.

`military.json` carries public national budget, veteran registration, civic board,
school and aggregate defence PSU turnover figures. Turnover is in rupees.
Its `vintage` object labels each headline observation. `national.personnel.active`
carries dated national cohorts, with per-key period, scope and source in
`personnel_provenance`. `installations` carries public DGDE Cantonment Board
towns and command HQ cities. Each point carries `gazetteer.source` and
`gazetteer.id`, plus `gazetteer.district_source` where an administrative
reference resolves a same-name match. The checker reconstructs the point and
its projected cell from the prepared civil gazetteer. District and urban
agglomeration memberships require unique spatial joins. `flagships`
lists published home-port city names, with the ship, period and source in
`flagship_provenance`. A home-port observation does not classify an installation.
The state and district tables carry registered veteran measurements or estimates
with their own provenance. The Almanac source entries carry welfare rates and
public civic board references.

Historical household measures use the existing state metric and lens records. Consumption compares
mean monthly spending per person with the India mean in the same survey sector. The rental-cost
index uses mean rent among renter households in the matching sector. Fixed/Wi-Fi and health-financing
shares use all households as the denominator. NFHS-6 state records carry their own fieldwork dates.
State poverty indexes keep rural and urban Rangarajan-method estimates separate and use the
same-sector median of matched reporting states as 100.

Explorer reads the Uttar Pradesh urban consumption index from city records and mapped district
details. City values require one matching urban member district. Explorer reads the Census 2011
cultivation share from district details and city profiles. City shares pool workers across urban
member districts. Both measures carry their own dated provenance.

Explorer city observations include district shares of the modelled city footprint area and
the share of each district's modelled population inside the footprint. These use different
denominators. The hazard event column pairs each type with its incident date or a labelled
report date when the incident date is unavailable.

City View's `districts.json` uses the existing district IDs for verified sites. A site-only
district has `via: "site"` and dated `sites` entries and omits workplace metrics. A district
with an existing workplace specialty can also carry those entries. Government Plaza
requires a sourced building point within a modelled footprint and member district.
The separate `capital_designation` and `roles` fields supply dated captions alongside
the workplace badge, including the Diversified classification.

Matched ASI wonder records carry `metrics.visitation` with a fiscal period, source, rank and cohort
size. The rank compares total domestic and foreign visits across reporting ticketed sites. The
existing description also shows the cohort and dates. The wonder's selection rank stays separate.

India's City View reads `cities[].gdp_by_industry`. Where detailed industry estimates exist, the
record uses them and carries the balance as `Other industry`. The sum of the rows equals city GDP.
The full industry total remains in `sector_output.values.industry` for aggregate comparisons.
Mining and utilities estimates with older weights carry the dated inputs and method in
`sector_output.fields` and `provenance.gdp_by_industry.fields`. Published fiscal-pair growth
has its own `provenance.economic_growth` and keeps the headline GDP series independent.

`workplace.json` carries independently licensed Sixth Economic Census observations under CC BY-NC-SA 4.0.
It holds `national`, `cities` keyed by UN city ID, `districts` keyed by Census 2011 district code and
`states` keyed by current atlas abbreviation where the historic districts can be combined. Each record
has its own older provenance and can carry jobs, industry shares, location quotients, excess jobs and
harmonised manufacturing share. The workplace and manufacturing totals exclude defence-mixed SHRIC groups.
Establishment counts are omitted when the exclusion could change them.
`thresholds` defines the minimum jobs, local share
and location quotient for a specialisation. Missing or incomplete comparisons are omitted. Workplace
observations have their own historical comparisons and do not feed the resident workforce or output cohorts.

An Indian port's `overseas_direction`, and each entry of `infrastructure.json.overseas_direction_by_state`,
carry FY 2024-25 older provenance and the `loaded` and `unloaded` shares of the same reporting geography's
overseas cargo. Marker sizing and cargo ranks continue to use their own cargo series.

`city_view.json.profiles[id].citizens.census_work` contains separate
`occupations` (B-25 A/B) and `industries` (B-18) Census 2011 observations.
Each carries `period`, `vintage`, `source`, `scope` and fractional `values`.
Occupation `benchmark` fractions describe eligible urban India workers and
the optional `specialist` names a family at least 1.5 times its benchmark.
Both observations describe urban member districts and publish derived shares.
**Historical land cover.** `world.json.historical_land` indexes records by state abbreviation and Census 2011
district geoid. The same records are available on state and district profile rows. Shares are fractions of
native classified land pixels on a 5 km equal-area lattice assigned by map hex ownership. Each metric carries its
source, period and valid sample count. Suppress products with fewer than 30 samples per region. Records with 30
to 99 samples carry `sparse: true` and display their sample count.
Esri v003 (2025) supplies tree cover, cropland and built-up share. Its composition includes seven mapped land
classes and excludes water, clouds and nodata. Other cover sums bare ground, snow or ice, and rangeland.
WorldCover v200 (2021) supplies grassland, shrubland and mapped wetlands (herbaceous wetland and mangrove).
Pasture has no separate measure.

**Historical flood impacts.** `city_view.json.profiles[].historical_flood_impacts` lists up to three recent
IFI-Impacts v3 events with a unique single member district attribution. The `casualties` sum uses reported
deaths and injuries. Tentative or unconfirmed counts are excluded. `lower_bound: true` indicates a missing
component. Each event carries its own period.

`states.json[].census_civic`, `lenses.json.places.counties[geoid].census_civic`
and `city_view.json.profiles[id].citizens.census_civic` carry ORGI derived
series. Each series has `vintage: "older"`, `period`, `source`, `scope`
and `values`. Numeric values are fractions. The median commute band is a
category label. Civic lenses use the
assigned census district for each land cell and attach period metadata at the
lens level. City series use the complete set of urban member districts and
keep their geography with their period.

**India build.** `world.json` has states and union territories, districts (in `counties`) and ESA WorldCover land
cover. The grid uses an 18 km radius and carries `projection` (the `MapProjection` parameters) for
checking geographic ownership. City IDs are UN agglomeration codes. City states are assigned from DataMeet at
the original UN coordinates, with a 10 km nearest-state limit for offshore points. The banner cell may differ. City `population` is the UN mid-2026 projection in people.
`projected_growth` is the fraction from 1 July 2025 to 1 July 2026, or null if unavailable. States and India
use `profile.growth` for the fraction from 1 March 2025 to 1 March 2026. Both carry `growth_period`.
City `ranks` and `rank_counts` report rank and the number of mapped urban agglomerations with a value.
Optional `population_2026` contains `values` keyed by `2026-01-01`, `2026-07-01` and `2026-12-31`, plus
`period`, `source` and `estimated: true`. Values are in people. The July figure is the UN midyear projection.
The endpoints interpolate by day between the adjacent UN midyear values.
The GDP rank uses the nominal INR estimate in `yields.gold`, and `gdp_per_capita` divides it by the UN
mid-2026 population. The growth rank uses `projected_growth`. Equal values keep the order in the city list.
Where available, `mapped_extent` gives the modelled footprint area and intersected hex count with provenance.
`resident_workforce` holds the PLFS-based employed-resident estimate, broad industry mix and state-urban
unemployment benchmark. `industry_plaques` describe documented clusters. `state_sector_mix` and the state
record’s `sector_mix` hold FY 2025-26 nominal GSVA shares, with source, period and estimate flag.
`sector_output` allocates each state’s contribution to city GDP by its GSVA mix and preserves the city GDP
total across three broad sectors. Industry details are part of the industry amount. `output_growth` uses
fixed footprint weights and comparable state GSDP series. `national_shares` uses India’s matching nominal
GDP and a national population projection interpolated to 1 July 2026. City View reuses these records and
the workforce and cluster records. Multi-state workforce estimates weight PLFS urban figures by the state
fragments and require published rates for each. City View `district_badges` identify checked civilian points
within the footprint and a member district. `citizens.age.bands.midlife` uses WorldPop ages 35–64 and
overlaps the headline age bins.
The City View growth fields carry the same 2025–2026 UN projection interval as `projected_growth`. For health values in `profile`, the
`health` metadata carries `period: "2026"` and `estimated: true`. Health lenses carry the same metadata.
City lenses report values
only on city footprints. City, state and national yield values are described below.

**India state comparisons.** `states.json[].employed` is an estimated resident headcount for states with a
July–September 2026 PLFS all-ages worker-population ratio, applied to the projected 1 March 2026 population.
`internet_per_100` divides June 2026 TRAI Internet subscriptions by that March population and rounds to one
decimal. The same value is available in `metrics.internet_per_100`, with source and estimate metadata.
State `metrics` also carries PMAY-Gramin and PMAY-Urban 2.0 completions per 1,000 residents, PM-JAY
cards and ABHA IDs per 100 residents, where available. The matching lens definitions supply each snapshot
period, unit and projection denominator. National scheme comparisons with the same snapshot are in
`nation.json.metrics`. Its `advisor_statistics` contains the independently dated national PM-JAY lower bound
and the September 2026 World Bank poverty nowcast (fraction, with explicit poverty line).
`sector_mix` is optional and carries source, status and derived FY 2025-26
(1 Apr 2025 – 31 Mar 2026) shares of state nominal GSVA. District `hazards` in `lenses.json.places.counties`
uses the City View event schema and appears only where a selected report identifies that district.
District `median_age`, when present, is in years and has its own provenance. It interpolates within the median
WorldPop age band after summing the mid-2026 raster counts by district.

**Almanac.** The optional `world.json.tables.terrain_examples` contains fixture names,
verified map cell indices and the base, relief and feature IDs corroborated by each location.
Indices are recomputed on every build and are never used as route IDs.
Optional `world.json.tables.feature_cells` maps feature IDs to cell intersections from
mapped footprints and point or shoreline evidence. The browser unions these with existing
per-cell feature IDs and counts unique Indian land or rendered water cells.
The URL fragment carries an optional `pedia=kind/id` alongside the map keys. Category indices
use `index`; other IDs come from the source row or a stable terrain key.
Derived lenses can provide `lenses.json.lenses[].sources`, a list of catalogue IDs
for their input datasets. The existing `source` field retains the primary catalogue ID.

**Disasters.** `lenses.json.disasters` contains a dated inventory of selected documented incidents.
Each event has a stable ID, type, label, an occurrence date or a report date, covered district IDs
and state/UT abbreviations, a source, and `estimated: false`. Cyclones carry landfall dates.
Earthquakes carry magnitude and projected epicentres in map km. When the reported location
cannot be resolved to a district in the atlas, the event stays at state/UT level.
An optional `impact` records a district and published incident-specific deaths or physical damage.
The geographic summaries contain distinct event counts, counts by type and the latest dated record
(`last_report_only` distinguishes report dates). Blank lens cells have no matching documented record.
City View joins only member districts and carries the same summary as `hazard_summary`.
District impact stays with the district where the source reported it.

**India yields.** `nation.json.yields` defines Food, Production, Gold, Science, Culture and Faith. Each definition has
`unit`, `scale` (raw units per displayed point), `period`, `description` and Almanac `sources` IDs.
The scalar `yields` values on city, state and national rows are raw tonnes, proxy points, nominal INR, research points,
proxy points and pilgrimage-site counts, respectively. The same rows carry `yield_meta[key].estimated` for IndiaCiv
estimates, optional `source` for the local GDP input, `coverage` for city geography, `derivation` for restricted input
sources and `components` for publishable inputs. CEA availability and ASI ticket counts stay in local interims.
Null means unavailable. A site count of zero means no verified sites in the selected inventory intersect that
geography. City yields use clipped GHSL shapes and district overlap shares when available and a city centre hex
proxy otherwise. The local `yield_rings` in the prepared City View profile are for point membership and stay local.

**Advisor statistics.** `states.json[].advisor_statistics` carries the three PLFS published industry percentages
(agriculture, secondary including mining and quarrying, and tertiary), the DGDE civic board count, estimated
registered ex-servicemen and the fraction of mid-2026 WorldPop residents they represent. The PLFS values retain
published rounding. `nation.json.advisor_statistics` carries the all-India PLFS context, national
budget and welfare records with provenance, and the selected public office points in map km, covered by ODbL 1.0.
`city_view.json.profiles[id].civic_offices` lists public board offices matched inside the clipped footprint or null
when none were verified. `lenses.json.places.counties` carries the estimated ratio of registered ex-servicemen
to mid-2026 WorldPop residents for twelve Himachal Pradesh districts, rounded to 0.01 percentage points.
State estimates are for 30 Jun 2026. District `registered_veterans` is the reported count on 31 Mar 2026
for the Himachal Pradesh pilot.

`world.json.tables.named_boundary_places` lists any hex retained for an Indian locality
by the political-map rule. Each record has a `cell` index, `names` and four `shares`
in km², ordered Indian land, foreign land, water and uncharted area.
The upstream City View opens through the city records in `cities.json`. Each mapped UN agglomeration carries
`city_view: true`. City View reads `footprint`, `counties`, `gdp`, `growth`, `pop_series`, `jobs` and their
provenance directly on each city record. City footprints contain the visible land intersections and the
city anchor. The single `pop_series` point uses the numeric year key `"2026"` for the UN midyear projection.
The district-density array is available in the initial lens catalogue. City View computes estimated residents
per hex from that density and the hex area. Advisor spatial inputs remain under
`city_view.json.profiles[UN id]`.

`citizens.json` supplies `groups`, `figures` and `cities`. Each city row has `shares`, allocated `figures`
and dated provenance. `total` and `counts` are optional and appear for the WorldPop age estimates. The
historic occupation benchmark is urban India from the same Census table. `districts.json` provides the
upstream `catalog`, `industries` and city `districts`, `badge` and `top` fields using the civilian Sixth
Economic Census workplace classification. The derived export carries the same CC BY-NC-SA 4.0 licence
and period as `workplace.json`. There is no military data file. `counties.json` uses the upstream columnar
shape with DataMeet district IDs. Population and density share the 1 March 2026 period and source metadata
from the district lens. Resource items use `cbsa` for unique City View placement. A site may carry `aggregate_mw` only when every counted MW site for that UA shares a period. Each site retains its own period.

See [the City View field mapping](IC-69-fields.md) for data coverage and the omitted fields.
The prepared interim and web file carry a grid fingerprint with grid dimensions, hex radius, projected origin
and a SHA-256 of the owner and water arrays. Reprepare the spatial inputs when this fingerprint changes.
A `ghsl` profile includes the pinned GHSL IDs, intersected state abbreviations, and `cells` with a map index,
fraction of that hex covered and share of the whole footprint (summing to one). Integer cell populations are mid-2026 IndiaCiv estimates using WorldPop weights and the UN total.
The GHSL proxy uses the 2025 reference epoch. GHSL centre IDs are exclusive and newly matched footprints
must have no positive-area overlap with other matches. Ambiguous matches remain point profiles.
`districts` can repeat across UA profiles. Each row uses a canonical DataMeet `id` and carries a share of the
footprint area plus a 2026 WorldPop district population and the fraction of that district's WorldPop mass inside
the footprint. Small DataMeet boundary gaps or overlaps may affect aggregate district area coverage.
Wonder IDs and resource coordinate keys `[type, name, x, y]` refer to existing source features. Resource items
with GEM's exact location flag expose `site_x` and `site_y` for City View joins and marks at the source point.
The City View build refreshes those joins against the current resource file using the prepared footprint rings. A reviewed
waterfront landmark can attach within 1.5 km in the city's state. A `point` profile has one anchor hex with
the UN total, null area fractions and empty memberships and site lists.
Every City View profile also has `citizens` and `industry_plaques`, keyed by the same UN ID for Explorer.
`citizens.age` is null or an IndiaCiv mid-2026 estimate with `counts` (people, keys `0_14`, `15_59`,
`60_plus`), `median_band` (inclusive lower and upper years, with null upper bound for an open band), and
`median` interpolated within that band. The existing `citizens.json` age row also carries `median`.
Its denominator is the full UN city population. The age profile uses the 2026 WorldPop age/sex grid within
the clipped footprint and requires a prepared spatial profile. The optional API preparation uses the
WorldPop 100 m population grid and administrative-unit age shares for the same footprint, identified by
`source: "city_worldpop_age_api"` and `method: "worldpop_api_footprint_to_un"`.
`citizens.workforce` is null or a Jul–Sep 2026 record with the primary state abbreviation `state`,
`employed_all_ages`, `employed_15_plus` and `population_15_plus` in people. The two 15+ headcounts
are null without city age data. `state_urban_wpr_all_ages`, `state_urban_wpr_15_plus` and
`state_urban_unemployment_15_plus` are observed PLFS state benchmarks stored as fractions. The unemployment
denominator is the state urban labour force age 15+ in current weekly status.
`national_urban_unemployment_15_plus` is the observed all-India counterpart from the same release, stored as a fraction.
`industries` lists agriculture, industry and services in that order, with the published `state_urban_share`
of employed residents age 15+ (fraction), an estimated 15+ `employed` count or null, and `icons` summing to 20.
The published fractions may sum slightly above or below 1 due to rounding. The allocation normalizes them.
Both age and workforce records carry `source` (catalog ID), `period`, `estimated: true` and `method`.
Workforce benchmark and share fields retain their state geography and published values.
`industry_plaques` lists up to five `kind: "qualitative"` records with a canonical member `district`,
`icon`, `label`, `source`, `citation`, `url`, `period`, `evidence` and `estimated: false`.
It can be empty. Qualitative plaques provide documented workplace cluster evidence.
Each profile's `economy` contains `gdp` (nominal INR, equal to Gold), `gdp_per_resident` (INR per
UN mid-2026 resident), `period`, `source` IDs and `estimated: true`. `ranks` place GDP, GDP per resident
and the six yields among the original 50 City View profiles, with shared ranks for equal values and null ranks
for missing values. Yield values, per-yield periods and estimate flags are in `cities.json`.
`sector_mix` is null or holds the primary state's advance nominal GSVA shares by sector as fractions
plus the state, release status and source ID. Shares can differ slightly from one due to publisher rounding.
`gateways` contains the nearest major `port`, the nearest scheduled-service `airports` keyed by size (each nullable),
and a `rail` list of mapped named corridors within one cell of the footprint. Gateway rows hold a name,
rounded straight-line map distance from the city centre in `distance_km`, source and period.
Rail rows also carry a `freight` flag and use the distance to the mapped alignment. With no named corridor
nearby, a `main_line: true` row can identify the closest mapped main line in the same search area.
City conditions are optional observations under the same UN ID:

- `air.aqi` is null below 244 valid days or without a matching CPCB city and state. It stores
  `bad_days` (AQI ≥201), `valid_days`, `calendar_days`, `rank` and `covered_cities`. Rank uses the
  exact bad-day fraction, highest first, across all eligible CPCB city/state reporting series, with
  shared ranks for ties. The period is Jan–Oct 2026.
- `air.pm25` is null without a footprint intersecting at least one district estimate. Its `value`
  is in µg/m³, with `footprint_coverage` as a fraction. The estimate weights eligible district
  estimates by intersected area and normalizes by that covered area. It carries `estimated: true`.
  Both air records carry `source` and `period`.
- `hazards` is a list of documented incidents with `id`, `type`, `label`, `start_date`,
  `end_date`, `reported_on` (ISO dates), `districts` (matched canonical member IDs), `source` and
  `url`. Date bounds may be null. An empty list means no documented match in the selected reports.
- `housing` is null outside covered RBI markets. It stores the original `market` label, the `index`
  (decimal text preserving published precision), `yoy_pct` (published change in percentage points
  or null), `period`, `provisional`, `source` and `url`. The base year appears in the source entry.
  Convert the index text to a number
  for Explorer sorting and scatter plots. Market geographies are those of the publisher.

For the six WorldPop places, `states.json` includes `age_source: "worldpop_age"`. Only `age_0_14`,
`age_60` (percentages) and `median_age` (years) use that source. Age lenses may include a `source_line`
string for the legend when the values use multiple sources.
The optional Air & weather group has city-only `city_bad_air` values (fractions of valid days), district
`district_pm25` estimates (µg/m³, marked `estimated: true`), and `monsoon_2026` values by IMD subdivision.
PM₂.₅ uses the same district sample and small-district area weighting as population density.
`monsoon_band` stores ordinal values from −2 (large deficit) to 2 (large excess), with 0 for near-normal rainfall.
The lenses carry `source_line` for the period and `share_credit` for attribution on exported images.

`lenses.json.places.counties` provides district inputs to the Explorer build, keyed by the canonical district `geoid` in
`world.json.counties`. Each record has `state` (the current state/UT abbreviation, or null),
`area_km2` (area calculated from its DataMeet rings in the equal-area projection),
`population` (the district's census count scaled by its state's projected change to 1 March 2026),
`density` (that population per mapped km²), and `center` (a projected reference point to
frame districts without a hex). `district_pm25` is present when the district air-quality input is
available and may be null. These are district-level values before blending neighbouring districts
onto a hex. `monsoon_2026` is the derived rainfall band of the IMD subdivision at the district's
reference point, or null. Each district has `sites` with UN city IDs, wonder IDs, and resource item
indices, joined using the original city and wonder points and the best available resource points.
`places.district_fallbacks` maps land cell indices without a district to the nearest mapped district
index in the cell's state or UT for panel navigation. These links leave geographic ownership and
lens samples intact. The city AQI lens carries `city_values`, a map of UN agglomeration ID to the fraction
of poor-or-worse AQI days. An unlisted city has no qualifying observation.

`protected_ramsar.json` and `protected_land.json` contain a `vintage` and `sites` list. Each site
has a stable `id`, `name`, `designation`, source reference and optional `wonder` ID of an
associated existing marker. `x`, `y` and `cell` are null when no verified location is available.
`cells` is null for a point or unlocated site. A polygon lists hexes with at least 30% geometric
coverage, including an empty list for extents below the threshold. The renderer uses a point
marker for a located entry with zero qualifying hexes. A Ramsar polygon also has simplified map-km
`rings`, drawn with the even–odd fill rule at close zoom. `area_ha` records official designated area
in hectares. Ramsar sites use it to size point markers. Other designations use `marker_radius`
in CSS pixels for fallback dots. `authority_source`, `authority`, `period`, `status` and
`estimated: false` describe the authority facts. Spatial-only Ramsar overlays inherit these
fields at render time from the matching RSIS record. OSM polygons are eligible only when their
projected area is within ±25% of the authority figure. Discarded candidates are recorded in the
local interim audit and contribute no area.

The RSIS-derived file is CC BY 4.0. The ODbL file contains OSM-derived extents and locations,
including any fallback geometry linked to an RSIS point by `ramsar_id`. It also contains
`shares.states[abbr]` and `shares.counties[geoid]` for the Explorer. These fractions divide the
intersection of the union of available extents with the DataMeet unit by its projected area.
Point-only locations contribute no area. Null means no eligible coverage calculation. Empty site
lists signal a build without the optional inputs.

`advisor_tables.json` uses the upstream district table's `columns`, `fields` and `rows` format
for each level. The first column identifies rows by state abbreviation, UN city ID or Census
district code. Optional `provenance` is keyed by row ID and then field key. It overrides field
defaults for observation periods, sources and estimates. The `advisor_tables` build reads state
metrics from their lenses, resource columns from the type catalog, and air and housing observations
from City View profiles. Site counts describe the served inventories.
The documented hazards column cites the matched reports and their incident or report dates.
Rail and highway counts use unique rendered links with at least one endpoint in the place.
An urban agglomeration needs a modelled footprint for these counts. Resource and wonder
membership within those footprints uses the spatial joins in the City View profile.
Cargo is displayed in Commerce on the reporting port authority's row, using its own
period, source and publisher status. Geographic counts of map markers carry no cargo.
City and state population records and district population and density records may carry
`provenance[field]` with a period label, source ID or IDs, and optional IndiaCiv estimate
flag. The build carries the growth and health periods from their lens definitions into the tables.

The US contract below is kept as the reference for the files India does not build yet.
Per-cell arrays have length `grid.cols * grid.rows`, with index `row * cols + col` (pointy-top, odd-r layout, see
`pipeline/core/hexgrid.py` ⇄ `web/js/hex.js`). `null` always means "no data". Never write `0` as a stand-in for "unknown".

### India transport (`infrastructure.json`, version 2)

Port tooltip fields `tons`, `domestic`, and `foreign` are absolute metric tonnes.
`period` provides the full reporting label. `overseas_direction` holds the separately
dated loaded and unloaded shares. Explorer reads shares and provenance from
`historical_cargo_split` for the non-major ports, outside the major-port rank cohort.
Airport `id` uses the IATA code, `ourairports_id` retains the source identity,
and `hub` and `period` carry the size class and pinned inventory date.

The build writes JSON null when transport inputs are unavailable. Otherwise the document has
`version`, `sources`, `vintage`, `rail`, `rail_corridors`, `main_lines`, `rail_facilities`, `roads`, `ports`, `airports`, `freight`,
`osm_license`, `lifecycle_audit` and `trade`.

An Almanac source can supply `license_url` and `download_path` for a served `data/*.json` file,
plus an optional `download_label`. The transport JSON embeds the OSM attribution, licence URI and
licence scope. The lifecycle audit records the excluded way count and any mistakenly admitted way IDs.

- `rail` rows are `[a, b, tier, ref?, name?, network?]`, with the checked trunk corridors at tier 0, other main lines
  at tier 1 and secondary tracks at tier 2. `roads` rows are `[a, b, class, ref, name, network]`, with expressways
  at class 0, Golden Quadrilateral routes at class 1 and other national highways at class 2.
  Missing way tags are null. Rail links with no tags may omit all three trailing fields. Both arrays contain unique adjacent, ascending cell pairs. The
  highest class wins when tracks or carriageways share a link. Links follow sampled geometry and
  end at foreign cells. Samples within the Survey of India outline whose hex is coded as
  neighbouring land can snap one cell inward. Short water crossings may join adjacent Indian land tiles.
- `rail_facilities` records the EDFC and WDFC link subsets and whether the operating Chenab bridge is present.
  It also records which corridors reach every checkpoint on one component of the live OSM node topology.
  The checker tests continuity at the national main-line zoom and flags splits in the finer source topology.
  It uses the dedicated freight subsets to distinguish them from parallel conventional lines.
- `rail_corridors` maps each resolved name to the ordered cell indices of its route. The same paths
  determine the national trunk layer and the City View gateway distances.
- `main_lines` holds `[a, b, name]` links from operating main lines for the City View fallback, with
  null names where the source has none. Airport rows carry the OurAirports `scheduled_service` flag and tagged municipality as `city`.
  Sites use a DataMeet state or UT point join at the facility, with the placement cell as a coastal fallback. Major and featured port city labels use the
  named locality of the facility, keyed by stable port ID.
- Site rows keep unique `id`, `name`, projected `x`/`y` and an Indian land `cell`. A nearby land cell
  can represent a coastal site. The renderer may shift its icon to clear a city or other sites.
- A port adds `category`, `geometry_source_id`, `rank`, `tier`, and `cargo`. Cargo is null or holds
  `domestic` and `foreign` (coastal and overseas fractions of that authority’s cargo),
  `share` (fraction of cargo across the 12 authorities), `label`, inclusive ISO `period_start` and
  `period_end`, `status`, `source_id` and `estimated` (IndiaCiv estimate flag).
  The top-level `port_split` uses the same metadata for the combined coastal and overseas split.
  Kolkata’s authority includes both the Kolkata and Haldia docks.
  Ranks compare major port authorities over the same period. Cargo tiers 0–2 use 100 and 25
  million metric tonne cutoffs. Tier 3 has no cargo value or rank. Selected non-major ports
  carry `featured: true` so their markers appear sooner.
- Airports carry `iata` (nullable) and `size` (large, medium or small) from OurAirports. The map
  includes large airports and medium or small airports with scheduled service.
- `freight` has the same period fields, its `source_id`, the national `total`, the `unit`
  (million metric tonnes), and `rows` of [railway code, name, originating freight loaded].

Rail and road geometry and OSM port positions are OpenStreetMap data under the ODbL 1.0.
Independent port statistics, freight statistics and airport locations have their own Sources entries.
**Layered Indian terrain.** Builds with the `india_layered_terrain` interim add:

* `base[i]` is the id in `tables.base` (0 unclassified land, 1 grassland, 2 plains, 3 desert, 4 tundra,
  5 snow/ice, 6 ocean, 7 coast, 8 lake). Grassland is a moist climate base. It can carry forest or crops.
* `relief[i]` remains the id in `tables.relief`. The detailed ETOPO land sample uses elevation spread and
  median local slope, so a high but locally even plateau can be flat. Indian cells with insufficient land
  sampling are drawn flat. `water` remains the authority for land and water ownership.
* `features[i]` is an array of sorted unique ids from `tables.features`. Multiple features can share a hex.
  `cover` and `pct` still carry WorldCover dominance and the independent land cover percentages.
* `featureFootprints` contains `{id, rings}` records. Each ring is a flat `[x,y,...]` sequence in map km,
  with the exterior first and optional holes. `featureSites` contains `{id, name, point: [x,y]}` or
  `{id, name, line: [x,y,...]}` records for located features. These geometries apply independently of the
  centre hex and can depict reef and nearshore features in mixed land and sea hexes.
* Base and feature table rows have `id`, `key`, `name`, `color`, `rule`, and `example`. The browser also
  accepts legacy files without these tables and fields.

## Pipeline conventions

* **Sources** (`pipeline/sources/*.py`) are discovered automatically: any `Source` subclass with `info = SourceInfo(...)`.
  `process()` returns a dict. It may include `"vintage"` (str) and `"_files"` (list of raw-file paths relative to
  `data/raw/<id>/` that this processing actually used; the Almanac cites only those).
* **Builders** (`pipeline/build/*.py`) are discovered automatically: a module with `REQUIRES`, `PRODUCES` and `build()`.
  They run in dependency order. Interims made by builders start with `_`. Helpers without `build()` (e.g. `yields.py`) are fine.
* The **`_world` interim** (made by `world`) holds: `grid`, `projection` (`MapProjection` kwargs), `owner`, `county`,
  `county_samples` (7 county indices per US cell, `[]` for other cells; sample 0 = centre), `states` (fips list, same order as
  world.json states), `counties` (geoid list), `water`, `cover`, `pct` (same as world.json). Builders that need to know whether a
  cell is land must use `owner[cell] >= 0`.
* Python is **standard library only**. Downloads go through `Source.download()` (or `Source.download_prefix()` for the
  leading block of a big sorted file), which cache them and record provenance in `data/raw/<id>/manifest.json`;
  `Source.discard(rel_path)` forgets a cached file that turned out to be bad. All three wrap `core.fetch`.
* Under `--offline` (`core.fetch.OFFLINE`, `Source.offline`) sources skip discovery requests and use the newest complete
  cached data; a download of a file that is not cached raises `OfflineError`.
* **Builder checks.** Any module in `pipeline/build/` may define `check(web_dir: Path) -> list[(level, message)]`, level one
  of `PASS`, `NOTE`, `WARN`, `FAIL`. `pipeline check` discovers and runs them after its own checks (section "builder
  checks", each line prefixed with the module name), so a new builder never edits `pipeline/check.py`. Rules: read only
  `web_dir` (tests point it at a tiny synthetic dataset); report a **missing output as a NOTE** (never WARN/FAIL: the unit
  tests run every discovered check against a dataset without your files); a check that raises is reported as a FAIL.
  Validate your file's shape against this document (keys, types, null rules, cell ranges against world.json) and add a
  short data-quality summary (counts, coverage) as PASS/NOTE lines.
* **ACS interims.** `acs_1yr` keeps every estimate line (`<TABLE>_<line>`, e.g. `C24010_007`) of its tables for the nation
  (`geos["0100000US"]`), the states (`geos["0400000USss"]`) and every CBSA (`cbsa["<5-digit code>"]`): `b01003 c24030 b19025
  b19013 b25064 b25077 b23025` plus, for citizens, `c24010` (occupation; male lines 002-037, female = male + 36), `b01001`
  (age; male 003-025, female = male + 24), `b01002` (median age), `c08301` (commute), `c15003` (education 25+) and `b05002`
  (place of birth). Sexes are **not** summed in the interim: builders add male + female lines. Census leaves some small
  CBSAs out of a table entirely (C24010 has 520 of 536 CBSAs, C08301 525, B05002 535): the CBSA's record then simply lacks
  those keys (treat as null). `acs_5yr` (`geos["0500000USsscc"]`, counties) adds `b21001` (veterans: `B21001_001` civilian
  population 18+, `_002` veterans) and `b23025` (`B23025_001` population 16+, `_006` in the armed forces, by residence).

## world.json

The India build adds hydrography in map kilometres:

- `river_edges` is a list of unique undirected shared edges. Each record has `corners` (two canonical vertex IDs
  in ascending order), `cells` (the one or two adjacent cell indices), `pts` (`[x0,y0,x1,y1]`, in corner ID order),
  `downstream` (the corner ID the primary flow enters), `rank` (cartographic width rank, higher means wider), `delta` (whether the
  edge belongs to a declared distributary), and `names` (the nonempty labels using that edge, possibly none).
  Vertex IDs are assigned by visiting cells in index order and visiting each cell's six vertices clockwise from top.
  Coincident vertices share their first assigned ID. Distributary order is an ordinal styling choice.
- `river_junctions` identifies single-corner joins in the primary network. Each entry records `river`, `parent`,
  the shared `vertex`, the branch-side `neighbor`, and whether the join is at the branch's `inlet` or `outlet` (`at`).
  The checker projects the independent source controls in `pipeline/india/open_rivers.py` and requires each
  junction within two hex radii (36 km) of its control. Primary edges must form a forest.
- `river_mask` has one integer per cell. Bits 0 through 5 are NE, E, SE, SW, W and NW. Adjacent cells
  share the same river edge, each with the bit for its own side set. A nonzero mask identifies a riverside tile.
- `lakes` records contain `name`, `point` (a representative location), `cell` (its containing hex), `polygons`
  (polygon → rings → points, outer ring first), and `tiles` (hexes with more than half their area covered).
  Majority tiles use the lake base class with administrative ownership intact. A named feature without a majority
  tile gets a marker. A location-only lake has an empty `polygons` array.
- `rivers` retains the original Natural Earth linework for the optional legacy rendering.

```jsonc
{
  "version": 2,
  "grid": {"radius": 25, "cols": 117, "rows": 90},
  "width": 5002.0, "height": 3301.7, "margin": 200,
  "owner":  [int],   // -1 water, -2 foreign land (Canada, Mexico, the Caribbean), >=0 index into states
  "county": [int],   // index into counties, -1 if none
  "elev":   [int],   // metres. Land: mean of land samples only. Water: mean of the hex's ETOPO samples below sea
                     // level (its depth, <= 0); lakes: min(mean, 0); -4000 where ETOPO has no samples
  "elev_max": [int], // optional: metres, the highest land sample in the hex (0 for water); the art uses it for snow
  "water":  [int],   // 0 land, 1 ocean, 2 coast (next to land or shallower than 200 m), 3 lake
  "relief": [int],   // 0 flat, 1 hills, 2 mountains, 3 peaks (alpine). 0 for water. A hex whose lower 60% of land
                     // samples is flat lowland (spread < 60 m, under 400 m) is eased one class (valley floors)
  "cover":  [int],   // land-cover id (see tables.cover). 0 = unknown/none (water, foreign land outside NLCD)
  "pct": {           // share of the cell's land samples, 0..100 ints (US cells; 0 elsewhere)
    "forest": [int], "crop": [int], "pasture": [int], "grass": [int], "shrub": [int],
    "wetland": [int], "developed": [int]
  },
  "tables": {
    "water":  [{"id": 0, "name": "Land"}, {"id": 1, "name": "Ocean", "color": "#1b4266", "rule": "..."}, ...],
    "relief": [{"id": 0, "name": "Flat", "rule": "..."}, ...],
    "cover":  [{"id": 1, "key": "forest_deciduous", "name": "Deciduous forest", "color": "#4f7a35", "nlcd": [41], "rule": "..."}, ...]
  },
  "states":   [{"fips": "01", "abbr": "AL", "name": "Alabama"}],
  "counties": [{"geoid": "01001", "name": "Autauga County"}],
  "rivers":   [{"name": "Mississippi", "rank": 1, "pts": [x0, y0, x1, y1, ...]}]   // clipped to the map; no lake centerlines
}
```

Cover ids (fixed): 0 none · 1 forest_deciduous · 2 forest_evergreen · 3 forest_mixed · 4 scrub (scrub & desert) ·
5 grassland · 6 pasture · 7 cropland · 8 wetland · 9 urban · 10 barren · 11 ice.
Dominant cover per cell = the largest group among its land samples. A cell is **urban** if NLCD 22+23+24 (developed
low/med/high) ≥ 30% of land samples. NLCD 21 (developed open space) counts toward grassland.

## cities.json

A list sorted by population, descending:

```jsonc
{
  "id": "35620",                  // 5-digit CBSA code
  "name": "New York", "full": "New York-Newark-Jersey City, NY-NJ Metro Area",
  "states": ["NY", "NJ"], "metro": true, "capital": false,   // capital: the national capital (Washington)
  "x": 3912.1, "y": 1100.4,       // principal city's true position (map km)
  "cell": 4567,                   // land cell (owner >= 0), unique per city where possible; banners anchor here
  "population": 20112448, "employed": 9876543,
  "yields": {"food": 15523, "production": 1059252, "gold": 2.1e12, "science": 1470849, "culture": 252479},  // any may be null
  "jobs": {"agriculture": 123, "...": null},
  "median_income": 98000, "median_rent": 1700, "home_value": 650000, "unemployment": 0.0578, "rent_burden": 0.227,
  "gdp": 2.1e12, "gdp_year": 2024,                       // BEA, current dollars; null if unavailable
  "gdp_by_industry": {"manufacturing": 1.2e11, "...": null},  // optional. BEA-withheld (D) county values are
                       // recovered from parent/sibling lines, else the parent's remainder is split in national proportions
  "gdp_undisclosed": null,          // optional: total minus the industries above when some stay null (usd), else null
  "gdp_estimated": ["utilities"],   // optional: industries whose value includes an apportioned county figure, or null
  "growth": 0.0174, "growth_years": [2021, 2025],         // population change, see below
  "counties": ["34003", "36005", "..."],                  // member county GEOIDs (OMB delineation, list 1), sorted
  "footprint": [3721, 3722, 3845, "..."],                 // US land cells of the metro, sorted (see below)
  "pop_series": {"2020": 20081935, "2021": 19708911, "...": null, "2025": 20112448},  // PEP, or null
  "ranks": {"population": 1, "gdp": 1, "gdp_per_capita": 12, "growth": 301,
            "food": 1, "production": 1, "gold": 1, "science": 1, "culture": 1},     // 1 = top; null if value null
  "peers": ["31080", "16980", "..."]                      // ids of the 5 cities closest in population
}
```

* **`footprint`**: the hexes that make up the metro on the map (City view). A US land cell (`owner >= 0`) belongs to
  a city when at least 4 of its 7 county samples (`_world.county_samples`) fall in the CBSA's member counties. The
  city's own `cell` is always included, even when it fails that test (a small metro, or a banner cell nudged away), so
  `footprint` is never empty. A cell is in at most one footprint by the majority rule, but a city's own `cell` may also
  sit in a bigger neighbour's footprint.
* **`counties`**: the CBSA's member counties from the OMB delineation (`cbsa_delineation`, list 1), the same list GDP is
  summed over. Some may be outside the map's county list (none are, today).
* **`pop_series`**: `{year (string): population}` for every year of the population-estimates vintage (2020 … latest,
  `pep_population`), on today's metro borders. A year without an estimate is `null`; the whole field is `null` when the
  CBSA is not in the estimates or its county list there differs from the delineation (the same guard as `growth`).
  These are PEP numbers, so the latest year will not equal the ACS `population`.
* **`ranks`**: rank among all cities in cities.json (metro and micro), 1 = highest, for `population`, `gdp`,
  `gdp_per_capita` (`gdp / population`), `growth` (1 = fastest growing) and each yield key. `null` where the value is
  null; non-null ranks are a permutation of 1..N, ties broken by population.
* **`peers`**: the 5 other cities whose population is closest to this one's, by ratio (|log(p / q)|), nearest first.

**Growth** (cities, states and `nation.nation`): `growth = population(end) / population(2021) - 1`, a fraction
(0.0174 = +1.74%), over `growth_years = [2021, end]`, where `end` equals nation.json `year` (the ACS year the panels
show). Both populations come from one vintage of the Census population estimates (PEP, source `pep_population`), which
estimates every year on the current (July 2023) metro delineations and with the same methods. So a city's growth is
like for like: no county added or dropped between the two years (e.g. Chicago without Kenosha County in both years,
Connecticut's planning regions back to 2020, renamed areas such as Kiryas Joel-Poughkeepsie-Newburgh), and no mix of
estimate vintages. `population` itself stays the ACS 1-year total; the two are different estimates and will not
divide exactly. The same `growth_years` is used in every file; it is null only when no estimates were fetched.
`growth` is **null** (never a guess) when:

* |growth| > 25% (a sanity cap; no area comes near it);
* for cities: the CBSA is not in the PEP metro file, or its member counties there differ from the OMB delineation
  the rest of the map uses (`cbsa_delineation`). See `pipeline/build/growth.py`.

Currently every city, every state and the nation have a rate. `check` fails if a state or the nation has none while
`growth_years` is set, if rows disagree on `growth_years`, or if it does not end at nation.json `year`.

## states.json

A list in the same order as world.json `states`, each with the same economic fields as a city (`population`, `employed`,
`yields`, `jobs`, medians, `unemployment`, `rent_burden`, `gdp`, …) plus `fips`, `abbr`, `name`,
`growth`/`growth_years` (as above), `ranks: {yieldKey: 1..49}` (1 = largest), and `label: {x, y, angle, size}` (null
for a state without hexes, i.e. DC). `label` is an optional suggested anchor for the big state name: `angle` in degrees
clockwise, `size` a suggested font height in map km, clamped to 14..110 km. The 14 km minimum can exceed very small
states (RI, DE), so the frontend should still clamp or hide those labels. The frontend may compute its own.

Also, per state:

```jsonc
"land": {"forest": 0.312, "crop": 0.204, "pasture": 0.051, "grass": 0.12, "shrub": 0.08, "wetland": 0.06,
         "developed": 0.044},   // or null (no hexes, i.e. DC)
"energy": {"unit": "MW", "total": 30530,
           "by_type": {"nuclear": 3937, "hydro": 0, "coal_plant": 0, "gas_plant": 5100, "geothermal": 0,
                       "pumped_storage": 0, "wind": 0, "solar": 7250, "battery": 4200},
           "sites": {"nuclear": 1, "hydro": 0, "...": 0},
           "note": "Only the mapped sites in resources.json ... not the state's total capacity."}
```

* **`land`**: land-cover shares as **0..1 fractions**: the mean of world.json `pct` over the state's cells
  (`owner == index`) that have land-cover samples (`cover > 0`). Keys are world.json `pct` keys. `null` for a state
  without such cells (DC).
* **`energy`**: MW summed from resources.json items whose `cell` is in the state, for every resource type with unit
  `MW` (all such types appear; `0` means no mapped site, a real zero for the map, not for the state). **It only counts
  the mapped sites above each type's threshold** (e.g. gas plants ≥ 1,500 MW, wind ≥ 500 MW per hex; see the types'
  `description`), so it is **not** the state's total generating capacity; `note` says so in plain words for the UI.
  Items count in their resources.json `state`; a site EIA files once per state (Hoover Dam, AZ + NV) is one item
  and counts in the state of its larger part. `sites` = number of mapped sites per type.
  `energy` is `null` if resources.json was not built.

## nation.json

```jsonc
{
  "vintage": "ACS 2025 1-year", "year": 2025,
  "gdp_vintage": "BEA CAGDP2, 2024",
  "nation": { /* same economic shape as a city */ },
  "yields": [{"key": "food", "icon": "y-food", "emoji": "🌾", "label": "Food", "color": "#7fbf3f",
              "unit": "workers|usd", "description": "..."}],
  "industries": {"agriculture": "Agriculture, forestry, fishing & hunting"}
}
```

### India trade (in infrastructure.json v2)

The optional `trade` object reuses the infrastructure and world grids.

- `corridors` lists the two operating Dedicated Freight Corridors by key in `rail_corridors`.
- `backbone` is an unweighted list of adjacent sea-cell indices for the schematic shared coastal lane.
- `branches` holds one `{port_id, tonnes, cells}` row per major port authority. Each route runs from
  a connected sea cell near the port (the Hooghly mouth for Kolkata and Haldia) to a backbone cell.
  `port_id` joins to `ports[].id`. `tonnes` measures domestic coastal cargo handled by that authority.
- `period_start` and `period_end` give ISO dates. `label` and `status` give the display period and estimate status.
  `source_id` joins to the October 2026 MoPSW report in `sources.json`.

Branch and backbone paths are drawing geometry. A branch carries a single port’s throughput, and
port-to-port flows have no fields in this object. Explorer assigns mapped gateways by state tiles or
city footprint tiles, allowing one adjacent tile for city rail matches as in City View.

### India state metrics

For the Explorer, join `states.json[].metrics` by `states.json[].abbr` and use the metric keys
as the matching `lenses.json.lenses[].id`. The national comparator is
`nation.json.metrics[metric_id]`. A record has `value` and the exact `source` ID in
`sources.json`. An absent key means unavailable. A numeric zero is valid.

Lens definitions provide `name`, `group`, `unit`, `format`, optional `precision`,
`higher_is`, `description`, `source_line`, and `period` with ISO `period_start` and
`period_end`. An effective-date schedule has a null end. PLFS variants use the keys with
`_rural` and `_urban` suffixes and combined values use the unsuffixed keys. Percentages
are fractions. Monetary amounts are nominal INR and electricity is kWh per projected resident.

`gsdp_pc` records have `estimated` and `base_fy_start`. The latter is provenance for the
calculation, useful for debugging and ingest. The displayed period comes from the metric
definition. The national comparison uses nominal GDP. For electricity, an optional `coverage`
string identifies the Jammu & Kashmir–Ladakh reporting area. Ladakh has no standalone row.
In the per-hex lens, `state_details` maps the owning state's array index to any estimate flag
or coverage note. Water, foreign cells and unavailable states have null hex values.

## lenses.json

The India build also emits `lens_catalog.json` with the same `vintage`, `groups` and
lens metadata, retaining only density's values and omitting the top-level district
and disaster records. The browser loads `lenses.json` at startup.

India now writes one value per cell in the upstream dense array format. Missing
cells are null. The pipeline still accepts legacy
`{"runs":[gap,length,value,...]}` grids from older local builds.

Produced by `pipeline/build/lenses.py`.

```jsonc
{
  "vintage": "ACS 2024 5-year",
  "groups": [{"id": "people", "name": "People"}, {"id": "prosperity", "name": "Prosperity"}, {"id": "knowledge", "name": "Knowledge"},
             {"id": "life", "name": "Daily life"}, {"id": "land", "name": "Land"}],
  "lenses": [{
    "id": "density", "group": "people", "name": "Population", "icon": "l-people", "emoji": "👥",
    "unit": "people / km²", "format": "int|usd|pct|float|minutes|years",   // pct values are 0..1 fractions
    "scale": "log|linear", "domain": [1, 2000],   // 2nd-98th percentile of the hex values, computed at build time "ramp": ["#..", "..."], "higher_is": "good|bad|neutral",
    "source": "acs_5yr", "description": "...",
    "values": [number|null],       // per cell; null on non-US cells
    "note": "..."                  // optional: a short caveat the legend always shows (e.g. what a count does not measure)
  }]
}
```

**Categorical lenses** (`"format": "category"`): each value is an integer index into `categories` (or null);
`"categories": [{"id": "catholic", "name": "Catholic", "color": "#…", "description"?: "…"}]` (≥ 2), `ramp` = the
categories' colours in the same order, `"scale": "linear"`, `"domain": [0, n - 1]` (so the ramp stops land exactly on the
colours). The legend shows swatches (click one to show only it) and tooltips show the category name. `check` enforces all
of this.

**County lenses from the Religion Census, CDC PLACES, FEMA and ACS veterans** (ids are a contract with the frontend, which may link to them):

| id | group | format | values | note (legend caveat) |
|---|---|---|---|---|
| `faith` | `faith` (group "Faith") | `float`, unit `adherents per 100 residents`, domain clamped to `[0, 100]` | 2020 U.S. Religion Census adherents ÷ 2020 population × 100 (compute it; do not trust the RATE columns), per county spread to hexes like the other county lenses. Can exceed 100 (adherents are counted where the congregation is) | required: counts congregations' adherents where they worship, not residents' beliefs; about half of Americans are counted; some traditions (notably historically Black churches) are under-reported; 2020 data |
| `faith_tradition` | `faith` | `category`: `evangelical`, `mainline`, `black_protestant`, `catholic`, `orthodox`, `lds`, `other` (Latter-day Saints split out of ARDA's "Other") | the county's largest tradition by adherents; null where no adherents were reported | same caveat |
| `amenities` | `life` | `float`, unit `index`, `higher_is: good` | 100 − 10 × mean z-score of the CDC PLACES age-adjusted shares of frequent mental distress, depression, fair/poor health and no leisure-time activity (state the exact recipe in `description`); null where PLACES has no BRFSS core data (all of KY and PA in the 2025 release): never imputed | required: model-based estimates, not a happiness survey |
| `disasters` | `hazards` (group "Hazards") | `int`, unit `declarations` | distinct FEMA major-disaster (DR) declarations naming the county since 2000 (Biological/COVID excluded; deduplicated by disaster number) | required: a declaration is an administrative act, not a measure of damage |
| `veterans` | `people` | `pct` (0..1) | ACS 5-year `B21001_002 / B21001_001` (veterans among civilian adults 18+) | |

Connecticut: the map's counties are the 2022 planning regions (`09110`…`09190`). Sources on the 8 legacy counties (USRC,
FEMA) need an overlap crosswalk, or CT stays null and the lens `note`/`description` says so.

**As built** (`pipeline/build/lenses.py` `community_lenses`, appended after the land lenses so the
existing lenses keep their array positions; every county value is spread to hexes with the same population weights as
the other county lenses, and the county formulas are shared with counties.json):

* `faith` (source `usrc_2020`): county `adherents / POP2020 × 100` (1 decimal); hex = population-weighted mean;
  `domain` fixed `[0, 100]` (no percentile note); counties can exceed 100 (max ≈ 450). **CT is null** (USRC's 8 old
  counties are not apportioned: no town-level adherent counts exist), as are the two counties with a blank total.
* `faith_tradition` (`usrc_2020`): categories in this order `evangelical, mainline, black_protestant, catholic, orthodox,
  lds, other` (each `{id, name, color, description}`; `other` = ARDA "Other" minus Latter-day Saints). Hex value = the
  tradition with the most adherents after summing each county's adherents × the share of the county in the hex; null
  where none were reported. Icon `l-faith-tradition`, name "Largest tradition".
* `amenities` (`cdc_places`), **named "Wellbeing"** (the id stays `amenities` for URLs and icons; the description says
  it stands in for the strategy-game Amenities): `100 − 10 × mean(z)` over `mhlth, depression, ghlth, lpa` (`_adjprev`), z against the
  unweighted mean ± SD of all mapped counties that have all four (the values are printed in `description`); unit
  `index (100 = average county)`, 1 decimal. Null for KY, PA (and Loving County, TX). PLACES already uses CT planning
  regions.
* `disasters` (`fema_declarations`): hex = population-weighted mean of the county counts **rounded to a whole number**
  (`format: int`); no nulls (0 = no declaration, a real zero). CT regions count a disaster declared for any old county
  they overlap (Census town crosswalk `ct_cou_to_cousub_crosswalk.xlsx`).
* `veterans` (`acs_5yr`): pct, 4 decimals; no `note`.
* Icons (fall back to the emoji until `web/js/icons.js` has them): `l-faith` 🕍, `l-faith-tradition` ⛪, `l-amenities` 🎭,
  `l-disasters` 🌪️, `l-veterans` 🎖️. Groups `faith` and `hazards` sit between `life` and `land`.
* `lenses.py` defines `check(web_dir)` (presence, required notes, faith domain, a short coverage summary).

## resources.json

India resource types can include a display `threshold` and default `period`. Items carry their own
`source` and `period`. A `byproducts` list can identify silver at a lead-zinc mine without adding
a second marker to the inventory. Battery project counts use verified operating sites. Field counts
use the GEM operating snapshot and keep mixed or unspecified oil and gas fields in `oil_gas`.

India uses operating sites from 2026 snapshots and representative growing areas. Numeric site values are rated
generating capacity (MW), mine capacity (million tonnes per year), or 1 for each operating oil and gas field
(`oil_gas`), which is additive.
Each item uses its tile's state code and has `cbsa: null`. A site needs coordinates more precise than a
country-level point and must land on an Indian hex or within its type's snap distance.

India's `types[].resource_class` identifies the Bonus, Luxury or Strategic group. The existing `category`
continues to identify energy, mineral or agricultural markers for consumers. Crop, diamond, bauxite, limestone and fish
markers carry an item-level `source` (catalogue ID) and `period`. Representative crop placements also carry
`estimated: true`. These entries have a null `value` and contribute only to the marker count.

Field-crop icons use cited growing districts and select a non-city hex with at least 10% cropland.
Plantation markers use documented growing areas and prefer cropland, with mixed tree cover as a fallback.
The Velur and Puliyannur farmer clusters constrain Thrissur's coconut, pepper and ginger markers,
which can share a tile because the crops are intercropped. A hex with 100% forest is ineligible for any crop marker.
The Darjeeling, Nilgiris and Chikkamagaluru markers apply minimum mean elevations
to select upland hexes. A fishing harbour must land on a same-state land hex adjacent to the sea, with a
maximum snap distance of 1.25 hex radii from the site to the tile centre.

```jsonc
{
  "types": [{"id": "nuclear", "name": "Nuclear plant", "category": "energy|mineral|agri",
             "emoji": "☢️", "icon": "r-nuclear", "color": "#e8d44d",
             "unit": "MW", "description": "...", "source": "eia_860m"}],
  "items": [{"type": "nuclear", "name": "Palo Verde", "x": 1234.5, "y": 2345.6, "cell": 4321,
             "value": 3937, "detail": "3 units, Arizona Public Service"}]
}
```

Each item also has `"state": "AZ"` (the state the source files the site under, e.g. EIA's plant state; for oil/gas
play hexes, or when that state is not on the map, the state owning its `cell`; a border site such as Vogtle, GA, can sit
in a hex another state owns) and `"cbsa": "38060"` (the id of the
cities.json city whose member counties contain the county at the cell's centre, `world.county[cell]`, or `null`).

Items are the meaningful sites only (thresholds are documented in each type's `description`). The frontend draws at most
one icon per cell at low zoom (the highest-ranked type wins) and may show more when zoomed in.

```jsonc
"summary": {
  "note": "Totals of the mapped sites only (each type's threshold applies) ...",
  "national": {"nuclear": {"count": 54, "value": 96952, "unit": "MW"}, "oil": {"count": 120, "value": null, "unit": "km² play area"}},
  "states":   {"AZ": {"nuclear": {"count": 1, "value": 3937, "unit": "MW"}, "...": {}}}   // only types present
}
```

`summary.national` has every type in `types`; `summary.states` has, per state abbr with at least one item, the types
present there. `value` is the sum of recorded values, or `null` when every value is missing or the type
is non-additive.

### _crop_production interim

Read `load_interim("_crop_production")` for the Food input. Its `version` is 1 and its
`grid` and `projection` match `_world`. `crops` maps each supported commodity slug (`rice`, `wheat`, `millets`,
`sugarcane`, `cotton`, `jute`) to a sparse object whose keys are zero-based flat hex indices as JSON strings
and whose values are estimated metric tonnes for the full period. Missing entries are unknown, including when
`crops` is empty. Crop production alone does not measure edible
output. Consumers should select the commodities appropriate to their yield model.

The header includes the `period` Crop year 2025-26 (1 Jul 2025 – 30 Jun 2026), `unit: "t"`, and
`estimated: true`. A populated file requires a catalogue `source` and an allocation `method`. The current
build emits `crops: {}`, `source: null` and `method: null`. PIB release 2265965 supplies national totals.
The district resource on data.gov.in is published under GODL–India (resource UUID
`35be999b-0208-4354-b557-f6ca9a5355de`, catalogue revision dated 16 Oct 2024).
Its public download was unavailable, and neither national totals nor crop marker counts establish tile tonnage.

## counties.json

One row per county on the map (the lower 48 + DC, world.json `counties` order), **column-oriented**:

```jsonc
{
  "vintage": "ACS 2024 5-year",
  "fields": [{"key": "population", "label": "Population", "format": "int", "unit": "people", "higher_is": "neutral",
              "source": "acs_5yr", "description": "..."}],    // one entry per column, in column order
  "columns": ["geoid", "name", "state", "population", "land_km2", "density", "income", "home_value", "poverty",
              "median_age", "foreign_born", "bachelors", "broadband", "commute", "homeownership", "uninsured",
              "forest", "crop", "pasture", "developed", "cbsa", "cell"],
  "rows": [["01001", "Autauga County", "AL", 59285, 1539.6, 38.5, 69841, 197900, 0.11, 39.1, ...,  "33860"]]
}
```

`rows[i][j]` is column `columns[j]` of county i; `fields` describes each column (`fields[j].key == columns[j]`).
`format` is one of the lens formats plus `text` (geoid, name, state, cbsa) and `km2`; as in lenses, `pct` values are
**0..1 fractions**. County metrics are computed exactly as the matching lenses (lens id `age` → `median_age`, `home` →
`home_value`). `density` = ACS population ÷ Gazetteer land area (people / km²). Land shares (`forest`, `crop`,
`pasture`, `developed`, same groupings as world.json `pct`) are the mean of the hex shares over the county's sample
points (`_world.county_samples`: a hex counts once per sample of the county in it), `null` for small counties that no
sample hits. `cbsa` is the cities.json id of the metro/micro area the county belongs to (OMB delineation), or `null`
(not in a CBSA, or in one too small for ACS 1-year data and so not in cities.json). `cell` (format `int`) is a
representative US land cell: the one nearest the county's Gazetteer centre point, in its own state where possible, so a
county smaller than a hex can still be ringed and framed. `null` always means no data.

**Faith, wellbeing, disaster and veteran columns** (`pipeline/build/counties.py` `community_fields`; `fields` describe
each, same null rules), after `cell`, in this order: `faith` (float, adherents per 100 residents, 1 decimal; null for CT), `faith_tradition` (text: a `faith_tradition`
category id), `amenities` (float index, 1 decimal), `mhlth` (pct, PLACES age-adjusted frequent mental distress),
`loneliness` (pct, PLACES; null in about 845 counties of states PLACES 2025 left out), `disasters` (int, DR declarations
since 2000-01-01, 0 = none), `veterans` (int, `B21001_002`), `veterans_pct` (pct of civilians 18+), `armed_forces` (int,
ACS `B23025_006`), `armed_forces_pct` (pct of population 16+). A column whose source interim is missing is all null.
Categorical county columns are `text` (the category id), not `category`.

## Optional map-layer files

Every file below is **optional**: the app and `check` work without it, and each owning builder validates its own file with
a `check(web_dir)` (see Pipeline conventions). Shared rules:

* Top level always has `"version": 1`, `"vintage"` (a human string, or `{part: string}`), and `"sources": [source ids]`
  (sources.json ids, so the Almanac can cite them).
* `cell` = a world.json cell index (pointy-top odd-r, `row * cols + col`); a site's `cell` is a US land cell (`owner >= 0`)
  unless stated. `x`, `y` = map km. `county` = 5-digit GEOID from world.json `counties` (or null), `cbsa` = a cities.json
  `id` (or null), `state` = postal abbr.
* Money is **US dollars** (not thousands or millions) unless the key says otherwise (`_musd`); shares are 0..1 fractions;
  `null` = unknown, never `0`. A value that is a **lower bound** (suppressed parts left out) says so (`lower_bound: true`
  or a `suppressed` count).
* Rules that pick things (districts, wonders, routes) are published inside the file as text (`rule` / `rules`) so the UI
  and the Almanac can quote them.
* **Loading** (browser): `infrastructure`, `military`, `wonders`, `trade` load eagerly right after the first frame (keep
  each **under ~300 kB**); `citizens`, `districts`, `disasters` load on demand with `app.loadData(name)`.

### citizens.json (lazy)

Per metro, the citizen mix for the City View's person icons, from ACS 1-year (`acs_1yr`), built by
`pipeline/build/citizens.py`. Figures are computed in the pipeline with **largest-remainder rounding** (each row's
figures sum exactly to its `figures` count), so the frontend only draws icons. About 950 kB: load on demand.

```jsonc
{
  "version": 1, "vintage": "ACS 2025 1-year", "year": 2025, "sources": ["acs_1yr"],
  "figures": {"workforce": 20, "age": 10, "commute": 10},   // icons per row (education/nativity have no figures)
  "rows": {"workforce": "Employed civilians 16+ by occupation", "age": "…", "commute": "…", "education": "…", "nativity": "…"},
  "groups": {   // the categories of each row, in display order
    "workforce": [{"key": "executive", "label": "Executives & managers", "icon": "c-executive",
                   "lines": "C24010 004 (male lines; female = male + 36)"},
                  {"key": "engineer"}, {"key": "scholar"}, {"key": "healer"}, {"key": "service"}, {"key": "clerk"},
                  {"key": "farmer"}, {"key": "builder"}, {"key": "maker"}],
    "age": [{"key": "child"}, {"key": "young"}, {"key": "midlife"}, {"key": "elder"}],
    "commute": [{"key": "drove_alone"}, {"key": "carpool"}, {"key": "transit"}, {"key": "walk"}, {"key": "other"}, {"key": "home"}],
    "education": [{"key": "less_than_hs"}, {"key": "high_school"}, {"key": "some_college"}, {"key": "bachelors"}, {"key": "graduate"}],
    "nativity": [{"key": "born_in_state"}, {"key": "other_state"}, {"key": "native_abroad"}, {"key": "foreign_born"}]
  },   // every entry has "label", "lines" and a suggested "icon" id (c-*; not yet in icons.js: fall back to a person)
  "rule": {"specialist_high": 1.5, "specialist_low": 0.67, "min_share": 0.01, "max_high": 4, "max_low": 2, "text": "…"},
  "national": { /* a row for the US (geos 0100000US); "specialists": [] and no "reliable" */ },
  "cities": {"41940": { /* a row */ }}   // every cities.json id; a city absent from all five tables → null
}
// a row:
{
  "workforce": {"total": 1056000, "counts": {"executive": 211000, …}, "shares": {"executive": 0.2, …},
                "figures": {"executive": 4, …}} | null,      // null when Census left the CBSA out of C24010
  "age": {"total": …, "counts": {…}, "shares": {…}, "figures": {…}, "median": 38.4 /* B01002_001, or null */} | null,
  "commute": {"total": …, "counts": {…}, "shares": {…}, "figures": {…}} | null,   // workers 16+ (C08301_001)
  "education": {"total": …, "counts": {…}, "shares": {…}, "bachelors_plus": 0.57} | null,  // adults 25+
  "nativity": {"total": …, "counts": {…}, "shares": {…}, "foreign_born": 0.42, "born_in_state": 0.31} | null,
  "specialists": [{"row": "workforce", "key": "engineer", "share": 0.26, "national": 0.074, "ratio": 3.5}],
  "reliable": true   // false for micropolitan areas (1-year margins of error are large there; the UI greys them)
}
```

* `counts` are whole people (rounded estimates); `shares` = count ÷ `total`, 3 decimals; every category of a row is
  present (a category can be 0). A row is null when Census left the CBSA out of that table (2025: 15 cities have no
  C24010 row, 10 no C08301 row) — never zeros.
* `specialists`: categories of any row whose share is ≥ 1.5× (up to 4, strongest first) or ≤ 0.67× (up to 2,
  strongest first) the national share; categories under 1% both in the city and nationally are skipped as noise.
  Ratios are computed from unrounded shares. Use them for the up/down chevrons and the "great person" call-out.

Category → lines (C24010 male line, female = +36): executive 004; engineer 007; scholar 011; healer 016 + 020; service
019 − 020; clerk 027; farmer 031; builder 030 − 031; maker 034 (they sum to `C24010_001`). Age (B01001 male, female = +24):
child 003-006, young 007-012, midlife 013-019, elder 020-025. Commute (C08301): drove_alone 003, carpool 004, transit 008,
walk 009, other 010, home 011 (shares of workers, not of all people). Education (C15003): less_than_hs 002-009,
high_school 010-011, some_college 012-014, bachelors 015, graduate 016-018. Nativity (B05002): born_in_state 003,
other_state 004, native_abroad 002 − 003 − 004, foreign_born 013. All five sums were verified to equal each table's
total line on the national row. Labels are plain words (original names; no game's unit names).

### districts.json (lazy)

Real industry specialisation from BLS QCEW annual averages (`bls_qcew`, ~40 industry slices), as strategy-game
districts, built by `pipeline/build/districts.py`. 2025 QCEW publishes metros as totals only, so **metro values are
sums of member counties** (cities.json `counties`), and LQ = (metro jobs in the district's NAICS ÷ metro total covered
jobs) ÷ (the same US ratio). The total is QCEW industry 10, all ownerships. About 670 kB: load on demand.

```jsonc
{
  "version": 1, "vintage": "BLS QCEW 2025 annual averages", "year": 2025, "sources": ["bls_qcew", "ipeds"],
  "rule": {"min_lq": 1.25, "min_jobs": 1000, "min_share": 0.01, "specialty_lq": 3.0, "specialty_jobs": 5000, "specialty_share": 0.005, "max_per_city": 5,
           "harbor_needs_water": true, "badge_lq": 6.0, "badge_share": 0.03, "college_share": 0.15, "text": "…(quote this in the UI)…", "county_note": "…"},
  "catalog": [{
    "id": "campus", "name": "Campus", "icon": "d-campus", "color": "#4a7bd0",
    "naics": ["5417", "6113", "5415", "5132", "5182"],   // codes summed for the district's score
    "own": [1, 2, 3, 5],                                  // QCEW ownership codes summed
    "sub": {"5417": "Research labs", "6113": "Universities", "5132": "Software", …},  // the listed specialities
    "badge": {"id": "scientific", "label": "Knowledge city", "labels": {"6113": "College town", "5132": "Tech city", …}},
    "description": "…", "caveat": null        // e.g. encampment: "Civilian defense staff only; …"
  }],
  "industries": {"3344": {"title": "Semiconductor and other electronic component manufacturing", "us_emp": 380000}},
  "national": {"emp": 155732363, "avg_pay": 76000},
  "cities": {"41940": {
    "emp": 1180000, "avg_pay": 152000, "counties": [2, 2],      // [counties with a disclosed total, member counties]
    "top": [{"naics": "3344", "emp": 45000, "lq": 15.1, "avg_pay": 251000, "oty_pct": 0.021,
             "suppressed": 0, "lower_bound": false}],           // up to 8 fetched industries by LQ (≥ 1,000 jobs,
                                                                // all ownerships; the 2-digit 31_33/52/22 excluded)
    "districts": [{"id": "campus", "lq": 2.82, "emp": 157377, "share": 0.133, "avg_pay": 190000,
                   "sub": "5415", "sub_lq": 4.66, "sub_emp": 60000,  // strongest speciality (null if none ≥ 1,000 jobs, LQ > 1)
                   "sub_lower_bound": false,  // the speciality's own value is a lower bound (show ≥)
                   "via": "broad",            // "broad" (the district passes) | "specialty" (only a speciality does)
                   "strength": 101000,        // jobs above the national norm, emp − emp/LQ: the ranking key
                   "suppressed": 2, "lower_bound": true}],   // passing the rule, strongest first, ≤ 5
    "badge": {"id": "scientific", "label": "Tech city", "district": "campus", "basis": "qcew",
              "text": "Computer services: 4.7× the national share of jobs"}  // "≥4.7×" when a lower bound;
                                                    // "Seat of government"/"Capital city" only for capital metros
           | {"id": "scientific", "label": "College town", "district": "campus", "basis": "ipeds", "withheld": true,
              "text": "Pennsylvania State University: R1 research university enrolment equal to 34% …"}
           | null
  } | null},                                                    // null: no member county has QCEW data
  "counties": {"06085": {"emp": 1100000, "districts": [["campus", 2.9, 150000]]}}  // [id, lq, emp], same rule
}                                                               // (no Harbor water test), every county with a total
```

Districts (fixed ids, in this order; NAICS 2022):

| id | name | summed NAICS (own) | specialities (`sub`) | badge id |
|---|---|---|---|---|
| campus | Campus | 5417, 6113, 5415, 5132, 5182 (all) | research labs, universities, software, computer services, data hosting | scientific |
| commercial_hub | Commercial hub | 52 (all) | 5231 securities, 524 insurance | commercial |
| industrial_zone | Industrial zone | 31-33, 211, 2121 (all) | 3361 autos, 3344 chips, 3254 pharma, 3241 refining, 331 metals, 211 oil & gas, 2121 coal | industrial |
| harbor | Harbor | 483, 4883 (all) | shipping lines, port services | maritime |
| theater_square | Theater square | 711, 512, 516 (all) | arts & sports, film, broadcasting | cultural |
| entertainment_complex | Entertainment complex | 713, 721 (all) | 7132 casinos, 713 amusement, 721 hotels | entertainment |
| aerodrome | Aerodrome | 481, 4881, 3364 (all) | airlines, airport services, aerospace | aviation |
| government_plaza | Government plaza | 921-927 (federal, state) | offices, courts/police/prisons, benefits, economic agencies, 927 space | governmental |
| encampment | Encampment | 928110 (federal, state) | defense civilians | militaristic |
| aqueduct | Aqueduct & dam | 22 (all) | 2211 power, 2213 water | utility |

* **Rule** (also in `rule.text`): a district appears when its summed LQ ≥ 1.25 and it has ≥ 1,000 jobs or ≥ 1% of the
  metro's jobs (`via: "broad"`), or when one of its specialities has LQ ≥ 3 with ≥ 1,000 jobs (`via: "specialty"`, e.g.
  Houston's oil and gas inside an average-sized Industrial zone: `lq` is then below 1.25). Districts are ranked by
  `strength` (jobs above the national norm, the larger of the district's and its qualifying speciality's), so a small,
  extreme speciality does not outrank what most of a city does; up to 5. Harbor needs a footprint hex that is water or
  next to water, or that a world.json river crosses.
* **Badge** = the strongest district's `badge`, unless a listed district has LQ ≥ `badge_lq` (6) and ≥ `badge_share`
  (3%) of the metro's jobs, in which case the strongest such district (Huntsville, Alamogordo: Military town). So
  `badge.district` is one of the city's `districts`, not always the first. The label is the speciality's nickname
  (`labels[sub]`) when that speciality has LQ ≥ 3, else the district's generic nickname — one vocabulary of nicknames:
  Knowledge city, Finance city, Factory town, Port city, Arts city, Resort city, Air hub, Government town, Military
  town, Utility town. A Government plaza in the national capital (cities.json `capital`) is "Capital city".
  `basis: "ipeds"`: when no Campus district passes because BLS withheld some of a member county's Campus rows, and R1
  universities' IPEDS 12-month enrolment is ≥ `college_share` (15%) of the metro's population, the badge is
  "College town" (`district: "campus"`, `withheld: true`; the campus is *not* in `districts`; State College, Ithaca,
  Champaign, Ames …). null when no district passes and no such rule applies ("diversified").
* Suppressed county rows (`disclosure_code` N, published as 0) are left out of the sums: `suppressed` = how many member
  counties had a withheld part of that value, `lower_bound` = suppressed > 0 (the UI shows "≥"). A value with no
  disclosed county at all is null, never 0. Big single employers are often withheld (e.g. the University of Michigan in
  Ann Arbor, Penn State), so Campus undercounts some college towns.
* Encampment here is QCEW NAICS 928110 (civilian DoD staff and state Guard employees). Uniformed troops come from
  military.json `cities`: the City View shows an Encampment when either file has one, with military.json's tier label.
* QCEW leaves out the self-employed, most farm workers, railroads and uniformed military; jobs are counted where the
  employer's establishment is, not where workers live.

### infrastructure.json (eager)

Tile improvements: roads and rail rasterised onto hex links (no polylines), plus ports and airports as sites. Built by
`pipeline/build/infrastructure.py` from `natural_earth_roads` (NE 1:10m roads + railroads, pinned v5.1.2), `usace_ports`
and `faa_airports` (both in `pipeline/sources/transport_hubs.py`). About 200 kB.

```jsonc
{
  "version": 1,
  "vintage": {"roads": "Natural Earth v5.1.2 (1:10m)", "rail": "…", "ports": "USACE principal ports, CY2023 tonnage",
              "airports": "FAA CY2025 enplanements, CY2025 all-cargo"},
  "sources": ["natural_earth_roads", "usace_ports", "faa_airports"],
  "rules": {"roads": "…", "rail": "…", "ports": "…", "airports": "…"},   // selection rules, quotable in the UI
  "road_classes": [{"id": "interstate", "name": "Interstate"}, {"id": "major", "name": "Major highway"}],
  "rail_tiers": [{"id": "main", "name": "Main line"}, {"id": "secondary", "name": "Secondary line"}],
  "hubs": {"L": "Large hub", "M": "Medium hub", "S": "Small hub", "N": "Nonhub primary"},
  "roads": [[3721, 3722, 0, "I-95"]],   // [cell a, cell b, class index, route name or null]; a < b, neighbours, unique pair
  "rail": [[3721, 3845, 0]],            // [a, b, tier index]; a < b, neighbours, unique pair
  "ports": [{"id": "2031", "name": "Houston Port Authority", "type": "coastal|great_lakes|inland", "rank": 1,
             "tons": 309531236, "domestic": …, "foreign": …, "imports": …, "exports": …, "year": 2023,   // short tons
             "x": …, "y": …, "cell": 9123, "county": "48201", "cbsa": "26420", "state": "TX"}],     // sorted by rank
  "airports": [{"id": "ATL", "name": "Hartsfield/Jackson Atlanta International", "city": "Atlanta", "hub": "L|M|S|N|null",
                "enplanements": 51459786, "enplanements_prev": 52511402, "cargo_lbs": 2864017498 | null, "year": 2025,
                "x": …, "y": …, "cell": …, "county": …, "cbsa": …, "state": "GA"}]   // sorted by enplanements, desc
}
```

* **Links** join **neighbouring** cells, at least one end on US land (`owner >= 0`) and neither end foreign land
  (`owner == -2`). Each line is sampled every 4 km, gaps are filled by a hex line walk, and a cell the line only clips
  at a corner is dropped (so a road along a row boundary does not zigzag). A pair appears once, with its best class
  (an Interstate link is never also a major link). Rail samples inside Canada or Mexico are dropped.
* **Road classes**: 0 = every NE road with `level == "Interstate"`; 1 = other roads at NE scale rank ≤ 6 plus
  expressways typed "Major Highway"/"Beltway". Route names: `I-95`, `US 101`, or the NE name for state roads; where
  several routes share a link the lowest number wins. **Rail tiers**: 0 = NE scale rank ≤ 5, 1 = 6–7.
  Natural Earth road and rail work is map art, not statistics (older alignment, about half the real rail network).
* **Ports**: USACE principal ports in the lower 48 (port-area centroid; long river ports are approximate). **Airports**:
  every primary airport (`hub` L/M/S/N) plus every airport in FAA's all-cargo table (`hub` null if not primary),
  placed by FAA id with the NASR airport master. `enplanements` null when the airport is only in the cargo table;
  `cargo_lbs` (all-cargo landed weight) null when it is not in the cargo table (not zero cargo).
* A site's `cell` is the US land cell at its point, else the nearest within 2 hexes; `x`/`y` stay the true position (a
  port's may be on water). `county`/`cbsa` come from that cell's centre county (OMB delineation, cities.json ids only).
  Tons and pounds are as published (short tons, landed lbs).

### trade.json (eager)

India uses the `routes[].path` and `top_mode` fields for map art. The builder writes
`literal_paths: true` and an empty `zones` list. The schematic sea backbone has
`schematic: true`. Coastal branches carry `name`, `tons_k` in thousand metric
tonnes handled by that port, `period`, its exact start and end, `status`, and
`source`. The rail records carry the operating corridor names, snapshot date,
and source. The map draws each cell in order. Commerce omits the upstream
origin–destination tables for this edition.


Freight "trade routes" between FAF5 zones (`faf5`), domestic flows only (`trade_type` 1), newest FAF year. Built by
`pipeline/build/trade.py` (after infrastructure, whose road links the drawn paths follow). About 70 kB.

```jsonc
{
  "version": 1, "vintage": "FAF5.7.1, 2024", "year": 2024, "sources": ["faf5"],
  "rule": "The 40 largest domestic freight flows by value between FAF zones in different states …",   // quote in the UI
  "path_note": "FAF gives a shipment's start and end zones, not its route: …",                          // quote in the UI
  "units": {"value_musd": "million current US dollars", "tons_k": "thousand short tons", "tmiles_m": "million ton-miles"},
  "modes": [{"id": "truck", "name": "Truck"}, {"id": "rail", …}, {"id": "water"}, {"id": "air"}, {"id": "multiple"},
            {"id": "pipeline"}, {"id": "other"}],                  // FAF dms_mode 1..7, in this order
  "commodities": {"43": "Mixed freight"},                          // SCTG2 code → FAF's short name (codes used below)
  "national_musd": {"domestic": 19788731.6, "import": 3134841.1, "export": 2045950.5},   // all zones incl. AK and HI
  "zones": [{"id": "092", "faf": ["092", "341", "363", "423"], "name": "New York-Newark, NY-NJ-CT-PA", "short": "New York",
             "kind": "metro|rest_of_state", "states": ["CT", "NJ", "NY", "PA"], "cities": ["35620", "…"],   // population order
             "counties": 30,                                          // member counties on the map
             "anchor": {"cell": 3845, "x": …, "y": …, "city": "35620" | null} | null,
             "partners": [["251", 61923.5, "truck"]],                // top 5 partner zones, any state: [zone, value_musd, top mode]
             "totals_musd": {"within": …, "other_zones": …, "import": …, "export": …}}],   // sorted by id
  "routes": [{"a": "092", "b": "251", "rank": 1, "value_musd": 61923.5, "tons_k": 15089.1, "tmiles_m": 3471.2,
              "modes": {"truck": 0.7268, "rail": 0.01, "...": 0}, "top_mode": "truck", "top_commodity": "43",
              "dist_km": 306, "path": [3845, 3846, "…"]}]           // rank order (value, desc)
}
```

* **Zones**: Alaska and Hawaii are dropped (115 zones remain). The parts of one CFS area split by a state line
  (same CSA/CBSA code) are **merged** into one zone: `id` = its lowest FAF code, `faf` lists the parts. Member counties
  come from the 2023 OMB delineation (CSA or CBSA code within the part's state; Knoxville's 2017 CSA 314 is today's 315);
  a rest-of-state zone holds the state's other counties. Each cities.json city joins the zone holding most of its
  member counties. `anchor` = the biggest city's banner cell, or (no city) the land cell nearest the middle of the
  zone's cells; `null` only if neither exists.
* **Routes**: only flows between FAF parts in **different states** count, the two zones may share no state, and their
  anchors must be ≥ 250 km apart; both directions are summed; the 40 largest by value are kept. `modes` are value
  shares (sum to 1). `top_commodity` is the largest SCTG2 by value among each part pair's top 5. `path` is a chain of
  neighbouring cells from `a`'s anchor to `b`'s along the cheapest road links (Interstate < major < rail < cross-country
  < water steps): a drawing aid, not data (FAF assigns no route).
* Values are FAF model estimates in **million current dollars** (`value_musd`) and **thousand short tons** (`tons_k`), as
  FAF publishes them; say so in the UI. Pipeline-dominated routes (crude, gas) are real and should get their own style.

### military.json (eager)

Built by `pipeline/build/military.py` from `mirta` (`sources/mirta.py`), `dmdc_personnel` (`sources/dmdc.py`),
`oldcc_spending` (`sources/oldcc.py`) and `acs_5yr`. About 280 kB (mostly installations).

```jsonc
{
  "version": 1,
  "vintage": {"installations": "DoD MIRTA FY2025 (layer edited …)", "personnel": "DMDC, as of September 30, 2026",
              "spending": "OLDCC FY2024", "acs": "ACS 2024 5-year"},
  "sources": ["mirta", "dmdc_personnel", "oldcc_spending", "acs_5yr"],
  "rule": "A metro gets an Encampment when …",           // the Encampment rule, quotable as is
  "rules": {"tier": "…", "ranges": "…", "encampment": "…", "installations": "…",   // every selection rule as text
            "names": "…"},                       // the 2025 Army renames applied to MIRTA names, with the source URL
  "flagships": ["Naval Station Norfolk", …],             // the curated flagship list (names as in MIRTA)
  "caveats": "…",                                         // show where installation/personnel numbers appear
  "components": [{"id": "army", "name": "Army", "codes": ["usa"]}, {"id": "navy"}, {"id": "air_force"}, {"id": "marines"},
                 {"id": "army_reserve"}, {"id": "navy_reserve"}, {"id": "air_force_reserve"}, {"id": "marine_reserve"},
                 {"id": "army_guard"}, {"id": "air_guard"}, {"id": "other"}],   // Space Force sites are filed as air_force
  "installations": [{"id": "fort-bragg-usa", "name": "Fort Bragg", "component": "army", "joint": false,
                     "name_mirta": "Fort Cavazos",          // optional: only when `name` differs (see rules.names);
                                                           // ids keep the MIRTA spelling (fort-cavazos-usa = Fort Hood)
                     "status": "act|semi|care",           // closed (clsd) and excess (excs) sites are left out
                     "tier": "major|base|site",            // rules.tier: by boundary area / component, never headcount
                     "curated": false,                     // true: a flagship base made 'major' by the published list
                     "area_km2": 628.4 | null,             // null: MIRTA has no boundary for the site (incl. folded parts)
                     "parts": ["NNSY St Helena", …],       // optional: small parcels folded into this installation
                     "components": ["air_force", "marines"],   // optional: when the folded parts span components
                     "cells": [..] | null,                 // hexes whose centre the boundary covers (boundaries >= 200 km²)
                     "x": …, "y": …, "cell": …, "county": "37051" | null, "cbsa": "22180" | null,
                     "state": "NC",                        // where the point lies (county, else hex owner)
                     "state_filed": "NC"}],                // the state MIRTA files it under (UTTR: NV)
                                                           // sorted major → base → site, then by area
  "ranges": [{"id": "nevada-test-and-training-range-usaf", "name": "Nevada Test and Training Range",
              "component": "air_force", "area_km2": 11702.8, "cells": [..],   // never empty (see rules.ranges)
              "state": "NV",                  // its installation's point state when mapped (Fort Bliss: TX), else hex_state
              "hex_state": "NV",              // the state holding most of its hexes (Fort Bliss: NM)
              "installation": "…" | null, "name_mirta": "…",   // name_mirta optional, as for installations
              "components": ["air_force", "marines"]}],   // optional; the 30 largest boundaries: restricted ground
  "states": {"NC": {                                       // postal abbr; 50 states, DC and PR (no data → null)
    "personnel": {"active": {"army": …, "navy": …, "marines": …, "air_force": …, "space_force": …, "coast_guard": …, "total": …},
                  "guard_reserve": {"army_guard": …, "army_reserve": …, "navy_reserve": …, "marine_reserve": …,
                                    "air_guard": …, "air_force_reserve": …, "coast_guard_reserve": …, "total": …},
                  "civilian": {"army": …, "navy": …, "marines": …, "air_force": …, "defense_wide": …, "total": …},
                  "total": …} | null,                     // DMDC, by duty state
    "spending": {"total": 1.2e10, "contracts": …, "grants": …, "payroll": …,          // OLDCC, US dollars
                 "payroll_parts": {"civilian": …, "active_duty": …, "guard_reserve": …},
                 "pct_gdp": 0.021, "per_resident": 1150, "personnel": …,              // OLDCC's own personnel count
                 "top_counties": [{"name": "Onslow", "county": "37133" | null, "contracts": …}],   // top 10, OLDCC names
                 "top_vendors": [{"name": "Austal", "contracts": …}]} | null}},       // top 5 contractors
  "national": {"personnel": {…same shape…}, "personnel_scope": "50 states, DC and US territories …",
               "spending": {"total": …, "contracts": …, "grants": …, "payroll": …, "pct_gdp": …, "per_resident": …,
                            "scope": "50 states and DC"},
               "veterans": 16900000, "armed_forces_resident": 1100000, "acs_scope": "…"},   // ACS 5-year, 50 states + DC
  "cities": {"22180": {"tier": "garrison|fortress", "armed_forces": 36721, "share": 0.1212, "naval": false,
                       "installations": ["fort-bragg-usa"],   // up to 8 ids, largest first
                       "installation_count": 1}}             // only cities that pass the Encampment rule
}
```

* Tiers: `major` = active-duty (or other DoD) boundary ≥ 100 km², or one of the curated `flagships` (large bases on
  small land: Naval Station Norfolk, Naval Base San Diego, Wright-Patterson …; `curated: true`). Guard and Reserve
  sites are never `major` (`base` from 10 km², else `site`). Other active-duty sites are `base` from 1 km², else `site`.
  Parcels under 1 km² sharing a hex and component with a larger installation are folded into the nearest one
  (`parts`); the two Barry M. Goldwater Range halves (Air Force, Marine Corps) are one installation and one range.
* Encampment (cities): (a) an active non-Guard installation of tier `major` or `base` in one of the metro's member
  counties, or a range covering one of its hexes, **and** (b) ACS armed forces (`B23025_006`, by residence, summed over
  member counties) ≥ 1% of the 16+ population, or ≥ 2,000 **and** ≥ 0.3%: `fortress` at ≥ 3%, else `garrison`.
  `naval` when the qualifying Navy and Marine installations outweigh the Army and Air Force ones, a `major` counting 4
  and a `base` 1 (so a cluster of small Navy parcels does not make Washington naval). New York and Detroit do not
  qualify; the smallest qualifying shares are about 0.3% (Tampa, Kansas City, Providence).
* Installation-level headcounts are not published; never invent them. Veterans and armed forces by county live in
  counties.json (`veterans`, `armed_forces`), not here.
* `top_counties[].county` is null where OLDCC's county name does not match one on the map (Connecticut: OLDCC uses the
  old counties, the map the 2022 planning regions; Alaska and Hawaii are not on the map). Contract dollars are by place
  of performance, not where bases are.
* Not on the map: sites outside the lower 48 and a few island sites with no US land hex within two rings (Key West,
  San Clemente and San Nicolas Islands).

### wonders.json (eager)

**India build.** `pipeline/india/wonders.py` imports the checksum-pinned IC-8 inventory.
`pipeline/build/wonders.py` projects all points onto the active grid and emits the v1 envelope below.
Its `vintage` is the inventory date, `license` is CC BY-SA 4.0 with a `license_url`, and `national` is an empty object.
A row's `kind` is `landmark`, `natural` or `university` (public research or teaching site).
`rule` is its primary selection rule and `selection_rules` keeps all applicable rule IDs.
Selected park rows carry `metrics.area_km2` and `metrics.protected_id`. Their `rank` orders
the five largest parks in the pinned WII inventory by official area. IISc, IIT and IISER rows carry
`metrics.institution_class` and `metrics.institution_count`, the number of verified mapped sites
in that class. Their rank is alphabetical within the class. These rows carry `period`,
`sources` and `estimated: false`. Other rows use `metrics: null` and an internal selection order.
`lat` and `lon` are decimal-degree anchors, and `cell` contains the projected `x` and `y`. The
selected parks use the verified projected IC-27 anchor and may have null `lat` and `lon`. The
containing cell can be water or have a different jurisdiction on a coarse grid. `draw_x` and `draw_y` give
the sprite and hit target coordinates after bounded decluttering within the anchor's grid ownership.
`state` is the
inventory's jurisdiction code and `location` its display name. Mount Kailash has `foreign_side: true`
and `state: null`, and its containing cell is foreign land. `county` and `cbsa` are null.
`cells` is the sorted union of accepted linked protection hexes, or null. `extent_sources` credits
the accepted geometry independently of the anchor and selection sources.
Rows also carry `subtype`, `motif`, `description`, `era`, `unesco_id` (ID or null), and the per-row `references` from IC-8.

US reference built from `nps_boundaries` (`sources/nps.py`), `nps_visits`, `ipeds`, `herd`
(`sources/nsf_herd.py`) and `nhl_landmarks` (`sources/nrhp_nhl.py`). About 20 kB, 52 wonders.

```jsonc
{
  "version": 1,
  "vintage": {"parks": "NPS recreation visits 2025", "boundaries": "…", "universities": "NSF HERD FY2025; IPEDS …",
              "landmarks": "NPS National Register GIS (NHL subset)"},
  "sources": ["nps_boundaries", "nps_visits", "ipeds", "herd", "nhl_landmarks"],
  "rules": [{"id": "national_park", "kind": "natural", "kinds": ["natural", "recreation", "coastal", "monument"],
             "year": 2025, "text": "The 15 lower-48 National Parks …"},
            {"id": "park_unit", "kind": "natural", "kinds": […same…], "year": 2025, "text": "The 5 most-visited other …"},
            {"id": "research_university", "kind": "university", "year": 2025, "text": "The 20 universities …"},
            {"id": "landmark", "kind": "landmark", "curated": true, "text": "Hand-picked by this project …"}],
  "national": {"park_visits": 323014305, "park_visits_year": 2025, "r1_universities": 187},
  "wonders": [{"id": "nps-GRSM", "name": "Great Smoky Mountains National Park", "short": "Great Smoky Mountains",
               "kind": "natural|recreation|coastal|monument|university|landmark",   // must be in its rule's `kinds`
               "rule": "national_park", "rank": 1,   // rank within its rule
               "metrics": {…},                    // see below; unknown values are null
               "x": …, "y": …, "cell": …, "cells": [..] | null,   // cells: hexes a big park covers (protected land)
               "county": "37173" | null, "cbsa": "…" | null, "state": "NC", "curated": false,
               "listed_as": "…",                  // landmarks only: the name in the NPS layer
               "state_note": "…"}]                // optional: why state/county differ from the publisher's (Statue of Liberty → NY)
}
```

* `metrics` by rule. Parks: `{visits, year, area_km2, unit_type}`; the merged National Mall (`nps-MALL`) adds
  `visits_of` (the memorial its `visits` come from), `memorials` ({code: visits}) and a `note`: never add the memorial
  counts together. Universities: `{rd_usd, federal_usd, year, enrollment, enrollment_year, r1, med_school,
  reported_as?}` (dollars; `enrollment` is IPEDS 12-month unduplicated headcount, which includes online students;
  `reported_as` names a combined HERD report matched to its lead campus, e.g. Texas A&M with its Health Science Center).
  Landmarks: NPS sites `{visits, year, unit_type}`, NHLs `{designated, nhl_ref, note?}` (`note` when a value the
  NHL layer leaves blank was filled in by hand: Wrigley Field's 2020 designation).
* Park `kind` follows the NPS unit type: National Recreation Areas → `recreation` (Golden Gate, Gateway, Lake Mead),
  seashores and lakeshores → `coastal` (Gulf Islands), memorials, historic sites and battlefields → `monument`, plus
  overrides for the National Mall and the Gateway Arch (a National Park, but a monument); everything else `natural`.
  `rule.kind` stays "natural" for old readers; `rule.kinds` lists what the rule allows. Parks of any of these kinds
  have `metrics.visits` and may have `cells` (protected land): readers should key on `rule` (national_park,
  park_unit), not `kind`, for visits and protected land.
* `rank` is 1-based within the wonder's rule; curated landmarks are ranked alphabetically (not by importance).
  Recreation visits are counted differently by unit type, so parks are ranked only within their rule (the rule text
  says so). Wonders are in rule order: national_park, park_unit, research_university, landmark.
* `state`/`county`: the publisher's filed state wins when the point lands across a border river on the 1:20M county
  outlines (Gateway Arch → St. Louis city). The curated landmarks never repeat a site a park rule already holds
  (Hoover Dam was dropped for Golden Spike because Lake Mead NRA is a park-unit wonder). Statue of Liberty: NPS files it under NJ,
  but Liberty Island is part of New York County, so `state` "NY", `county` "36061" with a `state_note`.

### disasters.json (lazy)

Built by `pipeline/build/disasters.py` from the sources `fema_declarations` (`pipeline/sources/openfema.py`) and
`noaa_billions` (`pipeline/sources/noaa_billion.py`). About 160 kB.

```jsonc
{
  "version": 1, "sources": ["fema_declarations", "noaa_billions"],
  "vintage": {"fema": "OpenFEMA declarations as of 2026-11-25", "noaa": "NOAA NCEI billion-dollar disasters 1980–2024 (final release)"},
  "fema": {
    "window": ["2000-01-01", "2026-11-25"], "as_of": "2026-11-25",     // as_of = the day the declarations were fetched
    "rule": "Distinct major-disaster (DR) declarations naming the county …",   // full text, quote it in the UI
    "types": [{"id": "hurricane", "name": "Hurricanes & tropical storms", "incident_types": ["Hurricane", "Tropical Storm", "Tropical Depression", "Typhoon"]},
              {"id": "flood", …}, {"id": "fire", …}, {"id": "severe_storm", …}, {"id": "winter", …},
              {"id": "other", "incident_types": []}],          // other = every FEMA incidentType not listed above
    "counties": {"columns": ["geoid", "total", "hurricane", "flood", "fire", "severe_storm", "winter", "other", "last_date"],
                 "rows": [["01001", 14, 3, 2, 0, 8, 1, 0, "2025-04-02"]]},   // world.json counties order; 0 = none declared; last_date null if none
    "states": {"TX": {"total": 120, "statewide": 3, "by_type": {"hurricane": 30, "...": 0}}},   // every DR disaster in the state (incl. AK, HI, territories)
    "recent_days": 365,
    "recent": [{"disaster": 4870, "type": "hurricane", "incident_type": "Hurricane", "title": "Severe Storms And Flooding",
                "date": "2026-10-02", "state": "FL", "counties": ["12086"], "statewide": false, "areas": 1}]
                // declared within recent_days of as_of, newest first; counties = map GEOIDs only (CT mapped to regions),
                // areas = FEMA's designated-county count (also counts areas off the map, e.g. Alaska or Puerto Rico)
  },
  "noaa": {
    "years": [1980, 2024], "final": true, "unit": "USD, CPI-adjusted", "rule": "…",
    "types": [{"id": "drought", "name": "Drought"}, {"id": "flooding"}, {"id": "freeze"}, {"id": "severe_storm"},
              {"id": "tropical_cyclone"}, {"id": "wildfire"}, {"id": "winter_storm"}],
    "states": {"TX": {"count": {"drought": 20, "...": 0}, "cost_usd": {"drought": 4.4e10, "...": 0}}},   // incl. AK, HI, PR, VI, GU
    "national": {"events": 403, "cost_usd": 2.92e12, "deaths": 16000,
                 "by_year": [{"year": 1980, "events": 3, "cost_usd": …}],      // from the national event list
                 "costliest": [{"name": "Hurricane Katrina (August 2005)", "type": "Tropical Cyclone", "begin": "2005-08-25",
                                "cost_usd": 2.0e11, "deaths": 1833}]}          // top 10 by CPI-adjusted cost
  }
}
```

NOAA events span many states: never add state costs together into a national figure (use `national`). The shared
helper `disasters.county_declarations(fema_interim, geoids)` gives the per-county counts used by the `disasters` lens,
the counties.json column and this file, so the three always agree.

## sources.json

A list of `{id, title, publisher, homepage, license, description, used_for, vintage, files: [{file, url, retrieved, sha256, bytes}]}`.
`files` lists only files the latest `process()` used (`_files`), or every manifest entry if the source didn't say. A file
saved by `download_prefix()` has a `partial` note in the manifest, and its `sha256`/`bytes` describe the saved part.

## almanac.json

India's additional `sections` for the existing Almanac pages, grouped by page title and table heading.
Rows use the terrain table's `name`, `rule` and optional `color` fields.
`facts` carry the value, formatted value, period, and any
source ID, vintage, estimate flag or scope. Row `sources` join to `sources.json` and `links` credit
the relevant references. The Almanac reads the usual terrain, yield, lens, resource and source
catalogues for their standard tables. `terrain_relief` attaches the ETOPO credits and mapped examples
to the standard relief classes. `cell_features` joins the sampled and footprint feature labels by hex.

## Browser module boundaries (web/js)

* `world.js`: `prepareWorld(world, cities, extras) → w` with `w.grid`, `w.raw`, `w.stateColor[]`, `w.cityByCell: Map<cell, city>`;
  `applyLens(w, lens, band = null)` sets `w.colors`/`w.rgb`; exports `WATER = -1`, `FOREIGN = -2`.
* `camera.js`: `Camera` with `fit()`, `toScreen()`, `toWorld()`, `zoomAt()`, `panBy()`, `centerOn()`, `flyTo(x, y, scale, ms)`,
  `step(dt) → bool stillMoving`, `view()`.
* `render/*`: map drawing and banners. `main.js` owns input, state and wiring. `ui/*` owns DOM panels.
* The `state` object (owned by `main.js`, read by `render/*`): `cities`, `lens` (a lenses.json lens or null = terrain),
  `band` (`[t0, t1]` in normalised lens units 0..1, or null: cells outside are dimmed, see `applyLens`), `hoverCell`,
  `selectedCity` (a city object or null), `selectedState` (a state index, abbr, fips or `{index|abbr|fips}`, or null;
  resolved with `world.js` `stateIndex(w, ref)`), `showResources`.
* `render/snapshot.js`: `renderToCanvas(target, cam, w, state, nation, opts) → {cam, hits}` draws a full frame off-screen
  (share images, OG cards) without touching the on-screen cache. `target` is a canvas, OffscreenCanvas or 2D context;
  `opts`: `banners = true`, `overlay = true`, `dpr = 1`, `fit = "contain"|"cover"|"same"`, or an explicit `scale`, `x`, `y`.

## Browser extension API (window.__app; main.js "extension API", app/api.js)

Extensions live in `web/js/ext/<name>/index.js` and export `install(app)`; `ext/index.js` loads `cityView`, `advisors` and
`layers` (roads, rail, forts, ports, airports, wonders and trade routes). The API:

**Data.**
* `app.data.<name>`: the map, place summaries and enabled map layers load at startup. `app.data.lenses`
  starts with the catalog metadata. Await `app.loadData("lenses")` for cell values, district records and
  disasters. `app.data.sources` is populated on first use.
* `app.loadData(name) → Promise<data | null>`: shares requests for `data/<name>.json`, caches results
  and emits `"data"` with `{name, data}` when a result is stored. Failed lens and source requests can be
  retried. `app.loadCounties()` calls `app.loadData("counties")`.

**Static map layers** (art that belongs in the cached map, drawn once per cache render):

```js
const off = app.registerStaticLayer({
  id: "roads",                 // unique; registering the same id again replaces the layer
  z: 55,                       // where it draws among the built-in steps (app.layerZ / render/map.js Z)
  draw(ctx, vp, w, o) {},      // required. ctx starts in world km (saved/restored around the call)
  visible() { return on; },    // optional; false = not drawn, not hit-tested (part of the cache key)
  sig() { return "v1"; },      // optional; any string that changes when the art must re-render (cache key)
  minRpx: 6, maxRpx: Infinity, // optional zoom range in hex radius css px (drawn when minRpx <= Rpx < maxRpx)
  hit(xKm, yKm, Rpx) { return item | null; },   // optional hover / click test, pointer in world km
  tooltip(item) { return "<b>html</b>" | {text: "plain"} | null; },  // optional; a string is HTML: escape data yourself
  click(item, ev) { return true; },             // optional; true consumes the click (see below)
  warm(ctx, vp, w, o) {},      // optional; paint sprites for vp's zoom in idle time (stamps may land anywhere)
  snapshot: true,              // default true: drawn into share images too
});
off();   // or app.unregisterStaticLayer("roads" | layer)
```

* `o` = `{Rpx, s, dpr, lod, lens, selectedCity, showResources, snapshot, app, cells, range: {r0, r1, c0, c1},
  world(), screen(), toScreen(x, y) → [css px]}`. `cells` are the visible cell indices; `o.screen()` switches ctx to
  screen css px of the cache canvas (use `o.toScreen`), `o.world()` back. Use sprites (`render/art/sprites.js`
  getSprite/drawSprite) for anything richer than a few paths.
* Built-in z steps: `WATER 10`, `LAND 20` (land tiles), `GRID 30`, `GLYPHS 40` (terrain), `RIVERS_BORDERS 50`, `CITIES 60`
  (city tiles), `FOG 70` (edge mist), `RESOURCES 80` (screen-space icons), `LABELS 90` (state names). A layer with z
  between two steps draws after the lower one; equal to a step = right after it. Suggested slots: 45 terrain
  improvements, **55 roads and rail**, 58 restricted ground / protected land hatching, **65 sites** (ports, airports,
  forts, wonders, plaques), **85 trade routes** (above resources, under state names).
* The cache key includes every layer's id, `visible()` and `sig()`, so toggling or restyling re-renders the cache and
  nothing else does. Errors in `draw`/`hit`/`sig`/... are logged once per layer and the layer is skipped.
* **Performance**: nothing may animate continuously (an idle map draws no frames); keep each layer under ~3 ms per cache
  render at typical zooms (time it with `drawStatic(..., {layers: app.staticLayers(), timings: T})`: it reports
  `layer:<id>`); precompute geometry once (not per draw); cull to `vp`.
* `app.staticLayers()` lists the registered layers; `app.hitLayer(mx, my)` (screen css px) → `{layer: id, item} | null`.

**Hover and click.** The hover tooltip asks the layers (highest z first, only those drawn at the current zoom) after the
city banners: the first non-null `hit()` wins and its `tooltip(item)` is shown (the cell tooltip otherwise). The
`"hover"` event payload is `{cell, city, resource, x, y, layer, item}` (`layer` = id or null). A click builds
`ev = {cell, city, resource, state, x, y, pointerType, layer, item}`; outside a mode the layer's `click(item, ev)` goes
first (true consumes it), then the `"mapclick"` handlers, then the default (select city/state). While a mode is active
(City View, advisors) the `"mapclick"` handlers go first and the layer's `click` only after them.

**Map toggles.** `app.ui.addMapToggle({id, label, icon, get() → bool, set(on), title?, default?}) → remove()`: a switch
in the "Map" menu next to the Resources toggle in the lens dock (one button + a small menu, so it fits phones). `set` is
yours (flip the state your layer's `visible()` reads); main redraws. The hash key `layers` lists the switches that are on
(`#layers=roads,rail,military`, `layers=none`) and is written only while some switch differs from its default; switches
added after load are set from it, and ids whose extension has not loaded yet stay in the URL. `app.ui.mapToggles()` →
`[{id, label, on}]`. `app.ui.setMapToggle(id, on) → bool` switches one from code exactly as the menu would (redraw,
hash), e.g. an advisor's "show roads, rail and forts" button; false if no toggle has that id (yet).

**URL.** Core keys: `lens`, `city` (CBSA id), `state`, `at`, plus extension keys (`advisor`, `layers`, ...).
* `#state=` accepts a FIPS code (`48`, `6`), a postal code (`TX`, `tx`) or a state name; a link keeps the form it
  was opened with.
* `at=x,y,z`: `x`, `y` = the map-km point at the centre of the screen (rounded), and `z` = **log2(camera scale ÷
  home-fit scale)**, the zoom relative to the "whole country fits" view: `0` = home framing, `1` = twice as close,
  negative = zoomed out past it. It is relative so a link frames the same area on any screen size; it is *not* the
  absolute scale (css px per km) that `app.flyTo(x, y, scale)` and `camera.scale` use. Convert with
  `scale = fitScale × 2^z`. `at` is written only once the user (or an extension) has moved the camera.
* When the hash is written: during a fly-to the link names the **destination** right away (within one 350 ms debounce
  of the flight starting); after a pan or wheel zoom it catches up 350 ms after the camera settles; `app.setMode`
  writes it on the next task. Lens, selection and mode changes push a history entry (Back undoes them); camera moves
  replace the current one. `app.hash.flush()` writes immediately (Share calls it before copying).

**Optional state and debug handles** (not data contracts; don't rely on them from other extensions without asking):
* `state.cityBadges`: an optional `Map<city id, {label, color: "#rrggbb"}>` that `render/banners.js` reads to draw a
  city-type tab on banners that show their yield row. Filled by `ext/cityView` from districts.json; absent = no tabs.
* `app.cityView.model`: read-only getter on the City View's current model (debugging).
* `app.mapArt = {model, on, layers}`: added by `ext/layers` for debugging. `model` holds `installations`, `ports`,
  `airports`, `wonders`, each item `{data (the json row), cell, x, y}`. The layers' hit items have the shape
  `{kind: "fort"|"range"|"port"|"airport"|"wonder"|"route", data}` (route items: `data.route` with `a`/`b`); the
  advisors rely on that shape for map-to-dashboard links, so keep it.

**Who reads which fields.** The advisors read every counties.json column after `cell`, military.json `states`, districts.json
`cities` and `counties`, and citizens.json `cities`; the City View reads citizens.json, districts.json, military.json
`cities`, trade.json zones and infrastructure.json `cbsa`. Update `web/js/ext/advisors` and `web/js/ext/cityView`
when renaming a field in those files.

**Lenses.** Legend ticks print numbers only (plus short units: %, $, min, /km²); a longer `unit` is printed once under
the ticks, so keep `unit` a plain phrase ("adherents per 100 residents"), not part of the number. `lens.note` is shown in the legend; `format: "category"` lenses get a swatch legend (see lenses.json).
