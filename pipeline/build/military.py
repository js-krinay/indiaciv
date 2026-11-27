"""Public national headline data for the upstream advisor."""

import json

from ..core.paths import WEB_DATA
from ..core.store import write_web
from ..india.advisor_sources import BOARDS, BOARDS_PERIOD, FY, RMS_BY_STATE, RMS_PERIOD, RMS_SOURCE

REQUIRES = ["nation.json"]
PRODUCES = ["military.json"]

PUBLIC_INDICATORS = (
    "cantonment_boards", "legacy_sainik_schools", "sainik_schools",
    "rashtriya_military_schools", "defence_psu_turnover",
)


def public_statistics(statistics):
    national = {}
    periods = {}
    sources = []
    spending = statistics.get("defence_budget")
    if spending:
        national["spending"] = {"total": round(spending["total"] * 10_000_000)}
        periods["spending"] = spending["period"]
        sources.append(spending["source"])
        if share := statistics.get("defence_budget_share_gdp"):
            national["spending"]["pct_gdp"] = share["value"]
            sources.extend(share["source"])
    if veterans := statistics.get("veterans"):
        national["veterans"] = veterans["value"]
        periods["veterans"] = veterans["period"]
        sources.extend(veterans["source"])
    for key in PUBLIC_INDICATORS:
        if observation := statistics.get(key):
            national[key] = observation["value"]
            periods[key] = observation["period"]
            sources.append(observation["source"])
    return {"national": national, "vintage": periods, "sources": list(dict.fromkeys(sources))}


def build():
    nation = json.loads((WEB_DATA / "nation.json").read_text())
    statistics = {**nation["advisor_statistics"],
                  "cantonment_boards": {"value": sum(map(len, BOARDS.values())),
                                        "period": BOARDS_PERIOD, "source": "cantonment_boards"},
                  "legacy_sainik_schools": {"value": 33, "period": "7 May 2026", "source": "sainik_schools_2026"},
                  "rashtriya_military_schools": {"value": sum(RMS_BY_STATE.values()), "period": RMS_PERIOD,
                                               "source": RMS_SOURCE},
                  "defence_psu_turnover": {"value": 129_000 * 10_000_000, "period": FY,
                                           "source": "dpsu_turnover_fy26"}}
    write_web("military.json", public_statistics(statistics))
