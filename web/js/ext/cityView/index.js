import { buildModel } from "./model.js";
import { createMapLayer } from "./mapLayer.js";
import { createBannerFocus } from "./bannerFocus.js";
import { renderIndia } from "./indiaScreen.js";
import { icon } from "../../ui/icon.js";
import { esc } from "../../format.js";
import { indianNumber } from "../../ui/cityHeadlines.js";

const MODE = "city";
const CSS_HREF = new URL("../../../css/cityview.css", import.meta.url).href;

// The stylesheet, injected once; resolves when it has loaded (or after a short timeout), so a City View opened
// from a link on page load never shows unstyled.
function injectCss() {
  if (document.getElementById("cityview-css")) return Promise.resolve();
  const l = document.createElement("link");
  l.id = "cityview-css";
  l.rel = "stylesheet";
  l.href = CSS_HREF;
  const done = new Promise((resolve) => {
    l.onload = l.onerror = () => resolve();
    setTimeout(resolve, 1500);
  });
  document.head.appendChild(l);
  return done;
}

export async function install(app) {
  const eligible = (city) => city?.city_view === true;
  if (!app.data.cities.some(eligible)) return;
  let profiles, pendingOpen = 0;
  await injectCss();
  const banners = createBannerFocus(app);
  const layer = createMapLayer(app, { focusRect: banners.focusRect });
  const cv = {
    city: null, model: null, dock: null, legend: null, highlight: null,
    pinned: -1, prevCam: null, fromPreview: false, restoreCam: true, exiting: false, timer: 0,
  };
  const origCityPanel = app.panels.city;
  let lastCtx = null;

  // --- the quick panel: keep it, add an "Open City View" button -------------------------------------------------
  function addOpenButton(city) {
    const panel = app.panels.element;
    const head = panel?.querySelector(".cp-head");
    if (!eligible(city) || !head || head.querySelector(".cv-open")) return;
    const b = document.createElement("button");
    b.type = "button";
    b.className = "cv-open";
    b.innerHTML = `<span class="cv-open-ic" aria-hidden="true">${icon("layers", "▦", { size: 15 })}</span><span>Open City View</span><span class="cv-open-go" aria-hidden="true">›</span>`;
    b.title = `Open ${city.name} in City View`;
    b.onclick = () => openCityView(city);
    head.appendChild(b);
  }

  app.panels.city = (city, ctx) => {
    lastCtx = ctx;
    if (app.mode === MODE) {
      if (eligible(city)) {
        app.panels.close();
        show(city);
        return;
      }
      cv.restoreCam = false;
      app.setMode(null);
    }
    origCityPanel(city, ctx);
    addOpenButton(city);
  };

  // The quick panel's callbacks, for when it was opened before this extension installed (a #city= link).
  const fallbackCtx = () => ({
    w: app.w, nation: app.data.nation, states: app.data.states, cities: app.data.cities,
    onClose: () => app.clearSelection(),
    onPedia: (key) => app.pedia?.open?.(key),
    pediaLink: app.pediaLink,
    onState: (idx) => app.selectState(idx, { fly: true }),
    onCity: (c) => app.selectCity(c, { fly: true }),
  });

  function openCityView(city) {
    if (!eligible(city)) return;
    if (!profiles) {
      const request = ++pendingOpen;
      const selected = app.state.selectedCity;
      const selectedState = app.state.selectedState;
      return Promise.all([app.loadData("city_view"), app.loadData("lenses")]).then(([data]) => {
        profiles = data?.profiles;
        if (profiles && request === pendingOpen && !app.mode &&
            selected === app.state.selectedCity && selectedState === app.state.selectedState) openCityView(city);
      });
    }
    if (!Object.hasOwn(profiles, city.id)) return;
    if (app.mode === MODE) app.selectCity(city, { fly: false });
    else app.setMode(MODE, { id: city.id });
  }

  // --- showing a city -------------------------------------------------------------------------------------------
  function dockWidth() {
    const w = innerWidth;
    return w >= 1500 ? 470 : w >= 1100 ? 430 : Math.max(340, Math.round(w * 0.42));
  }

  function show(city, { fit = true } = {}) {
    if (!city) return;
    const same = cv.city === city && cv.dock && !cv.dock.hidden;
    cv.city = city;
    const m = buildModel(app, city, profiles[city.id]);
    cv.model = m;
    layer.set(m); // a new model restarts the border animation
    banners.set(m);
    cv.pinned = -1;
    layer.focus(-1);

    cv.dock = app.ui.dock("right", { width: dockWidth(), label: `City View: ${city.name}` });
    if (!same) {
      renderIndia(cv.dock, m, {
        onClose: () => leave(true),
        onSite: (s) => flyToSite(s),
        pediaLink: app.pediaLink,
        onPedia: app.pedia.open,
      }, profiles, app.data.cities);
      installSwipe(cv.dock);
    }

    cv.highlight = {
      cells: new Set(m.footprint),
      resources: new Set(m.sites.map((s) => s.index)),
      dimOthers: true,
      color: `rgb(${m.stateRGB.map((v) => v | 0).join(",")})`,
    };
    app.setHighlight(cv.highlight);
    updateLegend(m);
    // After the caller's own camera move (main.js selectCity(…, {fly: true}) flies to the city right after
    // calling the panel), so the metro framing wins.
    if (fit) queueMicrotask(() => { if (cv.model === m) fitMetro(m); });
    app.hash.update();
    app.requestDraw();
    if (!cv.timer) startAnim();
    if (!same) {
      requestAnimationFrame(() => cv.dock?.querySelector(".cv-name")?.focus({ preventScroll: true }));
    }
  }

  function fitMetro(m) {
    const b = m.bbox;
    if (!b) return;
    const R = app.w.grid.R;
    const mobile = app.isMobile();
    // Room for the city banner above, the lens dock below and the legend at the top left.
    app.fitBounds(b.x0, b.y0, b.x1, b.y1, {
      padTop: mobile ? 72 : 84, padBottom: mobile ? 16 : 86, padLeft: mobile ? 16 : 60, padRight: mobile ? 16 : 40,
      maxScale: 90 / R, ms: 850,
    });
  }

  function flyToSite(s) {
    const it = s.item;
    const g = app.w.grid;
    const x = it.site_x ?? it.x, y = it.site_y ?? it.y;
    app.flyTo(x, y, Math.max(app.cam.scale, 70 / g.R), 700);
    cv.pinned = it.cell ?? -1;
    layer.focus(cv.pinned);
  }

  // --- map legend (schematic note) --------------------------------------------------------------------------------
  // The key explains the footprint and the displayed population estimates.
  const LEGEND_KEY = "cityview.legendOpen";
  let legendOpen = null; // null: not chosen by the viewer yet
  try {
    const v = localStorage.getItem(LEGEND_KEY);
    if (v === "1" || v === "0") legendOpen = v === "1";
  } catch { /* storage blocked */ }

  function updateLegend(m) {
    if (!cv.legend) {
      cv.legend = document.createElement("div");
      cv.legend.className = "panel cv-maplegend";
      cv.legend.setAttribute("role", "note");
      cv.legend.addEventListener("click", (e) => {
        if (!e.target.closest(".cv-ml-i")) return;
        legendOpen = !cv.legend.classList.contains("open");
        try { localStorage.setItem(LEGEND_KEY, legendOpen ? "1" : "0"); } catch { /* storage blocked */ }
        setLegendOpen(legendOpen);
      });
      document.body.appendChild(cv.legend);
    }
    const col = `rgb(${m.stateRGB.map((v) => v | 0).join(",")})`;
    const n = m.footprint.length;
    const mapped = m.city.mapped_extent;
    const extent = m.profile.method === "point" ? "Point location" :
      `${n} hex${n === 1 ? "" : "es"}${mapped ? ` · ${indianNumber(mapped.km2)} km²` : ""}`;
    cv.legend.setAttribute("aria-label", `${m.city.name} metro on the map`);
    cv.legend.innerHTML = `
      <div class="cv-ml-t"><i class="cv-ml-sw" style="--sc:${col}"></i><b title="${esc(m.city.full || m.city.name)}">${esc(m.city.name)}</b><span class="cv-ml-k">· ${extent}</span><button type="button" class="cv-ml-i" aria-controls="cv-ml-body" title="Map key">i</button></div>
      <div class="cv-ml-body" id="cv-ml-body">
        <p class="cv-ml-n">${m.profile.method === "point" ? "City location · footprint unavailable" :
          "GHSL urban footprint. Mid-2026 residents are IndiaCiv estimates from WorldPop and the UN projection. Land-cover symbols use ESA WorldCover imagery."}</p>
        ${mapped ? `<p class="cv-ml-n">Area · ${esc(mapped.period)} · IndiaCiv estimate · GHSL and Survey of India</p>` : ""}
      </div>`;
    setLegendOpen(legendOpen ?? false);
  }
  function setLegendOpen(open) {
    if (!cv.legend) return;
    cv.legend.classList.toggle("open", open);
    const b = cv.legend.querySelector(".cv-ml-i");
    if (b) {
      b.setAttribute("aria-expanded", open ? "true" : "false");
      b.setAttribute("aria-label", open ? "Hide the map key" : "Show the map key");
    }
  }

  // --- swipe the bottom sheet down to close (phones) ----------------------------------------------------------------
  function installSwipe(el) {
    if (el._cvSwipe) return;
    el._cvSwipe = true;
    let st = null;
    el.addEventListener("pointerdown", (e) => {
      if (e.pointerType === "mouse" || !app.isMobile() || !el.classList.contains("cv-dock")) return;
      const fromHead = e.target.closest(".cv-grip, .cv-head");
      if ((!fromHead && el.scrollTop > 0) || e.target.closest("button, a, input, select, summary")) return;
      st = { y: e.clientY, id: e.pointerId, dy: 0, head: !!fromHead };
    });
    el.addEventListener("pointermove", (e) => {
      if (!st || e.pointerId !== st.id) return;
      st.dy = Math.max(0, e.clientY - st.y);
      if (st.dy > 6 && (st.head || el.scrollTop <= 0)) {
        el.classList.add("cv-dragging");
        el.style.transform = `translateY(${st.dy}px)`;
      }
    });
    const end = (e) => {
      if (!st || e.pointerId !== st.id) return;
      const dy = st.dy;
      st = null;
      el.classList.remove("cv-dragging");
      el.style.transform = "";
      if (dy > 80 && app.mode === MODE) leave(true);
    };
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
  }

  // --- animation (the border's glow and marching line) -------------------------------------------------------------
  function startAnim() {
    stopAnim();
    if (!layer.animates()) return;
    // The layer settles on a still frame a few seconds after a city opens: draw that frame, then stop.
    cv.timer = setInterval(() => {
      if (!document.hidden) app.requestDraw();
      if (!layer.animates()) stopAnim();
    }, 40);
  }
  function stopAnim() {
    clearInterval(cv.timer);
    cv.timer = 0;
  }

  // The hover tooltip says "Click to open the city"; inside the City View that is wrong for the open city (it is
  // already open: the line goes) and for its neighbours (a click switches the view). The tooltip belongs to the
  // core, so this rewrites its line after the core has drawn it.
  let hoverCity = null;
  app.on("hover", (h) => { hoverCity = h?.city || null; });
  const tipObserver = new MutationObserver(() => {
    if (app.mode !== MODE || !cv.city) return;
    const tip = document.getElementById("tooltip");
    if (!tip) return;
    for (const s of tip.querySelectorAll("span.muted")) {
      if (s.textContent !== "Click to open the city") continue;
      if (hoverCity === cv.city) {
        const br = s.previousSibling;
        if (br && br.nodeName === "BR") br.remove();
        s.remove();
      } else if (eligible(hoverCity)) {
        s.textContent = "Click to open its City View";
      }
    }
  });

  // --- the mode ---------------------------------------------------------------------------------------------------
  function leave(restoreCam) {
    if (app.mode !== MODE) return;
    cv.restoreCam = restoreCam;
    app.setMode(null);
  }

  app.registerMode(MODE, {
    enter(p) {
      const city = (p?.id && app.cityById.get(String(p.id))) || app.state.selectedCity;
      if (!eligible(city) || !profiles?.[city.id]) {
        queueMicrotask(() => app.mode === MODE && app.setMode(null));
        return;
      }
      cv.prevCam = { x: app.cam.x, y: app.cam.y, scale: app.cam.scale };
      cv.fromPreview = app.state.selectedCity === city && !!app.panels.element && !app.panels.element.hidden;
      cv.restoreCam = true;
      cv.city = null;
      document.body.classList.add("cv-on");
      if (app.state.selectedCity !== city) app.selectCity(city, { fly: false }); // → app.panels.city → show()
      else {
        app.panels.close();
        show(city);
      }
      startAnim();
      const tip = document.getElementById("tooltip");
      if (tip) tipObserver.observe(tip, { childList: true, subtree: true, characterData: true });
    },
    exit() {
      cv.exiting = true;
      try {
        stopAnim();
        const city = cv.city;
        cv.city = null;
        cv.model = null;
        layer.set(null);
        banners.set(null);
        tipObserver.disconnect();
        if (cv.dock) {
          cv.dock.classList.remove("cv-dock");
          cv.dock.onscroll = null;
          cv.dock.style.transform = "";
        }
        app.ui.undock("right");
        cv.dock = null;
        cv.legend?.remove();
        cv.legend = null;
        document.body.classList.remove("cv-on");
        if (app.state.highlight === cv.highlight) app.setHighlight(null);
        cv.highlight = null;
        if (cv.restoreCam && cv.prevCam) {
          const p = cv.prevCam;
          app.cam.flyTo(p.x, p.y, p.scale, 700);
          app.requestDraw();
        }
        cv.prevCam = null;
        // Back to where we came from: the quick panel if it was open, else nothing selected.
        if (city && app.state.selectedCity === city) {
          if (cv.fromPreview) {
            origCityPanel(city, lastCtx || fallbackCtx());
            addOpenButton(city);
          } else app.clearSelection();
        }
      } finally {
        cv.exiting = false;
      }
    },
  });

  // The selection moved elsewhere (a state, nothing, Back in the browser): leave without flying back.
  app.on("select", (sel) => {
    if (app.mode !== MODE || cv.exiting) return;
    if (sel?.kind === "city") return; // app.panels.city already switched the view
    cv.restoreCam = false;
    app.setMode(null);
  });

  // Map clicks: a city opens (or switches) the City View; inside the metro clicks stay in it; a click outside
  // closes it.
  app.on("mapclick", (e) => {
    if (app.mode && app.mode !== MODE) return false; // another extension's mode owns the clicks
    if (app.mode !== MODE) {
      if (eligible(e.city)) {
        openCityView(e.city);
        return true;
      }
      return false;
    }
    if (e.city) {
      if (eligible(e.city)) {
        if (e.city !== cv.city) openCityView(e.city);
        return true;
      }
      cv.restoreCam = false;
      app.setMode(null);
      return false;
    }
    const m = cv.model;
    if (e.resource && m && m.sites.some((s) => s.item === e.resource)) {
      const s = m.sites.find((x) => x.item === e.resource);
      if (s) {
        cv.pinned = s.item.cell ?? -1;
        layer.focus(cv.pinned);

      }
      return true;
    }
    if (m && m.mask.has(e.cell)) return true;
    // Outside the metro: the click only closes the City View (the camera stays where the user is looking).
    cv.restoreCam = false;
    app.setMode(null);
    return true;
  });

  // URL: #city=<id>&view=city
  app.hash.register("view", {
    get: () => (app.mode === MODE && cv.city ? "city" : null),
    set(v) {
      if (v === "city") {
        const city = app.state.selectedCity;
        if (!eligible(city)) return;
        if (app.mode !== MODE) openCityView(city);
        else if (cv.city !== city) show(city);
      } else if (app.mode === MODE) {
        cv.restoreCam = false; // the URL's own camera ("at") wins
        app.setMode(null);
      }
    },
  });

  // A dock-width change on resize (desktop) keeps the dock proportionate.
  let rz = 0;
  addEventListener("resize", () => {
    clearTimeout(rz);
    rz = setTimeout(() => {
      if (app.mode === MODE && cv.dock && !app.isMobile()) app.ui.dock("right", { width: dockWidth(), label: `City View: ${cv.city?.name || ""}` });
    }, 150);
  });

  // If the quick panel is already showing a city (a #city= link opened before we installed), add the button.
  if (app.state.selectedCity && app.panels.element && !app.panels.element.hidden && app.panels.element.dataset.kind === "city") {
    addOpenButton(app.state.selectedCity);
  }

  app.cityView = { open: openCityView, close: () => leave(true), get city() { return cv.city; }, get model() { return cv.model; } };
}
