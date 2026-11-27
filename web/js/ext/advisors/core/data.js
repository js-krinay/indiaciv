import { frameBox, focusPoint } from "./frame.js";
import { formatLensValue } from "../../../ui/lenses.js";

const MARCH = "1 March 2026";
const MID = "Mid-2026";
const PLFS = "1 Jul – 30 Sep 2026";
const SNAPSHOT = "November 2026 inventory";
const TG = "tg_projections";
const UN = "un_wup_cities";
const DM = "datameet";
const LABOUR = "plfs_2026_q3";
const WONDERS = "india_wonders";
const OSM = "osm_transport";
const AQI = "cpcb_city_aqi";
const PM25 = "cpcb_station_pm25";
const HPI = "rbi_hpi_q1_2026";
const VETERANS = ["registered_veterans_pib", "registered_veterans_ksb"];
const BOARDS = "cantonment_boards";

function field(key, label, format, unit, group, period, source, readers, options = {}) {
  return { key, label, format, unit, group, period, source, readers, estimated: false, ...options };
}

function hazardFields(disasters) {
  if (!disasters) return [];
  const types = [...new Set(disasters.events.map((event) => event.type))].sort();
  const make = (key, label, format, read) => field(key, label, format,
    format === "int" ? "documented events" : "event or report date", "Hazards",
    disasters.period, "india_disasters_2026", all(({ hazardSummary }) => read(hazardSummary)),
    { description: disasters.coverage });
  return [
    make("disasters", "Documented hazard events", "int", (row) => row?.count),
    make("disaster_last_date", "Latest hazard date", "text", (row) =>
      row && (row.last_report_only ? `Reported ${row.last_date}` : row.last_date)),
    ...types.map((type) => make(`disaster_${type.toLowerCase()}_count`, `${type} events`, "int",
      (row) => row?.by_type[type])),
  ];
}

const stateOnly = (value) => ({ states: ({ state }) => value(state) });
const cityOnly = (value) => ({ metros: ({ city, profile }) => value(city, profile) });
const districtOnly = (value) => ({ counties: ({ district }) => value(district) });
const all = (read) => ({ states: read, metros: read, counties: read });
const age = (key, label) => field(`age_${key}_count`, label, "int", "people", "People", MID,
  "worldpop_age", cityOnly((_, p) => p?.citizens?.age?.counts?.[key]), {
    estimated: true, provenance: ({ profile }) => profile?.citizens?.age,
    description: "WorldPop age shares within the modelled urban footprint, scaled to the UN city population.",
  });
const work = (key, label, unit, estimate) => field(key, label, estimate ? "int" : "pct",
  unit, "Work", PLFS, LABOUR, cityOnly((city, p) => (p?.citizens?.workforce ?? city.resident_workforce)?.[key]), {
    estimated: estimate,
    provenance: ({ city, profile }) => {
      const record = profile?.citizens?.workforce ?? city?.resident_workforce;
      return record && { period: record.period, source: record.source,
        estimated: estimate || record.states?.length > 1 };
    },
    description: estimate
      ? "Applies state urban PLFS worker-population ratios to the matching projected city population."
      : "PLFS urban benchmark, weighted by the modelled state fragments for cross-state cities.",
  });
const sector = (id, label, estimated) => field(`sector_${id}_${estimated ? "workers" : "share"}`, label,
  estimated ? "int" : "pct", estimated ? "resident workers age 15+" : "share of state urban workers age 15+",
  "Work", PLFS, LABOUR,
  cityOnly((_, p) => p?.citizens?.workforce?.industries?.find((s) => s.sector === id)?.[estimated ? "employed" : "state_urban_share"]), {
    estimated, provenance: ({ profile }) => {
      const record = profile?.citizens?.workforce;
      return record && { period: record.period, source: record.source,
        estimated: estimated || record.states?.length > 1 };
    },
    description: estimated
      ? "City residents allocated across broad industries using the state urban PLFS mix."
      : "Urban PLFS share weighted by estimated worker counts for cross-state cities.",
  });

const typePeriod = {
  gem_power: "September 2026", gem_coal: "August 2026",
  gem_iron: "September 2026", gem_oil_gas: "March 2026",
};
const inventory = (key, label, group, period, source, value, description, format = "int", unit = "mapped sites") =>
  field(key, label, format, unit, group, period, source, all(({ sites }) => value(sites)), { description });
const tradeGatewaySources = [OSM, "pib_dfc_completion", "cwprs_port_locations", DM];
const tradeGatewayField = (key, label, read, format, unit) =>
  field(key, label, format, unit, "Commerce", SNAPSHOT, tradeGatewaySources, {
    states: ({ tradeGateways }) => tradeGateways && read(tradeGateways),
    metros: ({ tradeGateways }) => tradeGateways && read(tradeGateways),
  }, { description: "Major ports and dedicated freight corridors on state or UT tiles. City ports use the urban footprint, and corridors also use adjacent tiles." });

const counted = (key, label, group, source, category, predicate = () => true) =>
  inventory(key, label, group, SNAPSHOT, source,
    (sites) => sites[category]?.filter(predicate).length,
    "Count within the served inventory and the available mapped geography.");
const parkSources = ["wii_protected", "osm_protected", "wikidata_protected"];
const researchWonderSources = ["research_campuses", "research_points"];
const shared = (key, label, format, unit, group, readers, options) =>
  field(key, label, format, unit, group, MARCH, TG, readers, options);

const cityRecord = (key, label, format, unit, group, period, source, record, value, options = {}) =>
  field(key, label, format, unit, group, period, source, cityOnly((_, profile) => value(record(profile))), {
    ...options,
    provenance: ({ profile }) => {
      const detail = record(profile);
      return detail && { ...detail, status: detail.provisional ? "Provisional" : detail.status };
    },
  });
const airField = (key, label, format, unit, series, metric, options) =>
  cityRecord(key, label, format, unit, "Air & weather", "Jan–Oct 2026", series === "aqi" ? AQI : PM25,
    (profile) => profile?.air?.[series], (record) => record?.[metric], options);
const housingField = (key, label, format, unit, value) =>
  cityRecord(key, label, format, unit, "Housing", "Apr–Jun 2026", HPI, (profile) => profile?.housing, value,
    { description: "RBI registration-market index (base = 100)." });

const FY26 = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)";
const finances = (key, label, format, unit, rank = false) =>
  cityRecord(key, label, format, unit, "Economy", FY26, "gsdp_fy26",
    (p) => p?.economy, (r) => rank ? r?.ranks[key.replace(/_rank$/, "")] : r?.[key],
    { estimated: true, description: "Nominal state output allocated by projected urban population. GDP per resident uses the UN mid-2026 projection." });
const gsvaShare = (key, label) => {
  const record = ({ state, city }) => state?.sector_mix ?? city?.state_sector_mix;
  const read = (place) => record(place)?.shares[key];
  return field(`gsva_${key}_share`, label, "pct", "share of nominal state GSVA", "Economy", FY26,
    "mospi_national_gva_fy26", { states: read, metros: read }, {
      provenance: record, description: "Share of the state’s total nominal GSVA. Cities show their primary state here.",
    });
};
const outputField = (key, label, format, unit, readRecord, readValue) =>
  field(key, label, format, unit, "Economy", FY26, "gsdp_fy26",
    cityOnly((city) => readValue(readRecord(city), city)), {
      estimated: true, provenance: ({ city }) => city && readRecord(city),
    });
const gateway = (key, label, get, source, distance = false) =>
  cityRecord(key, label, distance ? "int" : "text", distance ? "km" : "gateway", "Commerce", SNAPSHOT,
    source, get, (r) => r?.[distance ? "distance_km" : "name"],
    { description: "Nearest mapped gateway in this class, by straight-line map distance from the city centre." });

function yieldFields(definitions) {
  return definitions.flatMap((y) => {
    const provenance = ({ state, city }) => (state || city)?.yield_meta?.[y.key];
    return [
      field(`yield_${y.key}`, `${y.label} yield`, y.unit === "INR" ? "inr" : "float", y.unit, "Economy",
        y.period, y.sources, {
          ...(y.key === "gold" ? {} : stateOnly((s) => s?.yields?.[y.key])),
          ...cityOnly((c) => c.yields?.[y.key]),
        },
        { provenance, description: y.description }),
      field(`yield_${y.key}_rank`, `${y.label} yield rank`, "int", "rank among City View cities", "Economy",
        y.period, y.sources, cityOnly((_, p) => p?.economy?.ranks[y.key]), { provenance }),
    ];
  });
}

// Add a definition here for fields with bespoke joins. State metrics use their producer's lens definitions.
const portTradeField = (key, label) => field(`port_${key}`, label, "pct", "share of major-port cargo",
  "Commerce", FY26, "mopsw_port_cargo", all(({ sites }) => {
    const cargo = (sites.ports || []).map((p) => p.cargo).filter((c) => c?.share > 0);
    const total = cargo.reduce((sum, c) => sum + c.share, 0);
    return total ? cargo.reduce((sum, c) => sum + c.share * c[key], 0) / total : null;
  }), { description: "Cargo-weighted share for mapped major port authorities in the area. Ministry advance estimates." });
const transportLabels = (key, label, source, category, labels, description) =>
  inventory(key, label, "Commerce", SNAPSHOT, source, (sites) => {
    const values = [...new Set(sites[category]?.map(labels).filter(Boolean))].sort();
    return values.length ? values.join(", ") : null;
  }, description, "text", "mapped labels");

export const FIELDS = [
  field("employed", "Employed residents", "int", "people", "Work", PLFS, [LABOUR, TG],
    stateOnly((s) => s?.employed), {
      estimated: true, description: "All-ages PLFS worker-population ratio applied to the projected 1 March 2026 population.",
    }),
  field("state_gsdp", "Nominal GSDP", "inr", "INR", "Economy", FY26, "gsdp_fy26",
    stateOnly((s) => s?.yields?.gold), {
      provenance: ({ state }) => state?.yield_meta?.gold,
      description: "Nominal output at current prices. Where required, the latest available GSDP is grown at India's nominal GDP growth rate.",
    }),
  field("internet_per_100", "Internet subscriptions per 100 residents", "decimal1", "subscriptions per 100 residents",
    "Daily life", "30 June 2026", ["trai_internet_june_2026", TG],
    stateOnly((s) => s?.metrics?.internet_per_100?.value ?? s?.internet_per_100), {
      lens: "internet_per_100", estimated: true,
      description: "June subscriptions divided by the projected 1 March 2026 population. Includes all access types.",
    }),
  field("kind", "Place type", "text", "UN geography", "Geography", MID, UN,
    cityOnly((city) => city.metro ? "Urban agglomeration" : null)),
  field("n_districts", "Districts in modelled footprint", "int", "districts", "Geography",
    "Current modelled footprint", ["city_footprints", DM],
    { metros: ({ memberDistricts }) => memberDistricts?.length }),
  field("plaque_count", "Documented industry clusters", "int", "reviewed clusters", "Work", "2026 evidence", "stpi_2026",
    cityOnly((_, profile) => profile?.industry_plaques?.length || null), {
      provenance: ({ profile }) => inventoryProvenance(profile?.industry_plaques),
    }),
  field("metro", "Overlapping modelled UAs", "text", "urban agglomerations", "Geography",
    "Current modelled footprint", ["city_footprints", DM],
    { counties: ({ memberCities }) => memberCities?.map((c) => c.name).join(" · ") || null }),
  field("districts", "Documented industry clusters", "text", "reviewed clusters", "Work", "2026 evidence", "stpi_2026",
    { counties: ({ plaques }) => plaques?.length ? [...new Set(plaques.map((p) => p.label))].join(" · ") : null },
    { provenance: ({ plaques }) => inventoryProvenance(plaques) }),
  field("crop_presence", "Mapped crop presence", "text", "documented crops", "Land", "2026 evidence", "tea_regions",
    all(({ sites }) => {
      const crops = sites.resources?.filter((r) => r.meta.category === "agri");
      return crops?.length ? [...new Set(crops.map((r) => r.meta.name))].sort().join(" · ") : null;
    }), {
      provenance: ({ sites }) => inventoryProvenance(sites.resources?.filter((r) => r.meta.category === "agri")),
      description: "Selected growing areas and representative markers in the atlas.",
    }),
  inventory("protected_count", "Mapped protected designations", "Land", "October–November 2026 inventory",
    ["osm_protected", "rsis_protected", "wikidata_protected", "wii_protected", "ntca_protected"],
    (sites) => sites.protected?.length, "Mapped designation markers within the referenced geography. Distinct designations can overlap."),
  outputField("gdp", "Estimated city GDP", "inr", "INR", (c) => c.yield_meta?.gold, (_, c) => c.yields?.gold),
  finances("gdp_per_resident", "Estimated city GDP per resident", "inr", "INR per resident"),
  field("gdp_rank", "City GDP rank", "int", "rank among mapped urban agglomerations", "Economy", FY26, "gsdp_fy26",
    cityOnly((city) => city.ranks?.gdp), { estimated: true, provenance: ({ city }) => city?.yield_meta?.gold }),
  finances("gdp_per_resident_rank", "City GDP per resident rank", "int", "rank among City View cities", true),
  gsvaShare("agriculture", "State GSVA · Agriculture & allied"),
  gsvaShare("industry", "State GSVA · Industry"),
  gsvaShare("services", "State GSVA · Services"),
  ...Object.entries({ agriculture: "Agriculture & allied", industry: "Industry", services: "Services",
    mining: "Mining & quarrying", manufacturing: "Manufacturing", construction: "Construction", utilities: "Utilities" })
    .map(([key, label]) => outputField(`gdp_${key}`, `City GDP · ${label}`, "inr", "INR",
      (c) => c.sector_output, (r) => r?.values[key])),
  outputField("economic_growth", "Nominal city output growth", "pct", "%", (c) => c.output_growth, (r) => r?.value),
  outputField("share_national_gdp", "Share of India’s GDP", "pct", "%", (c) => c.national_shares?.gdp, (r) => r?.value),
  outputField("share_national_population", "Share of India’s population", "pct", "%",
    (c) => c.national_shares?.population, (r) => r?.value),
  cityRecord("age_midlife_count", "Residents aged 35–64", "int", "people", "People", MID, "worldpop_age",
    (p) => p?.citizens?.age, (r) => r?.bands?.midlife, { estimated: true }),
  cityRecord("member_district_count", "Member districts", "int", "districts", "Geography", SNAPSHOT, "city_footprints",
    (p) => p?.method === "ghsl" ? p : null, (p) => p?.districts.length),
  ...Object.entries({ campus: "Campus", harbor: "Harbor", aerodrome: "Aerodrome", government_plaza: "Government plaza" })
    .map(([key, label]) => cityRecord(`district_${key}`, `${label} districts`, "int", "districts", "Geography", SNAPSHOT,
      { campus: "research_points", harbor: ["cwprs_port_locations", "featured_port_locations"],
        aerodrome: "ourairports", government_plaza: "soi_political_map" }[key],
      (p) => p?.method === "ghsl" ? { badges: p.district_badges } : null,
      (r) => r?.badges?.filter((b) => b.kind === key).length)),
  gateway("nearest_major_port", "Nearest major port", (p) => p?.gateways?.port, "cwprs_port_locations"),
  gateway("nearest_major_port_km", "Distance to nearest major port", (p) => p?.gateways?.port, "cwprs_port_locations", true),
  ...["large", "medium", "small"].flatMap((size) => [
    gateway(`nearest_${size}_airport`, `Nearest ${size} airport with scheduled service`,
      (p) => p?.gateways?.airports[size], "ourairports"),
    gateway(`nearest_${size}_airport_km`, `Distance to nearest ${size} airport with scheduled service`,
      (p) => p?.gateways?.airports[size], "ourairports", true),
  ]),
  ...[["rail", "Rail", false], ["freight", "Freight rail", true]].map(([key, label, freight]) =>
    field(`city_${key}_corridors`, `${label} corridors`, "text", "mapped corridors", "Commerce", SNAPSHOT, OSM,
      cityOnly((_, p) => p?.gateways?.rail.filter((r) => !r.main_line && r.freight === freight)
        .map((r) => `${r.name} (${r.distance_km} km)`).join(" · ") || null),
      { provenance: ({ profile }) => profile?.gateways?.rail.find((r) => !r.main_line && r.freight === freight),
        description: "Named corridors within one grid cell of the footprint. Distances are measured from the city centre to the mapped alignment." })),
  gateway("nearest_main_line", "Main line near city", (p) => p?.gateways?.rail.find((r) => r.main_line), OSM),
  gateway("nearest_main_line_km", "Distance to main line near city", (p) => p?.gateways?.rail.find((r) => r.main_line), OSM, true),
  field("name", "Place", "text", "place name", "Geography", SNAPSHOT, DM, all(({ name }) => name), {
    provenance: ({ city }) => city && { source: UN },
  }),
  field("state", "State / UT", "text", "state or UT code", "Geography", SNAPSHOT, DM, {
    metros: ({ city }) => city.states?.join(" · "), counties: ({ district }) => district?.state,
  }),
  field("city_view", "City View", "text", "availability", "Geography", SNAPSHOT, UN,
    cityOnly((city) => city.city_view ? "Available" : null)),
  field("capital", "Capital", "text", "designation", "Geography", SNAPSHOT, UN,
    cityOnly((city) => city.capital ? "National capital" : null)),
  shared("population", "Population", "int", "people", "People", {
    states: ({ state }) => state?.population, metros: ({ city }) => city.population,
    counties: ({ district }) => district?.population,
  }, {
    provenance: ({ city, district }) => city ? { source: UN, period: MID } :
      district ? { estimated: true, description: "District census totals scaled by the state projection's population change through March 2026." } : null,
  }),
  shared("density", "Population density", "float", "people / km²", "People", {
    states: ({ state }) => state?.profile?.density,
    metros: ({ city, area }) => area ? city.population / area : null,
    counties: ({ district }) => district?.density,
  }, {
    provenance: ({ city, district }) => city ? { source: [UN, "city_footprints"], period: MID, estimated: true } :
      district ? { lens: "density", estimated: true } : { lens: "state_density" },
    description: "Projected residents divided by mapped area. District and state areas each come from their own DataMeet boundaries.",
  }),
  field("area_km2", "Mapped area", "km2", "km²", "Land", "Current mapped geography", DM,
    { ...stateOnly((s) => s?.area_km2), metros: ({ area }) => area, ...districtOnly((d) => d?.area_km2) },
    {
      description: "Area measured in the equal-area projection from each state's or district's own DataMeet boundary rings.",
      provenance: ({ city }) => city && { source: "city_footprints", period: "Current modelled footprint",
        description: "Area of the clipped GHSL proxy for the UN urban agglomeration, from its fractions of atlas hexes." },
    }),
  field("population_rank", "Atlas population rank", "int", "rank among mapped cities", "People", MID, UN,
    cityOnly((city) => city.ranks?.population)),
  field("city_type", "Agglomeration size class", "text", "UN population class", "People", MID, UN,
    cityOnly((city) => city.population >= 1e6 ? "Million-plus" : "Under one million"),
    { description: "UN DESA size threshold applied to the mid-2026 projected population." }),
  shared("projected_growth", "Population growth", "signed", "%", "People", {
    states: ({ state, lenses }) => lenses.get("growth")?.period ? state?.profile?.growth : null,
    metros: ({ city, lenses }) => lenses.get("city_growth")?.period ? city.projected_growth : null,
  }, {
    provenance: ({ city, lenses }) => {
      const lens = city ? "city_growth" : "growth";
      return { ...lenses.get(lens), lens };
    },
  }),
  ...[
    ["sex_ratio", "Sex ratio", "int", "women per 1,000 men", "sex_ratio"],
    ["age_0_14", "Aged 0–14", "pct", "share of residents", "children"],
    ["age_60", "Aged 60+", "pct", "share of residents", "elderly"],
    ["median_age", "Median age", "years", "years", "median_age"],
    ["tfr", "Fertility", "float", "children per woman", "fertility"],
    ["imr", "Infant mortality", "float", "deaths per 1,000 births", "infant_mortality"],
    ["life_female", "Life expectancy of women", "years", "years", "life_female"],
    ["life_male", "Life expectancy of men", "years", "years", "life_male"],
  ].map(([key, label, format, unit, lens]) => {
    const isAge = ["age_0_14", "age_60", "median_age"].includes(key);
    const forecast = ["tfr", "imr", "life_female", "life_male"].includes(key);
    return shared(key, label, format, unit, forecast ? "Health" : "People", {
      states: ({ state, lenses }) => {
        const value = forecast && !lenses.get(lens)?.period ? null : state?.profile?.[key];
        return format === "pct" && value != null ? value / 100 : value;
      },
      ...(key === "median_age" ? { counties: ({ district }) => district?.median_age } : {}),
    }, {
      ...(key === "median_age" ? {} : { lens }),
      provenance: ({ state, district, lenses }) => {
        if (district) return district.provenance?.[key];
        return isAge && state?.age_source
          ? { source: state.age_source, period: "2026", estimated: true, lens }
          : { ...lenses.get(lens), lens };
      },
    });
  }),
  age("0_14", "Residents aged 0–14"), age("15_59", "Residents aged 15–59"), age("60_plus", "Residents aged 60+"),
  field("median_age_band", "Median age band", "text", "years", "People", MID,
    "worldpop_age", cityOnly((_, p) => {
      const band = p?.citizens?.age?.median_band;
      return band ? (band[1] == null ? `${band[0]}+` : band.join("–")) : null;
    }), { estimated: true, provenance: ({ profile }) => profile?.citizens?.age }),
  work("employed_all_ages", "Employed residents", "people", true),
  work("employed_15_plus", "Employed residents aged 15+", "people", true),
  field("population_15_plus", "Residents aged 15+", "int", "people", "People", MID,
    "worldpop_age", cityOnly((_, p) => p?.citizens?.workforce?.population_15_plus),
    { estimated: true, provenance: ({ profile }) => profile?.citizens?.age }),
  work("state_urban_wpr_all_ages", "Urban worker-population ratio benchmark (all ages)", "share of residents", false),
  work("state_urban_wpr_15_plus", "Urban worker-population ratio benchmark (15+)", "share of residents age 15+", false),
  work("state_urban_unemployment_15_plus", "Urban unemployment benchmark (15+)", "share of labour force age 15+", false),
  ...[["agriculture", "Agriculture"], ["industry", "Industry"], ["services", "Services"]].flatMap(([id, label]) => [
    sector(id, `${label} workers`, true), sector(id, `${label} share (state urban)`, false),
  ]),
  field("industry_plaques", "Documented industry clusters", "text", "cluster names", "Work", "2026 evidence", "stpi_2026",
    cityOnly((_, p) => p?.industry_plaques?.map((r) => r.label).join(" · ") || null), {
      provenance: ({ profile }) => {
        const records = profile?.industry_plaques || [];
        return {
          source: [...new Set(records.map((r) => r.source))],
          period: [...new Set(records.map((r) => r.period))].join(" · "),
          estimated: records.some((r) => r.estimated),
        };
      },
    }),
  field("footprint_districts", "Districts in the modelled footprint", "text", "district names", "Geography",
    "Current modelled footprint", ["city_footprints", DM],
    { metros: ({ memberDistricts }) => memberDistricts?.join(" · ") || null }),
  field("worldpop_district_population", "WorldPop district population", "int", "people", "People", MID,
    "city_population_grid", { counties: ({ worldpop }) => worldpop },
    { estimated: true, description: "Sum of population grid pixel centres within the district. Available for districts intersecting the modelled City View footprints." }),
  field("city_bad_air", "Poor or worse AQI days", "pct", "share of reported days", "Air & weather", "Jan–Oct 2026",
    "cpcb_city_aqi", { metros: ({ city, lenses }) => lenses.get("city_bad_air")?.city_values?.[city.id] },
    { lens: "city_bad_air", provenance: ({ lenses }) => lenses.get("city_bad_air"), description: "Reported days with AQI of 201 or higher, using qualifying city series." }),
  airField("city_bad_air_days", "Bad-air days", "int", "days with AQI ≥201", "aqi", "bad_days"),
  airField("city_air_valid_days", "Valid AQI days", "int", "reported days", "aqi", "valid_days"),
  airField("city_air_coverage_days", "AQI reporting window", "int", "calendar days", "aqi", "calendar_days"),
  airField("city_air_rank", "Bad-air rank", "int", "national rank among eligible series", "aqi", "rank",
    { description: "Highest share of bad-air days ranks first. Equal shares tie." }),
  airField("city_air_rank_cities", "Cities in AQI ranking", "int", "eligible city series", "aqi", "covered_cities"),
  airField("city_footprint_pm25", "Urban footprint PM₂.₅", "decimal1", "µg/m³", "pm25", "value",
    { estimated: true, description: "Area-weighted mean over footprint districts with PM₂.₅ estimates." }),
  airField("city_footprint_pm25_coverage", "Footprint PM₂.₅ coverage", "pct", "share of footprint area",
    "pm25", "footprint_coverage", { estimated: true }),
  field("city_hazards", "Documented hazards", "text", "selected member-district incidents", "Hazards", "2026", [],
    cityOnly((_, profile) => profile?.hazards?.map((event) => `${event.label} (${event.type})`).join(" · ") || null), {
      provenance: ({ profile }) => {
        const events = profile?.hazards;
        if (!events?.length) return null;
        const dates = events.map(({ start_date: start, end_date: end, reported_on: reported }) =>
          start ? (end ? `${start} – ${end}` : start) : `Reported ${reported}`);
        return { period: [...new Set(dates)].join(" · "), source: [...new Set(events.map((event) => event.source))] };
      },
    }),
  housingField("city_housing_market", "RBI housing market", "text", "registration market", (record) => record?.market),
  housingField("city_housing_index", "House Price Index", "decimal2", "index points",
    (record) => record?.index == null ? null : Number(record.index)),
  housingField("city_housing_yoy", "Annual house price change", "signed", "% change from a year earlier",
    (record) => record?.yoy_pct == null ? null : Number(record.yoy_pct) / 100),
  field("district_pm25", "District PM₂.₅", "float", "µg/m³", "Air & weather", "Jan–Oct 2026",
    "cpcb_station_pm25", { counties: ({ district }) => district?.district_pm25 }, {
      lens: "district_pm25", estimated: true, provenance: ({ lenses }) => lenses.get("district_pm25"),
      description: "Inverse-distance-squared weighting of eligible monitors within 150 km of the district centroid.",
    }),
  field("monsoon_2026", "Monsoon rainfall band", "text", "band", "Air & weather", "Jun–Sep 2026",
    "imd_monsoon", { metros: ({ city, lenses }) => {
      const lens = lenses.get("monsoon_2026");
      const value = lens?.values?.[city.cell];
      return value == null ? null : formatLensValue(lens, value);
    }, counties: ({ district, lenses }) => {
      const value = district?.monsoon_2026;
      return value == null ? null : formatLensValue(lenses.get("monsoon_2026"), value);
    } }, { lens: "monsoon_2026", provenance: ({ lenses }) => lenses.get("monsoon_2026"), description: "IndiaCiv rainfall band for the subdivision sampled at the place's map centre." }),
  field("protected_share", "Mapped protected share", "pct", "share of area", "Geography", "2026 snapshots",
    ["osm_protected", "rsis_protected", DM], {
      states: ({ protectedShare }) => protectedShare,
      counties: ({ protectedShare }) => protectedShare,
    }, { description: "Share of the DataMeet unit covered by available mapped Ramsar, park and tiger reserve extents, counting overlaps once." }),
  counted("wonders_count", "Mapped wonders", "Culture", WONDERS, "wonders"),
  counted("landmark_count", "Built wonders", "Culture", WONDERS, "wonders", (w) => w.kind === "landmark"),
  counted("natural_wonders_count", "Natural wonders", "Culture", WONDERS, "wonders", (w) => w.kind === "natural"),
  counted("park_wonders_count", "Largest-area national park wonders", "Culture", parkSources, "wonders",
    (w) => w.rule === "national_park"),
  counted("research_wonders_count", "Mapped research wonders", "Culture", researchWonderSources, "wonders",
    (w) => w.rule === "research_inventory"),
  inventory("park_wonder_area_ranks", "National park area ranks", "Culture", SNAPSHOT, parkSources,
    ({ wonders }) => wonders?.filter((w) => w.rule === "national_park")
      .map((w) => `#${w.rank} ${w.name}`).join(" · ") || null,
    "Order by published area within the five largest parks in the WII inventory.", "text", "rank and name"),
  inventory("wonder_extent_count", "Wonders with mapped protected extent", "Culture", SNAPSHOT,
    ["osm_protected", "rsis_protected"], ({ wonders }) => wonders?.filter((w) => w.cells?.length).length,
    "Wonders linked to protected-land hexes from accepted extents."),
  inventory("protected_official_areas", "Official protected site areas", "Land", "October–November 2026 inventory",
    ["rsis_protected", "wii_protected", "ntca_protected"], ({ protected: sites }) =>
      sites?.filter((site) => Number.isFinite(site.area_ha)).map((site) =>
        `${site.name} · ${(site.area_ha / 100).toLocaleString("en-IN", { maximumFractionDigits: 4 })} km² · ${site.status} · ${site.authority}`
      ).join(" | ") || null,
    "Official areas at mapped sites. Distinct protected designations can overlap.", "text", "km² per designation"),
  tradeGatewayField("trade_gateways", "Trade gateways", (names) => names.join(" · ") || null, "text", "gateway names"),
  tradeGatewayField("trade_gateway_count", "Mapped trade gateways", (names) => names.length, "int", "gateways"),
  portTradeField("foreign", "Overseas port cargo"),
  portTradeField("domestic", "Coastal port cargo"),
  field("major_port_rank", "Best major-port cargo rank", "int", "rank among 12 authorities", "Commerce",
    FY26, "mopsw_port_cargo", all(({ sites }) => {
      const ranks = (sites.ports || []).filter((p) => Number.isFinite(p.rank)).map((p) => p.rank);
      return ranks.length ? Math.min(...ranks) : null;
    }), { description: "Lowest national cargo rank among mapped major port authorities in the area." }),
  ...[["roads", "Highway"], ["rail", "Railway"]].flatMap(([category, label]) =>
    [["names", 4, "names"], ["networks", 5, "network tags"]].map(([key, index, title]) =>
      transportLabels(`${category}_${key}`, `${label} ${title}`, OSM, category, (r) => r[index],
        "Labels from tagged OpenStreetMap ways in the area."))),
  transportLabels("port_cities", "Port localities", ["cwprs_port_locations", "featured_port_locations"],
    "ports", (p) => p.city, "Documented facility localities of major and featured ports."),
  transportLabels("port_states", "Port states and UTs", DM, "ports", (p) => p.state,
    "DataMeet state or union territory at the facility, with a coastal placement fallback."),
  transportLabels("airport_cities", "Airport municipalities", "ourairports", "airports", (p) => p.city,
    "Municipality in the civilian OurAirports inventory."),
  transportLabels("airport_states", "Airport states and UTs", DM, "airports", (p) => p.state,
    "DataMeet state or union territory at the airport coordinates."),
  counted("port_count", "Mapped ports", "Commerce", [OSM, "cwprs_port_locations", "featured_port_locations"], "ports"),
  counted("airport_count", "Mapped airports", "Commerce", "ourairports", "airports"),
  counted("rail_links", "Mapped rail links", "Commerce", OSM, "rail"),
  counted("highway_links", "Mapped highway links", "Commerce", OSM, "roads"),
  inventory("energy_mw", "Mapped generating capacity", "Energy", typePeriod.gem_power, "gem_power",
    ({ resources }) => sum(resources?.filter((r) => r.meta.unit === "MW").map((r) => r.value)),
    "Rated capacity of operating sites in the mapped inventory, subject to each technology’s threshold.", "mw", "MW"),
  { ...inventory("mines_count", "Mapped mines", "Energy", "2026 inventory", ["gem_coal", "gem_iron"],
    ({ resources }) => resources?.filter((r) => r.meta.category === "mineral").length,
    "Selected operating mines in the map inventory."),
    provenance: ({ sites }) => inventoryProvenance(sites.resources?.filter((r) => r.meta.category === "mineral")),
  },
  inventory("oil_gas_count", "Mapped oil and gas fields", "Energy", typePeriod.gem_oil_gas, "gem_oil_gas",
    ({ resources }) => resources?.filter((r) => r.meta.source === "gem_oil_gas").length,
    "Mapped operating extraction fields."),
];

function sum(values) {
  const known = values?.filter(Number.isFinite);
  return known?.length ? known.reduce((a, b) => a + b, 0) : null;
}

function inventoryProvenance(records, period = (r) => r.period) {
  if (!records?.length) return null;
  return {
    source: [...new Set(records.map((r) => r.source))],
    period: [...new Set(records.map(period))].sort().join(" · "),
    estimated: records.some((r) => r.estimated),
  };
}

export const PORT_CARGO = { label: "Major-port cargo by authority", format: "pct", unit: "share of cargo across 12 authorities" };

function resourceFields(types) {
  const silver = types.find((type) => type.id === "lead_zinc");
  const definitions = silver ? [...types, { ...silver, id: "silver", name: "Silver by-product", unit: null,
    description: "Verified silver by-product at mapped lead-zinc mines." }] : types;
  return definitions.flatMap((type) => {
    const period = type.period || typePeriod[type.source] || SNAPSHOT;
    const matching = (items) => items?.filter((r) => r.type === type.id || r.byproducts?.includes(type.id));
    const fields = [inventory(`resource_${type.id}_count`, type.name + " sites", "Energy", period, type.source,
      ({ resources }) => matching(resources)?.length, type.description)];
    fields[0].group = type.category === "agri" ? "Crops" : "Resources";
    fields[0].provenance = ({ sites }) => {
      const records = matching(sites.resources) || [];
      return {
        period: [...new Set(records.map((r) => r.period).filter(Boolean))].join(" · "),
        source: records.length ? [...new Set(records.map((r) => r.source || type.source))] : type.source,
        estimated: records.some((r) => r.estimated),
      };
    };
    if (type.unit === "MW") fields.push(inventory(`resource_${type.id}_mw`, type.name + " capacity", "Energy", period, type.source,
      ({ resources }) => sum(matching(resources)?.map((r) => r.value)), type.description, "mw", "MW"));
    if (type.unit === "Mt/yr") fields.push(inventory(`resource_${type.id}_capacity`, type.name + " capacity", "Energy", period,
      type.source, ({ resources }) => sum(matching(resources)?.map((r) => r.value)), type.description,
      "float", "million metric tonnes per year"));
    return fields;
  });
}

const metricsGroup = { labour: "Work", prosperity: "Prosperity", daily_life: "Daily life", energy: "Energy",
  schemes: "Public schemes" };

function stateMetricFields(lenses, states) {
  const ids = new Set(states.flatMap((row) => Object.keys(row.metrics || {})));
  return [...ids].flatMap((key) => {
    if (key === "internet_per_100") return [];
    const lens = lenses.get(key);
    if (!lens?.period || !lens.source) return [];
    const format = lens.unit.includes("₹") || lens.unit.includes("INR") ? "inr"
      : lens.group === "schemes" ? `decimal${lens.precision}` : lens.format;
    const source = lens.denominator_source ? [lens.source, lens.denominator_source] : lens.source;
    return [field(key, lens.name, format, lens.unit, metricsGroup[lens.group] || "State metrics",
      lens.period, source, stateOnly((s) => s?.metrics?.[key]?.value), {
        description: lens.description, lens: key,
        provenance: ({ state }) => {
          const record = state?.metrics?.[key];
          return record && lens.denominator_source ? { ...record, source: [record.source, lens.denominator_source] } : record;
        },
      })];
  });
}

const resourceKey = (r) => JSON.stringify([r.type, r.name, r.x, r.y]);

function indexCells(owners) {
  const index = new Map();
  owners.forEach((id, cell) => {
    if (id < 0) return;
    if (!index.has(id)) index.set(id, []);
    index.get(id).push(cell);
  });
  return index;
}

function atPlaces(items, placeKeys) {
  const byKey = new Map();
  for (const item of items) {
    for (const key of new Set(placeKeys(item))) {
      if (key == null) continue;
      if (!byKey.has(key)) byKey.set(key, []);
      byKey.get(key).push(item);
    }
  }
  return byKey;
}

function siteIndex(raw, stateAt, districtAt, citiesAt) {
  const { resources, wonders, infrastructure } = raw;
  const types = new Map((resources?.types || []).map((t) => [t.id, t]));
  const sites = {
    protected: raw.protectedLand && [
      ...raw.protectedLand.sites.filter((r) => !r.ramsar_id), ...(raw.protectedRamsar?.sites || []),
    ].filter((r) => Number.isInteger(r.cell) && r.cell >= 0),
    resources: resources?.items.map((r) => ({ ...r, meta: types.get(r.type) })).filter((r) => r.meta),
    wonders: wonders?.wonders.filter((w) => !w.foreign_side),
    ports: infrastructure?.ports, airports: infrastructure?.airports,
    rail: infrastructure?.rail, roads: infrastructure?.roads,
  };
  const indexes = Object.fromEntries(Object.entries(sites).map(([key, items]) => {
    if (!items) return [key, null];
    const cells = (item) => Array.isArray(item) ? item.slice(0, 2) : [item.cell];
    return [key, {
      states: atPlaces(items, (r) => {
        const state = r.state_source_id ? r.state_abbr : r.state;
        return state ? [state] : cells(r).map(stateAt);
      }),
      counties: atPlaces(items, (r) => cells(r).map(districtAt)),
      metros: atPlaces(items, (r) => cells(r).flatMap(citiesAt)),
    }];
  }));
  const resourcesByKey = new Map((sites.resources || []).map((r) => [resourceKey(r), r]));
  const wondersByKey = new Map((sites.wonders || []).map((w) => [w.id, w]));
  function forPlace(level, key, profile, comparable, districtSites) {
    const out = Object.fromEntries(Object.entries(indexes).map(([id, index]) =>
      [id, comparable && index ? index[level].get(key) || [] : null]));
    if (level === "metros" && profile?.method === "ghsl") {
      out.resources = resources && profile.resources?.map((key) => resourcesByKey.get(JSON.stringify(key))).filter(Boolean);
      out.wonders = wonders && profile.wonders?.map((id) => wondersByKey.get(id)).filter(Boolean);
    }
    if (districtSites) {
      out.resources = resources && districtSites.resources.map((i) => resources.items[i]).filter(Boolean)
        .map((r) => ({ ...r, meta: types.get(r.type) })).filter((r) => r.meta);
      out.wonders = wonders && districtSites.wonders.map((id) => wondersByKey.get(id)).filter(Boolean);
    }
    return out;
  }
  return { forPlace, sites };
}

function makeLevel(id, label, noun, places, fields, geography) {
  const columns = fields.filter((f) => f.readers[id]);
  const rows = places.map(({ key, name, sub, ref, ...place }) => {
    place.name = name;
    const v = Object.fromEntries(columns.map((f) => [f.key, f.readers[id](place) ?? null]));
    return { key, name, sub, ref, level: id, v, place };
  });
  const fieldByKey = new Map(columns.map((f) => [f.key, f]));
  const byKey = new Map(rows.map((r) => [r.key, r]));
  return {
    id, label, noun, rows, byKey, fields: columns, ...geography,
    field: (key) => fieldByKey.get(key),
    rowAtCell: (cell) => byKey.get(geography.keyAt(cell)) || null,
    meta: (f, row) => {
      const place = row?.place;
      const producer = (place?.city || place?.state || place?.district)?.provenance?.[f.key];
      const detail = { ...(place && f.provenance?.(place)), ...producer };
      return { ...f, period: detail?.period || f.period, source: detail?.source || f.source,
        estimated: detail?.estimated ?? f.estimated, status: detail?.status, lens: detail?.lens || f.lens,
        description: [detail?.description || f.description, detail?.coverage].filter(Boolean).join(" · ") };
    },
  };
}

function researchFields(nation) {
  const science = nation?.yields?.find((row) => row.key === "science");
  if (!science) return [];
  const places = (read) => ({ ...stateOnly(read), ...cityOnly(read) });
  const meta = ({ state, city }) => (state || city)?.yield_meta?.science;
  const options = { provenance: meta, description: science.description };
  return [
    field("science_points", "Science points", "int", "points", "Knowledge", science.period, science.sources,
      places((place) => place?.yields?.science), options),
    ...["IIT", "IISc", "IISER", "NIT", "AIIMS", "AIIMS under development", "CSIR", "ISRO and DoS"].map((kind) =>
      field(`science_${kind.toLowerCase().replaceAll(" ", "_")}`, kind, "int", "institutions", "Knowledge",
        science.period, science.sources, places((place) => {
          const counts = place?.yield_meta?.science?.components;
          return counts ? counts[kind] ?? 0 : null;
        }), options)),
  ];
}

const advisorFields = [
  ...[
    ["agriculture", "Agriculture sector"],
    ["secondary", "Secondary sector, mining and quarrying"],
    ["tertiary", "Tertiary sector"],
  ].map(([id, label], index) => field(`industry_${id}_share`, label, "pct", "share of workers age 15+", "Work",
    PLFS, LABOUR, stateOnly((state) => {
      const value = state?.advisor_statistics?.industry?.[index];
      return value == null ? null : value / 100;
    }), { description: "PLFS Current Weekly Status, rural and urban persons combined, selected states." })),
  field("cantonment_boards", "Listed cantonment boards", "int", "civic boards", "Defence & veterans",
    "Directory checked 27 Nov 2026", BOARDS, stateOnly((state) => state?.advisor_statistics?.cantonment_boards)),
  field("civic_offices", "Verified cantonment board offices", "text", "public civic offices", "Defence & veterans",
    "Directory checked 27 Nov 2026", [BOARDS, "civic_office_points"],
    cityOnly((_, profile) => profile?.civic_offices?.join(", ")), {
      description: "Selected public offices verified inside the modelled urban footprint.",
    }),
  field("civic_office_count", "Mapped cantonment board offices", "int", "public civic offices", "Defence & veterans",
    "Directory checked 27 Nov 2026", [BOARDS, "civic_office_points"],
    cityOnly((_, profile) => profile?.civic_offices?.length), {
      description: "Count of selected public offices inside the modelled urban footprint. Blank where no office was verified.",
    }),
  field("registered_veterans", "Registered ex-servicemen", "int", "people", "Defence & veterans",
    "30 Jun 2026", VETERANS, {
      ...stateOnly((state) => state?.advisor_statistics?.registered_veterans),
      ...districtOnly((district) => district?.registered_veterans),
    }, {
      estimated: true, lens: "registered_veterans",
      description: "Carries forward the annual net change between two consecutive June registration snapshots.",
      provenance: ({ district }) => district && {
        period: "31 Mar 2026", source: "hp_veterans_2026", estimated: false,
        description: "Reported district registrations in the Himachal Pradesh pilot.",
      },
    }),
  field("veteran_share", "Registered ex-servicemen per 100 residents", "pct", "share of residents", "Defence & veterans",
    "30 Jun 2026 registrations · mid-2026 residents", [...VETERANS, "city_population_grid", DM], {
      ...stateOnly((state) => state?.advisor_statistics?.veteran_share),
      ...districtOnly((district) => district?.veteran_share),
    }, {
      estimated: true, description: "Divides estimated registrations by the State/UT’s mid-2026 WorldPop population.",
      provenance: ({ district }) => district && {
        period: "31 Mar 2026 registrations · mid-2026 residents", source: ["hp_veterans_2026", "city_population_grid", DM],
        description: "Divides reported district registrations by the district’s mid-2026 WorldPop population.",
      },
    }),
];

function tradeGatewayIndex(infrastructure, placeAt) {
  if (!infrastructure?.trade) return () => null;
  const gateways = [
    ...infrastructure.ports.filter((p) => p.category === "Major port")
      .map((p) => ({ name: p.name, cells: [p.cell], rail: false })),
    ...infrastructure.trade.corridors.map((name) => ({
      name, cells: infrastructure.rail_corridors[name] || [], rail: true,
    })),
  ];
  const index = atPlaces(gateways, ({ cells, rail }) => cells.flatMap((cell) => placeAt(cell, rail)));
  return (key) => (index.get(key) || []).map((site) => site.name).sort((a, b) => a.localeCompare(b));
}

export function buildData(app) {
  const raw = app.data;
  const { world, cities = [], states = [], city_view } = raw;
  const stateRows = new Map((states || []).map((s) => [s.abbr, s]));
  const districtRecords = raw.lenses?.places?.counties || {};
  const disasters = raw.lenses?.disasters;
  const lenses = new Map((raw.lenses?.lenses || []).map((l) => [l.id, l]));
  const profiles = city_view?.profiles || {};
  const districtNames = new Map(world.counties.map((record) => [record.geoid, record.name]));
  const worldpop = new Map(Object.values(profiles).flatMap((p) => (p.districts || [])
    .map((d) => [d.id, d.district_population])));
  const districtCities = atPlaces(cities, (city) => profiles[city.id]?.method === "ghsl"
    ? profiles[city.id].districts?.map((d) => d.id) || [] : []);
  const districtPlaques = atPlaces(Object.values(profiles).flatMap((p) => p.industry_plaques || []),
    (plaque) => [plaque.district]);
  const stateAt = (cell) => world.states[world.owner[cell]]?.abbr;
  const districtAt = (cell) => world.counties[world.county[cell]]?.geoid;
  const stateCells = indexCells(world.owner);
  const districtCells = indexCells(world.county);
  const footprint = (city) => profiles[city.id]?.method === "ghsl"
    ? profiles[city.id].cells.map((p) => p.cell) : city.footprint?.length ? city.footprint : [city.cell];
  const cityCells = atPlaces([...cities].sort((a, b) => b.population - a.population), footprint);
  const inventory = siteIndex(raw, stateAt, districtAt, (cell) => cityCells.get(cell)?.map((c) => c.id) || []);
  const fields = [...FIELDS, ...hazardFields(disasters),
    ...yieldFields(raw.nation?.yields || []), ...researchFields(raw.nation), ...advisorFields,
    ...resourceFields(raw.resources?.types || []), ...stateMetricFields(lenses, states || [])];
  const grid = app.w?.grid;
  const stateGateways = tradeGatewayIndex(raw.infrastructure, (cell) => [stateAt(cell)]);
  const cityGateways = tradeGatewayIndex(raw.infrastructure, (cell, rail) =>
    (rail && grid ? [cell, ...Array.from({ length: 6 }, (_, d) => grid.neighbour(cell, d))] : [cell]).flatMap((c) =>
      (cityCells.get(c) || []).map((city) => city.id)));
  const hexArea = grid && 1.5 * Math.sqrt(3) * grid.R ** 2;
  const statePlaces = world.states.map((record, ref) => ({
    key: record.abbr, name: record.name, ref, state: stateRows.get(record.abbr), lenses,
    hazardSummary: disasters?.states[record.abbr],
    protectedShare: raw.protectedLand?.shares?.states[record.abbr],
    tradeGateways: stateGateways(record.abbr),
    sites: inventory.forPlace("states", record.abbr, null, true),
  }));
  const metroPlaces = cities.map((city) => {
    const profile = profiles[city.id];
    const modelled = profile?.method === "ghsl";
    const mapped = cityGateways(city.id);
    const tradeGateways = mapped && [...new Set([...mapped,
      ...(profile?.gateways?.rail || []).filter((r) =>
        r.freight && raw.infrastructure.trade.corridors.includes(r.name)).map((r) => r.name),
    ])].sort((a, b) => a.localeCompare(b));
    const fraction = modelled ? sum(profile.cells.map((p) => p.hex_fraction)) : null;
    return {
      key: city.id, name: city.name, sub: city.states?.join(" · "), ref: city, city, lenses, profile, tradeGateways,
      hazardSummary: profile?.hazard_summary,
      sites: inventory.forPlace("metros", city.id, profile, modelled),
      area: hexArea && fraction ? hexArea * fraction : null,
      memberDistricts: modelled ? profile.districts?.map((d) => districtNames.get(d.id)).filter(Boolean) : null,
    };
  });
  const districtPlaces = world.counties.map((record, ref) => ({
    key: record.geoid, name: record.name, sub: districtRecords[record.geoid]?.state,
    ref, district: districtRecords[record.geoid], lenses, worldpop: worldpop.get(record.geoid),
    memberCities: districtCities.get(record.geoid),
    plaques: districtPlaques.get(record.geoid),
    hazardSummary: disasters?.districts[record.geoid],
    sites: inventory.forPlace("counties", record.geoid, null, districtCells.has(ref), districtRecords[record.geoid]?.sites),
    protectedShare: raw.protectedLand?.shares?.counties[record.geoid],
  }));
  const cellsOf = (row) => districtCells.get(row.ref) || [];
  const highlightCells = (rows, getCells) => ({ cells: new Set(rows.flatMap(getCells)) });
  const levels = {
    states: makeLevel("states", "States & UTs", "state or UT", statePlaces, fields, {
      keyAt: stateAt, focus: (r) => app.selectState(r.ref, { fly: true }),
      cellsOf: (r) => stateCells.get(r.ref) || [],
      highlight: (rows) => ({ states: new Set(rows.map((r) => r.ref)) }),
    }),
    metros: makeLevel("metros", "Urban agglomerations", "urban agglomeration", metroPlaces, fields, {
      keyAt: (cell) => cityCells.get(cell)?.[0].id, focus: (r) => app.selectCity(r.ref, { fly: true }),
      cellsOf: (r) => footprint(r.ref),
      highlight: (rows, opts = {}) => ({ ...highlightCells(rows, (r) => footprint(r.ref)),
        cities: rows.length <= (opts.ringMax ?? 30) ? new Set(rows.map((r) => r.key)) : undefined }),
    }),
    counties: makeLevel("counties", "Districts", "district", districtPlaces, fields, {
      keyAt: districtAt, cellsOf, highlight: (rows) => highlightCells(rows, cellsOf),
      focus: (row) => {
        const cells = cellsOf(row);
        if (!cells.length) {
          if (row.place.district?.center) focusPoint(app, ...row.place.district.center, 1.8);
          return;
        }
        const x = cells.map(grid.cx), y = cells.map(grid.cy);
        const r = grid.R;
        frameBox(app, { x0: Math.min(...x) - r, x1: Math.max(...x) + r, y0: Math.min(...y) - r, y1: Math.max(...y) + r });
      },
    }),
  };
  const portCargo = (raw.infrastructure?.ports || []).filter((p) => Number.isFinite(p.cargo?.share)).map((p) => ({
    key: p.id, label: p.name, place: p, value: p.cargo.share,
    period: p.cargo.label, source: p.cargo.source_id, status: p.cargo.status, estimated: p.cargo.estimated === true,
  }));
  return { levels, portCargo, sites: inventory.sites, infrastructure: raw.infrastructure,
    resourceTypes: raw.resources?.types ?? [], nationalPopulation: raw.nation?.nation?.population,
    nationalStatistics: raw.nation?.advisor_statistics, nationalMetrics: raw.nation?.metrics, source: (id) => {
    const entry = raw.sources?.find((s) => s.id === id);
    if (!entry) return null;
    const safeTitle = /\b(?:19\d\d|20(?:0\d|1\d|2[0-5]))\b/.test(entry.title) ? entry.publisher : entry.title;
    return { ...entry, title: id === "datameet" ? "DataMeet community maps of India" :
      id === "census_a01" ? "Census of India district areas" : safeTitle || entry.title };
  } };
}

export function rowsHighlight(level, rows, opts = {}) {
  if (!rows?.length) return null;
  const label = opts.label ?? (rows.length === 1 ? [rows[0].name, rows[0].sub].filter(Boolean).join(", ") : "");
  return { ...level.highlight(rows, opts), dimOthers: !!opts.dim, color: opts.color, label };
}

export function fieldContext(data, level, field, row) {
  const records = row ? [row] : level.rows.filter((r) => r.v[field.key] != null);
  const details = records.length ? records.map((r) => level.meta(field, r)) : [field];
  const unique = (values) => [...new Set(values.filter(Boolean))];
  const periods = unique(details.map((m) => m.period));
  const sources = unique(details.flatMap((m) => m.source)).map((id) => data.source(id)?.title || id);
  const estimate = details.every((m) => m.estimated) ? "IndiaCiv estimate" :
    details.some((m) => m.estimated) ? "Includes IndiaCiv estimates" : "";
  const statuses = unique(details.map((m) => m.status));
  const descriptions = unique(details.map((m) => m.description));
  return [field.unit, ...periods, estimate, ...statuses, ...sources, descriptions.length === 1 ? descriptions[0] : field.description]
    .filter(Boolean).join(" · ");
}
