// The Almanac: what every number means and exactly where it comes from.
import { resolveTables } from "../terrain.js";
import { esc } from "../format.js";
import { parseHex, luminance } from "../color.js";
import { icon, glyph } from "./icon.js";
import { formatLensValue, lensPeriodLabels } from "./lenses.js";

const COVER_ICON = { forest_deciduous: "l-forest", forest_evergreen: "l-forest", forest_mixed: "l-forest", cropland: "l-farmland", pasture: "l-farmland", urban: "l-developed" };
// Glyph colour that reads on a resource medallion (dark on light faces such as nuclear yellow or silver).
const inkOn = (hex) => {
  try { return /^#[0-9a-f]{6}$/i.test(hex || "") && luminance(parseHex(hex)) > 0.4 ? "#1c1710" : "#f8f0d8"; } catch { return "#f8f0d8"; }
};
const CATEGORY = { energy: "Energy", mineral: "Minerals", agri: "Agriculture" };

export function initPedia(data) {
  const modal = document.getElementById("pedia");
  const card = modal.querySelector(".modal-card");
  const nav = document.getElementById("pedia-nav");
  const body = document.getElementById("pedia-body");
  const srcName = (id) => data.sources?.find((s) => s.id === id)?.title || id || "";
  const sourceCaption = (text) => esc(text).replace(/\b[\da-f]{40,64}\b/gi,
    (hash) => `<abbr title="${hash}">${hash.slice(0, 8)}…</abbr>`);
  let restoreFocus = null;

  const h2 = (ic, fb, text) => `<h2>${icon(ic, fb, { size: 24 })}<span>${esc(text)}</span></h2>`;

  const link = (url, label) => /^(https?:\/\/|data\/[a-z0-9_-]+\.json$|LICENSE$)/i.test(url || "")
    ? `<a href="${esc(url)}">${esc(label)}</a>` : "";
  const row = (x) => `<tr><td class="nm">${x.color ? `<span class="swatch" style="background:${esc(x.color)}"></span>` : ""}${
    COVER_ICON[x.key] ? icon(COVER_ICON[x.key], "", { size: 15 }) + " " : ""}<b>${esc(x.name)}</b></td>
    <td>${esc(x.rule || "").replaceAll("\n", "<br>")}${(x.links || []).map(({ url, label }) =>
      link(url, label)).filter(Boolean).map((ref) => "<br>" + ref).join("")}</td></tr>`;
  const sections = (name) => Object.entries(data.almanac?.sections?.[name] || {}).map(([heading, rows]) =>
    `<h4>${esc(heading)}</h4><table>${rows.map(row).join("")}</table>`).join("");

  const pages = {
    "About this map": () => `
      ${h2("pedia", "📖", "About this map")}
      <p>This is India, drawn like a strategy game. The map uses the data listed under <i>Sources</i>.</p>
      <h4>Controls</h4>
      <p>Drag or arrow keys / WASD to pan · scroll, +/– or double-click to zoom · click a city or a state to open it ·
      / or ⌘K to search · L to cycle lenses · R to show or hide resources · ? for all shortcuts · Esc to close.</p>
      <p>The address bar always holds a link to what you're looking at (lens, selection and view); use <i>Share</i> to copy it
      or to download a picture.</p>`,
    Yields: () => `
      ${h2("y-production", "⚙️", "Yields")}
      <table>${data.nation.yields.map((y) => `<tr><td class="ic" style="color:${esc(y.color)}">${glyph(y, 26)}</td><td><b style="color:${esc(y.color)}">${esc(y.label)}${y.key === "gold" ? " (GDP)" : ""}</b><br>${esc(y.description)}<br>
        <span class="muted">${[y.period, y.scale && `${y.scale.toLocaleString("en-IN")} ${y.unit} per point`, ...(y.sources || []).map(srcName)].filter(Boolean).map(esc).join(" · ")}</span></td></tr>`).join("")}</table>`,
    States: () => `
      ${h2("terrain", "🗺️", "States")}
      ${data.states ? "" : `<p class="muted">This data build has no states.json, so state panels show names and cities only.</p>`}`,
    Terrain: () => {
      const t = data.w?.tables || resolveTables(data.world.tables);
      const hasCover = Array.isArray(data.world.cover);
      return `
      ${h2("terrain", "🗺️", "Terrain")}
      <h4>${icon("l-forest", "🌲", { size: 16 })} Land cover</h4>
      ${hasCover
        ? `${data.world.base ? "" : `<p>The base colour of each hex is its dominant land-cover group: the largest group among the land samples inside it.
           Small symbols show the mix: trees scale with the forest share, and fields, reeds, shrubs and grass tufts mark farmland,
           wetland, scrub and grassland.</p>`}
           <table>${t.cover.filter((x) => x.id > 0).map(row).join("")}</table>`
        : `<p class="muted">This data build has no land-cover layer yet; land is coloured by elevation.</p>`}
      <h4>Relief</h4>
      <table>${(data.almanac?.terrain_relief || t.relief).map(row).join("")}</table>
      <h4>${icon("r-hydro", "💧", { size: 16 })} Water</h4>
      <table>${t.water.filter((x) => x.id > 0).map(row).join("")}</table>
      <h4>Beyond the borders</h4>
      <p class="muted">Neighbouring countries are drawn under light fog for context.</p>`;
    },
    Lenses: () => `
      ${h2("layers", "▤", "Lenses")}
      <p>Lenses recolour the map by one measure. The period and method are listed for each lens.</p>
      <p>The legend shows how many hexes fall at each value. Hover or drag on it to show only that range on the map.</p>
      ${(data.lenses.groups || [{ id: null, name: "" }]).map((g) => {
        const ls = data.lenses.lenses.filter((l) => !g.id || l.group === g.id);
        if (!ls.length) return "";
        return `${g.name ? `<h3 class="grp">${icon(`g-${g.id}`, "", { size: 16 })} ${esc(g.name)}</h3>` : ""}${ls.map((l) => `
          <div class="lens-entry"><div class="le-ic">${glyph(l, 26)}</div><div>
          <h4>${esc(l.name)}</h4><p>${esc(l.description || "")}<br>
          ${lensPeriodLabels(l)}${l.estimated ? " · IndiaCiv estimate" : ""}
          ${[l.note, l.source_line].filter(Boolean).map((note) => "<br>" + esc(note)).join("")}
          <i class="le-ramp" style="background:linear-gradient(90deg, ${(l.ramp || []).map(esc).join(",")})"></i>
          <span class="muted">Scale: ${esc(l.scale)}${l.period && l.domain?.every(Number.isFinite)
            ? " · " + esc(l.format === "category"
              ? (l.categories || []).map((category) => category.name).join(" · ")
              : l.domain.map((bound) => formatLensValue(l, bound)).join("–")) : ""}${
            l.higher_is === "good" ? " · higher is better" : l.higher_is === "bad" ? " · higher is worse" : ""}${[...new Set([l.source, ...(l.sources || [])].filter(Boolean))].map((id) => " · " + esc(srcName(id))).join("")}</span></p></div></div>`).join("")}`;
      }).join("")}`,
    Resources: () => {
      const r = data.resources;
      if (!r?.types?.length) return `${h2("resources", "⛏️", "Resources")}<p class="muted">This data build has no resources layer.</p>`;
      const count = new Map();
      for (const it of r.items || []) count.set(it.type, (count.get(it.type) || 0) + 1);
      const cats = [...new Set(r.types.map((t) => t.category || "other"))];
      return `
      ${h2("resources", "⛏️", "Resources")}
      <p>Resources mark power plants, mines, fuel fields and representative agricultural sites.
      Inclusion criteria appear in each type's description. When zoomed out, a hex shows its
      highest-ranked resource; zoom in to see more. Press <b>R</b> to show or hide them.</p>
      ${cats.map((c) => `<h4>${esc(CATEGORY[c] || c)}</h4><table class="res-table">
        <tr><th></th><th>Type</th><th>What counts</th><th>Sites</th></tr>
        ${r.types.filter((t) => (t.category || "other") === c).map((t) => `<tr>
          <td class="ic"><span class="res-ic" style="background:${esc(t.color || "#24384f")};color:${inkOn(t.color)}">${glyph(t, 20)}</span></td>
          <td class="nm"><b>${esc(t.name)}</b>${t.unit ? `<br><span class="muted">value in ${esc(t.unit)}</span>` : ""}</td>
          <td>${esc(t.description || "")}${t.threshold ? "<br>" + esc(t.threshold) : ""}<br><span class="muted">${[t.period, srcName(t.source)].filter(Boolean).map(esc).join(" · ")}</span></td>
          <td class="num">${(count.get(t.id) || 0).toLocaleString("en-IN")}</td></tr>`).join("")}</table>`).join("")}`;
    },
    Sources: () => `
      ${h2("pedia", "📖", "Sources")}
      ${data.sources.map((s) => `
        <h4>${esc(s.title)}</h4>
        <p>${sourceCaption(s.description)}<br>
        <span class="muted">${esc(s.publisher)} · ${link(s.license_url, s.license) || esc(s.license)}${s.period || (s.vintage && s.vintage !== "older") ? " · " + esc(s.period || s.vintage) : ""} ·
        <a href="${esc(s.homepage)}" target="_blank" rel="noopener">homepage</a></span><br>
        ${(s.used_for || []).map(esc).join(" · ")}
        ${(s.credit_links || (s.credit_link ? [s.credit_link] : [])).map(({ url, label }) => link(url, label)).join(" · ")}
        ${link(s.download_path, s.download_label || "Download derived data")}</p>
        <table>${(s.files || []).map((f) => `<tr><td>${link(f.url, "Source file")}${f.sha256 ? `<br><code title="${esc(f.sha256)}">SHA-256 ${esc(f.sha256.slice(0, 8))}…</code>` : ""}
          ${f.timestamp ? `<br><code>${esc(f.timestamp)}</code>` : ""}${f.query ? `<br><code title="${esc(f.query)}">Source query</code>` : ""}</td>
          <td class="muted" style="white-space:nowrap">${esc((f.retrieved || "").slice(0, 10))}${f.bytes ? `<br>${(f.bytes / 1e6).toFixed(1)} MB` : ""}</td></tr>`).join("")}</table>`).join("")}`,
  };

  const show = (name) => {
    if (!pages[name]) name = "About this map";
    body.innerHTML = pages[name]() + sections(name);
    body.scrollTop = 0;
    nav.querySelectorAll("button").forEach((b) => {
      const on = b.dataset.page === name;
      b.classList.toggle("active", on);
      b.setAttribute("aria-current", on ? "page" : "false");
    });
  };
  nav.innerHTML = `<div class="hd">Almanac</div>` + Object.keys(pages).map((p) => `<button data-page="${esc(p)}">${esc(p)}</button>`).join("");
  nav.onclick = (e) => {
    const b = e.target.closest("button[data-page]");
    if (b) show(b.dataset.page);
  };
  const close = () => {
    if (modal.hidden) return;
    modal.hidden = true;
    if (restoreFocus && document.contains(restoreFocus)) restoreFocus.focus();
    restoreFocus = null;
  };
  modal.onclick = (e) => {
    if (e.target === modal || e.target.closest("[data-close]")) close();
  };
  // Keep Tab inside the dialog.
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...card.querySelectorAll("button, a[href], [tabindex]:not([tabindex='-1'])")].filter((x) => x.offsetParent);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  return {
    open(page = "About this map") {
      if (modal.hidden) restoreFocus = document.activeElement;
      show(page);
      modal.hidden = false;
      (nav.querySelector("button.active") || card.querySelector("[data-close]"))?.focus();
      if (!data.almanac && data.loadAlmanac) data.loadAlmanac().then((almanac) => {
        if (!almanac || data.almanac) return;
        data.almanac = almanac;
        if (!modal.hidden) show(nav.querySelector("button.active")?.dataset.page || page);
      });
    },
    close,
    get isOpen() {
      return !modal.hidden;
    },
  };
}
