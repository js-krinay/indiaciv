"""Generate local Canvas geometry from the official national outline archive."""

from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import shapefile
from pyproj import Transformer
from shapely import transform
from shapely.geometry import shape

from pipeline.core.store import save_interim
from pipeline.india.grid import CRS

CHECKSUM = "9e657f0c20ac4f4168e261b2c7d3fed4ed927a638a2fd411be9f6257463faf45"


def convert(path):
    if sha256(path.read_bytes()).hexdigest() != CHECKSUM:
        raise ValueError("Unexpected Survey of India outline archive")
    stem = "OUTLINE_OF_INDIA"
    with ZipFile(path) as archive, TemporaryDirectory() as temp:
        for extension in ("shp", "shx", "dbf"):
            archive.extract(f"{stem}.{extension}", temp)
        projection = archive.read(f"{stem}.prj").decode()
        project = Transformer.from_crs(projection, CRS, always_xy=True).transform
        with shapefile.Reader(str(Path(temp) / stem)) as source:
            polygons = [transform(shape(record.__geo_interface__), project, interleaved=False)
                        for record in source.iterShapes()]
    if len(polygons) != 1 or polygons[0].geom_type != "MultiPolygon":
        raise ValueError("Expected a single multipart national outline")
    boundary = polygons[0]
    return {
        "bounds": boundary.bounds,
        "polygons": [
            [
                [[round(x), round(y)] for x, y in ring.coords]
                for ring in (part.exterior, *part.interiors)
            ]
            for polygon in boundary.geoms
            for part in [polygon.simplify(150, preserve_topology=True)]
        ],
    }


if __name__ == "__main__":
    # Local only: Survey of India terms for redistributing this geometry are unresolved (docs/boundary-sources.md).
    save_interim("soi_outline", convert(Path(sys.argv[1])), vintage="Survey of India national outline, 2025-12-11")
