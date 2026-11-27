// IndiaCiv installs the transport and wonders layers from the shared map-art extension.
import { createModel } from "./model.js";
import { makeLayers } from "./layers.js";
import { tips } from "./tips.js";
import { esc } from "../../format.js";
import { showPanel } from "../../ui/infoPanel.js";
import { wonderFactsHtml } from "../../ui/wonderFacts.js";
import { indiaTradeLayer } from "./indiaTrade.js";
import { installProtectedLand } from "./protectedLand.js";

const TOGGLES = [
  { id: "roads", label: "Highways", icon: "t-road", def: false, title: "Open expressways and national highways" },
  { id: "rail", label: "Railways", icon: "t-rail", def: true, title: "Active main and secondary rail lines" },
  { id: "hubs", label: "Ports & airports", icon: "d-harbor", def: true, title: "Ports by cargo and airports by size class" },
];

export function install(app) {
  const transport = app.data.infrastructure;
  const wonders = app.data.wonders?.wonders?.length > 0;
  const protection = installProtectedLand(app, () => app.mapArt?.on.wonders ?? wonders);
  if (!transport && !wonders) return;
  const model = createModel(app.w);
  model.data.sources = app.data.sources;
  model.setData("infrastructure", transport);
  model.setData("wonders", app.data.wonders);
  const byId = new Map(model.wonders.map((site) => [site.data.id, site]));
  const on = { wonders, ...Object.fromEntries(TOGGLES.map((t) => [t.id, !!transport && t.def])) };
  const layers = makeLayers(model, on, { tips, app }).filter((layer) => (wonders && ["wonders", "plates"].includes(layer.id)) || (transport && ["roads", "rail", "hubs"].includes(layer.id)));
  const glyphs = layers.find((layer) => layer.id === "wonders");
  if (wonders) {
    glyphs.z = app.layerZ.RESOURCES + 1;
    layers.find((layer) => layer.id === "plates").z = app.layerZ.LABELS + 1;
  }

  function open(site, fly = false) {
    const { data } = site;
    const protectedSites = protection.filter((record) => (record.wonder === data.id || record.id === data.metrics?.protected_id) && record.x != null);
    app.clearSelection();
    showPanel({
      kind: "wonder",
      title: data.name,
      stripe: data.kind === "natural" ? "#8fd07a" : "#ecc46a",
      sub: esc(data.location),
      headExtra: `<p class="wonder-description">${esc(data.description)}</p>${data.period ? "" : `<p class="cp-full">${esc(data.era)}</p>`}`,
      sections: [{ title: "Wonder selection", html: `<p>${wonderFactsHtml(data, app.data)}</p>` }, ...(protectedSites.length ? [{
        title: "Associated protected land",
        html: protectedSites.map((r, i) => `<p><a href="#" data-protected-site="${i}">${esc(r.name)}</a></p>`).join(""),
      }] : [])],
      wire(panel) {
        panel.querySelectorAll("[data-protected-site]").forEach((link) => {
          link.onclick = (event) => {
            event.preventDefault();
            const record = protectedSites[+link.dataset.protectedSite];
            app.setLens(null);
            app.ui.setMapToggle("protected", true);
            const cell = record.cells?.[0];
            const point = cell == null ? [record.x, record.y] : [app.w.grid.cx(cell), app.w.grid.cy(cell)];
            app.clearSelection();
            app.flyTo(...point, 5);
          };
        });
      },
      onClose: app.clearSelection,
      onPedia: app.pedia.open,
      pediaRoute: `wonder/${data.id}`,
      pediaLink: app.pediaLink,
    });
    if (fly) app.flyTo(site.x, site.y, 4.5);
    app.requestDraw();
  }

  if (glyphs) glyphs.click = (site) => {
    open(site);
    return true;
  };
  app.openWonder = (id) => {
    const site = byId.get(id);
    if (!site) return;
    app.ui.setMapToggle("wonders", true);
    open(site, true);
  };
  if (transport?.trade) layers.push(indiaTradeLayer(app));
  for (const l of layers) app.registerStaticLayer(l);
  if (wonders) app.ui.addMapToggle({
    id: "wonders", label: "Wonders", icon: "w-landmark",
    title: "Built landmarks and natural wonders (W)", default: true,
    get: () => on.wonders,
    set: (v) => {
      on.wonders = !!v;
      if (!v && app.panels.element.dataset.kind === "wonder") app.clearSelection();
      app.requestDraw();
    },
  });
  for (const t of transport ? TOGGLES : []) {
    app.ui.addMapToggle({
      id: t.id, label: t.label, icon: t.icon, title: t.title, default: t.def,
      get: () => on[t.id],
      set: (v) => {
        on[t.id] = !!v;
        app.requestDraw();
      },
    });
  }

  app.mapArt = { model, on, layers };
  app.requestDraw();
}
