// City View "Citizens" rows: the metro's people as rows of small figures (citizens.json, ACS 1-year).
//
//   citizensHtml(m, data) → HTML      the rows (placeholders for the figure canvases)
//   mountCitizens(host, m, data)       paints the figures and wires the hover / focus read-out
//
// Each row: N figures (workforce 20, ages 10, commute 10 from the file; education and origins 10, rounded here with
// the same largest-remainder method), a caption ("each figure ≈ 72K workers"), a read-out line that a hovered or
// focused figure fills ("1 in 7 workers in San Jose is an engineer, coder or scientist (India: 1 in 14)"), and a thin
// U.S. bar for comparison. A row Census left out is said so, never drawn as zeros.
import { esc, pct, periodLabel } from "../../format.js";
import { compact, int } from "./fmt.js";
import { CATEGORY_COLOR, figureCanvas, loadPainter } from "./figures.js";

const ROWS = [
  { id: "workforce", title: "Workforce", sub: "by occupation", noun: ["worker", "workers"], n: null },
  { id: "age", title: "Generations", sub: "by age", noun: ["resident", "residents"], n: null },
  { id: "commute", title: "Commute", sub: "how workers get to work", noun: ["worker", "workers"], n: null },
  { id: "education", title: "Education", sub: "adults 25 and over", noun: ["adult", "adults 25+"], n: 10 },
  { id: "nativity", title: "Origins", sub: "where residents were born", noun: ["resident", "residents"], n: 10 },
];

// [singular verb phrase, plural verb phrase] per category, for "1 in 7 workers in X is …" / "7 in 10 … are …".
const PHRASE = {
  workforce: {
    executive: ["is an executive or manager", "are executives or managers"],
    engineer: ["is an engineer, coder or scientist", "are engineers, coders or scientists"],
    scholar: ["is a teacher, lawyer, artist or media worker", "are teachers, lawyers, artists or media workers"],
    healer: ["works in health care", "work in health care"],
    service: ["works in personal services or sales", "work in personal services or sales"],
    clerk: ["works in a clerical occupation", "work in clerical occupations"],
    farmer: ["farms, fishes or works in forestry", "farm, fish or work in forestry"],
    builder: ["builds, installs or repairs", "build, install or repair"],
    maker: ["works in a factory, transport or a warehouse", "work in factories, transport or warehouses"],
  },
  age: {
    child: ["is a child (under 18)", "are children (under 18)"],
    young: ["is a young adult (18–34)", "are young adults (18–34)"],
    midlife: ["is middle-aged (35–64)", "are middle-aged (35–64)"],
    elder: ["is 65 or older", "are 65 or older"],
  },
  commute: {
    drove_alone: ["drives to work alone", "drive to work alone"],
    carpool: ["carpools to work", "carpool to work"],
    transit: ["takes public transit to work", "take public transit to work"],
    walk: ["walks to work", "walk to work"],
    other: ["travels by another reported mode", "travel by another reported mode"],
    home: ["works from home", "work from home"],
  },
  education: {
    less_than_hs: ["has below-secondary attainment", "have below-secondary attainment"],
    high_school: ["has secondary or higher secondary attainment", "have secondary or higher secondary attainment"],
    some_college: ["has a diploma below degree level", "have a diploma below degree level"],
    bachelors: ["has a degree or higher qualification", "have a degree or higher qualification"],
    graduate: ["has a master's, professional degree or doctorate", "have a master's, professional degree or doctorate"],
  },
  nativity: {
    born_in_state: ["was born in the state they live in", "were born in the state they live in"],
    other_state: ["was born in another Indian state", "were born in another Indian state"],
    native_abroad: ["was born a U.S. citizen abroad or in a U.S. territory", "were born U.S. citizens abroad or in U.S. territories"],
    foreign_born: ["was born in another country", "were born in another country"],
  },
};

// Short legend labels (the file's labels are long).
const SHORT = {
  workforce: { executive: "Executives", engineer: "Engineers", scholar: "Teachers & arts", healer: "Health", service: "Service",
    clerk: "Clerical", farmer: "Farm", builder: "Builders", maker: "Makers & movers" },
  age: { child: "Under 18", young: "18–34", midlife: "35–64", elder: "65+" },
  commute: { drove_alone: "Drive alone", carpool: "Carpool", transit: "Transit", walk: "Walk", other: "Bike & other", home: "From home" },
  education: { less_than_hs: "Below secondary", high_school: "Secondary", some_college: "Diploma", bachelors: "Degree or higher", graduate: "Graduate" },
  nativity: { born_in_state: "This state", other_state: "Other Indian state", native_abroad: "U.S. citizen abroad", foreign_born: "Other country" },
};

/** Largest-remainder rounding of counts into n figures (the pipeline's method, for rows without figures). */
export function largestRemainder(counts, keys, n) {
  const tot = keys.reduce((a, k) => a + (counts[k] || 0), 0);
  if (!(tot > 0)) return null;
  const raw = keys.map((k) => ((counts[k] || 0) / tot) * n);
  const out = raw.map(Math.floor);
  let left = n - out.reduce((a, v) => a + v, 0);
  const order = raw.map((v, j) => [v - Math.floor(v), j]).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  for (let k = 0; k < left; k++) out[order[k][1]]++;
  return Object.fromEntries(keys.map((k, j) => [k, out[j]]));
}

/** "1 in 7", "3 in 10", "fewer than 1 in 1,000". */
export function oneIn(share) {
  if (share == null || !Number.isFinite(share)) return null;
  if (share <= 0) return { text: "none", plural: true };
  if (share < 0.001) return { text: "fewer than 1 in 1,000", plural: false };
  if (share >= 0.3) {
    const k = Math.round(share * 10);
    return k >= 10 ? { text: "nearly all", plural: true } : { text: `${k} in 10`, plural: k !== 1 };
  }
  const n = Math.round(1 / share);
  return { text: `1 in ${int(n)}`, plural: false };
}

function sentence(rowId, key, share, natShare, cityName, noun) {
  const a = oneIn(share);
  if (!a) return "";
  const ph = PHRASE[rowId]?.[key] || ["is in this group", "are in this group"];
  const us = oneIn(natShare);
  const lead = a.text.charAt(0).toUpperCase() + a.text.slice(1);
  return `${lead} ${noun[1]} in ${cityName} ${a.plural ? ph[1] : ph[0]}${us ? ` (India: ${us.text})` : ""}`;
}

function rowModel(rowDef, row, nat, groups, figuresN) {
  const keys = (groups[rowDef.id] || []).map((g) => g.key);
  const n = figuresN[rowDef.id] ?? rowDef.n ?? 10;
  const figs = row.figures || largestRemainder(row.counts || {}, keys, n);
  const natFigs = nat?.figures || (nat ? largestRemainder(nat.counts || {}, keys, n) : null);
  return { keys, n, figs, natFigs };
}

// Specialists by row/key from the file (ratios from unrounded shares).
function specMap(city) {
  const m = new Map();
  for (const s of city?.specialists || []) m.set(`${s.row}|${s.key}`, s);
  return m;
}

/** The Citizens rows. data = citizens.json (or null / undefined while loading). */
export function citizensHtml(m, data) {
  const c = m.city;
  if (data === undefined) return `<p class="muted cv-note">Loading the citizen mix…</p>`;
  if (!data || !data.cities) return `<p class="muted cv-note">The citizen mix is not available.</p>`;
  const row0 = data.cities[c.id];
  if (!row0) {
    return `<p class="muted cv-note">Citizen figures unavailable for ${esc(c.name)}.</p>`;
  }
  const nat = data.national || {};
  const groups = data.groups || {};
  const specs = specMap(row0);
  const label = Object.fromEntries(Object.entries(groups).map(([r, gs]) => [r, Object.fromEntries(gs.map((g) => [g.key, g.label]))]));

  // Headline: median age, degrees, foreign-born, and the "great person" call-out (the strongest specialist).
  const med = row0.age?.median, usMed = nat.age?.median;
  const ba = row0.education?.bachelors_plus, usBa = nat.education?.bachelors_plus;
  const fb = row0.nativity?.foreign_born ?? row0.nativity?.shares?.foreign_born;
  const usFb = nat.nativity?.foreign_born ?? nat.nativity?.shares?.foreign_born;
  const chip = (v, us, fmt, lbl, tip) => (v == null ? "" : `<div class="cv-cz-chip" title="${esc(tip)}"><b>${fmt(v)}</b><span>${esc(lbl)}${periodLabel(lbl === "have a degree" ? row0.education : lbl === "born abroad" ? row0.nativity : row0.age, " · ")}</span>${us != null ? `<small>India ${fmt(us)}</small>` : ""}</div>`);
  const top = (row0.specialists || []).find((s) => s.ratio >= (data.rule?.specialist_high ?? 1.5));
  const topRow = ROWS.find((r) => r.id === top?.row);
  const great = top && topRow ? `<div class="cv-great" style="--fc:${esc(CATEGORY_COLOR[top.row]?.[top.key] || "#c9a45c")}">
      <span class="cv-great-fig" data-great="${esc(top.row)}|${esc(top.key)}" aria-hidden="true"></span>
      <div><small>Standout citizens</small><b>${esc(label[top.row]?.[top.key] || top.key)}</b>
      <span>${pct(top.share, 1)} of ${esc(topRow.noun[1])} here, ${pct(top.national, 1)} nationally: ${top.ratio.toFixed(1)}× India’s share${periodLabel(top, " · ")}.</span></div></div>` : "";

  const rows = ROWS.map((rd) => {
    const row = row0[rd.id];
    const head = `<div class="cv-cz-h"><b>${esc(rd.title)}</b><span>${esc(rd.sub)}${periodLabel(row, " · ")}</span></div>`;
    if (!row) return "";
    const { keys, n, figs, natFigs } = rowModel(rd, row, nat[rd.id], groups, data.figures || {});
    if (!figs) return `<div class="cv-cz-row missing" data-row="${rd.id}">${head}<p class="muted cv-note">No counts for this row.</p></div>`;
    const per = row.total / n;
    const cells = [];
    for (const k of keys) {
      for (let j = 0; j < (figs[k] || 0); j++) {
        const sp = specs.get(`${rd.id}|${k}`);
        const mark = sp ? (sp.ratio >= 1 ? "up" : "down") : "";
        // One tab stop per category (its first figure), not one per figure.
        cells.push(`<span class="cv-fig${mark ? ` ${mark}` : ""}" tabindex="${j ? -1 : 0}" role="img" data-k="${esc(k)}" aria-label="${esc(label[rd.id]?.[k] || k)}"></span>`);
      }
    }
    // Legend: every category, with its share, India’s share and a chevron for specialists. Categories that
    // round to no figure are still listed (greyed), so nothing silently disappears.
    const legend = keys.map((k) => {
      const sh = row.shares?.[k], us = nat[rd.id]?.shares?.[k];
      const sp = specs.get(`${rd.id}|${k}`);
      const chev = sp ? `<em class="${sp.ratio >= 1 ? "up" : "down"}" title="${sp.ratio.toFixed(1)}× India’s share">${sp.ratio >= 1 ? "▲" : "▼"}</em>` : "";
      return `<span class="cv-cz-k${figs[k] ? "" : " zero"}" data-k="${esc(k)}" title="${esc(label[rd.id]?.[k] || k)}: ${sh != null ? pct(sh, 1) : "–"}${us != null ? ` (India ${pct(us, 1)})` : ""}${figs[k] ? "" : ". Rounds to no figure."}"><i style="background:${esc(CATEGORY_COLOR[rd.id]?.[k] || "#888")}"></i>${esc(SHORT[rd.id]?.[k] || label[rd.id]?.[k] || k)} <small>${sh != null ? pct(sh, 0) : "–"}</small>${chev}</span>`;
    }).join("");
    // U.S. comparison bar (shares), aligned with the figures' order.
    const usBar = nat[rd.id]?.shares ? `<div class="cv-cz-us" title="India’s mix, same order"><span>India</span><div>${keys.map((k) => {
      const s = nat[rd.id].shares[k] || 0;
      return s > 0 ? `<i style="flex:${s};background:${esc(CATEGORY_COLOR[rd.id]?.[k] || "#888")}" title="${esc(SHORT[rd.id]?.[k] || label[rd.id]?.[k] || k)}: ${pct(s, 1)} in India"></i>` : "";
    }).join("")}</div></div>` : "";
    const cap = row.total == null
      ? `Each figure ≈ ${pct(1 / n)} of ${rd.noun[1]} · ${periodLabel(row, "", { plain: true })}`
      : `Each figure ≈ ${compact(per)} ${rd.noun[1]} · ${compact(row.total)} in all${row.estimated ? " · IndiaCiv estimate" : ""}`;
    const extra = rd.id === "age" && med != null ? ` · median age ${med.toFixed(1)}${usMed != null ? ` (India ${usMed.toFixed(1)})` : ""}` : "";
    return `<div class="cv-cz-row" data-row="${rd.id}" style="--n:${n}">${head}
      <div class="cv-figs" role="group" aria-label="${esc(rd.title)}: ${keys.filter((k) => figs[k]).map((k) => `${figs[k]} of ${n} ${SHORT[rd.id]?.[k] || label[rd.id]?.[k] || k}`).join(", ")}">${cells.join("")}</div>
      ${usBar}
      <div class="cv-cz-out" aria-live="polite" data-default="${esc(cap + extra)}">${esc(cap + extra)}</div>
      <div class="cv-cz-legend">${legend}</div>
    </div>`;
  }).join("");

  const unreliable = row0.reliable === false
    ? `<p class="cv-warn">Micropolitan area: the 1-year survey's margins of error are large here, so read these figures as rough.</p>` : "";
  return `
    <div class="cv-cz-top">
      ${chip(med, usMed, (v) => v.toFixed(1), "median age", "IndiaCiv estimate from WorldPop · mid-2026")}
      ${chip(ba, usBa, (v) => pct(v, 0), "have a degree", `Adults aged 25+ with a degree or higher qualification${periodLabel(row0.education, " · ", { plain: true })}`)}
      ${chip(fb, usFb, (v) => pct(v, 0), "born abroad", `Residents born outside India${periodLabel(row0.nativity, " · ", { plain: true })}`)}
    </div>
    ${great}
    ${unreliable}
    <div class="cv-cz${row0.reliable === false ? " unreliable" : ""}">${rows}</div>
    <p class="cv-note">Occupations, commute, education and birthplace use Census 2011 urban member district shares. Figures use classified categories with matching chart slots. Commute covers Census Other workers with a reported mode of travel. Generations use WorldPop age groups scaled to the UN mid-2026 projection, with ages 15–19 split proportionally. Figures are rounded (largest remainder) so each row adds up; hover or tap a figure for its share.${specs.size ? " ▲▼ = at least 1.5× or at most 0.67× India’s share." : ""}</p>`;
}

/** Paint the figure canvases and wire the read-outs. */
export function mountCitizens(host, m, data) {
  if (!host || !data?.cities?.[m.city.id]) return;
  const row0 = data.cities[m.city.id];
  const nat = data.national || {};
  const dpr = Math.min(3, Math.max(1, Math.round((devicePixelRatio || 1) * 2) / 2));
  const paintAll = () => {
    host.querySelectorAll(".cv-cz-row[data-row]").forEach((rowEl) => {
      const rid = rowEl.dataset.row;
      rowEl.querySelectorAll(".cv-fig").forEach((el) => {
        const src = figureCanvas(rid, el.dataset.k, 36, dpr);
        const cv = document.createElement("canvas");
        cv.width = src.width;
        cv.height = src.height;
        cv.getContext("2d").drawImage(src, 0, 0);
        el.replaceChildren(cv);
      });
    });
    const g = host.querySelector("[data-great]");
    if (g) {
      const [rid, k] = g.dataset.great.split("|");
      const src = figureCanvas(rid, k, 36, dpr);
      const cv = document.createElement("canvas");
      cv.width = src.width;
      cv.height = src.height;
      cv.getContext("2d").drawImage(src, 0, 0);
      g.replaceChildren(cv);
    }
  };
  paintAll();
  // Once the citizen painter (render/art/people.js) loads, repaint the figures.
  loadPainter().then(() => { if (host.isConnected) paintAll(); });

  host.querySelectorAll(".cv-cz-row[data-row]").forEach((rowEl) => {
    const rid = rowEl.dataset.row;
    const rd = ROWS.find((r) => r.id === rid);
    const row = row0[rid];
    const out = rowEl.querySelector(".cv-cz-out");
    if (!row || !out) return;
    const show = (k) => {
      rowEl.querySelectorAll("[data-k]").forEach((el) => el.classList.toggle("lit", el.dataset.k === k));
      rowEl.classList.toggle("focus", !!k);
      if (!k) {
        out.textContent = out.dataset.default;
        out.classList.remove("on");
        return;
      }
      const sh = row.shares?.[k], us = nat[rid]?.shares?.[k];
      out.innerHTML = `${esc(sentence(rid, k, sh, us, m.city.name, rd.noun))}<small>${sh != null ? pct(sh, 1) : "–"} here${us != null ? ` · ${pct(us, 1)} in India` : ""}${row.counts?.[k] != null ? ` · ≈${compact(row.counts[k])} people` : ""}${periodLabel(row, " · ")}</small>`;
      out.classList.add("on");
    };
    let pinned = null;
    rowEl.addEventListener("pointerover", (e) => {
      const el = e.target.closest("[data-k]");
      if (el && rowEl.contains(el)) show(el.dataset.k);
    });
    rowEl.addEventListener("pointerleave", () => show(pinned));
    rowEl.addEventListener("focusin", (e) => {
      const el = e.target.closest("[data-k]");
      if (el) show(el.dataset.k);
    });
    rowEl.addEventListener("focusout", () => show(pinned));
    // A tap pins the category (phones have no hover); another tap on it lets go.
    rowEl.addEventListener("click", (e) => {
      const el = e.target.closest("[data-k]");
      if (!el) return;
      pinned = pinned === el.dataset.k ? null : el.dataset.k;
      show(pinned);
    });
  });
}
