import { drawProtected, prepareCellSet } from "../../render/art/sites.js";
import { esc } from "../../format.js";

function wetlandGeometry(site) {
  if (!site.rings?.length) return null;
  const path = new Path2D();
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const ring of site.rings) {
    path.moveTo(...ring[0]);
    for (const [x, y] of ring) {
      path.lineTo(x, y);
      x0 = Math.min(x0, x);
      y0 = Math.min(y0, y);
      x1 = Math.max(x1, x);
      y1 = Math.max(y1, y);
    }
    path.closePath();
  }
  return { site, path, x0, y0, x1, y1 };
}

export function installProtectedLand(app, wondersOn) {
  const { protectedLand, protectedRamsar, wonders } = app.data;
  const osm = protectedLand?.sites || [];
  const overlays = new Map(osm.filter((s) => s.ramsar_id).map((s) => [s.ramsar_id, s]));
  const sites = [...osm.filter((s) => !s.ramsar_id), ...(protectedRamsar?.sites || [])
    .map((s) => {
      const shape = overlays.get(s.id);
      return shape ? { ...s, cells: shape.cells, rings: shape.rings, source: shape.source } : s;
    })];
  if (!sites.length) return sites;

  const wonderIds = new Set((wonders?.wonders || []).map((s) => s.id));
  const grid = app.w.grid;
  const cellSites = new Map(), markers = [];
  for (const site of sites) {
    if (!site.cells?.length && site.cell != null) markers.push(site);
    for (const cell of site.cells || []) {
      if (!cellSites.has(cell)) cellSites.set(cell, []);
      cellSites.get(cell).push(site);
    }
  }
  const footprint = cellSites.size ? [prepareCellSet(app.w, cellSites.keys())] : [];
  const protectedWetlands = sites.map(wetlandGeometry).filter(Boolean);
  const wetlandBySite = new Map(protectedWetlands.map((geom) => [geom.site, geom]));
  const hitContext = protectedWetlands.length ? document.createElement("canvas").getContext("2d") : null;
  const showExtent = (geom, r) => geom && r >= 12
    && Math.min(geom.x1 - geom.x0, geom.y1 - geom.y0) * r / grid.R >= 4;
  const showMarker = (s, r) => (!wondersOn() || !wonderIds.has(s.wonder || `park-${s.id}`) || (s.marker_radius != null && s.cells === null))
    && (s.designation === "Ramsar wetland" || r >= 3)
    && !showExtent(wetlandBySite.get(s), r);
  const markerRadius = (s) => s.marker_radius ?? (s.area_ha == null ? 2.2 : Math.min(6, 2 + 0.068 * Math.sqrt(s.area_ha)));
  let on = true;
  app.registerStaticLayer({
    id: "protected", z: 57, minRpx: 1,
    visible: () => on && !app.state.lens,
    sig: () => String(wondersOn()),
    draw(ctx, vp, _world, options) {
      drawProtected(ctx, footprint, vp, options);
      ctx.fillStyle = "rgba(88,175,150,.24)";
      ctx.strokeStyle = "#7cc6ae";
      ctx.lineWidth = 1 / vp.s;
      for (const geom of protectedWetlands) {
        if (!showExtent(geom, options.Rpx)
          || geom.x1 < vp.x0 || geom.x0 > vp.x1 || geom.y1 < vp.y0 || geom.y0 > vp.y1) continue;
        ctx.fill(geom.path, "evenodd");
        ctx.stroke(geom.path);
      }
      for (const s of markers) {
        if (!showMarker(s, options.Rpx)) continue;
        const radius = markerRadius(s) / vp.s;
        if (s.x + radius < vp.x0 || s.x - radius > vp.x1 || s.y + radius < vp.y0 || s.y - radius > vp.y1) continue;
        ctx.beginPath();
        ctx.arc(s.x, s.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = s.designation === "Ramsar wetland" ? "#7cc6ae" : "#a6c485";
        ctx.fill();
        ctx.strokeStyle = "#28483c";
        ctx.lineWidth = 1 / vp.s;
        ctx.stroke();
      }
    },
    hit(x, y, r) {
      const scale = r / grid.R;
      const near = markers.filter((s) => showMarker(s, r)
        && Math.hypot(s.x - x, s.y - y) * scale <= markerRadius(s) + 2);
      for (const geom of protectedWetlands) {
        if (showExtent(geom, r) && x >= geom.x0 && x <= geom.x1 && y >= geom.y0 && y <= geom.y1
          && hitContext.isPointInPath(geom.path, x, y, "evenodd")) near.push(geom.site);
      }
      const covered = cellSites.get(grid.cellAt(x, y));
      return near.length ? [...new Set([...near, ...(covered || [])])] : covered;
    },
    tooltip: (records) => records.map((s) => [
      `<b>${esc(s.name)}</b>`, esc(s.status || s.designation),
      s.area_ha == null ? "" : `Official area · ${(s.area_ha / 100).toLocaleString("en-IN", { maximumFractionDigits: 4 })} km²`,
      esc([s.authority, s.period].filter(Boolean).join(" · ")),
      s.source?.startsWith("wikidata:") ? "Location · Wikidata" :
        /^(node|way|relation)\//.test(s.source || "") ? "Mapped geography · © OpenStreetMap contributors" : "",
    ].filter(Boolean).join("<br>")).join("<br><br>"),
  });
  app.ui.addMapToggle({
    id: "protected", label: "Protected land", swatch: "protected-swatch", default: true,
    title: "Green tint for mapped extents and dots for sites below the hex threshold",
    get: () => on, set: (value) => { on = value; },
  });
  return sites;
}
