import { css } from "../color.js";
import { esc, pct } from "../format.js";
import { cityStateIndex, isCapital } from "../world.js";
import { cityHeadlineStats, indianNumber, workforceSource } from "./cityHeadlines.js";
import { amenities, gdpRow, hasAmenities, industries, yieldGrid, showPanel, hidePanel } from "./infoPanel.js";

const sectors = { agriculture: "Agriculture and allied activities", industry: "Industry", services: "Services" };

function stat(label, text, rank = "") {
  return `<div class="stat-row"><span class="sl">${esc(label)}</span>
    <span><b>${esc(text)}</b>${rank ? ` · ${esc(rank)}` : ""}</span></div>`;
}

function note(text) {
  return `<p class="muted">${esc(text)}</p>`;
}

/**
 * ctx: {w, nation, onClose, onPedia, onState(stateIndex)}
 */
export function openCityPanel(city, ctx) {
  const { w, nation } = ctx;
  const owner = cityStateIndex(w, city);
  const col = css(w.stateColor[owner] || [190, 190, 190]);

  // The city's states as links to their state panels.
  const states = (w.raw.states.length > 1 ? city.states || [] : [])
    .map((abbr) => ({ abbr, i: w.raw.states.findIndex((s) => s.abbr === abbr) }))
    .map(({ abbr, i }) => (i >= 0 && ctx.onState
      ? `<button class="chip" data-state="${i}" title="Open ${esc(w.raw.states[i].name)}">${esc(abbr)}</button>`
      : `<span class="chip">${esc(abbr)}</span>`))
    .join("");

  const headlines = cityHeadlineStats(city, nation.yields?.find((y) => y.key === "gold"));
  const gdp = headlines.find((row) => row.key === "gdp");
  const work = city.resident_workforce;
  const extent = city.mapped_extent;
  const plaques = city.industry_plaques ?? [];
  const sectorMix = city.state_sector_mix;
  const stateName = (work?.states ?? [work?.state])
    .map((id) => w.raw.states.find((s) => s.abbr === id)?.name ?? id).join(", ");
  const blended = work?.states?.length > 1 ? " · IndiaCiv estimate" : "";

  showPanel({
    kind: "city",
    stripe: col,
    title: city.name,
    titleHtml: `${isCapital(city) ? `<span class="cap" title="National capital">★</span> ` : ""}${esc(city.name)}`,
    sub: `${esc(city.full || "")}${states ? `<div class="chips">${states}</div>` : ""}`,
    sections: [
      ctx.terrainLinks?.(city.cell).length ? { title: "Tile terrain", html: ctx.terrainLinks(city.cell).join(" · ") } : null,
      { title: "City headlines", html: headlines.map((row) => stat(row.label, row.text, row.rank) +
        (row.key === "gdp" || row.key === "gdp_per_capita" ? "" : note(row.source))).join("")
        + (gdp ? note(`${gdp.source}. GDP per resident uses UN mid-2026 population.`) : "")
        + note("Ranks among mapped urban agglomerations with each value.") },
      work && { title: "Resident workforce", html:
        stat("Employed residents · all ages", indianNumber(work.employed_all_ages)) +
        (work.employed_15_plus == null ? "" : stat("Employed residents · age 15+", indianNumber(work.employed_15_plus))) +
        note(workforceSource(work) + (work.employed_15_plus == null ? "" : " · WorldPop for the age 15+ estimate")) +
        stat("Urban unemployment benchmark · age 15+", pct(work.state_urban_unemployment_15_plus)) +
        note(`${stateName} · PLFS · ${work.period}${blended}`) +
        work.industries.map((row) => stat(sectors[row.sector], row.employed == null ? pct(row.state_urban_share) :
          `${indianNumber(row.employed)} · ${pct(row.state_urban_share)}`)).join("") +
        note(`Industry shares · ${stateName} urban workers age 15+ · PLFS · ${work.period}${blended}` +
          (work.employed_15_plus == null ? "" : " · City headcounts are IndiaCiv estimates")) },
      sectorMix && { title: `${esc(sectorMix.state)} sector output benchmark`,
        html: Object.entries(sectorMix.shares).map(([key, share]) => stat(sectors[key], pct(share, 2))).join("") +
          note(`Nominal state GSVA shares · ${sectorMix.status} · ${sectorMix.period} · ${sectorMix.publisher ?? "RBI and NSO"}`) },
      extent && { title: "Mapped footprint", html: stat("Area", `${indianNumber(extent.km2)} km² · ${extent.hexes} hexes`) +
        note(`${extent.period} · IndiaCiv estimate · GHSL and Survey of India`) },
      plaques.length > 0 && { title: "Documented industry clusters", html: plaques.map((plaque) =>
        `<div><a href="${esc(plaque.url)}" target="_blank" rel="noopener noreferrer">${esc(plaque.label)}</a></div>` +
        note(`${plaque.period} · ${plaque.citation}`)).join("") },
      nation.yields?.length && { title: "Yields", html: `<div class="yield-grid">${yieldGrid(nation, city.yields, null, 0, city.yield_meta)}</div>` },
      hasAmenities(city) && { title: "Amenities &amp; Housing", html: amenities(city, nation.nation) + gdpRow(city) },
      Object.keys(city.jobs || {}).length && { title: "Districts · where people work", html: industries(city, nation) },
    ].filter(Boolean),
    foot: "City population is the UN DESA mid-2026 projection for the urban agglomeration.",
    onClose: ctx.onClose,
    onPedia: ctx.onPedia,
    pediaRoute: `city/${city.id}`,
    pediaLink: ctx.pediaLink,
    wire(panel) {
      panel.querySelectorAll("[data-state]").forEach((b) => (b.onclick = () => ctx.onState(+b.dataset.state)));
    },
  });
}

export const closeCityPanel = hidePanel;
