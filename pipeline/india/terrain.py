"""Summarize public raster layers over the atlas's projected hex grid."""

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from math import ceil, floor

from pyproj import Transformer
import rasterio
from shapely import contains_xy
from shapely.geometry import MultiPolygon, Polygon

from pipeline.core.store import load_interim, save_interim
from pipeline.india.grid import CRS, ORIGIN_X, ORIGIN_Y, RADIUS_METRES, center, cell_at

WORLD_COVER = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
COPERNICUS = "https://copernicus-dem-90m.s3.amazonaws.com/"
SAMPLE_INTERVAL = 5_000


def tile_code(lat, lon):
    return f"{'N' if lat >= 0 else 'S'}{abs(lat):02}{'E' if lon >= 0 else 'W'}{abs(lon):03}"


def raster_url(layer, lat, lon):
    tile = tile_code(lat, lon)
    if layer == "cover":
        return f"{WORLD_COVER}ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
    stem = f"Copernicus_DSM_COG_30_{tile[:3]}_00_{tile[3:]}_00_DEM"
    return f"{COPERNICUS}{stem}/{stem}.tif"


def read_tile(job):
    layer, (lat, lon), points = job
    url = raster_url(layer, lat, lon)
    try:
        with rasterio.open(url) as dataset:
            # Reading an overview limits transfers. Keep categorical classes intact.
            size = (min(dataset.height, 256), min(dataset.width, 256))
            values = dataset.read(1, out_shape=size, masked=True)
            result = []
            for cell, x, y in points:
                row, col = dataset.index(x, y)
                if 0 <= row < dataset.height and 0 <= col < dataset.width:
                    value = values[row * size[0] // dataset.height, col * size[1] // dataset.width]
                    if not getattr(value, "mask", False) and (layer != "cover" or value):
                        result.append((cell, float(value)))
            return layer, url, result, None
    except rasterio.errors.RasterioError as error:
        return layer, url, [], str(error)


def build(outline):
    geometry = MultiPolygon([Polygon(part[0], part[1:]) for part in outline["polygons"]])
    west, south, east, north = outline["bounds"]
    invert = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
    jobs = defaultdict(list)
    samples = Counter()
    for x in range(ceil(west / SAMPLE_INTERVAL) * SAMPLE_INTERVAL, ceil(east), SAMPLE_INTERVAL):
        ys = range(ceil(south / SAMPLE_INTERVAL) * SAMPLE_INTERVAL, ceil(north), SAMPLE_INTERVAL)
        valid = contains_xy(geometry, x, list(ys))
        for y, inside in zip(ys, valid):
            if not inside:
                continue
            cell = cell_at(x, y)
            lon, lat = invert.transform(x, y)
            samples[cell] += 1
            jobs["cover", (floor(lat / 3) * 3, floor(lon / 3) * 3)].append((cell, lon, lat))
            jobs["elevation", (floor(lat), floor(lon))].append((cell, lon, lat))

    values = {"cover": defaultdict(list), "elevation": defaultdict(list)}
    sources = []
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="20"):
        with ThreadPoolExecutor(max_workers=12) as pool:
            for layer, url, results, error in pool.map(read_tile, [(kind, tile, points) for (kind, tile), points in jobs.items()]):
                sources.append({"url": url, "samples": len(results), "error": error})
                for cell, value in results:
                    values[layer][cell].append(value)

    cells = []
    for cell in sorted(samples):
        cover = Counter(map(int, values["cover"][cell]))
        elevations = values["elevation"][cell]
        x, y = center(*cell)
        cells.append({
            "id": f"{cell[0]}:{cell[1]}",
            "x": round(x),
            "y": round(y),
            "cover": cover.most_common(1)[0][0] if cover else None,
            "covers": {str(code): count for code, count in sorted(cover.items())},
            "elevation": round(sum(elevations) / len(elevations)) if elevations else None,
            "relief": round(max(elevations) - min(elevations)) if elevations else None,
            "landSamples": samples[cell],
            "coverSamples": sum(cover.values()),
            "elevationSamples": len(elevations),
        })
    return {"radius": RADIUS_METRES, "origin": [ORIGIN_X, ORIGIN_Y], "sampleInterval": SAMPLE_INTERVAL, "cells": cells, "sources": sources}


if __name__ == "__main__":
    result = build(load_interim("soi_outline"))
    counts = Counter((cell["cover"] is not None, cell["elevation"] is not None) for cell in result["cells"])
    print(dict(counts))
    if not any(has_cover and has_elevation for has_cover, has_elevation in counts):
        raise SystemExit("No terrain cells have both source layers")
    save_interim("india_terrain", result, vintage="ESA WorldCover 2021 v200; Copernicus GLO-90")
