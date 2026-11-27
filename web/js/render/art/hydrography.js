import { atLeast, lodFor } from "./lod.js";

const cache = new WeakMap();
export const legacyRivers = new URLSearchParams(location.search).get("rivers") === "legacy";
const TRUNKS = new Set(["Ganga", "Brahmaputra", "Indus", "Godavari", "Krishna", "Narmada", "Mahanadi",
  "Lower Meghna"]);
const REGIONAL = new Set(["Yamuna", "Tapti", "Kaveri", "Siang"]);
const BARAK_BASIN = new Set(["Barak", "Kushiyara", "Upper Meghna"]);
const DELTA = new Set(["Hooghly", "Ganga delta", "Godavari western distributary",
  "Krishna eastern distributary"]);

function riverStyle(edge, owner, indianNames) {
  const foreign = edge.cells.some((cell) => owner[cell] === -2) &&
    edge.cells.every((cell) => owner[cell] < 0);
  const trunk = edge.names.some((name) => TRUNKS.has(name));
  const delta = edge.names.some((name) => DELTA.has(name));
  if (foreign && !edge.names.some((name) => indianNames.has(name) &&
      (TRUNKS.has(name) || DELTA.has(name) || (edge.rank >= 7 && name === "Siang"))) &&
      !edge.names.some((name) => name === "Lower Meghna" || BARAK_BASIN.has(name))) return null;
  const minLod = trunk || (edge.names.length && edge.rank >= 8) ? "far"
    : delta || edge.names.some((name) => REGIONAL.has(name) || BARAK_BASIN.has(name)) ? "mid" : "close";
  return { foreign, trunk, minLod, rank: edge.rank };
}

function prepare(world) {
  if (cache.has(world)) return cache.get(world);
  const bands = new Map(), byCell = new Map();
  const register = (cell, item) => {
    if (!byCell.has(cell)) byCell.set(cell, []);
    byCell.get(cell).push(item);
  };
  const rivers = world.river_edges || [];
  const indianNames = new Set(rivers.filter((edge) => edge.cells.some((cell) => world.owner[cell] >= 0))
    .flatMap((edge) => edge.names));
  for (const edge of rivers) {
    const style = riverStyle(edge, world.owner, indianNames);
    if (!style) continue;
    const key = JSON.stringify(style);
    if (!bands.has(key)) bands.set(key, { ...style, path: new Path2D() });
    const { path } = bands.get(key);
    path.moveTo(edge.pts[0], edge.pts[1]);
    path.lineTo(edge.pts[2], edge.pts[3]);
    if (edge.names.length) for (const cell of edge.cells) register(cell, { ...edge, minLod: style.minLod });
  }
  const footprints = new Path2D(), markers = [], namedPolygons = [];
  for (const lake of world.lakes || []) {
    for (const polygon of lake.polygons) {
      if (lake.name) {
        let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
        for (const [x, y] of polygon[0]) {
          x0 = Math.min(x0, x); y0 = Math.min(y0, y);
          x1 = Math.max(x1, x); y1 = Math.max(y1, y);
        }
        namedPolygons.push({ name: lake.name, polygon, x0, y0, x1, y1 });
      }
      for (const ring of polygon) {
        footprints.moveTo(...ring[0]);
        for (const point of ring.slice(1)) footprints.lineTo(...point);
        footprints.closePath();
      }
    }
    if (!lake.tiles.length && lake.name) markers.push(lake);
    if (lake.name) for (const cell of new Set([lake.cell, ...lake.tiles])) register(cell, lake);
  }
  const prepared = { bands, byCell, footprints, markers, namedPolygons };
  cache.set(world, prepared);
  return prepared;
}

export function drawHydrography(ctx, world, { s, Rpx, lod, lens, showRivers }) {
  const { bands, footprints, markers } = prepare(world);
  ctx.save();
  ctx.fillStyle = lens ? "#5182a5aa" : "#3d80a6";
  ctx.fill(footprints, "evenodd");
  ctx.strokeStyle = "#a7d1ce88";
  ctx.lineWidth = 0.8 / s;
  ctx.stroke(footprints);
  ctx.lineCap = ctx.lineJoin = "round";
  const visible = showRivers ? [...bands.values()].filter((band) => atLeast(lod, band.minLod)) : [];
  visible.sort((a, b) => Number(a.trunk) - Number(b.trunk) || a.rank - b.rank);
  for (const { rank, path, trunk, foreign } of visible) {
    const width = Math.min(Rpx * (trunk ? 0.55 : 0.23),
      (trunk ? 2.8 + (rank - 6) * 0.32 : 0.75 + (rank - 3) * 0.21) * Math.sqrt(s / 0.25));
    ctx.globalAlpha = foreign ? 0.5 : 1;
    if (!lens && trunk) {
      ctx.strokeStyle = "#20434a";
      ctx.lineWidth = (width + 1.3) / s;
      ctx.stroke(path);
    }
    ctx.strokeStyle = lens ? "#68a1caaa" : trunk ? "#236c9e" : rank >= 7 ? "#518eab" : "#709da8";
    ctx.lineWidth = width / s;
    ctx.stroke(path);
    if (!lens && trunk) {
      ctx.strokeStyle = "#63aaba";
      ctx.lineWidth = width * 0.23 / s;
      ctx.stroke(path);
    }
  }
  ctx.globalAlpha = 1;
  if (!lens) {
    ctx.fillStyle = "#4e98ba";
    ctx.strokeStyle = "#b6d8cf";
    ctx.lineWidth = 0.85 / s;
    const radius = Math.min(4, Math.max(1.8, Rpx / 6)) / s;
    for (const { point: [x, y] } of markers) {
      ctx.beginPath();
      ctx.ellipse(x, y, radius, radius * 0.65, -0.35, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    }
  }
  ctx.restore();
}

export function waterNameAt(world, cell, [x, y], scale) {
  const { byCell, namedPolygons } = prepare(world);
  for (const { name, polygon, x0, y0, x1, y1 } of namedPolygons) {
    if (x < x0 || x > x1 || y < y0 || y > y1) continue;
    if (polygon.reduce((inside, ring) => inside !== insideRing(x, y, ring), false)) return name;
  }
  let best, distance = 5 / scale;
  const lod = lodFor(world.grid.radius * scale);
  for (const feature of byCell.get(cell) || []) {
    let d;
    if (feature.point) {
      d = feature.tiles.includes(cell) ? 0 : Math.hypot(x - feature.point[0], y - feature.point[1]);
    } else {
      if (legacyRivers || !atLeast(lod, feature.minLod)) continue;
      const [a, b, c, e] = feature.pts;
      const dx = c - a, dy = e - b;
      const t = Math.max(0, Math.min(1, ((x - a) * dx + (y - b) * dy) / (dx * dx + dy * dy)));
      d = Math.hypot(x - a - t * dx, y - b - t * dy);
    }
    if (d < distance) {
      distance = d;
      best = feature.name || feature.names.join(" · ");
    }
  }
  return best;
}

function insideRing(x, y, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [a, b] = ring[i], [c, d] = ring[j];
    if ((b > y) !== (d > y) && x < a + (y - b) * (c - a) / (d - b)) inside = !inside;
  }
  return inside;
}
