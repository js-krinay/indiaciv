// Camera tour for the IndiaCiv launch trailer. Coordinates are map kilometres.
import { titleCard, endCard, caption, lensLegend, vignette, darken, win, smooth, lerp, clamp01 } from "./overlays.js";

export const CONFIG = {
  title: "IndiaCiv",
  subtitle: "Explore India, hex by hex",
  url: "indiaciv.jinay.uk",
};

export const FPS = 30;
export const W = 1920, H = 1080;
const FADE = 0.45;
const MAP = { banners: false, resources: false, labels: false };

function camera(a, b, k) {
  return {
    x: lerp(a.x, b.x, k),
    y: lerp(a.y, b.y, k),
    rpx: a.rpx * (b.rpx / a.rpx) ** k,
  };
}

function nationalView(stage) {
  const { grid, raw } = stage.w;
  const land = raw.owner.flatMap((owner, i) => owner >= 0 && !raw.water[i] ? [i] : []);
  const xs = land.map((i) => grid.cx(i));
  const ys = land.map((i) => grid.cy(i));
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const y0 = Math.min(...ys), y1 = Math.max(...ys);
  const scale = Math.min(W * 0.86 / (x1 - x0 + 2 * grid.R), H * 0.88 / (y1 - y0 + 2 * grid.R)) / stage.dpr;
  return { x: (x0 + x1) / 2, y: (y0 + y1) / 2, rpx: scale * grid.R };
}

function almanacPanel(ctx, rows, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.fillStyle = "#10212d";
  ctx.strokeStyle = "#c9a45c";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.roundRect(965, 115, 850, 620, 18);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#ecd08e";
  ctx.font = "54px Georgia, serif";
  ctx.fillText("From the Almanac", 1025, 208);
  ctx.font = "28px system-ui, sans-serif";
  ctx.fillText("SOURCES", 1025, 272);
  rows.forEach(({ label, publisher }, i) => {
    const y = 345 + i * 102;
    ctx.fillStyle = "#efe4c6";
    ctx.font = "600 36px system-ui, sans-serif";
    ctx.fillText(label, 1025, y, 730);
    ctx.fillStyle = "#c9bfa6";
    ctx.font = "29px system-ui, sans-serif";
    ctx.fillText(publisher, 1025, y + 38, 730);
  });
  ctx.restore();
}

export function buildStoryboard(stage, cfg = CONFIG) {
  const { data } = stage;
  const home = nationalView(stage);
  const { min_x, max_y, margin } = stage.w.raw.projection;
  // Regional anchors use rounded offsets from pipeline.core.geo.Laea (WGS84, centred on 22°N, 82°E).
  // The published projection supplies the shift into the current grid.
  const region = (east, north, rpx) => ({ x: east - min_x + margin, y: max_y - north + margin, rpx });
  const point = (place, rpx, dx = 0, dy = 0) => ({ x: place.x + dx, y: place.y + dy, rpx });
  const taj = data.wonders.wonders.find((site) => site.id === "whc-252");
  const mumbai = data.cities.find((city) => city.name === "Mumbai");
  const lens = stage.lensById.get("density");
  const legend = {
    ...lens, name: "Population density", unit: lens.source_line,
    lo: stage.formatLensTick(lens, 0, 0), hi: stage.formatLensTick(lens, 1, 4),
  };
  const sources = [
    ["Land cover", "india_terrain"],
    ["Rivers and railways", "osm_transport"],
    ["Urban population projections", "un_wup_cities"],
    ["City View population grid", "city_population_grid"],
  ].map(([label, id]) => ({ label, publisher: data.sources.find((source) => source.id === id).publisher }));

  const shots = [];
  function shot(id, duration, a, b, { trans, view, text, overlay } = {}) {
    const t0 = shots.at(-1)?.t1 ?? 0;
    shots.push({
      id, t0, t1: t0 + duration, trans,
      render: (t) => [{ view: { ...camera(a, b, smooth(t / duration)), ...MAP, ...view } }],
      overlay(ctx, t) {
        if (text) caption(ctx, W, H, text, win(t, 0.45, duration + 0.2, 0.55, 0.45), clamp01((t - 0.45) / 0.65));
        overlay?.(ctx, t);
      },
    });
  }

  shot("title", 5, { ...home, rpx: home.rpx * 0.96 }, home, {
    overlay(ctx, t) {
      darken(ctx, W, H, 0.28);
      vignette(ctx, W, H, 0.6);
      titleCard(ctx, W, H, cfg, smooth(t / 0.85), smooth(t / 1.5));
    },
  });
  shot("ladakh", 6, region(-403, 1317, 23), region(-320, 1210, 35), {
    trans: "dip",
    text: { kicker: "The north", title: "Ladakh and the Himalaya", sub: "Snowfields above the high valleys" },
  });
  shot("ganga", 7, region(-198, 528, 31), region(-39, 462, 37), {
    trans: "dip", view: { layers: { rail: true } },
    text: { kicker: "Rivers and railways", title: "Across the Ganga plain", sub: "River bends and rail lines cross the floodplain" },
  });
  const tajPoint = { x: taj.draw_x, y: taj.draw_y };
  shot("agra", 6, point(tajPoint, 46, -62, 36), point(tajPoint, 94, -32, 28), {
    trans: "dip", view: { layers: { wonders: true } },
    text: { kicker: "Agra", title: taj.name, sub: "A landmark on the banks of the Yamuna" },
  });
  const { bbox } = stage.cityView(mumbai.id).model;
  const centre = { x: (bbox.x0 + bbox.x1) / 2, y: (bbox.y0 + bbox.y1) / 2 };
  shot("city", 7, point(centre, 85, -16, 22), point(centre, 112, -9, 15), {
    trans: "dip", view: { city: mumbai.id },
    overlay(ctx) {
      // The City View's population pills are visible throughout this shot, so keep the period on screen.
      caption(ctx, W, H, {
        kicker: "City View", title: "Mumbai", sub: "Explore the urban footprint and its neighbourhoods",
        source: "Tile residents · IndiaCiv estimate for 1 July 2026",
      }, 1);
    },
  });
  shot("ghats", 7, region(-588, -1145, 41), region(-610, -1285, 51), {
    trans: "dip",
    text: { kicker: "The southwest", title: "Western Ghats to Kerala", sub: "Rainforest ridges descend towards the Arabian Sea" },
  });
  shot("lakshadweep", 5, region(-1025, -1228, 52), region(-1011, -1242, 67), {
    trans: "dip",
    text: { kicker: "Arabian Sea", title: "Lakshadweep", sub: "Coral islands off the Malabar coast" },
  });
  shot("andamans", 6, region(1164, -1093, 27), region(1214, -1505, 24), {
    trans: "dip",
    text: { kicker: "Bay of Bengal", title: "Andaman and Nicobar Islands", sub: "Forested islands arc south through the sea" },
  });
  shot("lens", 6, { ...home, y: home.y - 30, rpx: home.rpx * 1.05 }, { ...home, rpx: home.rpx * 0.98 }, {
    trans: "dip", view: { lens: lens.id },
    text: { kicker: "Map lenses", title: "Where India lives", sub: "Explore how population density varies by district" },
    overlay(ctx) { lensLegend(ctx, W, H, legend, 1); },
  });
  shot("almanac", 5, { ...home, x: home.x + 720 }, { ...home, x: home.x + 820 }, {
    text: { kicker: "Almanac", title: "Trace the map to its sources" },
    overlay(ctx, t) { almanacPanel(ctx, sources, smooth(t / 0.7)); },
  });
  shot("end", 5, home, { ...home, rpx: home.rpx * 0.96 }, {
    trans: "dip",
    overlay(ctx, t) {
      darken(ctx, W, H, 0.48);
      vignette(ctx, W, H, 0.8);
      endCard(ctx, W, H, cfg, { facts: "", fallback: "" }, smooth(t / 0.6), smooth(t / 0.9));
    },
  });

  const duration = shots.at(-1).t1;
  return { shots, duration, fps: FPS, frames: duration * FPS, fade: FADE };
}

/** Shots visible at absolute time T, each with its transition progress `alpha` (0..1 over the incoming shot's fade).
 * A shot stays on screen until the next one is fully in (whatever its own t1 says), and everything under a fully
 * opaque shot is dropped. Transitions (`trans` on the incoming shot): undefined = crossfade (FADE s); "dip" = through
 * dark (DIP s); "punch" = zoom-through cut (PUNCH s; main.js draws it); "cut" = none (the camera carries on). */
const DIP = 0.6, PUNCH = 0.4;
export const fadeOf = (sb, s) => s.fade ?? ({ dip: DIP, punch: PUNCH, cut: 0 }[s.trans] ?? sb.fade);
export function activeShots(sb, T) {
  const out = [];
  sb.shots.forEach((s, i) => {
    const next = sb.shots[i + 1];
    const end = next ? Math.max(s.t1, next.t0 + fadeOf(sb, next)) : s.t1;
    if (T < s.t0 || T >= end) return;
    const f = fadeOf(sb, s);
    const alpha = i === 0 || f <= 0 ? 1 : clamp01((T - s.t0) / f);
    out.push({ shot: s, alpha: s.trans ? alpha : smooth(alpha), sec: T - s.t0 });
  });
  let k = out.length - 1;
  while (k > 0 && out[k].alpha < 1) k--;
  return out.slice(k);
}
