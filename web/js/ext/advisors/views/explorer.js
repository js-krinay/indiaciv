// Explorer: the generic slice-and-dice. Pick a level, any columns, filter, sort, plot any X / Y / size / colour,
// brush points onto the map, and show a column as a map lens where one exists.
import { periodLabel } from "../../../format.js";
import { esc, fin, colorScale, robustDomain, extent, RAMPS } from "../core/util.js";
import { fmtValue, fmtShort, fmtCell, parseNum, count3, int } from "../core/fmt.js";
import { chartPeriodLabel, rampLegend, swatchLegend } from "../core/charts.js";
import { createTable } from "../core/table.js";
import { createScatter } from "../core/scatter.js";
import { section, segmented, selectBox, sourcesHtml, frameBtn } from "../core/view.js";
import { rowsHighlight, fieldContext } from "../core/data.js";

const DEFAULT_COLS = {
  states: ["population", "growth", "gdp_pc", "median_income", "unemployment"],
  metros: ["states", "population", "growth", "gdp_pc", "median_income"],
  counties: ["state", "population", "density", "income", "poverty"],
};
const DEFAULT_XY = {
  states: { x: "median_income", y: "growth", s: "population", c: "unemployment" },
  metros: { x: "gdp_pc", y: "growth", s: "population", c: "median_income" },
  counties: { x: "income", y: "bachelors", s: "population", c: "density" },
};
const OPS = { num: [">", "≥", "<", "≤", "="], text: ["=", "contains", "≠"] };

export function columnPeriodLabels(observations) {
  const periods = new Map();
  for (const meta of observations) {
    if (meta.period) periods.set(meta.period, meta);
  }
  return [...periods.values()]
    .sort((a, b) => Number(a.vintage === "older") - Number(b.vintage === "older"))
    .map((meta) => `<span class="column-period">${periodLabel(meta, " · ")}</span>`).join("");
}

export function explorerColourLegend(field, values, period = "", log = false) {
  if (!field) return { color: null, html: "" };
  const numeric = field.format !== "text";
  const observations = values.filter((value) => numeric ? fin(value) : value != null);
  if (!observations.length) {
    const date = periodLabel(field, " ", { plain: true });
    return { color: null, html: `<p class="adv-note">${esc(`No${date} data`)}</p>` };
  }
  const label = [field.label, period].filter(Boolean).join(" · ");
  if (numeric) {
    const signed = field.format === "signed";
    const domain = robustDomain(observations, 0.03, log);
    const ramp = signed ? RAMPS.div : field.higher_is === "bad" ? RAMPS.heat : RAMPS.seq;
    const color = colorScale(signed ? { type: "div", domain, mid: 0 } : { type: "seq", domain, log, ramp });
    const magnitude = Math.max(...domain.map(Math.abs));
    const html = rampLegend({ ramp, domain: signed ? [-magnitude, magnitude] : domain, log,
      fmt: (v) => fmtShort(field.format, v), label, mid: signed ? 0 : null });
    return { color, html };
  }
  const categories = [...new Set(observations)];
  const palette = ["#e0b54c", "#4a86d6", "#3f9c82", "#c46a4f", "#9a7bc9", "#6e9a3c", "#d98a2b", "#5fbfbf", "#c9a0c0", "#a3a3c2", "#e8774a", "#b9b06a"];
  const colours = new Map(categories.slice(0, 12).map((key, i) => [key, palette[i]]));
  const fallback = "#8b8070";
  const swatches = [...colours].map(([label, color]) => ({ label, color }));
  if (categories.length > 12) swatches.push({ label: "others", color: fallback });
  return { color: (value) => colours.get(value) || fallback, html: swatchLegend(swatches, label) };
}

// Remember the explorer's setup per viewer (a convenience; the page works without it).
const STORE = "indiaciv.explorer.v1";
const load = () => { try { return JSON.parse(localStorage.getItem(STORE) || "null"); } catch { return null; } };
const save = (s) => { try { localStorage.setItem(STORE, JSON.stringify(s)); } catch { /* private mode */ } };

export async function mount(ctx) {
  const { app, data, el, link } = ctx;
  const avail = ["states", "metros", "counties"].filter((k) => data.levels[k]);
  const saved = load() || {};
  const st = {
    level: avail.includes(ctx.params.level) ? ctx.params.level : avail.includes(saved.level) ? saved.level : "metros",
    cols: { ...DEFAULT_COLS, ...app.data.nation?.explorer?.columns, ...(saved.cols || {}) },
    xy: { ...DEFAULT_XY, ...app.data.nation?.explorer?.axes, ...(saved.xy || {}) },
    filters: [],
    onlySel: false,
    sel: null,
  };
  if (ctx.params.field && data.levels[st.level].field(ctx.params.field) && !st.cols[st.level].includes(ctx.params.field)) {
    st.cols[st.level] = [...st.cols[st.level], ctx.params.field];
  }
  const persist = () => save({ level: st.level, cols: st.cols, xy: st.xy });
  const L = () => data.levels[st.level];

  // --- controls -------------------------------------------------------------------------------------------------
  const top = section(el, { title: "Explore the data", note: "Choose what to compare, filter it, sort the table, and plot any two columns. Hover a row or a point to see it on the map; drag across the chart to select a group." });
  const lvRow = document.createElement("div");
  lvRow.className = "adv-row";
  top.appendChild(lvRow);
  segmented(lvRow, {
    label: "Level", value: st.level,
    options: avail.map((k) => ({ value: k, label: data.levels[k].label })),
    onChange: (v) => { st.level = v; st.filters = st.filters.filter((f) => L().field(f.key)); st.sel = null; persist(); rebuild(); },
  });
  const colsBox = document.createElement("details");
  colsBox.className = "adv-cols";
  lvRow.appendChild(colsBox);

  const fRow = document.createElement("div");
  fRow.className = "adv-fbuild";
  top.appendChild(fRow);
  const chipsRow = document.createElement("div");
  chipsRow.className = "adv-row adv-filterbar";
  top.appendChild(chipsRow);
  const summary = document.createElement("p");
  summary.className = "adv-note adv-summary";
  top.appendChild(summary);

  // --- table ----------------------------------------------------------------------------------------------------
  const tBody = section(el, { title: "Table" });
  const selRow = document.createElement("div");
  selRow.className = "adv-row";
  tBody.appendChild(selRow);
  const tableHost = document.createElement("div");
  tBody.appendChild(tableHost);
  let table = null;

  // --- chart ----------------------------------------------------------------------------------------------------
  const cBody = section(el, { title: "Chart" });
  const axes = document.createElement("div");
  axes.className = "adv-axes";
  cBody.appendChild(axes);
  const scatterHost = document.createElement("div");
  cBody.appendChild(scatterHost);
  const legendEl = document.createElement("div");
  cBody.appendChild(legendEl);
  const lensRow = document.createElement("div");
  lensRow.className = "adv-row";
  cBody.appendChild(lensRow);
  const fieldInfo = document.createElement("div");
  fieldInfo.className = "adv-fieldinfo";
  cBody.appendChild(fieldInfo);
  const scatter = createScatter(scatterHost, {
    height: 320, points: [],
    onHover: (p) => { link.hover(p ? rowsHighlight(L(), [p.row]) : null); table?.setHot(p ? p.key : null, false); },
    onClick: (p) => L().focus(p.row),
    onBrush: (set) => { st.sel = set; applySelection(); },
  });
  const srcEl = document.createElement("div");
  el.appendChild(srcEl);

  // --- logic ----------------------------------------------------------------------------------------------------
  const fieldOpts = (withNone = false, numeric = true) => {
    const fs = L().fields.filter((f) => (numeric ? f.format !== "text" : f.key !== "name"));
    return [...(withNone ? [{ value: "", label: "None" }] : []), ...fs.map((f) => ({ value: f.key, label: f.label, group: f.group }))];
  };
  const numeric = (f) => f && f.format !== "text";
  const val = (r, k) => r.v[k] ?? null;
  const fmtF = (f, v) => fmtValue(f.format, v, f.unit);

  function passes(r) {
    for (const f of st.filters) {
      const fd = L().field(f.key);
      if (!fd) continue;
      const v = val(r, f.key);
      if (numeric(fd)) {
        if (!fin(v)) return false;
        const t = f.value;
        if (f.op === ">" && !(v > t)) return false;
        if (f.op === "≥" && !(v >= t)) return false;
        if (f.op === "<" && !(v < t)) return false;
        if (f.op === "≤" && !(v <= t)) return false;
        if (f.op === "=" && !(Math.abs(v - t) <= Math.abs(t) * 0.005 + 1e-9)) return false;
      } else {
        const s = String(v ?? "").toLowerCase(), t = String(f.value).toLowerCase();
        if (f.op === "=" && s !== t) return false;
        if (f.op === "≠" && s === t) return false;
        if (f.op === "contains" && !s.includes(t)) return false;
      }
    }
    return true;
  }
  const filtered = () => L().rows.filter(passes);

  function renderCols() {
    const on = new Set(st.cols[st.level]);
    const groups = new Map();
    for (const f of L().fields) {
      if (f.key === "name") continue;
      if (!groups.has(f.group)) groups.set(f.group, []);
      groups.get(f.group).push(f);
    }
    colsBox.innerHTML = `<summary class="adv-mini">Columns (${on.size})</summary><div class="adv-cols-pop">${[...groups].map(([g, list]) => `<fieldset><legend>${esc(g)}</legend>${list.map((f) => `<label title="${esc(f.description)}"><input type="checkbox" value="${esc(f.key)}"${on.has(f.key) ? " checked" : ""}> ${esc(f.label)}</label>`).join("")}</fieldset>`).join("")}</div>`;
  }
  colsBox.addEventListener("change", (e) => {
    const k = e.target.value;
    const list = st.cols[st.level].filter((x) => x !== k);
    if (e.target.checked) list.push(k);
    st.cols = { ...st.cols, [st.level]: list };
    colsBox.querySelector("summary").textContent = `Columns (${list.length})`;
    persist();
    buildTable();
  });

  function renderFilterBuilder() {
    fRow.innerHTML = "";
    const fs = L().fields;
    const fsel = selectBox(fRow, { label: "Filter", value: fs.find((f) => f.key === "population")?.key || fs[0].key, options: fs.map((f) => ({ value: f.key, label: f.label, group: f.group })) });
    const ops = document.createElement("select");
    ops.setAttribute("aria-label", "Comparison");
    const valIn = document.createElement("input");
    valIn.type = "text";
    valIn.placeholder = "e.g. 1M, 25%, KL";
    valIn.setAttribute("aria-label", "Value");
    const add = document.createElement("button");
    add.type = "button";
    add.className = "adv-mini";
    add.textContent = "Add";
    const syncOps = () => {
      const f = L().field(fsel.value);
      ops.innerHTML = (numeric(f) ? OPS.num : OPS.text).map((o) => `<option>${esc(o)}</option>`).join("");
      valIn.placeholder = numeric(f) ? (f.format === "pct" || f.format === "signed" ? "e.g. 25%" : f.format === "usd" || f.format === "money" ? "e.g. 80K" : "e.g. 1M") : st.level === "counties" ? "e.g. KL" : "text";
    };
    fsel.select.addEventListener("change", syncOps);
    syncOps();
    const submit = () => {
      const f = L().field(fsel.value);
      if (!f || !valIn.value.trim()) return;
      const v = numeric(f) ? parseNum(valIn.value, f.format) : valIn.value.trim();
      if (v == null) { valIn.setCustomValidity("Not a number"); valIn.reportValidity(); return; }
      valIn.setCustomValidity("");
      st.filters.push({ key: f.key, op: ops.value, value: v });
      valIn.value = "";
      refresh();
    };
    add.addEventListener("click", submit);
    valIn.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); submit(); } });
    fRow.append(ops, valIn, add);
    // quick presets
    const presets = document.createElement("span");
    presets.className = "adv-presets";
    const P = st.level === "counties" ? [["population", "≥", 1e5, "100K+ people"]] : [["population", "≥", 1e6, "1M+ people"], ["population", "≥", 2.5e5, "250K+"]];
    presets.innerHTML = P.map((p, i) => `<button type="button" class="adv-mini" data-preset="${i}">${esc(p[3])}</button>`).join("");
    presets.addEventListener("click", (e) => {
      const i = e.target.closest("[data-preset]")?.dataset.preset;
      if (i == null) return;
      const [key, op, value] = P[+i];
      st.filters = st.filters.filter((f) => f.key !== key);
      st.filters.push({ key, op, value });
      refresh();
    });
    fRow.appendChild(presets);
  }

  function renderChips() {
    chipsRow.innerHTML = st.filters.map((f, i) => {
      const fd = L().field(f.key);
      const txt = `${fd?.label || f.key} ${f.op} ${numeric(fd) ? fmtShort(fd.format, f.value) : f.value}`;
      return `<span class="adv-fchip">${esc(txt)}<button type="button" data-rm="${i}" aria-label="Remove filter ${esc(txt)}">✕</button></span>`;
    }).join("") + (st.filters.length > 1 ? `<button type="button" class="adv-mini" data-rm="all">Clear all</button>` : "") + (st.filters.length && filterHighlight() ? frameBtn() : "");
  }
  chipsRow.addEventListener("click", (e) => {
    const i = e.target.closest("[data-rm]")?.dataset.rm;
    if (i == null) return;
    if (i === "all") st.filters = [];
    else st.filters.splice(+i, 1);
    refresh();
  });

  function buildTable() {
    const lv = L();
    const keys = st.cols[st.level].filter((k) => lv.field(k));
    const isReligionShare = (k) => k === "faith" || k.startsWith("faith_") && k !== "faith_tradition";
    const sortKey = keys.includes("population") ? "population" : keys.find((k) => !isReligionShare(k)) || "name";
    const maxOf = (k) => { const e = extent(lv.rows.map((r) => val(r, k))); return e ? Math.max(Math.abs(e[0]), Math.abs(e[1])) : 1; };
    const cols = [
      { key: "name", label: lv.field("name")?.label || "Name", align: "l", width: "minmax(0,1.7fr)", value: (r) => r.name, html: (r) => `${esc(r.name)}${st.level !== "states" && r.sub ? ` <span class="sub">${esc(r.sub)}</span>` : ""}` },
      ...keys.map((k) => {
        const f = lv.field(k);
        const title = fieldContext(data, lv, f);
        const observations = lv.rows.filter((r) => val(r, k) != null).map((r) => lv.meta(f, r));
        const periods = new Set(observations.map((meta) => meta.period));
        const mixed = periods.size > 1;
        const scopes = f.censusCivic && lv.id === "metros" ? new Set(observations.map((meta) => meta.scope)) : new Set();
        const scopeHeading = scopes.size === 1 && scopes.has("urban member districts")
          ? '<span class="column-period">Urban member districts</span>' : "";
        const headingPeriods = f.periodScope === "per_state" ? [{ period: f.period, vintage: f.vintage }] : observations;
        const heading = columnPeriodLabels(headingPeriods) + scopeHeading;
        const text = (r) => {
          const v = val(r, k);
          return v == null ? "" : `${lv.meta(f, r).estimated ? "≈" : ""}${fmtCell(f.format, v, f.unit)}`;
        };
        return {
          key: k, label: f.label, title, hideRank: f.hideRank, sortable: !isReligionShare(k), value: (r) => val(r, k),
          short: heading ? esc(f.label) + heading : null,
          html: (r) => {
            const meta = lv.meta(f, r);
            const scope = scopes.size > 1 && meta.scope && val(r, k) != null ? ` · ${esc(meta.scope)}` : "";
            return esc(text(r)) + (mixed && val(r, k) != null ? periodLabel(meta, " · ") : "")
              + scope + (meta.sparse && val(r, k) != null ? `<span class="column-period"> · ${esc(meta.coverage)}</span>` : "");
          },
          width: numeric(f) ? undefined : "minmax(0,.8fr)", align: numeric(f) ? "r" : "l",
          tip: (r) => val(r, k) == null ? "" : `${fmtF(f, val(r, k))} · ${fieldContext(data, lv, f, r)}`,
          bar: k === sortKey && numeric(f) ? { max: maxOf(k), color: "rgba(154,123,201,.32)" } : null,
        };
      }),
    ];
    if (!table) {
      table = createTable(tableHost, {
        caption: `${lv.label} table`, columns: cols, rows: [], sort: { key: sortKey, dir: "desc" }, rank: true, maxHeight: 360,
        search: `Search ${lv.label.toLowerCase()}`,
        onHover: (r) => { link.hover(r ? rowsHighlight(L(), [r]) : null); scatter.setHot(r ? r.key : null); },
        onClick: (r) => L().focus(r),
      });
    } else table.setColumns(cols, { key: sortKey, dir: "desc" });
    refreshRows();
  }

  function axisSelects() {
    axes.innerHTML = "";
    const xy = st.xy[st.level];
    const fix = (k, fallback) => (L().field(k) && numeric(L().field(k)) ? k : fallback);
    xy.x = fix(xy.x, "population");
    xy.y = fix(xy.y, "population");
    xy.s = xy.s && L().field(xy.s) ? xy.s : "";
    xy.c = xy.c && L().field(xy.c) ? xy.c : "";
    const mk = (key, label, none) => selectBox(axes, {
      label, value: xy[key], options: fieldOpts(none, key !== "c"),
      onChange: (v) => { xy[key] = v; if (key === "x" || key === "y") delete xy[`log${key}`]; persist(); drawScatter(); },
    });
    mk("x", "X", false);
    mk("y", "Y", false);
    mk("s", "Size", true);
    mk("c", "Colour", true);
    const logs = document.createElement("span");
    logs.className = "adv-logs";
    logs.innerHTML = `<label class="adv-check"><input type="checkbox" data-log="x"> log X</label><label class="adv-check"><input type="checkbox" data-log="y"> log Y</label>`;
    axes.appendChild(logs);
    logs.addEventListener("change", (e) => {
      const a = e.target.dataset.log;
      xy[`log${a}`] = e.target.checked;
      persist();
      drawScatter();
    });
  }
  // A skewed, positive column reads better on a log axis.
  const autoLog = (k, rows) => {
    const e = extent(rows.map((r) => val(r, k)), true);
    const all = rows.map((r) => val(r, k)).filter(fin);
    return !!e && all.every((v) => v > 0) && e[1] / e[0] > 60;
  };

  function drawScatter() {
    const lv = L();
    const xy = st.xy[st.level];
    const rows = filtered();
    const fx = lv.field(xy.x), fy = lv.field(xy.y), fs = xy.s ? lv.field(xy.s) : null, fc = xy.c ? lv.field(xy.c) : null;
    const axesFields = [...new Set([fx, fy, fs, fc].filter(Boolean))];
    const scalePeriod = (field) => field && chartPeriodLabel(rows
      .filter((r) => val(r, field.key) != null).map((r) => lv.meta(field, r)));
    const lx = xy.logx ?? autoLog(xy.x, rows), ly = xy.logy ?? autoLog(xy.y, rows);
    axes.querySelector('[data-log="x"]').checked = lx;
    axes.querySelector('[data-log="y"]').checked = ly;
    const legend = explorerColourLegend(fc, rows.map((r) => val(r, fc?.key)),
      scalePeriod(fc), fc && autoLog(fc.key, rows));
    const { color } = legend;
    legendEl.innerHTML = legend.html;
    const big = [...rows].sort((a, b) => (val(b, "population") || 0) - (val(a, "population") || 0)).slice(0, st.level === "states" ? 10 : 6).map((r) => r.key);
    scatter.update({
      points: rows.map((r) => {
        const estimated = axesFields
          .filter((f) => val(r, f.key) != null && lv.meta(f, r).estimated).map((f) => f.label);
        return { key: r.key, x: val(r, xy.x), y: val(r, xy.y), s: fs ? val(r, xy.s) : null,
          c: fc ? val(r, xy.c) : null, label: r.name, sub: r.sub, row: r,
          extra: [
            estimated.length ? `IndiaCiv estimates · ${estimated.join(", ")}` : "",
            ...axesFields.flatMap((f) => {
              const meta = lv.meta(f, r);
              if (val(r, f.key) == null || meta.vintage !== "older") return [];
              return [[f.label, periodLabel(meta, "", { plain: true }), f.censusCivic && meta.scope, meta.sparse && meta.coverage].filter(Boolean).join(" · ")];
            }),
          ].filter(Boolean).join(" · ") };
      }),
      x: { label: fx.label, period: scalePeriod(fx), fmt: (v) => fmtShort(fx.format, v), log: lx },
      y: { label: fy.label, period: scalePeriod(fy), fmt: (v) => fmtShort(fy.format, v), log: ly },
      size: fs && numeric(fs) ? { label: fs.label, fmt: (v) => fmtF(fs, v), max: st.level === "counties" ? 13 : 15, min: 1.6 } : null,
      radius: st.level === "counties" ? 2.2 : 3.5,
      color, colorLabel: fc && [fc.label, scalePeriod(fc)].filter(Boolean).join(" · "), colorFmt: (v) => (fc && numeric(fc) ? fmtF(fc, v) : String(v)),
      labels: big,
      refLines: [], refX: [], refY: [],
    });
    if (st.sel) scatter.setSelected(st.sel);
    // Lens buttons for the plotted columns that have a matching map lens.
    lensRow.innerHTML = "";
    const lensFields = [fc, fy, fx].map((f) => {
      const row = rows.find((r) => f && val(r, f.key) != null);
      return f && lv.meta(f, row);
    }).filter((f, i, a) => f && f.lens && a.findIndex((g) => g && g.lens === f.lens) === i);
    for (const f of lensFields) {
      const lens = app.lensById.get(f.lens);
      if (!lens) continue;
      const b = document.createElement("button");
      b.type = "button";
      b.className = "adv-lensbtn";
      const on = app.state.lens?.id === lens.id;
      b.setAttribute("aria-pressed", String(on));
      b.textContent = on ? `Showing the ${lens.name} lens` : `Show ${f.label} on the map as a lens`;
      b.addEventListener("click", () => { app.setLens(app.state.lens?.id === lens.id ? null : lens.id); drawScatter(); });
      lensRow.appendChild(b);
    }
    fieldInfo.innerHTML = axesFields.map((f) =>
      `<p><b>${esc(f.label)}</b> · ${esc(fieldContext(data, lv, f))}</p>`).join("");
    const presented = [...new Set([...axesFields, ...st.cols[st.level].map(lv.field).filter(Boolean)])];
    const srcIds = presented.flatMap((f) => lv.rows.filter((r) => val(r, f.key) != null)
      .flatMap((r) => [lv.meta(f, r).source].flat()));
    srcEl.innerHTML = sourcesHtml(data, srcIds, [
      "≈ marks an IndiaCiv estimate. A blank cell indicates an unavailable value.",
      "Hover a column header or a value for its period, unit and source.",
    ]);
  }

  function applySelection() {
    const lv = L();
    const sel = st.sel ? lv.rows.filter((r) => st.sel.has(r.key)) : [];
    link.base(sel.length ? rowsHighlight(lv, sel, { dim: true }) : filterHighlight(), { frame: sel.length > 1 || (!sel.length && st.filters.length > 0) });
    table?.setSelected(st.sel);
    selRow.innerHTML = st.sel ? `<span class="adv-fchip">${int(st.sel.size)} selected on the chart<button type="button" data-clear-sel aria-label="Clear the selection">✕</button></span>${frameBtn()}
      <label class="adv-check"><input type="checkbox" data-only${st.onlySel ? " checked" : ""}> Only show the selection</label>` : `<span class="adv-note">Tip: drag across the chart below to select a group.</span>`;
    refreshRows();
    updateSummary();
  }
  selRow.addEventListener("click", (e) => { if (e.target.closest("[data-clear-sel]")) { st.sel = null; st.onlySel = false; scatter.setSelected(null); applySelection(); } });
  selRow.addEventListener("change", (e) => { if (e.target.matches("[data-only]")) { st.onlySel = e.target.checked; refreshRows(); } });

  // With filters on, outline the rows that pass (when there are not too many to read).
  function filterHighlight() {
    if (!st.filters.length) return null;
    const rows = filtered();
    if (!rows.length || rows.length > (st.level === "counties" ? 1500 : 300)) return null;
    return rowsHighlight(L(), rows, { dim: true, ringMax: 12 });
  }

  function refreshRows() {
    if (!table) return;
    let rows = filtered();
    if (st.onlySel && st.sel) rows = rows.filter((r) => st.sel.has(r.key));
    table.setRows(rows);
  }
  function updateSummary() {
    const rows = filtered();
    const field = L().field("population");
    const population = rows.filter((r) => val(r, "population") != null);
    const period = new Set(population.map((r) => L().meta(field, r).period));
    const total = period.size === 1 && population.length === rows.length
      ? ` · ${count3(population.reduce((sum, r) => sum + val(r, "population"), 0))} people${periodLabel(L().meta(field, population[0]), " · ")}`
      : "";
    summary.innerHTML = `<b>${int(rows.length)}</b> of ${int(L().rows.length)} ${esc(L().label.toLowerCase())}${total}${st.sel ? ` · <b>${int(st.sel.size)}</b> selected` : ""}`;
  }
  function refresh() {
    renderChips();
    st.sel = null;
    scatter.setSelected(null);
    refreshRows();
    drawScatter();
    applySelection();
  }
  function rebuild() {
    if (table) { table.destroy(); table = null; }
    renderCols();
    renderFilterBuilder();
    axisSelects();
    buildTable();
    refresh();
  }
  rebuild();

  const initialRow = L().byKey.get(ctx.params.row);
  if (initialRow) {
    link.base(rowsHighlight(L(), [initialRow]));
    L().focus(initialRow);
    table.setHot(initialRow.key);
    table.el.querySelector(".adv-tr.hot")?.scrollIntoView({ block: "nearest" });
  }

  const hostRowAt = (cell) => (cell >= 0 ? L().rowAtCell(cell) : null);
  return {
    destroy() { table?.destroy(); scatter.destroy(); },
    onMapHover(h) {
      const r = hostRowAt(h?.cell);
      scatter.setHot(r ? r.key : null);
      table?.setHot(r ? r.key : null);
    },
    onEscape() {
      if (st.sel) { st.sel = null; st.onlySel = false; scatter.setSelected(null); applySelection(); return true; }
      return false;
    },
  };
}
