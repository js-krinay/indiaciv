// Small isometric blocks painted directly over the existing relief, cover and waterways.
// The silhouettes are schematic. Site diamonds use the verified feature coordinates.
function poly(ctx, color, points) {
  ctx.fillStyle = color;
  ctx.beginPath();
  points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
  ctx.closePath();
  ctx.fill();
}

function block(ctx, x, y, width, height, palette) {
  const w = width / 2, d = width * 0.23;
  poly(ctx, "rgba(32,31,22,.29)", [[x-w,y],[x,y+d],[x+w*1.7,y+d/2],[x+w,y-d]]);
  poly(ctx, palette[0], [[x-w,y-height],[x,y-height+d],[x,y+d],[x-w,y]]);
  poly(ctx, palette[1], [[x,y-height+d],[x+w,y-height],[x+w,y],[x,y+d]]);
  poly(ctx, palette[2], [[x-w,y-height],[x,y-height-d],[x+w,y-height],[x,y-height+d]]);
  ctx.strokeStyle = "rgba(75,51,34,.6)";
  ctx.lineWidth = 0.6;
  for (let level = 3; level < height - 1; level += 3) {
    ctx.beginPath();
    ctx.moveTo(x - w * 0.72, y - level + d * 0.28);
    ctx.lineTo(x - w * 0.21, y - level + d * 0.79);
    ctx.stroke();
  }
}

const SANDSTONE = ["#ca9061", "#8e5843", "#ebbb88"];
const LIMEWASH = ["#ded6a4", "#a09b78", "#f7e4ba"];
const TERRACOTTA = ["#c2865f", "#8b6852", "#ad6249"];
const INDUSTRIAL = ["#b9a58e", "#77685e", "#d4bd9e"];
const COAST = new Set(["MH", "GA", "KL", "WB", "OD"]);

function quarter(ctx, x, y, size, variant, trees, coast) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(size, size);
  poly(ctx, "#a69272", [[-26, 0], [3, -14], [29, -2], [2, 14]]);
  poly(ctx, "#c7b18a", [[-24, -1], [3, -13], [27, -3], [2, 12]]);
  if (variant === 0) {
    block(ctx, -12, -2, 13, 9, LIMEWASH);
    block(ctx, 5, 2, 23, 10, SANDSTONE);
    block(ctx, 5, -7, 17, 5, SANDSTONE);
    block(ctx, 5, -12, 11, 4, LIMEWASH);
    poly(ctx, "#e2b67e", [[0,-16],[5,-23],[10,-16],[5,-14]]);
    block(ctx, 18, 1, 8, 8, TERRACOTTA);
  } else if (variant === 1) {
    block(ctx, -9, -2, 17, 8, INDUSTRIAL);
    block(ctx, 7, 2, 22, 8, INDUSTRIAL);
    for (let i = 0; i < 3; i++) {
      const roof = -2 + i * 6;
      poly(ctx, "#8f6051", [[roof-6,-6],[roof-2,-13],[roof+5,-10],[roof+3,-5]]);
    }
    block(ctx, -13, -4, 4, 19, SANDSTONE);
  } else {
    block(ctx, -11, -1, 13, coast ? 6 : 11, coast ? TERRACOTTA : LIMEWASH);
    block(ctx, 7, 0, 15, 11, SANDSTONE);
    block(ctx, -1, 6, 10, 8, coast ? TERRACOTTA : LIMEWASH);
    block(ctx, 17, 5, 11, 6, TERRACOTTA);
  }
  for (let i = 0; i < trees; i++) {
    const tx = -22 + i * 7, ty = 3 + (i % 3) * 2;
    ctx.fillStyle = "#58463b";
    ctx.fillRect(tx, ty - 4, 1, 5);
    ctx.fillStyle = i % 2 ? "#707849" : "#4d6643";
    ctx.beginPath();
    ctx.ellipse(tx, ty - 5, 2.8, 3.8, -0.3, 0, 2 * Math.PI);
    ctx.fill();
  }
  ctx.restore();
}

export function paintScene(ctx, cam, m, world, grid) {
  const radius = grid.R * cam.scale;
  if (radius < 16) return;
  const coast = COAST.has(m.city.states[0]);
  const tiles = m.sceneTiles;
  for (const [index, tile] of tiles.entries()) {
    const [x, y] = cam.toScreen(...tile.anchor);
    const size = Math.min(1.75, radius / 65) * (tile.cell === m.city.cell ? 1 : 0.82);
    const trees = 2 + Math.round((world.pct.forest[tile.cell] || 0) / 25);
    quarter(ctx, x + (tile.water ? 0 : radius * 0.12), y + (tile.water ? 0 : radius * 0.16),
      size, index === 0 ? 0 : index % 3, trees, coast);
  }
  for (const place of [...m.wonders, ...m.sites.map((site) => site.item)]) {
    const [x, y] = cam.toScreen(place.site_x ?? place.x, place.site_y ?? place.y);
    poly(ctx, "#342719", [[x,y-6],[x+5,y],[x,y+6],[x-5,y]]);
    poly(ctx, "#f2d18d", [[x,y-4],[x+3,y],[x,y+4],[x-3,y]]);
  }
}
