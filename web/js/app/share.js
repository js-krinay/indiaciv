// Share popover: copy a link to the current view, or download a 1600×900 PNG of it with a caption strip.
import { drawIcon, hasIcon } from "../icons.js";
import { icon } from "../ui/icon.js";

// The address printed on shared images. Set it to the published site (e.g. "example.com/us-atlas"); when left
// empty, the page's own host and path are used, except on a local dev server, where SITE_FALLBACK is printed.
export const SITE_URL = "indiaciv.jinay.uk";
const SITE_FALLBACK = "IndiaCiv";

export function siteLabel() {
  if (SITE_URL) return SITE_URL;
  try {
    const { hostname, host, pathname } = location;
    const local = !hostname || /^(localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0)$/.test(hostname) || /\.(localhost|test|local)$/.test(hostname);
    if (local || !/^https?:$/.test(location.protocol)) return SITE_FALLBACK;
    const path = pathname.replace(/\/index\.html?$/, "/").replace(/\/$/, "");
    return (host.replace(/^www\./, "") + path).slice(0, 60);
  } catch {
    return SITE_FALLBACK;
  }
}

export const IMG_W = 1600;
export const IMG_H = 900;
export const CAPTION_H = 128;
const SERIF = '"Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif';
const SANS = '-apple-system, "Segoe UI", system-ui, sans-serif';
const BASE_CREDITS = [
  "Source: Survey of India, Government of India · India boundaries by DataMeet India community (CC BY 4.0)",
  "Generalised to hexes. Survey of India disclaims liability for use. Refer to the original chart for authoritative boundaries.",
  "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium.",
  "NOAA ETOPO1 and ETOPO 2022 · Natural Earth · HydroLAKES · © OpenStreetMap contributors (ODbL 1.0)",
  "Population: Technical Group on Population Projections, National Commission on Population, MoHFW · UN DESA Population Division, File 22 (CC BY 3.0 IGO)",
];

export function imageCredits(info) {
  const rows = [...BASE_CREDITS];
  if (info.layerCredits?.length) rows.push(...info.layerCredits);
  if (info.lensCredits?.length) rows.push(`Lens data · ${info.lensCredits.join(" · ")}`);
  if (info.resourceCredits?.length) rows.push(`Resource data · ${info.resourceCredits.join(" · ")}`);
  const site = siteLabel();
  rows.push(site === SITE_FALLBACK ? "IndiaCiv · Sources in the Almanac" : `${site}/#pedia=source/index`);
  return rows;
}

async function copyText(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch { /* fall through to the legacy path */ }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  } catch {
    return false;
  }
}

function spaced(ctx, px) {
  if ("letterSpacing" in ctx) ctx.letterSpacing = px + "px";
}

/**
 * Compose the share image.
 * info: {renderMap(canvas, w, h) → bool, lens (lens object or null), formatValue(lens, t) → string,
 *        selection: {kind, name, sub} | null}
 */
export function composeImage(info, { height = IMG_H } = {}) {
  const imgH = Math.max(CAPTION_H + 100, Math.round(height)); // a shorter frame serves 1.91:1 social cards
  const cv = document.createElement("canvas");
  cv.width = IMG_W;
  cv.height = imgH;
  const ctx = cv.getContext("2d");
  ctx.font = `14px ${SANS}`;
  const credits = imageCredits(info).flatMap((line) => wrapCredit(ctx, line));
  const captionH = CAPTION_H + credits.length * 17;
  const mapH = Math.max(75, imgH - captionH);

  // --- map ---
  ctx.fillStyle = "#0d2a47";
  ctx.fillRect(0, 0, IMG_W, mapH);
  const map = document.createElement("canvas");
  map.width = IMG_W;
  map.height = mapH;
  let ok = false;
  try {
    ok = info.renderMap(map, IMG_W, mapH);
  } catch (err) {
    console.warn("share: map render failed", err);
  }
  if (ok) ctx.drawImage(map, 0, 0);

  // --- caption strip ---
  const y0 = mapH;
  const g = ctx.createLinearGradient(0, y0, 0, imgH);
  g.addColorStop(0, "#24364a");
  g.addColorStop(1, "#111a25");
  ctx.fillStyle = g;
  ctx.fillRect(0, y0, IMG_W, imgH - y0);
  ctx.fillStyle = "#c9a45c";
  ctx.fillRect(0, y0, IMG_W, 3);
  ctx.fillStyle = "rgba(0,0,0,.6)";
  ctx.fillRect(0, y0 + 3, IMG_W, 1);
  ctx.fillStyle = "rgba(236,208,142,.25)";
  ctx.fillRect(0, y0 + 7, IMG_W, 1);
  const cy = y0 + CAPTION_H / 2 + 3;

  // Emblem + title
  const ex = 64;
  // IndiaCiv's emblem (the favicon): a gold hexagon with a green peak.
  const hexagon = (r) => {
    ctx.beginPath();
    for (let k = 0; k < 6; k++) ctx.lineTo(ex + r * Math.cos(Math.PI / 3 * k - Math.PI / 2), cy + r * Math.sin(Math.PI / 3 * k - Math.PI / 2));
    ctx.closePath();
  };
  hexagon(31);
  ctx.fillStyle = "#120d06";
  ctx.fill();
  hexagon(28);
  ctx.fillStyle = "#c3ac62";
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(ex - 14, cy + 11);
  ctx.lineTo(ex, cy - 12);
  ctx.lineTo(ex + 14, cy + 11);
  ctx.closePath();
  ctx.fillStyle = "#517845";
  ctx.fill();

  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#ecd08e";
  ctx.font = `bold 36px ${SERIF}`;
  spaced(ctx, 5);
  ctx.fillText("INDIA", 112, cy + 2);
  spaced(ctx, 0);
  ctx.fillStyle = "#b9ab88";
  ctx.font = `italic 17px ${SERIF}`;
  ctx.fillText("A strategy-map atlas from public data", 114, cy + 28);
  if (info.lens?.share_credit) {
    ctx.font = `13px ${SANS}`;
    ctx.fillText(info.lens.share_credit, 114, cy + 46, 490);
  }

  // Lens + legend ramp
  const mx = 640;
  const lens = info.lens;
  const iconOk = (id) => id && hasIcon(id);
  const lensIcon = lens ? (iconOk(lens.icon) ? lens.icon : null) : "terrain";
  if (lensIcon) drawIcon(ctx, lensIcon, mx + 20, cy - 16, 40, { shadow: true });
  ctx.fillStyle = "#ecd08e";
  ctx.font = `24px ${SERIF}`;
  spaced(ctx, 1.5);
  if (lens?.share_credit) {
    ctx.fillText(lens.name.toUpperCase(), mx + 50, cy - 8, 390);
  } else {
    ctx.fillText(lens ? lens.name.toUpperCase() + " LENS" : "TERRAIN", mx + 50, cy - 8);
  }
  spaced(ctx, 0);
  if (lens?.ramp?.length) {
    const rx = mx + 50, ry = cy + 4, rw = 330, rh = 12;
    const rg = ctx.createLinearGradient(rx, 0, rx + rw, 0);
    lens.ramp.forEach((c, i) => rg.addColorStop(i / (lens.ramp.length - 1), c));
    ctx.fillStyle = "rgba(0,0,0,.6)";
    ctx.fillRect(rx - 1, ry - 1, rw + 2, rh + 2);
    ctx.fillStyle = rg;
    ctx.fillRect(rx, ry, rw, rh);
    ctx.font = `14px ${SANS}`;
    ctx.fillStyle = "#d8cba8";
    ctx.textAlign = "left";
    ctx.fillText("≤ " + info.formatValue(lens, 0), rx, ry + rh + 18);
    ctx.textAlign = "right";
    ctx.fillText("≥ " + info.formatValue(lens, 1), rx + rw, ry + rh + 18);
    ctx.textAlign = "left";
    if (lens.estimated && lens.source_line) {
      ctx.fillText(lens.source_line, rx, cy + 48, rw);
    }
  } else {
    ctx.font = `15px ${SANS}`;
    ctx.fillStyle = "#b9ab88";
    ctx.fillText("Land cover, relief and rivers", mx + 50, cy + 16);
  }

  // Selection, credits, site
  const rx = IMG_W - 44;
  ctx.textAlign = "right";
  const sel = info.selection;
  if (sel?.name) {
    ctx.font = `13px ${SANS}`;
    ctx.fillStyle = "#b9ab88";
    spaced(ctx, 2);
    ctx.fillText(sel.kind === "state" ? "STATE" : "CITY", rx, cy - 30);
    spaced(ctx, 0);
    ctx.font = `bold 24px ${SERIF}`;
    ctx.fillStyle = "#f3e6c4";
    ctx.fillText(fit(ctx, sel.name, 460), rx, cy - 6);
  }
  ctx.textAlign = "left";
  ctx.font = `14px ${SANS}`;
  ctx.fillStyle = "#d8cba8";
  credits.forEach((line, i) => ctx.fillText(line, 44, y0 + CAPTION_H + 17 * i, IMG_W - 88));

  // Thin gold frame around the whole picture
  ctx.strokeStyle = "rgba(201,164,92,.85)";
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, IMG_W - 2, imgH - 2);
  return cv;
}

function wrapCredit(ctx, line) {
  const lines = [];
  let current = "";
  for (const word of line.split(" ")) {
    const candidate = current ? `${current} ${word}` : word;
    if (current && ctx.measureText(candidate).width > IMG_W - 88) {
      lines.push(current);
      current = word;
    } else current = candidate;
  }
  if (current) lines.push(current);
  return lines;
}

function fit(ctx, text, maxW) {
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 3 && ctx.measureText(t + "…").width > maxW) t = t.slice(0, -1);
  return t + "…";
}

/**
 * opts: {button, getInfo() → composeImage info, fileName() → string, onToast(msg)}
 */
export function initShare(opts) {
  const btn = opts.button;
  const pop = document.getElementById("share-pop");
  if (!btn || !pop) return { close() {}, get isOpen() { return false; } };
  let restore = null;

  pop.innerHTML = `
    <div class="sp-title">Share this view</div>
    <button class="sp-item" data-act="copy">${icon("share", "🔗", { size: 16 })}<span>Copy link</span></button>
    <button class="sp-item" data-act="image">${icon("terrain", "🖼️", { size: 16 })}<span>Download image <span class="muted">1600×900 PNG</span></span></button>
    <div class="sp-status" role="status" aria-live="polite"></div>
    <input class="sp-url" type="text" readonly hidden aria-label="Link to this view">`;
  const status = pop.querySelector(".sp-status");
  const urlBox = pop.querySelector(".sp-url");

  function position() {
    const r = btn.getBoundingClientRect();
    const w = pop.offsetWidth || 250;
    pop.style.top = r.bottom + 8 + "px";
    pop.style.left = Math.max(8, Math.min(window.innerWidth - w - 8, r.right - w)) + "px";
  }
  function open() {
    restore = document.activeElement;
    status.textContent = "";
    urlBox.hidden = true;
    pop.hidden = false;
    btn.setAttribute("aria-expanded", "true");
    position();
    pop.querySelector(".sp-item")?.focus();
  }
  function close(restoreFocus = true) {
    if (pop.hidden) return;
    pop.hidden = true;
    btn.setAttribute("aria-expanded", "false");
    if (restoreFocus && restore && document.contains(restore)) restore.focus();
  }
  btn.addEventListener("click", () => (pop.hidden ? open() : close()));
  document.addEventListener("pointerdown", (e) => {
    if (!pop.hidden && !pop.contains(e.target) && !btn.contains(e.target)) close(false);
  });
  window.addEventListener("resize", () => !pop.hidden && position());

  pop.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-act]");
    if (!b) return;
    if (b.dataset.act === "copy") {
      opts.beforeCopy?.();
      const link = location.href;
      if (await copyText(link)) {
        status.textContent = "Link copied to the clipboard";
        opts.onToast?.("Link copied");
      } else {
        status.textContent = "Copy this link:";
        urlBox.hidden = false;
        urlBox.value = link;
        urlBox.focus();
        urlBox.select();
      }
    } else if (b.dataset.act === "image") {
      status.textContent = "Drawing the map…";
      await new Promise((r) => setTimeout(r, 30)); // let the status paint
      try {
        await opts.beforeImage?.();
        const cv = composeImage(opts.getInfo());
        const blob = await new Promise((r) => cv.toBlob(r, "image/png"));
        if (!blob) throw new Error("toBlob failed");
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = opts.fileName();
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 4000);
        status.textContent = `Saved ${a.download}`;
      } catch (err) {
        console.warn(err);
        status.textContent = "Could not create the image in this browser.";
      }
    }
  });

  return {
    open,
    close,
    get isOpen() { return !pop.hidden; },
  };
}
