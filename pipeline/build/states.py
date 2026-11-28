"""states.json: projected 2026 population, 2026 profile and land cover of each current state and union territory.

Population and profile come from the Technical Group projections, with WorldPop age estimates for six places.
district_states() tells the other builders which of today's states each census district lies in.
"""

from __future__ import annotations

import json
from collections import Counter

from ..core.geo import MapProjection, Shape, ShapeIndex
from ..core.paths import WEB_DATA
from ..core.store import load_interim, write_web
from ..india.advisor_sources import VETERAN_POPULATION
from ..india.annual_labour import SOURCE as ANNUAL_LABOUR_SOURCE, annual_rates, fallback_records
from ..india.census_civic_sources import INTERIM as CENSUS_CIVIC
from ..india.city_sources import HEX_GEOGRAPHY, LABOUR_SOURCE
from ..india.explorer_sources import ALL_AGES_WPR
from ..sources.worldpop_age import SOURCE_ID as AGE_SOURCE
from .advisor_statistics import industry_shares, state_explorer_columns, state_statistics, veteran_population
from .city_people import quarterly_resident_industries, resident_industries
from .boundaries import ring_moments
from .cities import NO_ECONOMY
from .historical_land import ESRI_CLASSES, advisor_columns as land_columns
from .household_analogues import state_columns as household_columns
from .hex_geography import AGE_META, prepared_geography
from .projection import state_population, state_profile, state_vitals
from .world import PCT
from .yields import rank_yields, regional_economy

REQUIRES = ["_world", "datameet", "tg_projections", AGE_SOURCE, "_state_metrics", "_yields",
            LABOUR_SOURCE, VETERAN_POPULATION, "resources.json", "infrastructure.json", "nation.json"]
PRODUCES = ["states.json"]
OPTIONAL_REQUIRES = [ANNUAL_LABOUR_SOURCE, HEX_GEOGRAPHY, CENSUS_CIVIC]

LATTICE = 5  # 5×5 points across a district's bounding box vote for its state


def advisor_columns(land, direction):
    """Data-driven state columns without an upstream statistic of the same scope."""
    columns = {}
    if cover := (land or {}).get("composition"):
        provenance = {key: cover[key] for key in ("period", "vintage", "source", "sparse", "samples")}
        if cover["sparse"]:
            provenance["coverage"] = f"Sparse · n = {cover['samples']}"
        fraction = {"format": "pct", "unit": "share of classified land samples",
                    "group": "Land", **provenance}
        columns["land_other"] = {**fraction, "label": "Other mapped cover", "value": cover["other"]}
        columns["land_dominant"] = {"label": "Largest mapped cover", "format": "text", "unit": "cover type",
                                    "group": "Land", "value": ESRI_CLASSES[int(cover["dominant"])], **provenance}
        for code in (4, 8, 9, 11):
            columns[f"land_cover_{code}"] = {
                **fraction, "label": ESRI_CLASSES[code], "value": cover["shares"][str(code)],
            }
    if direction:
        for key in ("unloaded", "loaded"):
            columns[f"port_{key}"] = {
                "label": f"Overseas cargo {key}", "group": "Commerce", "format": "pct",
                "unit": "share of overseas cargo", "value": direction[key], "period": direction["period"],
                "vintage": direction["vintage"], "source": direction["source_id"],
            }
    return columns


def power_summary(summary):
    power = {key: item for key, item in summary.items()
             if item["unit"] == "MW" and item["value"] is not None}
    if not power:
        return None
    by_type = {key: item["value"] for key, item in power.items()}
    return {"unit": "MW", "total": sum(by_type.values()), "by_type": by_type,
            "sites": {key: item["count"] for key, item in power.items()},
            "note": "September 2026 mapped capacity", "period": "September 2026", "source": "gem_power"}


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


def state_labour(code, population, metrics, rates):
    employed = round(population * ALL_AGES_WPR[code] / 100) if code in ALL_AGES_WPR else None
    if not rates:
        return employed, {}
    records = fallback_records(population, "tg_projections", "1 March 2026", "combined", rates)
    metrics.setdefault("unemployment", records["unemployment"])
    return (employed, {}) if employed is not None else (records["employed"]["value"], records)


def unemployment_slot(record):
    from .state_metrics import QUARTER

    return {"period": QUARTER, **record} if record and record.get("value") is not None else {}


def build() -> None:
    from .census_civic import advisor_columns as civic_columns, civic_rows
    from .city_economy import city_sector_output
    from .city_view_contract import SECTOR_LABELS, economy_column, explorer_gsva_columns, gdp_industry_fields, metadata
    from ..india.city_economy_sources import state_sector_mix
    from .state_metrics import FY, advisor_columns as metric_columns

    world = load_interim("_world")
    dm = load_interim("datameet")
    tg = load_interim("tg_projections")
    age_profiles = load_interim(AGE_SOURCE)["profiles"]
    geography = prepared_geography(world)
    median_fills = geography.get("state_age", {})
    states = sorted(dm["states"], key=lambda st: st["name"])
    if [st["name"] for st in states] != world["state_names"]:
        raise ValueError("DataMeet states are not in world.json order; rebuild world")
    project = MapProjection(**world["projection"])
    area = [mapped_area(st["rings"], project) for st in states]

    owner, cover, pct = world["owner"], world["cover"], world["pct"]
    state_metrics = load_interim("_state_metrics")
    metrics = state_metrics["geographies"]
    yields = load_interim("_yields")["rows"]
    industries = industry_shares()
    annual = annual_rates()
    residents = veteran_population("states")
    civic = civic_rows("states")
    resources = json.loads((WEB_DATA / "resources.json").read_text())["summary"]["states"]
    transport = json.loads((WEB_DATA / "infrastructure.json").read_text()) or {}
    directions = transport.get("overseas_direction_by_state", {})
    workforce_benchmark = json.loads((WEB_DATA / "nation.json").read_text()).get("state_workforce_benchmark")
    out = []
    for k, (abbr, name) in enumerate(zip(world["states"], world["state_names"])):
        cells = [i for i, o in enumerate(owner) if o == k and cover[i] > 0]
        land = {key: round(sum(pct[key][i] for i in cells) / len(cells) / 100, 4) for key in PCT} if cells else None
        age = age_profiles.get(name)
        profile = {**(state_profile(tg, name) or {}), **(age or {})}
        age_fill = None
        if profile.get("median_age") is None:
            if model := median_fills.get(abbr):
                age_fill = {**AGE_META, **model}
            else:
                age_fill = civic.get(abbr, {}).get("median_age")
        if age_fill:
            profile["median_age"] = age_fill["value"]
            age_meta = {key: value for key, value in age_fill.items() if key != "value"}
        vitals = state_vitals(tg, name)
        statistics = state_statistics(abbr, industries, residents.get(abbr))
        historical_land = world.get("historical_land", {}).get("states", {}).get(abbr)
        sector_mix = state_sector_mix(abbr, name, FY)
        pop = state_population(tg, name)
        employed, annual_work = state_labour(abbr, pop, metrics[abbr], annual.get(abbr, {}).get("combined"))
        unemployment = unemployment_slot(metrics[abbr].get("unemployment"))
        jobs, jobs_meta = quarterly_resident_industries(pop, profile, metrics[abbr], statistics["industry"])
        if jobs is None and (benchmark := annual_work.get("industry")):
            jobs, jobs_meta = resident_industries(employed, benchmark["value"], {
                "period": "1 March 2026", "input_weights": metadata(benchmark),
                "source": [benchmark["source"], "tg_projections"], "scope": "Residents, all ages",
            })
        gdp = yields[abbr]["values"]["gold"]
        sector_output = city_sector_output({abbr: gdp}, {abbr: sector_mix}) if gdp is not None else None
        industry_output = gdp_industry_fields(sector_output) if sector_output else {}
        state_gdp_columns = {
            f"gdp_{key}": economy_column(
                f"State GDP · {SECTOR_LABELS.get(key, key)}", "inr", "INR", value,
                {**sector_output, "description": "Nominal state GDP allocated using the state's nominal GSVA shares."},
            ) for key, value in industry_output.get("gdp_by_industry", {}).items()
        }
        out.append({
            **({"census_civic": civic[abbr]} if abbr in civic else {}),
            "fips": abbr, "abbr": abbr, "name": name,
            "population": pop, **NO_ECONOMY,
            # 2026 demographics and annual growth ending in March 2026.
            "area_km2": round(area[k]),
            "provenance": {
                "population": {"period": "Projected for 1 March 2026", "source": "tg_projections"},
                **({"median_age": age_meta} if age_fill else {}),
                **({"employed": annual_work["employed"]} if annual_work else {}),
                **({"unemployment": metadata(unemployment)} if unemployment else {}),
                **({"jobs": jobs_meta} if jobs else {}),
                **({"gdp_by_industry": metadata(sector_output)} if sector_output else {}),
                **({"growth": {"period": vitals["growth_period"], "source": "tg_projections", "estimated": True}}
                   if "growth" in vitals else {}),
            },
            "profile": {**profile, **vitals, "density": pop / area[k]},
            "growth": vitals.get("growth"),
            "growth_period": vitals.get("growth_period"),
            "growth_years": [2025, 2026] if vitals.get("growth") is not None else None,
            **({"age_source": age_meta["source"]} if age_fill and age_meta.get("estimated") else
               {"age_source": AGE_SOURCE} if age else {}),
            "ranks": {},
            **regional_economy(yields[abbr]),
            "gdp": gdp,
            **industry_output,
            "label": None,  # the frontend places the names
            "land": land,
            "historical_land": historical_land,
            "advisor_columns": {**advisor_columns(historical_land, directions.get(name)),
                                **land_columns(historical_land),
                                **civic_columns(civic.get(abbr, {})),
                                **state_explorer_columns(statistics, annual_work.get("industry")),
                                **explorer_gsva_columns(sector_mix),
                                **state_gdp_columns,
                                **metric_columns(metrics[abbr], state_metrics["definitions"]),
                                **household_columns(metrics[abbr], state_metrics["definitions"], historical_land)},
            "energy": power_summary(resources.get(abbr, {})),
            "metrics": metrics[abbr],
            "sector_mix": sector_mix,
            "advisor_statistics": statistics,
            "employed": employed,
            "unemployment": unemployment.get("value"),
            "jobs": jobs,
            "industry_comparison": {
                "jobs": workforce_benchmark["jobs"], "employed": workforce_benchmark["employed"],
                "provenance": workforce_benchmark["provenance"],
            } if workforce_benchmark and jobs and jobs_meta.get("period") == workforce_benchmark["provenance"]["period"]
                and jobs_meta.get("scope") == workforce_benchmark["provenance"].get("scope") else None,
            "internet_per_100": metrics[abbr].get("internet_per_100", {}).get("value"),
        })
    rank_yields(out)
    write_web("states.json", out)


def mapped_area(rings, project):
    """Area in km² of DataMeet rings, including signed holes, in the equal-area projection."""
    return abs(sum(ring_moments([project(*point) for point in ring])[0] for ring in rings)) / 2
