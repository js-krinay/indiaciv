// The city screen: a docked dashboard (a bottom sheet on phones) with the header (and its city-type badge),
// Citizens (figure rows from citizens.json), Districts (districts.json + military.json), Economy, Workforce,
// Resources and Compare. Plain HTML strings + inline SVG charts; render(el, model, handlers) fills `el`. The
// citizens and districts files load on demand (h.loadData) and fill their sections when they arrive.
import { dollars, esc, int, pct, periodLabel, yieldDetails } from "../../format.js";
import { compact, money, popShort, yieldValue } from "./fmt.js";
import { icon, glyph } from "../../ui/icon.js";
import { css } from "../../color.js";
import { isCapital } from "../../world.js";
import { sparkline, meter, bar } from "./charts.js";
import { popSeries, rankCount, resourceValue, LAND } from "./model.js";
import { citizensHtml, mountCitizens } from "./citizens.js";
import { badgeHtml, cityDistricts, districtsHtml } from "./districts.js";

const TABS = [
  ["citizens", "Citizens", "pop"],
  ["districts", "Districts", "l-developed"],
  ["economy", "Economy", "y-gold"],
  ["workforce", "Workforce", "y-production"],
  ["resources", "Resources", "resources"],
  ["compare", "Compare", "layers"],
];

const period = (record, prefix = " · ") => periodLabel(record, prefix);
const estimate = (record) => record?.estimated ? " · IndiaCiv estimate" : "";
const national = (value, format) => value != null ? ` · India ${format(value)}` : "";

const signed = (g, d = 1) => (g == null ? "–" : `${g >= 0 ? "+" : "−"}${Math.abs(g * 100).toFixed(d)}%`);
const rankCache = new WeakMap();
function countOf(cities, key) {
  let m = rankCache.get(cities);
  if (!m) rankCache.set(cities, (m = new Map()));
  if (!m.has(key)) m.set(key, rankCount(cities, key));
  return m.get(key);
}

function rankBadge(rank, of, label, tip) {
  if (rank == null) return "";
  const tier = rank <= 10 ? "gold" : rank <= 50 ? "silver" : "bronze";
  return `<div class="cv-rank ${tier}" title="${esc(tip || `${label}: #${rank} of ${of} urban agglomerations (1 = highest)`)}">
    <span class="cv-medal">#${rank}</span><span class="cv-rank-l">${esc(label)}</span></div>`;
}

function lqBadge(lq) {
  if (lq == null) return "";
  const tip = `Location quotient: this share is ${lq.toFixed(2)}× India’s share`;
  const cls = lq >= 1.25 ? "hi" : lq <= 0.75 ? "lo" : "mid";
  return `<span class="cv-lq ${cls}" title="${esc(tip)}">×${lq.toFixed(1)}</span>`;
}

function medallion(id, fallback, bg, size = 18) {
  return `<span class="cv-med" style="--bg:${esc(bg)}">${icon(id, fallback, { size })}</span>`;
}

// --- header --------------------------------------------------------------------------------------------------------
function header(m) {
  const c = m.city, n = m.nation.nation;
  const cities = m.cityList;
  const col = css(m.stateRGB);
  const chips = m.states.map((s) => (s.index >= 0
    ? `<button class="chip" data-state="${s.index}" title="Open ${esc(s.name)}">${esc(s.abbr)}</button>`
    : `<span class="chip">${esc(s.abbr)}</span>`)).join("");
  const g = Number.isFinite(c.growth) ? c.growth : null;
  const growth = g == null ? "" : `<span class="cv-growth ${g >= 0 ? "good" : "bad"}" title="UN population projection">${g >= 0 ? "▲" : "▼"} ${Math.abs(g * 100).toFixed(1)}% <small>${period(c.provenance?.growth, "")}</small></span>`;
  const perCap = c.gdp != null && c.population ? c.gdp / c.population : null;
  const r = c.ranks || {};
  const N = (k) => countOf(cities, k);
  return `
  <div class="sheet-grip cv-grip" aria-hidden="true"></div>
  <header class="cv-head" style="--sc:${col}">
    <div class="cv-ribbon" aria-hidden="true"></div>
    <button class="icon-btn cv-close" data-close aria-label="Close the City View (Esc)" title="Back to the map (Esc)">${icon("close", "✕", { size: 13 })}</button>
    <div class="cv-kind">City View · Urban agglomeration</div>
    <div class="cv-title">
      <div class="cv-crest" aria-hidden="true"><span>${esc(popShort(c.population))}</span></div>
      <div class="cv-tt">
        <h2 class="cv-name" tabindex="-1">${isCapital(c) ? `<span class="cv-cap" title="National capital">★</span> ` : ""}${esc(c.name)}</h2>
        <div class="cv-full">${esc(c.full || "")}</div>
        <div class="cv-typeslot" data-ctype></div>
        ${chips ? `<div class="chips">${chips}</div>` : ""}
      </div>
    </div>
    <div class="cv-headline">
      <div class="cv-big"><span class="lbl">${icon("pop", "👥", { size: 13 })} Population${period(c.provenance?.population)}</span><b>${int(c.population)}</b>${growth}</div>
      ${c.gdp == null ? "" : `<div class="cv-big"><span class="lbl">${icon("y-gold", "💰", { size: 13 })} GDP${period(c.provenance?.gdp)}</span><b>${money(c.gdp)}</b>${
        perCap != null ? `<span class="cv-sub">${money(perCap)} per person${estimate(c.provenance?.gdp)}</span>` : ""}</div>`}
    </div>
    <div class="cv-ranks" aria-label="Ranks among ${cities.length} urban agglomerations">
      ${rankBadge(r.population, N("population"), "Population", `Population: #${r.population} of ${N("population")}${periodLabel(c.provenance?.population, " · ", { plain: true })}`)}
      ${rankBadge(r.gdp, N("gdp"), "GDP", `GDP: #${r.gdp} of ${N("gdp")}${periodLabel(c.provenance?.gdp, " · ", { plain: true })}`)}
      ${rankBadge(r.gdp_per_capita, N("gdp_per_capita"), "GDP / person", `GDP per person: #${r.gdp_per_capita} of ${N("gdp_per_capita")}${periodLabel(c.provenance?.gdp, " · ", { plain: true })}`)}
      ${rankBadge(r.growth, N("growth"), "Growth", r.growth != null ? `Growth: #${r.growth} of ${N("growth")} (1 = fastest growing)${periodLabel(c.provenance?.growth, " · ", { plain: true })}` : "")}
    </div>
  </header>
  <nav class="cv-tabs" aria-label="City View sections">
    ${TABS.map(([id, label, ic]) => `<button type="button" data-tab="${id}">${icon(ic, "•", { size: 14 })}<span>${label}</span></button>`).join("")}
  </nav>`;
}

// --- citizens ------------------------------------------------------------------------------------------------------
function citizens(m) {
  const c = m.city, n = m.nation.nation;
  const series = popSeries(c);
  const ch = series.length >= 2 ? series.at(-1).value / series[0].value - 1 : null;
  // sub: the small line beside the value; by default the U.S. value, left out when there is none.
  const row = (ic, fb, label, v, us, fmt, better, max, sub = us != null ? `India ${fmt(us)}` : "", tick = us) => v == null ? "" : `
    <div class="cv-stat">
      <div class="cv-stat-top"><span class="sl">${icon(ic, fb, { size: 14 })}${esc(label)}</span>
        <span class="sv"><b>${v == null ? "–" : fmt(v)}</b>${sub ? `<small>${sub}</small>` : ""}</span></div>
      ${meter(v, tick, max ?? Math.max(v || 0, us || 0) * 1.35, better)}
    </div>`;
  const empShare = c.employed != null && c.population > 0 ? c.employed / c.population : null;
  const workforce = c.resident_workforce;
  const empSub = empShare == null ? ""
    : `${pct(empShare)} of residents${estimate(c.provenance?.employed)}${
      c.provenance?.employed?.age_scope === "age 15+" && Number.isFinite(workforce?.employed_all_ages)
        ? ` · ${int(workforce.employed_all_ages)} employed (all ages)${period(workforce)}${estimate(workforce)}` : ""}`;
  const multi = m.tiles.length > 1;
  const tilesNote = multi
    ? `On the map each agglomeration hex shows <b>≈ residents</b> (district density × hex area, IndiaCiv estimate for 1 March 2026) and its
       <b>main land use</b> (share of the hex's land)${m.residentsSum > 0
        ? `. Together the ${m.tiles.length} hexes hold about ${compact(m.residentsSum)} people by that estimate` : ""}.`
    : `This urban agglomeration is represented by one map hex (about ${compact(m.hexArea)} km²), shown with its city.`;
  return `
  <section class="cv-sec" id="cv-citizens" data-sec="citizens" aria-labelledby="cv-h-citizens">
    <h3 id="cv-h-citizens">${icon("pop", "👥", { size: 15 })}Citizens</h3>
    <div class="cv-citizens" data-citizens>${citizensHtml(m, undefined)}</div>
    ${series.length >= 2 ? `<h4 class="cv-h4">Population</h4>
    <div class="cv-card">
      <div class="cv-card-h"><span>Population${period(c.provenance?.pop_series)}</span>${
        ch != null ? `<span class="${ch >= 0 ? "good" : "bad"}">${signed(ch)}</span>` : ""}</div>
      ${sparkline(series, { fmt: (v) => popShort(v), title: `Population of ${c.name} during 2026` })}
      <p class="cv-note">UN population projection for 1 July 2026.</p>
    </div>` : ""}
    <div class="cv-stats">
      ${row("pop", "👥", `Employed residents${c.provenance?.employed?.age_scope ? ` (${c.provenance.employed.age_scope})` : ""}${periodLabel(c.provenance?.employed, " · ", { plain: true })}`, c.employed, null, int, null, c.population, empSub)}
      ${row("unemployment", "😐", `Urban unemployment (age 15+)${periodLabel(c.provenance?.unemployment, " · ", { plain: true })}`, c.unemployment, n.unemployment, (x) => pct(x), "low", undefined, n.unemployment != null ? `India ${pct(n.unemployment)}${period(n.provenance?.unemployment)}` : "")}
      ${row("l-income", "💵", "Median household income", c.median_income, n.median_income, dollars, "high")}
      ${row("l-homeownership", "🔑", "Median rent / month", c.median_rent, n.median_rent, dollars, null)}
      ${row("l-home", "🏠", "Median home value", c.home_value, n.home_value, dollars, null)}
      ${row(null, "⚖️", "Rent burden (rent ÷ income)", c.rent_burden, n.rent_burden, (x) => pct(x), "low")}
    </div>
    <div class="cv-legend-tiles">${tileLegend(m)}<p>${tilesNote}</p></div>
    <h4 class="cv-h4">Member districts <span class="muted">(${(c.counties || []).length})</span></h4>
    <div class="cv-counties" data-counties><p class="muted cv-note">Loading districts…</p></div>
  </section>`;
}

function tileLegend(m) {
  const counts = new Map();
  for (const t of m.tiles) if (t.land) counts.set(t.land.key, (counts.get(t.land.key) || 0) + 1);
  return `<div class="cv-tl">${LAND.filter((g) => counts.has(g.key)).map((g) =>
    `<span class="cv-tl-i"><i style="background:${esc(m.landColor(g.key))}"></i>${esc(g.label)} <small>${counts.get(g.key)}</small></span>`).join("")}</div>`;
}

export function countiesTable(m, data) {
  const c = m.city;
  if (!data || !Array.isArray(data.rows)) return `<p class="muted cv-note">District table unavailable.</p>`;
  const col = Object.fromEntries(data.columns.map((k, j) => [k, j]));
  const want = new Set(c.counties || []);
  const rows = data.rows.filter((r) => want.has(r[col.geoid])).sort((a, b) => (b[col.population] || 0) - (a[col.population] || 0));
  if (!rows.length) return `<p class="muted cv-note">Member district estimates unavailable.</p>`;
  const maxPop = rows[0][col.population] || 1;
  const show = rows.slice(0, 8);
  const hasIncome = rows.some((r) => r[col.income] != null);
  return `<div class="cv-ctable" role="table" aria-label="Member districts">
    <div class="cv-cr cv-cr-h" role="row"><span role="columnheader">District</span><span role="columnheader">People</span><span role="columnheader">/km²</span>${hasIncome ? `<span role="columnheader">Income</span>` : ""}</div>
    ${show.map((r) => `<div class="cv-cr" role="row">
      <span role="cell" class="cv-cn">${esc(r[col.name])} <small>${esc(r[col.state])}</small>${bar(r[col.population] / maxPop, "var(--sc, #c9a45c)")}</span>
      <span role="cell" title="${int(r[col.population])}${period(data)}">${compact(r[col.population])}</span><span role="cell">${r[col.density] != null ? int(r[col.density]) : "–"}</span>
      ${hasIncome ? `<span role="cell">${money(r[col.income])}</span>` : ""}</div>`).join("")}
    ${rows.length > show.length ? `<p class="muted cv-note">and ${rows.length - show.length} more.</p>` : ""}
    <p class="cv-note">IndiaCiv estimates${period(data)}. Census 2011 district populations projected at state rates.</p>
  </div>`;
}

// --- districts -----------------------------------------------------------------------------------------------------
function districts(m) {
  return `
  <section class="cv-sec" id="cv-districts" data-sec="districts" aria-labelledby="cv-h-districts">
    <h3 id="cv-h-districts">${icon("l-developed", "🏙", { size: 15 })}Districts</h3>
    <div data-districts>${districtsHtml(m, undefined, null)}</div>
  </section>`;
}

// --- economy -------------------------------------------------------------------------------------------------------
function economy(m) {
  const c = m.city, nat = m.nation, n = nat.nation;
  const r = c.ranks || {};
  const cities = m.cityList;
  const perCap = c.gdp != null && c.population ? c.gdp / c.population : null;
  const usPerCap = n.gdp && n.population ? n.gdp / n.population : null;
  const yields = nat.yields.map((y) => {
    const v = c.yields?.[y.key];
    const rk = r[y.key];
    const meta = c.yield_meta?.[y.key];
    if (v == null) return "";
    return `<div class="cv-yield" style="--yc:${esc(y.color)}" title="${esc(y.label)}: ${esc(yieldDetails({ ...y, period: meta?.period }, v, meta))}">
      <div class="ico">${glyph(y, 20)}</div><div class="val">${yieldValue(y, v)}</div>
      <div class="lbl">${esc(y.key === "gold" ? "GDP" : y.label)}${period(meta)}${estimate(meta)}</div>
      ${rk != null ? `<div class="rk">#${rk} <small>of ${countOf(cities, y.key)}</small></div>` : ""}</div>`;
  }).join("");
  const gi = m.gdpInds;
  const maxShare = gi.length ? Math.max(...gi.map((d) => Math.max(d.share, d.natShare))) : 1;
  const gdpRow = (d) => d.undisclosed
    ? `<div class="cv-ind und" title="BEA withholds some county figures to protect individual businesses: ${esc(d.missing.map((k) => nat.industries?.[k] || k).join(", ") || "several industries")}. This is the metro's GDP minus every disclosed industry.">
      <span class="cv-ind-ic" style="--bg:${esc(d.color)}">${icon(d.icon, "?", { size: 13 })}</span>
      <span class="cv-ind-n">${esc(d.short)}</span>
      <span class="cv-ind-v">${money(d.value)} <small>${pct(d.share, 0)}</small></span>
      ${bar(d.share / maxShare, "#7c8494", 0)}
    </div>`
    : `<div class="cv-ind" title="${esc(d.label)}: ${money(d.value)} (${pct(d.share)} of the agglomeration’s GDP${national(n.gdp_by_industry?.[d.key] != null ? d.natShare : null, pct)})${period(c.provenance?.gdp_by_industry)}${estimate(c.provenance?.gdp_by_industry)}">
      <span class="cv-ind-ic" style="--bg:${esc(d.color)}">${icon(d.icon, "•", { size: 13 })}</span>
      <span class="cv-ind-n">${esc(d.short)}${lqBadge(d.lq)}</span>
      <span class="cv-ind-v">${d.estimated ? "≈" : ""}${money(d.value)} <small>${pct(d.share, 0)}</small></span>
      ${bar(d.share / maxShare, d.lq != null && d.lq >= 1.25 ? "#9fd76a" : "#c9a45c", n.gdp_by_industry?.[d.key] == null ? null : d.natShare / maxShare)}
    </div>`;
  return `
  <section class="cv-sec" id="cv-economy" data-sec="economy" aria-labelledby="cv-h-economy">
    <h3 id="cv-h-economy">${icon("y-gold", "💰", { size: 15 })}Economy</h3>
    <div class="cv-gdp">
      <div><span class="lbl">GDP${period(c.provenance?.gdp)}</span><b>${money(c.gdp)}</b>${r.gdp != null ? `<small>#${r.gdp} of ${countOf(cities, "gdp")}</small>` : ""}</div>
      <div><span class="lbl">GDP per person${period(c.provenance?.gdp)}</span><b>${money(perCap)}</b>${
        usPerCap ? `<small class="${perCap >= usPerCap ? "good" : "bad"}">India ${money(usPerCap)}${period(n.provenance?.gdp)}</small>` : ""}</div>
      ${c.gdp != null && n.gdp ? `<div><span class="lbl">Share of India’s GDP${period(c.provenance?.gdp)}</span><b>${pct(c.gdp / n.gdp, 2)}</b><small>${pct(c.population / n.population, 2)} of people${period(n.provenance?.population)}</small></div>` : ""}
    </div>
    <h4 class="cv-h4">Yields <span class="muted">rank among urban agglomerations</span></h4>
    <div class="cv-yields">${yields}</div>
    <h4 class="cv-h4">GDP by industry${gi.some((d) => n.gdp_by_industry?.[d.key] != null) ? ` <span class="muted">tick = India’s share</span>` : ""}</h4>
    ${gi.length ? `<div class="cv-inds">${gi.slice(0, 8).map(gdpRow).join("")}</div>
      ${gi.length > 8 ? `<details class="cv-more"><summary>All ${gi.length} industries</summary><div class="cv-inds">${gi.slice(8).map(gdpRow).join("")}</div></details>` : ""}`
      : `<p class="muted cv-note">Industry breakdown unavailable.</p>`}
    ${gi.length ? `<p class="cv-note">Nominal GDP allocated by state GSVA shares${period(c.provenance?.gdp_by_industry)}${estimate(c.provenance?.gdp_by_industry)}.</p>` : ""}
  </section>`;
}

// --- workforce -----------------------------------------------------------------------------------------------------
function workforce(m) {
  const n = m.nation.nation;
  const cards = m.inds.map((d) => {
    const spec = d.lq != null && d.lq >= 1.25;
    return `<div class="cv-bld${spec ? " spec" : ""}" title="${esc(d.label)}: ${int(d.jobs)} residents in this sector (${pct(d.share)}${national(n.jobs?.[d.key] != null ? d.natShare : null, pct)})${period(m.city.provenance?.jobs)}">
      ${medallion(d.icon, "•", d.color, 17)}
      <div class="cv-bld-t"><span class="cv-bld-n">${esc(d.short)}</span>
        <span class="cv-bld-v">${compact(d.jobs)} <small>${pct(d.share, 1)}</small></span></div>
      ${lqBadge(d.lq)}
    </div>`;
  }).join("");
  return `
  <section class="cv-sec" id="cv-workforce" data-sec="workforce" aria-labelledby="cv-h-workforce">
    <h3 id="cv-h-workforce">${icon("y-production", "⚙️", { size: 15 })}Workforce</h3>
    ${cards ? `<p class="cv-lead">Where the agglomeration's ${int(m.city.employed)} employed residents aged 15+ work, by industry.${
      m.inds.some((d) => d.lq != null) ? ` <span class="cv-lq hi">×N</span> compares an industry's share of jobs with its India share.` : ""}</p>` : ""}
    <div class="cv-blds">${cards || `<p class="muted cv-note">No industry data.</p>`}</div>
    ${cards ? `<p class="cv-note">PLFS urban rates${period(m.city.provenance?.jobs)}${estimate(m.city.provenance?.jobs)}.</p>` : ""}
  </section>`;
}

// --- resources -----------------------------------------------------------------------------------------------------
function resources(m) {
  const list = m.sites.map((s, k) => {
    const t = s.type;
    const val = resourceValue(s.item, t, compact);
    return `<button type="button" class="cv-site" data-site="${k}" title="Fly to ${esc(s.item.name)}">
      <span class="cv-med" style="--bg:${esc(t?.color || "#3a4a5e")}">${glyph(t, 16)}</span>
      <span class="cv-site-t"><b>${esc(s.item.name)}</b><small>${esc(t?.name || s.item.type)}${s.item.state ? ` · ${esc(s.item.state)}` : ""}</small>
        ${s.item.detail || s.item.period ? `<small class="cv-site-d">${esc(s.item.detail || "")}${period(s.item, s.item.detail ? " · " : "")}${estimate(s.item)}</small>` : ""}</span>
      <span class="cv-site-v">${esc(val)}<i aria-hidden="true">›</i></span>
    </button>`;
  }).join("");
  const cats = {};
  for (const s of m.sites) cats[s.type?.category || "other"] = (cats[s.type?.category || "other"] || 0) + 1;
  const mwPeriod = m.sites.find((s) => s.item.aggregate_mw)?.item.aggregate_mw;
  const mw = mwPeriod?.value;
  const summary = m.sites.length
    ? `<p class="cv-lead">${m.sites.length} mapped site${m.sites.length === 1 ? "" : "s"}${
      mw && mwPeriod ? ` · ${mw >= 1000 ? `${(mw / 1000).toFixed(1)} GW` : `${Math.round(mw)} MW`} of mapped generating capacity${period(mwPeriod)}${estimate(mwPeriod)}` : ""}. Click one to fly there.</p>`
    : `<p class="muted cv-note">No mapped resource sites in this urban agglomeration.</p>`;
  return `
  <section class="cv-sec" id="cv-resources" data-sec="resources" aria-labelledby="cv-h-resources">
    <h3 id="cv-h-resources">${icon("resources", "⛏️", { size: 15 })}Resources</h3>
    ${summary}
    <div class="cv-sites">${list}</div>
    ${m.sites.length ? `<p class="cv-note">Sites within the mapped agglomeration footprint.</p>` : ""}
  </section>`;
}

// --- compare -------------------------------------------------------------------------------------------------------
const COMPARE = {
  size: [
    ["Population", (c) => c.population, popShort, "population"],
    ["GDP / person", (c) => (c.gdp != null && c.population ? c.gdp / c.population : null), money, "gdp"],
    ["Income", (c) => c.median_income, money],
    ["Growth", (c) => (Number.isFinite(c.growth) ? c.growth : null), (v) => signed(v), "growth"],
  ],
  housing: [
    ["Home value", (c) => c.home_value, money],
    ["Rent / mo", (c) => c.median_rent, dollars],
    ["Rent burden", (c) => c.rent_burden, (v) => pct(v, 0)],
    ["Jobless", (c) => c.unemployment, (v) => pct(v), "unemployment"],
  ],
};

export function compareTable(m, set = "size") {
  const rows = [m.city, ...m.peers];
  const cols = (COMPARE[set] || COMPARE.size).filter(([, f]) => rows.some((c) => f(c) != null));
  const max = cols.map(([, f]) => Math.max(...rows.map((c) => Math.abs(f(c) ?? 0))) || 1);
  return `<div class="cv-cmp" role="table" aria-label="${esc(m.city.name)} and its peers">
    <div class="cv-cmp-r cv-cmp-h" role="row"><span role="columnheader">Agglomeration</span>${cols.map(([l]) => `<span role="columnheader">${esc(l)}</span>`).join("")}</div>
    ${rows.map((c, k) => `<div class="cv-cmp-r${k === 0 ? " me" : ""}" role="row">
      <span role="cell">${k === 0 ? `<b class="cv-cmp-n">${esc(c.name)}</b>` : `<button type="button" class="cv-cmp-n" data-peer="${esc(c.id)}" title="Open ${esc(c.full || c.name)} in the City View">${esc(c.name)}</button>`}<small>${esc((c.states || []).join("–"))}</small></span>
      ${cols.map(([, f, fmt, key], j) => {
        const v = f(c);
        const col = v != null && v < 0 ? "#f08a6a" : k === 0 ? "#ecd08e" : "#8fa6bd";
        return `<span role="cell"><em>${v == null ? "–" : esc(fmt(v))}${v == null ? "" : period(c.provenance?.[key])}</em>${bar(v == null ? 0 : Math.abs(v) / max[j], col)}</span>`;
      }).join("")}
    </div>`).join("")}
  </div>`;
}

function compare(m) {
  return `
  <section class="cv-sec" id="cv-compare" data-sec="compare" aria-labelledby="cv-h-compare">
    <h3 id="cv-h-compare">${icon("layers", "⚖️", { size: 15 })}Compare</h3>
    <p class="cv-lead">The ${m.peers.length} urban agglomerations closest in UN mid-2026 population. Choose an available City View to open it.</p>
    <div class="cv-seg" role="group" aria-label="Metrics">
      <button type="button" data-set="size" aria-pressed="true">Size &amp; wealth</button>
      <button type="button" data-set="housing" aria-pressed="false">Housing &amp; jobs</button>
    </div>
    <div data-compare>${compareTable(m, "size")}</div>
  </section>`;
}

function footer(m) {
  return `<div class="cv-foot">Ranks cover mapped urban agglomerations with data for each measure.
    <a href="#" data-pedia>Almanac ›</a></div>`;
}

/**
 * Fill the dock. handlers: {onClose, onState(idx), onPeer(id), onSite(site), onSiteHover(site|null), onPedia,
 * loadCounties() → Promise<counties.json|null>, loadData(name) → Promise<data|null>, onDistricts(list)} (the
 * metro's districts once districts.json is in, for the map plaques).
 */
/**
 * Scrolls the dock to a section (its tab id, e.g. "districts"). Citizens and districts arrive later and change the
 * heights above, so the section is re-aligned as they do, for up to 4 s or until the user scrolls themselves.
 */
export function goToSection(el, id) {
  const sec = el?.querySelector(`[data-sec="${id}"]`);
  if (!sec) return false;
  const align = () => {
    const nav = el.querySelector(".cv-tabs");
    el.scrollTop = Math.max(0, sec.offsetTop - (nav?.offsetHeight || 0) - 4);
    el.onscroll?.(); // the tab spy (a scroll event is not always sent for a programmatic jump)
  };
  align();
  let ro = null;
  const stop = () => {
    ro?.disconnect();
    ro = null;
    for (const t of ["wheel", "touchstart", "keydown", "pointerdown"]) el.removeEventListener(t, stop);
  };
  for (const t of ["wheel", "touchstart", "keydown", "pointerdown"]) el.addEventListener(t, stop, { passive: true });
  if (typeof ResizeObserver === "function") {
    ro = new ResizeObserver(() => { if (sec.isConnected) align(); else stop(); });
    for (const c of el.children) ro.observe(c);
  }
  setTimeout(stop, 4000);
  return true;
}

export function render(el, m, h) {
  el.classList.add("cv-dock");
  el.style.setProperty("--sc", css(m.stateRGB));
  el.innerHTML = header(m) + citizens(m) + districts(m) + economy(m) + workforce(m) + resources(m) + compare(m) + footer(m);
  el.scrollTop = 0;

  el.querySelector("[data-close]").onclick = () => h.onClose();
  el.querySelectorAll("[data-state]").forEach((b) => (b.onclick = () => h.onState(+b.dataset.state)));
  el.querySelector("[data-pedia]").onclick = (e) => { e.preventDefault(); h.onPedia(); };

  // Sites: hover lights the hex on the map, click flies there.
  el.querySelectorAll("[data-site]").forEach((b) => {
    const s = m.sites[+b.dataset.site];
    b.onclick = () => h.onSite(s);
    b.onmouseenter = b.onfocus = () => h.onSiteHover(s);
    b.onmouseleave = b.onblur = () => h.onSiteHover(null);
  });

  // Compare: metric sets and peer links (delegated, the table is re-rendered).
  const cmp = el.querySelector("[data-compare]");
  el.querySelectorAll("[data-set]").forEach((b) => (b.onclick = () => {
    el.querySelectorAll("[data-set]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    cmp.innerHTML = compareTable(m, b.dataset.set);
  }));
  cmp.addEventListener("click", (e) => {
    const b = e.target.closest("[data-peer]");
    if (b) h.onPeer(b.dataset.peer);
  });

  // Tabs scroll to their section; the active tab follows the scroll position.
  const nav = el.querySelector(".cv-tabs");
  const tabs = [...el.querySelectorAll("[data-tab]")];
  const secs = tabs.map((t) => el.querySelector(`[data-sec="${t.dataset.tab}"]`));
  tabs.forEach((t, k) => (t.onclick = () => {
    const top = secs[k].offsetTop - nav.offsetHeight - 4;
    el.scrollTo({ top, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }));
  const spy = () => {
    const y = el.scrollTop + nav.offsetHeight + 24;
    let k = 0;
    secs.forEach((s, j) => { if (s.offsetTop <= y) k = j; });
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 4) k = secs.length - 1;
    tabs.forEach((t, j) => t.classList.toggle("on", j === k));
  };
  el.onscroll = spy;
  spy();

  // Citizens and districts arrive with their files (each loaded once, on demand).
  const czHost = el.querySelector("[data-citizens]");
  Promise.resolve(h.loadData?.("citizens")).then((data) => {
    if (!czHost.isConnected) return;
    czHost.innerHTML = citizensHtml(m, data ?? null);
    mountCitizens(czHost, m, data);
  }, () => { if (czHost.isConnected) czHost.innerHTML = citizensHtml(m, null); });
  const dHost = el.querySelector("[data-districts]");
  const typeSlot = el.querySelector("[data-ctype]");
  Promise.resolve(h.loadData?.("districts")).then((dd) => {
    if (!dHost.isConnected) return;
    dHost.innerHTML = districtsHtml(m, dd ?? null, null);
    typeSlot.innerHTML = badgeHtml(m, dd ?? null);
    h.onDistricts?.(dd ? cityDistricts(dd, null, m.city.id) : []);
  }, () => { if (dHost.isConnected) dHost.innerHTML = districtsHtml(m, null, null); });

  // Member districts arrive with counties.json (loaded once, on demand).
  const host = el.querySelector("[data-counties]");
  Promise.resolve(h.loadCounties()).then((data) => {
    if (host.isConnected) host.innerHTML = countiesTable(m, data);
  }, () => { if (host.isConnected) host.innerHTML = `<p class="muted cv-note">District table unavailable.</p>`; });
}
