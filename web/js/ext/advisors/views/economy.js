// Economy advisor: GDP by industry, metro GDP on the map, leaders, specialisation and growth vs output.
import { esc, fin, ratio, colorScale, robustDomain, RAMPS } from "../core/util.js";
import { money, dollars, pct, int, signedPct, count3, fmtShort } from "../core/fmt.js";
import { barList, rampLegend, sizeLegend } from "../core/charts.js";
import { createTable } from "../core/table.js";
import { createScatter } from "../core/scatter.js";
import { section, tiles, segmented, selectBox, sourcesHtml, frameBtn } from "../core/view.js";
import { rowsHighlight } from "../core/data.js";
import { icon } from "../../../ui/icon.js";
import { hasIcon } from "../../../icons.js";

export const METRO_MIN = 250000;
const short = (s) => String(s || "").replace(/\s*\(.*\)\s*$/, "");
const indIcon = (k) => (hasIcon(`i-${k}`) ? icon(`i-${k}`, "•", { size: 14 }) : k === "government" ? icon("i-public_admin", "🏛", { size: 14 }) : "");

export function mount(ctx) {
  const { app, data, el, link, params } = ctx;
  const nation = app.data.nation;
  const n = nation.nation || {};
  const metros = data.levels.metros;
  const rows = metros.rows;
  const gdpInd = n.gdp_by_industry || {};
  const jobInd = Object.keys(nation.industries || {}).filter((key) => fin(n.jobs?.[key]));
  const period = nation.gdp_vintage || "";
  const growth = metros.field("economic_growth");
  const growthValue = (row) => growth ? metros.value(row, growth.key) : null;
  const growthPeriod = (meta) => [meta?.period, meta?.estimated && "IndiaCiv estimate"].filter(Boolean).join(" · ");

  // --- headline -------------------------------------------------------------------------------------------------
  const topInd = Object.entries(gdpInd).filter(([, v]) => fin(v)).sort((a, b) => b[1] - a[1])[0];
  el.insertAdjacentHTML("beforeend", tiles([
    { label: `GDP ${n.gdp_year || ""}`, value: money(n.gdp), sub: period },
    { label: "Per person", value: money(ratio(n.gdp, n.population)), sub: period },
    ...(topInd ? [{ label: "Top industry", value: short(nation.gdp_industries?.[topInd[0]] || topInd[0]), sub: `${pct(topInd[1] / n.gdp)} of GDP · ${period}` }] : []),
  ]));

  // --- GDP by industry ------------------------------------------------------------------------------------------
  let indBars;
  if (topInd) {
    const indBody = section(el, { title: "GDP by industry", kicker: period, note: "Value added by each industry, where the work is done. Hover an industry to light up the states where it is the biggest share of the economy; click it to rank the metros that specialise in it." });
    const indRows = Object.entries(gdpInd).filter(([, v]) => fin(v)).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({
      key: k, label: short(nation.gdp_industries?.[k] || k), full: nation.gdp_industries?.[k], value: v, text: money(v), sub: pct(v / n.gdp), icon: indIcon(k),
    }));
    const states = app.data.states || [];
    indBars = barList(indBody, {
      rows: indRows, ariaLabel: "GDP by industry",
      onHover: (r) => {
        if (!r) return link.hover(null);
        const top = states.map((s, i) => ({ i, v: ratio(s.gdp_by_industry?.[r.key], s.gdp) })).filter((x) => fin(x.v)).sort((a, b) => b.v - a.v).slice(0, 8);
        link.hover({ states: new Set(top.map((x) => x.i)), dimOthers: true });
      },
      onClick: (r) => { setIndustry(r.key === "government" ? "public_admin" : r.key); specBody?.scrollIntoView({ behavior: "smooth", block: "start" }); },
    });
  }

  // --- map: metro GDP circles -----------------------------------------------------------------------------------
  const mapBody = section(el, { title: "Urban economies on the map", kicker: period, note: "Each circle is a urban agglomeration: its area is estimated GDP, its colour GDP per person. Hover a circle for numbers; click to open it." });
  const ppDomain = robustDomain(rows.filter((r) => r.v.population >= 100000).map((r) => r.v.gdp_pc), 0.03, true) || [30000, 120000];
  const ppColor = colorScale({ type: "seq", domain: ppDomain, ramp: RAMPS.gold });
  const gMax = Math.max(...rows.map((r) => r.v.gdp || 0));
  const bubbles = ctx.bubbles("gdp", {
    rMax: 30, minR: 1.5, alpha: 0.6,
    tip: (b) => `<b>${esc(b.row.name)}</b> <span class="sub">${esc(b.row.sub)}</span><br>GDP <b>${money(b.row.v.gdp)}</b> · per person <b>${money(b.row.v.gdp_pc)}</b><br>${esc(period)} · IndiaCiv estimate`,
    onHover: (b) => { table.setHot(b ? b.key : null); scatter.setHot(b ? b.key : null); link.hover(b ? rowsHighlight(metros, [b.row]) : null); },
    onClick: (b) => app.selectCity(b.row.ref),
  });
  const bubbleItems = rows.filter((r) => fin(r.v.gdp)).map((r) => ({ key: r.key, x: app.w.grid.cx(r.ref.cell), y: app.w.grid.cy(r.ref.cell), value: r.v.gdp, color: ppColor(r.v.gdp_pc), row: r }));
  bubbles.set(bubbleItems, { vMax: gMax });
  const showBubbles = document.createElement("label");
  showBubbles.className = "adv-check";
  showBubbles.innerHTML = `<input type="checkbox" checked> Show GDP circles`;
  showBubbles.querySelector("input").addEventListener("change", (e) => bubbles.set(e.target.checked ? bubbleItems : [], { vMax: gMax }));
  mapBody.appendChild(showBubbles);
  mapBody.insertAdjacentHTML("beforeend", rampLegend({ ramp: RAMPS.gold, domain: ppDomain, fmt: money, label: "GDP per person" })
    + sizeLegend([1e10, 1e11, 1e12].filter((v) => v <= gMax), (v) => 30 * Math.sqrt(v / gMax) , money, "Circle area = GDP (at the home zoom)"));

  // --- leaders --------------------------------------------------------------------------------------------------
  const lBody = section(el, { title: "Leading urban agglomerations", kicker: period, note: `GDP per person ranks only urban agglomerations of ${count3(METRO_MIN)}+ people (small areas with one big plant or mine swing wildly). Output growth is an IndiaCiv estimate from a separate matched fiscal series.` });
  const big = rows.filter((r) => (r.v.population || 0) >= METRO_MIN);
  segmented(lBody, {
    label: "Rank by", value: "gdp",
    options: [{ value: "gdp", label: "Largest GDP" }, { value: "gdp_pc", label: "GDP per person" }, ...(growth ? [{ value: growth.key, label: growth.label }] : [])],
    onChange: (v) => { table.setRows(v === "gdp" ? rows : big); table.setColumns(cols, { key: v, dir: "desc" }); },
  });
  const cols = [
    { key: "name", label: "Urban agglomeration", align: "l", value: (r) => r.name, html: (r) => `${esc(r.name)} <span class="sub">${esc(r.sub)}</span>` },
    { key: "gdp", label: "GDP", value: (r) => r.v.gdp, text: (r) => money(r.v.gdp), bar: { max: gMax, color: "rgba(224,181,76,.35)" } },
    { key: "gdp_pc", label: "Per person", value: (r) => r.v.gdp_pc, text: (r) => money(r.v.gdp_pc) },
    ...(growth ? [{
      key: growth.key, label: growth.label, value: growthValue,
      text: (r) => fin(growthValue(r)) ? `≈${signedPct(growthValue(r))}` : "–",
      tip: (r) => growthPeriod(metros.meta(growth, r)),
    }] : []),
  ];
  const table = createTable(lBody, {
    caption: "Urban agglomerations by GDP", columns: cols, rows, sort: { key: "gdp", dir: "desc" }, rank: true, maxHeight: 280,
    search: "Search urban agglomerations",
    onHover: (r) => { link.hover(r ? rowsHighlight(metros, [r]) : null); bubbles.setHot(r ? r.key : null); scatter.setHot(r ? r.key : null); },
    onClick: (r) => app.selectCity(r.ref),
  });

  // --- specialisation -------------------------------------------------------------------------------------------
  let specBody, indSel, specTable, specInfo;
  let industry = params.industry && jobInd.includes(params.industry) ? params.industry : jobInd[0];
  const lq = (r, k = industry) => {
    const o = r.ref;
    const us = ratio(n.jobs?.[k], n.employed);
    return us ? ratio(ratio(o.jobs?.[k], o.employed), us) : null;
  };
  if (industry) {
    specBody = section(el, { title: "Who specialises in what", kicker: n.provenance?.jobs?.period, note: `PLFS Current Weekly Status, age 15+. Location quotient divides the estimated urban agglomeration share by the all-India rural and urban share. Worker counts are IndiaCiv estimates. Urban agglomerations of ${count3(METRO_MIN)}+ people; the 15 most specialised are outlined on the map.` });
    indSel = selectBox(specBody, {
      label: "Industry", value: industry,
      options: jobInd.map((k) => ({ value: k, label: short(nation.industries[k]) })),
      onChange: (v) => setIndustry(v),
    });
    specInfo = document.createElement("p");
    specInfo.className = "adv-note";
    specBody.appendChild(specInfo);
    specTable = createTable(specBody, {
      caption: "Most specialised urban agglomerations", rank: true, maxHeight: 260, rows: [],
      columns: [
        { key: "name", label: "Urban agglomeration", align: "l", value: (r) => r.name, html: (r) => `${esc(r.name)} <span class="sub">${esc(r.sub)}</span>` },
        { key: "share", label: "Share of jobs", value: (r) => ratio(r.ref.jobs?.[industry], r.ref.employed), text: (r) => pct(ratio(r.ref.jobs?.[industry], r.ref.employed)) },
        { key: "lq", label: "LQ", value: (r) => lq(r), text: (r) => (fin(lq(r)) ? `×${lq(r).toFixed(2)}` : "–"), bar: { max: 1, color: "rgba(74,134,214,.4)" } },
        { key: "workers", label: "Workers", value: (r) => r.ref.jobs?.[industry], text: (r) => count3(r.ref.jobs?.[industry]) },
      ],
      sort: { key: "lq", dir: "desc" },
      onHover: (r) => { link.hover(r ? rowsHighlight(metros, [r]) : null); scatter.setHot(r ? r.key : null); bubbles.setHot(r ? r.key : null); },
      onClick: (r) => app.selectCity(r.ref),
    });
  }

  // --- scatter --------------------------------------------------------------------------------------------------
  const scBody = section(el, { title: "Growth vs output", kicker: period, note: "Each dot is an urban agglomeration. Estimated GDP per person is on the horizontal axis, nominal output growth is on the vertical axis, and size shows projected population for July 2026. Unemployment colour uses urban benchmarks for age 15+ from PLFS, 1 Jul – 30 Sep 2026, or PLFS 2025. Hover for the observation period." });
  const scCtl = document.createElement("div");
  scCtl.className = "adv-row";
  scBody.appendChild(scCtl);
  let colorBy = specTable ? "lq" : "none", allMetros = false;
  selectBox(scCtl, {
    label: "Colour", value: colorBy,
    options: [...(specTable ? [{ value: "lq", label: "Specialisation (chosen industry)" }] : []), ...(metros.field("unemployment") ? [{ value: "unemployment", label: "Urban unemployment benchmark (15+)" }] : []), { value: "none", label: "None" }],
    onChange: (v) => { colorBy = v; drawScatter(); },
  });
  segmented(scCtl, { label: "Urban agglomerations", value: "big", options: [{ value: "big", label: `${count3(METRO_MIN)}+` }, { value: "all", label: "All" }], onChange: (v) => { allMetros = v === "all"; drawScatter(); } });
  const legendEl = document.createElement("div");
  const scatter = createScatter(scBody, {
    points: [], height: 300,
    x: { label: "GDP per person", period: `${period} · IndiaCiv estimate`, fmt: (v) => money(v), log: true },
    y: { label: growth?.label, period: growthPeriod(growth), fmt: (v) => fmtShort("signed", v) },
    size: { label: "Population", fmt: count3, max: 15, min: 2 },
    refY: [],
    onHover: (p) => { link.hover(p ? rowsHighlight(metros, [p.row]) : null); bubbles.setHot(p ? p.key : null); table.setHot(p ? p.key : null, false); },
    onClick: (p) => app.selectCity(p.row.ref),
    onBrush: (set) => {
      const sel = set ? rows.filter((r) => set.has(r.key)) : [];
      link.base(sel.length ? rowsHighlight(metros, sel, { dim: true }) : specHighlight(), { frame: sel.length > 1 });
      bubbles.setSelected(set);
      brushInfo.innerHTML = sel.length ? brushSummary(sel) : "";
    },
  });
  scBody.appendChild(legendEl);
  const brushInfo = document.createElement("div");
  brushInfo.className = "adv-brushinfo";
  scBody.appendChild(brushInfo);
  function brushSummary(sel) {
    const pop = sel.reduce((a, r) => a + (r.v.population || 0), 0);
    const gdp = sel.reduce((a, r) => a + (r.v.gdp || 0), 0);
    return `<b>${sel.length}</b> urban agglomerations selected · ${count3(pop)} people (1 July 2026) · ${money(gdp)} GDP (${period}) ${frameBtn()}<button type="button" class="adv-mini" data-clear>Clear</button>`;
  }
  brushInfo.addEventListener("click", (e) => { if (e.target.closest("[data-clear]")) { scatter.setSelected(null); link.base(specHighlight()); bubbles.setSelected(null); brushInfo.innerHTML = ""; } });

  function drawScatter() {
    const list = rows.filter((r) => allMetros || (r.v.population || 0) >= METRO_MIN);
    const cv = (r) => (colorBy === "lq" ? lq(r) : colorBy === "none" ? null : r.v[colorBy]);
    let color = null, legend = "";
    if (colorBy !== "none") {
      const dom = robustDomain(list.map(cv), 0.03, colorBy === "lq") || [0, 1];
      const spec = colorBy === "lq" ? { type: "seq", domain: [Math.max(0.2, dom[0]), Math.max(1.5, dom[1])], log: true, ramp: RAMPS.seq } : { type: "seq", domain: dom, ramp: colorBy === "unemployment" ? RAMPS.heat : RAMPS.gold };
      const cs = colorScale(spec);
      color = (c) => cs(c);
      const f = colorBy === "lq" ? (v) => `×${v.toFixed(1)}` : colorBy === "unemployment" ? (v) => pct(v) : money;
      legend = rampLegend({ ramp: spec.ramp, domain: spec.domain, fmt: f, log: spec.log, label: colorBy === "lq" ? `Specialisation in ${short(nation.industries[industry]).toLowerCase()}` : colorBy === "unemployment" ? "Unemployment" : "Median household income" });
    }
    const labels = [...list].sort((a, b) => (b.v.population || 0) - (a.v.population || 0)).slice(0, 8).map((r) => r.key);
    scatter.update({
      points: list.filter((r) => fin(r.v.gdp_pc) && fin(growthValue(r))).map((r) => ({ key: r.key, x: r.v.gdp_pc, y: growthValue(r), s: r.v.population, c: cv(r), label: r.name, sub: r.sub, row: r, extra: colorBy === "unemployment" && fin(r.v.unemployment) ? metros.meta(metros.field("unemployment"), r).period : null })),
      color, labels, colorLabel: colorBy === "none" ? null : colorBy === "lq" ? "LQ" : colorBy === "unemployment" ? "Unemployment" : "Income",
      colorFmt: colorBy === "lq" ? (v) => `×${(+v).toFixed(2)}` : colorBy === "unemployment" ? pct : dollars,
    });
    legendEl.innerHTML = legend;
  }

  let specTop = [];
  const specHighlight = () => (specTop.length ? rowsHighlight(metros, specTop, { ringMax: 15 }) : null);
  function setIndustry(k) {
    if (!specTable || !jobInd.includes(k)) return;
    industry = k;
    indSel.set(k);
    const list = big.filter((r) => fin(lq(r))).sort((a, b) => lq(b) - lq(a));
    specTop = list.slice(0, 15);
    const maxLq = Math.max(1, ...list.slice(0, 40).map((r) => lq(r)));
    specTable.setColumns([
      { key: "name", label: "Urban agglomeration", align: "l", value: (r) => r.name, html: (r) => `${esc(r.name)} <span class="sub">${esc(r.sub)}</span>` },
      { key: "share", label: "Share of jobs", value: (r) => ratio(r.ref.jobs?.[industry], r.ref.employed), text: (r) => pct(ratio(r.ref.jobs?.[industry], r.ref.employed)) },
      { key: "lq", label: "LQ", value: (r) => lq(r), text: (r) => (fin(lq(r)) ? `×${lq(r).toFixed(2)}` : "–"), bar: { max: maxLq, color: "rgba(74,134,214,.45)" } },
      { key: "workers", label: "Workers", value: (r) => r.ref.jobs?.[industry], text: (r) => count3(r.ref.jobs?.[industry]) },
    ], { key: "lq", dir: "desc" });
    specTable.setRows(list);
    const us = ratio(n.jobs?.[k], n.employed);
    specInfo.innerHTML = `India: <b>${pct(us)}</b> of employed residents age 15+ (${count3(n.jobs?.[k])} people, IndiaCiv estimate) work in ${esc(short(nation.industries[k]).toLowerCase())}.`;
    if (!scatter.selected) link.base(specHighlight());
    indBars?.setSelected(k === "public_admin" ? "government" : k);
    drawScatter();
  }
  if (specTable) setIndustry(industry);
  else drawScatter();

  el.insertAdjacentHTML("beforeend", sourcesHtml(data, ["gdp_fy26", "gsdp_fy26", "un_wup_cities", "plfs_2026_q3", "plfs_annual_2025", ...[growth?.source].flat().filter(Boolean)], [
    "Urban agglomeration GDP is an IndiaCiv estimate. Source periods for sector and output growth series are in Explorer.",
  ]));

  return {
    onMapHover(h) {
      const r = h?.cell >= 0 ? metros.rowAtCell(h.cell) : null;
      scatter.setHot(r ? r.key : null);
      specTable?.setHot(r ? r.key : null);
    },
    onEscape() {
      if (scatter.selected) { scatter.setSelected(null); link.base(specHighlight()); bubbles.setSelected(null); brushInfo.innerHTML = ""; return true; }
      return false;
    },
  };
}
