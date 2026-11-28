"""Prepare historical shares of resident jobs from ORGI B-25 and B-18."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from ..core.store import load_interim, save_interim
from .census_civic import fetch_workbooks, validate_crosswalk
from .census_civic_sources import PERIOD
from .census_work_sources import INTERIM, workbook_manifest
from .orgi import Workbook, area_code, integer

TABLES = {"main": "B0425A", "marginal": "B0525B", "industry": "B0118"}
RESIDENCES = ("Total", "Rural", "Urban")
OCCUPATIONS = ("executive", "engineer", "scholar", "healer", "service", "clerk", "builder", "maker")
INDUSTRIES = {
    "mining": range(5, 10), "construction": range(41, 44), "manufacturing": range(10, 34),
    "wholesale": (46,), "retail": (47,), "transportation": range(49, 54), "utilities": range(35, 40),
    "information": range(58, 64), "finance": range(64, 67), "real_estate": (68,),
    "professional": range(69, 76), "admin": range(77, 83), "education": (85,), "health": range(86, 89),
    "arts": range(90, 94), "accommodation": (55, 56), "other": (*range(1, 4), *range(94, 100)),
}
# NIC 2008 includes inseparable defence or weapons activities in these classes.
EXCLUDED_NIC_CLASSES = frozenset({"2029", "2520", "2829", "3011", "3030", "3040"})
NIC_FAMILIES = {division: family for family, divisions in INDUSTRIES.items() for division in divisions}
DETAIL_LABELS = {
    "06": "Crude petroleum and natural gas extraction",
    "59": "Motion picture, video, sound recording and music publishing",
    "60": "Programming and broadcasting",
    "93": "Sports, amusement and recreation",
    "8411": "General public administration",
    "8412": "Regulation of social services",
    "8413": "Regulation of economic activity",
    "05": "Coal and lignite mining",
    "261": "Electronic components and boards",
    "291": "Motor vehicle manufacturing",
    "5222": "Service activities incidental to water transportation",
    "6612": "Security and commodity contract brokerage",
    "920": "Gambling and betting",
    "701": "Head offices",
}


def industry_details(entries):
    """Use explicitly published urban subtotals, including explicit zeroes."""
    return {code[-1]: values[2] for code, values in entries.items() if code and code[-1] in DETAIL_LABELS}


def member_industry_details(records, members, counts):
    denominator = counts["published"] - counts["excluded"]
    if not denominator or not members:
        return {}
    covered = [records[area] for area in sorted(members)]
    return {code: round(sum(row[code] for row in covered) / denominator, 7)
            for code in DETAIL_LABELS if all(code in row for row in covered)}


def occupation_family(code):
    division, sub, group, family = (*code, *([""] * (4 - len(code))))
    if group in {"345", "516"} or family == "8222" or division == "0":
        return None
    if division == "1":
        return "executive"
    if sub in {"21", "31"}:
        return "engineer"
    if sub in {"23", "33"} or group in {"242", "245"}:
        return "scholar"
    if group in {"222", "223", "322", "323", "324"}:
        return "healer"
    if division == "4":
        return "clerk"
    if division == "5" or sub == "91":
        return "service"
    if group in {"712", "713", "714", "724"}:
        return "builder"
    if sub in {"72", "73", "74", "81", "82", "83"} or group in {"932", "933"}:
        return "maker"
    return "other"


def industry_family(code):
    if not code:
        return "other"
    division = integer(code[0])
    group = code[1] if len(code) > 1 else ""
    if group in {"252", "304"} or division == 45 or code[-1] in EXCLUDED_NIC_CLASSES:
        return None
    if division == 84:
        return "public_admin" if group in {"841", "843"} else None
    return NIC_FAMILIES.get(division, "other")


def index_rows(kind, rows):
    """Key both-sexes, all-population rows by historic area and harmonised code."""
    industry = kind == "industry"
    columns = (8, 11, 14) if industry else (9, 12, 15)
    areas = defaultdict(dict)
    for row in rows:
        if not row or row[0] != TABLES[kind]:
            continue
        area = area_code(row[1], row[2])
        code = tuple(str(cell).strip() for cell in row[4:7 if industry else 8])
        while code and code[-1] == "0" * len(code[-1]):
            code = code[:-1]
        if code in areas[area]:
            raise ValueError(f"Duplicate {kind} entry for {area}, {code}")
        values = tuple(integer(row[i]) + (integer(row[i + 9]) if industry else 0) for i in columns)
        if values[0] != sum(values[1:]):
            raise ValueError(f"{kind} residence totals disagree for {area}, {code}")
        areas[area][code] = values

    return areas


def join_occupations(main, marginal):
    if main.keys() != marginal.keys():
        raise ValueError("B-25 A and B cover different areas")
    joined = {}
    for area, main_entries in main.items():
        marginal_entries = marginal[area]
        # Workbooks omit zero-count codes, so take the union within each area.
        zero = (0, 0, 0)
        joined[area] = {code: tuple(a + b for a, b in zip(main_entries.get(code, zero),
                                                        marginal_entries.get(code, zero), strict=True))
                        for code in main_entries.keys() | marginal_entries.keys()}
    return joined


def partition(kind, areas):
    """Convert the published hierarchy to mutually exclusive counts by residence."""
    classify = industry_family if kind == "industries" else occupation_family
    result = {}
    for area, entries in areas.items():
        children = defaultdict(list)
        for code in entries:
            if code:
                parent = code[:-1]
                while parent not in entries:
                    parent = parent[:-1]
                children[parent].append(code)
        for i, residence in enumerate(RESIDENCES):
            counts = Counter()
            for code, values in entries.items():
                remainder = values[i] - sum(entries[child][i] for child in children[code])
                if remainder < 0:
                    raise ValueError(f"{kind} detail exceeds subtotal for {area}, {code}, {residence}")
                family = classify(code) if code else "other"
                if remainder:
                    counts[family or "excluded"] += remainder
            counts["published"] = entries[()][i]
            result[area, residence] = counts
    return result


def observation(kind, counts, benchmark=None, scope="urban member districts"):
    total = counts["published"] - counts["excluded"]
    if not total:
        return None
    labels = (*OCCUPATIONS, "other") if kind == "occupations" else (*INDUSTRIES, "public_admin")
    values = {label: round(counts[label] / total, 7) for label in labels}
    if benchmark is not None:
        national = benchmark["published"] - benchmark["excluded"]
        ratios = {}
        for label in OCCUPATIONS:
            share, baseline = counts[label] / total, benchmark[label] / national
            if baseline and max(share, baseline) >= .01:
                ratio = share / baseline
                if ratio >= 1.5:
                    ratios[label] = ratio
        best = max(ratios, key=ratios.get, default=None)
    record = {"values": values, "scope": scope, "source": f"orgi_work_{kind}",
              "period": PERIOD, "vintage": "older"}
    if benchmark is not None:
        record["benchmark"] = {label: round(benchmark[label] / national, 7) for label in labels}
        if best:
            record["specialist"] = {"family": best, "ratio": round(ratios[best], 2)}
    return record


def sum_areas(rows, areas, residence):
    total = Counter()
    for area in sorted(set(areas)):
        total.update(rows[area, residence])
    return total


def prepare(directory):
    from ..build.city_view import cohort
    from ..build.yields import district_state_map

    districts = load_interim("census_a01")["districts"]
    states = district_state_map(load_interim("datameet"))
    validate_crosswalk(states, districts)
    profiles = load_interim("city_footprints")["profiles"]
    controls = {kind: {} for kind in TABLES}
    series = {"occupations": {}, "industries": {}}
    details = {}
    manifest = sorted(workbook_manifest(), key=lambda entry: (entry[1], entry[0]))
    main = None
    for kind, state, filename, checksum, _, _ in manifest:
        book = Workbook(filename, checksum, TABLES[kind])
        areas = index_rows(kind, book.rows(directory / filename))
        # National editions also print historic state rows, which are redundant here.
        areas = {area: values for area, values in areas.items() if area.startswith(state + "-")}
        expected = {state + "-000", *(code for code in districts if code.startswith(state + "-"))}
        if areas.keys() != expected or areas.keys() & controls[kind].keys():
            raise ValueError(f"Unexpected or duplicate coverage in {filename}")
        controls[kind].update((area, entries[()]) for area, entries in areas.items())
        if kind == "industry":
            series["industries"].update(partition("industries", areas))
            details.update((area, industry_details(entries)) for area, entries in areas.items())
        elif kind == "main":
            main = areas
        else:
            series["occupations"].update(partition("occupations", join_occupations(main, areas)))
            main = None

    for kind, totals in controls.items():
        for i, residence in enumerate(RESIDENCES):
            if sum(totals[code][i] for code in districts) != totals["00-000"][i]:
                raise ValueError(f"{kind} district totals disagree with the national {residence} total")
            for state in {code[:2] for code in districts}:
                members = [code for code in districts if code.startswith(state + "-")]
                if sum(totals[code][i] for code in members) != totals[state + "-000"][i]:
                    raise ValueError(f"{kind} district totals disagree with {state} {residence}")

    cities = {}
    reviewed = set(cohort())
    for city, profile in profiles.items():
        if city not in reviewed:
            continue
        members = {district["id"] for district in profile["districts"]}
        if not members or not members <= districts.keys():
            continue
        for kind, records in series.items():
            counts = sum_areas(records, members, "Urban")
            benchmark = records["00-000", "Urban"] if kind == "occupations" else None
            if record := observation(kind, counts, benchmark):
                cities.setdefault(city, {})[kind] = record
                if kind == "industries":
                    record["details"] = member_industry_details(details, members, counts)
    return cities


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        fetch_workbooks(args.directory, workbook_manifest())
    save_interim(INTERIM, prepare(args.directory), vintage=PERIOD)
