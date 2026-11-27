"""Prepare protected land from pinned RSIS, authority and OpenStreetMap snapshots."""

import argparse
import json
import re
import subprocess
from hashlib import sha256
from math import cos, pi, sin, sqrt
from pathlib import Path

from shapely import make_valid, transform, union_all
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import polygonize
from shapely.strtree import STRtree

from pipeline.build.city_view import grid_fingerprint, name_key
from pipeline.build.protected_land import SOURCE, civilian_site, official_area_matches, polygon_candidate, qualifying_cells
from pipeline.build.world import FOREIGN, STATE_ABBR
from pipeline.core.geo import MapProjection
from pipeline.core.hexgrid import HexGrid
from pipeline.core.paths import WEB_DATA
from pipeline.core.store import load_interim, save_interim
from pipeline.india.people_metrics import HtmlRows
from pipeline.india.protected_land_catalog import MANIFEST

# Alternate spellings and names used by the authority lists and by OSM.
ALIASES = {
    "Manipur Parvat (Mount Harriet)": ["Mount Harriet", "Mount Manipur"],
    "Valmiki National Park": ["Valmiki"],
    "Guru Ghasidas (Sanjay)": ["Guru Ghasidas"],
    "Indravati (Kutru)": ["Indravati"],
    "Bhagwan Mahavir (Mollem)": ["Bhagwan Mahavir", "Mollem", "Bhagwan Mahaveer"],
    "Blackbuck (Velavadar)": ["Blackbuck", "Velavadar", "Velavadar Blackbuck"],
    "Marine (Gulf of Kachchh)": ["Marine", "Gulf of Kutch Marine"],
    "Col. Sherjung Simbalbara": ["Simbalbara"],
    "Inderkala": ["Inderkilla", "Inderkila"],
    "Khirganga": ["Kheerganga", "Khir Ganga"],
    "Nagarhole": ["Nagarahole", "Rajiv Gandhi"],
    "Anshi": ["Anshi (Kali)"],
    "Papikonda": ["Papikondalu"],
    "Dihing Patkai": ["Dehing Patkai"],
    "Rajiv Gandhi (Rameswaram)": ["Rajiv Gandhi", "Rameswaram"],
    "Rajiv Gandhi (Orang)": ["Orang"],
    "Corbett": ["Jim Corbett"],
    "Govind": ["Govind Pashu Vihar"],
    "Navegaon": ["Nawegaon"],
    "Intanki": ["Ntangki"],
    "Shiroi": ["Shirui", "Sirohi"],
    "Sunderban": ["Sundarban", "Sundarbans", "Sunderbans"],
    "Keoladeo Ghana": ["Keoladeo", "Bharatpur Bird Sanctuary"],
    "Khangchendzonga": ["Kanchendzonga", "Kanchenjunga"],
    "Similipal": ["Simlipal"],
    "Simlipal": ["Similipal"],
    "Indira Gandhi": ["Anamalai"],
    "Kasu Brahmananda Reddy": ["KBR", "Kasu Brahmanandha Reddy"],
    "Rajbari": ["Bison", "Rajbari (Bison)"],
    "Ranthambore": ["Ranthambhore"],
    "Ranthambhore": ["Ranthambore"],
    "Nagarjunsagar Sagar": ["Nagarjuna Sagar-Srisailam", "Nagarjunasagar Srisailam"],
    "Kalakad Mundanthurai": ["Kalakkad Mundanthurai"],
    "Tadobha Andhari": ["Tadoba Andhari", "Tadoba"],
    "Pench – MH": ["Pench"],
    "Pakke": ["Pakhui"],
    "Satkoshia": ["Satkosia"],
    "Sanjay Dhubri": ["Sanjay Dubri"],
    "Mukundara": ["Mukundra", "Mukundara Hills", "Mukundra Hills"],
    "Dholpur – Karauli": ["Dhaulpur-Karauli"],
    "Biligiri Ranganatha Temple": ["Biligiri Rangaswamy Temple", "BRT"],
}
STATE_NAMES = {
    "Andaman & Nicobar Islands": "Andaman & Nicobar", "Orissa": "Odisha",
    "Chattisgarh": "Chhattisgarh", "Madhy Pradesh": "Madhya Pradesh",
}
WONDERS = {
    "national_park": {
        "Great Himalayan": "whc-1406", "Khangchendzonga": "whc-1513",
        "Nanda Devi": "whc-335", "Valley of Flowers": "whc-335",
        "Kaziranga": "whc-337", "Keoladeo Ghana": "whc-340",
        "Sunderban": "whc-452", "Manas": "whc-338",
        # Park extents associated with the Western Ghats serial property.
        "Eravikulam": "whc-1342", "Silent Valley": "whc-1342", "Mukurthi": "whc-1342",
        "Kudremukh": "whc-1342",
        "Dinosaur Fossils": "dinosaur-fossils", "Murlen": "murlen",
    },
    "tiger_reserve": {"Manas": "whc-338"},
    "ramsar": {229: "chilika", 463: "loktak", 1213: "tso-moriri", 2441: "lonar"},
}
DESIGNATION = {"national_park": "National park", "tiger_reserve": "Tiger reserve", "ramsar": "Ramsar wetland"}
# Reviewed item IDs for reference locations. Only the coordinate claim is used.
POINT_ITEMS = {
    "wii-an-manipurparvatmountharriet": "Q3091762", "wii-cg-kangervalley": "Q1723746",
    "wii-jk-kazinag": "Q4208325", "wii-jk-kishtwarhighaltitude": "Q727091",
    "wii-jk-salimalicityforest": "Q2667857", "wii-ka-anshi": "Q5215675",
    "wii-mp-dinosaurfossils": "Q135111713", "wii-mp-fossil": "Q3364416",
    "wii-mp-kanha": "Q1480481", "wii-mh-tadoba": "Q2639563", "wii-mh-pench": "Q2720864",
    "wii-ml-balpakram": "Q2979712", "wii-mz-phawngpui": "Q15266124",
    "wii-nl-intanki": "Q3091771", "wii-rj-desert": "Q3058213",
    "wii-rj-mukundrahills": "Q5224247", "wii-tn-gulfofmannarmarinepark": "Q5617576",
    "wii-ts-mahaveerharinavanasthali": "Q3092314", "wii-tr-cloudedleopard": "Q5135742",
    "wii-tr-rajbari": "Q7285897", "ntca-3": "Q1480481", "ntca-25": "Q2720864", "ntca-39": "Q7461463",
    "ntca-45": "Q127499823", "ntca-56": "Q131465770",
}
OSM_EXTENT_CHOICES = {
    "wii-gj-marinegulfofkachchh": "relation/8334753",
    "wii-kl-periyar": "relation/21656429",
    "wii-od-bhitarkanika": "relation/8815438",
    "wii-od-similipal": "relation/19289292",
}
# The named sanctuary or park gives a reference position within the wider reserve.
# Its extent is not a substitute for the whole reserve.
OSM_POINT_CHOICES = {
    "ntca-8": "way/71890925", "ntca-10": "relation/21656430", "ntca-18": "relation/2640060",
    "ntca-19": "way/155466998", "ntca-40": "way/378131783", "ntca-51": "relation/21656431",
    "ntca-57": "way/669498418",
}


def polygons(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry] if not geometry.is_empty else []
    return [p for part in getattr(geometry, "geoms", ()) for p in polygons(part)]


def ring_geometry(rings, project):
    result = Polygon()
    for ring in rings:
        if len(ring) >= 4:
            part = union_all(polygons(make_valid(Polygon([project(*p) for p in ring]))))
            result = result.symmetric_difference(part)
    return result


def osm_names(tags):
    names = [value for key, value in tags.items() if key in ("name", "name:en", "alt_name", "official_name")]
    return {site_key(part) for name in names for part in re.split(r"[/;]", name)}


def site_key(name):
    generic = r"\b(?:national park|tiger reserve|wildlife sanctuary|nature reserve|ramsar site|wls)\b"
    return name_key(re.sub(generic, "", name.casefold()))


def park_roster(path):
    layout = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)
    names = []
    for page in layout.split("\f"):
        if "Notification" not in page:
            continue
        for block in re.split(r"\n\s*\n", page):
            area = re.search(r"\b(?:19|20)\d{2}\s+([\d.,]+)\s+(?:East|West|North|South|Central)", block)
            if not area:
                continue
            state, name = [], []
            for line in block.splitlines():
                left = re.split(r"\s{2,}(?:19|20)\d{2}\s{2,}", line)[0]
                for token in re.finditer(r"\S+(?: \S+)*", left):
                    (state if token.start() < 29 else name).append(token.group())
            names.append((" ".join(state), " ".join(name), float(area[1].replace(",", ""))))
    if len(names) != 106:
        raise ValueError(f"Expected 106 WII rows, got {len(names)}")
    return [(state, name.split(",")[0].split(" (partially")[0].split(" (Bandipur")[0]
             .split(" (Nagarahole")[0].split(" (21 Islands)")[0].replace("Simlipal", "Similipal"), area)
            for state, name, area in names]


def tiger_roster(path):
    parser = HtmlRows()
    parser.feed(path.read_text())
    rows = [(int(row[0]), row[3], row[1], float(row[7].replace(",", ""))) for row in parser.rows if len(row) == 8
            and row[0].isdigit() and row[5].replace(",", "").replace(".", "").isdigit()]
    if [row[0] for row in rows] != list(range(1, 59)):
        raise ValueError("The NTCA roster differs from the 58-reserve snapshot")
    return rows


def osm_polygon(element):
    def coordinates(nodes):
        return [(node["lon"], node["lat"]) for node in nodes]

    if element["type"] == "way":
        points = coordinates(element.get("geometry", []))
        return Polygon(points) if len(points) >= 4 and points[0] == points[-1] else Polygon()
    members = element.get("members", [])
    if any(m["type"] != "way" or not m.get("geometry")
           for m in members if m["role"] in ("outer", "inner")):
        return Polygon()
    lines = {role: [LineString(coordinates(m["geometry"])) for m in members
                    if m["role"] == role and len(m["geometry"]) >= 2] for role in ("outer", "inner")}
    outer, inner = (union_all(list(polygonize(lines[role]))) for role in ("outer", "inner"))
    return outer.difference(inner)


def area_shares(extents, areas):
    cover = union_all(extents)
    return {key: round(min(1, cover.intersection(area).area / area.area), 7)
            if area.area and extents else None for key, area in areas.items()}


def covered_cells(extent, hexes, tree, owners):
    intersections = ((int(i), extent.intersection(hexes[i]).area)
                     for i in tree.query(extent) if owners[i] != FOREIGN)
    return qualifying_cells(intersections, hexes[0].area)


def reference_point(entity, project):
    claims = [claim for claim in entity.get("claims", {}).get("P625", [])
              if claim["rank"] != "deprecated" and claim["mainsnak"]["snaktype"] == "value"]
    for claim in sorted(claims, key=lambda c: c["rank"] != "preferred"):
        value = claim["mainsnak"]["datavalue"]["value"]
        if value["globe"].endswith("/Q2"):
            return Point(project(value["longitude"], value["latitude"]))
    return None


def prepare(directory, manifest, world):
    project = MapProjection(**world["projection"])
    grid = HexGrid(**world["grid"])
    boundaries = load_interim("datameet")
    states = {STATE_ABBR[s["name"]]: ring_geometry(s["rings"], project) for s in boundaries["states"]}
    districts = {f"{d['state_code']:02d}-{d['code']:03d}": ring_geometry(d["rings"], project)
                 for d in boundaries["districts"] if d["code"]}
    corners = [(grid.radius * cos(pi / 6 + k * pi / 3), grid.radius * sin(pi / 6 + k * pi / 3))
               for k in range(6)]
    hexes = []
    for i in range(grid.size):
        x, y = grid.center(*grid.col_row(i))
        hexes.append(Polygon([(x + dx, y + dy) for dx, dy in corners]))
    tree = STRtree(hexes)

    def mapped(geom):
        # Project each vertex in the atlas's equal-area coordinate system.
        return transform(geom, lambda coords: [project(x, y) for x, y in coords])

    def json_file(name):
        return json.loads((directory / name).read_text())

    def osm_id(element):
        return f"{element['type']}/{element['id']}"

    index = {osm_id(e): e for name in manifest if name.startswith("osm-index")
             for e in json_file(name)["elements"] if civilian_site(e.get("tags", {})) and osm_names(e.get("tags", {}))}
    geometry = {osm_id(e): e for name in manifest if name.startswith("osm-part-")
                for e in json_file(name)["elements"]}
    point_entities = json_file("wikidata-points.json")["entities"]
    raw_extents = {}
    areas = []
    osm_sites, ramsar_sites = [], []
    rejected_extents = []

    def checked_osm_extent(site_id, item, extent, official_km2):
        if official_area_matches(extent.area, official_km2):
            return extent
        rejected_extents.append({
            "site": site_id, "osm": osm_id(item), "mapped_km2": round(extent.area, 2),
            "official_km2": official_km2,
        })
        return None

    def register(site_id, name, kind, point, extent=None, source=None, area=None, wonder=None):
        x, y = point.coords[0] if point is not None else (None, None)
        cell = grid.cell_at(x, y) if point is not None else -1
        cells = None
        if extent is not None and not extent.is_empty:
            areas.append(extent)
            cells = covered_cells(extent, hexes, tree, world["owner"])
        site = {
            "id": site_id, "name": name, "designation": DESIGNATION[kind],
            "x": round(x, 3) if cell >= 0 else None, "y": round(y, 3) if cell >= 0 else None,
            "cell": cell if cell >= 0 else None, "cells": cells, "source": source,
            "area_ha": area, "wonder": wonder,
        }
        if kind == "ramsar" and cells is not None:
            simplified = extent.simplify(0.12, preserve_topology=True)
            site["rings"] = [
                [[round(x, 3), round(y, 3)] for x, y in ring.coords]
                for part in polygons(simplified) for ring in (part.exterior, *part.interiors)
            ]
        return site

    def extent_for(item):
        key = osm_id(item)
        if key not in raw_extents:
            geom = osm_polygon(geometry[key])
            raw_extents[key] = union_all(polygons(make_valid(mapped(geom)))) if not geom.is_empty else None
        return raw_extents[key]

    rsis_polygons = {}
    for feature in json_file("boundaries.json")["features"]:
        p, geom = feature["properties"], feature["geometry"]
        if p["iso3"] == "IND" and geom and geom["type"] in ("Polygon", "MultiPolygon"):
            rsis_polygons.setdefault(p["ramsarid"], []).extend(polygons(make_valid(mapped(shape(geom)))))
    for feature in sorted(json_file("centroids.json")["features"], key=lambda f: f["properties"]["ramsarid"]):
        p = feature["properties"]
        if p["iso3"] != "IND" or feature["geometry"]["type"] != "Point":
            continue
        rid = p["ramsarid"]
        point = mapped(shape(feature["geometry"]))
        extent = union_all(rsis_polygons.get(rid, []))
        site = register(f"rsis-{rid}", p["officialname"].strip(), "ramsar", point, extent, "rsis_protected",
                        p["area_off"], WONDERS["ramsar"].get(rid))
        ramsar_sites.append(site)
        if site["cells"] is None:
            matches = [e for e in index.values() if osm_id(e) in geometry and polygon_candidate("ramsar", e["tags"])
                       and (site_key(p["officialname"]) in osm_names(e["tags"])
                            or str(rid) == e["tags"].get("ref:ramsar"))]
            for e in matches:
                extent = extent_for(e)
                if extent is not None and extent.distance(point) <= 2:
                    extent = checked_osm_extent(site["id"], e, extent, p["area_off"] / 100)
                    if extent is None:
                        continue
                    spatial = register(site["id"], site["name"], "ramsar", point, extent, osm_id(e))
                    # Keep the credited RSIS facts with their original file.
                    osm_sites.append({**spatial, "id": f"osm-rsis-{rid}", "ramsar_id": site["id"]})
                    break
    if len(ramsar_sites) != 103 or not {"rsis-2602", "rsis-2603"} <= {s["id"] for s in ramsar_sites}:
        raise ValueError("RSIS GIS snapshot does not match the October 2026 roster")

    parks = [(None, state, name, area) for state, name, area in park_roster(directory / "national-parks.pdf")]
    for kind, roster in (("national_park", parks), ("tiger_reserve", tiger_roster(directory / "ntca.html"))):
        for serial, state, name, official_km2 in roster:
            abbr = STATE_ABBR[STATE_NAMES.get(state, state)]
            site_id = f"ntca-{serial}" if serial else f"wii-{abbr.lower()}-{name_key(name)}"
            names = {site_key(alias) for alias in (name, *ALIASES.get(name, []))}
            state_shape = states[abbr]
            matches = []
            for e in index.values():
                key = osm_id(e)
                if key != OSM_POINT_CHOICES.get(site_id) and not names.intersection(osm_names(e["tags"])):
                    continue
                center = e.get("center", e)
                if "lon" not in center:
                    continue
                point = Point(project(center["lon"], center["lat"]))
                if state_shape.distance(point) > (0 if "pench" in names else 25):
                    continue
                matches.append((e, point))
            candidates = [(e, extent_for(e)) for e, _ in matches if osm_id(e) in geometry
                          and (not OSM_EXTENT_CHOICES.get(site_id) or osm_id(e) == OSM_EXTENT_CHOICES[site_id])
                          and polygon_candidate(kind, e["tags"])]
            candidates = [(e, g) for e, g in candidates if g is not None and g.area > 0]
            candidates = [(e, checked_osm_extent(site_id, e, g, official_km2)) for e, g in candidates]
            candidates = [(e, g) for e, g in candidates if g is not None]
            source, extent, point = None, None, None
            if len(candidates) == 1:
                e, extent = candidates[0]
                source, point = osm_id(e), extent.representative_point()
            elif matches:
                # Prefer a designated OSM object's published label position for the fallback.
                preferred = [pair for pair in matches if osm_id(pair[0]) in
                             (OSM_EXTENT_CHOICES.get(site_id), OSM_POINT_CHOICES.get(site_id))]
                preferred = preferred or [pair for pair in matches if polygon_candidate(kind, pair[0]["tags"])]
                if len(preferred or matches) == 1:
                    e, point = (preferred or matches)[0]
                    source = osm_id(e)
            item = POINT_ITEMS.get(site_id)
            if point is None and item:
                entity = point_entities[item]
                reference = reference_point(entity, project)
                if reference is not None and state_shape.distance(reference) <= 25:
                    point = reference
                    source = f"wikidata:{item}@{entity['lastrevid']}"
            label = name if kind == "tiger_reserve" or " park" in name.lower() else f"{name} National Park"
            if name == "Pench":
                label = f"{label} ({state})"
            site = register(site_id, label, kind, point, extent, source, official_km2 * 100, WONDERS[kind].get(name))
            site["state"] = abbr
            if not site["cells"]:
                site["marker_radius"] = round(min(7, 2.2 + 0.12 * sqrt(official_km2)), 2)
            osm_sites.append(site)
    vintage = "November 2026"
    return {"grid": grid_fingerprint(world), "rejected_extents": rejected_extents,
            "osm": {"sites": osm_sites, "vintage": vintage, "shares": {
                "states": area_shares(areas, {s["abbr"]: states[s["abbr"]] for s in world["states"]}),
                "counties": area_shares(areas, {d["geoid"]: districts.get(d["geoid"], Polygon())
                                              for d in world["counties"]}),
            }}, "ramsar": {"sites": ramsar_sites, "vintage": "October 2026 list"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    for name, info in manifest.items():
        if sha256((args.directory / name).read_bytes()).hexdigest() != info["sha256"]:
            raise ValueError(f"Protected land checksum differs for {name}")
    world = json.loads((WEB_DATA / "world.json").read_text())
    prepared = prepare(args.directory, manifest, world)
    save_interim(SOURCE, prepared, vintage="November 2026")
    for dataset in ("ramsar", "osm"):
        sites = prepared[dataset]["sites"]
        print(f"{dataset}: {len(sites)} sites, {sum(s['cells'] is not None for s in sites)} extents, "
              f"{sum(s['x'] is None for s in sites)} without a mapped location")


if __name__ == "__main__":
    main()
