"""Allocate district-level lens values to Indian hexes."""

import math

from ..core.hexgrid import SQRT3


def district_sample_values(
    owner: list[int], samples: list[list[int]], values: list[float | None],
    extra: dict[int, list[tuple[float, float]]] | None = None,
) -> list[float | None]:
    """Per hex: the mean value of the districts under its 7 sample points.
    `extra` adds districts no sample hits, {cell: [(value, share of the hex's area)]}: they take their share and
    the sampled districts the rest. Null off India and where nothing has a value."""
    out = []
    for i, (o, smp) in enumerate(zip(owner, samples)):
        vals = [v for k in smp if k >= 0 and (v := values[k]) is not None] if o >= 0 else []
        add = (extra or {}).get(i, []) if o >= 0 else []
        rest = 1 - sum(f for _, f in add)
        if not vals and not add:
            out.append(None)
        elif not vals:
            out.append(sum(d * f for d, f in add) / sum(f for _, f in add))
        else:
            out.append(sum(d * f for d, f in add) + rest * sum(vals) / len(vals))
    return out


def small_district_values(owner, samples, grid, proj, districts, areas, values):
    # Small districts between the sample points (Kolkata, Chennai, central Delhi…) go into the hex holding their
    # centre, weighted by their area (as usaciv does for Manhattan).
    hit = {k for smp in samples for k in smp if k >= 0}
    hex_area = 1.5 * SQRT3 * grid.radius ** 2
    extra: dict[int, list[tuple[float, float]]] = {}
    for k, (district, area, value) in enumerate(zip(districts, areas, values)):
        if k in hit or value is None or not area:
            continue
        ring = max(district["rings"], key=len)
        lon, lat = sum(p[0] for p in ring[:-1]) / (len(ring) - 1), sum(p[1] for p in ring[:-1]) / (len(ring) - 1)
        x, y = proj(lon, lat)
        cell = grid.cell_at(x, y)
        if cell >= 0 and owner[cell] < 0:  # a coastal city's centre on a sea hex: the nearest land neighbour
            land = [j for j in grid.neighbours(cell) if owner[j] >= 0]
            cell = min(land, key=lambda j: math.dist(grid.center(*grid.col_row(j)), (x, y))) if land else -1
        if cell >= 0:  # else islands with no land hex nearby (Lakshadweep): left out
            extra.setdefault(cell, []).append((value, min(1.0, area / hex_area)))
    return extra
