"""2026 resident workforce estimates and workplace specialisations."""

from fractions import Fraction

from ..india.city_sources import AGE_API_SOURCE, AGE_SOURCE, CLUSTER_REPORTS, LABOUR_PERIOD, LABOUR_SOURCE
from ..sources.worldpop_age import median_age
from .city_view import apportion

SECTORS = ("agriculture", "industry", "services")
MAX_PLAQUES = 5


def resident_industries(employed, shares, provenance):
    if not employed or not shares:
        return None, {}
    weights = dict(zip(SECTORS, shares, strict=True))
    return apportion(employed, weights), {**provenance, "employed": employed, "estimated": True}


def quarterly_resident_industries(population, profile, metrics, shares):
    age_0_14 = profile.get("age_0_14")
    wpr = metrics.get("wpr", {}).get("value")
    employed = round(population * (1 - age_0_14 / 100) * wpr) if age_0_14 is not None and wpr is not None else None
    return resident_industries(employed, shares, {
        "period": LABOUR_PERIOD, "source": [LABOUR_SOURCE, "tg_projections"], "scope": "Residents age 15+",
    })


def qualitative_plaques(city_id, members):
    return [
        {"kind": "qualitative", "district": district, "icon": icon, "label": label,
         "source": source, "citation": f"{publisher} · {title}", "url": url, "period": period,
         "evidence": evidence, "estimated": False,
         **({"vintage": "2026"} if source == "upeida_lucknow_cluster" else {})}
        for source, (title, publisher, period, url, entries) in CLUSTER_REPORTS.items()
        for cid, district, icon, label, evidence in entries
        if cid == city_id and district in members
    ][:MAX_PLAQUES]


REGISTRATION_METHOD = (
    f"Registered-enterprise concentration requires a dated district and national NIC extract from the same "
    f"Udyam universe. Its location quotient divides the district share by the national share. The floors are "
    f"1,000 district registrations, 50 in the category and a quotient of "
    f"1.5. Rank by registrations above the national-share expectation, with up to "
    f"{MAX_PLAQUES} plaques. The current release uses qualitative evidence."
)


def age_profile(population, ages, source=AGE_SOURCE):
    total = sum(ages.values())
    if total <= 0:
        return None
    groups = {0: 0, 15: 0, 60: 0}
    cumulative = 0
    median = None
    for age, mass in sorted(ages.items()):
        groups[0 if age < 15 else 15 if age < 60 else 60] += mass
        cumulative += mass
        if median is None and cumulative >= total / 2:
            median = [age, {0: 0, 1: 4, 90: None}.get(age, age + 4)]
    counts = apportion(population, groups)
    midlife_bins = range(35, 65, 5)
    bands = {"midlife": round(population * sum(ages[age] for age in midlife_bins) / total)} if all(
        age in ages for age in midlife_bins) else {}
    return {
        "counts": dict(zip(("0_14", "15_59", "60_plus"), counts.values())),
        "median_band": median,
        "median": median_age(ages),
        "bands": bands,
        "source": source, "period": "mid-2026", "vintage": "2026 estimate", "estimated": True,
        "method": "worldpop_api_footprint_to_un" if source == AGE_API_SOURCE else "worldpop_footprint_to_un",
    }


def workforce(population, adult_population, rates, state):
    all_age_wpr, adult_wpr, unemployment, *mix = (Fraction(str(value)) / 100 for value in rates)
    all_ages = round(population * all_age_wpr)
    adults = None if adult_population is None else round(adult_population * adult_wpr)
    weights = dict(enumerate(mix))
    icons = apportion(20, weights)
    counts = {} if adults is None else apportion(adults, weights)
    return {
        "employed_all_ages": all_ages, "employed_15_plus": adults,
        "population_15_plus": adult_population, "state": state,
        "state_urban_wpr_all_ages": float(all_age_wpr), "state_urban_wpr_15_plus": float(adult_wpr),
        "state_urban_unemployment_15_plus": float(unemployment),
        "industries": [
            {"sector": sector, "state_urban_share": float(mix[i]), "icons": icons[i], "employed": counts.get(i)}
            for i, sector in enumerate(SECTORS)
        ],
        "source": LABOUR_SOURCE, "period": LABOUR_PERIOD, "estimated": True,
        "method": "primary_state_urban_cws",
    }


def footprint_workforce(population, adult_population, state_populations, rates):
    if not state_populations or any(state not in rates for state in state_populations):
        return None
    states = sorted(state_populations)
    if len(states) == 1:
        return workforce(population, adult_population, rates[states[0]], states[0])
    resident_mass = sum(state_populations.values())
    worker_mass = labour_mass = all_age_workers = 0
    sector_mass = [0, 0, 0]
    for state in states:
        residents = state_populations[state]
        all_ages, adults, unemployment, *mix = rates[state]
        # The city-wide age share is applied uniformly across fragments.
        workers = residents * adults / 100
        worker_mass += workers
        labour_mass += workers / (1 - unemployment / 100)
        all_age_workers += residents * all_ages / 100
        for index, share in enumerate(mix):
            sector_mass[index] += workers * share / sum(mix)
    weighted = [100 * all_age_workers / resident_mass, 100 * worker_mass / resident_mass,
                100 * (labour_mass - worker_mass) / labour_mass,
                *(100 * mass / worker_mass for mass in sector_mass)]
    result = workforce(population, adult_population, weighted, states[0])
    return {**result, "state": None, "states": states, "method": "footprint_state_urban_cws"}
