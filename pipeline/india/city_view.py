"""Prepare City View footprint intersections and 2026 population weights (see README)."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from hashlib import file_digest
from math import cos, pi, sin
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from threading import Event
from urllib.error import HTTPError, URLError
from zipfile import ZipFile

import numpy as np
import pyogrio
import rasterio
import shapely
from pyproj import Transformer
from rasterio.features import geometry_mask, geometry_window
from rasterio.errors import WindowError
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree

from pipeline.build.city_view import CONFIG, cohort, grid_fingerprint, point_profile, select_centres
from pipeline.build.district_values import district_sample_values, small_district_values
from pipeline.build.projection import state_profile
from pipeline.build.states import district_states, mapped_area
from pipeline.core.geo import MapProjection
from pipeline.core.hexgrid import HexGrid
from pipeline.core.paths import WEB_DATA
from pipeline.core.store import load_interim, save_interim
from pipeline.india import CITY_POPULATION_CHECKSUM, CITY_POPULATION_GRID, GHSL_CHECKSUM, GHSL_UCDB, WUP_SOURCE
from pipeline.india.city_age_api import AGE_BANDS, counts_for
from pipeline.india.city_sources import AGE_API_SOURCE, AGE_RELEASE, AGE_SOURCE, HEX_GEOGRAPHY
from pipeline.india.grid import CRS
from pipeline.sources.worldpop_age import SOURCE_ID as STATE_AGE_SOURCE, median_age

MIN_RASTER_COVERAGE = 0.8


def web(name):
    return json.loads((WEB_DATA / (name + ".json")).read_text())


def verify(path, expected):
    with path.open("rb") as stream:
        actual = file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"{path}: expected SHA-256 {expected}, got {actual}")


def read_centres(archive, to_map):
    with TemporaryDirectory() as tmp, ZipFile(archive) as zipped:
        member = next(n for n in zipped.namelist() if n.lower().endswith(".gpkg"))
        path = Path(tmp) / "ucdb.gpkg"
        with zipped.open(member) as source, path.open("wb") as dest:
            copyfileobj(source, dest)
        layer = "GHSL_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A"
        meta, _, geometries, fields = pyogrio.raw.read(
            path, layer=layer, columns=["ID_UC_G0", "GC_UCN_MAI_2025", "GC_CNT_GAD_2025"]
        )
    transform = Transformer.from_crs(meta["crs"], CRS, always_xy=True).transform
    centres = {}
    for ident, name, country, wkb in zip(*fields, geometries):
        if country != "India":
            continue
        shape = shapely.transform(shapely.from_wkb(wkb), transform, interleaved=False)
        centres[int(ident)] = (str(name), shapely.make_valid(shapely.transform(shape, to_map, interleaved=False)))
    if not centres:
        raise ValueError("No Indian urban centres found in the GHSL input")
    return centres


def ring_geometry(rings, project):
    """DataMeet rings use even–odd containment, including separate parts and holes."""
    shape = Polygon()
    for ring in rings:
        if len(ring) >= 4:
            part = shapely.make_valid(Polygon([project(lon, lat) for lon, lat in ring]))
            shape = shape.symmetric_difference(part)
    return shape


def raster_transform(project, crs):
    to_lonlat = Transformer.from_crs(CRS, crs, always_xy=True).transform

    def xy_to_raster(x, y):
        return to_lonlat((x + project.min_x - project.margin) * 1000,
                         (project.max_y + project.margin - y) * 1000)

    return xy_to_raster


def mass_sampler(raster, project):
    xy_to_raster = raster_transform(project, raster.crs)

    def mass(geometry):
        if geometry.is_empty or geometry.area == 0:
            return 0.0, 0.0
        geometry = shapely.transform(geometry, xy_to_raster, interleaved=False)
        try:
            window = geometry_window(raster, [geometry])
        except WindowError:
            return 0.0, 0.0
        data = raster.read(1, window=window, masked=True)
        inside = geometry_mask([geometry], data.shape, raster.window_transform(window), invert=True)
        selected = data[inside].compressed()
        valid = selected[np.isfinite(selected) & (selected >= 0)]
        total = int(inside.sum())
        return float(valid.sum(dtype=np.float64)), len(valid) / total if total else 0.0

    return mass


def mass_reader(raster, project):
    sample = mass_sampler(raster, project)

    def mass(geometry):
        return sample(geometry)[0]

    return mass


def overlap_mass_reader(raster, project):
    """Weight pixels cut by land by their intersected area in atlas km²."""
    to_raster = raster_transform(project, raster.crs)
    to_projected = Transformer.from_crs(raster.crs, CRS, always_xy=True).transform

    def to_map(x, y):
        x, y = to_projected(x, y)
        return project.from_projected(x / 1000, y / 1000)

    def mass(geometry):
        extent = shapely.transform(geometry, to_raster, interleaved=False)
        try:
            window = geometry_window(raster, [extent])
        except WindowError:
            return 0.0, 0.0
        raster_values = raster.read(1, window=window, masked=True)
        data = raster_values.data
        rows, cols = np.nonzero(~np.ma.getmaskarray(raster_values) & np.isfinite(data) & (data >= 0))
        if not len(rows):
            return 0.0, 0.0
        transform = raster.window_transform(window)
        x0, y0 = transform * (cols, rows)
        x1, y1 = transform * (cols + 1, rows + 1)
        pixels = shapely.transform(shapely.box(x0, y1, x1, y0), to_map, interleaved=False)
        areas = shapely.area(shapely.intersection(pixels, geometry))
        return float(np.dot(data[rows, cols], areas / shapely.area(pixels))), min(1, float(areas.sum()) / geometry.area)

    return mass


def age_readers(stack, directory, reference, project):
    readers = {}
    for age in AGE_BANDS:
        readers[age] = []
        for sex in ("f", "m"):
            path = directory / f"ind_{sex}_{age:02d}_2026_CN_1km_R2025A_UA_v1.tif"
            raster = stack.enter_context(rasterio.open(path))
            if (raster.crs, raster.transform, raster.shape) != (reference.crs, reference.transform, reference.shape):
                raise ValueError(f"{path}: WorldPop age grid differs from the population grid")
            readers[age].append(mass_sampler(raster, project))
    return readers


def read_age_mass(geometry, readers, min_coverage=MIN_RASTER_COVERAGE):
    counts = {}
    for age, pair in readers.items():
        (female, f_coverage), (male, m_coverage) = (read(geometry) for read in pair)
        if min(f_coverage, m_coverage) < min_coverage:
            return {}
        counts[age] = female + male
    return counts


def exclusive_footprints(matches, original):
    """Keep reviewed footprints and reject any new match sharing positive area."""
    ids = list(matches)
    shapes = [matches[cid][1] for cid in ids]
    tree = STRtree(shapes)
    retained = {}
    for cid, shape in zip(ids, shapes):
        conflicts = [ids[index] for index in tree.query(shape, predicate="intersects")
                     if ids[index] != cid and shape.intersection(shapes[index]).area > 1e-8]
        if cid in original:
            if any(other in original for other in conflicts):
                raise ValueError(f"Overlapping reviewed footprints: {cid}, {conflicts}")
        elif conflicts:
            print(f"{cid}: point fallback. Conflicting urban footprint(s): {conflicts}")
            continue
        retained[cid] = matches[cid]
    return retained


def api_age_mass(geometries, to_lonlat, cache, limited, *, cached_only=False):
    def read(item):
        key, footprint = item
        try:
            return key, counts_for(footprint, to_lonlat, cache, cached_only=cached_only or limited.is_set())
        except (URLError, TimeoutError, ValueError) as exc:
            if isinstance(exc, HTTPError) and exc.code == 429:
                limited.set()
            print(f"{key}: age estimate unavailable: {exc}")
            return key, {}

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(read, geometries.items()))


def prepare(archive, raster, world, ages=None, age_api_cache=None):
    project = MapProjection(**world["projection"])
    grid = HexGrid(**world["grid"])
    cities = {c["id"]: c for c in web("cities")}
    places = {str(p["id"]): p for p in load_interim(WUP_SOURCE)["places"]}
    rules = json.loads((CONFIG / "city_view_matches.json").read_text())
    boundaries = load_interim("datameet")

    def to_map(x, y):
        return project.from_projected(x / 1000, y / 1000)

    def outline_ring(ring):
        return [to_map(x, y) for x, y in ring]

    land = shapely.union_all([shapely.make_valid(Polygon(outline_ring(rings[0]), [
        outline_ring(ring) for ring in rings[1:]
    ])) for rings in load_interim("soi_outline")["polygons"]])
    lakes = [ring_geometry(lake["rings"], project) for lake in load_interim("natural_earth")["lakes"]]
    land = land.difference(shapely.union_all(lakes))
    districts = {f"{d['state_code']:02d}-{d['code']:03d}": ring_geometry(d["rings"], project)
                 for d in boundaries["districts"] if d["code"]}
    from pipeline.build.world import STATE_ABBR

    states = {STATE_ABBR[s["name"]]: ring_geometry(s["rings"], project) for s in boundaries["states"]}
    district_ids = list(districts)
    district_tree = STRtree(list(districts.values()))
    centre_data = read_centres(archive, to_map)
    centre_ids = list(centre_data)
    centre_tree = STRtree([shape for _, shape in centre_data.values()])
    close = [(grid.radius * cos(pi / 6 + k * pi / 3), grid.radius * sin(pi / 6 + k * pi / 3))
             for k in range(6)]
    hexes = []
    for cell in range(grid.size):
        x, y = grid.center(*grid.col_row(cell))
        hexes.append(Polygon([(x + dx, y + dy) for dx, dy in close]))
    hex_tree = STRtree(hexes)
    mass = mass_reader(raster, project)
    to_lonlat = raster_transform(project, raster.crs)
    district_mass = {}
    wonders = web("wonders")["wonders"]
    resources = web("resources")["items"]

    original = set(cohort())
    matches = {}
    for cid in cities:
        city, place = cities[cid], places[cid]
        point = Point(*to_map(place["x"], place["y"]))
        state = city["states"][0]
        candidates = []
        for row in centre_tree.query(point, predicate="covered_by"):
            gid = centre_ids[row]
            name, geom = centre_data[gid]
            candidates.append({"id": gid, "name": name, "contains": True,
                               "states": [state] if geom.intersection(states[state]).area > 0 else []})
        rule = rules.get(cid, {})
        ids = select_centres(city["name"], state, candidates, rule)
        if not ids:
            print(f"{cid} {city['name']}: point fallback. Containment candidates: {candidates}")
            continue
        footprint = shapely.union_all([centre_data[gid][1] for gid in ids]).intersection(land)
        if footprint.area > 0:
            matches[cid] = ids, footprint
    matches = exclusive_footprints(matches, original)
    limited = Event()
    api_counts = api_age_mass(
        {cid: shape for cid, (_, shape) in matches.items()},
        to_lonlat, age_api_cache, limited, cached_only=bool(ages),
    ) if age_api_cache else {}
    profiles = {}
    for cid, city in cities.items():
        if cid not in matches:
            profiles[cid] = point_profile(city)
            continue
        ids, footprint = matches[cid]
        state = city["states"][0]
        rule = rules.get(cid, {})
        intersected_states = sorted((abbr for abbr, geom in states.items() if geom.intersection(footprint).area > 0),
                                    key=lambda abbr: (abbr != state, abbr))
        if rule.get("required_states") and not set(rule["required_states"]).issubset(intersected_states):
            raise ValueError(f"{city['name']}: expected footprint to reach {rule['required_states']}, got {intersected_states}")
        cells = []
        for cell in sorted(hex_tree.query(footprint, predicate="intersects")):
            part = footprint.intersection(hexes[cell])
            if part.area:
                cells.append({"cell": int(cell), "hex_fraction": min(1, part.area / hexes[cell].area),
                              "footprint_share": min(1, part.area / footprint.area), "mass": mass(part)})
        if not cells or not sum(row["mass"] for row in cells):
            if cid in original:
                raise ValueError(f"{city['name']}: GHSL footprint has no usable WorldPop mass")
            print(f"{cid} {city['name']}: point fallback. No usable WorldPop footprint mass.")
            profiles[cid] = point_profile(city)
            continue
        members = []
        for row in district_tree.query(footprint, predicate="intersects"):
            district = district_ids[row]
            geom = districts[district]
            part = footprint.intersection(geom)
            if part.area <= 0:
                continue
            if district not in district_mass:
                district_mass[district] = mass(geom.intersection(land))
            total = district_mass[district]
            within = mass(part)
            members.append({"id": district, "footprint_share": min(1, part.area / footprint.area),
                            "district_population": round(total) if total else None,
                            "population_share": min(1, within / total) if total else None})
        members.sort(key=lambda row: (-row["footprint_share"], row["id"]))
        member_ids = {row["id"] for row in members}
        if not set(rule.get("required_districts", [])).issubset(member_ids):
            raise ValueError(f"{city['name']}: expected districts {rule['required_districts']}, got {sorted(member_ids)}")
        if member_ids.intersection(rule.get("excluded_districts", [])):
            raise ValueError(f"{city['name']}: re-audit district intersection {sorted(member_ids)}")
        nearby_wonders = set(rule.get("waterfront_wonders", []))
        excluded_resources = set(rule.get("excluded_resources", []))
        matched_wonders = []
        for wonder in wonders:
            point_at_site = Point(wonder["x"], wonder["y"])
            if footprint.covers(point_at_site) or (
                wonder["id"] in nearby_wonders and wonder["state"] == state and footprint.distance(point_at_site) <= 1.5
            ):
                matched_wonders.append(wonder["id"])
        profiles[cid] = {
            "method": "ghsl", "ghsl_ids": ids, "cells": cells, "districts": members, "states": intersected_states,
            "yield_rings": [list(ring.coords) for polygon in shapely.get_parts(footprint)
                            if polygon.geom_type == "Polygon" for ring in (polygon.exterior, *polygon.interiors)],
            "wonders": matched_wonders,
            "resources": [[r["type"], r["name"], r["x"], r["y"]] for r in resources
                          if r["name"] not in excluded_resources and "site_x" in r
                          and footprint.covers(Point(r["site_x"], r["site_y"]))],
        }
        cached = api_counts.get(cid, {})
        counts = {} if not ages or (cid in original and sum(cached.values())) else read_age_mass(
            footprint, ages, 0 if cid in original else MIN_RASTER_COVERAGE)
        if sum(counts.values()):
            profiles[cid]["age_mass"] = counts
        elif sum(cached.values()):
            profiles[cid].update(age_mass=cached, age_source=AGE_API_SOURCE)
        print(f"{cid} {city['name']}: GHSL {ids}, {len(cells)} hexes, districts {[m['id'] for m in members]}")
    geography = prepare_hex_geography(world, raster, land, hexes, districts, states, boundaries,
                                      ages, age_api_cache, limited)
    return profiles, geography


def prepare_hex_geography(world, raster, land, hexes, districts, states, boundaries, ages, age_api_cache, limited):
    """Sample only atlas-owned land in gaps, with no nearest-district assignment."""
    grid = HexGrid(**world["grid"])
    project = MapProjection(**world["projection"])
    district_ids = list(districts)
    district_tree = STRtree(list(districts.values()))
    internal = load_interim("_world")
    sorted_districts = sorted(boundaries["districts"], key=lambda d: (d["state_code"], d["code"]))
    sorted_states = sorted(boundaries["states"], key=lambda s: s["name"])
    homes = district_states(sorted_districts, sorted_states)
    indexes = {f"{row['state_code']:02d}-{row['code']:03d}": i
               for i, row in enumerate(sorted_districts)}
    areas = [mapped_area(row["rings"], project) for row in sorted_districts]
    support = [1 if area else None for area in areas]
    samples = internal["county_samples"]
    owner = world["owner"]
    density_extra = small_district_values(owner, samples, grid, project, sorted_districts, areas, support)
    density_values = district_sample_values(owner, samples, support, density_extra)
    tg = load_interim("tg_projections")
    state_age_inputs = load_interim(STATE_AGE_SOURCE)["profiles"]
    age_gaps = {row["abbr"] for row in world["states"] if
                (state_profile(tg, row["name"]) or {}).get("median_age") is None
                and state_age_inputs.get(row["name"], {}).get("median_age") is None}
    district_gaps = set(internal.get("district_gaps", [i for i, county in enumerate(world["county"]) if county < 0]))
    supported_mass = overlap_mass_reader(raster, project)
    density, counties, cell_age, state_age = {}, {}, {}, {}
    age_cells = {}
    for cell, (state, water) in enumerate(zip(owner, world["water"], strict=True)):
        if state < 0 or water:
            continue
        abbr = world["states"][state]["abbr"]
        if cell not in district_gaps and density_values[cell] is not None and abbr not in age_gaps:
            continue
        part = land.intersection(hexes[cell])
        if part.area <= 0:
            continue
        if cell in district_gaps:
            intersections = ((part.intersection(districts[district_ids[i]]).area, district_ids[i])
                             for i in district_tree.query(part, predicate="intersects")
                             if homes[indexes[district_ids[i]]] == state)
            area, district_id = max(intersections, default=(0, None))
            if area > 1e-6:
                counties[cell] = district_id
        if density_values[cell] is None:
            population, coverage = supported_mass(part)
            if coverage >= MIN_RASTER_COVERAGE:
                density[cell] = {"value": round(population / part.area, 3),
                                 "coverage": f"{coverage:.0%} of mapped land area"}
        if (ages or age_api_cache) and abbr in age_gaps:
            part = part.intersection(states[abbr])
            if part.area > 0:
                age_cells[cell] = part
    age_states = {}
    sample = mass_sampler(raster, project)
    for abbr in sorted(age_gaps):
        part = land.intersection(states[abbr])
        _, coverage = sample(part)
        if coverage >= MIN_RASTER_COVERAGE:
            age_states[abbr] = part
        else:
            print(f"{abbr}: {coverage:.1%} land pixel-centre coverage; state estimate withheld")
    targets = age_cells | age_states
    to_lonlat = raster_transform(project, raster.crs)
    api = api_age_mass(targets, to_lonlat, age_api_cache, limited, cached_only=bool(ages)) if age_api_cache else {}
    for key in targets:
        raster_counts = read_age_mass(targets[key], ages) if ages else {}
        counts = raster_counts if sum(raster_counts.values()) else api.get(key, {})
        if sum(counts.values()):
            (cell_age if isinstance(key, int) else state_age)[key] = {
                "value": round(median_age(counts), 2), "source": AGE_SOURCE if counts is raster_counts else AGE_API_SOURCE,
            }
    return {"districts": counties, "density": density, "cell_age": cell_age, "state_age": state_age}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ucdb", type=Path)
    parser.add_argument("worldpop", type=Path)
    parser.add_argument("--age-dir", type=Path, help="WorldPop India 2026 constrained 1 km age and sex GeoTIFFs")
    parser.add_argument("--age-api-cache", type=Path, help="WorldPop v3 response cache (reviewed cohort if both age inputs are supplied)")
    args = parser.parse_args()
    verify(args.ucdb, GHSL_CHECKSUM)
    verify(args.worldpop, CITY_POPULATION_CHECKSUM)
    world = web("world")
    if args.age_api_cache:
        args.age_api_cache.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        raster = stack.enter_context(rasterio.open(args.worldpop))
        ages = age_readers(stack, args.age_dir, raster, MapProjection(**world["projection"])) if args.age_dir else None
        profiles, geography = prepare(args.ucdb, raster, world, ages, args.age_api_cache)
    save_interim(GHSL_UCDB, {"grid_fingerprint": grid_fingerprint(world), "profiles": profiles},
                 vintage="GHS-UCDB R2024A v1.2 · reference epoch 2025")
    save_interim(CITY_POPULATION_GRID, {}, vintage="WorldPop R2025A v1 · 2026 population grid")
    save_interim(HEX_GEOGRAPHY, {"grid_fingerprint": grid_fingerprint(world), **geography}, vintage="mid-2026")
    if ages:
        save_interim(AGE_SOURCE, {}, vintage=f"WorldPop {AGE_RELEASE} · 2026 age and sex grids")
    if (any(profile.get("age_source") == AGE_API_SOURCE for profile in profiles.values())
            or any(row["source"] == AGE_API_SOURCE for group in ("cell_age", "state_age")
                   for row in geography[group].values())):
        save_interim(AGE_API_SOURCE, {}, vintage="WorldPop Global2 R2025A · 2026 API v3 age and sex")


if __name__ == "__main__":
    main()
