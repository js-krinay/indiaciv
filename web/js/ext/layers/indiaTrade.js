import { esc, int } from "../../format.js";

export const CORRIDOR_INK = "#ffba64";
export const COASTAL_INK = "#83e4ef";

export function indiaTradeLayer(app) {
  const { trade, ports, rail_corridors: corridors } = app.data.infrastructure;
  const { grid } = app.w;
  const points = (cells) => cells.map((cell) => [grid.cx(cell), grid.cy(cell)]);
  const rail = trade.corridors.filter((name) => corridors[name]?.length).map((name) => ({
    points: points(corridors[name]), color: CORRIDOR_INK, width: 2.7,
    html: `<b>${esc(name)}</b><br>Operational Dedicated Freight Corridor<br>
      <span class="muted">8 Sep 2026 · PMO via Press Information Bureau</span>`,
  }));
  const byId = new Map(ports.map((port) => [port.id, port]));
  const max = Math.max(...trade.branches.map((branch) => branch.tonnes));
  const branches = trade.branches.map(({ port_id, cells, tonnes }) => ({
    points: points(cells), color: COASTAL_INK, width: 1.4 + 5.6 * Math.sqrt(tonnes / max),
    html: `<b>${esc(byId.get(port_id).name)}</b><br>${int(tonnes)} metric tonnes of coastal cargo handled<br>
      ${esc(trade.label)} · ${esc(trade.status)}<br>
      <span class="muted">Ministry of Ports, Shipping and Waterways</span>`,
  }));
  const backbone = { points: points(trade.backbone), width: 1.35, color: COASTAL_INK };
  const stroke = (ctx, route, scale, inset = 0) => {
    ctx.beginPath();
    route.points.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.lineWidth = (route.width + inset) / scale;
    ctx.stroke();
  };
  const lines = [...rail, ...branches];
  let on = false;
  app.ui.addMapToggle({
    id: "trade", label: "Trade", icon: "d-harbor",
    title: "Dedicated freight corridors and coastal cargo", default: false,
    get: () => on, set: (value) => { on = value; app.requestDraw(); },
  });
  return {
    id: "india-trade", z: 69, minRpx: 0,
    visible: () => on,
    draw(ctx, vp) {
      ctx.save();
      ctx.lineJoin = ctx.lineCap = "round";
      ctx.strokeStyle = backbone.color;
      ctx.globalAlpha = 0.8;
      ctx.setLineDash([3 / vp.s, 4 / vp.s]);
      stroke(ctx, backbone, vp.s);
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;
      for (const line of lines) {
        ctx.strokeStyle = "#142d37";
        stroke(ctx, line, vp.s, 2);
        ctx.strokeStyle = line.color;
        stroke(ctx, line, vp.s);
      }
      for (const branch of branches) {
        ctx.beginPath();
        ctx.arc(...branch.points[0], Math.max(2.5, branch.width / 2) / vp.s, 0, 2 * Math.PI);
        ctx.fillStyle = branch.color;
        ctx.fill();
        ctx.lineWidth = 0.8 / vp.s;
        ctx.strokeStyle = "#142d37";
        ctx.stroke();
      }
      ctx.restore();
    },
    hit(x, y, rpx) {
      const scale = rpx / grid.R;
      let nearest = null;
      let best = Infinity;
      for (const line of lines) {
        for (let i = 1; i < line.points.length; i++) {
          const [ax, ay] = line.points[i - 1], [bx, by] = line.points[i];
          const dx = bx - ax, dy = by - ay;
          const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)));
          const d = Math.hypot(x - ax - t * dx, y - ay - t * dy) * scale;
          if (d < best && d <= Math.max(6, line.width / 2)) {
            nearest = line;
            best = d;
          }
        }
      }
      return nearest;
    },
    tooltip: (line) => line.html,
  };
}
