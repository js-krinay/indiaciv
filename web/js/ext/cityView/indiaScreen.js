import { esc, pct } from "../../format.js";
import { cityHeadlineStats, indianNumber } from "../../ui/cityHeadlines.js";
import { isCapital } from "../../world.js";
import { conditionsCards } from "./conditions.js";
import { sparkline } from "./charts.js";
import { bindCompare, comparePanel, economyPanel } from "./economy.js";

const people = new Intl.NumberFormat("en-IN");
const count = (n) => n == null ? "—" : people.format(n);
const ageLabels = { "0_14": "0–14 years", "15_59": "15–59 years", "60_plus": "60 years and above" };
const sectorLabels = { agriculture: "Agriculture", industry: "Industry", services: "Services" };

const plaquePaths = {
  software: "M3 4h18v12H3z M8 21h8m-4-5v5m-2-13-2 2 2 2m4-4 2 2-2 2",
  footwear: "M3 11v7h18v-3l-6-2-4-7-3 2 1 4z M3 15h5m6-1 2-2",
  diamond: "m3 9 4-5h10l4 5-9 11z M3 9h18m-11-5-2 5 4 11 4-11-2-5",
  textile: "M4 4h16v16H4z M8 4v16m4-16v16m4-16v16M4 8h16M4 12h16M4 16h16",
  automotive: "m4 13 3-6h10l3 6v5H4z M4 13h16m-13 5v2m10-2v2M7 15h2m6 0h2",
  steel: "M4 4h16v4h-5v8h5v4H4v-4h5V8H4z",
};

function workforcePanel({ profile, stateNames }) {
  const workforce = profile.citizens?.workforce;
  if (!workforce) return '<section class="cv-india-section"><p>PLFS workforce estimates are unavailable for this footprint.</p></section>';
  const states = (workforce.states ?? [workforce.state]).map((state) => stateNames.get(state) ?? state).join(", ");
  const multi = workforce.states?.length > 1;
  return `<section class="cv-india-section">
      <h3>Employed residents</h3>
      <dl class="cv-india-stats cv-people-stats">
        <div><dt>All ages</dt><dd>${count(workforce.employed_all_ages)}</dd></div>
        ${workforce.employed_15_plus == null ? "" : `<div><dt>Age 15+</dt><dd>${count(workforce.employed_15_plus)}</dd></div>`}
      </dl>
      <p>IndiaCiv estimate · ${esc(workforce.period)} · PLFS urban rates for ${esc(states)}.
        ${multi ? "The city’s adult share is applied uniformly across state fragments." : ""}</p>
      <h3>Broad industry mix · Age 15+</h3>
      <p>${esc(states)} · ${esc(workforce.period)} · ${multi ? "IndiaCiv estimate" : "PLFS urban benchmark"}</p>
      ${workforce.employed_15_plus == null ? "" : "<p>City headcounts · IndiaCiv estimate</p>"}
      <ul class="cv-industries">${workforce.industries.map((row) => `
        <li class="cv-industry-${row.sector}">
          <div><strong>${sectorLabels[row.sector]}</strong>
            <span>${pct(row.state_urban_share)}${row.employed == null ? "" : ` · ${count(row.employed)}`}</span></div>
          <div class="cv-citizen-icons" role="img" aria-label="${row.icons} of 20 icons">${"<i></i>".repeat(row.icons)}</div>
        </li>`).join("")}</ul>
      <h3>Unemployment benchmark</h3>
      <p><strong>${pct(workforce.state_urban_unemployment_15_plus)}</strong> ·
        ${esc(states)} urban labour force age 15+ · ${esc(workforce.period)} · ${multi ? "IndiaCiv estimate from PLFS" : "PLFS"}</p>
    </section>`;
}

function citizenSummary({ city, profile, stateNames }, population) {
  const work = profile.citizens?.workforce;
  const states = (work?.states ?? [work?.state]).map((state) => stateNames.get(state) ?? state).join(", ");
  const series = city.population_2026;
  const points = series && [
    { year: "1 Jan", value: series.values["2026-01-01"] },
    { year: "1 Jul", value: series.values["2026-07-01"] },
    { year: "31 Dec", value: series.values["2026-12-31"] },
  ];
  const change = points && (points[2].value / points[0].value - 1);
  return `<section class="cv-india-section">
    <h3>Population · 2026</h3>
    <p><strong>${esc(population.text)}</strong> · ${esc(population.source)}
      ${population.rank ? ` · ${esc(population.rank)} mapped urban agglomerations` : ""}</p>
    ${points ? `${sparkline(points, { fmt: count, title: `${city.name} population in 2026` })}
      <p>IndiaCiv estimate · ${esc(series.period)} · ${change > 0 ? "+" : ""}${pct(change, 2)} change ·
        Interpolated from UN DESA midyear projections.</p>` : ""}
    ${work ? `<h3>Employment and unemployment</h3>
      <p><strong>${pct(work.state_urban_wpr_all_ages, 1)}</strong> employed · All ages · IndiaCiv estimate</p>
      <p>Urban unemployment benchmarks · Labour force age 15+</p>
      <p><strong>${pct(work.state_urban_unemployment_15_plus, 1)}</strong> · ${esc(states)}
        ${work.states?.length > 1 ? " · IndiaCiv estimate" : ""}</p>
      ${work.national_urban_unemployment_15_plus == null ? "" :
        `<p><strong>${pct(work.national_urban_unemployment_15_plus, 1)}</strong> · India</p>`}
      <p>PLFS · ${esc(work.period)}</p>` : ""}
  </section>`;
}

function citizenPanel({ city, profile }) {
  const age = profile.citizens?.age;
  if (!age) return '<section class="cv-india-section"><p>Age estimates are unavailable for this city.</p></section>';
  const median = age.median_band;
  return `<section class="cv-india-section">
      <h3>Age profile</h3>
      <table class="cv-india-table">
        <thead><tr><th scope="col">Age group</th><th scope="col">Residents</th><th scope="col">Share</th></tr></thead>
        <tbody>${Object.entries(ageLabels).map(([key, label]) => `<tr><th scope="row">${label}</th>
          <td>${count(age.counts[key])}</td><td>${pct(age.counts[key] / city.population)}</td></tr>`).join("")}</tbody>
      </table>
      ${age.bands?.midlife == null ? "" : `<p><strong>Midlife (35–64)</strong> ·
        ${count(age.bands.midlife)} residents · ${pct(age.bands.midlife / city.population)}</p>`}
      <p><strong>Median age band</strong> · ${median[1] == null ? `${median[0]}+` :
        median[0] === median[1] ? median[0] : `${median[0]}–${median[1]}`} years</p>
      <p>IndiaCiv estimate · ${esc(age.period)} · WorldPop age counts scaled to the UN population${age.method ===
        "worldpop_api_footprint_to_un" ? " · WorldPop API uses administrative-unit age shares" : ""}</p>
    </section>`;
}

const badgeLabels = { campus: "Campus", harbor: "Harbor", aerodrome: "Aerodrome", government_plaza: "Government plaza" };

function districtPanel(plaques, badges, districtNames, sources) {
  return `${badges.length ? `<section class="cv-india-section">
    <h3>District badges</h3>
    <p>One badge per type in each member district when a verified site falls inside the urban footprint.</p>
    <ul class="cv-plaques">${badges.map((badge) => `<li><details class="cv-plaque">
      <summary><span><strong>${badgeLabels[badge.kind]}</strong><small>${esc(districtNames.get(badge.district))}</small></span></summary>
      <p>${esc(badge.name)}${badge.kind === "government_plaza" ? " · mapped capital locality" : ""} ·
        ${esc(badge.period)} · ${esc(sources.get(badge.source) ?? badge.source)}</p>
    </details></li>`).join("")}</ul>
  </section>` : ""}<section class="cv-india-section">
    <h3>Industry specialisations</h3>
    ${plaques.length ? `<ul class="cv-plaques">${plaques.map((plaque) => `
      <li><details class="cv-plaque">
        <summary title="${esc(`${plaque.evidence} ${plaque.citation} · ${plaque.period}`)}">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="${plaquePaths[plaque.icon]}"/></svg>
          <span><strong>${esc(plaque.label)}</strong><small>Documented cluster · ${esc(plaque.period)}</small></span>
        </summary>
        <p>${esc(plaque.evidence)} <a href="${esc(plaque.url)}" target="_blank" rel="noopener noreferrer">${esc(plaque.citation)}</a></p>
      </details></li>`).join("")}</ul>` : "<p>No industry specialisations documented for this city.</p>"}
  </section>`;
}

function resourcePanel(m) {
  const sites = m.sites;
  const capacity = sites.filter(({ type, item }) => type?.unit === "MW" && Number.isFinite(item.value))
    .reduce((total, { item }) => total + item.value, 0);
  return `<section class="cv-india-section">
    <h3>Resources</h3>
    <p>${count(sites.length)} mapped sites${capacity ? ` · ${count(capacity)} MW mapped generating capacity` : ""}</p>
    <p>Inventory covers verified resource points inside the urban footprint.</p>
    <ul class="cv-india-places">${sites.map(({ item, type }, i) => `<li>
      <button type="button" data-resource="${i}">${esc(item.name)} <span aria-hidden="true">↗</span></button>
      <small>${esc([type?.name, m.stateNames.get(item.state), Number.isFinite(item.value) && type?.unit
        ? `${count(item.value)} ${type.unit}` : null].filter(Boolean).join(" · "))}</small>
      <small>${esc([item.detail, item.estimated && "IndiaCiv estimate", item.period,
        m.sources.get(item.source) || item.source].filter(Boolean).join(" · "))}</small>
    </li>`).join("")}</ul>
  </section>`;
}

export function renderIndia(dock, m, actions, profiles, cities) {
  const { city, profile, states } = m;
  const headlines = cityHeadlineStats(city, m.yieldDefinitions.find((y) => y.key === "gold"));
  const output = headlines.find((row) => row.key === "gdp");
  const districtNames = new Map(m.counties.map((d) => [d.geoid, d.name]));
  const districts = profile.districts.map((d) => {
    const context = m.districts[d.id];
    const state = m.stateNames.get(context?.state);
    return `<tr><th scope="row">${esc(districtNames.get(d.id) || d.id)}
      ${state ? `<small>${esc(state)}</small>` : ""}</th>
      <td>${count(d.district_population)}</td>
      <td>${context?.density == null ? "—" : indianNumber(context.density)}</td>
      <td>${pct(d.population_share)}</td><td>${pct(d.footprint_share)}</td></tr>`;
  }).join("");
  const places = m.wonders;
  const tabs = ["Overview", "Citizens", "Districts"];
  const conditions = conditionsCards(profile, districtNames);
  if (conditions) tabs.push("Conditions");
  const workforceIndex = tabs.push("Workforce") - 1;
  const peers = cities.filter((peer) => peer.id !== city.id && Object.hasOwn(profiles, peer.id))
    .sort((a, b) => a.name.localeCompare(b.name));
  const economyIndex = tabs.push("Economy") - 1;
  const resourcesIndex = tabs.push("Resources") - 1;
  const compareIndex = tabs.push("Compare") - 1;
  const tabPanel = (i, content) => `<div role="tabpanel" tabindex="0" id="cv-india-panel-${i}"
    aria-labelledby="cv-india-tab-${i}" hidden>${content}</div>`;
  dock.classList.add("cv-dock");
  dock.innerHTML = `
    <header class="cv-head">
      <button type="button" class="cv-close" data-close aria-label="Close City View">×</button>
      <div class="cv-india-state">Urban agglomeration · ${esc(states.map((s) => s.name).join(", "))}</div>
      <h2 class="cv-name" tabindex="-1">${isCapital(city) ? '<span title="National capital" aria-label="National capital">★</span> ' : ""}${esc(city.name)}</h2>
      ${city.full && city.full !== city.name ? `<div class="cv-india-state">${esc(city.full)}</div>` : ""}
      ${profile.industry_plaques?.length ? `<div class="cv-india-state">Documented clusters ·
        ${profile.industry_plaques.map((plaque) => `<a href="${esc(plaque.url)}" target="_blank" rel="noopener noreferrer"
          title="${esc(`${plaque.period} · ${plaque.citation}`)}">${esc(plaque.label)}</a>`).join(", ")}</div>` : ""}
      ${actions.pediaLink?.(`city/${city.id}`, "Almanac ›") || ""}
      <dl class="cv-india-stats">
        ${headlines.map((row) => `<div title="${esc(row.source)}"><dt>${esc(row.label)}</dt>
          <dd>${esc(row.text)} ${row.rank ? `<small>${esc(row.rank)}</small>` : ""}</dd>
          ${row.key === "population" || row.key === "growth" ? `<dt>${esc(row.source)}</dt>` : ""}</div>`).join("")}
      </dl>
      ${output ? `<p class="cv-head-note">${esc(output.source)}</p>` : ""}
      <p class="cv-head-note">Ranks among mapped urban agglomerations with each value.</p>
    </header>
    <nav class="cv-tabs cv-india-tabs" role="tablist" aria-label="City View tabs">
      ${tabs.map((name, i) => `<button type="button" role="tab" id="cv-india-tab-${i}"
        aria-controls="cv-india-panel-${i}" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}"
        class="${i === 0 ? "on" : ""}">${name}</button>`).join("")}
    </nav>
    <div role="tabpanel" tabindex="0" id="cv-india-panel-0" aria-labelledby="cv-india-tab-0">
    <section class="cv-india-section">
      <h3>Member districts${districts ? ` · ${profile.districts.length}` : ""}</h3>
      ${districts ? `<table class="cv-india-table cv-member-table">
        <thead><tr><th scope="col">District / state</th><th scope="col">District residents</th>
        <th scope="col">Density per km²</th><th scope="col">District residents inside city</th>
        <th scope="col">Share of city area</th></tr></thead>
        <tbody>${districts}</tbody></table>
        <p>IndiaCiv estimates. Residents and population shares use mid-2026 WorldPop and the GHSL footprint.
          Density uses Census of India district population and area with Technical Group projections for 1 March 2026.
          Membership and area shares use the 2026 map extent from DataMeet, GHSL and Survey of India.</p>`
        : "<p>District membership is unavailable for this city’s point location.</p>"}
      ${profile.civic_offices?.length ? `<p><strong>Public civic offices</strong> ·
        ${esc(profile.civic_offices.join(", "))} · DGDE directory checked 27 Nov 2026 ·
        © OpenStreetMap contributors (ODbL 1.0)</p>` : ""}
    </section>
    ${places.length ? `<section class="cv-india-section"><h3>Mapped places</h3>
      <ul class="cv-india-places">${places.map((p, i) =>
        `<li><button type="button" data-place="${i}">${esc(p.name)} <span aria-hidden="true">↗</span></button>
          ${p.period && p.source ? `<small>${esc([p.period, p.estimated && "IndiaCiv estimate",
            m.sources.get(p.source) || p.source].filter(Boolean).join(" · "))}</small>` : ""}</li>`).join("")}</ul>
    </section>` : ""}
    </div>
    <div role="tabpanel" tabindex="0" id="cv-india-panel-1" aria-labelledby="cv-india-tab-1" hidden>
      ${citizenSummary(m, headlines.find((row) => row.key === "population"))}
      ${citizenPanel(m)}
    </div>
    <div role="tabpanel" tabindex="0" id="cv-india-panel-2" aria-labelledby="cv-india-tab-2" hidden>
      ${districtPanel(profile.industry_plaques ?? [], profile.district_badges ?? [], districtNames, m.sources)}
    </div>
    ${conditions ? tabPanel(3, conditions) : ""}
    ${tabPanel(workforceIndex, workforcePanel(m))}
    ${tabPanel(economyIndex, economyPanel({ ...m, cohortSize: peers.length + 1 }))}
    ${tabPanel(resourcesIndex, resourcePanel(m))}
    ${tabPanel(compareIndex, comparePanel(city, peers, profiles, m.stateNames))}`;
  dock.scrollTop = 0;
  const buttons = [...dock.querySelectorAll('[role="tab"]')];
  function selectTab(index) {
    buttons.forEach((button, i) => {
      const active = i === index;
      button.classList.toggle("on", active);
      button.setAttribute("aria-selected", active);
      button.tabIndex = active ? 0 : -1;
      dock.querySelector(`#cv-india-panel-${i}`).hidden = !active;
    });
  }
  buttons.forEach((button, i) => {
    button.onclick = () => selectTab(i);
    button.onkeydown = (event) => {
      const next = { ArrowLeft: (i + tabs.length - 1) % tabs.length, ArrowRight: (i + 1) % tabs.length,
        Home: 0, End: tabs.length - 1 }[event.key];
      if (next == null) return;
      event.preventDefault();
      selectTab(next);
      buttons[next].focus();
    };
  });
  dock.querySelector("[data-close]").onclick = actions.onClose;
  dock.querySelector("[data-pedia-route]")?.addEventListener("click", (event) => {
    if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    actions.onPedia(event.currentTarget.dataset.pediaRoute);
  });
  bindCompare(dock, m, peers, profiles);
  for (const button of dock.querySelectorAll("[data-place]")) {
    button.onclick = () => actions.onSite({ item: places[Number(button.dataset.place)] });
  }
  for (const button of dock.querySelectorAll("[data-resource]")) {
    button.onclick = () => actions.onSite(m.sites[Number(button.dataset.resource)]);
  }
}
