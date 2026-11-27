import { wonderNotes } from "./pediaWonders.js";
import { wonderFacts } from "./wonderFacts.js";
import { esc } from "../format.js";
import { formatLensTick, formatLensValue } from "./lenses.js";

export const number = (value, digits = 2) => Number.isFinite(value)
  ? value.toLocaleString("en-IN", { maximumFractionDigits: digits }) : "";
const percent = (value) => Number.isFinite(value) ? `${number(value * 100)}%` : "";
const GROUPED_NORTH_EAST = new Set(["AR", "MN", "ML", "MZ", "NL", "SK", "TR"]);
const FY26 = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)";
const SOURCE_LINKS = {
  datameet: ["https://creativecommons.org/licenses/by/4.0/"],
  india_terrain: ["https://creativecommons.org/licenses/by/4.0/", "https://doi.org/10.5281/zenodo.7254221"],
  un_wup_cities: ["https://creativecommons.org/licenses/by/3.0/igo/", "https://zenodo.org/records/10475196/files/WUP2018-F22-Cities_Over_300K_Annual.xls?download=1"],
  soi_outline: ["https://surveyofindia.gov.in/pages/copyright-policy"],
  tg_projections: ["https://www.nhm.gov.in/NTCP/Manuals_Guidelines/index4.php?lang=1&level=0&lid=13&linkid=8"],
  gem_power: ["https://creativecommons.org/licenses/by/4.0/"],
  gem_coal: ["https://creativecommons.org/licenses/by/4.0/"],
  gem_iron: ["https://creativecommons.org/licenses/by/4.0/"],
  gem_oil_gas: ["https://creativecommons.org/licenses/by/4.0/"],
};

export function external(url, label) {
  if (!/^https?:\/\//i.test(url || "")) return esc(label || "");
  return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label || url)}</a>`;
}

function sourceDetails(row, data) {
  if (!row) return `<p>IndiaCiv builds on ${external("https://karpathy.ai/usaciv", "usaciv")} by Andrej Karpathy.</p>
    <p><a href="LICENSE">Read the full MIT licence and copyright notice</a></p>`;
  const [licence, edition] = SOURCE_LINKS[row.id] || [];
  const files = row.files || [];
  const downloads = {
    "data/world.json": data.world,
    "data/wonders.json": data.wonders,
    "data/nation.json": data.nation,
    "data/infrastructure.json": data.infrastructure,
    "data/protected_land.json": data.protectedLand,
    "data/protected_ramsar.json": data.protectedRamsar,
  };
  const downloadAvailable = /^data\/[a-z0-9_-]+\.json$/.test(row.download_path || "")
    && (!Object.hasOwn(downloads, row.download_path) || downloads[row.download_path]);
  return `<p>${esc(row.description || "")}</p><dl class="pedia-facts">
    <div><dt>Publisher</dt><dd>${esc(row.publisher || "")}</dd></div>
    <div><dt>Licence and attribution</dt><dd>${external(row.license_url || licence, row.license)}</dd></div>
    ${row.vintage ? `<div><dt>Edition or release</dt><dd>${esc(row.vintage)}</dd></div>` : ""}
    ${row.period ? `<div><dt>Data period</dt><dd>${esc(row.period)}</dd></div>` : ""}
    </dl>
    ${row.id === "un_wup_cities" ? "<p>© United Nations. Department of Economic and Social Affairs, Population Division. The map filters to Indian urban agglomerations, joins their coordinates to the hex grid and calculates growth between the two projected July totals.</p>" : ""}
    ${row.id === "india_terrain" ? "<p>Zanaga et al., ESA WorldCover 10 m v200.</p>" : ""}
    ${row.id === "soi_outline" && !row.description?.startsWith("Source: Survey of India")
      ? "<p>Source: Survey of India, Government of India.</p>" : ""}
    ${row.id === "tg_projections" ? "<p>Technical Group on Population Projections, National Commission on Population, Ministry of Health and Family Welfare, Government of India. Population Projections for India and States 2011–2036.</p>" : ""}
    ${row.id === "datameet" ? `<p>${external("https://github.com/datameet/maps/tree/b3fbbde595310b397a55d718e0958ce249a4fa1f/States", "Pinned Admin2 dataset")} ·
      ${external("https://github.com/datameet/maps/tree/b3fbbde595310b397a55d718e0958ce249a4fa1f/Districts/Census_2011", "Pinned district dataset")}</p>` : ""}
    ${row.id.startsWith("gem_") ? "<p>IndiaCiv filters the release to eligible operating sites and assigns them to map hexes, with limited snapping to nearby Indian land.</p>" : ""}
    ${row.id === "gem_power" ? `<p>The exact TransitionZero contribution vintage is unresolved.
      ${row.credit_link ? "" : `${external("https://www.transitionzero.org/terms/tz-sam-terms-of-use", "Solar Asset Mapper attribution terms")} · `}
      ${external("https://creativecommons.org/licenses/by-nc/4.0/", "CC BY-NC 4.0")}</p>` : ""}
    ${row.used_for?.length ? `<h2>How this map uses it</h2><ul>${row.used_for.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>` : ""}
    <p>${external(row.homepage, "Publisher website")}${edition ? ` · ${external(edition, "Dataset release")}` : ""}</p>
    ${row.credit_link ? `<p>${external(row.credit_link.url, row.credit_link.label)}</p>` : ""}
    ${downloadAvailable
      ? `<p><a href="${esc(row.download_path)}" download>${esc(row.download_label || "Download derived data")}</a></p>` : ""}
    ${files.length ? `<h2>Files and pins</h2><ul class="pedia-files">${files.map((file) => `<li>
      ${external(file.url, file.file || file.url)}
      ${file.sha256 ? `<br><small>SHA-256 <code>${esc(file.sha256)}</code></small>` : ""}
      ${file.timestamp ? `<br><small>OSM update ${esc(file.timestamp)}</small>` : ""}
      ${file.retrieved ? `<br><small>Retrieved ${esc(file.retrieved.slice(0, 10))} · ${number((file.bytes || 0) / 1e6, 1)} MB</small>` : ""}
      ${file.query ? `<details><summary>Source query</summary><pre>${esc(file.query)}</pre></details>` : ""}</li>`).join("")}</ul>` : ""}`;
}

const PROFILE_FIELDS = [
  ["sex_ratio", "Women per 1,000 men", "sex_ratio", 1],
  ["age_0_14", "Age 0–14", "children", .01],
  ["age_60", "Age 60 and over", "elderly", .01],
  ["median_age", "Median age", "median_age", 1],
  ["imr", "Infant mortality", "infant_mortality", 1],
  ["tfr", "Total fertility", "fertility", 1],
  ["life_female", "Life expectancy, women", "life_female", 1],
  ["life_male", "Life expectancy, men", "life_male", 1],
];

function stateFacts(entry, data, index, link, facts) {
  const { row } = entry;
  const profile = row.profile || {};
  const projection = row.provenance?.population?.period;
  const india = data.nation?.nation;
  if (projection) {
    facts.push(["Population", number(row.population), projection]);
    if (data.nation.year === 2026 && Number.isFinite(india?.population)) facts.push(["India population", number(india.population), projection]);
    if (Number.isFinite(profile.density) && Number.isFinite(data.nation.profile?.density)) {
      facts.push(["State density", `${number(profile.density, 0)} people/km²`, projection],
        ["India density", `${number(data.nation.profile.density, 0)} people/km²`, projection]);
    }
  }
  if (profile.growth_period) facts.push(["Projected population growth", percent(profile.growth), profile.growth_period]);
  const profileRows = PROFILE_FIELDS.map(([field, label, id, factor]) => {
    const lens = index.get(`lens/${id}`)?.row;
    if (!lens?.period || !Number.isFinite(profile[field])) return "";
    const health = ["imr", "tfr", "life_female", "life_male"].includes(field);
    if (health && profile.health?.period !== "2026") return "";
    const age = ["age_0_14", "age_60", "median_age"].includes(field);
    const date = health ? "2026 · IndiaCiv estimate" : age && row.age_source === "worldpop_age" ? "2026 · WorldPop estimate" : projection;
    if (!date) return "";
    const scope = GROUPED_NORTH_EAST.has(entry.id) && (age || health) ? " · Combined North-East profile" : "";
    return `<tr><th scope="row">${link(`lens/${id}`, label)}</th><td>${esc(formatLensValue(lens, profile[field] * factor))}</td><td>${esc(date + scope)}</td></tr>`;
  }).join("");
  const metrics = Object.entries(row.metrics || {}).map(([id, metric]) => {
    const lens = index.get(`lens/${id}`)?.row;
    if (!lens?.period || !Number.isFinite(metric.value)) return "";
    const national = data.nation.metrics?.[id];
    const baseline = national?.source === metric.source && Number.isFinite(national?.value)
      ? formatLensValue(lens, national.value) + (national.estimated ? " · IndiaCiv estimate" : "") : "—";
    return `<tr><th scope="row">${link(`lens/${id}`, lens.name)}</th><td>${esc(formatLensValue(lens, metric.value))}</td>
      <td>${esc(baseline)}</td><td>${esc(lens.period)}${metric.estimated ? " · IndiaCiv estimate" : ""}</td></tr>`;
  }).join("");
  const resources = Object.entries(data.resources?.summary?.states?.[entry.id] || {}).map(([id, item]) => {
    const resource = index.get(`resource/${id}`);
    if (!resource) return "";
    const periods = [...new Set(resource.items.map((site) => site.period))];
    const total = periods.length === 1 && periods[0] && Number.isFinite(item.value)
      ? ` · ${number(item.value)} ${esc(item.unit)}${item.unit === "MW" || item.unit === "Mt/yr" ? " capacity" : ""} · ${esc(periods[0])}` : "";
    return `<li>${link(resource.key)} · ${number(item.count)} mapped sites${total}</li>`;
  }).join("");
  return `${profileRows ? `<h2>State profile</h2><table><thead><tr><th>Measure</th><th>Value</th><th>Period and scope</th></tr></thead><tbody>${profileRows}</tbody></table>` : ""}
    ${metrics ? `<h2>State and India measures</h2><table><thead><tr><th>Measure</th><th>State</th><th>India</th><th>Period and scope</th></tr></thead><tbody>${metrics}</tbody></table>` : ""}
    ${Number.isFinite(profile.density) && Number.isFinite(data.nation.profile?.density) ?
      `<p>${link("lens/state_density", "State density")} divides the state projection by its mapped DataMeet area.
      India density uses the published national area.</p>` : ""}
    ${resources ? `<h2>Resource sites</h2><ul>${resources}</ul>` : ""}
    <p>Compare population and other measures with the ${link("lens/index", "map lenses")}.</p>`;
}

export function caption(entry) {
  if (entry.kind === "state" && entry.cells.length) return "State or territory shape from its map tiles";
  if (entry.kind === "wonder") return "Wonder motif used on the map";
  if (entry.kind === "resource") return "Resource marker used on the map";
  if (entry.kind === "lens") return "Map colour scale";
  if (entry.kind === "city" && entry.row.cell != null) return "City and footprint as drawn on the map";
  if (entry.kind === "terrain" && entry.cell != null) return entry.example?.name || "Verified example tile from the map build";
  if (entry.kind === "river" && entry.cell != null) return "Terrain near the mapped river course";
  if (entry.kind === "rail" && entry.cells?.length) return "Rail corridor across its mapped hexes";
  if (entry.kind === "protected" && entry.cell != null) return "Mapped protected land and its location";
  return "Illustrative terrain specimen";
}

export function articleContent(entry, data, index, link) {
  const { row, kind } = entry;
  const facts = [];
  let intro = row?.description || "";
  let detail = "";
  switch (kind) {
    case "state":
      intro = "Explore places, people and resources across this part of India.";
      detail = stateFacts(entry, data, index, link, facts);
      break;
    case "wonder": {
      if (!row.period) facts.push(["Era", row.era || ""]);
      if (row.subtype) facts.push(["Type", row.subtype.replaceAll("_", " ")]);
      if (row.foreign_side) facts.push(["Jurisdiction", row.location || "Tibet"]);
      facts.push(...wonderFacts(row, data));
      const selected = (data.wonders.rules || []).filter((rule) => rule.id !== row.rule && row.selection_rules?.includes(rule.id));
      const refs = Object.entries(row.references || {});
      detail = `<h2>Setting and significance</h2><p>${esc(wonderNotes[row.id] || row.long_description || row.description)}</p>
        ${selected.map(({ text }) => `<p>${esc(text.replace(/FY 2025-26(?! \()/g, FY26))}</p>`).join("")}
        ${refs.length ? `<h2>References</h2><ul>${refs.map(([type, ref]) => `<li>${external(ref.url, type === "facts" ? "Site history and significance" : "Mapped location")}${ref.license ? ` · ${esc(ref.license)}` : ""}</li>`).join("")}</ul>` : ""}`;
      break;
    }
    case "terrain":
      intro = entry.field === "features" ? "A mapped feature that can coexist with other terrain on the same hex."
        : entry.field === "relief" ? "A landform class assigned independently of climate and vegetation."
          : "A class used to paint the surface of the map.";
      facts.push([entry.field === "water" ? "Map water hexes"
        : entry.field === "features" ? "Indian land and map water hexes"
          : entry.field === "base" && ["ocean", "coast", "lake"].includes(row.key) ? "Map water hexes" : "Indian land hexes", number(entry.count)]);
      detail = `<h2>Assignment rule</h2><p>${esc(row.rule || "Classification follows the terrain table for this map build.")}</p>
        ${entry.examples?.length ? `<h2>Verified map examples</h2><ul>${entry.examples.map((example) =>
          `<li><button class="btn" data-example="${example.cell}">${esc(example.name)} ↗</button></li>`).join("")}</ul>`
          : row.example ? `<p>Landscape reference · ${esc(row.example)}</p>` : ""}
        ${entry.sites?.length ? `<h2>Mapped sites</h2><ul>${entry.sites.map((site) => `<li>${esc(site.name)}</li>`).join("")}</ul>` : ""}
        <p>${link("terrain/index", "Browse terrain classes")}</p>`;
      break;
    case "city":
      facts.push(["Population", number(row.population), row.provenance?.population?.period || "Projected for mid-2026"],
        ["Population rank in India", number(row.ranks?.population), "Mid-2026 projection"]);
      if (row.growth_period) facts.push(["Projected growth", percent(row.projected_growth), row.growth_period]);
      detail = `<p>Population describes the UN urban agglomeration. The map places the city at its canonical location and footprint.</p>
        <p>${link("lens/city_population")} · ${link("lens/city_growth")}</p>`;
      break;
    case "resource": {
      const periods = [...new Set(entry.items.map((item) => item.period).filter(Boolean))];
      facts.push(["Mapped sites", number(entry.items.length), periods.join(" · ")]);
      const total = data.resources.summary?.national?.[entry.id];
      const measure = row.unit === "MW" ? "Rated capacity" : row.unit === "Mt/yr" ? "Mine capacity" : "Reported measure";
      if (periods.length === 1 && entry.items.every((item) => item.period) && Number.isFinite(total?.value)) {
        facts.push([`India · ${measure}`, `${number(total.value)} ${total.unit || ""}`, periods[0]]);
      }
      detail = `<h2>Mapped locations</h2>${entry.items.length ? `<ul class="pedia-locations">${entry.items.map((item, i) => {
        const state = index.get(`state/${item.state}`);
        return `<li>${esc(item.name)}${state ? ` · ${link(state.key)}` : ""}${item.period ? ` · ${esc(item.period)}` : ""}
          ${item.estimated ? " · IndiaCiv estimate" : ""}
          ${item.period && Number.isFinite(item.value) && row.unit ? ` · ${esc(measure)} ${number(item.value)} ${esc(row.unit)}` : ""}
          ${Number.isFinite(item.x) && Number.isFinite(item.y) ? ` <button class="btn" data-site-index="${i}" aria-label="Show ${esc(item.name || row.name)} on map">↗</button>` : ""}</li>`;
      }).join("")}</ul>` : "<p>No mapped sites for this type.</p>"}`;
      break;
    }
    case "lens": {
      const cells = row.values?.filter(Number.isFinite).length || 0;
      facts.push(["Period", row.period || "Data unavailable"], ["Geography", entry.geography || "As described in the lens method"],
        ["Scale", row.scale || ""], ["Unit", row.unit || ""],
        ["Legend range", row.period && cells ? `${formatLensTick(row, 0, 0)} to ${formatLensTick(row, 1, 4)}` : ""],
        ["Eligible hexes in this build", number(cells)]);
      detail = `${row.note ? `<h2>Method</h2><p>${esc(row.note)}</p>` : ""}
        ${row.source_line ? `<p>${esc(row.source_line)}</p>` : ""}
        ${row.higher_is === "good" || row.higher_is === "bad" ? `<p>Higher values are ${row.higher_is === "good" ? "better" : "worse"} for this measure.</p>` : ""}
        <p>Hexes with missing values stay uncoloured by the lens. Hover or drag on the legend to isolate a range.</p>
        <p>See a ${link("state/index", "state profile")} for published comparisons with matching geography, units and dates.</p>`;
      break;
    }
    case "river":
      intro = "A named river course shown along the map’s hex edges.";
      facts.push(["Mapped channel segments", number(entry.edges.length)]);
      detail = `<p>Channel width follows a cartographic rank by named course. ${link("river/index", "Read about river mapping")}.</p>`;
      break;
    case "rail":
      intro = row ? "An operating railway zone in the national freight report." : "A trunk railway corridor drawn from the mapped network.";
      if (row) facts.push(["Originating freight", `${number(row[2])} ${data.infrastructure.freight.unit}`, data.infrastructure.freight.label]);
      else facts.push(["Mapped corridor hexes", number(new Set(entry.cells).size), data.infrastructure.vintage.network]);
      detail = `<p>${link("rail/index", "Compare originating freight and read the transport method")}.</p>`;
      break;
    case "protected":
      intro = "A site in the map’s protected land inventory.";
      facts.push(["Status", row.status || entry.group || "", row.period]);
      if (Number.isFinite(row.area_ha)) {
        facts.push(["Official area", `${number(row.area_ha / 100, 4)} km²`, row.authority]);
      }
      detail = `<p>${link("protected/index", "Read how protected land is mapped")}.</p>`;
      break;
    case "yield":
      facts.push(["Period", row.period], ["Underlying unit", row.unit], ["Units per point", number(row.scale || 1)]);
      detail = `<p>${link("yield/index", "About yield points")}</p>`;
      break;
    case "source":
      detail = sourceDetails(row, data);
      intro = "";
      break;
  }
  return { facts, intro, detail };
}
