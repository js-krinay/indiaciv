import { css } from "../color.js";
import { esc, int, pct, popShort } from "../format.js";
import { formatLensValue } from "./lenses.js";
import { isCapital } from "../world.js";
import { yieldGrid, popLine, growthSpan, showPanel, statRow } from "./infoPanel.js";

const FY = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)";
const number = (value) => value.toLocaleString("en-IN", { maximumFractionDigits: 1 });

function stateDetails(st, nation) {
  const fields = [];
  const add = (label, value, format = number) => {
    if (value != null) fields.push(statRow("l-people", "", label, value, null, format, null));
  };
  add("Referenced district area · current geography", st.area_km2, (v) => `${number(v)} km²`);
  add("Share of India’s projected population · 1 March 2026",
    nation.population > 0 && st.population != null ? st.population / nation.population : null, (v) => pct(v, 2));
  add("Employed residents · 1 Jul – 30 Sep 2026 · IndiaCiv estimate", st.employed);
  const gdp = st.yields?.gold;
  const estimate = st.yield_meta?.gold?.estimated ? " · IndiaCiv estimate" : "";
  add(`Nominal GSDP · ${FY}${estimate}`, gdp, (v) => `₹${number(v / 1e7)} crore`);
  add(`Share of India’s nominal GDP · ${FY}${estimate}`,
    nation.yields?.gold > 0 && gdp != null ? gdp / nation.yields.gold : null, (v) => pct(v, 2));
  return fields.join("");
}

function stateCapacity(resources, abbr, world) {
  const power = new Map((resources?.types || []).filter((t) => t.source === "gem_power" && t.unit === "MW")
    .map((type) => [type.id, type.name]));
  const mix = new Map();
  for (const site of resources?.items || []) {
    const state = site.state ?? world.states[world.owner[site.cell]]?.abbr;
    if (state !== abbr || !power.has(site.type) || !Number.isFinite(site.value)) continue;
    mix.set(site.type, (mix.get(site.type) || 0) + site.value);
  }
  if (!mix.size) return null;
  const total = [...mix.values()].reduce((a, b) => a + b, 0);
  return {
    title: "Mapped generating capacity · GEM · September 2026",
    html: statRow("l-energy", "", "Total within the mapped operating inventory", total, null, (v) => `${number(v)} MW`, null)
      + [...mix].sort((a, b) => b[1] - a[1]).map(([type, mw]) => statRow("l-energy", "", power.get(type), mw, null,
        (v) => `${number(v)} MW · ${pct(v / total)}`, null)).join(""),
  };
}

// states.json profile (2026 projections) rows: icon, fallback, label, key, format, higher is good (null: neutral).
const years = (v) => `${v.toFixed(1)} yrs`;
const PROFILE_ROWS = [
  ["l-people", "👥", "Women per 1,000 men", "sex_ratio", int, null],
  ["l-age", "🧒", "Children (0–14)", "age_0_14", (v) => `${v.toFixed(1)}%`, null],
  ["l-age", "🧓", "Aged 60+", "age_60", (v) => `${v.toFixed(1)}%`, null],
  ["l-age", "📅", "Median age", "median_age", years, null],
  ["l-density", "🏘️", "People per km²", "density", int, null],
  ["l-people", "📈", "Projected growth", "growth", (v) => `${(v * 100).toFixed(2)}%`, null],
  ["l-people", "👶", "Children per woman", "tfr", (v) => v.toFixed(2), null],
  ["l-uninsured", "🍼", "Infant deaths per 1,000 births", "imr", (v) => v.toFixed(1), false],
  ["l-amenities", "❤️", "Life expectancy, women", "life_female", years, true],
  ["l-amenities", "❤️", "Life expectancy, men", "life_male", years, true],
];
const HEALTH_KEYS = new Set(["tfr", "imr", "life_female", "life_male"]);
const profileRows = (p, np, health = false) => PROFILE_ROWS.filter(([, , , k]) => HEALTH_KEYS.has(k) === health).map(([ic, fb, label, k, fmt, good]) =>
  p[k] == null ? "" : statRow(ic, fb, k === "growth" ? `${label} · ${p.growth_period}` : label, p[k], np?.[k], fmt, good)).join("");

function metricSections(lenses, state, national) {
  const sections = new Map();
  for (const lens of lenses || []) {
    const record = state?.[lens.id];
    const comparison = national?.[lens.id];
    if (!record && !comparison) continue;
    const title = lens.group === "labour" ? `People & Work · ${lens.source_line}` : lens.source_line;
    const name = lens.id === "gsdp_pc" ? "GSDP per person (India: GDP per person)" : lens.name;
    const higherIsGood = lens.higher_is === "neutral" ? null : lens.higher_is === "good";
    const precision = lens.group === "schemes" ? lens.precision : 1;
    const format = (v) => Number.isFinite(v) && lens.format !== "pct"
      ? `${v.toLocaleString("en-IN", { maximumFractionDigits: precision })} ${esc(lens.unit)}` : formatLensValue(lens, v);
    const notes = [record?.estimated ? "IndiaCiv estimate" : "", record?.coverage].filter(Boolean);
    const note = notes.length ? `<p class="muted">${esc(notes.join(" · "))}</p>` : "";
    const row = statRow(lens.icon, "", name, record?.value, comparison?.value, format, higherIsGood);
    const missingComparison = !record && comparison
      ? `<p class="muted">India ${format(comparison.value)}</p>` : "";
    sections.set(title, (sections.get(title) || "") + row + note + missingComparison);
  }
  return [...sections].map(([title, html]) => ({ title: esc(title), html }));
}

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
  const ageEstimate = st.age_source === "worldpop_age";
  const count = ctx.states?.length || w.raw.states.length;

  const mappedCities = (ctx.cities || []).filter((c) => (c.states || []).includes(abbr));
  const cities = mappedCities.slice(0, 8);
  const cityRows = cities.length
    ? `<div class="city-list">${cities
        .map((c) => {
          const multi = (c.states || []).length > 1 ? `<span class="muted"> · ${esc(c.states.join("–"))}</span>` : "";
          return `<button class="city-row" data-city="${esc(c.id)}" title="${esc(c.full || c.name)}">
            <span class="cr-name">${isCapital(c) ? "★ " : ""}${esc(c.name)}${multi}</span>
            <span class="cr-pop">${popShort(c.population)}</span><span class="cr-go" aria-hidden="true">›</span></button>`;
        })
        .join("")}</div>`
    : `<p class="muted">No mapped cities in this state.</p>`;

  const hasEcon = st.population != null || st.yields;
  const details = stateDetails(st, n);
  showPanel({
    kind: "state",
    stripe: css(w.stateColor[idx] || [190, 190, 190]),
    title: name,
    sub: `${esc(abbr)}${geo.fips && geo.fips !== abbr ? ` · FIPS ${esc(geo.fips)}` : ""}`,
    headExtra: hasEcon ? popLine(st, growthSpan(st, n)) : "",
    sections: [
      ctx.terrainLinks?.(ctx.cell).length ? { title: "Tile terrain", html: ctx.terrainLinks(ctx.cell).join(" · ") } : null,
      // Only sections with data.
      st.profile && { title: ageEstimate ? "2026 profile" : "Projected for 2026", html: profileRows(st.profile, nation.profile) },
      st.profile?.health?.estimated && { title: "IndiaCiv estimate for 2026 (interpolated from Technical Group projections)",
        html: profileRows(st.profile, nation.profile, true) },
      ...metricSections(ctx.metricLenses, st.metrics, nation.metrics),
      details && { title: "State indicators", html: details },
      st.sector_mix && {
        title: `Nominal GSVA by sector · ${FY}`,
        html: `<p class="muted">Shares of state GSVA · ${esc(st.sector_mix.status)}</p>` +
          [["agriculture", "Agriculture & allied"], ["industry", "Industry"], ["services", "Services"]]
            .map(([key, label]) => statRow("l-people", "", label, st.sector_mix.shares[key], null, pct, null)).join(""),
      },
      stateCapacity(ctx.resources, abbr, w.raw),
      st.yields && nation.yields?.length && { title: "Yields · rank among states", html: `<div class="yield-grid">${yieldGrid(nation, st.yields, st.ranks, count, st.yield_meta)}</div>` },
      { title: `Biggest cities · ${int(mappedCities.length)} mapped UAs · mid-2026`, html: cityRows },
      !hasEcon && { title: "Data", html: `<p class="muted">State statistics are not in this data build (states.json is missing).</p>` },
    ],
    foot: ageEstimate ? "Age values · 2026 estimate (WorldPop). Population and other profile figures · Technical Group projections (MoHFW)."
      : `Source: ${esc(nation.vintage)}${nation.gdp_vintage ? `; GDP: ${esc(nation.gdp_vintage)}` : ""}. Population and profile:
      Technical Group projections (MoHFW).${nation.yields?.length ? ` Ranks are among the ${count} states and union territories (1 = largest).` : ""}`,
    onClose: ctx.onClose,
    onPedia: ctx.onPedia,
    pediaRoute: `state/${w.raw.states[idx].abbr || w.raw.states[idx].fips}`,
    pediaLink: ctx.pediaLink,
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
