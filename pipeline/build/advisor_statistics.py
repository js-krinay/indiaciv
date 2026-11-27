"""Shared state and national statistics for IndiaCiv advisors."""

from ..core.geo import Shape
from ..core.store import load_interim
from ..india.advisor_sources import (BOARDS, CIVIC_OFFICES, FY, REGISTRATIONS, VETERAN_METHOD,
                                    VETERAN_PERIOD, VETERAN_POPULATION, VETERAN_SOURCES)
from ..india.city_sources import LABOUR_SOURCE
from ..india.civic_sources import PMJAY, POVERTY


def veteran_estimate(earlier, latest):
    if earlier is None or latest is None:
        return None
    estimate = 2 * latest - earlier
    return estimate if estimate >= 0 else None


def industry_shares():
    try:
        return load_interim(LABOUR_SOURCE).get("broad_industry", {})
    except FileNotFoundError:
        return {}

def veteran_population(level):
    try:
        return load_interim(VETERAN_POPULATION)[level]
    except FileNotFoundError:
        return {}


def state_statistics(code, industries, residents):
    veterans = veteran_estimate(*REGISTRATIONS.get(code, (None, None)))
    return {
        "industry": industries.get(code),
        "cantonment_boards": len(BOARDS.get(code, ())),
        "registered_veterans": veterans,
        "veteran_share": veterans / residents if veterans is not None and residents else None,
    }


def civic_office_points(project):
    points = []
    for name, lon, lat in CIVIC_OFFICES:
        x, y = project(lon, lat)
        points.append({"name": name, "x": round(x, 3), "y": round(y, 3)})
    return points


def civic_offices_in_footprint(offices, rings):
    if not rings:
        return None
    footprint = Shape(rings)
    return [office["name"] for office in offices if footprint.contains(office["x"], office["y"])] or None


def national_statistics(industries, population, gdp_inr):
    budget_crore = 681210.27
    budget_inr = round(budget_crore * 10_000_000)
    return {
        "industry": industries.get("IN"),
        "poverty_nowcast": {
            "value": 0.01395, "line": "$3.00 per person per day (PPP)", "period": "2026",
            "vintage": "September 2026", "source": POVERTY, "estimated": True,
        },
        "pmjay_cards": {
            "value": 100 * 455_000_000 / population, "period": "12 August 2026",
            "denominator_period": "1 March 2026", "source": [PMJAY, "tg_projections"],
            "estimated": True, "lower_bound": True,
        },
        "defence_budget": {
            "period": FY, "source": "defence_budget_fy26", "estimated": False,
            "total": budget_crore,
            "heads": {"Capital": 180000, "Revenue": 311732.30, "Pensions": 160795,
                      "Civil organisations": 28682.97},
        },
        "defence_budget_per_resident": {
            "value": budget_inr / population,
            "period": FY, "denominator_period": "1 Mar 2026", "estimated": True,
            "source": ["defence_budget_fy26", "tg_projections"],
        },
        "defence_budget_share_gdp": {
            "value": budget_inr / gdp_inr,
            "period": FY, "estimated": True, "source": ["defence_budget_fy26", "gdp_fy26"],
        } if gdp_inr else None,
        "veteran_penury_grant": {
            "value": 8000, "period": "2026", "estimated": False, "source": "veterans_welfare_rates",
        },
        "sainik_schools": {"value": 79, "period": "7 May 2026", "source": "sainik_schools_2026", "estimated": False},
        "cantonment_boards": sum(map(len, BOARDS.values())),
        "veterans": {
            "value": sum(veteran_estimate(*pair) for pair in REGISTRATIONS.values()),
            "coverage": len(REGISTRATIONS), "period": VETERAN_PERIOD, "source": VETERAN_SOURCES,
            "estimated": True, "description": VETERAN_METHOD,
        },
    }
