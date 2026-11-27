import { css } from "../color.js";
import { esc, periodLabel } from "../format.js";
import { cityStateIndex, isCapital } from "../world.js";
import { yieldGrid, hasAmenities, amenities, industries, gdpRow, popLine, growthSpan, showPanel, hidePanel } from "./infoPanel.js";

/**
 * ctx: {w, nation, onClose, onPedia, onState(stateIndex)}
 */
export function openCityPanel(city, ctx) {
  const { w, nation } = ctx;
  const owner = cityStateIndex(w, city);
  const col = css(w.stateColor[owner] || [190, 190, 190]);

  // The city's states as links to their state panels.
  const states = (city.states || [])
    .map((abbr) => ({ abbr, i: w.raw.states.findIndex((s) => s.abbr === abbr) }))
    .map(({ abbr, i }) => (i >= 0 && ctx.onState
      ? `<button class="chip" data-state="${i}" title="Open ${esc(w.raw.states[i].name)}">${esc(abbr)}</button>`
      : `<span class="chip">${esc(abbr)}</span>`))
    .join("");

  const growth = growthSpan(city);
  const period = periodLabel(city.provenance?.population || "Mid-2026 · UN DESA", " · ");

  showPanel({
    kind: "city",
    stripe: col,
    title: city.name,
    titleHtml: `${isCapital(city) ? `<span class="cap" title="National capital">★</span> ` : ""}${esc(city.name)}`,
    sub: `${esc(city.full || "")}${states ? `<div class="chips">${states}</div>` : ""}`,
    headExtra: popLine({ ...city, employed: city.resident_workforce?.employed_all_ages,
      provenance: { employed: { ...city.resident_workforce, age_scope: "all ages" } } }, period + growth),
    sections: [
      city.yields && { title: "Yields", html: `<div class="yield-grid">${yieldGrid(nation, city.yields, null, 0, city.yield_meta)}</div>` },
      hasAmenities(city) && { title: "Amenities &amp; Housing", html: amenities(city, nation.nation) + gdpRow(city) },
      city.jobs && { title: "Districts · where people work", html: industries(city, nation) },
    ],
    foot: "Population and growth · UN DESA urban agglomeration projections.",
    onClose: ctx.onClose,
    onPedia: ctx.onPedia,
    wire(panel) {
      panel.querySelectorAll("[data-state]").forEach((b) => (b.onclick = () => ctx.onState(+b.dataset.state)));
    },
  });
}

export const closeCityPanel = hidePanel;
