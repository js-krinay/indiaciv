"""Compute research points from the public institution inventories."""

from collections import Counter, defaultdict

from ..india.science_sources import ROSTER

WEIGHTS = {
    "IIT": 2, "IISc": 2, "IISER": 2, "NIT": 1, "AIIMS": 1,
    "AIIMS under development": 0, "CSIR": 2, "ISRO and DoS": 2,
}
RULE = (
    "Two points per IIT, IISc, IISER, CSIR lab or public ISRO and Department of Space centre. "
    "One point per NIT or AIIMS with services or classes. AIIMS under development contribute zero. "
    "City scores use verified sites inside the clipped urban footprint, or the centre hex where no footprint exists. "
    "Institutions without verified points count in their state and India."
)


def research_by_state(roster=ROSTER):
    by_state = defaultdict(Counter)
    for kind, institutes in roster.items():
        for _, state, _ in institutes:
            by_state[state][kind] += 1
    return by_state


def science_yield(counts):
    return sum(WEIGHTS[kind] * count for kind, count in counts.items())
