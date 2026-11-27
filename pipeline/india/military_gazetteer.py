"""Prepare civil place points from the pinned Natural Earth, GHSL and GeoNames datasets."""

import argparse
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from pyproj import Transformer
import shapefile

from pipeline.core.store import save_interim
from pipeline.build.military import BOARDS, COMMANDS, TOWN_ALIASES, name_key
from pipeline.india import GHSL_CHECKSUM
from pipeline.india.grid import CRS
from pipeline.india.military_sources import GEONAMES_CHECKSUM, GEONAMES_EDITION, NATURAL_EARTH_CHECKSUM


def natural_earth_places(path):
    if sha256(path.read_bytes()).hexdigest() != NATURAL_EARTH_CHECKSUM:
        raise ValueError("Unexpected Natural Earth Populated Places archive")
    project = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    places = []
    with shapefile.Reader(str(path)) as source:
        for item in source.iterShapeRecords():
            record = item.record.as_dict()
            if record["ADM0NAME"] != "India":
                continue
            longitude, latitude = item.shape.points[0]
            x, y = project.transform(longitude, latitude, errcheck=True)
            places.append({
                "id": str(record["NE_ID"]),
                "name": record["NAME"],
                "x": round(x),
                "y": round(y),
            })
    if not places or len({place["id"] for place in places}) != len(places):
        raise ValueError("Missing places or duplicate place IDs")
    return sorted(places, key=lambda place: place["name"])


def ghsl_places(path):
    if sha256(path.read_bytes()).hexdigest() != GHSL_CHECKSUM:
        raise ValueError("Unexpected GHSL Urban Centre Database archive")
    project = Transformer.from_crs("ESRI:54009", CRS, always_xy=True)
    with TemporaryDirectory() as tmp, ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.endswith(".gpkg"))
        with closing(sqlite3.connect(archive.extract(member, tmp))) as db:
            rows = db.execute("""
                SELECT g.ID_UC_G0, g.GC_UCN_MAI_2025, c.GC_UCC_LON_2025, c.GC_UCC_LAT_2025
                FROM GHSL_UCDB_THEME_GENERAL_CHARACTERISTICS_GLOBE_R2024A g
                JOIN UC_centroids c USING (ID_UC_G0)
                WHERE g.GC_CNT_GAD_2025 = 'India' AND g.GC_UCN_MAI_2025 IS NOT NULL
                ORDER BY g.ID_UC_G0
            """).fetchall()
    return [{"id": str(ident), "name": name, "x": round(x), "y": round(y)}
            for ident, name, east, north in rows if east is not None and north is not None
            for x, y in [project.transform(east, north, errcheck=True)]]


def geonames_places(path):
    if sha256(path.read_bytes()).hexdigest() != GEONAMES_CHECKSUM:
        raise ValueError("Unexpected GeoNames India archive")
    towns = {name_key(town) for names in BOARDS.values() for town in names}
    towns.update(name_key(town) for _, _, town, _, _ in COMMANDS)
    towns.update(map(name_key, TOWN_ALIASES.values()))
    project = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    places = []
    with ZipFile(path) as archive, archive.open("IN.txt") as source:
        for line in source:
            fields = line.decode("utf-8").rstrip("\n").split("\t")
            ident, name, ascii_name, aliases, lat, lon, category, code, country = fields[:9]
            if country != "IN" or category != "P" or code not in {"PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC"}:
                continue
            keys = towns.intersection(map(name_key, [name, ascii_name, *aliases.split(",")]))
            if keys:
                x, y = project.transform(float(lon), float(lat), errcheck=True)
                places.extend({"id": ident, "name": key, "x": round(x), "y": round(y)} for key in sorted(keys))
    return places


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("ne", "ghsl", "geonames"))
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.source == "ne":
        save_interim("ne_places", {"places": natural_earth_places(args.archive)},
                     vintage="Natural Earth Populated Places 5.1.2")
    elif args.source == "ghsl":
        save_interim("ghsl_town_centres", {"places": ghsl_places(args.archive)},
                     vintage="GHS-UCDB R2024A v1.2 · reference epoch 2025")
    else:
        save_interim("geonames_india", {"places": geonames_places(args.archive)}, vintage=GEONAMES_EDITION)
