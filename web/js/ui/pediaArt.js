import { hexPath } from "../render/map.js";
import { drawTerrainGlyphs } from "../render/art/terrain.js";
import { drawWaterGlyphs } from "../render/art/water.js";
import { drawCityTile } from "../render/art/city.js";
import { drawWonder } from "../render/art/sites.js";
import { drawIcon, hasIcon } from "../icons.js";
import { formatLensTick } from "./lenses.js";
import { esc } from "../format.js";

function paintTiles(ctx, width, height, w, cells, entry) {
  const { grid } = w;
  const xs = cells.map((i) => grid.cx(i));
  const ys = cells.map((i) => grid.cy(i));
  const left = Math.min(...xs), right = Math.max(...xs);
  const top = Math.min(...ys), bottom = Math.max(...ys);
  const vertical = entry.kind === "city" ? 2.6 : 2;
  const scale = Math.min((width - 24) / (right - left + 2 * grid.R), (height - 24) / (bottom - top + vertical * grid.R));
  ctx.save();
  ctx.translate(width / 2, height / 2);
  ctx.scale(scale, scale);
  ctx.translate(-(left + right) / 2, -(top + bottom) / 2);
  for (const i of cells) {
    hexPath(ctx, grid, i, 1);
    const [r, g, b] = w.terrainColors[i];
    ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
    ctx.fill();
    ctx.strokeStyle = "rgba(235,217,165,.22)";
    ctx.lineWidth = .7 / scale;
    ctx.stroke();
  }
  const art = { Rpx: grid.R * scale, s: scale };
  ctx.save();
  if (cells.length === 1 && entry.kind !== "city") { hexPath(ctx, grid, cells[0], 1); ctx.clip(); }
  drawWaterGlyphs(ctx, cells, w, art);
  drawTerrainGlyphs(ctx, cells, w, art);
  const city = entry.kind === "city" ? entry.row : null;
  if (city?.cell != null) {
    const owner = w.raw.owner[city.cell];
    drawCityTile(ctx, city, grid.cx(city.cell), grid.cy(city.cell), grid.R, { ...art, stateColor: w.stateColor[owner] });
  }
  if (entry.kind === "rail" && entry.cells?.length) {
    ctx.beginPath();
    entry.cells.forEach((cell, i) => ctx[i ? "lineTo" : "moveTo"](grid.cx(cell), grid.cy(cell)));
    ctx.lineWidth = 2 / scale;
    ctx.strokeStyle = "#f4d081";
    ctx.stroke();
  }
  if (entry.kind === "river") {
    ctx.beginPath();
    for (const { pts } of entry.edges) {
      ctx.moveTo(pts[0], pts[1]);
      for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
    }
    ctx.lineWidth = 3 / scale;
    ctx.strokeStyle = "#71c4e5";
    ctx.stroke();
  }
  if (entry.kind === "protected" && entry.cells?.length) {
    ctx.fillStyle = "rgba(114,202,132,.4)";
    for (const cell of cells) { hexPath(ctx, grid, cell); ctx.fill(); }
  }
  ctx.restore();
  ctx.restore();
}

export function paintPedia(canvas, entry, data) {
  const width = canvas.clientWidth, height = canvas.clientHeight;
  if (!width || !height) return;
  const dpr = devicePixelRatio || 1;
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  const bg = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, Math.hypot(width, height) / 2);
  bg.addColorStop(0, "#354735");
  bg.addColorStop(1, "#151d22");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, width, height);
  const { row, kind } = entry;
  const size = Math.min(width, height);
  if (kind === "wonder" && row) {
    drawWonder(ctx, row.kind, width / 2, height / 2, size * .74, { motif: row.motif });
  } else if (kind === "resource" && row) {
    const icon = row.icon || `r-${row.id}`;
    const color = row.color || "#3e5465";
    if (!hasIcon(icon) || !drawIcon(ctx, icon, width / 2, height / 2, size * .62, { bg: color })) {
      ctx.beginPath();
      ctx.arc(width / 2, height / 2, size * .31, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    }
  } else if (kind === "lens" && row?.ramp?.length) {
    const left = width * .09, right = width - left;
    const grad = ctx.createLinearGradient(left, 0, right, 0);
    row.ramp.forEach((color, i) => grad.addColorStop(i / Math.max(1, row.ramp.length - 1), color));
    ctx.fillStyle = grad;
    ctx.fillRect(left, height * .38, right - left, height * .2);
    ctx.fillStyle = "#f4e7c2";
    ctx.font = "14px system-ui";
    ctx.fillText(formatLensTick(row, 0), left, height * .73);
    ctx.textAlign = "right";
    ctx.fillText(formatLensTick(row, 1), right, height * .73);
  } else {
    const exemplar = entry.cell ?? data.homeCell;
    const cells = kind === "city" && row?.cell != null ? (row.footprint?.length ? row.footprint : [row.cell])
      : entry.cells?.length ? entry.cells : exemplar != null ? [exemplar] : [];
    if (cells.length) paintTiles(ctx, width, height, data.w, cells, entry);
  }
}

export function specimen(entry, caption) {
  return `<figure class="pedia-specimen"><canvas data-specimen="${esc(entry.key)}" aria-label="${esc(caption)}" role="img"></canvas><figcaption>${esc(caption)}</figcaption></figure>`;
}
