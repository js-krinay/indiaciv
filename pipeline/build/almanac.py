"""Adapt Indian inventories to the Almanac's existing name/rule table rows."""

import json
import math
import re
from collections import Counter

from ..core.paths import WEB_DATA
from ..core.store import write_web
from .almanac_text import NOTES, WONDER_NOTES
from .projection import NORTH_EAST

REQUIRES = ["world.json", "states.json", "cities.json", "nation.json", "lens_catalog.json",
            "resources.json", "wonders.json", "infrastructure.json", "protected_land.json",
            "protected_ramsar.json", "sources.json", "military.json"]
PRODUCES = ["almanac.json"]
RUN_LAST = True

FY26 = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"


def number(value, digits=2):
    whole, _, fraction = f"{value:.{digits}f}".partition(".")
    fraction = fraction.rstrip("0")
    sign = "-" if whole.startswith("-") else ""
    whole = whole.lstrip("-")
    groups = [whole[-3:]]
    whole = whole[:-3]
    while whole:
        groups.append(whole[-2:])
        whole = whole[:-2]
    return sign + ",".join(reversed(groups)) + ("." + fraction if fraction else "")


def make_entries(*, world, states=(), cities=(), wonders=None, lenses=None, nation=None,
                 resources=None, infrastructure=None, protected=(), sources=(), military=None):
    pages = {}
    source_names = {row["id"]: row["title"] for row in sources}
    lens_names = {row["id"]: row for row in (lenses or {}).get("lenses", [])}
    state_names = {row["abbr"]: row["name"] for row in world.get("states", []) if row.get("abbr")}
    wonders, nation, resources, infrastructure = (wonders or {}, nation or {}, resources or {}, infrastructure or {})
    types = {row["id"]: row for row in resources.get("types", [])}
    inventory = resources.get("summary", {})
    resource_periods = {}
    for item in resources.get("items", []):
        resource_periods.setdefault(item["type"], set()).add(item.get("period"))

    def add(page, group, name, *parts, sources=(), links=(), **extra):
        rows = pages.setdefault(page, {}).setdefault(group, [])
        facts = [part for part in parts if isinstance(part, dict)]
        credits = list(dict.fromkeys(source for source in sources if source))

        def caption(part):
            if isinstance(part, str):
                return part
            source = part.get("source")
            source_ids = source if isinstance(source, list) else [source]
            fields = [part["label"], part["formatted"], part["period"],
                      "IndiaCiv estimate" if part.get("estimated") else "", part.get("scope"),
                      *(source_names.get(s, s) for s in source_ids if s)]
            return " · ".join(field for field in fields if field)

        lines = [caption(part) for part in parts if part]
        if credits:
            lines.append(" · ".join(source_names.get(source, source) for source in credits))
        rows.append({"name": name, "rule": "\n".join(lines), "facts": facts,
                     "sources": credits, "links": list(links), **extra})

    def figure(label, value, unit, provenance, *, scope=""):
        period = provenance.get("period")
        if not period or not isinstance(value, (int, float)) or not math.isfinite(value):
            return None
        text = f"₹{number(value)}" if unit == "INR" else f"{number(value)} {unit}".rstrip()
        return {"label": label, "value": value, "formatted": text, "scope": scope, **provenance}

    grid = world["grid"]
    add("About this map", "How it's built", "India's hex grid",
        f"Lambert azimuthal equal-area, centred on 22° N, 82° E. "
        f"{grid['cols']}×{grid['rows']} hexes, each {grid['radius'] * 2} km corner to corner.",
        *NOTES["About this map"], sources=("soi_outline", "soi_political_map", "datameet"))
    add("Sources", "Credits", "usaciv · MIT licence",
        "IndiaCiv builds on usaciv by Andrej Karpathy.",
        links=({"url": "https://karpathy.ai/usaciv", "label": "usaciv"},
               {"url": "LICENSE", "label": "Read the MIT licence"}))
    for row in (world.get("tables") or {}).get("named_boundary_places", []):
        indian, foreign, water = row["shares"][:3]
        add("About this map", "How it's built", " and ".join(row["names"]),
            f"Hex {row['cell']}. Charted areas in km² · {number(indian, 1)} Indian land, "
            f"{number(foreign, 1)} neighbouring land and {number(water, 1)} water.")

    add("About this map", "Cities", "Urban agglomerations", *NOTES["Cities"],
        sources=("un_wup_cities", "tg_projections"))
    for row in cities:
        provenance = row.get("provenance", {}).get("population", {})
        sources = ["un_wup_cities"]
        growth_provenance = row.get("provenance", {}).get("projected_growth", {})
        growth = (row.get("projected_growth")
                  if all(meta.get("vintage") != "older" for meta in
                         (provenance, growth_provenance, row.get("provenance", {}).get("growth", {}))) else None)
        add("About this map", "Cities", row["name"],
            " · ".join(state_names.get(s, s) for s in row.get("states", [])),
            figure("Population", row.get("population"), "people", provenance),
            figure("Population rank in India", row.get("ranks", {}).get("population")
                   if provenance.get("vintage") != "older" else None, "", provenance),
            figure("Projected growth", growth * 100 if growth is not None else None, "%",
                   {**growth_provenance, "period": row.get("growth_period")}),
            sources=sources)

    rules = {row["id"]: row["text"] for row in wonders.get("rules", [])}
    if wonders.get("wonders"):
        add("About this map", "Wonders", "Wonder inventory", *NOTES["Wonders"],
            sources=("india_wonders", *wonders.get("sources", [])),
            links=[{"url": wonders.get("license_url"), "label": "CC BY-SA 4.0"}])
    for row in wonders.get("wonders", []):
        selection = [rules[key] for key in dict.fromkeys([row.get("rule"), *row.get("selection_rules", [])])
                     if key in rules]
        selection = [re.sub(r"FY 2025-26(?! \()", FY26, text) for text in selection]
        metrics = row.get("metrics") or {}
        period = row.get("period")
        area = (f"Official area · {number(metrics['area_km2'], 4)} km² · Area rank {row['rank']} · {period}"
                if period and metrics.get("area_km2") is not None and row.get("rank") is not None else "")
        order = (f"Class order · {row['rank']} of {metrics['institution_count']} mapped "
                 f"{metrics['institution_class']} sites · {period}"
                 if period and metrics.get("institution_count") is not None else "")
        inventory_order = (f"Inventory order · {row['rank']} · {period}"
                           if period and row.get("rank") is not None and not (area or order) else "")
        add("About this map", "Wonders", row["name"],
            " · ".join(filter(None, [row.get("kind"), (row.get("subtype") or "").replace("_", " "),
                                     row.get("location") or state_names.get(row.get("state")), period])),
            row.get("description"), row.get("era") if not period else None, WONDER_NOTES.get(row["id"], row.get("long_description")),
            *selection, area, order, inventory_order,
            f"Mapped extent · {number(len(row['cells']), 0)} protected land hexes" if row.get("cells") else "",
            sources=["india_wonders", *(row.get("sources") or []), *row.get("extent_sources", [])],
            links=[{"url": ref.get("url"), "label": kind.title() + (f" · {ref['license']}" if ref.get("license") else "")}
                   for kind, ref in (row.get("references") or {}).items()])

    add("States", "States and union territories", "Population and boundaries", *NOTES["States"],
        sources=("datameet", "soi_outline", "tg_projections", "worldpop_age"))
    for row in states:
        if not row or not row.get("abbr") or row["abbr"] == "00":
            continue
        sources = ["datameet", "tg_projections"]
        population = row.get("provenance", {}).get("population", {})
        profile = row.get("profile") or {}
        figures = [figure("Population", row.get("population"), "people", population),
                   figure("India population", (nation.get("nation") or {}).get("population"), "people",
                          {"period": "Projected for 1 March 2026", "source": "tg_projections"}
                          if nation.get("year") == 2026 else {}),
                   figure("Density", profile.get("density"), "people/km²", population),
                   figure("India density", (nation.get("profile") or {}).get("density"), "people/km²", population),
                   figure("Women per 1,000 men", profile.get("sex_ratio"), "", population),
                   figure("Projected growth", profile["growth"] * 100 if profile.get("growth") is not None else None,
                          "%", {"period": profile.get("growth_period"), "source": "tg_projections"})]
        for field, label, unit in [
            ("age_0_14", "Age 0–14", "%"), ("age_60", "Age 60 and over", "%"),
            ("median_age", "Median age", "years"), ("imr", "Infant mortality", "per 1,000 births"),
            ("tfr", "Total fertility", "births per woman"), ("life_female", "Life expectancy, women", "years"),
            ("life_male", "Life expectancy, men", "years"),
        ]:
            age = field.startswith("age_") or field == "median_age"
            estimate = not age or row.get("age_source") == "worldpop_age"
            provenance = ({"period": "2026" if estimate else population.get("period"),
                           "source": row.get("age_source"), "estimated": False} if age
                          else {"period": (profile.get("health") or {}).get("period"),
                                "source": "tg_projections", "estimated": True})
            scope = ("WorldPop estimate" if age and estimate else
                     "Combined North-East profile" if row["name"] in NORTH_EAST else "")
            figures.append(figure(label, profile.get(field), unit, provenance, scope=scope))
        for key, record in (row.get("metrics") or {}).items():
            lens = lens_names.get(key, {})
            value = record.get("value")
            unit = lens.get("unit", "")
            if lens.get("format") == "pct" and isinstance(value, (int, float)):
                value *= 100
                unit = "%"
            provenance = {k: record[k] for k in ("period", "source", "vintage", "estimated") if k in record}
            figures.append(figure(lens.get("name", key), value, unit, provenance))
            baseline = (nation.get("metrics") or {}).get(key, {})
            if baseline and all(baseline.get(k) == record.get(k) for k in ("period", "source", "vintage")):
                value = baseline.get("value")
                if lens.get("format") == "pct" and isinstance(value, (int, float)):
                    value *= 100
                figures.append(figure(f"{lens.get('name', key)} · India", value, unit, baseline))
        for key, summary in inventory.get("states", {}).get(row["abbr"], {}).items():
            periods = resource_periods.get(key, set())
            label = types[key]["name"]
            if len(periods) == 1 and None not in periods:
                period = next(iter(periods))
                figures.append(figure(f"{label} · mapped sites", summary["count"], "",
                                      {"period": period, "source": types[key].get("source")}))
                figures.append(figure(f"{label} · mapped sites total", summary.get("value"),
                                      summary.get("unit") or "", {"period": period}))
        add("States", "States and union territories", row["name"], *figures, sources=sources)

    terrain = world.get("tables") or {}
    add("Terrain", "Terrain methods", "Relief and land cover", *NOTES["Terrain"],
        (terrain.get("notes") or {}).get("relief"))
    for field, group, sources in [
        ("base", "Base terrain", ("koppen_geiger", "india_terrain", "soi_political_map")),
        ("features", "Terrain features", ("india_terrain", "koppen_geiger", "glwd_v2", "gfplain",
                                          "global_mangrove_watch", "allen_coral_atlas", "gvp_vents",
                                          "varkala_geoheritage", "chennai_marina", "chilika_saltmarsh")),
    ]:
        for row in terrain.get(field, []):
            if field == "features" and not row["id"]:
                continue
            examples = [sample["name"] for sample in terrain.get("terrain_examples", [])
                        if (sample.get(field) == row["id"] or
                            field == "features" and row["id"] in sample.get(field, []))]
            sites = [site["name"] for site in world.get("featureSites", [])
                     if field == "features" and site["id"] == row["id"]]
            add("Terrain", group, row["name"],
                row.get("rule"), " · ".join(examples or ([row["example"]] if row.get("example") else [])),
                " · ".join(sites), sources=sources, color=row.get("color"))
    add("Terrain", "Rivers", "River and lake mapping", *NOTES["Rivers"],
        sources=("open_rivers", "natural_earth", "hydrolakes", "pulicat"))
    channels = {}
    for edge in world.get("river_edges", []):
        for name in edge.get("names", []):
            channels[name] = channels.get(name, 0) + 1
    for name, count in sorted(channels.items()):
        add("Terrain", "Rivers", name, f"{number(count, 0)} mapped channel segments")

    add("Lenses", "Lens methods", "Population and health estimates", *NOTES["Lenses"])
    add("Yields", "Yield methods", "Yield points", *NOTES["Yields"])
    add("Resources", "Resource methods", "Resource markers", *NOTES["Resources"])
    for key, summary in inventory.get("national", {}).items():
        periods = resource_periods.get(key, set())
        if len(periods) == 1 and None not in periods and summary.get("value") is not None:
            add("Resources", types[key]["name"] + " locations", "India",
                figure("Total for mapped sites", summary["value"], summary.get("unit") or "",
                       {"period": next(iter(periods)), "source": types[key].get("source")}))
    for row in resources.get("items", []):
        resource = types.get(row["type"])
        if not resource:
            continue
        sources = [row.get("source") or resource.get("source")]
        add("Resources", resource["name"] + " locations", row.get("name") or resource["name"],
            state_names.get(row.get("state")), row.get("detail"), row.get("period"),
            figure("Reported measure", row.get("value") if resource.get("unit") else None,
                   resource.get("unit") or "", {k: row[k] for k in ("period", "source", "vintage", "estimated")
                                                   if k in row}), sources=sources)

    if gva := nation.get("national_gva"):
        meta = {key: gva[key] for key in ("period", "source", "scope", "status")}
        total = sum(gva["values"].values())
        for key, value in gva["values"].items():
            add("Yields", "National gross value added", gva["labels"][key],
                figure("Provisional GVA at basic prices", value, "INR", meta),
                f"{number(100 * value / total)}% of nominal GVA · {gva['period']}",
                sources=(gva["source"],))

    if military:
        national = military["national"]
        for key, label, source, unit in (
            ("cantonment_boards", "Cantonment Boards", "cantonment_boards", "civic boards"),
            ("legacy_sainik_schools", "Traditional Sainik Schools", "sainik_schools_2026", "schools"),
            ("sainik_schools", "Partnership Sainik Schools", "sainik_schools_2026", "schools"),
            ("rashtriya_military_schools", "Rashtriya Military Schools", "rashtriya_military_schools_2026", "schools"),
            ("defence_psu_turnover", "Defence PSU turnover", "dpsu_turnover_fy26", "INR"),
        ):
            if key in national:
                add("Yields", "Public defence statistics", label,
                    figure(label, national[key], unit, {"period": military["vintage"][key], "source": source}),
                    sources=(source,))
        for key, observation in military.get("personnel_provenance", {}).items():
            label = observation["label"]
            add("Yields", "Public defence statistics", label,
                figure(label, national["personnel"]["active"][key], "people", observation),
                observation["description"], sources=(observation["source"],))

    network_period = infrastructure.get("vintage", {}).get("network")
    for key, heading in (("roads", "Highways"), ("rail", "Railway lines")):
        lines = Counter()
        for _, _, _, *labels in infrastructure.get(key, []):
            ref, name, network = (labels + [None] * 3)[:3]
            title = " · ".join(dict.fromkeys(filter(None, (name, ref))))
            if title or network:
                lines[title or heading, network or ""] += 1
        for (title, network), count in sorted(lines.items()):
            caption = f"{number(count, 0)} mapped segments"
            add("About this map", heading, title, " · ".join(filter(None, (network, network_period, caption))),
                sources=("osm_transport",))

    freight = infrastructure.get("freight")
    if freight:
        add("About this map", "Railways", "Originating freight by railway", *NOTES["Railways"],
            infrastructure.get("vintage", {}).get("network"),
            infrastructure.get("vintage", {}).get("airports"), sources=infrastructure.get("sources", []))
        for code, name, amount in [*freight["rows"], ("india", "India", freight["total"])]:
            add("About this map", "Railways", name,
                f"{number(amount)} {freight['unit']} · {freight['label']}")
    for name, cells in infrastructure.get("rail_corridors", {}).items():
        add("About this map", "Railways", name,
            f"{number(len(set(cells)), 0)} mapped corridor hexes · {infrastructure['vintage']['network']}",
            sources=("osm_transport",))
    if trade := infrastructure.get("trade"):
        add("About this map", "Trade", "Domestic coastal cargo", *NOTES["Trade"],
            trade.get("label"), trade.get("status"),
            "The Kolkata and Haldia authority has one combined branch at the mouth of the Hooghly.",
            sources=(trade.get("source_id"), "pib_dfc_completion", "osm_transport", "cwprs_port_locations"))
    for port in infrastructure.get("ports", []):
        cargo = {key: port[key] for key in ("period", "vintage", "estimated") if key in port}
        cargo["source"] = port.get("source_id")
        coastal = port.get("coastal_cargo") or {}
        direction = port.get("overseas_direction") or {}
        add("About this map", "Ports", port["name"],
            " · ".join(filter(None, (port.get("category"), port.get("city"), port.get("state")))),
            *(figure(label, port.get(key), unit, cargo) for key, label, unit in (
                ("tons", "Cargo handled", "metric tonnes"), ("rank", "Major-port cargo rank", ""),
                ("domestic", "Domestic cargo", "metric tonnes"), ("foreign", "Overseas cargo", "metric tonnes"))),
            figure(" · ".join(filter(None, ("Coastal cargo", coastal.get("status")))), coastal.get("tons"), "metric tonnes",
                   {"period": coastal.get("period"), "source": coastal.get("source_id")}),
            *(figure(label, direction[key] * 100, "%", {
                "period": direction["period"], "vintage": direction["vintage"], "source": direction.get("source_id"),
              })
              for key, label in (("unloaded", "Overseas cargo unloaded"), ("loaded", "Overseas cargo loaded"))
              if direction.get(key) is not None))
    for airport in infrastructure.get("airports", []):
        locality = airport.get("city_provenance") or {}
        add("About this map", "Airports", airport["name"],
            " · ".join(filter(None, (airport["id"], airport.get("city"), airport.get("state"),
                                     airport.get("period") or infrastructure.get("vintage", {}).get("airports")))),
            " · ".join(filter(None, ("Locality · Airports Authority of India", locality.get("period")))) if locality else "",
            sources=("ourairports", locality.get("source_id") or locality.get("source")))

    sites = {row["id"]: row for file in protected if file for row in file.get("sites", []) if not row.get("ramsar_id")}
    if sites:
        add("Terrain", "Protected land", "Protected land mapping", *NOTES["Protected land"],
            sources=("rsis_protected", "wii_protected", "ntca_protected", "osm_protected", "wikidata_protected"))
    for row in sites.values():
        area = row.get("area_ha")
        geometry_source = row.get("source")
        if geometry_source and geometry_source.startswith(("node/", "way/", "relation/")):
            geometry_source = "osm_protected"
        elif geometry_source and geometry_source.startswith("wikidata:"):
            geometry_source = "wikidata_protected"
        add("Terrain", "Protected land", row["name"],
            row.get("designation"), row.get("status"), row.get("period"), row.get("authority"),
            f"Official area · {number(area / 100, 4)} km² · {row['period']}"
            if area is not None and row.get("period") else "",
            sources=(row.get("authority_source"), geometry_source))
    return pages


def terrain_captions(world):
    tables = world.get("tables") or {}
    examples = {}
    for example in tables.get("terrain_examples", []):
        if "relief" in example:
            examples.setdefault(example["relief"], []).append(example["name"])
    source = "NOAA ETOPO 2022" if tables.get("base") else "NOAA ETOPO1"
    relief = []
    for row in tables.get("relief", []):
        names = examples.get(row["id"], []) or ([row["example"]] if row.get("example") else [])
        captions = [row.get("rule"), "Mapped examples: " + " · ".join(names) if names else "", source]
        relief.append({**row, "rule": "\n".join(text for text in captions if text),
                       "sources": ["etopo_2022" if tables.get("base") else "etopo"]})

    names = {row["id"]: row["name"] for row in tables.get("features", [])}
    membership = {cell: set(ids) for cell, ids in enumerate(world.get("features", [])) if ids}
    for feature, cells in tables.get("feature_cells", {}).items():
        for cell in cells:
            membership.setdefault(cell, set()).add(int(feature))
    labels = {str(cell): [names[id_] for id_ in sorted(ids) if id_ in names]
              for cell, ids in membership.items()}
    return {**tables, **({"relief": relief} if relief else {})}, labels


def read_entries(web_dir):
    def read(name, fallback=None):
        path = web_dir / f"{name}.json"
        return json.loads(path.read_text()) if path.exists() else fallback

    world = read("world")
    sections = make_entries(
        world=world, states=read("states", []), cities=read("cities", []),
        wonders=read("wonders"), lenses=read("lens_catalog"), nation=read("nation"),
        resources=read("resources"), infrastructure=read("infrastructure"),
        protected=(read("protected_land"), read("protected_ramsar")),
        sources=read("sources", []), military=read("military"),
    )
    tables, labels = terrain_captions(world)
    return {"sections": sections, "terrain_relief": tables.get("relief"), "cell_features": labels}


def build():
    write_web("almanac.json", read_entries(WEB_DATA))


def check(web_dir):
    path = web_dir / "almanac.json"
    if not path.exists():
        return []
    pages = json.loads(path.read_text())
    if pages != read_entries(web_dir):
        return [("FAIL", "Almanac entries do not match the map inventories; rebuild almanac")]
    count = sum(len(rows) for groups in pages["sections"].values() for rows in groups.values())
    return [("PASS", f"{count} Almanac rows match the map inventories")]
