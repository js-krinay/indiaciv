"""states.json: projected 2026 population, 2026 profile and land cover of each current state and union territory.

Population and profile come from the Technical Group projections, with WorldPop age estimates for six places.
district_states() tells the other builders which of today's states each census district lies in.
"""

from __future__ import annotations

from collections import Counter

from ..core.geo import MapProjection, Shape, ShapeIndex
from ..core.store import load_interim, write_web
from ..india.advisor_sources import VETERAN_POPULATION
from ..india.city_sources import LABOUR_SOURCE
from ..india.city_economy_sources import SECTOR_MIX
from ..india.explorer_sources import ALL_AGES_WPR
from ..sources.worldpop_age import SOURCE_ID as AGE_SOURCE
from .advisor_statistics import industry_shares, state_statistics, veteran_population
from .boundaries import ring_moments
from .cities import NO_ECONOMY
from .projection import state_population, state_profile, state_vitals
from .world import PCT
from .yields import rank_yields, regional_economy

REQUIRES = ["_world", "datameet", "tg_projections", AGE_SOURCE, "_state_metrics", "_yields",
            LABOUR_SOURCE, VETERAN_POPULATION]
PRODUCES = ["states.json"]

LATTICE = 5  # 5×5 points across a district's bounding box vote for its state


def district_states(districts: list[dict], states: list[dict]) -> list[int]:
    """Index into `states` of the state holding most of each district (lon/lat rings), or -1 if none does."""
    state_idx = ShapeIndex([Shape(st["rings"]) for st in states], cell_km=1.0)  # degrees, despite the name
    out = []
    for d in districts:
        shape = Shape(d["rings"])
        x0, y0, x1, y1 = shape.bbox
        pts = [(x0 + (x1 - x0) * (i + 0.5) / LATTICE, y0 + (y1 - y0) * (j + 0.5) / LATTICE)
               for i in range(LATTICE) for j in range(LATTICE)]
        # A thin district or one of small islands (Lakshadweep) may miss every lattice point: use its rings' centres.
        inside = [p for p in pts if shape.contains(*p)] or [
            (sum(x for x, _ in r[:-1]) / (len(r) - 1), sum(y for _, y in r[:-1]) / (len(r) - 1)) for r in d["rings"]]
        votes = [k for p in inside if (k := state_idx.locate(*p)) >= 0]
        out.append(Counter(votes).most_common(1)[0][0] if votes else -1)
    return out


def build() -> None:
    from ..india.city_economy_sources import state_sector_mix
    from .state_metrics import FY

    world = load_interim("_world")
    dm = load_interim("datameet")
    tg = load_interim("tg_projections")
    age_profiles = load_interim(AGE_SOURCE)["profiles"]
    states = sorted(dm["states"], key=lambda st: st["name"])
    if [st["name"] for st in states] != world["state_names"]:
        raise ValueError("DataMeet states are not in world.json order; rebuild world")
    project = MapProjection(**world["projection"])
    area = [mapped_area(st["rings"], project) for st in states]

    owner, cover, pct = world["owner"], world["cover"], world["pct"]
    metrics = load_interim("_state_metrics")["geographies"]
    yields = load_interim("_yields")["rows"]
    industries = industry_shares()
    residents = veteran_population("states")
    out = []
    for k, (abbr, name) in enumerate(zip(world["states"], world["state_names"])):
        cells = [i for i, o in enumerate(owner) if o == k and cover[i] > 0]
        land = {key: round(sum(pct[key][i] for i in cells) / len(cells) / 100, 4) for key in PCT} if cells else None
        age = age_profiles.get(name)
        out.append({
            "fips": abbr, "abbr": abbr, "name": name,
            "population": (pop := state_population(tg, name)), **NO_ECONOMY,
            # 2026 demographics and annual growth ending in March 2026.
            "area_km2": round(area[k]),
            "provenance": {"population": {"period": "Projected for 1 March 2026", "source": "tg_projections"}},
            "profile": {**(state_profile(tg, name) or {}), **(age or {}),
                        **state_vitals(tg, name), "density": pop / area[k]},
            **({"age_source": AGE_SOURCE} if age else {}),
            "ranks": {},
            **regional_economy(yields[abbr]),
            "label": None,  # the frontend places the names
            "land": land,
            "energy": None,
            "metrics": metrics[abbr],
            "sector_mix": state_sector_mix(abbr, name, FY),
            "advisor_statistics": state_statistics(abbr, industries, residents.get(abbr)),
            "employed": round(pop * ALL_AGES_WPR[abbr] / 100) if abbr in ALL_AGES_WPR else None,
            "internet_per_100": metrics[abbr].get("internet_per_100", {}).get("value"),
            "sector_mix": SECTOR_MIX.get(abbr),
        })
    rank_yields(out)
    write_web("states.json", out)


def mapped_area(rings, project):
    """Area in km² of DataMeet rings, including signed holes, in the equal-area projection."""
    return abs(sum(ring_moments([project(*point) for point in ring])[0] for ring in rings)) / 2
