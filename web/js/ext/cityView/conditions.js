import { esc, pct } from "../../format.js";
import { disasterDate, disasterEvent } from "../disasterEvents.js";

function airCard({ aqi, pm25 } = {}) {
  if (!aqi && !pm25) return "";
  return `<section class="cv-india-section">
    <h3>Air quality</h3>
    <dl class="cv-india-stats">
      ${aqi ? `<div><dt>Bad-air days · ${esc(aqi.period)}</dt><dd>${aqi.bad_days}</dd></div>
        <div><dt>Valid-day coverage</dt><dd>${aqi.valid_days} of ${aqi.calendar_days} days</dd></div>
        <div><dt>National rank by share of bad-air days</dt><dd>${aqi.rank} of ${aqi.covered_cities}</dd></div>` : ""}
      ${pm25 ? `<div><dt>Footprint PM₂.₅</dt><dd>${pm25.value.toFixed(1)} µg/m³</dd></div>` : ""}
    </dl>
    ${aqi ? "<p>AQI rated Poor or worse (≥201). Rank 1 has the highest share. CPCB via EnviroCatalysts.</p>" : ""}
    ${pm25 ? `<p>IndiaCiv estimate · ${esc(pm25.period)} · ${pct(pm25.footprint_coverage)} of footprint covered by district estimates.</p>` : ""}
  </section>`;
}

function hazardCard(events, summary, districts) {
  if (!events.length) return "";
  return `<section class="cv-india-section">
    <h3>Documented hazards</h3>
    <p>Selected member-district records · ${esc(events[0].period || "2026")}</p>
    ${summary ? `<dl class="cv-india-stats">
      <div><dt>Documented events</dt><dd>${summary.count}</dd></div>
      <div><dt>${summary.last_report_only ? "Latest report date" : "Latest event date"}</dt>
        <dd>${disasterDate(summary.last_date)}</dd></div>
      ${Object.entries(summary.by_type).map(([type, count]) =>
        `<div><dt>${esc(type)}</dt><dd>${count}</dd></div>`).join("")}
    </dl>` : ""}
    ${events.map((event) => disasterEvent(event, districts)).join("")}
  </section>`;
}

function housingCard(housing) {
  if (!housing) return "";
  return `<section class="cv-india-section">
    <h3>House Price Index</h3>
    <dl class="cv-india-stats">
      <div><dt>${esc(housing.market)} · ${esc(housing.period)}</dt><dd>${esc(housing.index ?? "—")}</dd></div>
      ${housing.yoy_pct == null ? "" : `<div><dt>Change from a year earlier</dt><dd>${esc(housing.yoy_pct)}%</dd></div>`}
    </dl>
    <p>Index (base = 100) · ${housing.provisional ? "Provisional · " : ""}
      <a href="${esc(housing.url)}" target="_blank" rel="noopener noreferrer">Reserve Bank of India</a></p>
  </section>`;
}

export function conditionsCards(profile, districts) {
  return airCard(profile.air) + hazardCard(profile.hazards ?? [], profile.hazard_summary, districts) + housingCard(profile.housing);
}
