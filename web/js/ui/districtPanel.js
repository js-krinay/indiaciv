import { css } from "../color.js";
import { esc, int } from "../format.js";
import { showPanel } from "./infoPanel.js";
import { formatLensValue } from "./lenses.js";

export function openDistrictPanel(idx, ctx) {
  const { w, places, sources } = ctx;
  const district = w.raw.counties[idx];
  const record = places?.counties?.[district.geoid] || {};
  const owner = w.raw.states.findIndex((state) => state.abbr === record.state);
  const state = w.raw.states[owner];
  const sourceNames = (ids) => [...new Set([ids].flat().filter(Boolean)
    .map((id) => sources.find((source) => source.id === id)?.publisher).filter(Boolean))].join(" · ");
  const fact = (label, value, detail) => `<div class="district-fact">
    <span>${esc(label)}</span><strong>${value == null ? "—" : esc(value)}</strong>
    ${detail ? `<small class="muted">${esc(detail)}</small>` : ""}
  </div>`;
  const detail = (period, estimated, source) => [period, estimated && "IndiaCiv estimate", source].filter(Boolean).join(" · ");
  const population = record.provenance?.population;
  const metrics = [
    fact("Population", record.population == null ? null : int(record.population),
      detail(population?.period, population?.estimated, sourceNames(population?.source))),
    ...ctx.metricLenses.filter((lens) => Object.hasOwn(record, lens.id)).map((lens) => {
      const meta = record.provenance?.[lens.id] || lens;
      const label = lens.id === "density" ? "Population density" : lens.name.replace(/, [^,]*2026$/, "");
      const value = record[lens.id];
      return fact(label, value == null ? null : formatLensValue(lens, value),
        detail(meta.period, meta.estimated, lens.share_credit || sourceNames(meta.source)));
    }),
  ].join("");
  const list = (values, empty, item) => values.length
    ? `<ul class="district-sites">${values.map((value) => `<li>${item(value)}</li>`).join("")}</ul>`
    : `<p class="muted">${empty}</p>`;
  const cities = (record.sites?.cities || []).map((id) => ctx.cityById.get(id)).filter(Boolean);
  const wonders = (record.sites?.wonders || []).map((id) => ctx.wonders.find((w) => w.id === id)).filter(Boolean);
  const resources = (record.sites?.resources || []).map((i) => ctx.resources?.items[i]).filter(Boolean);
  const resourceNames = new Map(ctx.resources?.types.map((type) => [type.id, type.name]));
  showPanel({
    kind: "district",
    stripe: css(w.stateColor[owner] || [190, 190, 190]),
    title: district.name,
    sub: state ? `<a href="#state=${esc(state.abbr)}" data-district-state>${esc(state.name)} ›</a>` : "",
    headExtra: ctx.approximate ? '<p class="cp-full">Nearest mapped district for this tile</p>' : "",
    sections: [
      ctx.terrainLinks(ctx.cell).length ? { title: "Tile terrain", html: ctx.terrainLinks(ctx.cell).join(" · ") } : null,
      { title: "2026 district figures", html: metrics },
      { title: "Cities", html: list(cities, "No mapped cities.", (city) =>
        `<button type="button" data-city="${esc(city.id)}">${esc(city.name)}</button> ${ctx.pediaLink(`city/${city.id}`, "Almanac")}`) },
      { title: "Wonders", html: list(wonders, "No mapped wonders.", (wonder) =>
        `<button type="button" data-wonder="${esc(wonder.id)}">${esc(wonder.name)}</button> ${ctx.pediaLink(`wonder/${wonder.id}`, "Almanac")}`) },
      { title: "Resources", html: list(resources, "No mapped resources.", (resource) =>
        ctx.pediaLink(`resource/${resource.type}`, resource.name || resourceNames.get(resource.type) || resource.type)
          || esc(resource.name || resource.type)) },
    ],
    foot: ctx.onCompare ? '<a href="#advisor=explorer" data-district-compare>Compare in Explorer ›</a> · ' : "",
    onClose: ctx.onClose,
    onPedia: ctx.onPedia,
    pediaRoute: state ? `state/${state.abbr}` : "source/index",
    pediaLink: ctx.pediaLink,
    wire(panel) {
      panel.querySelector("[data-district-state]")?.addEventListener("click", (event) => {
        event.preventDefault();
        ctx.onState(owner);
      });
      panel.querySelector("[data-district-compare]")?.addEventListener("click", (event) => {
        event.preventDefault();
        ctx.onCompare(district.geoid);
      });
      panel.querySelectorAll("[data-city]").forEach((button) => {
        button.onclick = () => ctx.onCity(ctx.cityById.get(button.dataset.city));
      });
      panel.querySelectorAll("[data-wonder]").forEach((button) => {
        button.onclick = () => ctx.onWonder(button.dataset.wonder);
      });
    },
  });
}
