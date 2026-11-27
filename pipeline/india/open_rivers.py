"""Assemble named river courses from pinned OSM queries and Natural Earth 1:10m."""

import json
import math
import re
from collections import defaultdict
from pathlib import Path

from ..core.store import save_interim
from . import KRISHNA_SHA256
from .hydrography import RIVER_ANCHORS, verify

SNAPSHOTS = Path(__file__).with_name("open_river_sources.json")

ALIASES = {
    "ganges": "Ganga", "padma": "Ganga", "hugli": "Hooghly",
    "zaskar": "Zanskar", "satluj": "Sutlej", "shiquan": "Indus",
    "ghäghara": "Ghaghara", "ghaghra": "Ghaghara", "karnali": "Ghaghara",
    "narayani": "Gandak", "sapt": "Kosi", "koshi": "Kosi", "sone": "Son",
    "dihang": "Siang", "yarlung tsangpo": "Siang", "yarlung": "Siang",
    "jamuna": "Brahmaputra", "meghna": "Upper Meghna",
    "luhit": "Lohit", "tista": "Teesta", "balak": "Barak", "tapi": "Tapti",
    "sharavati": "Sharavathi", "mahänä nadï": "Mahanadi", "mahäna nadï": "Mahanadi",
    "godävari": "Godavari", "penna": "Pennar", "penner": "Pennar",
    "cauvery": "Kaveri", "kabani": "Kabini",
}

# Trunks have an ordinal cartographic rank, independent of estimated flow.
RANKS = {name: 9 for name in ("Indus", "Ganga", "Brahmaputra", "Narmada", "Godavari", "Krishna", "Mahanadi")}
RANKS.update({name: 7 for name in ("Yamuna", "Chenab", "Sutlej", "Ghaghara", "Tapti", "Kaveri", "Hooghly", "Siang")})
CONTINUATIONS = {"Kushiyara": (91.85, 24.77), "Upper Meghna": (90.65, 23.62)}
NAMES = {name.casefold(): name for name in (*RIVER_ANCHORS, "Hooghly", *CONTINUATIONS)}

# Basin topology, with receiving courses listed before their tributaries.
PARENTS = {
    "Zanskar": "Indus", "Shyok": "Indus", "Chenab": "Indus", "Jhelum": "Chenab",
    "Ravi": "Chenab", "Sutlej": "Chenab", "Beas": "Sutlej",
    "Brahmaputra": "Ganga", "Yamuna": "Ganga", "Bhagirathi": "Ganga", "Alaknanda": "Ganga",
    "Ramganga": "Ganga", "Gomti": "Ganga", "Ghaghara": "Ganga", "Gandak": "Ganga",
    "Kosi": "Ganga", "Son": "Ganga", "Chambal": "Yamuna", "Betwa": "Yamuna", "Ken": "Yamuna",
    "Siang": "Brahmaputra", "Dibang": "Brahmaputra", "Lohit": "Brahmaputra",
    "Subansiri": "Brahmaputra", "Manas": "Brahmaputra", "Teesta": "Brahmaputra",
    "Damodar": "Hooghly", "Tel": "Mahanadi", "Baitarani": "Brahmani",
    "Pranhita": "Godavari", "Indravati": "Godavari", "Bhima": "Krishna", "Tungabhadra": "Krishna",
    "Kabini": "Kaveri", "Bhavani": "Kaveri",
    "Barak": "Kushiyara", "Kushiyara": "Upper Meghna",
}
MOUTHS = {
    "Indus": (67.56, 24.08), "Narmada": (72.59, 21.59), "Tapti": (72.72, 21.14),
    "Mahi": (72.77, 22.21), "Sabarmati": (72.40, 22.27), "Periyar": (76.16, 10.18),
    "Sharavathi": (74.42, 14.30), "Mahanadi": (86.40, 20.30), "Brahmani": (86.93, 20.71),
    "Subarnarekha": (87.37, 21.57), "Godavari": (82.24, 16.71), "Krishna": (80.84, 15.76),
    "Pennar": (80.19, 14.58), "Kaveri": (79.85, 11.13), "Vaigai": (79.00, 9.35),
    "Hooghly": (88.06, 22.03), "Ganga": (89.749278, 23.848009),
}
JUNCTIONS = {
    "Zanskar": (77.33, 34.17), "Shyok": (75.91, 35.23), "Chenab": (70.65, 29.11),
    "Jhelum": (72.15, 31.17), "Ravi": (71.82, 30.61), "Sutlej": (71.06, 29.38),
    "Beas": (74.95, 31.15), "Brahmaputra": (89.75, 23.85), "Yamuna": (81.89, 25.42),
    "Bhagirathi": (78.60, 30.14), "Alaknanda": (78.60, 30.14),
    "Ramganga": (79.84, 27.16), "Gomti": (83.16, 25.51), "Ghaghara": (84.67, 25.74),
    "Gandak": (85.19, 25.66), "Kosi": (87.26, 25.40), "Son": (84.87, 25.70),
    "Chambal": (79.25, 26.49), "Betwa": (80.23, 25.92), "Ken": (80.53, 25.78),
    "Siang": (95.29, 27.81), "Dibang": (95.48, 27.80), "Lohit": (95.48, 27.80),
    "Subansiri": (94.04, 26.92), "Manas": (90.68, 26.19), "Teesta": (89.70, 25.43),
    "Damodar": (88.10, 22.30), "Tel": (83.96, 20.84), "Baitarani": (86.86, 20.76),
    "Pranhita": (79.91, 18.82), "Indravati": (80.28, 18.71),
    "Bhima": (77.29, 16.41), "Tungabhadra": (78.24, 15.97),
    "Kabini": (76.91, 12.21), "Bhavani": (77.69, 11.43),
    "Barak": (92.489126, 24.8759119), "Kushiyara": (91.1183351, 24.2412075),
    "Upper Meghna": (90.63125, 23.22292), "Ganga": (89.749278, 23.848009),
    "Hooghly": (88.0912542, 24.4935828),
}
MEGHNA_INLETS = {"Ganga", "Upper Meghna"}


def canonical(name):
    name = re.sub(r"(^river | river$)", "", name.strip(), flags=re.I).casefold()
    return NAMES.get(name) or ALIASES.get(name)


def osm_lines(paths):
    results = defaultdict(dict)
    for path in paths:
        doc = json.loads(path.read_text())
        if doc.get("remark"):
            raise ValueError(f"{path}: {doc['remark']}")
        for item in doc["elements"]:
            tags = item.get("tags", {})
            name = next((n for key in ("name:en", "int_name", "name") if (n := canonical(tags.get(key, "")))), None)
            if not name:
                continue
            if item["type"] == "way":
                ways = [(item["id"], item.get("geometry"), False)]
            elif item["type"] == "relation":
                ways = [(m["ref"], m.get("geometry"), m.get("role") == "main_stream")
                        for m in item.get("members", []) if m["type"] == "way" and m.get("role") in ("", "main_stream")]
            else:
                continue
            for wid, geometry, main in ways:
                if geometry and (main or wid not in results[name]) and all(geometry):
                    results[name][wid] = [(p["lon"], p["lat"]) for p in geometry]
    return results


def natural_earth_lines(path):
    results = defaultdict(list)
    for feature in json.loads(path.read_text())["features"]:
        p = feature["properties"]
        if name := canonical(p.get("name") or ""):
            if not (p.get("featurecla") or "").startswith("Lake Centerline"):
                lines = feature["geometry"]["coordinates"]
                if name == "Ganga":
                    lines = [line for line in lines if line[0][0] < 81 or line[-1][0] == 89.749278]
                results[name].extend(lines)
    return results


def merged(lines):
    from shapely import MultiLineString, line_merge

    collection = line_merge(MultiLineString([line for line in lines if len(line) > 1]))
    return [list(line.coords) for line in sorted(
        collection.geoms if collection.geom_type == "MultiLineString" else [collection],
        key=lambda line: -line.length) if not line.is_empty]


def stitch(lines):
    """Bridge small mapping gaps between independently named pieces of one river."""
    while len(lines) > 1:
        line = lines[0]
        distance, index, start, reverse = min(
            (math.dist(line[-1 if start else 0], other[0 if start != reverse else -1]), i, start, reverse)
            for i, other in enumerate(lines[1:], 1) for start in (False, True) for reverse in (False, True)
        )
        if distance > 0.17:
            break
        other = lines.pop(index)
        if reverse:
            other = other[::-1]
        lines[0] = line + other if start else other + line
    return lines


def courses(osm_paths, earth_path):
    from shapely import LineString, Point
    from shapely.ops import substring

    osm, earth = osm_lines(osm_paths), natural_earth_lines(earth_path)
    anchors = {**RIVER_ANCHORS, "Hooghly": (88.34, 22.55), **CONTINUATIONS}
    selected = {}
    for name, location in anchors.items():
        anchor = Point(location)
        candidates = []
        for source, segments in (("osm", osm[name].values()), ("natural_earth", earth[name])):
            for coordinates in stitch(merged(segments)):
                line = LineString(coordinates)
                d = line.distance(anchor)
                if d <= 0.42 and line.length > 0.12:
                    candidates.append((line.length - d * 4, source, line))
        if not candidates:
            print(f"No continuous source course for {name}")
            continue
        _, source, line = max(candidates, key=lambda item: item[0])
        selected[name] = source, line

    emitted = set()

    def emit(name):
        if name in emitted or name not in selected:
            return
        parent = PARENTS.get(name)
        if parent:
            yield from emit(parent)
        source, line = selected[name]
        target = Point(JUNCTIONS[name] if parent or name in MEGHNA_INLETS else MOUTHS[name]) if (
            parent or name in MEGHNA_INLETS or name in MOUTHS) else None
        vertices = list(line.coords)
        if target is not None:
            if Point(vertices[0]).distance(target) < Point(vertices[-1]).distance(target):
                line = LineString(vertices[::-1])
            trimmed = substring(line, 0, line.project(target))
            if trimmed.geom_type == "LineString":
                vertices = list(trimmed.coords)
        if name in ("Ganga", "Brahmaputra"):
            head = Point(JUNCTIONS["Alaknanda" if name == "Ganga" else "Siang"])
            oriented = LineString(vertices)
            trimmed = substring(oriented, oriented.project(head), oriented.length)
            if trimmed.geom_type == "LineString":
                vertices = list(trimmed.coords)
        result = {"name": name, "rank": RANKS.get(name, 6), "source": source,
                  "line": vertices, "mouth": name in MOUTHS}
        if parent and parent in selected:
            parent_line = selected[parent][1]
            junction = parent_line.interpolate(parent_line.project(target))
            result.update(end_on=parent, junction=list(junction.coords[0]))
        if name in MEGHNA_INLETS:
            result.update(mouth=False, end_on="Lower Meghna", junction=list(JUNCTIONS[name]))
        if name == "Hooghly":
            result.update(start_on="Ganga")
        emitted.add(name)
        yield result

    for name in anchors:
        yield from emit(name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("natural_earth", type=Path)
    parser.add_argument("cache", type=Path, help="directory containing the pinned Overpass snapshots")
    args = parser.parse_args()
    manifest = json.loads(SNAPSHOTS.read_text())
    paths = []
    for item in manifest["snapshots"]:
        path = args.cache / item["file"]
        verify(path, "sha256", item["sha256"])
        paths.append(path)
    verify(args.natural_earth, "sha256", KRISHNA_SHA256)
    result = list(courses(paths, args.natural_earth))
    missing = (RIVER_ANCHORS.keys() | CONTINUATIONS.keys()) - {course["name"] for course in result}
    if missing:
        raise ValueError(f"Missing named courses: {', '.join(sorted(missing))}")
    save_interim("open_rivers", {"courses": result}, vintage="November 2026 OSM snapshots")
