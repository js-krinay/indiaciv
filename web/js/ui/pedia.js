import { esc } from "../format.js";
import { buildPediaIndex, categories, indexFeatureCells, searchPedia } from "./pediaIndex.js";
import { paintPedia, specimen } from "./pediaArt.js";
import { pediaNotes } from "./pediaNotes.js";
import { articleContent, caption } from "./pediaArticle.js";

const INTRO = {
  state: "States", wonder: "Wonders", terrain: "Terrain", resource: "Resources",
  lens: "Lenses", river: "Rivers", rail: "Railways", trade: "Trade", protected: "Protected land", yield: "Yields",
};

export function initPedia(data, routing) {
  const modal = document.getElementById("pedia");
  const card = modal.querySelector(".modal-card");
  const nav = document.getElementById("pedia-nav");
  const body = document.getElementById("pedia-body");
  const search = document.getElementById("pedia-search");
  const picker = document.getElementById("pedia-category");
  const back = document.getElementById("pedia-back");
  const forward = document.getElementById("pedia-forward");
  let featureCells, index, notes, featured, sorted, loading;
  const features = () => (featureCells ??= indexFeatureCells(data.world));
  function prepare() {
    index = buildPediaIndex(data, features());
    notes = pediaNotes(data);
    featured = ["state/UP", "wonder/whc-251", "terrain/relief-hills"].filter((key) => index.has(key));
    data.homeCell = index.get("terrain/relief-hills")?.cell ?? index.get("state/UP")?.cell
      ?? data.world.owner.findIndex((owner) => owner >= 0);
    if (data.homeCell < 0) data.homeCell = null;
    sorted = [...index.values()].filter((entry) => entry.id !== "index")
      .sort((a, b) => (a.group || "").localeCompare(b.group || "") || a.title.localeCompare(b.title));
  }

  let current = null;
  let currentEntryId = null;
  let opener = null;
  const inerted = new Set();
  const locations = new Map();
  const visibleThumbnails = new IntersectionObserver((entries) => {
    for (const observed of entries) if (observed.isIntersecting) paintCanvas(observed.target);
  }, { root: body });

  function link(key, label) {
    const entry = index.get(key);
    if (!entry) return "";
    return `<a href="${esc(routing.href(key))}" data-route="${esc(key)}">${esc(label || entry.title)}</a>`;
  }

  function sourceLink(id) {
    const key = `source/${id}`;
    return link(key, index.get(key)?.shortTitle);
  }

  function cards(entries, { art = false, group = (entry) => entry.group } = {}) {
    let previous = null;
    return entries.map((entry) => {
      const section = group(entry);
      const heading = section && section !== previous ? `<h2>${esc(section)}</h2>` : "";
      previous = section;
      return `${heading}<div class="pedia-card">${art ? specimen(entry, caption(entry)) : ""}
        ${link(entry.key)}${entry.location ? `<small>${esc(entry.location)}</small>` : ""}
        ${entry.kind === "source" && entry.row ? `<small>${esc(entry.row.license || "")}</small>` : ""}</div>`;
    }).join("");
  }

  function home() {
    return `<div class="pedia-hero"><div><p class="pedia-kicker">IndiaCiv Almanac</p>
      <h1 tabindex="-1">Read the map</h1>
      <p>Explore India as a strategy-game map. Follow rivers across painted hexes, see where cities and
      resources cluster, and look up the wonders you find along the way.</p></div>
      ${specimen(index.get("home/index"), "Painted terrain from the map build")}</div>
      <h2>From the map</h2><div class="pedia-featured">${cards(featured.map((key) => index.get(key)), { art: true, group: () => "" })}</div>
      <h2>How to read the map</h2>
      <p>Terrain, relief and features describe the land. City banners mark urban agglomerations. Resource markers
      identify mapped sites. Switch lenses to colour the map by one measure at a time. Select a tile or wonder to
      open its Almanac entry.</p>
      <h2>The 2026 data promise</h2>
      <p>Figures describe 2026 and carry their period and estimate or projection label where applicable.
      Reporting years ending in 2026 carry their exact dates, including FY 2025-26 (1 Apr 2025 – 31 Mar 2026).
      Missing figures stay blank. Terrain and locations describe the map build. ${link("source/index")} lists
      the datasets, how we adapted them and their reuse terms.</p>
      <p>IndiaCiv builds on Andrej Karpathy’s usaciv, released under the MIT licence.
      ${link("source/usaciv", "Read the full licence")}.</p>
      ${notes["About this map"]()}`;
  }

  function categoryPage(entry) {
    const entries = sorted.filter((row) => row.kind === entry.kind);
    const method = INTRO[entry.kind] ? notes[INTRO[entry.kind]]() : "";
    const map = entry.kind === "rail" && data.infrastructure?.rail?.length
      ? '<button class="btn pedia-map-action" data-map>Show railways on map</button>' : "";
    const protection = entry.kind === "protected" && entries.length
      ? '<button class="btn pedia-map-action" data-map>Show protected land on map</button>' : "";
    const trade = entry.kind === "trade" && entry.target
      ? '<button class="btn pedia-map-action" data-map>Show trade on map</button>' : "";
    return `<h1 tabindex="-1">${esc(entry.title)}</h1>${map}${protection}${trade}
      <div class="pedia-catalogue">${cards(entries)}</div>${method}
      ${entry.sources.length ? `<h2>Sources</h2><ul>${entry.sources.map((id) => `<li>${sourceLink(id)}</li>`).join("")}</ul>` : ""}
      ${!entries.length && !method ? '<p class="muted">No entries are available in this map build.</p>' : ""}`;
  }

  function article(entry) {
    const { facts, detail, intro } = articleContent(entry, data, index, link);
    const related = [...new Set(entry.related)].map((key) => index.get(key)).filter(Boolean);
    const nearby = entry.nearby?.map((key) => index.get(key));
    const sourceLinks = entry.sources.map(sourceLink);
    return `<p class="pedia-breadcrumb">${link(`${entry.kind}/index`)} / ${esc(entry.title)}</p>
      <div class="pedia-hero">
        <div><p class="pedia-kicker">${esc(entry.group || entry.category)}${entry.location ? ` · ${esc(entry.location)}` : ""}</p>
        <h1 tabindex="-1">${esc(entry.title)}</h1>${intro ? `<p>${esc(intro)}</p>` : ""}
        ${entry.target ? `<button class="btn pedia-map-action" data-map>${entry.kind === "lens" ? "Activate on map" : "Show on map"}</button>` : ""}</div>
        ${entry.kind === "source" ? "" : specimen(entry, caption(entry))}
      </div>
      ${facts.length ? `<dl class="pedia-facts">${facts.map(([label, value, period]) =>
        `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd>${period ? `<dd class="muted">${esc(period)}</dd>` : ""}</div>`).join("")}</dl>` : ""}
      ${detail}
      ${related.length ? `<h2>${entry.kind === "source" ? "Used in the Almanac" : "Related entries"}</h2><div class="pedia-catalogue">${cards(related, { group: (row) => row.category })}</div>` : ""}
      ${nearby?.length ? `<h2>Nearby cities and wonders</h2><p>Within 100 km on the projected map.</p>
        <div class="pedia-catalogue">${cards(nearby, { group: () => "" })}</div>` : ""}
      ${sourceLinks.length ? `<h2>Sources</h2><ul>${sourceLinks.map((html) => `<li>${html}</li>`).join("")}</ul>` : ""}`;
  }

  function render({ focus = true, restore = false } = {}) {
    visibleThumbnails.disconnect();
    if (!index) {
      body.innerHTML = '<h1 tabindex="-1">Almanac</h1><p role="status">Loading the Almanac…</p>';
      if (focus) body.querySelector("h1").focus({ preventScroll: true });
      loading ??= Promise.resolve(routing.load?.()).then(() => {
        prepare();
        if (current) render({ focus: body.contains(document.activeElement) });
      });
      return;
    }
    const kind = current.split("/")[0];
    const entry = index.get(current);
    if (search.value.trim()) {
      const matches = searchPedia(index, search.value);
      body.innerHTML = `<h1 tabindex="-1">Search results</h1><p role="status" data-search-results>${matches.length.toLocaleString("en-IN")}
        ${matches.length === 1 ? "result" : "results"}</p>
        ${matches.length ? `<div class="pedia-catalogue">${cards(matches, { group: (row) => row.category, })}</div>`
          : "<p>No matching entries.</p>"}`;
    } else if (!entry) {
      body.innerHTML = `<h1 tabindex="-1">Entry unavailable</h1><p>This entry is unavailable in the current map build.</p>
        <p>${link(`${kind}/index`)} ${link("home/index")}</p>`;
    } else {
      body.innerHTML = current === "home/index" ? home() : entry.id === "index" ? categoryPage(entry) : article(entry);
    }
    nav.innerHTML = Object.entries(categories).map(([key, label]) =>
      `<a href="${esc(routing.href(`${key}/index`))}" data-route="${key}/index"${key === kind ? ' aria-current="page"' : ""}>${esc(label)}</a>`).join("");
    picker.value = categories[kind] ? kind : "home";
    const location = restore ? locations.get(currentEntryId) : null;
    body.scrollTop = location?.scroll || 0;
    if (focus) {
      const anchor = location?.focus && [...body.querySelectorAll("[data-route]")]
        .find((item) => item.dataset.route === location.focus);
      (anchor || (location?.scroll ? body : body.querySelector("h1")))?.focus({ preventScroll: true });
    }
    for (const thumb of body.querySelectorAll(".pedia-card canvas")) visibleThumbnails.observe(thumb);
    redraw();
  }

  function paintCanvas(canvas) {
    paintPedia(canvas, index.get(canvas.dataset.specimen), data);
  }

  function redraw() {
    if (modal.hidden) return;
    const articleBounds = body.getBoundingClientRect();
    for (const canvas of body.querySelectorAll("[data-specimen]")) {
      const bounds = canvas.getBoundingClientRect();
      if (!canvas.closest(".pedia-card") || (bounds.bottom > articleBounds.top && bounds.top < articleBounds.bottom)) paintCanvas(canvas);
    }
  }

  const resize = new ResizeObserver(redraw);
  resize.observe(body);
  let resolution;
  function watchResolution() {
    resolution = matchMedia(`(resolution: ${devicePixelRatio}dppx)`);
    resolution.addEventListener("change", () => { redraw(); watchResolution(); }, { once: true });
  }
  watchResolution();

  function inertBackground() {
    for (const element of modal.parentElement.children) {
      if (element === modal || element.inert) continue;
      element.inert = true;
      inerted.add(element);
    }
  }
  const background = new MutationObserver(inertBackground);

  function rememberLocation() {
    if (!current || currentEntryId == null) return;
    const active = document.activeElement;
    const focus = body.contains(active) ? active?.dataset.route : null;
    locations.set(currentEntryId, { scroll: body.scrollTop, focus });
  }

  function apply(key, { restore = false, mapFocus = false } = {}) {
    const nextEntryId = routing.entryId();
    if (key && key === current && restore && nextEntryId === currentEntryId) return;
    if (!search.value) rememberLocation();
    if (!key) {
      if (modal.hidden) return;
      modal.hidden = true;
      current = null;
      background.disconnect();
      for (const element of inerted) element.inert = false;
      inerted.clear();
      const focus = mapFocus ? document.getElementById("map") : opener?.isConnected ? opener : document.getElementById("btn-pedia");
      focus?.focus({ preventScroll: true });
      opener = null;
      return;
    }
    if (modal.hidden) {
      opener = document.activeElement === document.body ? document.getElementById("btn-pedia") : document.activeElement;
      inertBackground();
      background.observe(modal.parentElement, { childList: true });
      modal.hidden = false;
    }
    current = key;
    currentEntryId = nextEntryId;
    search.value = "";
    render({ restore });
  }

  function open(key = "home/index") {
    routing.navigate(key);
  }

  function close() {
    routing.navigate(null);
  }

  picker.innerHTML = Object.entries(categories).map(([id, label]) => `<option value="${id}">${esc(label)}</option>`).join("");
  picker.onchange = () => open(`${picker.value}/index`);
  search.oninput = () => {
    if (!body.querySelector("[data-search-results]")) rememberLocation();
    render({ focus: false, restore: !search.value });
  };
  back.onclick = () => routing.travel(-1);
  forward.onclick = () => routing.travel(1);

  modal.addEventListener("click", (event) => {
    const anchor = event.target.closest("a[data-route]");
    if (anchor && event.button === 0 && !event.metaKey && !event.ctrlKey && !event.altKey && !event.shiftKey) {
      event.preventDefault();
      open(anchor.dataset.route);
    } else if (event.target === modal || event.target.closest("[data-close]")) close();
    else if (event.target.closest("[data-site-index]")) {
      const siteIndex = Number(event.target.closest("[data-site-index]").dataset.siteIndex);
      const row = index.get(current)?.items?.[siteIndex];
      if (row) routing.navigate(null, { kind: "resource", row });
    } else if (event.target.closest("[data-example]")) {
      routing.navigate(null, { kind: "cell", cell: Number(event.target.closest("[data-example]").dataset.example) });
    } else if (event.target.closest("[data-map]")) {
      const target = index.get(current)?.target || { kind: current.split("/")[0] };
      routing.navigate(null, target);
    }
  });

  modal.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      if (search.value) { search.value = ""; render({ focus: false, restore: true }); search.focus(); }
      else close();
      return;
    }
    if (event.key !== "Tab") return;
    const items = [...card.querySelectorAll("button, a[href], input, select")].filter((el) => el.offsetParent && !el.disabled);
    if (event.shiftKey && document.activeElement === items[0]) {
      event.preventDefault();
      items.at(-1)?.focus();
    } else if (!event.shiftKey && document.activeElement === items.at(-1)) {
      event.preventDefault();
      items[0]?.focus();
    }
  });

  return {
    apply, open, close, has: (key) => index?.has(key) ?? false,
    featuresAt(cell) {
      return [...new Set([...(data.world.features?.[cell] || []), ...(features().get(cell) || [])])];
    },
    setHistory({ back: canBack, forward: canForward }, id) {
      back.disabled = !canBack;
      forward.disabled = !canForward;
      currentEntryId = id;
    },
    get route() { return current; },
    get isOpen() { return !modal.hidden; },
  };
}
