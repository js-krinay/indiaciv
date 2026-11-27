import assert from "node:assert/strict";
import { formatHash, parseHash } from "../web/js/app/urlstate.js";
import { buildPediaIndex, searchPedia } from "../web/js/ui/pediaIndex.js";

const route = { lens: "state_density", state: "UP", at: [100, 200, 2], pedia: "state/UP" };
assert.deepEqual(parseHash(formatHash(route)), { city: null, ...route });
assert.match(formatHash(route), /pedia=state\/UP/);
for (const hash of ["#pedia=state", "#pedia=state/UP/extra", "#pedia=state/%", "#pedia=state%2FUP"]) {
  assert.equal(parseHash(hash).pedia, null, hash);
}

const data = {
  world: { states: [{ abbr: "UP", name: "Uttar Pradesh" }], owner: [0, 0], water: [0, 0],
    relief: [0, 1], base: [1, 1], features: [[1], []],
    tables: { feature_cells: { 1: [0, 1] }, base: [{ id: 1, key: "plains", name: "Plains" }],
      features: [{ id: 1, key: "woods", name: "Woods" }] } },
  resources: { types: [{ id: "rice", name: "Rice" }], items: [{ type: "rice", state: "UP" }] },
  sources: [{ id: "census_a01", title: "Census 2011 Table A-01", publisher: "Census of India" }],
  cities: [{ id: 17, name: "Āgra", states: ["UP"], cell: 0, ranks: { population: 50 } },
    { id: 18, name: "Other", ranks: { population: 51 } }],
  wonders: { wonders: [{ id: "fort", name: "Agra Fort", state: "UP", kind: "built" },
    { id: "kailash", name: "Mount Kailash", state: "UP", foreign_side: true }] },
};
const index = buildPediaIndex(data);
assert.deepEqual(index.get("state/UP").cells, [0, 1]);
assert.ok(index.get("state/UP").related.includes("wonder/fort"));
assert.ok(!index.get("state/UP").related.includes("wonder/kailash"));
assert.equal(index.get("terrain/relief-hills").count, 1);
assert.equal(index.get("terrain/feature-woods").count, 2, "Footprint and sampled feature cells are unioned");
assert.equal(index.has("city/18"), false);
assert.deepEqual(searchPedia(index, "agra").map((e) => e.key), ["city/17", "wonder/fort"]);
assert.deepEqual(searchPedia(index, "fort pradesh").map((e) => e.key), ["wonder/fort"]);

assert.ok(searchPedia(index, "rice Uttar Pradesh").some((e) => e.key === "resource/rice"));
assert.ok(searchPedia(index, "agra fort up").some((e) => e.key === "wonder/fort"));
assert.equal(index.get("source/census_a01").shortTitle, "Census of India · Table A-01");
assert.equal(index.get("source/census_a01").title, "Census 2011 Table A-01");

const { createHashState } = await import("../web/js/app/api.js");
const listeners = {};
globalThis.window = { addEventListener(name, fn) { listeners[name] = fn; } };
globalThis.location = { hash: "#pedia=state/UP", pathname: "/", search: "" };
let historyOffset = 0;
const historyRows = [{ data: { unrelated: 7 }, hash: location.hash }];
function update(data, url, offset) {
  const hash = url == null ? location.hash : url.slice(1);
  historyRows[offset] = { data, hash };
  location.hash = hash;
}
globalThis.history = {
  get state() { return historyRows[historyOffset].data; },
  replaceState(data, _title, url) { update(data, url, historyOffset); },
  pushState(data, _title, url) {
    historyRows.splice(++historyOffset);
    update(data, url, historyOffset);
  },
  go(offset) {
    historyOffset += offset;
    location.hash = historyRows[historyOffset].hash;
    listeners.popstate();
  },
};
let core, directions;
const controller = createHashState({
  read: () => core,
  apply: (value) => { core = value; },
  onHistory: (value) => { directions = value; },
});
controller.applyCurrent(true);
const initialId = controller.entryId;
assert.deepEqual(directions, { back: false, forward: false });
assert.equal(history.state.unrelated, 7);
core.pedia = "wonder/fort";
controller.flush();
const wonderId = controller.entryId;
assert.notEqual(wonderId, initialId);
core.at = [10, 20, 2];
controller.flush();
assert.equal(controller.entryId, wonderId);
assert.equal(historyRows.length, 2, "Camera changes replace the current Almanac entry");
core.pedia = null;
controller.flush();
assert.equal(historyRows.length, 3, "Closing pushes one entry");
controller.travel(-1);
assert.equal(core.pedia, "wonder/fort");
assert.equal(controller.entryId, wonderId);
assert.deepEqual(core.at, [10, 20, 2]);
controller.travel(-1);
assert.equal(core.pedia, "state/UP");
assert.equal(controller.entryId, initialId);
assert.deepEqual(directions, { back: false, forward: true });
controller.travel(1);
assert.equal(core.pedia, "wonder/fort");
