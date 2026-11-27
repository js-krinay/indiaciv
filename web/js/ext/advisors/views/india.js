import { barList, stackedBars } from "../core/charts.js";
import { fieldContext, PORT_CARGO, rowsHighlight } from "../core/data.js";
import { fmtValue } from "../core/fmt.js";
import { focusPoint } from "../core/frame.js";
import { section, sourcesHtml, topBy } from "../core/view.js";
import { esc } from "../core/util.js";
import { disasterDate, disasterEvent } from "../../disasterEvents.js";
import { indianNumber } from "../../../ui/cityHeadlines.js";

const CHARTS = {
  economy: [
    ["metros", "gdp"], ["metros", "gdp_rank"], ["metros", "economic_growth"], ["metros", "population"],
    ["states", "gsva_industry_share"], ["metros", "gdp_industry"], ["metros", "gdp_services"],
    ["metros", "gdp_agriculture"], ["metros", "state_urban_unemployment_15_plus"],
    ["states", "industry_agriculture_share"], ["states", "industry_secondary_share"], ["states", "industry_tertiary_share"],
    ["states", "gsdp_pc"], ["metros", "employed_all_ages"], ["metros", "sector_services_workers"],
    ["metros", "sector_industry_workers"], ["metros", "sector_agriculture_workers"],
  ],
  people: [
    ["states", "population"], ["metros", "population"], ["states", "density"], ["states", "projected_growth"],
    ["states", "age_0_14"], ["states", "age_60"], ["states", "median_age"],
  ],
  prosperity: [
    ["states", "rural_tap_water"], ["states", "public_works_daily_wage"],
    ["states", "unemployment"], ["metros", "state_urban_unemployment_15_plus"],
    ["states", "pmayg_completions"], ["states", "pmayu2_completions"],
    ["states", "pmjay_cards"], ["states", "abha_ids"],
  ],
  land: [
    ["states", "yield_food"], ["states", "agri_worker_share"], ["states", "protected_share"],
    ["counties", "protected_share"], ["states", "area_km2"], ["counties", "density"], ["counties", "district_pm25"],
  ],
  energy: [
    ["states", "energy_mw"], ["states", "electricity_pc"], ["states", "mines_count"], ["states", "oil_gas_count"],
    ["states", "resource_pumped_storage_count"], ["states", "resource_battery_count"],
    ["states", "resource_oil_count"], ["states", "resource_gas_count"],
  ],
  commerce: [["states", "trade_gateway_count"], ["metros", "trade_gateway_count"], ["states", "port_count"], ["states", "airport_count"], ["states", "rail_links"]],
  culture: [["states", "wonders_count"], ["states", "landmark_count"], ["states", "natural_wonders_count"],
    ["states", "park_wonders_count"], ["states", "research_wonders_count"]],
  knowledge: [["states", "science_points"], ["metros", "science_points"], ["states", "population"],
    ["states", "employed"], ["states", "internet_per_100"]],
  military: [["states", "registered_veterans"], ["states", "veteran_share"],
    ["counties", "veteran_share"], ["states", "cantonment_boards"]],
};

const PROSPERITY_RATES = new Set(["pmayg_completions", "pmayu2_completions", "pmjay_cards", "abha_ids"]);

const NOTES = {
  people: ["Seven smaller North-East states share one age projection. WorldPop supplies ages for Goa and five union territories."],
  prosperity: ["City unemployment benchmarks use the urban labour force in the states covered by each footprint."],
  land: ["Forest and cropland shares have no validated 2026 land-cover estimate. The foodgrain estimate uses mapped cropland only as an allocation input."],
  energy: ["The power chart covers mapped operating sites above the inventory’s technology thresholds."],
  commerce: ["Zonal rail loading and major-port cargo use different reporting geographies."],
  culture: ["Charts count the atlas’s selected built and natural wonders."],
  military: ["State and UT estimates cover comparable registration areas. Himachal Pradesh district rates use reported registrations."],
};

function placeChart(ctx, level, field, sources) {
  const { data, el, link } = ctx;
  const entries = topBy(level.rows, (r) => r.v[field.key], {
    n: 12, asc: field.key.includes("unemployment") || field.key.endsWith("_rank"),
  });
  if (!entries.length) return null;
  const metas = entries.map(({ r }) => level.meta(field, r));
  for (const meta of metas) sources.push(...[meta.source].flat());
  const periods = [...new Set(metas.map((m) => m.period))];
  const descriptions = [...new Set(metas.map((m) => m.description))];
  const host = section(el, { title: field.label, note: esc([level.label, ...periods, field.unit,
    descriptions.length === 1 ? descriptions[0] : field.description].filter(Boolean).join(" · ")) });
  const chart = barList(host, {
    rows: entries.map(({ r, v }, i) => ({
      key: r.key, label: r.name, value: v, place: r,
      sub: PROSPERITY_RATES.has(field.key) && Number.isFinite(r.v.population)
        ? `${indianNumber(r.v.population)} projected residents · 1 Mar 2026`
        : field.key === "trade_gateway_count" ? r.v.trade_gateways : r.sub,
      text: (metas[i].estimated ? "≈" : "") + fmtValue(field.format, v, field.unit),
    })),
    rank: true, diverging: entries.some(({ v }) => v < 0),
    onHover: (r) => link.hover(r && rowsHighlight(level, [r.place])),
    onClick: ({ place }) => {
      ctx.keepCamera();
      link.base(rowsHighlight(level, [place]));
      level.focus(place);
    },
  });
  for (const b of chart.el.querySelectorAll("[data-key]")) {
    const row = level.byKey.get(b.dataset.key);
    b.title += " · " + fieldContext(data, level, field, row);
  }
  const explore = document.createElement("button");
  explore.className = "adv-mini";
  explore.type = "button";
  explore.textContent = `Explore ${level.label.toLowerCase()}`;
  explore.addEventListener("click", () => ctx.switchTo("explorer", { level: level.id, field: field.key === "trade_gateway_count" ? "trade_gateways" : field.key }));
  host.appendChild(explore);
  return { chart, level };
}

function inventoryCharts(ctx, sources) {
  const { data, el, app, link } = ctx;
  if (ctx.advisor.id === "land") {
    const level = data.levels.states;
    const field = level.field("crop_presence");
    const rows = level.rows.filter((row) => row.v.crop_presence);
    if (rows.length) {
      const host = section(el, { title: "Documented growing areas", note: field.description });
      const picker = document.createElement("select");
      picker.setAttribute("aria-label", "State or UT growing areas");
      picker.innerHTML = rows.map((row) => `<option value="${esc(row.key)}">${esc(row.name)}</option>`).join("");
      const detail = document.createElement("p");
      detail.className = "adv-note";
      const showCrops = () => {
        const row = level.byKey.get(picker.value);
        detail.textContent = `${row.v.crop_presence} · ${fieldContext(data, level, field, row)}`;
      };
      picker.addEventListener("change", showCrops);
      host.append(picker, detail);
      showCrops();
      for (const row of rows) sources.push(...[level.meta(field, row).source].flat());
    }
  }
  if (ctx.advisor.id === "energy") {
    const types = data.resourceTypes.filter((type) => ["energy", "mineral"].includes(type.category));
    if (types.length) {
      const host = section(el, { title: "Inventory inclusion thresholds" });
      const list = document.createElement("dl");
      list.innerHTML = types.map((type) => `<dt><strong>${esc(type.name)}</strong></dt>
        <dd>${esc(type.source === "gem_oil_gas" || type.unit == null ? type.description : type.threshold)}</dd>`).join("");
      host.append(list);
      sources.push(...types.map((type) => type.source));
    }
    const level = data.levels.states;
    const fields = level.fields.filter((f) => f.key.startsWith("resource_") && f.key.endsWith("_mw"));
    const rows = fields.map((f) => {
      const values = level.rows.map((r) => r.v[f.key]).filter(Number.isFinite);
      const value = values.reduce((sum, v) => sum + v, 0);
      return { key: f.key, label: f.label, sub: f.period, value, text: fmtValue("mw", value), source: f.source };
    }).filter((r) => r.value > 0).sort((a, b) => b.value - a.value);
    if (rows.length) {
      sources.push(...rows.map((r) => r.source));
      barList(section(el, { title: "Mapped capacity by technology" }), {
        rows, onClick: (r) => ctx.switchTo("explorer", { level: "states", field: r.key }),
      });
    }
  }
  if (ctx.advisor.id === "commerce") {
    const ports = data.portCargo;
    if (ports.length) {
      sources.push(...ports.map((p) => p.source));
      const periods = [...new Set(ports.map((p) => p.period))];
      const statuses = [...new Set(ports.map((p) => p.status))];
      const host = section(el, { title: PORT_CARGO.label,
        note: esc([...periods, PORT_CARGO.unit, ...statuses].filter(Boolean).join(" · ")) });
      barList(host, {
        rows: [...ports].sort((a, b) => b.value - a.value).map((p) => ({
          ...p,
          text: fmtValue(PORT_CARGO.format, p.value),
        })),
        rank: true, onHover: (r) => link.hover(r ? { cells: new Set([r.place.cell]), label: r.label } : null),
        onClick: (r) => { ctx.keepCamera(); focusPoint(app, r.place.x, r.place.y, 2); },
      });
    }
    const split = data.infrastructure?.port_split;
    if (split && ports.length) {
      sources.push(split.source_id);
      const share = (value) => fmtValue("pct", value);
      const host = section(el, { title: "Overseas and coastal port cargo",
        note: esc(`${split.label} · ${split.status} · Ministry of Ports, Shipping and Waterways`) });
      host.classList.add("adv-port-split");
      const summary = document.createElement("p");
      summary.className = "adv-note";
      summary.textContent = `All 12 authorities · ${share(split.foreign)} overseas · ${share(split.domestic)} coastal`;
      host.append(summary);
      stackedBars(host, {
        keys: [
          { key: "foreign", label: "Overseas", color: "#65b9c8" },
          { key: "domestic", label: "Coastal", color: "#e4b465" },
        ],
        rows: ports.map((p) => {
          const { foreign, domestic } = p.place.cargo;
          return { ...p, parts: { foreign, domestic }, text: `${share(foreign)} / ${share(domestic)}` };
        }),
        normalize: true, fmt: share,
        onHover: (hit) => link.hover(hit ? { cells: new Set([hit.row.place.cell]), label: hit.row.label } : null),
        onClick: ({ row }) => { ctx.keepCamera(); focusPoint(app, row.place.x, row.place.y, 2); },
      });
    }
    const rail = data.infrastructure?.freight;
    if (rail?.rows.length) {
      sources.push(rail.source_id);
      const rows = rail.rows.map(([key, label, value]) => ({ key, label, value, text: value.toFixed(2) }))
        .sort((a, b) => b.value - a.value);
      const host = section(el, { title: "Rail freight loading by zone", note: esc(`${rail.label} · ${rail.unit} · Ministry of Railways via Press Information Bureau`) });
      barList(host, { rows, rank: true, static: true });
    }
  }
  if (ctx.advisor.id === "culture" && data.sites.wonders?.length) {
    const host = section(el, { title: "Find a wonder", note: "Select a landmark or natural feature to fly to it." });
    const select = document.createElement("select");
    select.setAttribute("aria-label", "Find a wonder");
    const wonders = [...data.sites.wonders].sort((a, b) => a.name.localeCompare(b.name));
    select.innerHTML = `<option value="">Choose a wonder</option>${wonders.map((w, i) =>
      `<option value="${i}">${esc(w.name)}</option>`).join("")}`;
    const note = document.createElement("p");
    note.className = "adv-note";
    select.addEventListener("change", () => {
      const w = select.value === "" ? null : wonders[Number(select.value)];
      note.textContent = w?.description || "";
      if (!w) return;
      ctx.keepCamera();
      link.base({ cells: new Set(w.cells || [w.cell]), label: w.name });
      focusPoint(app, w.draw_x ?? w.x, w.draw_y ?? w.y, 2);
    });
    host.append(select, note);
    sources.push(data.levels.states.field("wonders_count").source);
    const classes = new Map();
    for (const wonder of wonders.filter((row) => row.rule === "research_inventory")) {
      classes.set(wonder.metrics.institution_class, wonder.metrics.institution_count);
      sources.push(...wonder.sources);
    }
    if (classes.size) {
      const inventory = section(el, { title: "Mapped research wonders",
        note: "IISc, IITs and IISERs with verified locations in the 27 November 2026 Science inventory." });
      const counts = document.createElement("p");
      counts.textContent = [...classes].sort(([a], [b]) => a.localeCompare(b)).map(([kind, count]) => `${kind} ${count}`).join(" · ");
      inventory.append(counts);
    }
  }
  if (ctx.advisor.id === "culture" && app.data.lenses?.disasters?.events.length) {
    const { period, coverage, events } = app.data.lenses.disasters;
    const host = section(el, { title: "Disasters", note: esc(`${period} · ${coverage}`) });
    const select = document.createElement("select");
    select.setAttribute("aria-label", "Hazard type");
    const types = [...new Set(events.map((event) => event.type))].sort();
    select.innerHTML = `<option value="">All documented events</option>${types.map((type) =>
      `<option value="${esc(type)}">${esc(type)}</option>`).join("")}`;
    const list = document.createElement("div");
    const districts = new Map(app.data.world.counties.map(({ geoid, name }) => [geoid, name]));
    const states = new Map(app.data.world.states.map(({ abbr, name }) => [abbr, name]));
    const geography = document.createElement("select");
    geography.setAttribute("aria-label", "Hazard state or territory");
    const covered = new Set(events.flatMap((event) => event.states));
    geography.innerHTML = `<option value="">All reported areas</option>${[...states].filter(([id]) => covered.has(id))
      .map(([id, name]) => `<option value="${esc(id)}">${esc(name)}</option>`).join("")}`;
    const update = () => {
      const matches = events.filter((event) => (!select.value || event.type === select.value)
        && (!geography.value || event.states.includes(geography.value)));
      const dateOf = (event) => event.end_date || event.start_date || event.reported_on;
      const latest = matches.reduce((best, event) => !best || dateOf(event) > dateOf(best) ? event : best, null);
      const summary = latest
        ? `<p class="adv-note">${matches.length} documented ${matches.length === 1 ? "event" : "events"} · ${latest.start_date ? "Latest event" : "Latest report"}
          ${disasterDate(dateOf(latest))}</p>` : "";
      list.innerHTML = matches.length
        ? summary + matches.map((event) => disasterEvent(event, districts, states)).join("")
        : '<p class="adv-note">No matching documented events.</p>';
    };
    const lens = document.createElement("button");
    lens.className = "adv-mini";
    lens.type = "button";
    lens.textContent = "Show district counts on map";
    lens.addEventListener("click", () => ctx.setLens(`disasters_district_${select.value.toLowerCase() || "all"}`));
    select.addEventListener("change", update);
    geography.addEventListener("change", update);
    host.append(select, geography, lens, list);
    update();
    sources.push("india_disasters_2026");
  }
}

function nationalCharts(ctx, sources) {
  const { data, advisor, el } = ctx;
  const stats = data.nationalStatistics;
  if (!stats) return;
  function bars(title, note, values, format) {
    barList(section(el, { title, note: esc(note) }), {
      static: true, rows: Object.entries(values).map(([label, value]) => ({
        key: label, label, value, text: format(value),
      })),
    });
  }
  function summary(title, value, note) {
    const host = section(el, { title, note: esc(note) });
    const item = document.createElement("strong");
    item.textContent = value;
    host.appendChild(item);
  }
  if (advisor.id === "military") {
    const { defence_budget: budget, sainik_schools: schools, veterans } = stats;
    const currency = (value) => `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} crore`;
    summary("Union defence allocation", currency(budget.total), `${budget.period} · Budget Estimate`);
    bars("Allocation by budget head", `${budget.period} · Budget Estimate`, budget.heads, currency);
    summary("Listed cantonment boards", fmtValue("int", stats.cantonment_boards),
      "Directorate General Defence Estates · Civic directory checked 27 Nov 2026");
    if (stats.civic_offices?.length) {
      const host = section(el, { title: "Find a public board office",
        note: `${stats.civic_offices.length} mapped public offices · © OpenStreetMap contributors · ODbL 1.0` });
      const focus = (office) => {
        ctx.keepCamera();
        focusPoint(ctx.app, office.x, office.y, 2);
      };
      const points = ctx.bubbles("public-offices", { rMax: 7, alpha: 0.9, onClick: focus,
        tip: (office) => esc(office.name) });
      points.set(stats.civic_offices.map((office) => ({
        ...office, key: office.name, color: ctx.advisor.color, value: 1,
      })));
      for (const office of stats.civic_offices) {
        const button = document.createElement("button");
        button.className = "adv-mini";
        button.type = "button";
        button.textContent = office.name;
        button.addEventListener("click", () => focus(office));
        host.appendChild(button);
      }
      sources.push("civic_office_points");
    }
    summary("New partnership Sainik Schools", fmtValue("int", schools.value),
      `Affiliated and operational · ${schools.period}`);
    summary("Registered ex-servicemen in covered areas", `≈${fmtValue("int", veterans.value)}`,
      `IndiaCiv estimate · ${veterans.period} · ${veterans.coverage} states and UTs · ${veterans.description}`);
    sources.push(budget.source, schools.source, "cantonment_boards", ...veterans.source);
    const perResident = stats.defence_budget_per_resident;
    if (perResident) {
      summary("Union defence allocation per resident", `≈${fmtValue("inr", Math.round(perResident.value))}`,
        `IndiaCiv estimate · ${perResident.period} · Population projected for ${perResident.denominator_period}`);
      sources.push(...perResident.source);
    }
    const gdp = stats.defence_budget_share_gdp;
    if (gdp) {
      summary("Union defence allocation as a share of GDP", `≈${(100 * gdp.value).toFixed(2)}%`,
        `IndiaCiv estimate · ${gdp.period} · Provisional nominal GDP`);
      sources.push(...gdp.source);
    }
    const grant = stats.veteran_penury_grant;
    if (grant) {
      summary("Veteran penury grant", `${fmtValue("inr", grant.value)} per month`,
        `Notified rate per eligible beneficiary · ${grant.period}`);
      sources.push(grant.source);
    }
  }
  if (advisor.id === "knowledge") {
    const level = data.levels.states;
    const counts = level.fields.filter((field) => field.key.startsWith("science_") && field.key !== "science_points");
    if (counts.length) {
      bars("Research institutions by class", counts[0].period,
        Object.fromEntries(counts.map((field) => [field.label,
          level.rows.reduce((total, row) => total + (row.v[field.key] ?? 0), 0)])), (value) => fmtValue("int", value));
      sources.push(...counts[0].source);
    }
  }
  if (advisor.id === "prosperity") {
    const { poverty_nowcast: poverty, pmjay_cards: cards } = stats;
    const denominator = data.nationalPopulation;
    const denominatorText = Number.isFinite(denominator)
      ? `${indianNumber(denominator)} residents projected for 1 March 2026`
      : "population projected for 1 March 2026";
    if (Number.isFinite(denominator)) sources.push("tg_projections");
    if (poverty) {
      summary("India poverty nowcast", `${(100 * poverty.value).toFixed(3)}%`,
        `${poverty.line} · Calendar ${poverty.period} · World Bank estimate, ${poverty.vintage} vintage`);
      sources.push(poverty.source);
    }
    if (cards) {
      const lowerBound = Math.floor(cards.value * 10) / 10;
      summary("PM-JAY cards issued in India", `≥${lowerBound.toFixed(1)} cards per 100 residents`,
        `${cards.period} · Cumulative cards · IndiaCiv estimate using ${denominatorText}`);
      sources.push(...cards.source);
    }
    for (const key of ["pmayg_completions", "pmayu2_completions", "abha_ids"]) {
      const field = data.levels.states.field(key);
      const record = data.nationalMetrics?.[key];
      if (!field || !record) continue;
      summary(`${field.label} in India`, `≈${fmtValue(field.format, record.value)} ${field.unit}`,
        `${field.period} · Cumulative · IndiaCiv estimate using ${denominatorText}`);
      sources.push(...[field.source].flat());
    }
  }
  if (advisor.id === "economy" && stats.industry) {
    const fields = ["industry_agriculture_share", "industry_secondary_share", "industry_tertiary_share"]
      .map((key) => data.levels.states.field(key));
    bars("Employment by broad industry in India", `${fields[0].period} · PLFS workers age 15+`,
      Object.fromEntries(fields.map((field, index) => [field.label, stats.industry[index] / 100])),
      (value) => fmtValue("pct", value));
    sources.push(fields[0].source);
  }
}

function researchByClass(ctx, sources) {
  const level = ctx.data.levels.states;
  const fields = level.fields.filter((field) => field.key.startsWith("science_") && field.key !== "science_points");
  if (!fields.length) return [];
  const host = section(ctx.el, { title: "Compare places by institution class" });
  const select = document.createElement("select");
  select.setAttribute("aria-label", "Institution class");
  select.innerHTML = fields.map((field) => `<option value="${field.key}">${esc(field.label)}</option>`).join("");
  const content = document.createElement("div");
  host.append(select, content);
  const charts = [];
  const render = () => {
    content.replaceChildren();
    charts.splice(0);
    for (const id of ["states", "metros"]) {
      const placeLevel = ctx.data.levels[id];
      const chart = placeChart({ ...ctx, el: content }, placeLevel, placeLevel.field(select.value), []);
      if (chart) charts.push(chart);
    }
  };
  select.addEventListener("change", render);
  render();
  sources.push(...fields[0].source);
  return charts;
}

export function mount(ctx) {
  const { advisor, data, el } = ctx;
  const sources = [];
  nationalCharts(ctx, sources);
  inventoryCharts(ctx, sources);
  const charts = CHARTS[advisor.id].flatMap(([id, key]) => {
    const level = data.levels[id];
    const field = level.field(key);
    const chart = field && placeChart(ctx, level, field, sources);
    return chart ? [chart] : [];
  });
  const researchCharts = advisor.id === "knowledge" ? researchByClass(ctx, sources) : [];
  el.insertAdjacentHTML("beforeend", sourcesHtml(data, sources, [
    ...(NOTES[advisor.id] || []), "≈ marks an IndiaCiv estimate.",
  ]));
  return {
    onMapHover(h) {
      for (const { level, chart } of [...charts, ...researchCharts]) chart.setHot(level.rowAtCell(h?.cell)?.key ?? null);
    },
  };
}
