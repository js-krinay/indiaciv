// India City View display model. Geography and population come from the prepared profile.

// Land-use groups shown as a hex's "tile yield" (world.json pct keys → group). Cover ids give the map colour.
export const LAND = [
  { key: "built", label: "Built-up", icon: "l-developed", cover: 9, keys: ["developed"] },
  { key: "farm", label: "Farmland", icon: "l-farmland", cover: 7, keys: ["crop", "pasture"] },
  { key: "forest", label: "Forest", icon: "l-forest", cover: 3, keys: ["forest"] },
  { key: "open", label: "Open land", icon: null, cover: 4, keys: ["grass", "shrub", "wetland"] },
];

function landOf(w, cell) {
  let best = null, share = 0;
  for (const group of LAND) {
    const value = group.keys.reduce((total, key) => total + (w.pct?.[key]?.[cell] || 0), 0);
    if (value > share) {
      best = group;
      share = value;
    }
  }
  return best;
}

export function buildModel(app, city, profile) {
  const { w, data } = app;
  const grid = w.grid;
  const stateIdx = w.raw.states.findIndex((s) => s.abbr === city.states[0]);
  const stateRGB = w.stateColor[stateIdx] || [201, 164, 92];
  const footprint = profile.cells.map((row) => row.cell);
  const mask = new Set(footprint);

  const resourceKeys = new Set(profile.resources.map((key) => JSON.stringify(key)));
  const typeById = new Map((data.resources?.types || []).map((type) => [type.id, type]));
  const sites = [];
  (data.resources?.items || []).forEach((item, index) => {
    if (resourceKeys.has(JSON.stringify([item.type, item.name, item.x, item.y]))) {
      sites.push({ item, index, type: typeById.get(item.type) });
    }
  });
  sites.sort((a, b) => (b.item.value ?? 0) - (a.item.value ?? 0));
  const siteCells = new Map();
  for (const site of sites) {
    const cell = site.item.cell;
    if (!siteCells.has(cell)) siteCells.set(cell, []);
    siteCells.get(cell).push(site);
  }

  const tiles = profile.cells.map((row) => {
    const cell = row.cell;
    const water = !!w.raw.water[cell];
    const anchor = row.scene_anchor || [city.x, city.y];
    const labelAnchor = water ? anchor : [grid.cx(cell), grid.cy(cell)];
    return { cell, anchor, labelAnchor, water, residents: row.population, land: landOf(w, cell) };
  });
  const populated = tiles.filter((tile) => tile.residents > 0).sort((a, b) => b.residents - a.residents);
  const sceneTiles = populated.filter((tile, index) => tile.water || index < 9);
  const x = footprint.map((cell) => grid.cx(cell));
  const y = footprint.map((cell) => grid.cy(cell));
  const bbox = { x0: Math.min(...x) - grid.R, y0: Math.min(...y) - grid.R,
    x1: Math.max(...x) + grid.R, y1: Math.max(...y) + grid.R };

  const states = (profile.states || city.states).map((abbr) => {
    const index = w.raw.states.findIndex((s) => s.abbr === abbr);
    return { name: w.raw.states[index]?.name || abbr };
  });
  const wonderIds = new Set(profile.wonders);
  const wonders = (data.wonders?.wonders || []).filter((wonder) => wonderIds.has(wonder.id));
  return { city, profile, footprint, mask, tiles, sceneTiles, bbox, stateRGB, states, sites, siteCells,
    wonders, counties: w.raw.counties, districts: data.lenses?.places?.counties ?? {},
    stateNames: new Map(w.raw.states.map(({ abbr, name }) => [abbr, name])),
    sources: new Map((data.sources ?? []).map(({ id, publisher }) => [id, publisher])),
    yieldDefinitions: data.nation.yields ?? [] };
}
