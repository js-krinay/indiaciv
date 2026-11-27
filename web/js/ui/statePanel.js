import { css } from "../color.js";
import { esc, periodLabel, popShort } from "../format.js";
import { isCapital } from "../world.js";
import { yieldGrid, hasAmenities, amenities, industries, gdpRow, popLine, growthSpan, showPanel } from "./infoPanel.js";

/**
 * Opens the panel for state `idx` (index into world.json states / states.json).
 * ctx: {w, nation, states (states.json or null), cities, onClose, onPedia, onCity(city)}
 */
export function openStatePanel(idx, ctx) {
  const { w, nation } = ctx;
  const n = nation.nation;
  const geo = w.raw.states[idx] || {};
  // states.json is in the same order as world.json states; fall back to matching by fips.
  let st = ctx.states?.[idx];
  if (st && geo.fips && st.fips && st.fips !== geo.fips) st = ctx.states.find((s) => s.fips === geo.fips);
  st = st || { ...geo };
  const name = st.name || geo.name || "State";
  const abbr = st.abbr || geo.abbr || "";
  const count = ctx.states?.length || w.raw.states.length;

  const cities = (ctx.cities || []).filter((c) => (c.states || []).includes(abbr)).slice(0, 8);
  const cityRows = cities.length
    ? `<div class="city-list">${cities
        .map((c) => {
          const multi = (c.states || []).length > 1 ? `<span class="muted"> · ${esc(c.states.join("–"))}</span>` : "";
          return `<button class="city-row" data-city="${esc(c.id)}" title="${esc(c.full || c.name)}">
            <span class="cr-name">${isCapital(c) ? "★ " : ""}${esc(c.name)}${multi}</span>
            <span class="cr-pop">${popShort(c.population)}</span><span class="cr-go" aria-hidden="true">›</span></button>`;
        })
        .join("")}</div>`
    : `<p class="muted">No mapped urban agglomerations in this state or union territory.</p>`;

  const hasEcon = st.population != null || st.yields;
  const jobs = st.provenance?.jobs;
  const benchmark = nation.state_workforce_benchmark;
  const workforceNation = benchmark && jobs?.period === benchmark.provenance.period
    ? { ...nation, nation: benchmark } : nation;
  showPanel({
    kind: "state",
    stripe: css(w.stateColor[idx] || [190, 190, 190]),
    title: name,
    sub: `${esc(abbr)}`,
    headExtra: hasEcon ? popLine(st, " · 1 March 2026" + growthSpan(st)) : "",
    sections: [
      st.yields && { title: "Yields · rank among states", html: `<div class="yield-grid">${yieldGrid(nation, st.yields, st.ranks, count, st.yield_meta)}</div>` },
      hasAmenities(st) && { title: "Amenities &amp; Housing", html: amenities(st, n) + gdpRow(st) },
      st.jobs && {
        title: jobs ? `Top industries · ${esc(jobs.scope)}${periodLabel(jobs, " · ")} · IndiaCiv estimate${jobs.input_weights ? ` · ${periodLabel(jobs.input_weights)} benchmark` : ""}` : "Top industries · where people work",
        html: industries(jobs ? { ...st, employed: jobs.employed } : st, workforceNation, 8),
      },
      { title: "Largest urban agglomerations · mid-2026", html: cityRows },
      !hasEcon && { title: "Data", html: `<p class="muted">State statistics are not in this data build (states.json is missing).</p>` },
    ],
    foot: `Population · Technical Group projections (MoHFW). Ranks are among the ${count} mapped states and union territories (1 = largest).${st.provenance?.median_age?.period && st.profile?.median_age != null ? ` Median age · ${esc(st.provenance.median_age.period)} · ${st.profile.median_age.toFixed(1)} years.` : ""}`,
    onClose: ctx.onClose,
    onPedia: ctx.onPedia,
    wire(panel) {
      panel.querySelectorAll("[data-city]").forEach((b) => {
        b.onclick = () => {
          const c = ctx.cities.find((x) => x.id === b.dataset.city);
          if (c) ctx.onCity(c);
        };
      });
    },
  });
}
