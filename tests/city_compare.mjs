import assert from "node:assert/strict";
import { compareTable } from "../web/js/ext/cityView/screen.js";

const city = { name: "City A", population: 100, gdp: 15000, growth: 0, unemployment: 0.06,
  provenance: { population: { period: "mid-2026" }, gdp: { period: "FY 2025-26" },
    growth: { period: "1 Jul 2025 – 1 Jul 2026" }, unemployment: { period: "1 Jul – 30 Sep 2026" } } };
const peer = { id: "b", city_view: true, name: "City B", population: 80, growth: 0.01,
  provenance: { population: { period: "Census 2011", vintage: "older" },
    growth: { period: "1 Jul 2025 – 1 Jul 2026" } } };
const model = { city, peers: [peer] };
const size = compareTable(model);
assert.match(size, /FY 2025-26/);
assert.match(size, /Census 2011/);
assert.match(size, /₹150/);
assert.match(size, /data-peer="b"/);
assert.doesNotMatch(size, /columnheader">Income</);
const housing = compareTable(model, "housing");
assert.match(housing, /6\.0%/);
assert.match(housing, /1 Jul – 30 Sep 2026/);
assert.doesNotMatch(housing, /columnheader">Home value</);
