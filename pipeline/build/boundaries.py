"""Geometry and coverage rules for India's border, coast and territories."""

import math
from collections import defaultdict

from ..core.geo import ring_contains
from ..core.hexgrid import SQRT3

# DataMeet district codes distinguish the detached parts of each combined UT.
UT_PARTS = {
    "DH": (494, 495, 496),
    "PY": (634, 635, 636, 637),
}
UTS = {"AN", "CH", "DH", "DL", "JK", "LA", "LD", "PY"}

def chart_owner(shares):
    """Resolve a charted hex by water versus combined land, then by nationality."""
    india, foreign, water, uncharted = shares
    if uncharted >= max(india, foreign, water):
        return None
    if water > india + foreign:
        return "water"
    if india != foreign:
        return "india" if india > foreign else "foreign"
    return None


def named_indian_cells(grid, project, points, states):
    """Only Indian places protect land. Area controls named for a hex do not."""
    localities = defaultdict(list)
    for name, lon, lat, abbr in points:
        if abbr in states and not name.endswith(" hex"):
            cell = grid.cell_at(*project(lon, lat))
            if cell >= 0:
                localities[cell].append((name, states[abbr]))
    return localities


def guarantee_named_places(owner, water, localities, land):
    changed = {}
    for cell, places in localities.items():
        if owner[cell] >= 0:
            continue
        names, states = zip(*places)
        if len(set(states)) != 1:
            raise ValueError(f"Indian localities in different states share cell {cell}: {', '.join(names)}")
        owner[cell], water[cell] = states[0], land
        changed[cell] = names
    return changed


def check_chart(world, chart, decisions, localities):
    """Check ownership independently of the recorded rule and report the perimeter."""
    if ((chart["grid"], chart["projection"]) != (world["grid"], world["projection"])
            or len(chart["shares"]) != len(world["owner"])):
        return [], ["Political-map shares were prepared for a different grid"]
    islands, parts = set(decisions["islands"]), set(decisions["ut_parts"])
    named = {row["cell"] for row in decisions["named"]}
    boundary = set(chart["boundary"])
    rows, errors = [], []
    for cell, shares in enumerate(chart["shares"]):
        owner = world["owner"][cell]
        actual = "india" if owner >= 0 else {-1: "water", -2: "foreign"}[owner]
        vote = chart_owner(shares)
        protected = owner >= 0 and any(owner == state for _, state in localities.get(cell, ()))
        if cell in named and protected:
            rule = "named Indian locality"
        elif cell in parts:
            rule = "detached union territory"
        elif cell in islands:
            rule = "detached island"
        elif vote is None:
            rule = "incomplete or tied chart coverage"
        else:
            rule = "charted water majority" if vote == "water" else "charted national land majority"
        water_exception = actual == "india" and (protected or cell in islands)
        foreign_exception = actual == "india" and cell in named and protected
        if vote is not None and actual != vote and not (
            (vote == "water" and water_exception) or (vote == "foreign" and foreign_exception)
        ):
            errors.append(f"political map hex {cell}: {vote} majority, found {actual} ({rule})")
        if cell in boundary:
            rows.append({"cell": cell, "indian_km2": shares[0], "foreign_km2": shares[1],
                         "water_km2": shares[2], "uncharted_km2": shares[3], "owner": actual, "rule": rule})
    return rows, errors


def ring_moments(ring):
    """Twice the signed area and the centroid of a ring, in map km."""
    area = mx = my = 0.0
    ox, oy = ring[0]
    for (x, y), (u, v) in zip(ring, ring[1:] + ring[:1]):
        cross = (x - ox) * (v - oy) - (y - oy) * (u - ox)
        area += cross
        mx += (x + u - 2 * ox) * cross
        my += (y + v - 2 * oy) * cross
    return area, (ox + mx / (3 * area), oy + my / (3 * area)) if area else (ox, oy)


def clip_ring(ring, nx, ny, limit):
    """Clip a polygon ring against one half-plane of the convex hex."""
    points = []
    prev = ring[-1]
    a = nx * prev[0] + ny * prev[1] - limit
    for point in ring:
        b = nx * point[0] + ny * point[1] - limit
        if (a <= 0) != (b <= 0):
            t = a / (a - b)
            points.append(tuple(p + t * (q - p) for p, q in zip(prev, point)))
        if b <= 0:
            points.append(point)
        prev, a = point, b
    return points


def hex_overlap(grid, cell, shape):
    cx, cy = grid.center(*grid.col_row(cell))
    half_width = SQRT3 / 2 * grid.radius
    area = 0.0
    for ring in shape.rings:
        depth = sum(ring_contains(other, *ring[0]) for other in shape.rings if other is not ring)
        for nx, ny in ((1, 0), (-1, 0), (0.5, SQRT3 / 2), (-0.5, SQRT3 / 2),
                       (0.5, -SQRT3 / 2), (-0.5, -SQRT3 / 2)):
            ring = clip_ring(ring, nx, ny, half_width + nx * cx + ny * cy)
            if not ring:
                break
        if len(ring) >= 3:
            area += (-1) ** depth * abs(ring_moments(ring)[0]) / 2
    return area


def india_area_majority(grid, cell, outline):
    """Decide whether the official outline covers most of the hex."""
    cx, cy = grid.center(*grid.col_row(cell))
    radius = grid.radius
    size = outline.cell
    candidates = {
        i
        for gx in range(math.floor((cx - radius) / size), math.floor((cx + radius) / size) + 1)
        for gy in range(math.floor((cy - radius) / size), math.floor((cy + radius) / size) + 1)
        for i in outline.buckets.get((gx, gy), ())
    }
    area = sum(hex_overlap(grid, cell, outline.shapes[i]) for i in sorted(candidates))
    half_hex = 0.75 * SQRT3 * radius ** 2
    if math.isclose(area, half_hex, rel_tol=0, abs_tol=1e-8):
        return outline.locate(cx, cy) >= 0
    return area > half_hex


def overlaps(grid, shape):
    """Visit only hexes whose bounding boxes can intersect the shape."""
    x0, y0, x1, y1 = shape.bbox
    radius = grid.radius
    width = SQRT3 * radius
    height = 1.5 * radius
    for row in range(max(0, math.ceil((y0 - radius) / height)),
                     min(grid.rows, math.floor((y1 + radius) / height) + 1)):
        shift = 0.5 * (row & 1)
        for col in range(max(0, math.ceil(x0 / width - shift - 0.5)),
                         min(grid.cols, math.floor(x1 / width - shift + 0.5) + 1)):
            cell = grid.index(col, row)
            if (area := hex_overlap(grid, cell, shape)) > 1e-8:
                yield cell, area


def reserve_part(grid, owners, state, part):
    candidates = list(overlaps(grid, part))
    largest = max((ring_moments(ring) for ring in part.rings), key=lambda item: abs(item[0]))
    centre = grid.cell_at(*largest[1])
    present = [(cell, area) for cell, area in candidates if owners[cell] == state]
    cell, _ = max(present or candidates, key=lambda item: (round(item[1], 8), item[0] == centre))
    owners[cell] = state
    return cell


def nearest_state(x, y, states, limit=math.inf):
    """Find the nearest DataMeet state boundary within the optional distance limit."""
    best = limit, len(states.shapes)
    for state, shape in enumerate(states.shapes):
        x0, y0, x1, y1 = shape.bbox
        if math.hypot(max(x0 - x, x - x1, 0), max(y0 - y, y - y1, 0)) > best[0]:
            continue
        for ring in shape.rings:
            for (a, b), (u, v) in ring_edges(ring):
                dx, dy = u - a, v - b
                length_squared = dx * dx + dy * dy
                t = min(1, max(0, ((x - a) * dx + (y - b) * dy) / length_squared)) if length_squared else 0
                best = min(best, (math.hypot(x - a - t * dx, y - b - t * dy), state))
    return best[1] if best[1] < len(states.shapes) else -1


def ring_edges(ring):
    return zip(ring, ring[1:] + ring[:1])


def edge_buckets(a, b, size=20):
    for x in range(int(min(a[0], b[0]) // size), int(max(a[0], b[0]) // size) + 1):
        for y in range(int(min(a[1], b[1]) // size), int(max(a[1], b[1]) // size) + 1):
            yield x, y


def segments_touch(a, b, c, d):
    def cross(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    if any(max(min(a[i], b[i]), min(c[i], d[i])) > min(max(a[i], b[i]), max(c[i], d[i]))
           for i in (0, 1)):
        return False
    return cross(a, b, c) * cross(a, b, d) <= 0 and cross(c, d, a) * cross(c, d, b) <= 0


def touches_mainland(island, mainland, edges):
    if mainland.contains(*island.rings[0][0]):
        return True
    for ring in island.rings:
        for a, b in ring_edges(ring):
            for bucket in edge_buckets(a, b):
                if any(segments_touch(a, b, c, d) for c, d in edges.get(bucket, ())):
                    return True
    return False


def promote_islands(grid, owner, water, polygons, states, land, *, foreign_cells=()):
    """Give each uncovered detached SoI polygon a land hex at its largest overlap."""
    # The largest polygon is the mainland. Process the larger islands first so
    # a small nearby islet can share a land hex already reserved for its group.
    by_size = sorted(polygons, key=lambda shape: abs(ring_moments(shape.rings[0])[0]), reverse=True)
    mainland, *islands = by_size
    edges = defaultdict(list)
    for ring in mainland.rings:
        for a, b in ring_edges(ring):
            for bucket in edge_buckets(a, b):
                edges[bucket].append((a, b))
    promoted = 0
    for island in islands:
        candidates = [(cell, area) for cell, area in overlaps(grid, island) if cell not in foreign_cells]
        if not candidates or any(water[cell] == land for cell, _ in candidates) or touches_mainland(island, mainland, edges):
            continue
        cell, _ = max(candidates, key=lambda item: item[1])
        x, y = ring_moments(island.rings[0])[1]
        state = states.locate(x, y)
        if state < 0:
            state = nearest_state(x, y, states)
        owner[cell], water[cell] = state, land
        promoted += 1
    return promoted
