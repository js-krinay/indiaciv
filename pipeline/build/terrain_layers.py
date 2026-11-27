"""Combine independently sampled climate, relief and geographic features."""

from collections import Counter
from math import isfinite

BASE = [
    ("neutral", "Unclassified land", "#9c997a", "Land with insufficient climate sampling.", "Small offshore islets"),
    ("grassland", "Grassland", "#a3ae66", "Moist climate. This base can carry trees or crops.", "Assam lowlands"),
    ("plains", "Plains", "#d0ad74", "Steppe or a seasonal dry climate.", "Solapur"),
    ("desert", "Desert", "#d6b781", "Most ice-free climate samples are hot or cold desert.", "Thar"),
    ("tundra", "Tundra", "#a8a695", "Polar climate on land with limited mapped snow and ice.", "High Ladakh"),
    ("snow", "Snow and ice", "#e6edf0", "Most sampled land is mapped as persistent snow or ice.", "Upper Siachen"),
    ("ocean", "Ocean", "#1b4266", "Open sea beyond the coastal shelf.", "Arabian Sea"),
    ("coast", "Coast", "#2d6d97", "Shallow sea or sea adjoining land.", "Gulf of Mannar"),
    ("lake", "Lake", "#3a80b0", "Inland water in the atlas water mask.", "Pangong Tso"),
]

FEATURES = [
    ("woods", "Woods", "#3f6944", "Tree cover reaches one fifth of sampled land.", "Kanha"),
    ("rainforest", "Rainforest proxy", "#2f6948", "At least 35% tree cover in a predominantly wet tropical climate. This proxy can include plantations.", "Agumbe"),
    ("marsh", "Marsh", "#6c9e83", "Mapped herbaceous or non-forested saturated wetland. Rice paddies are excluded.", "Harike Wetland"),
    ("floodplain", "Floodplain", "#729b8a", "Mapped alluvial landforms. The extent describes the landform.", "Kosi plain"),
    ("mangrove", "Mangrove", "#39776b", "Global Mangrove Watch extent with WorldCover mangrove corroboration or fallback.", "Sundarbans"),
    ("salt_flat", "Salt flat", "#e1d9c2", "Mapped salt pans and saline wetlands.", "Great Rann of Kutch"),
    ("ice_patch", "Ice patch", "#d7edf2", "At least 10% mapped snow and ice below the snow-base threshold.", "Nanda Devi"),
    ("cropland", "Cropland", "#b6aa54", "At least 20% WorldCover cropland.", "Punjab"),
    ("scrub", "Scrub", "#aa9464", "At least 20% WorldCover shrubland.", "Barmer"),
    ("urban", "Built-up", "#8a8378", "At least 30% WorldCover built-up area.", "Delhi"),
    ("reef", "Reef", "#63c1ad", "Mapped shallow reef extent.", "Agatti"),
    ("volcano", "Volcano", "#af6d55", "A vent in the Smithsonian volcano inventory.", "Barren Island"),
    ("beach", "Beach", "#efcf92", "A source-verified sandy shore.", "Marina Beach"),
    ("cliff", "Coastal cliff", "#987358", "A source-verified coastal cliff.", "Varkala"),
]


def table(entries, start=0):
    return [dict(id=i, key=key, name=name, color=color, rule=rule, example=example)
            for i, (key, name, color, rule, example) in enumerate(entries, start)]


BASE_TABLE = table(BASE)
FEATURE_TABLE = table(FEATURES, 1)
FEATURE_ID = {entry["key"]: entry["id"] for entry in FEATURE_TABLE}
DRY_CLIMATE = {3, *range(6, 14), *range(17, 25)}
FLAT_SPREAD, FLAT_SLOPE = 250, 5
MOUNTAIN_SPREAD, MOUNTAIN_SLOPE = 700, 11.5


def land_share(cover, code):
    land = sum(n for key, n in cover.items() if key != 80)
    return cover.get(code, 0) / land if land else 0


def base_for(water, climate, cover):
    if water:
        return water + 5
    if land_share(cover, 70) > 0.5:
        return 5
    total = sum(climate.values())
    if total < 8:
        return 0
    if climate.get(4, 0) + climate.get(5, 0) > total / 2:
        return 3
    groups = Counter()
    for code, count in climate.items():
        base = 4 if code in (29, 30) else 2 if code in DRY_CLIMATE or code in (4, 5) else 1
        groups[base] += count
    return max(sorted(groups), key=groups.get)


def relief_for(spread, slope):
    """Classify from p90–p10 spread (metres) and median local slope (degrees)."""
    if spread < FLAT_SPREAD and slope < FLAT_SLOPE:
        return 0
    return 2 if spread >= MOUNTAIN_SPREAD and slope >= MOUNTAIN_SLOPE else 1


def features_for(base, climate, cover, mapped):
    features = set()
    trees = land_share(cover, 10)
    if trees >= 0.20:
        wet = climate.get(1, 0) + climate.get(2, 0)
        features.add("rainforest" if trees >= 0.35 and wet > sum(climate.values()) / 2 else "woods")
    for key in ("marsh", "floodplain", "mangrove", "salt_flat"):
        if mapped.get(key, 0) >= 0.10:
            features.add(key)
    for key, code, threshold in (("marsh", 90, .10), ("mangrove", 95, .10),
                                 ("cropland", 40, .20), ("scrub", 20, .20), ("urban", 50, .30)):
        if land_share(cover, code) >= threshold:
            features.add(key)
    if base != 5 and land_share(cover, 70) >= 0.10:
        features.add("ice_patch")
    return sorted(FEATURE_ID[key] for key in features)


def layer_errors(world):
    """Check the published arrays and the three forms of located geometry."""
    water = world["water"]
    base, features = world.get("base"), world.get("features")
    if not all(isinstance(arr, list) and len(arr) == len(water) for arr in (base, features)):
        return ["terrain base and features must have one entry per cell"]
    tables = world["tables"]
    if tables.get("base") != BASE_TABLE or tables.get("features") != FEATURE_TABLE:
        return ["terrain tables do not match the published ids and definitions"]
    errors = []
    bad_base = sum(type(b) is not int or not (0 <= b <= 5 if wet == 0 else b == wet + 5)
                   for b, wet in zip(base, water))
    if bad_base:
        errors.append(f"{bad_base} base ids do not match their land/water class")
    ids = set(FEATURE_ID.values())
    bad_features = sum(not isinstance(row, list) or any(type(x) is not int or x not in ids for x in row)
                       or row != sorted(set(row)) or (wet != 0 and bool(row))
                       for row, wet in zip(features, water))
    if bad_features:
        errors.append(f"{bad_features} cells have invalid feature lists")

    def coords(values, minimum):
        return (isinstance(values, list) and len(values) >= minimum and len(values) % 2 == 0
                and all(type(v) in (int, float) and isfinite(v) for v in values))

    for field in ("featureFootprints", "featureSites"):
        records = world.get(field)
        if not isinstance(records, list):
            errors.append(f"{field} is missing or is not an array")
            continue
        for record in records:
            valid = (isinstance(record, dict) and type(record.get("id")) is int and record["id"] in ids)
            if valid and field == "featureFootprints":
                rings = record.get("rings")
                valid = isinstance(rings, list) and bool(rings) and all(coords(ring, 8) for ring in rings)
            elif valid:
                point = record.get("point")
                valid = (bool(record.get("name")) and
                         (coords(point, 2) and len(point) == 2 if point is not None
                          else coords(record.get("line"), 4)))
            if not valid:
                errors.append(f"{field} contains invalid geometry")
                break
    return errors
