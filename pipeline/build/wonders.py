"""Project the IC-8 point inventory onto the current hex grid."""
import json
import math
from collections import Counter

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.source import osm_notice
from ..core.paths import WEB_DATA
from ..india.science_sources import ROSTER, research_points
from ..india.wonder_visitation import INTERIM as VISITATION, PERIOD as VISIT_PERIOD, SOURCE as VISIT_SOURCE
from ..core.store import load_interim, write_web
from ..india.wonders import CREDITS, LICENSE, LICENSE_URL, SOURCE

REQUIRES = ["_world", SOURCE, VISITATION, "datameet", "protected_land.json", "protected_ramsar.json"]
PRODUCES = ["wonders.json"]
PARK_LIMIT = 5
PARK_RULE = "national_park"
RESEARCH_RULE = "research_inventory"
RESEARCH_PERIOD = "27 November 2026"
RESEARCH_CLASSES = {"IISc", "IIT", "IISER"}
FEATURED_CAMPUSES = {"IISc", "IIT Delhi"}
PARK_ART = {
    "wii-la-hemis": ("peak", "High ridges and narrow valleys shape this cold-desert park in Ladakh."),
    "wii-rj-desert": ("desert", "Low dunes, grassland and sparse scrub make up this protected stretch of the Thar."),
    "wii-uk-gangotri": ("peak", "Glaciers and exposed ridges frame the upper Bhagirathi valley."),
    "wii-jk-kishtwarhighaltitude": ("peak", "Steep valleys climb from forest into the alpine terrain of the western Himalaya."),
    "wii-ar-namdapha": ("forest", "Forest climbs from the Noa-Dihing river valley into the eastern Himalayan foothills."),
}
RULE_LABELS = {
    "owner_named": "Selected landmarks", PARK_RULE: "National parks", RESEARCH_RULE: "Research institutions",
}
RULES = {
    "owner_named": "Selected project landmarks.",
    "unesco_inscribed": "Inscribed on the UNESCO World Heritage List.",
    "asi_domestic_top10": f"Selected from ASI ticketed monuments in {VISIT_PERIOD}.",
    "unesco_tentative_sample": "Selected from India's UNESCO Tentative List.",
    "ramsar_sample": "Selected from the Ramsar wetland inventory.",
    "gvp_active_volcano": "Active volcano in the Smithsonian Global Volcanism Program catalogue.",
    "regional_sample": "Selected for regional coverage and distinctive landscapes or architecture.",
    PARK_RULE: f"The {PARK_LIMIT} largest national parks by published area in the pinned WII inventory. Ties use site ID.",
    RESEARCH_RULE: "IISc, IITs and IISERs with verified locations in the Science inventory. "
                   "Alphabetical order within each institution class.",
}
MOTIFS = {
    "burial-mound": "mound", "church": "basilica", "civic": "civic", "domed-tomb": "domed-tomb",
    "excavated-rock": "rock-cave", "forest": "forest", "fort": "rampart", "gateway": "memorial",
    "geology": "rock-cave", "historic-quarter": "quarter", "lighthouse": "coast",
    "living-root-bridge": "root-bridge", "mountain": "peak", "palace": "palace", "railway": "railway",
    "ruins": "ruins", "salt-flat": "salt-flat", "sculpture": "statue", "stepwell": "stepwell",
    "stupa": "stupa", "temple": "temple-north", "tower": "minaret", "volcanic": "volcano",
    "waterbody": "lake", "waterfall": "falls", "wetland": "wetland",
}
SITE_MOTIFS = {
    "whc-252": "taj-mahal", "statue-of-unity": "statue-of-unity", "jatayu": "jatayu",
    "india-gate": "india-gate", "gateway-of-india": "gateway-of-india", "hawa-mahal": "hawa-mahal",
    "mount-kailash": "kailash", "whc-246": "konark-wheel", "golden-temple": "sikh-shrine",
    "whc-250": "vimana", "whc-249": "vimana", "whc-241": "vimana", "lepakshi": "vimana",
    "whc-239": "temple-deccan", "whc-1570": "temple-deccan", "whc-1670": "temple-deccan",
    "dzu": "valley", "morni": "valley", "whc-452": "mangrove", "charminar": "charminar",
    "st-marys": "basalt",
}
SITE_LABELS = {
    "whc-1321": "Chandigarh Capitol Complex",
    "whc-1480": "Mumbai Art Deco and Gothic Ensembles",
}
STATE_ALIASES = {"Andaman and Nicobar Islands": "Andaman & Nicobar", "Jammu and Kashmir": "Jammu & Kashmir"}


def draw_point(x, y, cell, grid, owner, placed):
    """Find room for a sprite while preserving the anchor cell's owner."""
    territory = owner[cell]
    if territory < 0:
        return x, y  # Keep foreign and water anchors at their precise coordinates.
    spacing = 0.72 * grid.radius
    nearby = [(row["draw_x"], row["draw_y"]) for row in placed
              if math.hypot(row["draw_x"] - x, row["draw_y"] - y) < 1.6 * grid.radius]
    best = (x, y)
    clearance = min((math.hypot(x - px, y - py) for px, py in nearby), default=math.inf)
    if clearance >= spacing:
        return best
    for fraction in (0.18, 0.36, 0.54, 0.69, 0.84):
        radius = fraction * grid.radius
        for bearing in range(90, 450, 30):
            angle = math.radians(bearing)
            px = round(x + radius * math.cos(angle), 6)
            py = round(y + radius * math.sin(angle), 6)
            candidate = grid.cell_at(px, py)
            if candidate < 0 or owner[candidate] != territory:
                continue
            nearest = min(math.hypot(px - ox, py - oy) for ox, oy in nearby)
            if nearest >= spacing:
                return px, py
            if nearest > clearance:
                best, clearance = (px, py), nearest
    return best


def place_wonders(rows, grid, owner, project, states):
    placed = []
    ranks = Counter()
    order = {rule: index for index, rule in enumerate(RULES)}
    for row in sorted(rows, key=lambda p: (min(order[tag] for tag in p["selection_rules"]), p["id"])):
        x, y = project(row["lon"], row["lat"])
        x, y = round(x, 6), round(y, 6)
        cell = grid.cell_at(x, y)
        foreign = row["foreign_side"]
        if cell < 0 or (foreign and owner[cell] != -2):
            raise ValueError(f"{row['id']}: invalid wonder cell {cell}")
        draw_x, draw_y = draw_point(x, y, cell, grid, owner, placed)
        state_name = row["state"]
        state = None if foreign else states[STATE_ALIASES.get(state_name, state_name)]
        tags = row["selection_rules"]
        rule = next(key for key in RULES if key in tags)
        ranks[rule] += 1
        name = "Mount Kailash (Tibet)" if row["id"] == "mount-kailash" else row["name"]
        short = name if foreign else row.get("short") or SITE_LABELS.get(row["id"], name)
        placed.append({
            "id": row["id"], "name": name, "short": short,
            "kind": "landmark" if row["kind"] == "built" else "natural",
            "subtype": row["subtype"], "motif": SITE_MOTIFS.get(row["id"], MOTIFS[row["motif_group"]]),
            "description": row["description"], "era": row["era"], "foreign_side": foreign,
            "state": state, "location": state_name, "county": None, "cbsa": None,
            "lat": row["lat"], "lon": row["lon"], "x": x, "y": y, "cell": cell, "cells": None,
            "draw_x": draw_x, "draw_y": draw_y,
            "rule": rule, "rank": ranks[rule], "selection_rules": tags, "metrics": None,
            "unesco_id": row.get("unesco", {}).get("id"), "references": row.get("sources", {}),
        })
    return placed


def select_parks(sites):
    parks = (s for s in sites if s["designation"] == "National park" and s.get("area_ha"))
    return sorted(parks, key=lambda s: (-s["area_ha"], s["id"]))[:PARK_LIMIT]


def select_research(points):
    eligible = sorted((p for p in points if p["kind"] in RESEARCH_CLASSES),
                      key=lambda p: (p["kind"], p["name"].casefold()))
    counts = Counter(p["kind"] for p in eligible)
    ranks = Counter()
    rows = []
    for point in eligible:
        kind = point["kind"]
        ranks[kind] += 1
        rows.append(dict(point, rank=ranks[kind], institution_count=counts[kind]))
    return rows


def attach_protection(wonders, sites):
    covers = {}
    linked_wetlands = {site["id"]: site["wonder"] for site in sites if site["id"].startswith("rsis-")}
    for site in sites:
        wonder = site.get("wonder") or linked_wetlands.get(site.get("ramsar_id"))
        if wonder and site["cells"]:
            cover = covers.setdefault(wonder, {"cells": set(), "sources": set()})
            cover["cells"].update(site["cells"])
            cover["sources"].add("rsis_protected" if site["id"].startswith("rsis-") and not site.get("ramsar_id")
                                 else "osm_protected")
    for row in wonders:
        if cover := covers.get(row["id"]):
            row["cells"] = sorted(cover["cells"])
            row["extent_sources"] = sorted(cover["sources"])


def add_rule_wonders(wonders, protected, points, world, grid, project):
    states = dict(zip(world["states"], world["state_names"]))
    owner = world["owner"]
    roster = {name: (state, locality) for rows in ROSTER.values() for name, state, locality in rows}

    def append(site_id, name, state, x, y, rule, rank, kind, motif, description, period, metrics,
               sources, subtype, cells=None, lon=None, lat=None):
        cell = grid.cell_at(x, y)
        if cell < 0:
            raise ValueError(f"{site_id}: invalid wonder anchor")
        draw_x, draw_y = draw_point(x, y, cell, grid, owner, wonders)
        wonders.append({
            "id": site_id, "name": name, "short": name, "state": state, "location": states[state],
            "x": x, "y": y, "cell": cell, "draw_x": draw_x, "draw_y": draw_y, "cells": cells or None,
            "lat": lat, "lon": lon, "foreign_side": False, "county": None, "cbsa": None,
            "rule": rule, "rank": rank, "kind": kind, "motif": motif, "description": description,
            "period": period, "estimated": False, "sources": sources, "selection_rules": [rule],
            "metrics": metrics, "era": period, "subtype": subtype,
        })

    by_id = {row["id"]: row for row in wonders}
    for rank, site in enumerate(select_parks(protected), 1):
        if site["cell"] is None:
            continue
        source = "wikidata_protected" if (site["source"] or "").startswith("wikidata:") else "osm_protected"
        metrics = {"area_km2": site["area_ha"] / 100, "protected_id": site["id"]}
        sources = ["wii_protected", source]
        if existing := by_id.get(site["wonder"]):
            existing.update(rule=PARK_RULE, rank=rank, period=site["period"], estimated=False,
                            metrics=metrics, sources=sources)
            existing["selection_rules"].append(PARK_RULE)
            continue
        motif, description = PARK_ART.get(site["id"], ("forest", f"A notified national park in {states[site['state']]}."))
        append(f"park-{site['id']}", site["name"], site["state"], site["x"], site["y"], PARK_RULE, rank,
               "natural", motif, description, site["period"], metrics, sources, "National park", site["cells"])
        if site["cells"]:
            wonders[-1]["extent_sources"] = ["osm_protected"]

    descriptions = {
        "IISc": "The Bengaluru campus brings science and engineering research together with postgraduate teaching.",
        "IIT": "An Indian Institute of Technology campus for engineering, science and research.",
        "IISER": "An Indian Institute of Science Education and Research campus that combines science teaching and research.",
    }
    for point in select_research(points):
        name, kind = point["name"], point["kind"]
        state, locality = roster[name]
        lon, lat = point["lon"], point["lat"]
        x, y = (round(v, 6) for v in project(lon, lat))
        site_id = "research-" + "-".join(name.lower().split())
        motif = "research-campus" if name in FEATURED_CAMPUSES else "civic"
        append(site_id, name, state, x, y, RESEARCH_RULE, point["rank"], "university", motif,
               f"{locality}. {descriptions[kind]}", RESEARCH_PERIOD,
               {"institution_count": point["institution_count"], "institution_class": kind},
               ["research_campuses", "research_points"], kind, lon=lon, lat=lat)
        wonders[-1]["references"] = {"location": {"url": point["url"]}}


def wonder_document(world, data, protected=(), wetlands=(), points=()):
    grid = HexGrid(**world["grid"])
    project = MapProjection(**world["projection"])
    wonders = place_wonders(data["wonders"], grid, world["owner"], project,
                            dict(zip(world["state_names"], world["states"])))
    attach_protection(wonders, [*protected, *wetlands])
    add_rule_wonders(wonders, protected, points, world, grid, project)
    return {
        "version": 1, "vintage": data["as_of"], "license": LICENSE, "license_url": LICENSE_URL,
        "sources": [info.id for info in CREDITS],
        "osm_license": osm_notice("OpenStreetMap-derived landmark anchors and protected area extents"),
        "rules": [{"id": key, "kinds": (["university"] if key == RESEARCH_RULE else
                  ["natural"] if key == PARK_RULE else ["natural", "landmark"]),
                   "label": RULE_LABELS.get(key, key.replace("_", " ").capitalize()),
                   "ranked": False, "text": phrase} for key, phrase in RULES.items()],
        "national": {}, "wonders": wonders,
    }


def add_visit_ranks(wonders, cohort):
    for row in wonders:
        if (rank := cohort["ranks"].get(row["id"])) is None:
            continue
        visit = {"rank": rank, "cohort_size": cohort["size"], "period": VISIT_PERIOD, "source": VISIT_SOURCE}
        row["metrics"] = {**(row["metrics"] or {}), "visitation": visit}
        sources = row.setdefault("sources", [])
        if VISIT_SOURCE not in sources:
            sources.append(VISIT_SOURCE)
        row["description"] += (f" Ranked {rank} of {cohort['size']} reporting ASI ticketed sites "
                               f"by domestic and foreign visits in {VISIT_PERIOD}.")


def protected_inventory(osm, wetlands):
    overlays = {site["ramsar_id"]: site for site in osm if site.get("ramsar_id")}
    sites = [site for site in osm if not site.get("ramsar_id")]
    for site in wetlands:
        shape = overlays.get(site["id"])
        sites.append({**site, **{key: shape.get(key) for key in ("cells", "rings", "source")}} if shape else site)
    result = []
    for site in sites:
        source = site.get("source") or ""
        area = site.get("area_ha")
        area_text = ""
        if area is not None:
            from .almanac import number
            area_text = f"Official area · {number(area / 100, 4)} km²"
        result.append({**site, "hover": [
            site.get("status") or site.get("designation"),
            area_text,
            " · ".join(filter(None, (site.get("authority"), site.get("period")))),
            "Location · Wikidata" if source.startswith("wikidata:") else
            "Mapped geography · © OpenStreetMap contributors" if source.startswith(("node/", "way/", "relation/")) else "",
        ]})
    return result


def build():
    try:
        data = load_interim(SOURCE)
    except FileNotFoundError as exc:
        raise FileNotFoundError("Import the snapshot with python3 -m pipeline.india.wonders .cache/IC-8-wonders.json") from exc
    from .yields import district_state_map

    datameet = load_interim("datameet")
    points = research_points(datameet, district_state_map(datameet))
    protected, wetlands = (json.loads((WEB_DATA / name).read_text())["sites"]
                           for name in ("protected_land.json", "protected_ramsar.json"))
    document = wonder_document(load_interim("_world"), data, protected, wetlands, points)
    document["protected"] = protected_inventory(protected, wetlands)
    add_visit_ranks(document["wonders"], load_interim(VISITATION))
    write_web("wonders.json", document)


def check(web_dir):
    path = web_dir / "wonders.json"
    catalog = web_dir / "sources.json"
    sources = {item["id"]: item for item in json.loads(catalog.read_text())} if catalog.is_file() else {}
    if not path.is_file():
        level = "FAIL" if SOURCE in sources else "NOTE"
        return [(level, "wonders.json: missing; import the IC-8 snapshot and build wonders")]
    doc = json.loads(path.read_text())
    rows = doc["wonders"]
    kinds = Counter(row["kind"] for row in rows if not row["id"].startswith(("park-", "research-")))
    if len({row["id"] for row in rows}) != len(rows) or kinds != {"landmark": 55, "natural": 26}:
        return [("FAIL", "wonders.json: duplicate IDs or original inventory size changed")]
    if (doc["license"] != LICENSE or doc.get("license_url") != LICENSE_URL
            or any(key not in sources for key in doc["sources"]) or SOURCE not in doc["sources"]
            or any(sources.get(info.id, {}).get("license_url") != LICENSE_URL for info in CREDITS
                   if info.license == LICENSE)):
        return [("FAIL", "wonders.json: source credits or licence missing")]
    world = json.loads((web_dir / "world.json").read_text())
    grid = HexGrid(**world["grid"])
    rules = {rule["id"]: rule["kinds"] for rule in doc["rules"]}
    states = {state["abbr"] for state in world["states"]}
    foreign = [row["id"] for row in rows if row["foreign_side"]]
    if foreign != ["mount-kailash"] or {row["state"] for row in rows if not row["foreign_side"]} != states:
        return [("FAIL", "wonders.json: expected all Indian jurisdictions and Mount Kailash as the only foreign site")]
    issues = []
    for row in rows:
        cell = row["cell"]
        coords = all(type(row[key]) in (int, float) and math.isfinite(row[key]) for key in (("x", "y") if row["rule"] == PARK_RULE else ("x", "y", "lat", "lon")))
        draw_coords = [row.get("draw_x"), row.get("draw_y")]
        draw_cell = grid.cell_at(*draw_coords) if all(type(v) in (int, float) and math.isfinite(v) for v in draw_coords) else -1
        if (type(cell) is not int or not 0 <= cell < grid.size or not coords or grid.cell_at(row["x"], row["y"]) != cell
                or draw_cell < 0 or world["owner"][draw_cell] != world["owner"][cell]
                or (row["foreign_side"] and (row["state"] is not None or world["owner"][cell] != -2))
                or row["kind"] not in rules.get(row["rule"], [])
                or not all(isinstance(row[key], str) and row[key] for key in
                           ("name", "short", "subtype", "motif", "description", "location", "era"))
                or any(row[key] is not None for key in ("county", "cbsa"))
                or any(key not in sources for key in row.get("sources", []) + row.get("extent_sources", []))
                or (row["cells"] is not None and (
                    row["cells"] != sorted(set(row["cells"]))
                    or any(type(c) is not int or not 0 <= c < grid.size for c in row["cells"])))
                or (row["kind"] == "university" and (row["rule"] != RESEARCH_RULE
                    or (row["metrics"] or {}).get("institution_class") not in RESEARCH_CLASSES
                    or not any(name == row["name"]
                               for name, _, _ in ROSTER[(row["metrics"] or {})["institution_class"]])))):
            issues.append(row["id"])
    if issues:
        return [("FAIL", f"wonders.json: invalid point records: {', '.join(issues)}")]
    protected_path = web_dir / "protected_land.json"
    if protected_path.is_file():
        parks = select_parks(json.loads(protected_path.read_text())["sites"])
        expected = [(rank, site["id"], site["area_ha"] / 100) for rank, site in enumerate(parks, 1)
                    if site["cell"] is not None]
        actual = [(row["rank"], row["metrics"]["protected_id"], row["metrics"]["area_km2"])
                  for row in rows if row["rule"] == PARK_RULE]
        if actual != expected:
            return [("FAIL", "wonders.json: park ranks differ from the official-area selection")]
    research = [row for row in rows if row["rule"] == RESEARCH_RULE]
    counts = Counter(row["metrics"]["institution_class"] for row in research)
    if counts != {kind: len(ROSTER[kind]) for kind in RESEARCH_CLASSES} or any(
        row["metrics"]["institution_count"] != counts[row["metrics"]["institution_class"]] for row in research
    ):
        return [("FAIL", "wonders.json: invalid research institution counts")]
    for kind, count in counts.items():
        cohort = sorted((row for row in research if row["metrics"]["institution_class"] == kind),
                        key=lambda row: row["name"].casefold())
        if [row["rank"] for row in cohort] != list(range(1, count + 1)):
            return [("FAIL", f"wonders.json: invalid {kind} inventory order")]
    return [("PASS", f"wonders.json: {len(rows)} unique projected wonders and civilian research sites")]
