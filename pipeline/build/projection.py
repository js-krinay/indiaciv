"""2026 projections (interim tg_projections, pipeline/india/projections.py) for today's states and union territories.

Helpers only (no build()): the report's units and names differ from DataMeet's state names.
"""

from __future__ import annotations

# DataMeet state → the report's Table 21 units (one unless merged since; others use the same name).
UNITS = {
    "Andaman & Nicobar": ["Andaman & Nicobar Islands"], "Chandigarh": ["Chandigarh *"], "Delhi": ["NCT of Delhi"],
    "Uttarakhand": ["Uttaranchal"], "Jammu & Kashmir": ["Jammu & Kashmir (UT)"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Dadra & Nagar Haveli", "Daman Diu"],
}
UNIT_BY_CENSUS_STATE = {25: "Daman Diu", 26: "Dadra & Nagar Haveli"}  # for the merged UT's districts
NORTH_EAST = {"Arunachal Pradesh", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"}
PROFILE_NAMES = {"Delhi": "NCT OF DELHI", "Jammu & Kashmir": "JAMMU & KASHMIR (UT)"}
STATE_GROWTH_PERIOD = "1 Mar 2025 – 1 Mar 2026"
CITY_GROWTH_PERIOD = "1 Jul 2025 – 1 Jul 2026"


def units(state: str) -> list[str]:
    return UNITS.get(state, [state])


def state_population(tg: dict, state: str) -> int:
    """Projected population on 1 March 2026 (people; the report counts thousands)."""
    return 1000 * sum(tg["population"][u]["2026"][0] for u in units(state))


def state_vitals(tg: dict, state: str) -> dict:
    """2026 sex ratio (Table 21) and projected growth between the two March totals (Table 8)."""
    rows = [tg["population"][u] for u in units(state)]
    men, women = sum(r["2026"][1] for r in rows), sum(r["2026"][2] for r in rows)
    vitals = {"sex_ratio": round(1000 * women / men)}
    annual = tg.get("annual_population")
    if annual:
        p25, p26 = (sum(annual[u][year] for u in units(state)) for year in ("2025", "2026"))
        vitals.update(growth=p26 / p25 - 1, growth_period=STATE_GROWTH_PERIOD)
    return vitals


def district_growth(tg: dict, state: str, census_state_code: int) -> float:
    """Projected growth factor to 2026 of the report unit a district belongs to."""
    us = units(state)
    unit = us[0] if len(us) == 1 else UNIT_BY_CENSUS_STATE[census_state_code]
    p = tg["population"][unit]
    return p["2026"][0] / p["2011"][0]


def state_profile(tg: dict, state: str) -> dict | None:
    """2026 characteristics (T-17) and interpolated health (17A), or None where the report has no detailed tables
    (Goa, Ladakh and the smaller UTs). The seven smaller North-East states share one combined profile."""
    key = PROFILE_NAMES.get(state) or ("NORTH-EAST STATES (EXCLUDING ASSAM)" if state in NORTH_EAST else state.upper())
    if key not in tg["profile"]:
        return None
    health = tg["indicators"].get(key, {}) if "annual_population" in tg else {}
    return {**tg["profile"][key], **health, **({"health": {"period": "2026", "estimated": True}} if health else {})}
