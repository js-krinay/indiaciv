import assert from "node:assert/strict";
import { buildData, FIELDS } from "../web/js/ext/advisors/core/data.js";
import { fmtCell } from "../web/js/ext/advisors/core/fmt.js";

const world = {
  states: [{ abbr: "LA", name: "Ladakh" }, { abbr: "JK", name: "Jammu & Kashmir" }],
  counties: [{ geoid: "01-003", name: "Leh" }, { geoid: "01-001", name: "Kupwara" }],
  owner: [0, 1], county: [0, 1],
};
const cities = [
  { id: "21228", name: "Delhi", metro: true, cell: 1, population: 100, projected_growth: 0.02, provenance: { population: { period: "1 Mar 2026", source: "delhi_projection" } }, footprint: [1] },
  { id: "21229", name: "Modelled city", cell: 0, population: 50, footprint: [0] },
];
const hazard = { count: 1, by_type: { Flood: 1 }, last_date: "2026-09-16", last_report_only: true };
const { levels, portCargo } = buildData({ data: {
  world,
  nation: { yields: [{ key: "food", label: "Food", unit: "t", period: "Crop year 2025-26", sources: ["foodgrains_fy26"] }] },
  states: [
    { abbr: "JK", population: 300, employed: 0, yields: { food: 12 }, yield_meta: { food: { estimated: true } }, profile: { growth: 0.02, tfr: 2.2, imr: 10 }, metrics: { gsdp_pc: { value: 120000, source: "gsdp_estimate", estimated: true } } },
    { abbr: "LA", population: 50, metrics: { gsdp_pc: { value: 0, source: "gsdp_fy26", period: "Jul 2026" },
      internet_per_100: { value: 147.5, source: "trai_internet_june_2026", estimated: true },
      pmayu2_completions: { value: 0, source: "pmayu2_test", estimated: true } } },
  ],
  cities,
  city_view: { profiles: {
    "21228": { method: "point", citizens: { workforce: { employed_all_ages: 0 } },
      air: {
        aqi: { bad_days: 0, valid_days: 300, calendar_days: 304, rank: 57, covered_cities: 102,
          period: "Jan–Oct 2026", source: "test_aqi" },
        pm25: { value: 121.2, footprint_coverage: 0.8, period: "Jan–Oct 2026",
          source: "test_pm25", estimated: true },
      },
      housing: { market: "Delhi", index: "114.00", yoy_pct: null, period: "Apr–Jun 2026",
        source: "test_hpi", provisional: true },
      hazards: [{ type: "Flood", label: "September flooding", reported_on: "2026-09-16", source: "test_pib" }],
      hazard_summary: hazard },
    "21229": { method: "ghsl", cells: [{ cell: 0, hex_fraction: 0.25 }], wonders: ["monastery"],
      resources: [], districts: [{ id: "01-003", district_population: 64 }],
      industry_plaques: [{ label: "Textiles", district: "01-003", period: "Jul 2026", source: "bharat_tex_2026", estimated: false }] },
  } },
  wonders: { wonders: [{ id: "monastery", state: "LA", cell: 0, kind: "landmark" }] },
  infrastructure: { rail: [[0, 1], [0, 0]], ports: [{ id: "kolkata-haldia", name: "Kolkata and Haldia", cell: 0, city: "Kolkata and Haldia", state: "Ladakh", state_source_id: "datameet", rank: 6, cargo: { share: 0.0773, domestic: 0.06, foreign: 0.94, label: "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)", status: "Advance estimate", source_id: "mopsw_port_cargo" } }], airports: [] },
  lenses: {
    disasters: { period: "1 Jan – 27 Nov 2026", events: [{ type: "Flood" }],
      states: { JK: hazard }, districts: { "01-001": hazard } },
    places: { counties: { "01-001": { population: 200, state: "JK" },
      "01-003": { population: 50, state: "LA", density: 10, district_pm25: 0, registered_veterans: 5,
        median_age: 30.5,
        hazards: [{ reported_on: "2026-11-04", source: "test_pib" }],
        provenance: {
          density: { period: "1 March 2026", source: ["census_a01", "tg_projections"], estimated: true },
          median_age: { period: "mid-2026", source: ["district_worldpop_age", "datameet"], estimated: true },
        } } } },
    lenses: [{ id: "fertility", period: "2026", source: "tg_projections", estimated: true },
      { id: "city_growth", period: "Mid-2025 – mid-2026", source: "un_wup_cities" },
      { id: "pmayu2_completions", name: "PMAY-Urban 2.0 houses completed or delivered", unit: "houses per 1,000 residents",
        group: "schemes", format: "float", precision: 3, period: "3 August 2026",
        source: "pmayu2_test", denominator_source: "tg_projections" },
      { id: "gsdp_pc", name: "GSDP per person", unit: "₹ / person", format: "int",
      period: "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)", source: "gsdp_fy26" }],
  },
}, w: { grid: { R: 18 } } });
assert.equal(levels.states.rowAtCell(0).v.population, 50);
const la = levels.states.byKey.get("LA");
const internet = levels.states.field("internet_per_100");
const housing = levels.states.field("pmayu2_completions");
assert.equal(internet.lens, "internet_per_100");
assert.equal(la.v.internet_per_100, 147.5);
assert.equal(la.v.pmayu2_completions, 0);
assert.equal(fmtCell(housing.format, 0.003), "0.003");
assert.equal(levels.states.meta(housing, la).estimated, true);
assert.deepEqual(levels.states.meta(housing, la).source, ["pmayu2_test", "tg_projections"]);
assert.equal(levels.states.byKey.get("JK").v.pmayu2_completions, null);
assert.equal(levels.counties.rowAtCell(0).v.state, "LA");
assert.equal(levels.counties.byKey.get("01-001").v.population, 200);
assert.equal(levels.metros.rowAtCell(1).key, "21228");
assert.equal(levels.metros.byKey.get("21228").v.employed_all_ages, 0);
assert.equal(levels.metros.byKey.get("21228").v.age_0_14_count, null);
assert.equal(levels.metros.byKey.get("21228").v.wonders_count, null);
assert.equal(levels.counties.byKey.get("01-003").v.worldpop_district_population, 64);
assert.equal(levels.counties.byKey.get("01-003").v.district_pm25, 0);
assert.equal(levels.counties.byKey.get("01-001").v.district_pm25, null);
assert.equal(levels.metros.byKey.get("21229").v.wonders_count, 1);
assert.equal(levels.metros.byKey.get("21229").v.footprint_districts, "Leh");
assert.ok(levels.metros.byKey.get("21229").v.area_km2 > 0);
const industry = levels.metros.meta(levels.metros.field("industry_plaques"), levels.metros.byKey.get("21229"));
assert.equal(industry.period, "Jul 2026");
assert.deepEqual(industry.source, ["bharat_tex_2026"]);
assert.equal(industry.estimated, false);
assert.equal(levels.states.byKey.get("LA").v.rail_links, 2);
assert.equal(levels.states.byKey.get("JK").v.rail_links, 1);
assert.equal(levels.states.byKey.get("LA").v.port_count, 1);
assert.equal(levels.counties.byKey.get("01-003").v.port_count, 1);
assert.equal(levels.metros.byKey.get("21229").v.port_count, 1);
for (const level of Object.values(levels)) {
  assert.ok(level.rows.every((r) => r.v.port_cargo == null));
}
assert.equal(levels.states.byKey.get("LA").v.port_cities, "Kolkata and Haldia");
assert.equal(levels.states.byKey.get("LA").v.port_states, "Ladakh");
assert.equal(levels.states.byKey.get("LA").v.major_port_rank, 6);
assert.ok(Math.abs(levels.states.byKey.get("LA").v.port_domestic - 0.06) < 1e-12);
assert.ok(Math.abs(levels.states.byKey.get("LA").v.port_foreign - 0.94) < 1e-12);
assert.equal(levels.states.byKey.get("JK").v.port_domestic, null);
assert.equal(portCargo[0].value, 0.0773);
assert.equal(portCargo[0].period, "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)");
assert.equal(portCargo[0].source, "mopsw_port_cargo");
assert.equal(portCargo[0].status, "Advance estimate");
assert.equal(portCargo[0].estimated, false);
const metro = levels.metros.byKey.get("21228");
const metroMeta = key => levels.metros.meta(levels.metros.field(key), metro);
assert.equal(metro.v.city_bad_air_days, 0);
assert.equal(metroMeta("city_bad_air_days").source, "test_aqi");
assert.equal(metro.v.city_air_valid_days, 300);
assert.equal(metro.v.city_air_rank, 57);
assert.equal(metro.v.city_footprint_pm25, 121.2);
assert.equal(metroMeta("city_footprint_pm25").estimated, true);
assert.equal(metroMeta("city_footprint_pm25").source, "test_pm25");
assert.equal(metro.v.city_housing_index, 114);
assert.equal(metroMeta("city_housing_index").description, "RBI registration-market index (base = 100).");
assert.equal(metro.v.city_type, "Under one million");
assert.equal(fmtCell(metroMeta("city_housing_index").format, metro.v.city_housing_index), "114.00");
assert.equal(metroMeta("city_housing_index").period, "Apr–Jun 2026");
assert.equal(metroMeta("city_housing_index").status, "Provisional");
assert.equal(metro.v.city_housing_yoy, null);
assert.equal(metro.v.city_hazards, "September flooding (Flood)");
assert.equal(metro.v.disasters, 1);
assert.equal(metro.v.disaster_last_date, "Reported 2026-09-16");
assert.equal(metroMeta("disasters").period, "1 Jan – 27 Nov 2026");
assert.equal(levels.counties.byKey.get("01-001").v.disaster_flood_count, 1);
assert.equal(levels.counties.byKey.get("01-003").v.disasters, null);
assert.equal(levels.states.byKey.get("JK").v.disasters, 1);
assert.deepEqual(metroMeta("city_hazards").source, ["test_pib"]);
assert.equal(metroMeta("city_hazards").period, "Reported 2026-09-16");
assert.equal(levels.metros.byKey.get("21229").v.city_hazards, null);
assert.equal(levels.metros.byKey.get("21229").v.city_housing_index, null);
assert.equal(levels.metros.meta(levels.metros.field("population"), metro).period, "1 Mar 2026");
assert.equal(levels.metros.meta(levels.metros.field("projected_growth"), metro).period, "Mid-2025 – mid-2026");
const jk = levels.states.byKey.get("JK");
assert.equal(jk.v.projected_growth, null);
assert.equal(jk.v.imr, null);
assert.equal(jk.v.tfr, 2.2);
assert.equal(levels.states.meta(levels.states.field("tfr"), jk).estimated, true);
const leh = levels.counties.byKey.get("01-003");
assert.equal(leh.v.median_age, 30.5);
const districtAge = levels.counties.meta(levels.counties.field("median_age"), leh);
assert.deepEqual(districtAge.source, ["district_worldpop_age", "datameet"]);
assert.equal(districtAge.estimated, true);
assert.equal(districtAge.lens, undefined);
assert.deepEqual(levels.counties.meta(levels.counties.field("density"), leh).source, ["census_a01", "tg_projections"]);

const gsdp = levels.states.field("gsdp_pc");
assert.equal(gsdp.format, "inr");
assert.equal(levels.states.meta(gsdp, levels.states.byKey.get("LA")).period, "Jul 2026");
assert.equal(levels.states.byKey.get("LA").v.gsdp_pc, 0);
assert.equal(levels.states.meta(gsdp, levels.states.byKey.get("LA")).estimated, false);
assert.equal(levels.states.meta(gsdp, levels.states.byKey.get("JK")).source, "gsdp_estimate");
assert.equal(levels.states.meta(gsdp, levels.states.byKey.get("JK")).estimated, true);
for (const fields of Object.values(levels).map(level => level.fields)) {
  assert.equal(new Set(fields.map(f => f.key)).size, fields.length);
  assert.ok(fields.every(f => f.label && f.unit && f.period && f.source && typeof f.estimated === "boolean"));
}
assert.ok(FIELDS.length);

const tradeWorld = {
  states: [{ abbr: "A", name: "Coast" }, { abbr: "B", name: "Inland" }],
  counties: [], owner: [0, 0, 1, 1], county: [-1, -1, -1, -1],
};
const tradeData = buildData({ data: {
  world: tradeWorld,
  cities: [{ id: "port-city", name: "Port City", cell: 0, population: 100 }],
  infrastructure: {
    ports: [
      { id: "major", name: "Major harbour", category: "Major port", cell: 0 },
      { id: "other", name: "Other harbour", category: "Mapped port", cell: 0 },
    ],
    rail_corridors: { DFC: [1, 2], "Ordinary rail": [0, 1] },
    trade: { corridors: ["DFC"] },
  },
}, w: { grid: { R: 18, neighbour: (cell, direction) => direction === 0 && cell === 1 ? 0 : -1 } } });
assert.equal(tradeData.levels.states.byKey.get("A").v.trade_gateways, "DFC · Major harbour");
assert.equal(tradeData.levels.states.byKey.get("B").v.trade_gateways, "DFC");
assert.equal(tradeData.levels.metros.byKey.get("port-city").v.trade_gateway_count, 2);
assert.equal(tradeData.levels.metros.byKey.get("port-city").v.trade_gateways, "DFC · Major harbour");

assert.equal(jk.v.employed, 0);
assert.equal(levels.states.meta(levels.states.field("employed"), jk).estimated, true);
assert.equal(jk.v.yield_food, 12);
assert.equal(levels.states.meta(levels.states.field("yield_food"), jk).estimated, true);
assert.equal(metro.v.kind, "Urban agglomeration");
assert.equal(levels.metros.byKey.get("21229").v.n_districts, 1);
assert.equal(leh.v.metro, "Modelled city");
assert.equal(levels.counties.byKey.get("01-001").v.metro, null);
assert.equal(leh.v.districts, "Textiles");
assert.equal(leh.v.registered_veterans, 5);
assert.equal(levels.counties.meta(levels.counties.field("registered_veterans"), leh).estimated, false);
