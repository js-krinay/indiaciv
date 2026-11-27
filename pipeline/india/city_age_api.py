"""Read WorldPop's public v3 age estimates for the clipped city polygons."""

import json
from hashlib import sha256
from math import isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

import shapely
from shapely.geometry import mapping

from .city_sources import AGE_API_URL

AGE_BANDS = (0, 1, *range(5, 95, 5))


def counts_for(footprint, to_lonlat, cache, *, cached_only=False):
    lonlat = shapely.transform(footprint, to_lonlat, interleaved=False)
    body = json.dumps({"geojson": mapping(lonlat), "year": 2026}, separators=(",", ":")).encode()
    path = cache / (sha256(body).hexdigest() + ".json")
    if path.exists():
        raw = path.read_bytes()
    elif cached_only:
        return {}
    else:
        request = Request(AGE_API_URL, data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
    data = json.loads(raw)
    if (data.get("data_year") != 2026 or data.get("data_source") != "WorldPop Global2 R2025A, 100 m"
            or data.get("agesex_coverage") != 1):
        raise ValueError("Unexpected WorldPop release or incomplete age coverage")
    counts = {int(row["class"]): row["female"] + row["male"] for row in data["agesex_pyramid"]}
    if counts.keys() != set(AGE_BANDS) or not all(isfinite(mass) and mass >= 0 for mass in counts.values()):
        raise ValueError("WorldPop age response has missing or invalid population bands")
    if not path.exists():
        with NamedTemporaryFile(dir=cache, delete=False) as stream:
            stream.write(raw)
        Path(stream.name).replace(path)
    return counts
