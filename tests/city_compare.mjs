import assert from "node:assert/strict";
import { compareRows } from "../web/js/ext/cityView/economy.js";

const a = { city: { population: 100, projected_growth: 0, growth_period: "same", yields: { science: 0 },
  provenance: { population: { period: "mid-2026", source: "un_wup_cities" } },
  yield_meta: { science: { coverage: "Mapped urban footprint", period: "Snapshot" } } },
  profile: { method: "ghsl", economy: { period: "FY", gdp_per_resident: 10 },
    air: { aqi: { period: "same", source: "CPCB", calendar_days: 304, valid_days: 290, bad_days: 16 } },
    citizens: { workforce: { period: "same", source: "PLFS", state_urban_wpr_all_ages: 0.5 } } } };
const b = structuredClone(a);
b.profile.air.aqi.valid_days = 300;
assert.equal(compareRows(a, b).length, 6);
b.city.yield_meta.science.period = "Other snapshot";
assert.deepEqual(compareRows(a, b).map((row) => row.label),
  ["Population", "Projected growth", "GDP per resident", "Bad-air days", "Employed share"]);
b.city.yield_meta.science.period = "Snapshot";
const otherPopulation = structuredClone(a);
otherPopulation.city.provenance.population.period = "Different projection date";
assert.deepEqual(compareRows(a, otherPopulation).map((row) => row.label), ["Bad-air days", "Employed share", "Science"]);
b.city.growth_period = "different";
b.city.yield_meta.science.coverage = "City centre hex proxy";
b.profile.economy.period = "different";
b.profile.air.aqi.period = "different";
b.profile.citizens.workforce = null;
assert.deepEqual(compareRows(a, b).map((row) => row.label), ["Population"]);

a.profile.citizens.workforce.state_urban_unemployment_15_plus = 0.06;
const sameRelease = structuredClone(a);
assert.equal(compareRows(a, sameRelease).find((row) => row.label === "Urban unemployment benchmark (15+)").left, "6.0%");
sameRelease.profile.citizens.workforce.period = "different";
assert.ok(!compareRows(a, sameRelease).some((row) => row.label.includes("unemployment")));
