"""Prepare single-district physical impacts from IFI-Impacts v3."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import re

from pipeline.core.store import save_interim
from pipeline.india import IFI_CHECKSUM, IFI_SOURCE

TENTATIVE = re.compile(r"\b(?:fear\w*|about|approx\w*|likely|estimated|suspected|probably|around|reportedly)\b", re.I)
NUMBER_WORDS = {word: value for value, word in enumerate(
    ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"))}
NUMBER = r"\b(?:\d+|" + "|".join(NUMBER_WORDS) + r")\b"
DEATH = r"(?:died|drowned|killed|dead)"
INJURY = r"(?:injured|hurt|wounded)"


def narrative_problem(description, counts):
    if TENTATIVE.search(description):
        return "tentative"
    if not description:
        return None
    for count, outcome in zip(counts, (DEATH, INJURY), strict=True):
        # Require a corroborating count in the same clause as the outcome.
        intervening = rf"(?:(?!{NUMBER}|\b{DEATH}\b|\b{INJURY}\b)[\w '-])*?"
        pattern = rf"({NUMBER}){intervening}\b{outcome}\b"
        evidence = {int(n) if n.isdecimal() else NUMBER_WORDS[n]
                    for n in re.findall(pattern, description)}
        if (count and evidence != {count}) or (not count and any(evidence)):
            return "unconfirmed"
    return None


def place_key(name):
    return re.sub(r"[^a-z0-9]", "", name.casefold().replace("&", " and "))


def event_impacts(rows, districts, excluded=None):
    impacts = defaultdict(list)
    id_counts = Counter(row["UEI"] for row in rows)
    for row in rows:
        event = row["UEI"]
        if id_counts[event] != 1 or not re.fullmatch(r"UEI-IMD-FL-\d{4}-\d+", event):
            continue
        district = districts.get((place_key(row["State"]), place_key(row["Districts"])))
        if not district or not row["District_LGD_Codes"].strip().isdecimal():
            continue
        try:
            start, end = (datetime.strptime(row[key], "%d-%m-%Y %H:%M").date()
                          for key in ("Start Date", "End Date"))
        except ValueError:
            continue
        if not 1967 <= start.year <= end.year <= 2023 or start > end:
            continue
        fields = [row[key].strip() for key in ("Human fatality", "Human injured")]
        counts = [int(value) if value.isdecimal() else None for value in fields]
        total = sum(count for count in counts if count is not None)
        if total <= 0:
            continue
        narrative = row.get("Description of Casualties/injured", "").strip().casefold()
        problem = ("ambiguous numeric cell" if any(value and count is None for value, count in zip(fields, counts))
                   else narrative_problem(narrative, counts))
        if problem:
            if excluded is not None:
                excluded[problem] += 1
            continue
        dates = [f"{day.day} {day:%b %Y}" for day in (start, end)]
        impacts[district].append({
            "id": event, "district": district, "casualties": total,
            "lower_bound": not all(value.isdecimal() for value in fields),
            "period": " to ".join(dict.fromkeys(dates)), "vintage": "older", "source": IFI_SOURCE,
            "date": start.isoformat(),
        })
    return dict(impacts)


def build(path):
    from pipeline.build.states import district_states
    from pipeline.core.store import load_interim
    from pipeline.india import DISPLAY_NAMES

    if sha256(path.read_bytes()).hexdigest() != IFI_CHECKSUM:
        raise ValueError("IFI-Impacts v3 CSV checksum mismatch")
    datameet = load_interim("datameet")
    districts = datameet["districts"]
    states = datameet["states"]
    keys = defaultdict(set)
    for district, home in zip(districts, district_states(districts, states), strict=True):
        if home < 0:
            continue
        state = place_key(states[home]["name"])
        name = district["name"]
        geoid = f"{district['state_code']:02d}-{district['code']:03d}"
        for alias in {name, DISPLAY_NAMES.get(name, name)}:
            keys[state, place_key(alias)].add(geoid)
    unique = {key: next(iter(ids)) for key, ids in keys.items() if len(ids) == 1}
    excluded = Counter()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        impacts = event_impacts(list(csv.DictReader(handle)), unique, excluded)
    save_interim(IFI_SOURCE, {"districts": impacts}, vintage="IFI-Impacts v3 (1967–2023)")
    print(f"{sum(map(len, impacts.values()))} single-district flood impact records in {len(impacts)} districts")
    print(f"Excluded {sum(excluded.values())} reports with uncertain counts: {dict(excluded)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    build(parser.parse_args().csv)
