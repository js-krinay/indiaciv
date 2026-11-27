"""Optional, grid-specific repairs from the City View spatial preparation."""

from ..core.store import load_interim
from ..india import CITY_POPULATION_GRID
from ..india.city_sources import AGE_SOURCE, HEX_GEOGRAPHY

DENSITY_META = {"source": CITY_POPULATION_GRID, "period": "mid-2026",
                "vintage": "2026 estimate", "estimated": True}
AGE_META = {**DENSITY_META, "source": AGE_SOURCE}


def prepared_geography(world):
    from .city_view import grid_fingerprint

    try:
        data = load_interim(HEX_GEOGRAPHY)
    except FileNotFoundError:
        return {}
    if data["grid_fingerprint"] != grid_fingerprint(world):
        raise ValueError("Stale hex geography. Re-run pipeline.india.city_view (see README).")
    return data


def fill_blanks(values, candidates, metadata):
    details = {}
    for key, record in candidates.items():
        cell = int(key)
        if values[cell] is None:
            values[cell] = record["value"]
            details[key] = {**metadata, **{k: v for k, v in record.items() if k != "value"}}
    return details
