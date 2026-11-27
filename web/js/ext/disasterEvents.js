import { esc } from "../format.js";

const formatter = new Intl.DateTimeFormat("en-IN", {
  day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
});
export const disasterDate = (value) => formatter.format(new Date(value));

export function disasterEvent(event, districts, states = new Map()) {
  const when = event.start_date
    ? disasterDate(event.start_date) + (event.end_date ? ` – ${disasterDate(event.end_date)}` : "")
    : `Reported ${disasterDate(event.reported_on)}`;
  const areas = [
    event.area, ...event.districts.map((id) => districts.get(id)),
    ...(event.states || []).map((id) => states.get(id)),
  ].filter(Boolean);
  const links = [event, ...(event.related_sources || [])].map((record) =>
    `<a href="${esc(record.url)}" target="_blank" rel="noopener noreferrer">${esc(record.publisher || "Press Information Bureau")}</a>`);
  const notes = [
    event.landfall_date && `Landfall ${disasterDate(event.landfall_date)}`,
    event.magnitude != null && `Magnitude ${event.magnitude.toFixed(1)}`,
  ].filter(Boolean);
  const impact = event.impact;
  const losses = [
    impact?.deaths != null && `${impact.deaths} deaths`,
    impact?.houses_destroyed != null && `${impact.houses_destroyed} houses destroyed`,
  ].filter(Boolean);
  if (losses.length) notes.push(`${districts.get(impact.district)} · ${losses.join(" · ")}`);
  return `<p><strong>${esc(event.label)}</strong> · ${esc(event.type)} · ${esc(when)}<br>
    ${esc([...new Set([...areas, ...notes])].join(" · "))}<br>${links.join(" · ")}</p>`;
}
