"""Shared state and national statistics for IndiaCiv advisors."""

from ..core.geo import Shape
from ..core.store import load_interim
from ..india.advisor_sources import (BOARD_CENSUS, BOARD_CENSUS_SOURCE, BOARD_CLASS_PERIOD,
                                    BOARDS, BOARDS_PERIOD, CIVIC_OFFICES, FY, PARTNERSHIP_PLACES,
                                    PARTNERSHIP_SOURCE, PARTNERSHIP_SUPPLEMENT, PARTNERSHIP_SUPPLEMENT_SOURCE,
                                    PENURY_GRANT_INR, PENURY_GRANT_PERIOD,
                                    PSU_FINANCIALS, REGISTRATIONS, RMS_BY_STATE, RMS_PERIOD,
                                    RMS_SOURCE, RMS_TOWNS, SAINIK_ROSTER, SAINIK_ROSTER_SOURCE, VETERAN_METHOD,
                                    VETERAN_PERIOD, VETERAN_POPULATION, VETERAN_SOURCES)
from ..india.city_sources import LABOUR_SOURCE
from ..india.civic_sources import PMJAY, POVERTY


def veteran_columns(count, share, *, district=False):
    period = "31 Mar 2026" if district else VETERAN_PERIOD
    source = "hp_veterans_2026" if district else VETERAN_SOURCES
    common = {"group": "Defence & veterans"}
    columns = {}
    if count is not None:
        columns["registered_veterans"] = {
            **common, "label": "Registered ex-servicemen", "format": "int", "unit": "people",
            "value": count, "period": period, "source": source, "estimated": not district,
            "lens": "registered_veterans",
            "description": "Reported district registrations in Himachal Pradesh." if district else VETERAN_METHOD,
        }
    if share is not None:
        columns["veteran_share"] = {
            **common, "label": "Registered ex-servicemen per 100 residents", "format": "pct",
            "unit": "share of residents", "value": share, "estimated": True,
            "period": f"{period} registrations · mid-2026 residents",
            "source": [*([source] if district else source), "city_population_grid", "datameet"],
            "description": "Registrations divided by the mid-2026 WorldPop population.",
        }
    return columns


def state_explorer_columns(statistics, annual_industry=None):
    columns = veteran_columns(statistics["registered_veterans"], statistics["veteran_share"])
    columns["cantonment_boards"] = {
        "label": "Listed cantonment boards", "format": "int", "unit": "civic boards",
        "group": "Defence & veterans", "value": statistics["cantonment_boards"],
        "period": "27 Nov 2026", "source": "cantonment_boards",
    }
    if names := statistics.get("cantonment_board_names"):
        columns["cantonment_board_names"] = {
            "label": "Cantonment Board names", "format": "text", "group": "Defence & veterans",
            "value": ", ".join(names), "period": BOARDS_PERIOD, "source": "cantonment_boards",
        }
        historical = {"format": "text", "group": "Defence & veterans",
                      "source": BOARD_CENSUS_SOURCE, "vintage": "older"}
        columns["cantonment_board_classes"] = {
            **historical, "label": "Cantonment Board classes", "period": BOARD_CLASS_PERIOD,
            "value": ", ".join(f"{name} ({BOARD_CENSUS[name][1]})" for name in names),
        }
        columns["cantonment_board_population"] = {
            **historical, "label": "Cantonment Board population (all residents)", "period": "Census 2011",
            "value": ", ".join(f"{name} ({BOARD_CENSUS[name][0]})" for name in names),
        }
    columns["rashtriya_military_schools"] = {
        "label": "Rashtriya Military Schools", "format": "int", "unit": "schools",
        "group": "Defence & veterans", "value": statistics.get("rashtriya_military_schools", 0),
        "period": RMS_PERIOD, "source": RMS_SOURCE,
    }
    if towns := statistics.get("rashtriya_military_school_towns"):
        columns["rashtriya_military_school_towns"] = {
            "label": "Rashtriya Military School towns", "format": "text", "group": "Defence & veterans",
            "value": ", ".join(towns), "period": RMS_PERIOD, "source": RMS_SOURCE,
        }
    if schools := statistics.get("traditional_sainik_school_roster"):
        columns["traditional_sainik_school_roster"] = {
            "label": "Traditional Sainik School places", "format": "text", "group": "Defence & veterans",
            "value": ", ".join(schools), "period": "2026", "source": SAINIK_ROSTER_SOURCE,
            "description": "Place labels from the traditional school names in the AISSEE 2026 roster.",
        }
    places = statistics.get("partnership_sainik_school_places", ())
    supplement = statistics.get("partnership_sainik_school_supplement", ())
    if places or supplement:
        sources = [source for values, source in ((places, PARTNERSHIP_SOURCE),
                                                (supplement, PARTNERSHIP_SUPPLEMENT_SOURCE)) if values]
        columns["partnership_sainik_school_places"] = {
            "label": "Partnership Sainik School places", "format": "text", "group": "Defence & veterans",
            "value": ", ".join((*places, *supplement)), "period": "2026", "source": sources,
            "description": "Places in the AISSEE 2026 admissions roster and its October supplement.",
        }
    for key, company, _, city, measure, value, edition, _ in statistics.get("defence_psu_financials", ()):
        columns[key] = {
            "label": f"{company} {measure}", "format": "inr", "unit": "INR",
            "group": "Defence & veterans", "value": value, "period": FY, "source": key,
            "description": f"Headquarters city: {city}. Company disclosure: {edition}.",
            "hide_rank": True,
        }
    for (key, label), value in zip((
        ("agriculture", "Agriculture sector"),
        ("secondary", "Secondary sector, mining and quarrying"),
        ("tertiary", "Tertiary sector"),
    ), statistics["industry"] or []):
        columns[f"industry_{key}_share"] = {
            "label": label, "format": "pct", "unit": "share of workers age 15+", "group": "Work",
            "value": value / 100, "period": "1 Jul – 30 Sep 2026", "source": LABOUR_SOURCE,
            "description": "PLFS Current Weekly Status, rural and urban persons combined, selected states.",
        }
    if not statistics["industry"] and annual_industry:
        for key, value in zip(("Agriculture", "Secondary", "Tertiary"), annual_industry["value"]):
            columns[f"annual_industry_{key.lower()}_share"] = {
                **annual_industry, "label": f"{key} sector (annual CWS workers)", "format": "pct",
                "unit": "share of surveyed workers", "group": "Work", "value": value / 100, "hide_rank": True,
                "scope": "Rural and urban combined, published annual survey universe",
            }
    return columns


def civic_office_columns(offices):
    if not offices:
        return {}
    common = {"group": "Defence & veterans", "unit": "public civic offices",
              "period": "27 Nov 2026", "source": ["cantonment_boards", "civic_office_points"]}
    return {
        "civic_offices": {**common, "label": "Verified cantonment board offices", "format": "text",
                          "value": ", ".join(offices)},
        "civic_office_count": {**common, "label": "Mapped cantonment board offices", "format": "int",
                              "value": len(offices)},
    }


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
        "cantonment_board_names": BOARDS.get(code, ()),
        "rashtriya_military_schools": RMS_BY_STATE.get(code, 0),
        "rashtriya_military_school_towns": RMS_TOWNS.get(code, ()),
        "traditional_sainik_school_roster": SAINIK_ROSTER.get(code, ()),
        "partnership_sainik_school_places": PARTNERSHIP_PLACES.get(code, ()),
        "partnership_sainik_school_supplement": PARTNERSHIP_SUPPLEMENT.get(code, ()),
        "defence_psu_financials": [row for row in PSU_FINANCIALS if row[2] == code],
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
            "value": PENURY_GRANT_INR, "period": PENURY_GRANT_PERIOD, "estimated": False,
            "source": "veterans_welfare_rates",
        },
        "sainik_schools": {"value": 79, "period": "7 May 2026", "source": "sainik_schools_2026", "estimated": False},
        "cantonment_boards": sum(map(len, BOARDS.values())),
        "veterans": {
            "value": sum(veteran_estimate(*pair) for pair in REGISTRATIONS.values()),
            "coverage": len(REGISTRATIONS), "period": VETERAN_PERIOD, "source": VETERAN_SOURCES,
            "estimated": True, "description": VETERAN_METHOD,
        },
    }
