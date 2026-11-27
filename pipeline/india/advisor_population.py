"""Prepare WorldPop denominators for state and district veteran rates."""

import argparse
from pathlib import Path

import rasterio

from ..core.geo import MapProjection
from ..core.store import load_interim, save_interim
from ..build.world import STATE_ABBR
from . import CITY_POPULATION_CHECKSUM
from .advisor_sources import HP_REGISTRATIONS, OLDER_REGISTRATIONS, REGISTRATIONS, VETERAN_POPULATION
from .city_view import mass_reader, ring_geometry, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worldpop", type=Path)
    args = parser.parse_args()
    verify(args.worldpop, CITY_POPULATION_CHECKSUM)
    project = MapProjection(**load_interim("_world")["projection"])
    districts, states = {}, {}
    selected_states = REGISTRATIONS.keys() | OLDER_REGISTRATIONS.keys()
    boundaries = load_interim("datameet")
    with rasterio.open(args.worldpop) as raster:
        mass = mass_reader(raster, project)
        for district in boundaries["districts"]:
            district_id = f"{district['state_code']:02d}-{district['code']:03d}"
            if district_id in HP_REGISTRATIONS:
                districts[district_id] = round(mass(ring_geometry(district["rings"], project)))
        for state in boundaries["states"]:
            code = STATE_ABBR[state["name"]]
            if code in selected_states:
                states[code] = round(mass(ring_geometry(state["rings"], project)))
    if (districts.keys() != HP_REGISTRATIONS.keys() or states.keys() != selected_states
            or any(value <= 0 for value in [*districts.values(), *states.values()])):
        raise ValueError("WorldPop denominators must cover each selected district and State/UT")
    save_interim(VETERAN_POPULATION, {"districts": districts, "states": states}, vintage="Mid-2026")


if __name__ == "__main__":
    main()
