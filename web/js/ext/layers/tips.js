// Hover tooltips for the map-art layers (HTML strings; every data value is escaped). Each says where the number comes
// from and the caveat that matters for it (FAF values are model estimates; bases have no published headcount; the
// trade arc is a drawing aid; curated landmarks are an editorial pick).
import { esc, compact, int, pct, periodLabel } from "../../format.js";
import { WONDER_KINDS } from "../../render/art/sites.js";
import { MODE_STYLE } from "../../render/art/improvements.js";
import { wonderFactsHtml } from "../../ui/wonderFacts.js";

const muted = (s) => `<span class="muted">${s}</span>`;
const num = (n, d = 1) => (n == null || !Number.isFinite(n) ? "–" : compact(n));
const sign = (x) => (x > 0 ? "+" : x < 0 ? "−" : "±");

function usd(n) {
  if (n == null || !Number.isFinite(n)) return "–";
  const a = Math.abs(n);
  if (a >= 1e12) return `$${(n / 1e12).toFixed(2)} trillion`;
  if (a >= 1e9) return `$${(n / 1e9).toFixed(a >= 1e10 ? 1 : 2)} billion`;
  if (a >= 1e6) return `$${(n / 1e6).toFixed(1)} million`;
  return `$${int(n)}`;
}

const HUB_NAME = { L: "Large hub", M: "Medium hub", S: "Small hub", N: "Nonhub primary airport" };
const PORT_TYPE = { coastal: "Coastal port", great_lakes: "Great Lakes port", inland: "Inland river port" };

export const tips = {
  port(p, m) {
    const yr = p.year ?? "";
    const lines = [
      `<b>${esc(p.name)}</b> ${muted(esc([p.category || PORT_TYPE[p.type] || "Port", p.city, p.state].filter(Boolean).join(", ")))}`,
    ];
    if (p.tons != null) lines.push(`${p.rank == null ? "" : `#${int(p.rank)} by cargo among major ports · `}<b>${num(p.tons)}</b> metric tonnes (${periodLabel(p) || esc(yr)})`);
    if (p.foreign != null || p.domestic != null) lines.push(`Overseas ${num(p.foreign)} · coastal ${num(p.domestic)} metric tonnes`);
    if (p.coastal_cargo?.tons != null) lines.push(`Coastal cargo · <b>${num(p.coastal_cargo.tons)}</b> metric tonnes (${periodLabel(p.coastal_cargo) || esc(p.coastal_cargo.year)}) · ${esc(p.coastal_cargo.status)}`);
    if (p.overseas_direction) lines.push(`Overseas cargo · ${pct(p.overseas_direction.unloaded)} unloaded · ${pct(p.overseas_direction.loaded)} loaded · ${periodLabel(p.overseas_direction)}`);
    if (p.source_id || p.overseas_direction) lines.push(muted([p.cargo?.status, "Ministry of Ports, Shipping and Waterways"].filter(Boolean).map(esc).join(" · ")));
    return lines.join("<br>");
  },
  airport(a) {
    const lines = [`<b>${esc(a.id)} · ${esc(a.name)}</b> ${muted(esc([a.city, a.state].filter(Boolean).join(", ")))}`];
    if (a.hub) lines.push(esc(HUB_NAME[a.hub] || a.hub));
    if (a.enplanements != null) {
      let ch = "";
      if (a.enplanements_prev > 0) {
        const r = a.enplanements / a.enplanements_prev - 1;
        ch = ` (${sign(r)}${Math.abs(r * 100).toFixed(1)}% on ${a.year - 1})`;
      }
      lines.push(`<b>${num(a.enplanements)}</b> boardings in ${esc(a.year)}${ch}`);
    }
    if (a.cargo_lbs != null) lines.push(`All-cargo landed weight ${num(a.cargo_lbs)} lb`);
    lines.push(muted(`OurAirports · ${periodLabel(a) || esc(a.year || "")}`));
    if (a.city_provenance) lines.push(muted(`Locality · Airports Authority of India · ${periodLabel(a.city_provenance)}`));
    return lines.join("<br>");
  },
  wonder(x, m) {
    if (x.description) return [
      `<b>${esc(x.name)}</b>`, esc(x.description), muted(esc(x.location)), wonderFactsHtml(x, m.data),
    ].join("<br>");
    const k = WONDER_KINDS[x.kind]?.name || "Wonder";
    const rule = m.data.wonders?.rules?.find((r) => r.id === x.rule);
    const mt = x.metrics || {};
    const lines = [`<b>${esc(x.name)}</b> ${muted(esc([x.state].filter(Boolean).join("")))}`];
    if (x.kind === "university") {
      lines.push(`${esc(k)} · #${esc(x.rank)} by research spending`);
      if (mt.rd_usd != null) lines.push(`R&amp;D ${usd(mt.rd_usd)} (FY${esc(mt.year)})${mt.federal_usd != null ? `, ${pct(mt.federal_usd / mt.rd_usd, 0)} federal` : ""}`);
      if (mt.enrollment != null) lines.push(`${int(mt.enrollment)} students (12-month headcount, ${esc(mt.enrollment_year)})`);
    } else if (x.curated) {
      lines.push(`${esc(k)} · hand-picked (curated, not ranked by data)`);
      if (mt.visits != null) lines.push(`${num(mt.visits)} recreation visits (${esc(mt.year)})`);
      if (mt.designated) lines.push(`National Historic Landmark since ${esc(mt.designated)}`);
    } else {
      lines.push(`${esc(k)} · #${esc(x.rank)} by visits${mt.unit_type ? ` among ${esc(mt.unit_type === "National Park" ? "National Parks" : "other park units")}` : ""}`);
      if (mt.visits != null) lines.push(`<b>${num(mt.visits)}</b> recreation visits (${esc(mt.year)})${mt.visits_of ? ` ${muted(`(${esc(mt.visits_of)})`)}` : ""}`);
      if (mt.area_km2 != null) lines.push(`${int(mt.area_km2)} km²`);
    }
    if (rule?.text) lines.push(muted(esc(rule.text)));
    return lines.join("<br>");
  },
  protected(records) {
    return records.map((site) => [
      `<b>${esc(site.name)}</b>`, ...(site.hover || []).filter(Boolean).map(esc),
    ].join("<br>")).join("<br><br>");
  },
  route(rt, m) {
    const r = rt.route;
    if (rt.literal) {
      const source = m.data.sources?.find((item) => item.id === r.source);
      return [
        `<b>${esc(r.name)}</b>`,
        r.tons_k == null ? "Operational Dedicated Freight Corridor" : `${int(r.tons_k * 1000)} metric tonnes of coastal cargo handled`,
        esc([r.period, r.status, source?.publisher].filter(Boolean).join(" · ")),
      ].join("<br>");
    }
    const t = m.data.trade || {};
    const a = rt.a?.short || rt.a?.name || r.a, b = rt.b?.short || rt.b?.name || r.b;
    const modes = Object.entries(r.modes || {}).filter(([, v]) => v >= 0.05).sort((p, q) => q[1] - p[1])
      .map(([k, v]) => `${esc(MODE_STYLE[k]?.label || k)} ${Math.round(v * 100)}%`).join(" · ");
    const com = t.commodities?.[r.top_commodity];
    const lines = [
      `<b>${esc(a)} ⇄ ${esc(b)}</b> ${muted(`trade route #${esc(r.rank)}`)}`,
      `<b>${usd(r.value_musd * 1e6)}</b> of freight a year, ${num(r.tons_k * 1e3)} short tons (FAF ${esc(t.year ?? "")} estimate)`,
    ];
    if (modes) lines.push(modes);
    if (com) lines.push(`Top commodity: ${esc(com)}`);
    lines.push(muted("Both directions summed. Drawn as an arc between each zone's largest city: FAF records where freight starts and ends, not its route."));
    return lines.join("<br>");
  },
};
