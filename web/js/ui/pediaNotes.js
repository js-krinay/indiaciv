// The Almanac: what every number means and exactly where it comes from.
import { esc } from "../format.js";
import { external } from "./pediaArticle.js";
import { shortSourceTitle } from "./pediaIndex.js";

export function pediaNotes(data) {
  const srcName = (id) => shortSourceTitle(data.sources?.find((s) => s.id === id));
  const freightDigits = { minimumFractionDigits: 2, maximumFractionDigits: 2 };
  return {
    "About this map": () => `
      <h4>How it's built</h4>
      <p>India is projected (Lambert azimuthal equal-area, centred on 22° N, 82° E) and cut into ${data.world.grid.cols}×${data.world.grid.rows}
      hexes, each ${data.world.grid.radius * 2} km corner to corner. The Survey of India political map decides whether
      charted water exceeds combined land in each hex. On land, the larger national share wins. Indian localities
      in the map's reference fixture keep an Indian land hex if they would otherwise fall in water or beyond the border.
      Uncovered detached islands retain land tiles. Where samples cross state lines, the state with the largest DataMeet overlap wins.
      A union territory or named detached part that would have no tile takes the hex it overlaps most. District density
      uses the geographic sample points. The Terrain page describes the map's terrain layers.</p>
      ${(data.world.tables?.named_boundary_places || []).map(({cell, names, shares}) =>
        `<p>${esc(names.join(" and "))} kept hex ${cell}. Charted area in km² is ${shares[0].toFixed(1)} Indian land,
          ${shares[1].toFixed(1)} neighbouring land and ${shares[2].toFixed(1)} water.</p>`).join("")}
      <p><b>Cities</b> are urban agglomerations mapped using UN DESA coordinates and mid-2026 population projections.
      A city’s state comes from its UN location. When two agglomerations fall in one hex, the larger one is shown. India's population is the
      official projection for 1 March 2026 (Technical Group on Population Projections, MoHFW).</p>
      <h4>Controls</h4>
      <p>Drag or arrow keys / WASD to pan · scroll, +/– or double-click to zoom · click a city or a state to open it ·
      / or ⌘K to search · L to cycle lenses · ? for all shortcuts · Esc to close.</p>
      <p>The address bar always holds a link to what you're looking at (lens, selection and view); use <i>Share</i> to copy it
      or to download a picture.</p>
`,
    Yields: () => `<p>Yield points use the scales shown in each entry. Map panels and national reports show
      underlying values and flag IndiaCiv estimates.</p>`,
    States: () => `
      <p>Click any land hex without a city to open its state or union territory. The borders are today's 28 states and
      8 union territories, from DataMeet's community maps (unofficial).</p>
      <p><b>Population, sex ratio and age</b> use the Technical Group (MoHFW) projections for 1 March 2026.
      State and national growth compare the projected totals on 1 March 2025 and 1 March 2026. The seven smaller
      North-East states share one combined age and health profile. WorldPop supplies 2026 age estimates
      for Goa, Andaman &amp; Nicobar, Chandigarh, Puducherry, Lakshadweep and Dadra and Nagar Haveli and Daman and Diu.</p>
      <p>Every union territory and each detached part of Puducherry and of Dadra and Nagar Haveli and Daman and Diu
      has a tile. When a part would have no tile, it takes the hex it overlaps most. Detached islands without a
      land hex get one based on the Survey of India outline.</p>
      ${data.states ? "" : `<p class="muted">This data build has no states.json, so state panels show names and cities only.</p>`}`,
    Terrain: () => `
      <p>The base describes the climate or water class. Relief describes the shape of the ground.
      Features show vegetation, landforms and sites that can coexist on the same tile.</p>
      <p>${esc(data.world.tables?.notes?.relief || "Relief uses mean elevation and the roughness of the samples inside each hex.")}</p>
      <p>Shading uses elevation differences with neighbouring hexes, lit from the north-west.
      Neighbouring countries (Natural Earth) are drawn under light fog for context. India’s extent follows the Survey of India outline.</p>
      ${data.world.base ? "" : `<p>Each hex averages its ETOPO1 elevation samples. Relief uses their mean
      elevation and roughness (the standard deviation).</p>
      ${Array.isArray(data.world.cover) ? `<p>Dominant land cover is the largest group among land samples
      inside the hex. Symbols show the mix. Trees scale with the forest share. Fields, reeds, shrubs and
      grass tufts mark farmland, wetland, scrub and grassland.</p>` :
      "<p>This build has no land-cover layer. Land is coloured by elevation.</p>"}`}`,
    Lenses: () => `
      <p><b>Population</b> is estimated per
      district: each district's census count grown at its state's projected rate to 1 March 2026, over its area. Each
      hex is sampled at 7 points and takes the mean of the districts under them, so a hex split between two districts
      gets a blend. A small district that no sample hits is blended into the hex holding its centre by its share of
      the hex's area. State, union territory and health lenses show the region’s projection or estimate across its hexes.</p>
      <p>The city population and growth lenses colour only city hexes. They show the UN mid-2026 population projection for each urban
      agglomeration and its projected growth from 1 July 2025 to 1 July 2026.</p>
      <p><b>Health</b> uses IndiaCiv estimates for 2026. For each indicator, we place the two Technical Group
      five-year averages at their midpoints and interpolate linearly, three-fifths of the way from the earlier
      midpoint to the later one. Values with a missing endpoint stay blank.</p>
      <p>The legend shows how many hexes fall at each value. Hover or drag on it to show only that range on the map.</p>
`,
    Resources: () => `
      <p>Press <b>R</b> to show or hide resource markers. The Resource group selector uses this legend.
      Zoom in to see more locations. Hover or tap a marker for its period and source.</p>
      <p>IndiaCiv estimates place crop markers on representative tiles within documented growing areas.
      These markers show where a crop is grown. Power and mine figures shown as capacities use rated or design capacity.</p>`,
    Trade: () => {
      const trade = data.infrastructure?.trade;
      if (!trade) return "";
      return `<p>Turn on <b>Trade</b> in Map layers. Amber lines follow the operating Eastern and Western
        Dedicated Freight Corridors on the OpenStreetMap rail grid. © OpenStreetMap contributors, ODbL 1.0.</p>
        <p>Cyan branches show domestic coastal cargo handled by each major port authority. Width uses a
        square-root scale so smaller ports stay readable. The shared dashed sea lane is schematic and carries
        no cargo weight. Hover over a branch for its port and volume.</p>
        <p>${esc(trade.label)} · ${esc(trade.status)} · Ministry of Ports, Shipping and Waterways.
        The Kolkata and Haldia authority has one combined branch at the mouth of the Hooghly.</p>`;
    },
    Railways: () => {
      if (!data.infrastructure?.freight) return "";
      const { freight, vintage } = data.infrastructure;
      return `
        <p>The ${esc(vintage.network)} OpenStreetMap snapshot supplies operating rail lines, expressways,
        national highways and mapped port locations. The national view shows trunk rail corridors,
        expressways and Golden Quadrilateral highways. Zoom in for other main lines and secondary tracks.
        Parallel tracks can share a hex link. © OpenStreetMap contributors, ODbL 1.0.</p>
        <p>Major port markers show rank and the coastal and overseas shares of cargo for ${esc(freight.label)}.
        IndiaCiv divides the March report’s coastal cargo by total cargo for each authority.
        Kolkata includes both Kolkata and Haldia docks. The Ministry of Ports, Shipping and Waterways supplies the advance estimates.
        Named port localities are matched by authority or facility ID. State and UT labels join the facility coordinates to DataMeet state boundaries, with a coastal placement fallback.
        Airport markers use OurAirports
        size classes from ${esc(vintage.airports)}.</p>
        <h4>Originating freight by railway</h4>
        <p>${esc(freight.label)} · ${esc(freight.unit)} · Ministry of Railways via Press Information Bureau</p>
        <table>
          <tr><th scope="col">Railway</th><th scope="col">Freight loaded</th></tr>
          ${freight.rows.map(([code, name, amount]) =>
            `<tr><td>${esc(name)} (${esc(code)})</td><td class="num">${amount.toLocaleString("en-IN", freightDigits)}</td></tr>`).join("")}
          <tr><th scope="row">India</th><td class="num">${freight.total.toLocaleString("en-IN", freightDigits)}</td></tr>
        </table>
        <h4>Transport sources</h4>
        <ul>${data.infrastructure.sources.map((id) => `<li>${esc(srcName(id))}</li>`).join("")}</ul>`;
    },
    Wonders: () => `
      <p>Explore built landmarks and natural sites across India, plus Mount Kailash in Tibet.
      Press <b>W</b> to show or hide the layer. Search for a wonder or click its marker for details.</p>
      <p>The November 2026 inventory includes UNESCO inscriptions, wetlands, and other sites chosen for regional
      coverage. The derived wonder data carries the ${external(data.wonders?.license_url, "CC BY-SA 4.0 licence")}.</p>`,
    Rivers: () => `
      <p>Rivers follow hex edges. Larger streams have wider channels. Hover over a named river or lake to identify it.</p>
      <p>River courses come from OpenStreetMap and Natural Earth. Channel width follows a cartographic
      rank by named course. Lake and reservoir outlines come from ${esc(srcName("hydrolakes"))} and
      © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>.</p>
`,
    "Protected land": () => `
      <p>Green tint marks hexes with at least 30% coverage by a mapped Ramsar wetland, national park or tiger
      reserve. Dots mark located sites without a qualifying hex. Dots scale with the published site area, and wetland
      outlines appear as you zoom in.</p>
      <p>The October 2026 Ramsar list supplies site locations, areas and available published boundaries.
      Park and tiger reserve designations come from WII and NTCA. © OpenStreetMap contributors supply
      available park and reserve geometry and fallback locations under ODbL 1.0.
      Wikidata supplies additional point locations under CC0. An OpenStreetMap extent must be within
      25% of the official area to contribute to the tint or Explorer shares.</p>
      <p>Explorer reports the share of each DataMeet state or district covered by the union of available extents
      from the 2026 snapshots. Point markers contribute no area. These shares describe mapped coverage
      and can be lower than legal protected-area totals.</p>`,
  };
}
