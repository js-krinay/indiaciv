import { compact, pct } from "../format.js";

export const indianNumber = (value) => value.toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const cityGdp = (value) => `₹${indianNumber(value / 1e7)} crore`;
export const compactCityGdp = (value) => `₹${compact(value / 1e7)} cr`;

export function cityHeadlineStats(city, gold) {
  const gdp = city.yields?.gold;
  const meta = city.yield_meta?.gold;
  const outputSource = [meta?.period ?? gold?.period, meta?.estimated && "IndiaCiv estimate",
    "MoSPI and state accounts, allocated by projected urban population"].filter(Boolean).join(" · ");
  const projectedGrowth = city.growth_period && city.projected_growth;
  return [
    ["population", "Population", city.population, indianNumber,
      "Mid-2026 · UN DESA projection"],
    ["growth", "Projected growth", projectedGrowth,
      (n) => `${n > 0 ? "+" : ""}${pct(n, 2)}`, `${city.growth_period} · UN DESA projection`],
    ["gdp", "Nominal GDP", gdp, cityGdp, outputSource],
    ["gdp_per_capita", "GDP per resident", city.gdp_per_capita,
      (n) => `₹${indianNumber(n)}`, `${outputSource} · UN mid-2026 residents`],
  ].filter(([, , value]) => Number.isFinite(value)).map(([key, label, value, format, source]) => ({
    key, label, text: format(value), source,
    rank: city.ranks?.[key] == null || !city.rank_counts?.[key]
      ? "" : `#${city.ranks[key]} of ${city.rank_counts[key]}`,
  }));
}

export function workforceSource(workforce) {
  return `${workforce.period} · IndiaCiv estimate · PLFS urban worker rates and UN mid-2026 population`;
}
