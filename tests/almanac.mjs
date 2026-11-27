import assert from "node:assert/strict";
import { formatHash, parseHash } from "../web/js/app/urlstate.js";

const route = { lens: "state_density", state: "UP", at: [100, 200, 2] };
assert.deepEqual(parseHash(formatHash(route)), { city: null, ...route });
assert.equal(formatHash({ ...route, pedia: "state/UP" }), formatHash(route));
assert.deepEqual(parseHash("#state=UP&pedia=state/UP"), { lens: null, city: null, state: "UP", at: null });
