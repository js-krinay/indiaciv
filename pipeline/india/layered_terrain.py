"""Prepare terrain observations for the fixed India grid (see README)."""

import argparse
from collections import Counter
from hashlib import sha256
from math import ceil, floor
from pathlib import Path
import re
import warnings
from zipfile import ZipFile

from affine import Affine
import numpy as np
from pyproj import Transformer
import rasterio
from rasterio.errors import NotGeoreferencedWarning
from rasterio.features import rasterize, shapes
from rasterio.transform import from_bounds, from_origin
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds as window_from_bounds
from shapely import contains_xy
from shapely.geometry import Polygon, shape

from pipeline.core.store import load_interim, save_interim
from pipeline.india.grid import CRS, ORIGIN_X, ORIGIN_Y, RADIUS_METRES, vertices
from pipeline.india.terrain import raster_url
from pipeline.india.terrain_assets import ELEVATION, REEFS, elevation_name, prepare_assets

RELIEF_STEP = 500
FEATURE_STEP = 1000
MARSH_CLASSES = (9, 11, 13, 15, 17, 19, 23, 25, 27, 29)
NARCONDAM_BOUNDS = (94.2267, 13.4102, 94.2967, 13.4802)
NARCONDAM_SAMPLE_SHA = "d35d624d179b9a3cd1ddf4df45ff931f9bb0fb88b0b7a813e9e289d074ac80a3"


def surface(outline, step):
    west, south, east, north = outline["bounds"]
    west, north = floor(west / step) * step, ceil(north / step) * step
    size = (ceil((north - south) / step), ceil((east - west) / step))
    transform = from_origin(west, north, step, step)
    land = rasterize(
        (Polygon(rings[0], rings[1:]) for rings in outline["polygons"]),
        out_shape=size, transform=transform, dtype="uint8",
    ).astype(bool)
    return transform, land


def warp(paths, transform, size, *, nodata=255, dtype="uint8", resampling=Resampling.nearest):
    values = np.full(size, nodata, dtype=dtype)
    for path in paths:
        with rasterio.open(path) as source:
            reproject(
                rasterio.band(source, 1), values, dst_transform=transform, dst_crs=CRS,
                dst_nodata=nodata, init_dest_nodata=False, resampling=resampling,
            )
    return values


def local_window(transform, size, q, r, halo=0):
    polygon = Polygon(vertices(q, r))
    west, south, east, north = polygon.bounds
    col0, row0 = (~transform) * (west, north)
    col1, row1 = (~transform) * (east, south)
    rows = slice(max(0, floor(row0) - halo), min(size[0], ceil(row1) + halo))
    cols = slice(max(0, floor(col0) - halo), min(size[1], ceil(col1) + halo))
    x = transform.c + transform.a * (np.arange(cols.start, cols.stop) + .5)
    y = transform.f + transform.e * (np.arange(rows.start, rows.stop) + .5)
    return rows, cols, contains_xy(polygon, x[None, :], y[:, None])


def relief_stats(height, land, hex_mask):
    heights = height[land & hex_mask]
    if len(heights) < 12:
        return {}
    slope_y, slope_x = np.gradient(height, RELIEF_STEP)
    # Central differences crossing the coast or an absent sample are excluded.
    interior = land[1:-1, 1:-1] & land[:-2, 1:-1] & land[2:, 1:-1] & land[1:-1, :-2] & land[1:-1, 2:]
    slopes = np.degrees(np.arctan(np.hypot(slope_x, slope_y)))[1:-1, 1:-1]
    slopes = slopes[interior & hex_mask[1:-1, 1:-1]]
    if not slopes.size:
        return {}
    low, high = np.percentile(heights, [10, 90])
    return dict(spread=round(float(high - low), 1), slope=round(float(np.median(slopes)), 1),
                elevation=round(float(heights.mean())), upper=round(float(np.percentile(heights, 99))))


def patches(mask, transform, minimum):
    for geometry, _ in shapes(mask.astype("uint8"), mask=mask, transform=transform):
        polygon = shape(geometry)
        if polygon.area >= minimum:
            rings = polygon.simplify(FEATURE_STEP * .4, preserve_topology=True).__geo_interface__["coordinates"]
            yield rings


def geographic_patches(mask, transform, key, minimum, tolerance):
    project = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    for geometry, _ in shapes(mask.astype("uint8"), mask=mask, transform=transform):
        rings = []
        for ring in geometry["coordinates"]:
            xx, yy = project.transform(*zip(*ring))
            rings.append(list(zip(xx, yy)))
        polygon = Polygon(rings[0], rings[1:])
        if polygon.area >= minimum:
            yield {"key": key, "rings": polygon.simplify(tolerance).__geo_interface__["coordinates"]}


def reef_patches(directory):
    for region, (bounds, width, height, _) in REEFS.items():
        geographic = from_bounds(*map(float, bounds.split(",")), width, height)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
            with rasterio.open(directory / f"reef-{region}.png") as source:
                reef = source.read(4) >= 128
        yield from geographic_patches(reef, geographic, "reef", 45_000, 150)


def small_island_woods(directory):
    path = directory / "narcondam-worldcover.bin"
    if path.exists():
        pixels = path.read_bytes()
    else:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="25"):
            with rasterio.open(raster_url("cover", 12, 93)) as source:
                window = window_from_bounds(*NARCONDAM_BOUNDS, transform=source.transform)
                pixels = source.read(1, window=window, out_shape=(80, 80)).tobytes()
    if sha256(pixels).hexdigest() != NARCONDAM_SAMPLE_SHA:
        raise ValueError("Narcondam WorldCover window does not match its pinned sample")
    if not path.exists():
        path.write_bytes(pixels)
    cover = np.frombuffer(pixels, dtype="uint8").reshape(80, 80)
    yield from geographic_patches(cover == 10, from_bounds(*NARCONDAM_BOUNDS, 80, 80), "woods", 30_000, 75)


def prepare(directory, outline, cell_ids):
    relief_transform, relief_land = surface(outline, RELIEF_STEP)
    elevations = warp([directory / elevation_name(tile) for tile in ELEVATION], relief_transform, relief_land.shape,
                      nodata=-32768, dtype="float32", resampling=Resampling.bilinear)
    relief_land &= elevations != -32768

    transform, land = surface(outline, FEATURE_STEP)
    climate = warp([directory / "climate.tif"], transform, land.shape)
    wetland = warp([directory / "wetlands.tif"], transform, land.shape)
    wetland_area = warp([directory / "wetlands-area.tif"], transform, land.shape, nodata=0)
    flood = warp([directory / "flood.tif"], transform, land.shape)
    with ZipFile(directory / "mangroves.zip") as archive:
        # Global land coverage requires just the India neighbourhood from the tiled archive.
        paths = []
        for name in archive.namelist():
            if not name.endswith(".tif"):
                continue
            tile = re.search(r"N(\d{2})E(\d{3})", name, re.IGNORECASE)
            if not tile or not (6 <= int(tile[1]) <= 24 and 68 <= int(tile[2]) <= 97):
                continue
            paths.append(archive.extract(name, directory / "gmw"))
    if not paths:
        raise ValueError("No India tiles in the Global Mangrove Watch archive")
    mangrove = warp(paths, transform, land.shape)
    cells = {}
    footprints = [*reef_patches(directory), *small_island_woods(directory)]
    for cell_id in cell_ids:
        q, r = map(int, cell_id.split(":"))
        rs, cs, in_hex = local_window(relief_transform, relief_land.shape, q, r, halo=1)
        relief = relief_stats(elevations[rs, cs], relief_land[rs, cs], in_hex)
        rs, cs, in_hex = local_window(transform, land.shape, q, r)
        in_land = in_hex & land[rs, cs]
        wet = wetland[rs, cs]
        wet_share = wetland_area[rs, cs]
        classes = climate[rs, cs]
        # GLWD standing water is excluded from the climate land sample. The lake layer owns water geometry.
        standing_water = np.isin(wet, [1, 2, 3, 6]) & (wet_share >= 50)
        climate_mask = in_land & (classes > 0) & (classes <= 30) & ~standing_water
        counts = Counter(map(int, classes[climate_mask]))
        mapped = {}
        local = transform * Affine.translation(cs.start, rs.start)
        masks = {
            "marsh": np.isin(wet, MARSH_CLASSES) & in_land,
            # The GFPLAIN TIFF encodes mapped floodplain as 0 and other land as NoData (255).
            "floodplain": (flood[rs, cs] == 0) & in_land & ~standing_water & ~np.isin(wet, [4, 5, 28, 29, 32]),
            "salt_flat": (wet == 32) & in_hex,
            "mangrove": (mangrove[rs, cs] == 1) & in_hex,
        }
        for key, mask in masks.items():
            denominator = (in_hex if key in ("mangrove", "salt_flat") else in_land).sum()
            if not denominator or not mask.any():
                continue
            if key in ("marsh", "salt_flat"):
                # GLWD fractions describe the main class; avoid treating a sparse class as the entire pixel.
                mapped[key] = round(float(wet_share[mask].sum() / (100 * denominator)), 4)
                mask &= wet_share >= 30
            else:
                mapped[key] = round(float(mask.sum() / denominator), 4)
            # Above the tile threshold the colour and relief carry the wide floodplain or marsh.
            if key not in ("floodplain", "marsh") or mapped[key] < .10:
                minimum = FEATURE_STEP ** 2 * {"marsh": 5, "floodplain": 6}.get(key, 1)
                for rings in patches(mask, local, minimum):
                    footprints.append({"key": key, "rings": rings})
        cells[cell_id] = {"climate": dict(counts), "relief": relief, "mapped": mapped}
    return {
        "radius": RADIUS_METRES, "origin": [ORIGIN_X, ORIGIN_Y],
        "cells": cells, "footprints": footprints,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".cache/terrain-layers"))
    args = parser.parse_args()
    prepare_assets(args.directory)
    cover = load_interim("india_terrain")
    if (cover["radius"], cover["origin"]) != (RADIUS_METRES, [ORIGIN_X, ORIGIN_Y]):
        raise ValueError("Rerun pipeline.india.terrain for the current grid first")
    data = prepare(args.directory, load_interim("soi_outline"), [c["id"] for c in cover["cells"]])
    print(f"{len(data['cells'])} sampled cells and {len(data['footprints'])} feature footprints")
    save_interim("india_layered_terrain", data, vintage="Köppen–Geiger v3; ETOPO 2022; GLWD v2; GFPLAIN; GMW v3")


if __name__ == "__main__":
    main()
