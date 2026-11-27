"""Small, dependency-free geometry helpers.

Everything on the map lives in "map km": a Lambert azimuthal equal-area projection
centred on India, shifted so the top-left of the map is (0, 0) and y points *down*
(like screen coordinates). Both the hex grid and the browser use this space.
"""

from __future__ import annotations

import json
import math
import struct
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from typing import IO, Iterable, Iterator

from .hexgrid import SQRT3

R_EARTH_KM = 6371.0088


class Laea:
    """Ellipsoidal Lambert azimuthal equal-area, oblique aspect (Snyder 1987, eqs. 3-12, 24-27), output in km.

    WGS 84, centred on 22° N, 82° E: the same projection as IndiaCiv's axial hex grid (pipeline/india/grid.py).
    """

    def __init__(self, lat0=22.0, lon0=82.0, a=6378.137, inv_f=298.257223563):
        f = 1 / inv_f
        self.e2 = f * (2 - f)
        self.e = math.sqrt(self.e2)
        self.lon0 = math.radians(lon0)
        p0 = math.radians(lat0)
        qp = self._q(math.pi / 2)
        self.qp = qp
        self.rq = a * math.sqrt(qp / 2)
        self.b1 = math.asin(self._q(p0) / qp)
        m1 = math.cos(p0) / math.sqrt(1 - self.e2 * math.sin(p0) ** 2)
        self.d = a * m1 / (self.rq * math.cos(self.b1))

    def _q(self, phi: float) -> float:
        s, e = math.sin(phi), self.e
        return (1 - self.e2) * (s / (1 - self.e2 * s * s) - math.log((1 - e * s) / (1 + e * s)) / (2 * e))

    def __call__(self, lon: float, lat: float) -> tuple[float, float]:
        beta = math.asin(self._q(math.radians(lat)) / self.qp)
        dl = math.radians(lon) - self.lon0
        b = self.rq * math.sqrt(2 / (1 + math.sin(self.b1) * math.sin(beta) + math.cos(self.b1) * math.cos(beta) * math.cos(dl)))
        x = b * self.d * math.cos(beta) * math.sin(dl)
        y = (b / self.d) * (math.cos(self.b1) * math.sin(beta) - math.sin(self.b1) * math.cos(beta) * math.cos(dl))
        return x, y


@dataclass
class MapProjection:
    """lon/lat → map km (origin top-left, y down)."""

    min_x: float
    max_y: float
    margin: float

    def __post_init__(self):
        self._laea = Laea()

    @classmethod
    def hex_aligned(cls, min_x: float, max_y: float, margin: float, radius: float) -> "MapProjection":
        """A projection whose odd-r grid (pipeline/core/hexgrid.py) has a cell centre on every centre of
        IndiaCiv's axial grid (pipeline/india/grid.py), so cells sampled there drop onto the map exactly.

        The x shift is snapped to a whole cell width and the y shift to two rows, keeping row parity."""
        width, two_rows = SQRT3 * radius, 3 * radius
        shift_x = math.ceil((margin - min_x) / width) * width
        shift_y = math.ceil((max_y + margin) / two_rows) * two_rows
        return cls(margin - shift_x, shift_y - margin, margin)

    def from_projected(self, x: float, y: float) -> tuple[float, float]:
        """Projected km (y north) → map km."""
        return x - self.min_x + self.margin, self.max_y - y + self.margin

    def __call__(self, lon: float, lat: float) -> tuple[float, float]:
        return self.from_projected(*self._laea(lon, lat))

    def to_dict(self) -> dict:
        return {"min_x": self.min_x, "max_y": self.max_y, "margin": self.margin}


def ring_contains(ring: list[tuple[float, float]], x: float, y: float) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


class Shape:
    """A (multi)polygon as a bag of rings; even-odd rule handles holes."""

    def __init__(self, rings: Iterable[list[tuple[float, float]]]):
        self.rings = [r for r in rings if len(r) >= 3]
        xs = [p[0] for r in self.rings for p in r] or [0]
        ys = [p[1] for r in self.rings for p in r] or [0]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))

    def contains(self, x: float, y: float) -> bool:
        x0, y0, x1, y1 = self.bbox
        if x < x0 or x > x1 or y < y0 or y > y1:
            return False
        inside = False
        for r in self.rings:
            if ring_contains(r, x, y):
                inside = not inside
        return inside


class ShapeIndex:
    """Bucket shapes by coarse grid square so point lookups only test a few shapes."""

    def __init__(self, shapes: list[Shape], cell_km: float = 100.0):
        self.shapes = shapes
        self.cell = cell_km
        self.buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
        for k, s in enumerate(shapes):
            x0, y0, x1, y1 = s.bbox
            for gx in range(int(x0 // cell_km), int(x1 // cell_km) + 1):
                for gy in range(int(y0 // cell_km), int(y1 // cell_km) + 1):
                    self.buckets[(gx, gy)].append(k)

    def locate(self, x: float, y: float) -> int:
        for k in self.buckets.get((int(x // self.cell), int(y // self.cell)), ()):
            if self.shapes[k].contains(x, y):
                return k
        return -1


# --- file formats -----------------------------------------------------------

KML_NS = "{http://www.opengis.net/kml/2.2}"


def read_kml_placemarks(fileobj: IO[bytes]) -> Iterator[tuple[dict, list[list[tuple[float, float]]]]]:
    """Yield (properties, rings) for each Placemark in a Census cartographic KML."""
    for _, el in ET.iterparse(fileobj):
        if el.tag != KML_NS + "Placemark":
            continue
        props = {sd.get("name"): (sd.text or "") for sd in el.iter(KML_NS + "SimpleData")}
        rings = []
        for coords in el.iter(KML_NS + "coordinates"):
            pts = []
            for tok in (coords.text or "").split():
                lon, lat = tok.split(",")[:2]
                pts.append((round(float(lon), 5), round(float(lat), 5)))
            rings.append(pts)
        yield props, rings
        el.clear()


def read_shapefile(shp: bytes, dbf: bytes) -> Iterator[tuple[dict, list[list[tuple[float, float]]]]]:
    """Yield (attributes, rings) per record of a polygon shapefile (.shp + .dbf bytes). Character and numeric
    attributes come back as stripped strings; a null shape has no rings."""
    if len(shp) < 100 or struct.unpack(">i", shp[:4])[0] != 9994:
        raise ValueError("not a shapefile (.shp file code is not 9994)")
    n, hlen, rlen = struct.unpack("<IHH", dbf[4:12])
    fields, o = [], 32
    while dbf[o] != 0x0D:
        fields.append((dbf[o:o + 11].split(b"\0")[0].decode(), dbf[o + 16]))
        o += 32
    pos = 100
    for k in range(n):
        rec = dbf[hlen + k * rlen:hlen + (k + 1) * rlen]
        props, p = {}, 1  # byte 0 is the deletion flag
        for name, ln in fields:
            props[name] = rec[p:p + ln].decode("utf-8", "replace").strip()
            p += ln
        (length,) = struct.unpack(">i", shp[pos + 4:pos + 8])
        content = shp[pos + 8:pos + 8 + 2 * length]
        pos += 8 + 2 * length
        rings: list[list[tuple[float, float]]] = []
        if struct.unpack("<i", content[:4])[0] != 0:
            nparts, npts = struct.unpack("<2i", content[36:44])
            starts = list(struct.unpack(f"<{nparts}i", content[44:44 + 4 * nparts])) + [npts]
            xy = struct.unpack(f"<{2 * npts}d", content[44 + 4 * nparts:44 + 4 * nparts + 16 * npts])
            rings = [[(xy[2 * j], xy[2 * j + 1]) for j in range(a, b)] for a, b in zip(starts, starts[1:])]
        yield props, rings


def geojson_rings(geom: dict) -> list[list[tuple[float, float]]]:
    t, c = geom["type"], geom["coordinates"]
    polys = [c] if t == "Polygon" else c if t == "MultiPolygon" else []
    return [[(round(x, 5), round(y, 5)) for x, y, *_ in ring] for poly in polys for ring in poly]


def geojson_lines(geom: dict) -> list[list[tuple[float, float]]]:
    t, c = geom["type"], geom["coordinates"]
    lines = [c] if t == "LineString" else c if t == "MultiLineString" else []
    return [[(round(x, 5), round(y, 5)) for x, y, *_ in line] for line in lines]


def load_geojson(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["features"]


def bbox_intersects(points: Iterable[tuple[float, float]], bbox: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = bbox
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in points)
