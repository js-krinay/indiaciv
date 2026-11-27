import { resolveTables } from "../terrain.js";

export const categories = {
  home: "Home", state: "States & territories", wonder: "Wonders", terrain: "Terrain",
  resource: "Resources", lens: "Lenses", city: "Cities", river: "Rivers", rail: "Railways",
  trade: "Trade", protected: "Protected land", yield: "Yields", source: "Sources",
};
export const normalize = (value) => String(value ?? "").normalize("NFD").replace(/\p{M}/gu, "")
  .toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
const slug = (s) => normalize(s).replaceAll(" ", "-");
const groupLabels = { base: "Base", water: "Water", relief: "Relief", features: "Feature", cover: "Land cover" };
const ut = new Set(["AN", "CH", "DH", "DL", "JK", "LA", "LD", "PY", "DN", "DD"]);
const aliases = {
  "state/OD": "Orissa",
  "state/UK": "Uttaranchal",
  "state/PY": "Pondicherry",
  "river/ganga": "Ganges",
  "river/yamuna": "Jamuna",
  "wonder/whc-251": "Red Fort of Agra",
  "wonder/whc-945": "Victoria Terminus CSMT",
};
const cityAliases = { Mumbai: "Bombay", Chennai: "Madras", Kolkata: "Calcutta", Bengaluru: "Bangalore", Kochi: "Cochin" };
const sourceLabels = {
  census_a01: "Census of India · Table A-01",
  datameet: "DataMeet boundary data",
  etopo: "NOAA ETOPO1",
  etopo_2022: "NOAA ETOPO relief",
  india_terrain: "ESA WorldCover",
  tg_projections: "Technical Group population projections",
  un_wup_cities: "UN DESA urban population projections",
  worldpop_age: "WorldPop age and sex estimates",
};

export function shortSourceTitle(row) {
  return sourceLabels[row?.id] || row?.short_title || row?.publisher || "Dataset details";
}

export function terrainRoute(field, row) {
  return `terrain/${field === "features" ? "feature" : field}-${row.key || slug(row.name)}`;
}

export function indexFeatureCells(world) {
  const byCell = new Map();
  for (const [id, cells] of Object.entries(world.tables?.feature_cells || {})) {
    for (const cell of cells) {
      if (!byCell.has(cell)) byCell.set(cell, []);
      byCell.get(cell).push(Number(id));
    }
  }
  return byCell;
}

export function buildPediaIndex(data, featureCells = indexFeatureCells(data.world)) {
  const entries = new Map();
  const add = (kind, id, title, props = {}) => {
    const key = `${kind}/${id}`;
    const entry = { kind, id: String(id), key, title, category: categories[kind], related: [], sources: [], ...props,
      aliases: [aliases[key], ...[props.aliases].flat()].filter(Boolean) };
    entries.set(key, entry);
    return entry;
  };
  for (const [kind, title] of Object.entries(categories)) add(kind, "index", title);

  const { world, w } = data;
  const tileStates = [];
  const states = new Map();
  const citiesByCell = new Set((data.cities || []).filter((row) => row.cell != null).map((row) => row.cell));
  for (const [idx, row] of (world.states || []).entries()) {
    const id = row.abbr || row.fips;
    if (!id || id === "00") continue;
    const entry = add("state", id, row.name, {
      row: data.states?.[idx] || row, cells: [], group: ut.has(id) ? "Union territory" : "State", aliases: id,
      sources: ["datameet", "soi_outline", "tg_projections", data.states?.[idx]?.age_source,
        ...Object.values(data.states?.[idx]?.metrics || {}).map((metric) => metric.source)],
    });
    tileStates[idx] = entry;
    states.set(id, entry);
  }
  for (const row of data.states || []) {
    const id = row?.abbr || row?.fips;
    if (id && id !== "00" && !states.has(id)) {
      states.set(id, add("state", id, row.name, {
        row, cells: [], group: ut.has(id) ? "Union territory" : "State", aliases: id,
        sources: ["datameet", "tg_projections", row.age_source],
      }));
    }
  }
  const associate = (entry, ids) => {
    for (const id of ids) {
      const st = states.get(id);
      if (!st) continue;
      st.related.push(entry.key);
      entry.related.push(st.key);
      (entry.geographies ||= new Set()).add(st);
    }
  };

  for (const row of data.cities || []) {
    const rank = row.ranks?.population;
    if (!rank || rank > 50) continue;
    const entry = add("city", row.id, row.name, {
      row, location: row.states?.map((id) => states.get(id)?.title || id).join(" · "),
      aliases: [row.full, cityAliases[row.name]], sources: ["un_wup_cities"],
      target: row.cell == null ? null : { kind: "city", row },
    });
    associate(entry, row.states || []);
  }
  for (const row of data.wonders?.wonders || []) {
    const entry = add("wonder", row.id, row.name, {
      row, group: row.kind === "natural" ? "Natural" : row.kind === "university" ? "Research" : "Built",
      location: row.foreign_side ? "Tibet" : row.location || states.get(row.state)?.title,
      sources: [...new Set([...(row.sources || data.wonders.sources || []), ...(row.extent_sources || [])])],
      target: Number.isFinite(row.x) && Number.isFinite(row.y) ? { kind: "wonder", row } : null,
    });
    if (!row.foreign_side) associate(entry, [row.state]);
  }

  const tables = w?.tables || resolveTables(world.tables);
  const terrain = {};
  const terrainSources = {
    base: ["koppen_geiger", "india_terrain", "soi_political_map"],
    water: ["soi_political_map", "soi_outline", "etopo", "natural_earth"],
    relief: [tables.base.length ? "etopo_2022" : "etopo"], cover: ["india_terrain"],
    features: ["india_terrain", "koppen_geiger", "glwd_v2", "gfplain", "global_mangrove_watch",
      "allen_coral_atlas", "gvp_vents", "varkala_geoheritage", "chennai_marina", "chilika_saltmarsh"],
  };
  for (const field of ["base", "water", "relief", "features", "cover"]) {
    if (field === "cover" && tables.base.length) continue;
    terrain[field] = new Map();
    for (const row of tables[field]) {
      if (!row.id && field !== "relief" && field !== "base") continue;
      const id = terrainRoute(field, row).split("/")[1];
      terrain[field].set(row.id, add("terrain", id, row.name, {
        row, field, group: groupLabels[field], count: 0,
        sources: terrainSources[field],
      }));
    }
  }
  const record = (entry, cell) => {
    if (!entry) return;
    entry.count++;
    if (entry.cell == null || (citiesByCell.has(entry.cell) && !citiesByCell.has(cell))) entry.cell = cell;
  };
  const owners = world.owner || [];
  const water = w?.water || world.water || [];
  for (let cell = 0; cell < owners.length; cell++) {
    const indianLand = !water[cell] && owners[cell] >= 0;
    if (indianLand) {
      tileStates[owners[cell]]?.cells.push(cell);
      record(terrain.relief.get((w?.relief || world.relief)?.[cell]), cell);
      record(terrain.cover?.get(world.cover?.[cell]), cell);
    }
    if (water[cell]) record(terrain.water.get(water[cell]), cell);
    if (indianLand || water[cell]) {
      record(terrain.base.get(world.base?.[cell]), cell);
      for (const id of new Set([...(world.features?.[cell] || []), ...(featureCells.get(cell) || [])])) record(terrain.features.get(id), cell);
    }
  }
  for (const entry of states.values()) {
    entry.cell = entry.cells.find((cell) => !citiesByCell.has(cell)) ?? entry.cells[0];
    if (entry.cells.length) entry.target = { kind: "state", id: entry.id };
  }
  for (const sample of world.tables?.terrain_examples || []) {
    for (const field of ["base", "relief", "features"]) {
      const ids = field === "features" ? sample.features || [] : [sample[field]];
      for (const id of ids) {
        const entry = terrain[field].get(id);
        if (!entry) continue;
        (entry.examples ||= []).push(sample);
        if (!entry.example) {
          entry.example = sample;
          entry.cell = sample.cell;
        }
      }
    }
  }
  for (const field of Object.values(terrain)) for (const entry of field.values()) {
    if (entry.cell != null) entry.target = { kind: "cell", cell: entry.cell };
  }
  for (const site of world.featureSites || []) {
    const entry = terrain.features.get(site.id);
    if (!entry) continue;
    (entry.sites ||= []).push(site);
    entry.target ||= { kind: "point", point: site.point || site.line.slice(0, 2) };
  }

  const types = new Map();
  const resourceGroups = { bonus: "Bonus", luxury: "Luxury", strategic: "Strategic", other: "Other" };
  for (const row of data.resources?.types || []) {
    types.set(row.id, add("resource", row.id, row.name, {
      row, group: resourceGroups[row.resource_class] || "Other", sources: [row.source], items: [],
    }));
  }
  const resourceStates = new Map();
  for (const row of data.resources?.items || []) {
    const entry = types.get(row.type);
    if (!entry) continue;
    entry.items.push(row);
    entry.sources.push(row.source);
    if (row.state) {
      if (!resourceStates.has(entry)) resourceStates.set(entry, new Set());
      resourceStates.get(entry).add(row.state);
    }
    if (Number.isFinite(row.x) && Number.isFinite(row.y)) entry.target ||= { kind: "resource", row };
  }
  for (const [entry, ids] of resourceStates) associate(entry, ids);

  const lensGroups = new Map(data.lenses?.groups?.map((g) => [g.id, g.name]));
  for (const row of data.lenses?.lenses || []) add("lens", row.id, row.name, {
    row, group: lensGroups.get(row.group), geography: row.geography || ({
      city_bad_air: "Urban agglomerations with eligible station coverage",
      district_pm25: "District estimates from reporting stations",
      monsoon_2026: "IMD meteorological subdivisions",
    })[row.id] || lensGroups.get(row.group), sources: [row.source, ...(row.sources || [])],
    target: row.period && row.values?.some(Number.isFinite) ? { kind: "lens", id: row.id } : null,
  });
  for (const row of data.nation?.yields || []) add("yield", row.key, row.label, { row, sources: row.sources || [] });

  const rivers = new Map();
  for (const edge of world.river_edges || []) {
    for (const name of edge.names || []) {
      const entry = rivers.get(name) || add("river", slug(name), name, {
        edges: [], sources: ["open_rivers", "natural_earth", "hydrolakes"],
      });
      rivers.set(name, entry);
      entry.edges.push(edge);
    }
  }
  for (const entry of rivers.values()) {
    entry.cells = [...new Set(entry.edges.flatMap((edge) => edge.cells || []))].filter((cell) => cell >= 0);
    const edge = entry.edges[Math.floor(entry.edges.length / 2)];
    if (edge.pts?.length >= 2) entry.target = { kind: "point", point: edge.pts.slice(0, 2) };
    entry.cell = edge.cells?.find((cell) => cell >= 0);
  }
  for (const row of data.infrastructure?.freight?.rows || []) {
    add("rail", row[0], row[1], { row, group: "Freight reporting zones", aliases: row[0], sources: data.infrastructure.sources });
  }

  for (const [name, cells] of Object.entries(data.infrastructure?.rail_corridors || {})) {
    const cell = cells[Math.floor(cells.length / 2)];
    const point = cell != null && w ? [w.grid.cx(cell), w.grid.cy(cell)] : null;
    add("rail", slug(name), name, {
      group: "Trunk corridors", cells, cell, sources: ["osm_transport"],
      target: point && { kind: "rail", point },
    });
  }
  const trade = data.infrastructure?.trade;
  if (trade) {
    const entry = entries.get("trade/index");
    entry.target = { kind: "trade" };
    entry.sources = [trade.source_id, "pib_dfc_completion", "osm_transport", "cwprs_port_locations"];
  }
  const areaFiles = [data.protectedLand, data.protectedRamsar];
  for (const [i, file] of areaFiles.entries()) {
    for (const row of file?.sites || []) {
      if (row.ramsar_id) continue;
      const entry = add("protected", row.id, row.name, {
        row, cell: row.cell, cells: row.cells, group: row.designation,
        sources: i === 1 ? ["rsis_protected"] : [
          row.designation === "National park" ? "wii_protected" : "ntca_protected",
          row.source?.startsWith("wikidata:") ? "wikidata_protected" : "osm_protected",
        ],
        target: Number.isFinite(row.x) && Number.isFinite(row.y)
          ? { kind: "protected", point: [row.x, row.y] } : null,
      });
      const owner = tileStates[owners[row.cell]];
      if (owner) { entry.location = owner.title; associate(entry, [owner.id]); }
      const wonder = entries.get(`wonder/${row.wonder || `park-${row.id}`}`);
      if (wonder) { entry.related.push(wonder.key); wonder.related.push(entry.key); }
    }
  }

  // The small featured cohorts allow distance joins without scanning the full map for each article.
  const places = [...entries.values()].filter(({ kind, row }) =>
    (kind === "city" || kind === "wonder") && Number.isFinite(row?.x) && Number.isFinite(row?.y));
  for (const entry of places) {
    const nearby = places.filter((other) => other !== entry).map((other) =>
      [other, Math.hypot(entry.row.x - other.row.x, entry.row.y - other.row.y)])
      .filter(([, distance]) => distance <= 100).sort((a, b) => a[1] - b[1]).slice(0, 6);
    entry.nearby = nearby.map(([other]) => other.key);
  }

  for (const row of data.sources || []) add("source", row.id, row.title, {
    row, location: row.publisher, aliases: row.used_for?.join?.(" "),
    shortTitle: shortSourceTitle(row),
  });
  add("source", "usaciv", "usaciv · MIT licence");
  for (const entry of entries.values()) {
    entry.sources = [...new Set(entry.sources)].filter((id) => entries.has(`source/${id}`));
    for (const id of entry.sources) entries.get(`source/${id}`).related.push(entry.key);
  }
  return entries;
}

export function searchPedia(index, query) {
  const q = normalize(query);
  if (!q) return [];
  const tokens = q.split(" ");
  return [...index.values()].map((entry) => {
    const names = [entry.title, ...entry.aliases].map(normalize);
    const geography = [...(entry.geographies || [])].flatMap((state) => [state.title, state.id, ...state.aliases]);
    const full = normalize([...names, entry.category, entry.group, entry.location, ...geography].filter(Boolean).join(" "));
    const rank = names.includes(q) ? 0 : names.some((name) => name.startsWith(q)) ? 1
      : tokens.every((token) => full.includes(token)) ? 2 : Infinity;
    return { entry, rank };
  }).filter(({ rank }) => Number.isFinite(rank))
    .sort((a, b) => a.rank - b.rank || a.entry.category.localeCompare(b.entry.category) || a.entry.title.localeCompare(b.entry.title))
    .map(({ entry }) => entry);
}
