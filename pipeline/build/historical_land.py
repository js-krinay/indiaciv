"""Area shares from classified equal-area samples."""

from collections import Counter, defaultdict

ESRI_SOURCE = "esri_land_cover"
WC_SOURCE = "worldcover_history"
ESRI_PERIOD = "Esri 2025 (1 Jan – 31 Dec 2025)"
WC_PERIOD = "WorldCover 2021 (1 Jan – 31 Dec 2021)"
ESRI_FIELDS = {"forest": (2, "Tree cover"), "crop": (5, "Cropland"), "developed": (7, "Built-up")}
WC_FIELDS = {"grass": "Grassland", "shrub": "Shrubland", "wetland": "Mapped wetlands"}
DENOMINATOR = "Share of classified land samples"
MIN_SAMPLES = 30
SPARSE_BELOW = 100
ESRI_CLASSES = {
    2: "Tree cover", 4: "Flooded vegetation", 5: "Cropland", 7: "Built-up",
    8: "Bare ground", 9: "Snow or ice", 11: "Rangeland",
}
WORLDCOVER_LAND = (10, 20, 30, 40, 50, 60, 70, 90, 95, 100)


def advisor_columns(records, *, district=False):
    columns = {}
    for key, label, lens in (
        ("forest", "Tree cover", "forest"), ("crop", "Cropland", "farmland"),
        ("developed", "Built-up", "developed"), ("grass", "Grassland", None),
        ("shrub", "Shrubland", None), ("wetland", "Mapped wetlands", None),
    ):
        record = (records or {}).get(key)
        if record is None or (district and lens is None):
            continue
        columns[f"land_{key}"] = {
            **record, "label": label, "group": "Land", "format": "pct",
            "unit": "share of classified land samples", "lens": lens,
            **({"coverage": f"Sparse · n = {record['samples']}"} if record.get("sparse") else {}),
        }
    return columns


def esri_tile(lon, lat):
    """Esri uses UTM zone and latitude band identifiers for its India tiles."""
    return f"{int((lon + 180) // 6) + 1}{'NPQRSTUVWX'[int(lat // 8)]}"


def esri_summary(counts):
    samples = sum(counts.get(code, 0) for code in ESRI_CLASSES)
    if not samples:
        return None
    dominant = max(ESRI_CLASSES, key=lambda code: counts.get(code, 0))
    return {
        "shares": {str(code): counts.get(code, 0) / samples for code in ESRI_CLASSES},
        "dominant": str(dominant),
        "other": sum(counts.get(code, 0) for code in (8, 9, 11)) / samples,
        "samples": samples,
    }


def worldcover_summary(counts):
    samples = sum(counts.get(code, 0) for code in WORLDCOVER_LAND)
    if not samples:
        return None
    return {
        "shares": {
            "grass": counts.get(30, 0) / samples,
            "shrub": counts.get(20, 0) / samples,
            "wetland": (counts.get(90, 0) + counts.get(95, 0)) / samples,
        },
        "samples": samples,
    }


def rollup(samples):
    states = defaultdict(lambda: (Counter(), Counter()))
    districts = defaultdict(lambda: (Counter(), Counter()))
    for state, district, esri, worldcover in samples:
        for regions, key in ((states, state), (districts, district)):
            if key is not None:
                regions[key][0].update(esri)
                regions[key][1].update(worldcover)

    def records(regions):
        out = {}
        for key, (esri, worldcover) in regions.items():
            metrics = {}
            if (cover := esri_summary(esri)) and cover["samples"] >= MIN_SAMPLES:
                meta = metadata(cover, ESRI_PERIOD, ESRI_SOURCE)
                metrics.update({field: {**meta, "value": cover["shares"][str(code)]}
                                for field, (code, _) in ESRI_FIELDS.items()})
                metrics["composition"] = {**cover, **meta}
            if (cover := worldcover_summary(worldcover)) and cover["samples"] >= MIN_SAMPLES:
                meta = metadata(cover, WC_PERIOD, WC_SOURCE)
                metrics.update({field: {**meta, "value": value}
                                for field, value in cover["shares"].items()})
            if metrics:
                out[key] = metrics
        return out

    return {"states": records(states), "districts": records(districts)}


def metadata(cover, period, source):
    samples = cover["samples"]
    return {"period": period, "vintage": "older", "source": source,
            "samples": samples, "sparse": samples < SPARSE_BELOW}
