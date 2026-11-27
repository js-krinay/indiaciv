"""Estimate crop production and choose representative resource tiles."""

import math

from ..sources.resource_references import FIELD_CROPS, GROWING_ANCHORS, GROWING_REGIONS, SITES
from .world import COAST, OCEAN

MIN_FIELD_CROPLAND = 10
# Coarse terrain checks keep these icons on the upland side of districts that
# also contain lowland cropland. Thresholds are map-scale mean elevations.
HILL_ELEVATION_MIN = {("tea", "19-327"): 800, ("tea", "33-611"): 1000,
                      ("coffee", "29-570"): 900}


def site_cell(grid, world, x, y, expected_owner, coastal=False):
    cell = grid.cell_at(x, y)
    if cell < 0:
        return -1
    owner, water = world["owner"], world["water"]
    if not coastal:
        return cell if owner[cell] == expected_owner else -1
    if owner[cell] >= 0 and owner[cell] != expected_owner:
        return -1
    candidates = [cell, *grid.neighbours(cell)]
    nearby = ((math.dist((x, y), grid.center(*grid.col_row(i))), i)
              for i in candidates if owner[i] == expected_owner
              and any(water[n] in (COAST, OCEAN) for n in grid.neighbours(i)))
    distance, closest = min(nearby, default=(math.inf, -1))
    return closest if distance <= 1.25 * grid.radius else -1


def world_elevation(world, rendered):
    for data in (world, rendered):
        if data and all(data.get(key) == world.get(key) for key in ("grid", "projection")):
            elevation = data.get("elev")
            if isinstance(elevation, list) and len(elevation) == len(world["owner"]):
                return elevation
    return None


def growing_cell(grid, world, state, district, cities, occupied, anchors=(), *, elevation=None, minimum=None,
                 canopy=True, crop_floor=1):
    crop, forest = (world["pct"][key] for key in ("crop", "forest"))
    candidates = []
    for i, (owner, county) in enumerate(zip(world["owner"], world["county"])):
        if owner != state or county != district or i in cities or i in occupied or forest[i] == 100:
            continue
        if minimum is not None and (elevation is None or elevation[i] < minimum):
            continue
        if not (crop[i] >= crop_floor or (canopy and 20 <= forest[i] <= 95)):
            continue
        distance = min((math.dist(grid.center(*grid.col_row(i)), point) for point in anchors), default=0)
        if distance <= 1.75 * grid.radius:
            candidates.append((distance, -crop[i], -forest[i], i))
    return min(candidates)[-1] if candidates else None


def crop_items(world, grid, project, cities, occupied, elevation):
    """Return resource markers for documented growing areas and sites."""
    state_indices = {code: i for i, code in enumerate(world["states"])}
    county_indices = {code: i for i, code in enumerate(world["counties"])}
    owner = world["owner"]
    occupied, items = set(occupied), []

    def item(kind, name, cell, source, period, detail, **metadata):
        x, y = grid.center(*grid.col_row(cell))
        return dict(type=kind, name=name, x=round(x, 1), y=round(y, 1), cell=cell,
                    value=None, detail=detail, state=world["states"][owner[cell]], cbsa=None,
                    source=source, period=period, **metadata)

    for kind, name, state, lat, lon, source, period in SITES:
        x, y = project(lon, lat)
        coastal = kind == "fish"
        cell = site_cell(grid, world, x, y, state_indices[state], coastal)
        if cell < 0:
            print(f"    ! {name}: no qualifying land cell")
            continue
        detail = "Fishing landing centre · land-side marker" if coastal else "Operating mine · approximate lease location"
        metadata = {}
        if kind == "battery":
            detail = "Commissioned battery storage · approximate project location"
        if name == "Sindesar Khurd mine":
            detail += " · silver by-product"
            metadata["byproducts"] = ["silver"]
        items.append(item(kind, name, cell, source, period, detail, **metadata))
        occupied.add(cell)

    for kind, name, state, district, source, period in GROWING_REGIONS:
        state_index = state_indices[state]
        anchors = [project(lon, lat) for lat, lon in GROWING_ANCHORS.get(source, ())]
        cell = growing_cell(grid, world, state_index, county_indices[district], cities, occupied, anchors,
                            elevation=elevation, minimum=HILL_ELEVATION_MIN.get((kind, district)),
                            canopy=kind not in FIELD_CROPS | {"silk"},
                            crop_floor=MIN_FIELD_CROPLAND if kind in FIELD_CROPS else 1)
        if cell is None and source == "thrissur_crops":
            # The source confirms these crops are intercropped in the same clusters.
            cell = growing_cell(grid, world, state_index, county_indices[district], cities, set(), anchors)
        if cell is not None:
            items.append(item(kind, name, cell, source, period, "Representative growing area",
                              estimated=True))
            occupied.add(cell)
        else:
            print(f"    ! {name}: no qualifying growing-area cell for {kind}")

    return items
