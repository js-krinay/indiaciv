"""Measure IC-6's 43 terrain anchors against a generated IndiaCiv world."""

import argparse
import json
from math import dist
from pathlib import Path

from pipeline.core.geo import MapProjection, Shape
from pipeline.core.hexgrid import HexGrid

FIXTURE = Path(__file__).with_name("terrain_places.json")


def unexpected_fields(site, missing):
    return [field for field in missing if field not in site.get("allowed_unmet", ())]


def pairs(flat):
    return list(zip(flat[::2], flat[1::2]))


def segment_distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = dx * dx + dy * dy
    if not length:
        return dist(point, a)
    t = max(0, min(1, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length))
    return dist(point, (a[0] + t * dx, a[1] + t * dy))


def nearby(shape, point, radius):
    x, y = point
    left, top, right, bottom = shape.bbox
    if not (left - radius <= x <= right + radius and top - radius <= y <= bottom + radius):
        return False
    return shape.contains(*point) or any(
        segment_distance(point, a, b) <= radius
        for ring in shape.rings for a, b in zip(ring, ring[1:] + ring[:1])
    )


def measure(world, fixtures):
    grid = HexGrid(**world["grid"])
    project = MapProjection(**world["projection"])
    tables = world["tables"]
    bases = {row["id"]: row["key"] for row in tables["base"]}
    relief = {row["id"]: row["name"] for row in tables["relief"]}
    keys = {row["id"]: row["key"] for row in tables["features"]}
    shapes = [(keys[row["id"]], Shape(pairs(ring) for ring in row["rings"]))
              for row in world["featureFootprints"]]
    sites = [(keys[row["id"]], pairs(row["line"]) if "line" in row else [row["point"]])
             for row in world["featureSites"]]
    centres = [grid.center(*grid.col_row(i)) for i in range(grid.size)]
    rows = []
    for site in fixtures:
        point = project(site["lon"], site["lat"])
        cell = grid.cell_at(*point)
        base, form = bases[world["base"][cell]], relief[world["relief"][cell]]
        features = {keys[x] for x in world["features"][cell]}
        missing = []
        if site["base"] and base not in site["base"]:
            missing.append("base")
        if site["relief"] and form not in site["relief"]:
            missing.append("relief")
        for requirement in site["features"]:
            names, _, radius = requirement.partition("@")
            allowed = set(names.split("/"))
            if "snow" in allowed and base == "snow" or allowed & features:
                continue
            if radius:
                km = float(radius)
                if any(key in allowed and nearby(shape, point, km) for key, shape in shapes):
                    continue
                if any(key in allowed and (
                    dist(point, points[0]) <= km if len(points) == 1 else
                    any(segment_distance(point, a, b) <= km for a, b in zip(points, points[1:]))
                ) for key, points in sites):
                    continue
                if allowed & {"woods", "rainforest"} and any(
                    dist(point, centre) <= km + grid.radius / 2
                    and allowed.intersection(keys[x] for x in world["features"][i])
                    for i, centre in enumerate(centres)
                ):
                    continue
            missing.append(requirement)
        rows.append((site, cell, base, form, sorted(features), missing))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", type=Path)
    args = parser.parse_args()
    fixtures = json.loads(FIXTURE.read_text())
    rows = measure(json.loads(args.world.read_text()), fixtures)
    print("| Place | Cell | Base | Relief | Cell features | Unmet | Explanation | Outside or deferred |")
    print("| --- | ---: | --- | --- | --- | --- | --- | --- |")
    for site, cell, base, form, features, missing in rows:
        explanation = site.get("exception", "Unexplained") if missing else ""
        print(f"| {site['name']} | {cell} | {base} | {form} | {', '.join(features)} | "
              f"{', '.join(missing)} | {explanation} | {site.get('other', '')} |")
    print()
    print(f"{sum(not r[-1] for r in rows)}/{len(rows)} anchors meet the encoded IC-9 checks.")
    if any(unexpected_fields(site, missing) for site, *_, missing in rows):
        raise SystemExit("One or more measurements differ from the fixture without an explanation.")


if __name__ == "__main__":
    main()
