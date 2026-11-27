"""Prepare local per-hex areas from the IC-34 registered political-map vectors."""

import argparse
import json
from math import cos, radians, sin
from pathlib import Path

from shapely import clip_by_rect, from_wkb, intersection, make_valid, union_all
from shapely.geometry import Polygon
from shapely.strtree import STRtree

from pipeline.core.hexgrid import HexGrid
from pipeline.core.store import save_interim


def prepare(reference, world):
    grid = HexGrid(**world["grid"])
    offsets = [(grid.radius * cos(radians(i * 60 - 30)),
                grid.radius * sin(radians(i * 60 - 30))) for i in range(6)]
    centres = [grid.center(*grid.col_row(i)) for i in range(grid.size)]
    hexes = [Polygon([(x + dx, y + dy) for dx, dy in offsets]) for x, y in centres]
    tree = STRtree(hexes)
    paths = json.loads((reference / "reference.wkb.json").read_text())
    areas = {key: make_valid(from_wkb(bytes.fromhex(value))) for key, value in paths.items()}
    foreign, water = areas.pop("FOREIGN"), areas.pop("WATER")
    india = union_all(list(areas.values()), grid_size=.001)
    foreign = foreign.difference(india)
    water = water.difference(india).difference(foreign)
    shore = [Polygon(p.exterior).boundary for p in india.geoms if p.geom_type == "Polygon"]
    strokes = [from_wkb((reference / name).read_bytes())
               for name in ("national-line.wkb", "national-backing.wkb")]
    boundary = sorted({int(i) for i in tree.query(union_all([*shore, *strokes]), predicate="intersects")})
    shares = [[0.0, 0.0, 0.0, hexes[0].area] for _ in centres]
    # Clip to a buffered row strip before per-hex clipping. The buffer
    # contains each full hex and the strips assign every hex exactly once.
    for start in range(0, grid.rows, 8):
        end = min(start + 8, grid.rows)
        ids = range(start * grid.cols, end * grid.cols)
        ymin, ymax = centres[ids.start][1], centres[ids.stop - 1][1]
        for k, shape in enumerate((india, foreign, water)):
            strip = make_valid(clip_by_rect(shape, -2 * grid.radius, ymin - 2 * grid.radius,
                                           world["width"] + 2 * grid.radius, ymax + 2 * grid.radius))
            for i, piece in zip(ids, intersection(hexes[ids.start:ids.stop], strip)):
                amount = piece.area
                shares[i][k] = amount
                shares[i][3] -= amount
    return {"grid": world["grid"], "projection": world["projection"], "boundary": boundary,
            "shares": [[round(max(v, 0), 3) for v in row] for row in shares]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--world", type=Path, default=Path("web/data/world.json"))
    args = parser.parse_args()
    save_interim("soi_boundary_chart", prepare(args.reference, json.loads(args.world.read_text())),
                 vintage="Survey of India Political Map of India, English 13th edition (2026)")
