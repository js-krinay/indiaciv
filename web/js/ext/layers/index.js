// Map-art extension: tile improvements (Interstates and major highways, railroads, ports, airports),
// wonders and protected land, and freight trade routes, each as a static layer
// drawn into the cached map (nothing animates; an idle map draws no frames), with a switch in the "Map" menu.
//
// Data: infrastructure.json, wonders.json and trade.json (loaded eagerly by main.js right after the
// first frame; app.loadData returns the same promise). A missing file (null) leaves its layers off and their switches
// harmless. Defaults: roads, rail, ports & airports and wonders on (roads, rail and hubs only from the region
// view in: see each layer's minRpx), trade routes off.
import { createModel } from "./model.js";
import { makeLayers } from "./layers.js";
import { tips } from "./tips.js";

const TOGGLES = [
  { id: "roads", label: "Highways", icon: "t-road", def: true, title: "Open expressways and national highways · OpenStreetMap", layers: ["roads"] },
  { id: "rail", label: "Railways", icon: "t-rail", def: true, title: "Active main and secondary rail lines · OpenStreetMap", layers: ["rail"] },
  { id: "hubs", label: "Ports & airports", icon: "d-harbor", def: true, title: "Major ports and scheduled-service airports", layers: ["hubs"] },
  { id: "wonders", label: "Wonders", icon: "w-landmark", def: true, title: "Built landmarks and natural wonders", layers: ["wonders", "protected", "plates"] },
  { id: "trade", label: "Trade", icon: "t-trade", def: false, title: "Dedicated Freight Corridors and single-port coastal cargo", layers: ["trade"] },
];

export function install(app) {
  const model = createModel(app.w);
  const on = Object.fromEntries(TOGGLES.map((t) => [t.id, t.def]));
  model.data.sources = app.data.sources;
  const layers = makeLayers(model, on, { tips, app });
  for (const l of layers) app.registerStaticLayer(l);

  for (const t of TOGGLES) {
    app.ui.addMapToggle({
      id: t.id, label: t.label, icon: t.icon, title: t.title, default: t.def,
      get: () => on[t.id],
      set: (v) => {
        on[t.id] = !!v;
        app.requestDraw();
      },
    });
  }

  const apply = (name, data) => {
    model.setData(name, data);
    app.requestDraw();
  };
  for (const name of ["infrastructure", "wonders", "trade"]) {
    if (app.data[name] !== undefined) apply(name, app.data[name]);
    else app.loadData(name).then((d) => apply(name, d), (err) => console.warn(`map layers: ${name} failed to load`, err));
  }

  // For debugging and the gallery: the model and switches.
  app.mapArt = { model, on, layers };
}
