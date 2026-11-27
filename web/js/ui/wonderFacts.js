import { esc } from "../format.js";

export function wonderFacts(row, data) {
  const facts = [];
  const rule = data.wonders?.rules?.find((item) => item.id === row.rule);
  if (rule) facts.push(["Selection rule", rule.text.replace(/FY 2025-26(?! \()/g, "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)")]);
  if (row.period) {
    facts.push(["Inventory", row.period]);
    const sources = (row.sources || []).map((id) => data.sources?.find((source) => source.id === id)?.publisher);
    facts.push(["Source", [...new Set(sources.filter(Boolean))].join(" · ")]);
  }
  const metrics = row.metrics;
  if (metrics?.area_km2 != null) {
    facts.push(["Area rank", String(row.rank)]);
    facts.push(["Official area", `${metrics.area_km2.toLocaleString("en-IN", { maximumFractionDigits: 4 })} km²`]);
  }
  if (metrics?.institution_count != null) {
    facts.push(["Class order", `${row.rank} of ${metrics.institution_count} mapped ${metrics.institution_class} sites`]);
  }
  if (row.cells?.length) facts.push(["Mapped extent", `${row.cells.length} protected land hexes`]);
  return facts;
}

export function wonderFactsHtml(row, data) {
  return wonderFacts(row, data).map(([label, value]) => `<b>${esc(label)}</b> · ${esc(value)}`).join("<br>");
}
