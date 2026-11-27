"""Advisors' configurable tables in the upstream district-table format."""

import json
import math
from collections import Counter

from ..core.lens_values import decode as decode_lens_values
from ..core.paths import WEB_DATA
from ..core.store import write_web
from ..india.advisor_sources import BOARDS_PERIOD
from .advisor_inventory import FY, SNAPSHOT, column, index_inventory, inventory_columns
from .advisor_observations import city_district_observations, path_value, place_columns
from .counties import field
from .military import BOARD_SOURCE, CIVIC
from .state_metrics import QUARTER

REQUIRES = [
    "world.json", "lenses.json", "workplace.json", "cities.json", "city_view.json", "states.json", "nation.json", "counties.json",
    "resources.json", "wonders.json", "infrastructure.json", "protected_land.json", "protected_ramsar.json",
    "military.json",
]
PRODUCES = ["advisor_tables.json"]


def column_table(places, id_key):
    definitions = {id_key: field(id_key, id_key, "text")}
    for observations in places.values():
        for key, observation in observations.items():
            base = field(key, key, "text") if observation.get("hidden") else {"key": key}
            definitions.setdefault(key, {**base, "estimated": False,
                                         **{k: v for k, v in observation.items() if k != "value"}})
            vintage = observation.get("vintage")
            if (vintage == "older" and key in ("median_age", "unemployment", "state_urban_unemployment_15_plus",
                                               "registered_veterans", "veterans", "veteran_share", "veterans_pct")
                    or key == "city_bad_air" and vintage == "2026 observed"):
                definitions[key]["hide_rank"] = True
    columns = list(definitions)
    provenance = {}
    for key, observations in places.items():
        differences = {}
        for name, observation in observations.items():
            if observation.get("hidden"):
                continue
            definition = definitions[name]
            detail = {k: observation.get(k, False if k == "estimated" else None)
                      for k in ("source", "period", "vintage", "estimated", "scope", "status",
                                "description", "sparse", "coverage")
                      if observation.get(k, False if k == "estimated" else None) != definition.get(k)}
            if observation.get("lens") and observation["lens"] != definition.get("lens"):
                detail["lens"] = observation["lens"]
            if definition.get("heading_caption") and observation.get("period") != definition["heading_caption"]:
                detail["period"] = observation["period"]
            if detail and observation.get("vintage") == "older":
                detail["vintage"] = "older"
                detail["period"] = observation["period"]
            if detail and observation.get("value") is not None:
                differences[name] = detail
        if differences:
            provenance[key] = differences
    return {
        "columns": columns,
        "fields": list(definitions.values()),
        "rows": [[key, *(observations.get(name, {}).get("value") for name in columns[1:])]
                 for key, observations in places.items()],
        "provenance": provenance,
    }


def declared_columns(definitions, level, place):
    out = {}
    for definition in definitions:
        path = definition.get("paths", {}).get(level)
        if not path:
            continue
        parent = path_value(place, path[:-1])
        value = parent.get(path[-1]) if isinstance(parent, dict) else None
        if value is None and parent is not None:
            value = definition.get("default")
        row = place.get("state", place.get("city", {}))
        detail = path_value(row, definition.get("provenance_path", [])) if definition.get("provenance_path") else None
        record = {k: v for k, v in definition.items() if k not in ("key", "paths", "provenance_path", "default")}
        for key in ("period", "vintage", "source", "estimated", "description", "lens", "status", "scope"):
            if detail and detail.get(key) is not None:
                record[key] = detail[key]
        out[definition["key"]] = {**record, "value": value}
    return out


DISTRICT_COLUMNS = {
    "population": "population", "density": "density", "median_age": "median_age", "area_km2": "land_km2",
    "land_forest": "forest", "land_crop": "crop", "land_developed": "developed", "foreign_born": "foreign_born",
    "bachelors": "bachelors", "commute": "commute", "homeownership": "homeownership", "faith": "faith",
    "registered_veterans": "veterans", "veteran_share": "veterans_pct", "workplace_jobs": "qcew_jobs",
}


def advisor_tables(world, lenses, workplace, cities, city_view, states, nation, counties,
                   resources, wonders, infrastructure, protected, ramsar, military=None):
    districts = lenses["places"]["counties"]
    boards = [row for row in (military or {}).get("installations", []) if row["tier"] == CIVIC]
    board_counts = {level: Counter(row[place_key] for row in boards if row[place_key] is not None)
                    for level, place_key in (("counties", "county"), ("metros", "cbsa"))}
    profiles = city_view["profiles"]
    indexes, gateways = index_inventory(world, cities, profiles, districts, resources, wonders,
                                       infrastructure, protected, ramsar)
    district_cells = set(world["county"])
    states_by_id = {row["abbr"]: row for row in states}
    cities_by_id = {row["id"]: row for row in cities}
    county_columns = counties["columns"]
    county_rows = {row[county_columns.index("geoid")]: dict(zip(county_columns, row)) for row in counties["rows"]}
    lens_index = {row["id"]: row for row in lenses["lenses"]}
    if monsoon := lens_index.get("monsoon_2026"):
        lens_index["monsoon_2026"] = {**monsoon, "values": decode_lens_values(monsoon["values"], len(world["owner"]))}
    disasters = lenses.get("disasters", {})
    definitions = [*nation.get("advisor_fields", []), *disasters.get("advisor_fields", [])]
    memberships, populations, plaques = city_district_observations(cities, profiles)
    hex_area = 1.5 * math.sqrt(3) * world["grid"]["radius"] ** 2
    tables = {}
    national = nation.get("nation", {})
    benchmarks = {
        "states": {**nation.get("metrics", {}).get("unemployment", {}), "period": QUARTER,
                   "scope": "rural and urban", "population": "labour force aged 15+"},
        "metros": {"value": national.get("unemployment"),
                   **national.get("provenance", {}).get("unemployment", {}),
                   "population": "urban labour force aged 15+"},
    }
    city_names = {row["id"]: row["name"] for row in cities}
    mapped_city_counts = Counter(abbr for city in cities for abbr in city.get("states", []))
    wonder_names = {row["id"]: row.get("name", row["id"]) for row in wonders.get("wonders", [])}
    resource_type_names = {row["id"]: row["name"] for row in resources.get("types", [])}
    resource_names = {index: row.get("name") or resource_type_names[row["type"]]
                      for index, row in enumerate(resources.get("items", []))}
    resource_sources = {index: row.get("source") for index, row in enumerate(resources.get("items", []))}
    for level, id_key, identities, records, work_group, observations_by_place in (
        ("states", "abbr", world["states"], states_by_id, "states", disasters.get("states", {})),
        ("metros", "id", cities, cities_by_id, "cities", {}),
        ("counties", "geoid", world["counties"], districts, "districts", disasters.get("districts", {})),
    ):
        observations = {}
        for index, identity in enumerate(identities):
            key = identity[id_key]
            row = records.get(key, {})
            profile = profiles.get(key, {}) if level == "metros" else {}
            comparable = level == "states" or profile.get("method") == "ghsl" or level == "counties" and index in district_cells
            kinds = ("protected", "resources", "wonders", "ports", "airports", "rail", "roads")
            sites = {kind: indexes[level][key].get(kind, []) for kind in kinds
                     if comparable or (level == "counties" and kind in indexes[level][key]
                                       and kind in ("resources", "wonders") and districts.get(key, {}).get("sites"))}
            names = gateways[level][key] if level in gateways and infrastructure.get("trade") else None
            columns = place_columns(level, row, identity, profile, lens_index,
                                    protected.get("shares", {}).get(level, {}).get(key),
                                    (memberships[key], populations.get(key), plaques[key]), hex_area)
            columns.update(inventory_columns(sites, names, resources.get("advisor_fields", [])))
            if count := board_counts.get(level, {}).get(key):
                columns["cantonment_boards"] = column(
                    "Matched cantonment boards", "int", "civic boards", "Defence & veterans",
                    BOARDS_PERIOD, BOARD_SOURCE, count, sparse=True,
                    coverage="Boards with a unique civil town joined to this district or verified urban footprint.")
            place = {"hazardSummary": profile.get("hazard_summary") if level == "metros" else observations_by_place.get(key)}
            if level == "states":
                place["state"] = row
            elif level == "metros":
                place.update(city=row, profile=profile)
            columns.update(declared_columns(definitions, level, place))
            work = workplace.get(work_group, {}).get(key)
            for definition in workplace.get("advisor_fields", []):
                columns[definition["key"]] = {
                    **{k: v for k, v in definition.items() if k not in ("key", "path")},
                    "value": path_value(work, definition["path"]),
                }
            for local in (row.get("advisor_columns", {}), profile.get("advisor_columns", {})):
                for name, record in local.items():
                    if name not in columns or record.get("value") is not None:
                        columns[name] = {**record, **row.get("provenance", {}).get(name, {})}
            if level == "states":
                population = row.get("population")
                output = path_value(row, ("yields", "gold"))
                output_total = path_value(nation, ("nation", "yields", "gold"))
                population_total = path_value(nation, ("nation", "population"))
                columns["state_population_share"] = column(
                    "Share of India's projected population", "pct", "share", "People",
                    "1 March 2026", "tg_projections",
                    population / population_total if population is not None and population_total else None)
                columns["state_gdp_share"] = column(
                    "Share of India's nominal GDP", "pct", "share", "Economy", FY, "gsdp_fy26",
                    output / output_total if output is not None and output_total else None,
                    estimated=bool(path_value(row, ("yield_meta", "gold", "estimated"))))
                columns["mapped_city_count"] = column(
                    "Mapped urban agglomerations", "int", "urban agglomerations", "Geography",
                    SNAPSHOT, "un_wup_cities", mapped_city_counts[key])
            if level == "metros":
                for field, label, period, source in (
                    ("growth", "Population growth", row.get("growth_period"), "un_wup_cities"),
                    ("gdp", "Nominal GDP", FY, "gsdp_fy26"),
                    ("gdp_per_capita", "GDP per resident", FY, ["gsdp_fy26", "un_wup_cities"]),
                ):
                    rank = row.get("ranks", {}).get(field)
                    count = row.get("rank_counts", {}).get(field)
                    if rank is not None and count and period:
                        columns[f"atlas_{field}_rank"] = column(
                            f"{label} rank across mapped urban agglomerations", "int", f"rank of {count}",
                            "People" if field == "growth" else "Economy", period, source, rank,
                            estimated=field != "growth", hide_rank=True)
            if level == "metros" and (extent := row.get("mapped_extent")):
                columns["mapped_footprint_hexes"] = column(
                    "Mapped footprint hexes", "int", "hexes", "Geography", extent["period"],
                    "city_footprints", extent["hexes"], estimated=True)
            if level == "counties":
                district_sites = row.get("sites", {})
                for kind, title, source, names in (
                    ("cities", "Mapped urban agglomerations", "un_wup_cities", city_names),
                    ("wonders", "Mapped wonders", "india_wonders", wonder_names),
                    ("resources", "Mapped resources", None, resource_names),
                ):
                    labels = [names[key] for key in district_sites.get(kind, []) if key in names]
                    if labels:
                        if kind == "resources":
                            source = sorted({resource_sources[index] for index in district_sites[kind]
                                             if resource_sources.get(index)})
                        columns[f"district_{kind}"] = column(title, "text", "mapped places", "Geography",
                                                             SNAPSHOT, source, " · ".join(labels))
                for lens_id, lens in lens_index.items():
                    if lens_id in columns or row.get(lens_id) is None or not lens.get("period"):
                        continue
                    detail = row.get("provenance", {}).get(lens_id, lens)
                    fmt = {"pct": "pct", "int": "int", "money": "inr"}.get(lens.get("format"), "float")
                    columns[lens_id] = column(
                        lens["name"], fmt, lens.get("unit"), "District indicators",
                        detail.get("period", lens["period"]), detail.get("source", lens.get("source")),
                        row[lens_id], vintage=detail.get("vintage"), estimated=bool(detail.get("estimated")), lens=lens_id)
                native = county_rows.get(key, {})
                meta = counties.get("provenance", {}).get(key, {})
                for name, upstream in DISTRICT_COLUMNS.items():
                    if name in columns and native.get(upstream) is not None:
                        columns[name].update(value=native[upstream], **meta.get(upstream, {}))
                columns["cell"] = {"hidden": True, "value": native.get("cell")}
                columns["center"] = {"hidden": True, "value": row.get("center")}
            aliases = {"land_km2": "area_km2", **{
                f"y_{name.removeprefix('yield_')}": name
                for name in columns if name.startswith("yield_") and not name.endswith("_rank")
            }}
            if level == "metros":
                aliases["gdp_pc"] = "gdp_per_resident"
            else:
                aliases.update(veterans="registered_veterans", veterans_pct="veteran_share")
            for alias, original in aliases.items():
                record = columns.get(original, {})
                columns[alias] = {"hidden": True, "value": record.get("value"), "vintage": record.get("vintage")}
            growth = row.get("growth")
            columns["growth"] = {"hidden": True, "value": growth if growth is not None else
                                 columns.get("projected_growth", {}).get("value")}
            observations[key] = columns
        tables[level] = column_table(observations, id_key)
        for definition in tables[level]["fields"]:
            if definition["key"] == "unemployment" and level in benchmarks:
                definition["benchmark"] = benchmarks[level]
    return tables


def build():
    write_web("advisor_tables.json", advisor_tables(
        *(json.loads((WEB_DATA / name).read_text()) for name in REQUIRES)
    ))
