import assert from "node:assert/strict";
import { periodLabel } from "../web/js/format.js";
import { formatLensTick, lensPeriodLabels } from "../web/js/ui/lenses.js";
import { growthSpan } from "../web/js/ui/infoPanel.js";
import { buildReport } from "../web/js/ui/yieldReport.js";
import { imageCredits } from "../web/js/app/share.js";
import { columnPeriodLabels, explorerColourLegend } from "../web/js/ext/advisors/views/explorer.js";
import { stackedRowLabel } from "../web/js/ext/advisors/core/charts.js";
import { fmtValue } from "../web/js/ext/advisors/core/fmt.js";
import { chartPeriodLabel } from "../web/js/ext/advisors/core/charts.js";
import { tableShowsRank } from "../web/js/ext/advisors/core/table.js";

assert.equal(periodLabel(), "");
assert.equal(periodLabel({ period: "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)" }),
  "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)");
assert.equal(periodLabel({ vintage: "older", period: "Census 2011" }, " · "),
  '<span class="muted period-tag"> · Census 2011</span>');
assert.equal(periodLabel({ vintage: "older", period: "<NFHS-5> (2019-21)" }),
  '<span class="muted period-tag">&lt;NFHS-5&gt; (2019-21)</span>');

const census = { period: "Census 2011", vintage: "older" };
assert.equal(stackedRowLabel({ label: "Gujarat", text: "72% / 28%", observation: census }), "Gujarat: 72% / 28% · Census 2011");
assert.equal(fmtValue("lq", 1.249), "×1.249");
assert.equal(lensPeriodLabels({ period: "2026", state_details: { 0: census, 1: census } }),
  '2026 · <span class="muted period-tag">Census 2011</span>');
assert.equal(lensPeriodLabels({ ...census, cell_details: { 0: census } }),
  '<span class="muted period-tag">Census 2011</span>');
assert.ok(imageCredits({ lens: { period: "2026", cell_details: { 0: census } } })
  .includes("Lens period · 2026 · Census 2011"));

assert.equal(growthSpan({ growth: null, provenance: { population: census } }), "");
assert.match(growthSpan({ growth: .01, growth_period: "1 Jul 2025 – 1 Jul 2026" }), /1 Jul 2025 – 1 Jul 2026/);
const march = "1 Mar 2025 – 1 Mar 2026", july = "1 Jul 2025 – 1 Jul 2026";
const report = buildReport("population", {
  nation: { nation: { population: 1010, state_reference_population: 1000, growth: .009, growth_period: march } },
  states: [{ population: 1000, growth: .01, growth_period: march }],
  cities: [{ id: "example", population: 300000, growth: .02, growth_period: july }],
});
assert.equal(report.scope.note, "");
assert.match(report.context[0], /1 Mar 2025 – 1 Mar 2026/);
assert.equal(report.boards.modes[1].states[0].sub, march);
assert.equal(report.boards.modes[1].metros[0].sub, july);
assert.equal(columnPeriodLabels([census, { period: "2026" }, census]),
  '<span class="column-period"> · 2026</span><span class="column-period"><span class="muted period-tag"> · Census 2011</span></span>');

assert.equal(chartPeriodLabel([{ period: "Census 2011", vintage: "older", scope: "urban member districts" }]),
  "Census 2011 · urban member districts");
assert.equal(chartPeriodLabel([{ period: "2026" }, { period: "Census 2011", vintage: "older" }]),
  "2026 / Census 2011");
assert.equal(tableShowsRank(true, [{ key: "faith_hindu", hideRank: true }], { key: "faith_hindu" }), false);

assert.equal(explorerColourLegend({ ...census, label: "Occupation share", format: "pct" }, [null]).html.includes("No Census 2011 data"), true);
assert.equal(explorerColourLegend({ ...census, label: "Occupation share", format: "pct" }, [null]).color, null);
assert.equal(typeof explorerColourLegend({ ...census, label: "Occupation share", format: "pct" }, [0]).color, "function");
assert.equal(periodLabel(census, " · ", { plain: true }), " · Census 2011");
assert.equal(formatLensTick({ format: "pct", domain: [0, 1] }, 1, 4), "100%");
assert.equal(formatLensTick({ format: "pct", domain: [0, .8] }, 1, 4), "≥ 80%");
