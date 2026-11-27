import { esc, pct, yieldDetails } from "../../format.js";

const number = (n) => n.toLocaleString("en-IN", { maximumFractionDigits: 3 });
const rupees = (n) => `₹${number(Math.round(n))}`;
const rank = (n, size) => n == null ? "—" : `${n} of ${size}`;
const sectorLabels = { agriculture: "Agriculture & allied", industry: "Industry", services: "Services" };
const detailLabels = { mining: "Mining & quarrying", manufacturing: "Manufacturing",
  construction: "Construction", utilities: "Utilities" };

function sectorBars(mix, period) {
  if (!mix) return "";
  return `<section class="cv-india-section">
    <h3>${esc(mix.state)} sector mix</h3>
    <p>Share of nominal GSVA · ${esc(mix.status)} · ${esc(period)} · ${esc(mix.publisher || "RBI and NSO")}</p>
    ${mix.description ? `<p>${esc(mix.description)}</p>` : ""}
    <ul class="cv-industries">${Object.entries(sectorLabels).map(([key, label]) => `
      <li class="cv-industry-${key}">
        <div><strong>${label}</strong><span>${pct(mix.shares[key], 2)}</span></div>
        <meter aria-label="${label}" min="0" max="1" value="${mix.shares[key]}"></meter>
      </li>`).join("")}</ul>
  </section>`;
}

function gatewayTable(gateways) {
  if (!gateways) return "";
  const rows = [
    ["Major port", gateways.port],
    ...Object.entries(gateways.airports).map(([size, airport]) =>
      [`${size[0].toUpperCase()}${size.slice(1)} airport with scheduled service`, airport]),
    ...gateways.rail.map((route) => [route.main_line ? "Main line" : route.freight ? "Freight corridor" : "Rail corridor", route]),
  ].filter(([, record]) => record);
  return `<section class="cv-india-section">
    <h3>Transport gateways</h3>
    ${rows.length ? `<table class="cv-india-table cv-economy-table">
      <thead><tr><th scope="col">Gateway</th><th scope="col">Distance</th></tr></thead>
      <tbody>${rows.map(([label, record]) => `<tr><th scope="row">${esc(record.name)}
        <small>${esc([record.name === label ? null : label, record.period].filter(Boolean).join(" · "))}</small></th>
        <td>${number(record.distance_km)} km</td></tr>`).join("")}</tbody>
      </table><p>Approximate straight-line distances from the city centre. Rail distances use the mapped
        alignment on the hex grid.${gateways.rail.length ? "" : " No corridor or main line is mapped near this footprint."}</p>
      <p>Port locations · CWPRS. Airports · OurAirports. Rail · © OpenStreetMap contributors.</p>`
      : "<p>Gateway data is unavailable.</p>"}
  </section>`;
}

export function economyPanel({ city, profile, yieldDefinitions, cohortSize, sources: sourceNames }) {
  const economy = profile.economy;
  if (!economy) return '<section class="cv-india-section"><p>Economy data is unavailable.</p></section>';
  const shares = economy.national_shares;
  const growth = economy.output_growth;
  const sectorOutput = economy.sector_output;
  const sources = (ids) => [ids].flat().map((id) => sourceNames?.get(id) ?? id).join(" · ");
  return `<section class="cv-india-section">
    <h3>City output</h3>
    <dl class="cv-india-stats cv-people-stats">
      <div><dt>Nominal GDP</dt><dd>${economy.gdp == null ? "—" : `₹${number(economy.gdp / 1e7)} crore`}</dd>
        <dt>Rank ${rank(city.ranks?.gdp, city.rank_counts?.gdp)}</dt></div>
      <div><dt>GDP per resident</dt><dd>${economy.gdp_per_resident == null ? "—" : rupees(economy.gdp_per_resident)}</dd>
        <dt>Rank ${rank(city.ranks?.gdp_per_capita, city.rank_counts?.gdp_per_capita)}</dt></div>
      ${growth ? `<div><dt>Nominal output growth</dt><dd>${pct(growth.value, 2)}</dd>
        <dt title="${esc(sources(growth.source))}">IndiaCiv estimate · ${esc(growth.period)}</dt></div>` : ""}
      ${Object.entries(shares ?? {}).filter(([, row]) => row).map(([key, row]) =>
        `<div><dt>Share of India’s ${key === "gdp" ? "GDP" : "population"}</dt><dd>${pct(row.value, 3)}</dd>
          <dt title="${esc(sources(row.source))}">IndiaCiv estimate · ${esc(row.period)}</dt></div>`).join("")}
    </dl>
    <p>IndiaCiv estimate · ${esc(economy.period)}. State output allocated by projected urban population.
      GDP per resident uses the UN mid-2026 projection. GDP ranks cover mapped urban agglomerations with each value.</p>
  </section>
  ${sectorOutput ? `<section class="cv-india-section">
    <h3>City GDP by sector</h3>
    <p>IndiaCiv estimate · ${esc(sectorOutput.period)}. ${esc(sectorOutput.description)}</p>
    <table class="cv-india-table cv-economy-table">
      <thead><tr><th scope="col">Sector</th><th scope="col">₹ crore</th></tr></thead>
      <tbody>${Object.entries(sectorLabels).map(([key, label]) =>
        `<tr><th scope="row">${label}</th><td>${number(sectorOutput.values[key] / 1e7)}</td></tr>`).join("")}
      ${Object.entries(detailLabels).filter(([key]) => sectorOutput.values[key] != null).map(([key, label]) =>
        `<tr><th scope="row"><small>Industry · ${label}</small></th><td>${number(sectorOutput.values[key] / 1e7)}</td></tr>`).join("")}</tbody>
    </table>
    <p>${esc(sources(sectorOutput.source))}</p>
  </section>` : ""}
  <section class="cv-india-section">
    <h3>City yields</h3>
    <table class="cv-india-table cv-economy-table">
      <thead><tr><th scope="col">Yield and period</th><th scope="col">Rank</th></tr></thead>
      <tbody>${yieldDefinitions.map((y) => {
        const value = city.yields?.[y.key];
        const meta = city.yield_meta?.[y.key];
        const display = value == null ? "—" : y.unit === "INR" ? rupees(value) : `${number(value)} ${y.unit}`;
        return `<tr><th scope="row" title="${esc(yieldDetails(y, value, meta))}">${esc(y.label)} · ${esc(display)}
          <small>${esc(meta?.period ?? y.period)}${meta?.estimated ? " · IndiaCiv estimate" : ""}
          ${meta?.coverage === "City centre hex proxy" ? " · City centre hex proxy" : ""}</small></th>
          <td>${rank(economy.ranks[y.key], cohortSize)}</td></tr>`;
      }).join("")}</tbody>
    </table>
  </section>
  ${sectorBars(economy.sector_mix, economy.period)}
  ${gatewayTable(profile.gateways)}`;
}

function sharedPeriod(a, b) {
  return a?.period && a.period === b?.period && a.source === b.source ? a.period : null;
}

export function compareRows(left, right) {
  const rows = [];
  function add(label, series, a, b, format, note = "") {
    if (series && Number.isFinite(a) && Number.isFinite(b)) {
      rows.push({ label, period: series, left: format(a), right: format(b), note });
    }
  }
  const { city: a, profile: p } = left;
  const { city: b, profile: q } = right;
  const populationPeriod = sharedPeriod(a.provenance?.population, b.provenance?.population);
  add("Population", populationPeriod && `${populationPeriod} · UN`, a.population, b.population, number);
  add("Projected growth", populationPeriod && a.growth_period === b.growth_period && a.growth_period,
    a.projected_growth, b.projected_growth, (n) => pct(n, 2));
  const gdp = p.economy, otherGdp = q.economy;
  add("GDP per resident", populationPeriod && p.method === q.method && gdp?.period &&
    gdp.period === otherGdp?.period && `${gdp.period} · IndiaCiv estimate`,
    gdp?.gdp_per_resident, otherGdp?.gdp_per_resident, rupees);
  const air = p.air?.aqi, otherAir = q.air?.aqi;
  if (sharedPeriod(air, otherAir) &&
      air.calendar_days === otherAir.calendar_days && air.valid_days > 0 && otherAir.valid_days > 0 &&
      Number.isFinite(air.bad_days) && Number.isFinite(otherAir.bad_days)) {
    rows.push({ label: "Bad-air days", period: air.period, note: "AQI ≥201 · CPCB. Counts are shown per valid reporting days.",
      left: `${air.bad_days} of ${air.valid_days}`, right: `${otherAir.bad_days} of ${otherAir.valid_days}` });
  }
  const work = p.citizens?.workforce, otherWork = q.citizens?.workforce;
  add("Employed share", sharedPeriod(work, otherWork) && work.method === otherWork.method && work.period,
    work?.state_urban_wpr_all_ages, otherWork?.state_urban_wpr_all_ages, (n) => pct(n),
    "IndiaCiv estimate using the state urban PLFS rate for all ages.");
  add("Urban unemployment benchmark (15+)", sharedPeriod(work, otherWork),
    work?.state_urban_unemployment_15_plus, otherWork?.state_urban_unemployment_15_plus, (n) => pct(n, 1),
    "PLFS state urban labour force. Cross-state footprints use estimated labour-force weights.");
  const science = a.yield_meta?.science, otherScience = b.yield_meta?.science;
  add("Science", sharedPeriod(science, otherScience) && science.coverage && science.coverage === otherScience.coverage &&
    science.period, a.yields?.science, b.yields?.science, (n) => `${number(n)} points`, science?.coverage);
  return rows;
}

function stateLabel(city, profile, stateNames) {
  return (profile?.states ?? city.states).map((state) => stateNames.get(state) ?? state).join(", ");
}

export function comparePanel(city, peers, profiles, stateNames) {
  return `<section class="cv-india-section cv-compare">
    <label for="cv-compare-city">Compare ${esc(city.name)} · ${esc(stateLabel(city, profiles[city.id], stateNames))} with</label>
    <select id="cv-compare-city">
      <option value="">Choose a city</option>
      ${peers.map((peer) => `<option value="${esc(peer.id)}">${esc(peer.name)} ·
        ${esc(stateLabel(peer, profiles[peer.id], stateNames))}</option>`).join("")}
    </select>
    <div data-comparison aria-live="polite"></div>
  </section>`;
}

export function bindCompare(dock, model, peers, profiles) {
  const select = dock.querySelector("#cv-compare-city");
  const output = dock.querySelector("[data-comparison]");
  select.onchange = () => {
    const city = peers.find((peer) => peer.id === select.value);
    const profile = city && profiles[city.id];
    if (!profile) {
      output.replaceChildren();
      return;
    }
    const rows = compareRows(model, { city, profile });
    output.innerHTML = `<table class="cv-india-table cv-economy-table">
      <thead><tr><th scope="col">Measure</th><th scope="col">${esc(model.city.name)}
      <small>${esc(stateLabel(model.city, model.profile, model.stateNames))}</small></th>
      <th scope="col">${esc(city.name)}<small>${esc(stateLabel(city, profile, model.stateNames))}</small></th></tr></thead>
      <tbody>${rows.map((row) => `<tr><th scope="row">${esc(row.label)}<small>${esc(row.period)}${row.note ?
        `<br>${esc(row.note)}` : ""}</small></th><td>${esc(row.left)}</td><td>${esc(row.right)}</td></tr>`).join("")}</tbody>
    </table>`;
  };
}
