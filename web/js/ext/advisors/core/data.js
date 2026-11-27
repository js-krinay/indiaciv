// The advisors' data model: three levels of rows with typed fields and links between the rows and the hex map.
import { frameBox, focusPoint } from "./frame.js";

const LAND_KEYS = ["forest", "crop", "pasture", "grass", "shrub", "wetland", "developed"];
export const LAND_LABEL = {
  forest: "Forest", crop: "Cropland", pasture: "Pasture & hay", grass: "Grassland", shrub: "Scrub & desert", wetland: "Wetland", developed: "Built-up",
};
export const LAND_COLOR = {
  forest: "#3f7a3a", crop: "#d2c457", pasture: "#93b852", grass: "#b9b06a", shrub: "#c9a874", wetland: "#4f9a86", developed: "#9a8f9e",
};
export { LAND_KEYS };

// The district table's columns / fields / rows contract also supplies state and city observations.
function configurableColumns(table, id) {
  const cols = table?.columns || [];
  const fields = (table?.fields || []).filter((f) => f.key !== id && !f.hidden).map((f) => ({
    ...f, period: f.heading_caption || f.period, periodScope: f.period_scope,
    censusCivic: f.census_civic, hideRank: f.hide_rank,
  }));
  const rows = (table?.rows || []).map((r) => {
    const v = {};
    cols.forEach((k, j) => (v[k] = r[j]));
    return [v[id], v];
  });
  return {
    fields,
    values: new Map(rows),
    meta(f, row) {
      const meta = { ...f, ...table?.provenance?.[row?.key]?.[f.key] };
      return { ...meta, description: [meta.description, meta.coverage].filter(Boolean).join(" · ") };
    },
  };
}

export function buildData(app) {
  const { cities = [], nation = {}, sources = [], advisor_tables: tables } = app.data;
  const w = app.w;
  const grid = w?.grid;
  const world = w?.raw || app.data.world;
  const owner = world.owner;
  const countyOf = world.county || [];
  const n = grid?.size ?? owner.length;

  // --- cell indexes ---------------------------------------------------------------------------------------------
  const stateCells = new Map();
  const countyCells = new Map();
  for (let i = 0; i < n; i++) {
    const o = owner[i];
    if (!(o >= 0)) continue;
    if (!stateCells.has(o)) stateCells.set(o, []);
    stateCells.get(o).push(i);
    const c = countyOf[i];
    if (c >= 0) {
      if (!countyCells.has(c)) countyCells.set(c, []);
      countyCells.get(c).push(i);
    }
  }
  // cell → metro: footprints, smaller metros first so a bigger metro's majority wins; then every city's own cell.
  const cellMetro = new Map();
  for (let k = cities.length - 1; k >= 0; k--) for (const cell of cities[k].footprint || []) cellMetro.set(cell, cities[k]);
  for (const c of cities) if (c.cell != null) cellMetro.set(c.cell, c);
  const srcTitle = new Map(sources.map((s) => [s.id, s]));
  const nat = nation.nation || {};

  // --- states ---------------------------------------------------------------------------------------------------
  const stateColumns = configurableColumns(tables?.states, "abbr");
  const stateRows = world.states.map((s, idx) => ({
    key: s.abbr, name: s.name, sub: s.abbr, level: "states", ref: idx,
    v: stateColumns.values.get(s.abbr) || {},
  }));
  const states_ = makeLevel({
    id: "states", label: "States & UTs", noun: "state or UT",
    rows: stateRows, fields: stateColumns.fields, meta: stateColumns.meta,
    highlight: (rows) => ({ states: new Set(rows.map((r) => r.ref)) }),
    rowAtCell: (cell, byKey) => (owner[cell] >= 0 ? stateRows[owner[cell]] || null : null),
    focus: (row) => app.selectState(row.ref, { fly: true }),
    cellsOf: (row) => stateCells.get(row.ref) || [],
  });

  // --- metros ---------------------------------------------------------------------------------------------------
  const cityColumns = configurableColumns(tables?.metros, "id");
  const metroRows = cities.map((c) => ({
    key: c.id, name: c.name, sub: (c.states || []).join(" · "), level: "metros", ref: c,
    v: cityColumns.values.get(c.id) || {},
  }));
  const metroByCity = new Map(metroRows.map((r) => [r.ref, r]));
  const metros = makeLevel({
    id: "metros", label: "Urban agglomerations", noun: "urban agglomeration",
    rows: metroRows,
    fields: cityColumns.fields, meta: cityColumns.meta,
    highlight: (rows, o = {}) => {
      const cells = new Set();
      for (const r of rows) for (const c of r.ref.footprint || [r.ref.cell]) cells.add(c);
      return { cells, cities: rows.length <= (o.ringMax ?? 30) ? new Set(rows.map((r) => r.key)) : undefined };
    },
    rowAtCell: (cell) => { const c = cellMetro.get(cell); return c ? metroByCity.get(c) : null; },
    focus: (row) => app.selectCity(row.ref, { fly: true }),
    cellsOf: (row) => row.ref.footprint || [row.ref.cell],
  });

  // --- counties ---------------------------------------------------------------------------------------------------
  const countyColumns = configurableColumns(tables?.counties, "geoid");
  const countyRows = world.counties.map((c, i) => {
    const v = countyColumns.values.get(c.geoid) || {};
    return { key: c.geoid, name: c.name, full: c.name, sub: v.state, level: "counties", ref: i, v };
  });
  const rowByWorld = new Map(countyRows.map((r) => [r.ref, r]));
  const cellsOfRow = (r) => countyCells.get(r.ref) || [];
  const counties_ = makeLevel({
    id: "counties", label: "Districts", noun: "district",
    rows: countyRows, fields: countyColumns.fields, meta: countyColumns.meta,
    highlight: (rows) => {
      const cells = new Set();
      for (const r of rows) for (const c of cellsOfRow(r)) cells.add(c);
      return { cells };
    },
    rowAtCell: (cell) => (countyOf[cell] >= 0 ? rowByWorld.get(countyOf[cell]) || null : null),
    focus: (row) => {
      const cells = cellsOfRow(row);
      if (!cells.length) {
        if (row.v.center) focusPoint(app, ...row.v.center, 1.8);
        return;
      }
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (const c of cells) {
        const x = grid.cx(c), y = grid.cy(c);
        x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
      }
      const R = grid.R;
      frameBox(app, { x0: x0 - R, y0: y0 - R, x1: x1 + R, y1: y1 + R });
    },
    cellsOf: (row) => cellsOfRow(row),
  });

  return {
    app, nation, nat, levels: { states: states_, metros, counties: counties_ },
    stateCells, countyCells, cellMetro, metroByCity,
    source: (id) => {
      const entry = srcTitle.get(id);
      if (!entry) return null;
      const safeTitle = /\b(?:19\d\d|20(?:0\d|1\d|2[0-5]))\b/.test(entry.title) ? entry.publisher : entry.title;
      return { ...entry, title: id === "datameet" ? "DataMeet community maps of India" :
        id === "census_a01" ? "Census of India district areas" : safeTitle || entry.title };
    },
  };
}

function makeLevel(def) {
  const fieldByKey = new Map(def.fields.map((f) => [f.key, f]));
  const byKey = new Map(def.rows.map((r) => [r.key, r]));
  return {
    ...def,
    byKey,
    field: (k) => fieldByKey.get(k) || null,
    value: (row, k) => row.v[k] ?? null,
    numericFields: () => def.fields.filter((f) => f.format !== "text"),
    /** Add fields after the fact (optional files that load on demand); a key already present is skipped. */
    addFields(list) {
      for (const f of list) {
        if (fieldByKey.has(f.key)) continue;
        def.fields.push(f);
        fieldByKey.set(f.key, f);
      }
    },
  };
}

/** The highlight for a set of rows of one level, with defaults (gold outline, other land dimmed when asked). */
export function rowsHighlight(level, rows, opts = {}) {
  if (!level || !rows || !rows.length) return null;
  const one = rows.length === 1 ? rows[0] : null;
  const label = opts.label ?? (one ? (one.level === "states" ? one.name : `${one.full || one.name}${one.sub ? `, ${one.sub}` : ""}`) : "");
  return { ...level.highlight(rows, opts), dimOthers: !!opts.dim, color: opts.color, label };
}

export function fieldContext(data, level, field, row) {
  const records = row ? [row] : level.rows.filter((r) => r.v[field.key] != null);
  const details = records.length ? records.map((r) => level.meta(field, r)) : [field];
  const unique = (values) => [...new Set(values.filter(Boolean))];
  const periods = unique(details.map((m) => m.period));
  const sources = unique(details.flatMap((m) => m.source)).map((id) => data.source(id)?.title || id);
  const estimate = details.every((m) => m.estimated) ? "IndiaCiv estimate" :
    details.some((m) => m.estimated) ? "Includes IndiaCiv estimates" : "";
  const statuses = unique(details.map((m) => m.status));
  const descriptions = unique(details.map((m) => m.description));
  return [field.unit, ...periods, estimate, ...statuses, ...sources, descriptions.length === 1 ? descriptions[0] : field.description]
    .filter(Boolean).join(" · ");
}
