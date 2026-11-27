"""Aggregate the pinned WorldPop 2026 age grids within DataMeet districts."""

import argparse
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import rasterize

from ..core.store import load_interim, save_interim
from ..sources.worldpop_age import median_age
from .city_age_api import AGE_BANDS
from .city_sources import DISTRICT_AGE_SOURCE
from .city_view import ring_geometry


def district_medians(directory, districts):
    def path(sex, age):
        return directory / f"ind_{sex}_{age:02d}_2026_CN_1km_R2025A_UA_v1.tif"

    with rasterio.open(path("f", 0)) as raster:
        grid = (raster.crs, raster.transform, raster.shape)
    crs, transform, shape = grid
    project = Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform
    ids = [f"{d['state_code']:02d}-{d['code']:03d}" for d in districts]
    polygons = (ring_geometry(d["rings"], project) for d in districts)
    labels = rasterize(
        [(polygon, i) for i, polygon in enumerate(polygons, 1) if not polygon.is_empty],
        out_shape=shape, transform=transform, dtype="uint16",
    )
    counts = {age: np.zeros(len(ids) + 1) for age in AGE_BANDS}
    for age in AGE_BANDS:
        for sex in ("f", "m"):
            with rasterio.open(path(sex, age)) as raster:
                if (raster.crs, raster.transform, raster.shape) != grid:
                    raise ValueError(f"{raster.name}: inconsistent WorldPop age grid")
                for _, window in raster.block_windows(1):
                    y, x = window.toslices()
                    values = raster.read(1, window=window, masked=True).filled(0)
                    counts[age] += np.bincount(labels[y, x].ravel(), weights=values.ravel(),
                                              minlength=len(ids) + 1)
    medians = {}
    for i, geoid in enumerate(ids, 1):
        bands = {age: values[i] for age, values in counts.items()}
        if sum(bands.values()) > 0:
            medians[geoid] = round(median_age(bands), 1)
    return medians


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("age_dir", type=Path)
    args = parser.parse_args()
    districts = sorted((d for d in load_interim("datameet")["districts"] if d["code"]),
                       key=lambda d: (d["state_code"], d["code"]))
    medians = district_medians(args.age_dir, districts)
    save_interim(DISTRICT_AGE_SOURCE, {"districts": medians}, vintage="Mid-2026 WorldPop estimate")
    print(f"{len(medians)} of {len(districts)} atlas districts with WorldPop age estimates")


if __name__ == "__main__":
    main()
