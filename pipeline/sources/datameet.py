import math

from ..core.geo import read_shapefile
from ..core.source import Source, SourceInfo

# Pinned to a commit so the content (and sha256) cannot change under the same URL.
COMMIT = "b3fbbde595310b397a55d718e0958ce249a4fa1f"
BASE = f"https://raw.githubusercontent.com/datameet/maps/{COMMIT}"
STATES = "States/Admin2"  # current states and union territories (36; Ladakh and J&K as of 2021)
DISTRICTS = "Districts/Census_2011/2011_Dist"  # the 640 Census 2011 districts, with their census codes
THIN_DEG = 0.01  # ~1 km: far below the 18 km hexes, and keeps point-in-polygon lookups fast


def thin(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Drop vertices closer than THIN_DEG to the last kept one (the closing vertex always stays)."""
    out = [ring[0]]
    for p in ring[1:-1]:
        if math.dist(p, out[-1]) >= THIN_DEG:
            out.append(p)
    out.append(ring[-1])
    return [(round(x, 4), round(y, 4)) for x, y in out]


class DataMeet(Source):
    info = SourceInfo(
        id="datameet",
        title="DataMeet community maps of India (states and Census 2011 districts)",
        publisher="DataMeet India community",
        homepage="https://projects.datameet.org/maps/",
        license="CC BY 4.0. India boundaries by DataMeet India community (https://github.com/datameet/maps).",
        description="Unofficial boundaries. The state and union-territory outlines decide each Indian hex's state; the "
        "district outlines (joined to Census table A-01 by district code: all 640 match) decide its "
        "district. India's outer extent still follows the Survey of India outline. "
        f"Files are pinned to datameet/maps commit {COMMIT[:7]}.",
        used_for=["State and union-territory borders", "Districts (hover, density lens)"],
    )

    def fetch(self, force=False):
        for stem in (STATES, DISTRICTS):
            for ext in ("shp", "dbf"):
                self.download(f"{BASE}/{stem}.{ext}", f"{stem}.{ext}", force=force, expect_binary=True)

    def _read(self, stem):
        shp, dbf = ((self.raw_dir / f"{stem}.{ext}").read_bytes() for ext in ("shp", "dbf"))
        for props, rings in read_shapefile(shp, dbf):
            yield props, [r for r in map(thin, rings) if len(r) >= 4]

    def process(self):
        states = [{"name": p["ST_NM"], "rings": rings} for p, rings in self._read(STATES)]
        districts = [
            {"code": int(p["censuscode"]), "state_code": int(p["ST_CEN_CD"]), "name": p["DISTRICT"], "rings": rings}
            for p, rings in self._read(DISTRICTS)
            if int(p["censuscode"] or 0) > 0  # one J&K polygon is "Data Not Available" with code 0: no district
        ]
        return {
            "vintage": f"DataMeet maps @ {COMMIT[:7]}",
            "_files": [f"{stem}.{ext}" for stem in (STATES, DISTRICTS) for ext in ("shp", "dbf")],
            "states": states,
            "districts": districts,
        }
