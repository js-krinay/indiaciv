import { compact, pct } from "../format.js";

export const indianNumber = (value) => value.toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const cityGdp = (value) => `₹${indianNumber(value / 1e7)} crore`;
export const compactCityGdp = (value) => `₹${compact(value / 1e7)} cr`;

export function cityProjectedGrowth(city) {
  if (city.provenance?.population?.vintage === "older" ||
      city.provenance?.projected_growth?.vintage === "older" || city.provenance?.growth?.vintage === "older") return null;
  return city.growth_period ? city.projected_growth : null;
}

export function cityHeadlineStats(city, gold) {
  const population = city.provenance?.population;
  const olderPopulation = population?.vintage === "older";
  const gdp = city.yields?.gold;
  const meta = city.yield_meta?.gold;
  const outputSource = [meta?.period ?? gold?.period, meta?.estimated && "IndiaCiv estimate",
    "MoSPI and state accounts, allocated by projected urban population"].filter(Boolean).join(" · ");
  const projectedGrowth = cityProjectedGrowth(city);
  return [
    ["population", "Population", city.population, indianNumber,
      olderPopulation ? population.period : `${population?.period || "Mid-2026"} · UN DESA`,
      olderPopulation ? population : null],
    ["growth", "Projected growth", projectedGrowth,
      (n) => `${n > 0 ? "+" : ""}${pct(n, 2)}`, `${city.growth_period} · UN DESA projection`],
    ["gdp", "Nominal GDP", gdp, cityGdp, outputSource],
    ["gdp_per_capita", "GDP per resident", olderPopulation ? null : city.gdp_per_capita,
      (n) => `₹${indianNumber(n)}`, `${outputSource} · UN mid-2026 residents`],
  ].filter(([, , value]) => Number.isFinite(value)).map(([key, label, value, format, source, periodMeta]) => ({
    key, label, text: format(value), source, periodMeta,
    rank: periodMeta?.vintage === "older" || city.ranks?.[key] == null || !city.rank_counts?.[key]
      ? "" : `#${city.ranks[key]} of ${city.rank_counts[key]}`,
  }));
}

export function workforceSource(workforce) {
  return `${workforce.period} · IndiaCiv estimate · PLFS urban worker rates and UN mid-2026 population`;
}
