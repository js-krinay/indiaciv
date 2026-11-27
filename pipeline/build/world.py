"""The map itself: hex grid, land/water, relief, land cover, rivers.

The Survey of India political map and outline decide which hexes are India; DataMeet's (unofficial) state and
union-territory outlines decide each Indian hex's state, and its Census 2011 district outlines the hex's district.

Also saves interim "_world" (grid + projection + per-cell owner/water/cover)
so the other builders can drop their data onto the same hexes.
"""

from __future__ import annotations

import csv
import io
import json
import math
from collections import Counter
from pathlib import Path

from ..core.geo import MapProjection, Shape, ShapeIndex
from ..core.hexgrid import SQRT3, HexGrid
from ..core.paths import INTERIM
from ..core.store import atomic_write_text, load_interim, save_interim, write_web
from ..india import DISPLAY_NAMES
from ..india.grid import ORIGIN_X, ORIGIN_Y, RADIUS_METRES, center
from .boundaries import (
    UTS, UT_PARTS, chart_owner, check_chart, guarantee_named_places, hex_overlap, india_area_majority,
    named_indian_cells, nearest_state, promote_islands, reserve_part,
)
from .rivers import ESTUARIES, EdgeGraph, build_edges, build_lakes, check_hydrography, delta_courses, edge_masks
from ..core.source import osm_notice
from .terrain_layers import (
    BASE_TABLE, FEATURE_ID, FEATURE_TABLE, FLAT_SLOPE, FLAT_SPREAD, MOUNTAIN_SLOPE, MOUNTAIN_SPREAD,
    base_for, features_for, layer_errors, relief_for,
)
from ..india.terrain_validation import FIXTURE as TERRAIN_FIXTURE, measure, unexpected_fields

REQUIRES = ["soi_outline", "india_terrain", "india_layered_terrain", "natural_earth", "etopo", "datameet",
            "open_rivers", "hydrolakes", "krishna_delta", "pulicat", "soi_boundary_chart"]
BOUNDARY_FIXTURE = Path(__file__).with_name("soi_conformity.json")
PRODUCES = ["_world", "_boundary_decisions", "world.json"]

HEX_RADIUS_KM = RADIUS_METRES / 1000
MARGIN_KM = 200.0
# Two-letter state and union-territory codes (as on vehicle plates), by DataMeet's state name.
STATE_ABBR = {
    "Andaman & Nicobar": "AN", "Andhra Pradesh": "AP", "Arunachal Pradesh": "AR", "Assam": "AS", "Bihar": "BR",
    "Chandigarh": "CH", "Chhattisgarh": "CG", "Dadra and Nagar Haveli and Daman and Diu": "DH", "Delhi": "DL",
    "Goa": "GA", "Gujarat": "GJ", "Haryana": "HR", "Himachal Pradesh": "HP", "Jammu & Kashmir": "JK",
    "Jharkhand": "JH", "Karnataka": "KA", "Kerala": "KL", "Ladakh": "LA", "Lakshadweep": "LD", "Madhya Pradesh": "MP",
    "Maharashtra": "MH", "Manipur": "MN", "Meghalaya": "ML", "Mizoram": "MZ", "Nagaland": "NL", "Odisha": "OD",
    "Puducherry": "PY", "Punjab": "PB", "Rajasthan": "RJ", "Sikkim": "SK", "Tamil Nadu": "TN", "Telangana": "TS",
    "Tripura": "TR", "Uttar Pradesh": "UP", "Uttarakhand": "UK", "West Bengal": "WB",
}

# Cell owner codes (besides state index >= 0)
WATER, FOREIGN = -1, -2

# --- tables (written to world.json so the frontend and Almanac read one definition) ---------

LAND, OCEAN, COAST, LAKE = range(4)
TIDAL_SEA_SHARE = 0.5  # share of ETOPO samples below 0 m that keeps a sea-centred hex as water
COAST_DEPTH_M = -200
WATER_TABLE = [
    {"id": LAND, "name": "Land", "rule": "Charted land competes with charted water. The larger national share decides land ownership, with coverage for named Indian localities and detached islands."},
    {"id": OCEAN, "name": "Ocean", "color": "#1b4266", "rule": "Sea deeper than 200 m and not next to land."},
    {"id": COAST, "name": "Coast", "color": "#2d6d97", "rule": "Sea next to a land hex, or shallower than 200 m (ETOPO1 mean)."},
    {"id": LAKE, "name": "Lake", "color": "#3a80b0", "rule": "Water hex (most of its 7 sample points off land) with Natural Earth 1:50m lake points that outnumber sea points, or above sea level."},
]

WATER_NOTE = (
    "The Survey of India political map supplies charted water and land area per hex. "
    "Where its fill is incomplete, the national outline, Natural Earth and elevation samples classify the hex. "
    "Open-sea elevation uses the mean of ETOPO1 samples below sea level."
)

FLAT, HILLS, MOUNTAINS, PEAKS = range(4)
LAND_MIN_ALT_M = -100  # ETOPO samples below this inside a land hex are treated as sea floor
RELIEF_TABLE = [
    {"id": FLAT, "name": "Flat", "rule": "Elevation standard deviation inside the hex under 85 m."},
    {"id": HILLS, "name": "Hills", "rule": "Elevation standard deviation ≥ 85 m."},
    {"id": MOUNTAINS, "name": "Mountains", "rule": "Elevation standard deviation ≥ 260 m, or mean elevation ≥ 2,300 m."},
    {"id": PEAKS, "name": "Peaks", "rule": "Mean elevation ≥ 2,700 m (alpine)."},
]
RELIEF_NOTE = (
    "From ETOPO1 samples (~9 km apart, about 10 per hex) with altitude ≥ -100 m, so bays and sea floor don't "
    "count; all samples are used if none qualify. Water hexes are always flat."
)

URBAN_MIN_PCT = 30
CONIFER_MIN_ELEV_M = 2000  # WorldCover has one tree class; above this mean elevation it is drawn as conifer forest
# id, key, name, colour, WorldCover 2021 codes, rule. Ids are fixed by docs/DATA_CONTRACTS.md.
COVER = [
    (1, "forest_deciduous", "Broadleaf forest", "#4f7a35", [10], f"Tree cover (10) is the largest group and the hex's mean elevation is under {CONIFER_MIN_ELEV_M:,} m."),
    (2, "forest_evergreen", "Conifer forest", "#2f5a3a", [10], f"Tree cover (10) is the largest group and the hex's mean elevation is {CONIFER_MIN_ELEV_M:,} m or more (Himalayan forest)."),
    (3, "forest_mixed", "Mixed forest", "#43703f", [], "Not used: WorldCover does not separate forest types."),
    (4, "scrub", "Scrub & desert", "#c9b07a", [20], "Shrubland (20) is the largest group."),
    (5, "grassland", "Grassland", "#a9b35a", [30, 100], "Grassland (30) plus moss and lichen (100) is the largest group."),
    (6, "pasture", "Pasture", "#8fb04e", [], "Not used: WorldCover counts pasture as grassland."),
    (7, "cropland", "Cropland", "#c2b84e", [40], "Cropland (40) is the largest group."),
    (8, "wetland", "Wetland", "#4f8a6e", [90, 95], "Herbaceous wetland (90) plus mangroves (95) is the largest group."),
    (9, "urban", "Urban", "#8a8378", [50], f"Built-up (50) is ≥ {URBAN_MIN_PCT}% of the hex's land, whatever else is there."),
    (10, "barren", "Barren", "#bfae95", [60], "Bare or sparse vegetation (60: rock, sand, salt flats) is the largest group."),
    (11, "ice", "Ice & snow", "#e8eef2", [70], "Snow and ice (70) is the largest group."),
]
COVER_NOTE = (
    "From ESA WorldCover 2021 v200, sampled every 5 km inside the Survey of India outline (about 34 points per fully land hex). "
    "Permanent water (80) and no-data pixels are ignored; shares are of the remaining land points, rounded to whole "
    "percent, and the urban threshold is applied to the rounded built-up share. Foreign hexes have cover 0 (none)."
)
# Groups competing for the dominant cover (urban is decided by its threshold first).
GROUPS = {
    "forest": (10,), "scrub": (20,), "grassland": (30, 100), "cropland": (40,), "wetland": (90, 95), "barren": (60,), "ice": (70,),
}
GROUP_ID = {"scrub": 4, "grassland": 5, "cropland": 7, "wetland": 8, "barren": 10, "ice": 11}
URBAN_ID = 9
BUILT_UP, WORLDCOVER_WATER = 50, 80
PCT = {
    "forest": (10,), "crop": (40,), "pasture": (), "grass": (30, 100), "shrub": (20,), "wetland": (90, 95), "developed": (50,),
}


def classify_relief(mean: float, std: float) -> int:
    if mean >= 2700:
        return PEAKS
    if std >= 260 or mean >= 2300:
        return MOUNTAINS
    if std >= 85:
        return HILLS
    return FLAT


def is_valley_floor(samples: list) -> bool:
    """True when the lower 60% of a hex's land samples is flat lowland (within 60 m, under 400 m): the hex is mostly
    valley floor even if a range at its edge makes the whole hex's spread look hilly or mountainous."""
    if len(samples) < 6:
        return False
    v = sorted(samples)
    lo = v[: max(3, int(len(v) * 0.6))]
    return lo[-1] < 400 and lo[-1] - lo[0] < 60


def dominant_cover(counts: Counter, land: int, elev: float) -> int:
    """Cover id for a hex from its WorldCover class counts (land = points that are not water or no-data)."""
    if not land:
        return 0
    if round(100 * counts[BUILT_UP] / land) >= URBAN_MIN_PCT:  # same rounding as pct.developed
        return URBAN_ID
    best, best_n = None, 0
    for g, codes in GROUPS.items():  # dict order breaks ties
        n = sum(counts[c] for c in codes)
        if n > best_n:
            best, best_n = g, n
    if best is None:
        return 0  # only developed land below the urban threshold
    if best == "forest":
        return 2 if elev >= CONIFER_MIN_ELEV_M else 1
    return GROUP_ID[best]


def cell_layers(water, owner, observation, counts):
    if water != LAND or owner < 0:
        return base_for(water, {}, {}), []
    climate = {int(code): count for code, count in observation.get("climate", {}).items()}
    base = base_for(water, climate, counts)
    return base, features_for(base, climate, counts, observation.get("mapped", {}))


def simplify(points: list[tuple[float, float]], min_km: float) -> list[tuple[float, float]]:
    out = [points[0]]
    for p in points[1:-1]:
        if math.dist(p, out[-1]) >= min_km:
            out.append(p)
    out.append(points[-1])
    return out


def clip_segment(p, q, w, h):
    """Liang–Barsky: the part of segment p→q inside [0,w]×[0,h], or None."""
    (x0, y0), (x1, y1) = p, q
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for pk, qk in ((-dx, x0), (dx, w - x0), (-dy, y0), (dy, h - y0)):
        if pk == 0:
            if qk < 0:
                return None
            continue
        t = qk / pk
        if pk < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    return (x0 + t0 * dx, y0 + t0 * dy), (x0 + t1 * dx, y0 + t1 * dy)


def clip_polyline(pts, w, h) -> list[list[tuple[float, float]]]:
    """Split a polyline into the pieces that lie inside the map rectangle."""
    pieces, cur = [], []
    for p, q in zip(pts, pts[1:]):
        seg = clip_segment(p, q, w, h)
        if seg is None:
            if len(cur) >= 2:
                pieces.append(cur)
            cur = []
            continue
        a, b = seg
        if cur and math.dist(cur[-1], a) < 1e-9:
            cur.append(b)
        else:
            if len(cur) >= 2:
                pieces.append(cur)
            cur = [a, b]
        if b != q:  # left the map inside this segment
            pieces.append(cur)
            cur = []
    if len(cur) >= 2:
        pieces.append(cur)
    return pieces


def land_runs(pts, is_land, step: float = 2.0) -> list[list[tuple[float, float]]]:
    """Split a projected polyline (densified every `step` km) into the runs whose points satisfy is_land."""
    runs, cur = [], []
    for k, (p, q) in enumerate(zip(pts, pts[1:])):
        n = max(1, math.ceil(math.dist(p, q) / step))
        for j in range(0 if k == 0 else 1, n + 1):
            t = j / n
            pt = (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
            if is_land(pt):
                cur.append(pt)
            else:
                if len(cur) >= 2:
                    runs.append(cur)
                cur = []
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def join_lines(lines: list[list[tuple[float, float]]], tol: float = 0.5) -> list[list[tuple[float, float]]]:
    """Greedily join polylines whose ends meet (within `tol` km), reversing pieces as needed."""
    lines = [list(l) for l in lines]
    joined = True
    while joined:
        joined = False
        for a in range(len(lines)):
            for b in range(len(lines)):
                if a == b or not lines[a] or not lines[b]:
                    continue
                la, lb = lines[a], lines[b]
                for la2, lb2 in ((la, lb), (la, lb[::-1]), (la[::-1], lb), (la[::-1], lb[::-1])):
                    if math.dist(la2[-1], lb2[0]) <= tol:
                        lines[a] = la2 + lb2[1:]
                        lines[b] = []
                        joined = True
                        break
        lines = [l for l in lines if l]
    return lines


def hex_lattice(radius: float, step: float) -> list[tuple[float, float]]:
    """Offsets of a square lattice (spacing `step`) that fall inside a pointy-top hex."""
    half_w = SQRT3 / 2 * radius
    n = int(radius // step) + 1
    out = []
    for iy in range(-n, n + 1):
        for ix in range(-n, n + 1):
            x, y = (ix + 0.5) * step, (iy + 0.5) * step
            if abs(x) <= half_w and abs(y) <= radius - abs(x) / SQRT3:
                out.append((x, y))
    return out


def majority(values: list, centre) -> object:
    """Most common value; ties go to `centre` if it is among the tied, else to the first seen."""
    counts = Counter(values)
    top = max(counts.values())
    tied = [v for v in counts if counts[v] == top]
    return centre if centre in tied else tied[0]


def build() -> None:
    outline = load_interim("soi_outline")  # projected metres, y north (pipeline/india/outline.py)
    terrain = load_interim("india_terrain")  # cells of IndiaCiv's axial grid (pipeline/india/terrain.py)
    if (terrain["radius"], terrain.get("origin")) != (RADIUS_METRES, [ORIGIN_X, ORIGIN_Y]):
        raise ValueError("Terrain sampling grid differs from the world grid. Rerun pipeline.india.terrain.")
    try:
        layers = load_interim("india_layered_terrain")
    except FileNotFoundError:
        layers = None
    if layers and (layers["radius"], layers["origin"]) != (RADIUS_METRES, [ORIGIN_X, ORIGIN_Y]):
        raise ValueError("Rerun pipeline.india.layered_terrain for the current grid.")
    ne = load_interim("natural_earth")
    etopo = load_interim("etopo")
    dm = load_interim("datameet")

    states = sorted(dm["states"], key=lambda st: st["name"])
    unknown = [st["name"] for st in states if st["name"] not in STATE_ABBR]
    if unknown:
        raise ValueError(f"DataMeet states without a code in STATE_ABBR: {unknown}")
    districts = sorted(dm["districts"], key=lambda d: (d["state_code"], d["code"]))
    NO_STATE = len(states)  # inside the Survey of India outline but outside every DataMeet state polygon

    # Projection: fit India with a margin, snapped so IndiaCiv's terrain cells land on grid centres.
    west, south, east, north = (v / 1000 for v in outline["bounds"])
    origin_x, origin_y = ORIGIN_X / 1000, ORIGIN_Y / 1000
    aligned = MapProjection.hex_aligned(west - origin_x, north - origin_y, MARGIN_KM, HEX_RADIUS_KM)
    proj = MapProjection(aligned.min_x + origin_x, aligned.max_y + origin_y, MARGIN_KM)
    width = east - proj.min_x + 2 * MARGIN_KM
    height = proj.max_y - south + 2 * MARGIN_KM
    grid = HexGrid.covering(width, height, HEX_RADIUS_KM)
    print(f"    grid {grid.cols}×{grid.rows} = {grid.size} hexes of {HEX_RADIUS_KM:g} km")

    def shape(rings):
        return Shape([[proj(lon, lat) for lon, lat in r] for r in rings])

    india_idx = ShapeIndex(
        [Shape([[proj.from_projected(x / 1000, y / 1000) for x, y in ring] for ring in polygon]) for polygon in outline["polygons"]]
    )
    state_idx = ShapeIndex([shape(st["rings"]) for st in states])
    district_idx = ShapeIndex([shape(d["rings"]) for d in districts], cell_km=60)
    foreign_idx = ShapeIndex([shape(c["rings"]) for c in ne["countries"]], cell_km=200)
    lake_idx = ShapeIndex([shape(l["rings"]) for l in ne["lakes"]])

    # --- elevation statistics per hex (land samples and all samples) -----------------------------
    stats_all = [[0, 0.0, 0.0] for _ in range(grid.size)]
    stats_land = [[0, 0.0, 0.0] for _ in range(grid.size)]
    samples_land = [[] for _ in range(grid.size)]  # land altitudes, for the peak height and the valley-floor test
    below_sea = [0] * grid.size  # ETOPO samples below 0 m ...
    below_sum = [0.0] * grid.size  # ... and their altitude sum
    for lat, lon, alt in zip(etopo["lat"], etopo["lon"], etopo["alt"]):
        i = grid.cell_at(*proj(lon, lat))
        if i < 0:
            continue
        if alt < 0:
            below_sea[i] += 1
            below_sum[i] += alt
        for st in (stats_all[i], stats_land[i]) if alt >= LAND_MIN_ALT_M else (stats_all[i],):
            st[0] += 1
            st[1] += alt
            st[2] += alt * alt
        if alt >= LAND_MIN_ALT_M:
            samples_land[i].append(alt)

    def sea_share(i):
        return below_sea[i] / stats_all[i][0] if stats_all[i][0] else 0.0

    def mean_std(st):
        n, s1, s2 = st
        if not n:
            return None, None
        m = s1 / n
        return m, math.sqrt(max(0.0, s2 / n - m * m))

    # --- ownership: national outline and 7 sample points --------------------------------------------------
    # The centre plus six points 60% of the way to each corner. Each point is lake, a state, foreign
    # land or other water. Mixed inland national cells use SoI overlap. Mixed state cells use
    # DataMeet overlap area. All seven samples also give a district mix for lenses.
    offsets = [(0.0, 0.0)] + [
        (0.6 * HEX_RADIUS_KM * math.cos(math.radians(60 * k - 30)), 0.6 * HEX_RADIUS_KM * math.sin(math.radians(60 * k - 30)))
        for k in range(6)
    ]
    owner = [WATER] * grid.size
    water = [OCEAN] * grid.size
    chart = load_interim("soi_boundary_chart")
    if (chart["grid"], chart["projection"], len(chart["shares"])) != (grid.to_dict(), proj.to_dict(), grid.size):
        raise ValueError("The Survey of India political-map shares need to be regenerated for this grid")
    chart_votes = [chart_owner(shares) for shares in chart["shares"]]
    for i in range(grid.size):
        cx, cy = grid.center(*grid.col_row(i))
        kinds = []
        for dx, dy in offsets:
            x, y = cx + dx, cy + dy
            if lake_idx.locate(x, y) >= 0:
                kinds.append("lake")
            elif india_idx.locate(x, y) >= 0:
                kinds.append(st if (st := state_idx.locate(x, y)) >= 0 else NO_STATE)
            elif foreign_idx.locate(x, y) >= 0:
                kinds.append(FOREIGN)
            else:
                kinds.append("sea")
        land = [k for k in kinds if not isinstance(k, str)]
        m_all, _ = mean_std(stats_all[i])
        # Tidal creeks and estuaries are narrower than half a hex; keep them
        # water when the centre is sea and the hex is mostly at or below sea level in ETOPO1.
        tidal = kinds[0] == "sea" and m_all is not None and (m_all <= 0 or sea_share(i) >= TIDAL_SEA_SHARE)
        india = [k for k in land if k >= 0]
        centre = kinds[0]
        india_centred = isinstance(centre, int) and centre >= 0
        is_indian = india_centred or (centre != FOREIGN and len(india) >= 4 and not tidal)
        mixed_inland = (india and FOREIGN in land and "lake" not in kinds
                        and ("sea" not in kinds or (centre == "sea" and m_all is not None
                                                    and m_all > 0 and sea_share(i) < TIDAL_SEA_SHARE)))
        mixed_coast = india_centred and FOREIGN not in land and "sea" in kinds and "lake" not in kinds
        if chart_votes[i] == "water":
            water[i] = LAKE if lake_idx.locate(cx, cy) >= 0 else OCEAN
            continue
        if chart_votes[i] == "foreign":
            owner[i], water[i] = FOREIGN, LAND
            continue
        if chart_votes[i] == "india":
            is_indian = True
        elif mixed_inland or mixed_coast:
            is_indian = india_area_majority(grid, i, india_idx)
        if is_indian:
            placed = sorted(set(india) - {NO_STATE})
            if len(placed) > 1:
                owner[i] = max(placed, key=lambda k: (hex_overlap(grid, i, state_idx.shapes[k]), k == centre))
            else:
                owner[i] = placed[0] if placed else (
                    nearest_state(cx, cy, state_idx) if chart_votes[i] == "india" else NO_STATE
                )
            water[i] = LAND
        elif mixed_inland or (not mixed_coast and len(land) >= 4 and not tidal):
            owner[i], water[i] = FOREIGN, LAND
        else:
            wet = [k for k in kinds if isinstance(k, str)]
            # Points in neither the lake nor the land outlines are usually sea, but next to a lake they are
            # mostly gaps between the two datasets' shorelines, so a lake hex needs only to be above sea level.
            above_sea = m_all is not None and m_all > 0
            lakeish = "lake" in wet and (above_sea or majority(wet, kinds[0] if kinds[0] in wet else "lake") == "lake")
            water[i] = LAKE if lakeish else OCEAN

    # Sliver fix: the Survey of India and Natural Earth (1:50m) outlines don't meet exactly, leaving water hexes
    # on land along the borders. A non-lake water hex whose ETOPO mean is above sea
    # level becomes land if at least 4 of its neighbours are land, or if it touches both Indian and foreign land.
    # The sliver fill extends neighbouring land only. India needs direct outline evidence.
    slivers = []
    for i in range(grid.size):
        if water[i] != OCEAN or chart_votes[i] == "water":
            continue
        m, _ = mean_std(stats_all[i])
        land_nb = [owner[j] for j in grid.neighbours(i) if water[j] == LAND]
        border = FOREIGN in land_nb and any(o >= 0 for o in land_nb)
        if m is not None and m > 0 and sea_share(i) < TIDAL_SEA_SHARE and (len(land_nb) >= 4 or border):
            slivers.append(i)
    for i in slivers:
        owner[i], water[i] = FOREIGN, LAND
    print(f"    {len(slivers)} sliver water hexes turned into land: {slivers}")

    # Indian hexes that no DataMeet state covers (coastline and border mismatches with the Survey of India outline)
    # take the most common state among their neighbours, spreading inward until every one has a state.
    unplaced = [i for i in range(grid.size) if owner[i] == NO_STATE]
    todo = list(unplaced)
    while todo:
        later = []
        for i in todo:
            nb = [owner[j] for j in grid.neighbours(i) if 0 <= owner[j] < NO_STATE]
            if nb:
                owner[i] = Counter(nb).most_common(1)[0][0]
            else:
                later.append(i)
        if len(later) == len(todo):
            raise ValueError(f"{len(later)} Indian hexes have no state and no neighbour with one")
        todo = later
    print(f"    {len(unplaced)} Indian hexes outside every DataMeet state took their neighbours' state")

    before_islands = owner.copy()
    foreign_cells = {i for i, vote in enumerate(chart_votes) if vote == "foreign"}
    promoted = promote_islands(grid, owner, water, india_idx.shapes, state_idx, LAND, foreign_cells=foreign_cells)
    island_cells = {i for i, before in enumerate(before_islands) if owner[i] != before}
    print(f"    {promoted} land hexes added for detached Survey of India islands")

    before_ut_parts = owner.copy()
    part_counties = {}
    for state, record in enumerate(states):
        abbr = STATE_ABBR[record["name"]]
        if abbr not in UTS:
            continue
        if abbr in UT_PARTS:
            for district, record in enumerate(districts):
                if record["code"] in UT_PARTS[abbr]:
                    cell = reserve_part(grid, owner, state, district_idx.shapes[district])
                    part_counties[cell] = district
                    water[cell] = LAND
        elif state not in owner:
            cell = reserve_part(grid, owner, state, state_idx.shapes[state])
            water[cell] = LAND

    points = json.loads(BOUNDARY_FIXTURE.read_text())["points"]
    state_ids = {STATE_ABBR[record["name"]]: i for i, record in enumerate(states)}
    localities = named_indian_cells(grid, proj, points, state_ids)
    named = guarantee_named_places(owner, water, localities, LAND)
    named_places = [{"cell": i, "names": names, "shares": chart["shares"][i]}
                    for i, names in sorted(named.items())]
    ut_cells = [i for i, before in enumerate(before_ut_parts) if i not in named and owner[i] != before]

    # --- Census 2011 districts for Indian cells (the "county" of USACiv) --------------------------
    county = [-1] * grid.size
    county_samples: list[list[int]] = [[] for _ in range(grid.size)]
    for i in range(grid.size):
        if owner[i] >= 0:
            cx, cy = grid.center(*grid.col_row(i))
            county_samples[i] = [district_idx.locate(cx + dx, cy + dy) for dx, dy in offsets]
    borrowed = 0
    for i, smp in enumerate(county_samples):
        if smp and max(smp) < 0:  # all seven points miss the district outlines: borrow the neighbours' district
            nb = [k for j in grid.neighbours(i) for k in county_samples[j] if k >= 0]
            if nb:
                smp[0] = Counter(nb).most_common(1)[0][0]
                borrowed += 1
        valid = [k for k in smp if k >= 0]
        if valid:
            county[i] = smp[0] if smp[0] >= 0 else Counter(valid).most_common(1)[0][0]
    # Keep the named part on the map while preserving geographic samples for district density.
    for cell, district in part_counties.items():
        county[cell] = district
    print(f"    {borrowed} Indian hexes borrowed a neighbour's district; {sum(1 for i in range(grid.size) if owner[i] >= 0 and county[i] < 0)} have none")
    geoids = [f"{d['state_code']:02d}-{d['code']:03d}" for d in districts]  # Census table A-01 keys
    states_out = [{"fips": STATE_ABBR[st["name"]], "abbr": STATE_ABBR[st["name"]], "name": st["name"]} for st in states]

    lake_sources = [lake for lake in load_interim("hydrolakes")["lakes"] if lake["name"] != "Pulicat"]
    lakes = build_lakes(grid, [*lake_sources, load_interim("pulicat")["lake"]], proj, water)

    # --- elevation, water depth classes and relief -------------------------------------------------
    elev = [0] * grid.size
    relief = [FLAT] * grid.size
    elev_max = [0] * grid.size  # highest land sample (m): snow on high ranges whose mean is held down by valleys
    valley_floor = 0
    no_elev = 0
    for i in range(grid.size):
        if water[i] == LAND:
            m, sd = mean_std(stats_land[i])
            if m is None:
                m, sd = mean_std(stats_all[i])
                m = None if m is None else max(m, 0.0)
            if m is None:
                no_elev += 1
                continue  # elev 0, flat
            elev[i] = round(m)
            relief[i] = classify_relief(max(m, 0.0), sd)
            if relief[i] in (HILLS, MOUNTAINS) and is_valley_floor(samples_land[i]):
                relief[i] -= 1  # mostly flat lowland with a range at one edge (the Central Valley's rim)
                valley_floor += 1
            if samples_land[i]:
                elev_max[i] = max(0, round(max(samples_land[i])))
        else:
            m, _ = mean_std(stats_all[i])
            if m is None:
                no_elev += 1
                elev[i] = -4000  # outside the elevation window: assume deep ocean
            elif water[i] != LAKE and below_sea[i]:
                elev[i] = round(below_sum[i] / below_sea[i])  # sea: mean depth of the samples under water
            else:
                elev[i] = min(round(m), 0)
            if water[i] == OCEAN:
                near_land = any(water[j] == LAND for j in grid.neighbours(i))
                water[i] = COAST if near_land or elev[i] > COAST_DEPTH_M else OCEAN
    print(f"    {no_elev} hexes without elevation samples; {valley_floor} valley-floor hexes eased one relief class")

    # --- land cover from WorldCover samples -------------------------------------------------------
    legacy_elevation = elev.copy()
    counts_at: dict[int, Counter] = {}
    layers_at = {}
    for c in terrain["cells"]:
        q, r = map(int, c["id"].split(":"))
        x, y = center(q, r)
        i = grid.cell_at(*proj.from_projected(x / 1000, y / 1000))
        if i >= 0 and c["covers"]:
            counts_at[i] = Counter({int(code): n for code, n in c["covers"].items()})
        if i >= 0 and layers and c["id"] in layers["cells"]:
            layers_at[i] = layers["cells"][c["id"]]
            obs = layers_at[i]["relief"]
            if water[i] == LAND and owner[i] >= 0 and obs:
                elev[i], elev_max[i] = obs["elevation"], obs["upper"]
                relief[i] = relief_for(obs["spread"], obs["slope"])
    cover = [0] * grid.size
    pct = {k: [0] * grid.size for k in PCT}
    no_cover = 0
    for i in range(grid.size):
        if owner[i] < 0 or water[i] != LAND:
            continue
        if layers and not layers_at.get(i, {}).get("relief"):
            # On a subpixel island the coarse relief sample mostly describes the sea floor.
            # Leave insufficiently supported land relief visually flat.
            relief[i] = FLAT
        counts = counts_at.get(i, Counter())
        land = sum(n for code, n in counts.items() if code != WORLDCOVER_WATER)
        cover[i] = dominant_cover(counts, land, legacy_elevation[i])
        if not land:
            no_cover += 1
            continue
        for k, codes in PCT.items():
            pct[k][i] = round(100 * sum(counts[c] for c in codes) / land)
    print(f"    {len(counts_at)} hexes with WorldCover samples; {no_cover} Indian hexes without land-cover samples")

    # --- rivers ----------------------------------------------------------------------------------
    courses = load_interim("open_rivers")["courses"]
    delta = [*delta_courses(ne["rivers"]), load_interim("krishna_delta")["course"]]
    # Lake centerlines are kept only where they cross land hexes (reservoirs narrower than half a hex,
    # e.g. Lake Sakakawea or Lake Mead), so rivers don't stop in the middle of land; over water hexes they go.
    def on_land(pt):
        c = grid.cell_at(*pt)
        return c >= 0 and water[c] == LAND

    by_river: dict[tuple, list] = {}
    for r in ne["rivers"]:
        if r["rank"] > 8:
            continue
        line = [proj(lon, lat) for lon, lat in r["line"]]
        if (r.get("featurecla") or "").startswith("Lake Centerline"):
            parts = [run for p in clip_polyline(line, width, height) for run in land_runs(p, on_land)]
        else:
            parts = clip_polyline(line, width, height)
        by_river.setdefault((r["name"], r["rank"]), []).extend(parts)
    rivers = []
    for (name, rank), parts in by_river.items():
        for piece in join_lines(parts):
            if sum(math.dist(a, b) for a, b in zip(piece, piece[1:])) < 1.0:
                continue  # a corner clipped down to nothing
            pts = simplify(piece, 4.0)
            if len(pts) >= 2:
                rivers.append({"name": name, "rank": rank, "pts": [round(v, 1) for p in pts for v in p]})
    river_graph = EdgeGraph(grid, water)
    river_junctions = []
    river_edges = build_edges(river_graph, [*ESTUARIES, *courses, *delta], proj, simplify,
                              clip_polyline, width, height, rivers, river_junctions)

    cover_table = [{"id": 0, "key": "none", "name": "None", "rule": "Water, foreign land, or no WorldCover land samples."}] + [
        {"id": cid, "key": key, "name": name, "color": color, "worldcover": codes, "rule": rule}
        for cid, key, name, color, codes, rule in COVER
    ]
    tables = {
        "water": WATER_TABLE,
        "relief": RELIEF_TABLE,
        "cover": cover_table,
        "notes": {"water": WATER_NOTE, "relief": RELIEF_NOTE, "cover": COVER_NOTE},
        "named_boundary_places": named_places,
    }
    layered_fields = {}
    if layers:
        base, features = [], []
        for i in range(grid.size):
            base_id, cell_features = cell_layers(water[i], owner[i], layers_at.get(i, {}), counts_at.get(i, {}))
            base.append(base_id)
            features.append(cell_features)
        footprints = [
            {"id": FEATURE_ID[p["key"]], "rings": [
                [round(v, 2) for x, y in ring for v in proj.from_projected(x / 1000, y / 1000)]
                for ring in p["rings"]
            ]}
            for p in layers["footprints"]
        ]
        sites = []
        for site in json.loads(Path(__file__).resolve().parents[1]
                               .joinpath("india", "terrain_sites.json").read_text()):
            geometry = ({"point": [round(v, 2) for v in proj(*site["point"])]} if "point" in site else
                        {"line": [round(v, 2) for pt in site["line"] for v in proj(*pt)]})
            sites.append({"id": FEATURE_ID[site["key"]], "name": site["name"], **geometry})
        tables.update(base=BASE_TABLE, features=FEATURE_TABLE, relief=[
            {"id": 0, "name": "Flat", "color": "#aba575", "rule": f"Elevation spread below {FLAT_SPREAD} m and median slope below {FLAT_SLOPE}°. Sparse Indian cells use a flat fallback.", "example": "Punjab plain"},
            {"id": 1, "name": "Hills", "color": "#91805d", "rule": "Rolling or dissected terrain below either mountain threshold.", "example": "Aravalli"},
            {"id": 2, "name": "Mountains", "color": "#766b60", "rule": f"Elevation spread of at least {MOUNTAIN_SPREAD} m and median slope of at least {MOUNTAIN_SLOPE}°.", "example": "Greater Himalaya"},
            {"id": 3, "name": "Peaks", "color": "#bbb9b7", "rule": "Legacy elevation-based relief where detailed samples are unavailable.", "example": "Himalayan borderlands"},
        ])
        tables["notes"]["relief"] = ("ETOPO surface sampled at 500 m on Indian land. Spread is the gap between "
                                     "the 10th and 90th elevation percentiles.")
        examples = []
        for fixture in json.loads(TERRAIN_FIXTURE.read_text()):
            cell = grid.cell_at(*proj(fixture["lon"], fixture["lat"]))
            if cell < 0 or (owner[cell] < 0 and not water[cell]):
                continue
            row = {"name": fixture["name"], "cell": cell}
            if BASE_TABLE[base[cell]]["key"] in fixture["base"]:
                row["base"] = base[cell]
            if not water[cell] and tables["relief"][relief[cell]]["name"] in fixture["relief"]:
                row["relief"] = relief[cell]
            expected = {key for req in fixture["features"] for key in req.split("@")[0].split("/")}
            row["features"] = [FEATURE_ID[key] for key in sorted(expected)
                               if key in FEATURE_ID and FEATURE_ID[key] in features[cell]]
            examples.append(row)
        tables["terrain_examples"] = examples

        intersections = {}
        for footprint in footprints:
            shape = Shape(list(zip(ring[::2], ring[1::2])) for ring in footprint["rings"])
            x0, y0, x1, y1 = shape.bbox
            cells = intersections.setdefault(footprint["id"], set())
            for r in range(max(0, int(y0 / (1.5 * grid.radius)) - 1), min(grid.rows, int(y1 / (1.5 * grid.radius)) + 2)):
                for c in range(max(0, int(x0 / (SQRT3 * grid.radius)) - 1), min(grid.cols, int(x1 / (SQRT3 * grid.radius)) + 2)):
                    cell = grid.index(c, r)
                    if (owner[cell] >= 0 or water[cell]) and hex_overlap(grid, cell, shape) > 0:
                        cells.add(cell)
        for site in sites:
            points = [site["point"]] if "point" in site else list(zip(site["line"][::2], site["line"][1::2]))
            cells = intersections.setdefault(site["id"], set())
            for point in points:
                cell = grid.cell_at(*point)
                if cell >= 0 and (owner[cell] >= 0 or water[cell]):
                    cells.add(cell)
        tables["feature_cells"] = {key: sorted(cells) for key, cells in intersections.items()}
        layered_fields = {"base": base, "features": features, "featureFootprints": footprints, "featureSites": sites}
    write_web(
        "world.json",
        {
            "version": 2,
            "grid": grid.to_dict(),
            "projection": proj.to_dict(),
            "width": round(width, 1),
            "height": round(height, 1),
            "margin": MARGIN_KM,
            "owner": owner,
            "county": county,
            "elev": elev,
            "elev_max": elev_max,
            "water": water,
            "relief": relief,
            "cover": cover,
            "pct": pct,
            "tables": tables,
            "states": states_out,
            "counties": [{"geoid": g, "name": DISPLAY_NAMES.get(d["name"], d["name"])} for g, d in zip(geoids, districts)],
            "rivers": rivers,
            "river_edges": river_edges,
            "river_junctions": river_junctions,
            "river_mask": edge_masks(river_graph, river_edges),
            "lakes": lakes,
            "osm_license": osm_notice("OSM-derived river courses and junctions, river edges and masks, and Pulicat Lagoon"),
            **layered_fields,
        },
    )
    save_interim(
        "_boundary_decisions", {"islands": sorted(island_cells), "ut_parts": ut_cells, "named": named_places},
    )
    save_interim(
        "_world",
        {
            "grid": grid.to_dict(),
            "projection": proj.to_dict(),
            "owner": owner,
            "county": county,
            "county_samples": county_samples,
            "states": [st["fips"] for st in states_out],
            "state_names": [st["name"] for st in states_out],
            "counties": geoids,
            "water": water,
            "elev": elev,
            "cover": cover,
            "pct": pct,
        },
    )


def conformity(world, points):
    grid = HexGrid(**world["grid"])
    project = MapProjection(**world["projection"])
    mismatches = []
    for name, lon, lat, expected in points:
        cell = grid.cell_at(*project(lon, lat))
        if cell < 0:
            actual = "OUTSIDE"
        else:
            owner = world["owner"][cell]
            actual = world["states"][owner]["abbr"] if owner >= 0 else {-1: "WATER", -2: "FOREIGN"}[owner]
        if actual != expected:
            mismatches.append(f"{name} (cell {cell}): expected {expected}, got {actual}")
    return mismatches


def check(web_dir: Path):
    path = web_dir / "world.json"
    if not path.exists():
        return [("NOTE", "world.json missing")]
    world = json.loads(path.read_text())
    if not any(state.get("abbr") == "JK" for state in world["states"]):
        return [("NOTE", "Survey of India checks apply to the India grid")]
    if "projection" not in world:
        return [("FAIL", "India world.json is missing its projection")]
    fixture = json.loads(BOUNDARY_FIXTURE.read_text())
    points = fixture["points"]
    mismatches = conformity(world, points)
    results = [("FAIL", message) for message in mismatches]
    if not mismatches:
        results.append(("PASS", f"all {len(points)} Survey of India ownership points match"))
    try:
        chart = load_interim("soi_boundary_chart")
        decisions = load_interim("_boundary_decisions")
    except FileNotFoundError as exc:
        results.append(("FAIL", f"political-map boundary check needs local interims: {exc}"))
    else:
        localities = named_indian_cells(
            HexGrid(**world["grid"]), MapProjection(**world["projection"]), points,
            {state["abbr"]: i for i, state in enumerate(world["states"])},
        )
        rows, errors = check_chart(world, chart, decisions, localities)
        if rows:
            output = io.StringIO()
            writer = csv.DictWriter(output, rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            atomic_write_text(INTERIM / "_boundary_check.csv", output.getvalue())
        results.extend([("FAIL", error) for error in errors] or [
            ("PASS", f"charted majorities checked; {len(rows)} external-boundary hexes in data/interim/_boundary_check.csv"),
        ])
    counts = Counter(world["states"][owner]["abbr"] for owner in world["owner"] if owner >= 0)
    missing = sorted(set(STATE_ABBR.values()) - counts.keys())
    results.append(("FAIL", f"states/UTs without land: {', '.join(missing)}") if missing else
                   ("PASS", f"all {len(counts)} states and UTs have land"))
    missing_parts = []
    for ut, districts in UT_PARTS.items():
        assigned = {int(world["counties"][county]["geoid"].split("-")[-1])
                    for owner, county in zip(world["owner"], world["county"])
                    if owner >= 0 and world["states"][owner]["abbr"] == ut and county >= 0}
        for district in sorted(set(districts) - assigned):
            missing_parts.append(("FAIL", f"{ut} has no land in DataMeet district {district}"))
    results.extend(missing_parts or [("PASS", "all 7 detached parts of the multipart UTs have land")])
    results.extend(check_hydrography(world))
    if "base" in world:
        terrain_errors = layer_errors(world)
        results.extend([("FAIL", error) for error in terrain_errors] or [
            ("PASS", f"layered terrain for {len(world['base'])} cells, {len(world['featureFootprints'])} footprints "
                     f"and {len(world['featureSites'])} named sites"),
        ])
        if not terrain_errors:
            rows = measure(world, json.loads(TERRAIN_FIXTURE.read_text()))
            regressions = [(site["name"], unexpected_fields(site, missing)) for site, *_, missing in rows]
            results.extend([("FAIL", f"{name} terrain differs in {', '.join(fields)}")
                            for name, fields in regressions if fields] or [
                ("PASS", f"{sum(not row[-1] for row in rows)}/{len(rows)} terrain anchors match, with remaining differences documented"),
            ])
    return results
