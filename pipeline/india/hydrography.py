"""Prepare lake footprints and the Natural Earth Krishna distributary for the build."""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from . import KRISHNA_SHA256, LAKES_SHA256, PULICAT_SHA256
from ..core.store import save_interim

# Interior points on named courses, upstream of their terminal junctions.
# Coordinates are longitude, latitude.
RIVER_ANCHORS = {
    "Indus": (77.56, 33.99), "Ganga": (78.595, 30.134), "Brahmaputra": (91.69, 26.18),
    "Yamuna": (77.26, 28.60), "Zanskar": (77.16, 34.11), "Shyok": (77.60, 34.63),
    "Chenab": (74.73, 32.89), "Sutlej": (76.51, 30.96), "Jhelum": (74.82, 34.07),
    "Ravi": (75.60, 32.37), "Beas": (75.30, 31.52),
    "Bhagirathi": (78.45, 30.73), "Alaknanda": (78.79, 30.22),
    "Chambal": (75.82, 25.19), "Betwa": (78.64, 25.36), "Ken": (80.26, 25.47),
    "Ramganga": (78.76, 28.88), "Gomti": (80.94, 26.87), "Ghaghara": (82.18, 26.79),
    "Gandak": (84.18, 27.43), "Kosi": (86.78, 26.46), "Son": (84.12, 24.91),
    "Damodar": (87.32, 23.46),
    "Siang": (95.22, 28.20), "Dibang": (95.75, 28.18), "Lohit": (96.38, 27.93),
    "Subansiri": (94.26, 27.56), "Manas": (91.00, 26.72), "Teesta": (88.46, 26.88),
    "Barak": (92.80, 24.85), "Narmada": (77.72, 22.76), "Tapti": (73.14, 21.24),
    "Mahi": (73.04, 22.29), "Sabarmati": (72.57, 23.03), "Luni": (72.47, 25.82),
    "Periyar": (76.35, 10.11), "Sharavathi": (74.81, 14.23),
    "Mahanadi": (83.88, 21.58), "Tel": (83.85, 20.80), "Brahmani": (84.95, 22.19),
    "Baitarani": (86.12, 21.21), "Subarnarekha": (86.22, 22.79),
    "Godavari": (73.79, 20.01), "Pranhita": (79.90, 19.08), "Indravati": (81.96, 19.08),
    "Krishna": (80.60, 16.50), "Bhima": (75.32, 17.68), "Tungabhadra": (76.47, 15.34),
    "Pennar": (79.97, 14.46), "Kaveri": (75.97, 12.45), "Kabini": (76.44, 12.00),
    "Bhavani": (77.05, 11.29), "Vaigai": (78.12, 9.92),
}
LAKE_ANCHORS = {
    "Chilika": (85.37, 19.72), "Loktak": (93.80, 24.54), "Wular": (74.57, 34.36),
    "Dal": (74.87, 34.10), "Vembanad": (76.39, 9.63), "Pulicat": (80.25, 13.53),
    "Pangong Tso": (78.75, 33.78), "Sambhar": (75.04, 26.93),
    "Gobind Sagar": (76.49, 31.44), "Hirakud": (83.80, 21.59),
    "Indira Sagar": (76.58, 22.27), "Sardar Sarovar": (73.80, 21.92),
    "Nagarjuna Sagar": (79.21, 16.59), "Srisailam": (78.84, 16.08),
    "Gandhi Sagar": (75.51, 24.34), "Rihand": (83.02, 24.11),
}
BOUNDS = (59, 4, 105, 39)


def records(path, fields=None, bbox=BOUNDS):
    import shapefile

    with ZipFile(path) as archive:
        shp = next(name for name in archive.namelist() if name.endswith(".shp"))
        # Local files are seekable without inflating the archive for every seek.
        from tempfile import TemporaryDirectory

        with TemporaryDirectory(prefix="indiaciv-hydro-") as directory:
            for ext in (".shp", ".shx", ".dbf"):
                archive.extract(shp[:-4] + ext, directory)
            with shapefile.Reader(str(Path(directory) / shp), encodingErrors="replace") as source:
                yield from source.iterShapeRecords(fields=fields, bbox=bbox)


def lake_footprints(path):
    from shapely import Point, STRtree
    from shapely.geometry import shape

    candidates = []
    for item in records(path, ["Lake_name", "Lake_area"]):
        name, area = item.record["Lake_name"], item.record["Lake_area"]
        if area >= 1:
            candidates.append((name, area, shape(item.shape.__geo_interface__)))
    index = STRtree([geom for _, _, geom in candidates])
    labels = {}
    for name, anchor in LAKE_ANCHORS.items():
        point = Point(anchor)
        nearby = index.query(point, predicate="dwithin", distance=0.13)
        if not len(nearby):
            print(f"HydroLAKES has no mapped footprint near {name}; retaining its location")
            yield {"name": name, "point": list(anchor), "polygons": []}
            continue
        best = min(nearby, key=lambda i: (candidates[i][2].distance(point), -candidates[i][1], i))
        labels[best] = name
    for i, (name, area, geom) in enumerate(candidates):
        if i not in labels and area < 100:
            continue
        yield lake_feature(labels.get(i, name or ""), geom)


def lake_feature(name, geometry):
    point = geometry.representative_point()
    geom = geometry.simplify(0.002, preserve_topology=True)
    polygons = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    return {"name": name, "point": [point.x, point.y],
            "polygons": [[list(poly.exterior.coords), *(list(ring.coords) for ring in poly.interiors)]
                         for poly in polygons]}


def pulicat_footprint(path):
    from shapely import LineString, union_all
    from shapely.ops import polygonize

    elements = json.loads(path.read_text())["elements"]
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node"}
    ways = {e["id"]: LineString([nodes[node] for node in e["nodes"]])
            for e in elements if e["type"] == "way"}
    members = next(e["members"] for e in elements if e["type"] == "relation" and e["id"] == 1624070)
    outer = union_all(list(polygonize(ways[m["ref"]] for m in members if m["role"] == "outer")))
    inner = union_all(list(polygonize(ways[m["ref"]] for m in members if m["role"] == "inner")))
    return lake_feature("Pulicat", outer.difference(inner))


def verify(path, algorithm, expected):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, algorithm).hexdigest()
    if actual != expected:
        raise ValueError(f"{path}: {algorithm} mismatch ({actual})")


def krishna_distributary(path):
    features = json.loads(path.read_text())["features"]
    line = next(line for feature in features if feature["properties"]["name"] == "Krishna"
                for line in feature["geometry"]["coordinates"] if line[-1][0] > 80.8)
    # Keep the delta segment beginning below Vijayawada where the courses diverge.
    first = next(i for i, (_, lat) in enumerate(line) if lat < 16.45 and line[i][0] > 80.6)
    return {"name": "Krishna eastern distributary", "line": line[first - 1:], "trunk": "Krishna",
            "rank": 7, "mouth": True, "delta": True}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lakes", type=Path)
    parser.add_argument("--krishna", type=Path, help="Natural Earth 1:10m rivers GeoJSON")
    parser.add_argument("--pulicat", type=Path, help="OpenStreetMap relation 1624070 full JSON")
    args = parser.parse_args()
    if not (args.lakes or args.krishna or args.pulicat):
        parser.error("provide at least one source archive")
    if args.lakes:
        verify(args.lakes, "sha256", LAKES_SHA256)
        save_interim("hydrolakes", {"lakes": list(lake_footprints(args.lakes))})
    if args.krishna:
        verify(args.krishna, "sha256", KRISHNA_SHA256)
        save_interim("krishna_delta", {"course": krishna_distributary(args.krishna)})
    if args.pulicat:
        verify(args.pulicat, "sha256", PULICAT_SHA256)
        save_interim("pulicat", {"lake": pulicat_footprint(args.pulicat)})
