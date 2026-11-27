import { esc, int, popShort, compact, periodLabel } from "../format.js";
import { formatLensValue } from "./lenses.js";
import { glyph } from "./icon.js";
import { FOREIGN } from "../world.js";
import { cityHeadlineStats, indianNumber, workforceSource } from "./cityHeadlines.js";

const el = () => document.getElementById("tooltip");

const nameOf = (table, id) => table.find((t) => t.id === id)?.name;

export function showCellTooltip(mx, my, w, i, lens, showResources = true, resourceFilter = null, sources = new Map()) {
  const raw = w.raw;
  const lines = [];
  const city = w.cityByCell.get(i);
  if (city) {
    const population = city.provenance?.population;
    const period = population?.vintage === "older" ? periodLabel(population, " · ") : " projected for 2026";
    lines.push(`<b>${esc(city.name)}</b> <span class="muted">· ${popShort(city.population)} people${period}</span>`);
  }

  const wt = w.water[i];
  if (wt) {
    const depth = raw.elev[i] < 0 ? ` <span class="muted">· ${int(-raw.elev[i])} m deep</span>` : "";
    lines.push(`<b>${esc(nameOf(w.tables.water, wt) || "Water")}</b>${depth}`);
  } else {
    const cover = w.base?.[i] ? nameOf(w.tables.base, w.base[i]) :
      w.cover[i] > 0 ? nameOf(w.tables.cover, w.cover[i]) : null;
    const relief = w.relief[i] > 0 ? nameOf(w.tables.relief, w.relief[i]) : null;
    const terrain = [cover, relief].filter(Boolean).join(" · ") || (relief ?? "Land");
    lines.push(`<b>${esc(terrain)}</b> <span class="muted">· ${int(raw.elev[i])} m</span>`);
  }
  const features = (w.features?.[i] || []).map((id) => nameOf(w.tables.features, id)).filter(Boolean);
  if (features.length) lines.push(`<span class="muted">${esc(features.join(" · "))}</span>`);
  const o = raw.owner[i];
  if (o >= 0) {
    const county = raw.county[i] >= 0 ? raw.counties[raw.county[i]].name + ", " : "";
    lines.push(`${esc(county)}${esc(raw.states[o].name)}`);
    if (lens) {
      const details = lens.values[i] == null ? null : lens.cell_details?.[i] || lens.state_details?.[o];
      const periodMeta = details?.period ? details : lens;
      const period = lens.name.endsWith(` · ${periodMeta.period}`) ? "" : periodLabel(periodMeta, " · ");
      const estimate = details?.estimated ? " · IndiaCiv estimate" : "";
      const coverage = details?.coverage ? ` · ${esc(details.coverage)}` : "";
      lines.push(`${glyph(lens, 13)} ${esc(lens.name)}: <b>${formatLensValue(lens, lens.values[i])}</b>${estimate}${coverage}${period}`);
    }
  } else if (o === FOREIGN) {
    lines.push(`<span class="muted">Beyond the borders (not mapped)</span>`);
  }
  const items = showResources && w.resources?.byCell.get(i);
  const res = items && resourceFilter ? items.filter(resourceFilter) : items;
  if (res) {
    for (const it of res.slice(0, 4)) {
      const t = w.resources.typeById.get(it.type);
      if (it.period) {
        lines.push(resourceDetail(w, t, it, sources));
        continue;
      }
      const num = it.value == null ? "" : t.unit === "Mt/yr"
        ? it.value.toLocaleString("en-US", { maximumFractionDigits: 3 })
        : Math.abs(it.value) < 1e6 ? int(it.value) : compact(it.value);
      const val = num ? ` · ${num}${t.unit ? " " + esc(t.unit) : ""}` : "";
      const kind = it.name && it.name !== t.name ? ` <span class="muted">· ${esc(t.name)}${val}</span>` : `<span class="muted">${val}</span>`;
      lines.push(`<span style="color:${esc(t.color || "#efe4c6")}">${glyph(t, 13)}</span> ${esc(it.name || t.name)}${kind}`);
    }
    if (res.length > 4) lines.push(`<span class="muted">+${res.length - 4} more</span>`);
  }
  if (city) lines.push(`<span class="muted">Click to open the city</span>`);
  else if (o >= 0) lines.push(`<span class="muted">Click to open ${esc(raw.states[o].name)}</span>`);
  show(mx, my, lines.join("<br>"));
}

export function showResourceTooltip(mx, my, w, item, sources) {
  show(mx, my, resourceDetail(w, w.resources.typeById.get(item.type), item, sources));
}

function resourceDetail(w, type, item, sources) {
  const name = item.name ? ` · ${esc(item.name)}` : "";
  const status = item.estimated ? "IndiaCiv estimate · " : "";
  const state = w.raw.states.find((row) => row.abbr === item.state)?.name;
  const local = w.resources.summary?.states?.[item.state]?.[item.type];
  const national = w.resources.summary?.national?.[item.type];
  const context = [
    state && local ? `${state} · ${local.count} mapped statewide` : state,
    type.threshold ? `Eligibility · ${type.threshold}` : "",
    national ? `${national.count} mapped nationally` : "",
  ].filter(Boolean).map((line) => `${esc(line)}<br>`).join("");
  const value = Number.isFinite(item.value) && type.unit !== "field"
    ? `${esc(item.value.toLocaleString("en-IN"))} ${esc(type.unit)}<br>` : "";
  return `${glyph(type, 16)} <b>${esc(type.name)}${name}</b><br>${esc(status + item.detail)}<br>${value}${context}` +
    `<span class="muted">${periodLabel(item)} · ${esc(sources.get(item.source) || item.source)}</span>`;
}

/**
 * A tooltip with ready-made content: a string is HTML (escape any data yourself with format.js esc), {text} is
 * plain text. Used for registered static layers' tooltip(item).
 */
export function showHtmlTooltip(mx, my, content) {
  if (content == null || content === "") return hideTooltip();
  const html = typeof content === "string" ? content : esc(content.text ?? "");
  show(mx, my, html);
}

export function showCityTooltip(mx, my, city, gold) {
  const stats = cityHeadlineStats(city, gold).filter((row) => row.key !== "gdp_per_capita");
  const work = city.resident_workforce;
  if (Number.isFinite(work?.employed_all_ages)) {
    stats.push({ label: "Employed residents", text: indianNumber(work.employed_all_ages), source: workforceSource(work) });
  }
  show(mx, my, `<b>${esc(city.full)}</b>${stats.map((row) =>
    `<br>${esc(row.label)} · ${esc(row.text)}<br><span class="muted">${periodLabel(row.periodMeta) || esc(row.source)}</span>`).join("")}
    <br><span class="muted">Click to open the city</span>`);
}

function show(mx, my, html) {
  const t = el();
  t.innerHTML = html;
  t.hidden = false;
  const r = t.getBoundingClientRect();
  t.style.left = Math.max(4, Math.min(window.innerWidth - r.width - 8, mx + 16)) + "px";
  t.style.top = Math.max(4, Math.min(window.innerHeight - r.height - 8, my + 16)) + "px";
}

export function hideTooltip() {
  el().hidden = true;
}
