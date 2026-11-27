"""Map the 2026 air and monsoon measures onto their respective hexes."""

from math import fsum
from statistics import mean

from ..core.geo import Shape, ShapeIndex
from ..core.store import load_interim
from .district_values import district_sample_values, small_district_values

GROUP = {"id": "air_weather", "name": "Air & weather"}
INPUTS = ["cpcb_city_aqi", "cpcb_station_pm25", "imd_monsoon"]
PM_RADIUS_KM = 150
MONSOON_BANDS = ("Large deficit", "Deficit", "Near normal", "Excess", "Large excess")
AQI_ALIASES = {
    "Ahilyanagar": "Ahmednagar",
    "Belagavi": "Belgaum",
    "Chhatrapati Sambhajinagar": "Aurangabad (Maharashtra)",
    "Durg-Bhilai": "Bhilai",
    "Hubballi-Dharwad": "Hubballi",
    "Mangaluru": "Mangalore",
    "Nanded Waghala": "Nanded",
}
# Cross-border urban agglomerations can land on the adjoining state hex.
AQI_STATE_OVERRIDES = {"Chandigarh": "Chandigarh", "Puducherry": "Puducherry",
                       "Thiruvananthapuram": "Kerala"}


def inverse_distance(x, y, stations):
    nearby = []
    coincident = []
    for sx, sy, value in stations:
        square = (sx - x) ** 2 + (sy - y) ** 2
        if square == 0:
            coincident.append(value)
        elif square <= PM_RADIUS_KM ** 2:
            nearby.append((value, 1 / square))
    if coincident:
        return mean(coincident)
    if nearby:
        return fsum(value * weight for value, weight in nearby) / fsum(weight for _, weight in nearby)
    return None


def aqi_by_city(cities, state_names, observations):
    values = {}
    lookup = {(row["city"].casefold(), row["state"].casefold()): row for row in observations}
    for city in cities:
        original = city["name"]
        name = AQI_ALIASES.get(original, original).casefold()
        state = AQI_STATE_OVERRIDES.get(original, state_names[city["states"][0]]).casefold()
        row = lookup.get((name, state))
        if row is not None:
            values[city["id"]] = round(row["poor"] / row["days"], 5)
    return values


def district_pm25(districts, projection, stations):
    results = []
    for district in districts:
        # Area centroid of the main contiguous polygon in the equal-area projection.
        rings = [[projection(*p) for p in ring] for ring in district["rings"]]
        rings = [ring for ring in rings if len(ring) >= 3]
        moments = []
        for ring in rings:
            edges = list(zip(ring, ring[1:] + ring[:1]))
            cross = [x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in edges]
            area = fsum(cross)
            if area:
                x = fsum((a[0] + b[0]) * c for (a, b), c in zip(edges, cross)) / (3 * area)
                y = fsum((a[1] + b[1]) * c for (a, b), c in zip(edges, cross)) / (3 * area)
                moments.append((abs(area), x, y))
        if moments:
            _, x, y = max(moments)
            results.append(inverse_distance(x, y, stations))
        else:
            results.append(None)
    return results


def monsoon_band(departure):
    if departure < -59:
        return -2
    if departure <= -20:
        return -1
    if departure < 20:
        return 0
    return 1 if departure < 60 else 2


def monsoon_lookup(subdivisions, projection):
    entries = list(subdivisions.values())
    shapes = ShapeIndex([Shape([[projection(*p) for p in ring] for ring in sub["rings"]]) for sub in entries])

    def at(x, y):
        k = shapes.locate(x, y)
        return monsoon_band(entries[k]["departure"]) if k >= 0 else None

    return at


def weather_lenses(world, grid, projection, districts, cities, areas, centers=()):
    inputs = {}
    for source in INPUTS:
        try:
            inputs[source] = load_interim(source)
        except FileNotFoundError:
            pass
    out = []
    if (data := inputs.get("cpcb_city_aqi")) is not None:
        by_city = aqi_by_city(cities, dict(zip(world["states"], world["state_names"])), data["cities"])
        values = [None] * grid.size
        for city in reversed(cities):
            if city["id"] in by_city:
                for cell in city["footprint"]:
                    values[cell] = by_city[city["id"]]
        out.append({
            "id": "city_bad_air", "name": "Bad-air days, Jan–Oct 2026",
            "icon": "l-developed", "unit": "% of reported days", "format": "pct", "domain": [0, 1],
            "ramp": ["#f8e7b1", "#df9c71", "#b65f58", "#813a58", "#45173f"], "higher_is": "bad",
            "source": "cpcb_city_aqi", "period": "Jan–Oct 2026", "source_line": "CPCB via EnviroCatalysts · Jan–Oct 2026",
            "share_credit": "CPCB National AQI bulletin · EnviroCatalysts, India Air Quality Portal",
            "description": "Share of reported days in the three highest pollution categories.",
            "note": "Poor or worse (AQI ≥201). City hexes with at least 244 of 304 reported days.",
            "values": values, "city_values": by_city,
        })
    if (data := inputs.get("cpcb_station_pm25")) is not None:
        stations = [(*projection(row["lon"], row["lat"]), row["mean"]) for row in data["stations"].values()]
        estimates = district_pm25(districts, projection, stations)
        owner, samples = world["owner"], world["county_samples"]
        extra = small_district_values(owner, samples, grid, projection, districts, areas, estimates)
        values = [None if value is None else round(value, 1)
                  for value in district_sample_values(owner, samples, estimates, extra)]
        out.append({
            "id": "district_pm25", "name": "District PM₂.₅, Jan–Oct 2026",
            "icon": "l-developed", "unit": "µg/m³", "format": "float", "domain": [0, 100],
            "ramp": ["#fff0b7", "#edba78", "#d78165", "#984b64", "#55234c"], "higher_is": "bad",
            "source": "cpcb_station_pm25", "period": "Jan–Oct 2026", "source_line": "IndiaCiv estimate, Jan–Oct 2026", "estimated": True,
            "sources": ["cpcb_station_pm25", "datameet"],
            "share_credit": "CPCB CAAQMS · EnviroCatalysts · XKDR Forum (station locations)",
            "description": "IndiaCiv estimate of mean surface PM₂.₅, January–October 2026. Hexes blend district "
                           "estimates at seven sample points and weight missed small districts by area.",
            "note": "District centroids use inverse-distance-squared weighting of monitors within 150 km. "
                    "Monitors need 244 valid days with at least 18 hourly readings per day.",
            "values": values,
            "district_values": [None if value is None else round(value, 1) for value in estimates],
        })
    if (data := inputs.get("imd_monsoon")) is not None:
        monsoon_at = monsoon_lookup(data["subdivisions"], projection)
        ramp = ["#8c4725", "#d5914f", "#f4efd4", "#6db8ba", "#226586"]
        out.append({
            "id": "monsoon_2026", "name": "Monsoon rainfall, Jun–Sep 2026",
            "icon": "r-hydro", "unit": "rainfall band", "format": "category", "domain": [0, 4],
            "categories": [{"id": name.lower().replace(" ", "_"), "name": name, "color": color}
                           for name, color in zip(MONSOON_BANDS, ramp)],
            "ramp": ramp, "higher_is": "neutral",
            "source": "imd_monsoon", "period": "Jun–Sep 2026", "source_line": "India Meteorological Department · Jun–Sep 2026",
            "share_credit": "India Meteorological Department · India by Numbers transcription",
            "description": "IndiaCiv groups observed southwest monsoon rainfall into five bands relative to IMD’s long-period average.",
            "note": "Uses the subdivision at each hex centre or district reference point.",
            "values": [band + 2 if band is not None else None for band in
                       (monsoon_at(*grid.center(*grid.col_row(i))) if state >= 0 else None
                        for i, state in enumerate(world["owner"]))],
            "district_values": [monsoon_at(*center) for center in centers],
        })
    return [{**lens, "emoji": "", "group": GROUP["id"], "scale": "linear"} for lens in out]
