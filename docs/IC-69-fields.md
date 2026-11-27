# IC-69 City View field mapping

The input periods below describe the observations. All sources are the pinned entries in the existing Almanac. City View reads the shared upstream contracts directly. Profiles remain available for the Explorer.

| usaciv input | Indian value and period |
| --- | --- |
| `cities[].id, name, full, capital, metro, x, y, cell` | Existing UN WUP ID, place name and reference position with IndiaCiv labels, Survey of India extent and DataMeet ownership. Existing 2026 map inventory. |
| `cities[].population`, crest and population rank | UN DESA mid-2026 urban agglomeration projection. Rank across the mapped UN cohort with that period. |
| `cities[].growth, growth_years` and growth rank | UN change from 1 July 2025 to 1 July 2026. The exact range is in `provenance.growth.period`. The numeric bounds are 2025 and 2026. |
| `cities[].pop_series` | One numeric-year point for the UN midyear projection. Explorer retains the additional dated interpolation endpoints. |
| `cities[].states, footprint, counties` | GHSL urban centres clipped to Survey of India land. States and member districts are DataMeet intersections (2026 map snapshot). A city without a defensible GHSL match has one anchor hex and no district membership. |
| `lenses.density` → tile residents | Upstream calculation multiplies mapped district density by full hex area. Density describes 1 March 2026 and is a Census A-01 and Technical Group projection. Hex totals include non-UA residents where district density extends across the hex. |
| `world.pct` → built-up, farmland, forest and open shares | ESA WorldCover 2021 classified land. Land shares describe the map hex. Esri 2025 and ESA 2021 historical regional measures remain in Explorer. |
| `cities[].yields, ranks`, `nation.yields` | Existing six IndiaCiv yields and ranks, using each yield's source list, period and coverage. Yield tooltips use the existing atlas definition and metadata. |
| `cities[].gdp, gdp_year, gdp_per_capita`, GDP ranks | Allocates nominal state GSDP to UAs, FY 2025-26 (1 Apr 2025 – 31 Mar 2026). Per person divides by the UN mid-2026 total. Exact fiscal period replaces the scalar GDP year in captions. |
| `cities[].gdp_by_industry, gdp_estimated` | Three mutually exclusive nominal GDP allocations using Indian state GSVA shares, FY 2025-26 (1 Apr 2025 – 31 Mar 2026). Allocations reconcile to the city's total. Detailed sub-sectors remain in Explorer. |
| `gdp_undisclosed`, national industry GDP and tick | Absent. There is no withheld component in the allocation. The inputs do not supply a matching national GDP series on the same allocation basis. |
| `nation.nation.gdp, population` for GDP and people shares | Existing `cities[].national_shares` divides by NSO FY 2025-26 national nominal GDP and by the Technical Group national projection interpolated to 1 July 2026. |
| `nation.nation.gdp / population` benchmark | MoSPI nominal GDP for FY 2025-26 divided by the national population projection for 1 July 2026, interpolated from Technical Group values. |
| `cities[].employed` | PLFS urban age-15-plus worker-population rates, scaled to the estimated city age-15-plus population. 1 Jul – 30 Sep 2026, IndiaCiv estimate. |
| `cities[].unemployment` and benchmark | PLFS state-urban unemployment, ages 15+, 1 Jul – 30 Sep 2026. Multi-state city values blend state rates. The national comparison uses PLFS all-India urban unemployment ages 15+. |
| `cities[].jobs` and Workforce denominator | PLFS State urban worker composition scaled to the estimated employed population aged 15+, 1 Jul – 30 Sep 2026. No worker counts without an age-aware denominator. |
| `nation.nation.jobs`, `nation.nation.employed` and Workforce location quotient | Absent. The available national sector mix combines rural and urban workers, so it is not used as an urban comparison. |
| `median_income, median_rent, home_value, rent_burden` | Absent. No compatible household-level city or district series in the existing inputs. RBI housing price indices remain in Explorer. |
| `counties.columns, fields, rows` | DataMeet district names, IDs, mapped area and state or UT. Density and population use Census 2011 A-01 totals grown to 1 March 2026 with Technical Group rates. The Census source table is not reproduced. |
| `citizens.cities[id].workforce`, national benchmark and specialist | ORGI B-25 A/B, Census 2011. Eligible occupations for urban member districts compared with eligible urban India workers. Figures normalise eligible categories with available slots and use shares without estimating 2011 headcounts. Explorer retains unclassified occupations. |
| `citizens.cities[id].age`, counts and total | WorldPop mid-2026 grid weights scaled to the projected UN population. Figure bins are under 18, 18–34, 35–64 and 65+. The 15–19 grid bin is split 3:2 at age 18. |
| `citizens.cities[id].age.median` | Absent. The age source indicates a median band, which stays available through existing data consumers. |
| `citizens.cities[id].commute` | ORGI B-28, Census 2011, urban member districts. On foot, bus and train, and other reported transport, among workers with a stated travel mode. Explorer retains the no-travel and unstated shares. |
| `citizens.cities[id].education`, degree headline | ORGI C-08, Census 2011, urban member district residents 25+. Indian attainment bands and degree-or-higher share. Explorer retains the unclassified share. |
| `citizens.cities[id].nativity`, born abroad headline | ORGI D-01, Census 2011, urban member districts. Census state, elsewhere in India and outside India. Explorer retains the unclassifiable share. No US-specific citizenship category. |
| Citizen national age, commute, education and origins comparisons | Absent. No matching benchmark is published in the City View export. |
| `districts.cities[id].emp, top, districts, badge`, `catalog, industries, rule` | Allowlisted civilian jobs and location quotients from Sixth Economic Census (January 2013 – April 2014), via SHRUG v2.2 Pakora and checked 2011 UA joins. Job quantities by industry are derived from the reported shares and civilian denominator. Badge and plaques require the existing IC-67 thresholds. No extrapolation from whole districts into an unmatched UA. |
| `districts.avg_pay, oty_pct, suppressed, lower_bound` | Absent. No like-for-like wage, growth or partial reporting data for the workplace comparisons. |
| `military.json`, Encampment | Absent. No military data are built, requested or displayed. |
| `resources.types, items, cbsa` | Existing civilian GEM energy and mining sites clipped to eligible GHSL footprints using exact site coordinates; largest eligible agglomeration wins a shared site. Every quantity retains the site's own 2026 source and snapshot period. |
| `cities[].peers` | Existing mapped peers by proximity in UN mid-2026 population. Peer links open City View through the upstream handler. Peer metrics use their own periods and omit entire unsupported columns. |
| Hazards and flood history | No upstream City View slot. Existing 2026 hazard lenses and Explorer inventory remain. IFI-Impacts v3 older events have a dated Explorer field and retain lower-bound flags. |
| Wonders, gateways and historical land coverage | No separate upstream City View slot. Existing map layers, Explorer and Almanac entries retain these values and their periods. |
