"""Assign mapped inventories to the same areas used by the advisor tables."""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from ..core.hexgrid import HexGrid

SNAPSHOT = "November 2026"
FY = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
OSM = "osm_transport"
PROTECTED = ["osm_protected", "rsis_protected", "wikidata_protected", "wii_protected", "ntca_protected"]
PORTS = ["cwprs_port_locations", "featured_port_locations"]


def column(label, format, unit, group, period, source, value, **meta):
    return {"label": label, "format": format, "unit": unit, "group": group, "period": period,
            "source": source, "value": value, **meta}


def inventory_columns(sites, gateways, definitions):
    out = {}

    def add(key, label, group, source, value, format="int", unit="mapped sites", period=SNAPSHOT, **meta):
        out[key] = column(label, format, unit, group, period, source, value, **meta)

    def count(key, label, group, source, category, predicate=lambda row: True):
        if (rows := sites.get(category)) is not None:
            add(key, label, group, source, sum(predicate(row) for row in rows),
                description="Count within the served inventory and the available mapped geography.")

    def labels(key, label, source, category, get, description):
        if (rows := sites.get(category)) is not None:
            names = sorted({name for row in rows if (name := get(row))})
            add(key, label, "Commerce", source, ", ".join(names) or None,
                "text", "mapped labels", description=description)

    for key, label, kind in (("wonders_count", "Mapped wonders", None),
                             ("landmark_count", "Built wonders", "landmark"),
                             ("natural_wonders_count", "Natural wonders", "natural")):
        count(key, label, "Culture", "india_wonders", "wonders", lambda row: kind is None or row["kind"] == kind)
    parks = ["wii_protected", "osm_protected", "wikidata_protected"]
    count("park_wonders_count", "Largest-area national park wonders", "Culture", parks,
          "wonders", lambda row: row.get("rule") == "national_park")
    count("research_wonders_count", "Mapped research wonders", "Culture", ["research_campuses", "research_points"],
          "wonders", lambda row: row.get("rule") == "research_inventory")
    if (wonders := sites.get("wonders")) is not None:
        add("park_wonder_area_ranks", "National park area ranks", "Culture", parks,
            " · ".join(f"#{row['rank']} {row['name']}" for row in wonders if row.get("rule") == "national_park") or None,
            "text", "rank and name", description="Order by published area within the five largest parks in the WII inventory.")
        add("wonder_extent_count", "Wonders with mapped protected extent", "Culture", ["osm_protected", "rsis_protected"],
            sum(bool(row.get("cells")) for row in wonders),
            description="Wonders linked to protected-land hexes from accepted extents.")
    if (protected := sites.get("protected")) is not None:
        period = "Oct–Nov 2026"
        add("protected_count", "Mapped protected designations", "Land", PROTECTED, len(protected), period=period,
            description="Mapped designation markers within the referenced geography. Distinct designations can overlap.")
        areas = [f"{row['name']} · {indian_number(Decimal(str(row['area_ha'])) / 100)} km² · {row['status']} · {row['authority']}"
                 for row in protected if isinstance(row.get("area_ha"), (int, float))]
        add("protected_official_areas", "Official protected site areas", "Land",
            ["rsis_protected", "wii_protected", "ntca_protected"], " | ".join(areas) or None, "text",
            "km² per designation", period, description="Official areas at mapped sites. Distinct protected designations can overlap.")
    if gateways is not None:
        sources = [OSM, "pib_dfc_completion", "cwprs_port_locations", "datameet"]
        names = " · ".join(sorted(gateways, key=str.casefold))
        desc = ("Major ports and dedicated freight corridors on state or UT tiles. City ports use the urban footprint, "
                "and corridors also use adjacent tiles.")
        add("trade_gateways", "Trade gateways", "Commerce", sources, names or None, "text", "gateway names", description=desc)
        add("trade_gateway_count", "Mapped trade gateways", "Commerce", sources, len(gateways), unit="gateways", description=desc)
    if (ports := sites.get("ports")) is not None:
        cargo = [row["cargo"] for row in ports if (row.get("cargo") or {}).get("share", 0) > 0]
        total = sum(row["share"] for row in cargo)
        add("port_cargo_share", "Share of major-port cargo", "Commerce", "mopsw_port_cargo", total if cargo else None,
            "pct", "share of cargo across 12 authorities", FY,
            description="Sum of the published cargo shares of mapped major port authorities in the area. Ministry advance estimates.")
        authority_splits = [
            f"{row['name']} · #{row['rank']} · {row['cargo']['share']:.2%} of major-port cargo"
            f" · {row['cargo']['domestic']:.2%} coastal · {row['cargo']['foreign']:.2%} overseas"
            for row in ports if (row.get("cargo") or {}).get("share", 0) > 0
        ]
        add("port_authority_splits", "Cargo by mapped port authority", "Commerce", "mopsw_port_cargo",
            " | ".join(authority_splits) or None, "text", "authority, rank and cargo shares", FY,
            description="Published cargo shares by authority. Ministry advance estimates.")
        for key, label in (("foreign", "Overseas port cargo"), ("domestic", "Coastal port cargo")):
            value = sum(row["share"] * row[key] for row in cargo) / total if total else None
            add(f"port_{key}", label, "Commerce", "mopsw_port_cargo", value, "pct", "share of major-port cargo", FY,
                description="Cargo-weighted share for mapped major port authorities in the area. Ministry advance estimates.")
        rank = min((row["rank"] for row in ports if isinstance(row.get("rank"), int)), default=None)
        add("major_port_rank", "Best major-port cargo rank", "Commerce", "mopsw_port_cargo", rank, "int",
            "rank among 12 authorities", FY, description="Lowest national cargo rank among mapped major port authorities in the area.")
        historical = [(row["name"], row["historical_cargo_split"])
                      for row in ports if row.get("historical_cargo_split")]
        if historical:
            provenance = historical[0][1]
            shares = " | ".join(f"{name} · {split['domestic']:.2%} coastal · {split['foreign']:.2%} overseas"
                                for name, split in historical)
            add("non_major_port_cargo_mix", "Non-major port cargo mix", "Commerce", provenance["source_id"],
                shares, "text", "shares of each port's cargo", provenance["period"], vintage="older",
                description="Coastal and overseas shares for each matched non-major port, based on Ministry of Ports, Shipping and Waterways Table 2.2.1.")
    for kind, label in (("roads", "Highway"), ("rail", "Railway")):
        for key, index, title in (("names", 4, "names"), ("networks", 5, "network tags")):
            labels(f"{kind}_{key}", f"{label} {title}", OSM, kind,
                   lambda row: row[index] if len(row) > index else None,
                   "Labels from tagged OpenStreetMap ways in the area.")
    labels("port_names", "Mapped port names", [OSM, *PORTS], "ports", lambda r: r["name"],
           "Port authorities and named facilities in the mapped inventory.")
    labels("port_cities", "Port localities", PORTS, "ports", lambda r: r.get("city"),
           "Documented facility localities of major and featured ports.")
    labels("port_states", "Port states and UTs", "datameet", "ports", lambda r: r.get("state"),
           "DataMeet state or union territory at the facility, with a coastal placement fallback.")
    labels("airport_cities", "Airport municipalities", "ourairports", "airports", lambda r: r.get("city"),
           "Municipality in the civilian OurAirports inventory.")
    labels("airport_states", "Airport states and UTs", "datameet", "airports", lambda r: r.get("state"),
           "DataMeet state or union territory at the airport coordinates.")
    for key, label, source, kind in (
        ("port_count", "Mapped ports", [OSM, *PORTS], "ports"),
        ("airport_count", "Mapped airports", "ourairports", "airports"),
        ("rail_links", "Mapped rail links", OSM, "rail"),
        ("highway_links", "Mapped highway links", OSM, "roads"),
    ):
        count(key, label, "Commerce", source, kind)
    if (resources := sites.get("resources")) is not None:
        capacity = [row["value"] for row in resources if row["meta"]["unit"] == "MW"
                    and isinstance(row.get("value"), (int, float))]
        add("energy_mw", "Mapped generating capacity", "Energy", "gem_power", sum(capacity) if capacity else None, "mw", "MW",
            "September 2026", description="Rated capacity of operating sites in the mapped inventory, subject to each technology’s threshold.")
        mines = [row for row in resources if row["meta"]["category"] == "mineral"]
        add("mines_count", "Mapped mines", "Energy", ["gem_coal", "gem_iron"], len(mines), period="2026",
            description="Selected operating mines in the map inventory.")
        inventory_credit(out["mines_count"], mines, sort_periods=True)
        add("oil_gas_count", "Mapped oil and gas fields", "Energy", "gem_oil_gas",
            sum(row["meta"]["source"] == "gem_oil_gas" for row in resources), period="March 2026",
            description="Mapped operating extraction fields.")
        crops = [row for row in resources if row["meta"]["category"] == "agri"]
        add("crop_presence", "Mapped crop presence", "Land", "tea_regions",
            " · ".join(sorted({row["meta"]["name"] for row in crops})) or None, "text", "documented crops",
            description="Selected growing areas and representative markers in the atlas.")
        inventory_credit(out["crop_presence"], crops, sort_periods=True)
        for definition in definitions:
            key = definition["type"]
            rows = [row for row in resources if row["type"] == key or key in row.get("byproducts", [])]
            values = [row["value"] for row in rows if isinstance(row.get("value"), (int, float))]
            record = {k: definition[k] for k in ("label", "format", "unit", "group", "period", "source", "description")}
            record["value"] = (sum(values) if values else None) if definition.get("sum_values") else len(rows)
            if not definition.get("sum_values"):
                inventory_credit(record, rows)
            out[definition["key"]] = record
    return out


def inventory_credit(record, rows, *, sort_periods=False):
    if not rows:
        return
    sources = list(dict.fromkeys(row.get("source") or record["source"] for row in rows))
    periods = list(dict.fromkeys(row["period"] for row in rows if row.get("period")))
    record.update(source=sources, period=" · ".join(sorted(periods) if sort_periods else periods) or record["period"],
                  estimated=any(row.get("estimated") for row in rows))


def indian_number(value):
    rounded = value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    integral, _, fraction = f"{rounded:f}".rstrip("0").partition(".")
    tail = integral[-3:]
    prefix = integral[:-3]
    while prefix:
        tail = f"{prefix[-2:]},{tail}"
        prefix = prefix[:-2]
    return f"{tail}.{fraction}" if fraction else tail


def footprint(city, profile):
    if profile.get("method") == "ghsl":
        return [row["cell"] for row in profile["cells"]]
    return city.get("footprint") or [city["cell"]]


def index_inventory(world, cities, profiles, districts, resources, wonders, infrastructure, protected, ramsar):
    city_cells = defaultdict(list)
    for city in cities:
        for cell in footprint(city, profiles.get(city["id"], {})):
            city_cells[cell].append(city["id"])

    def owner_at(cell, owners, records, key):
        if isinstance(cell, int) and 0 <= cell < len(owners) and owners[cell] >= 0:
            return records[owners[cell]][key]
        return None

    def state_at(cell):
        return owner_at(cell, world["owner"], world["states"], "abbr")

    def district_at(cell):
        return owner_at(cell, world["county"], world["counties"], "geoid")

    types = {row["id"]: row for row in resources["types"]}
    resource_items = [{**row, "meta": types[row["type"]]} if row["type"] in types else None
                      for row in resources["items"]]
    sites = {
        "protected": [row for row in protected["sites"] if not row.get("ramsar_id")] + ramsar["sites"],
        "resources": [row for row in resource_items if row is not None],
        "wonders": [row for row in wonders["wonders"] if not row.get("foreign_side")],
        **{key: infrastructure[key] for key in ("ports", "airports", "rail", "roads")},
    }
    sites["protected"] = [row for row in sites["protected"]
                          if isinstance(row.get("cell"), int) and row["cell"] >= 0]
    indexes = {level: defaultdict(lambda: defaultdict(list)) for level in ("states", "metros", "counties")}

    def add(level, keys, kind, row):
        for key in dict.fromkeys(keys):
            if key is not None:
                indexes[level][key][kind].append(row)

    for kind, rows in sites.items():
        for row in rows:
            cells = row[:2] if isinstance(row, list) else [row.get("cell")]
            state = (row.get("state_abbr") if row.get("state_source_id") else row.get("state")) if isinstance(row, dict) else None
            add("states", [state] if state else map(state_at, cells), kind, row)
            add("counties", map(district_at, cells), kind, row)
            add("metros", (city for cell in cells for city in city_cells.get(cell, ())), kind, row)

    def resource_key(row):
        return row["type"], row["name"], row["x"], row["y"]

    resource_by_key = {resource_key(row): row for row in sites["resources"]}
    wonder_by_id = {row["id"]: row for row in sites["wonders"]}
    for key, profile in profiles.items():
        if profile["method"] == "ghsl":
            place = indexes["metros"][key]
            place["resources"] = [resource_by_key[tuple(row)] for row in profile["resources"]
                                  if tuple(row) in resource_by_key]
            place["wonders"] = [wonder_by_id[row] for row in profile["wonders"] if row in wonder_by_id]
    for key, district in districts.items():
        if mapped := district.get("sites"):
            place = indexes["counties"][key]
            place["resources"] = [resource_items[i] for i in mapped["resources"] if resource_items[i] is not None]
            place["wonders"] = [wonder_by_id[row] for row in mapped["wonders"] if row in wonder_by_id]

    gateways = {level: defaultdict(set) for level in ("states", "metros")}
    if trade := infrastructure.get("trade"):
        grid = HexGrid(**world["grid"])
        corridors = set(trade["corridors"])
        for port in sites["ports"]:
            if port["category"] == "Major port":
                gateways["states"][state_at(port["cell"])].add(port["name"])
                for key in city_cells.get(port["cell"], ()):
                    gateways["metros"][key].add(port["name"])
        for name in corridors:
            for cell in infrastructure["rail_corridors"].get(name, []):
                gateways["states"][state_at(cell)].add(name)
                for nearby in [cell, *grid.neighbours(cell)]:
                    for key in city_cells.get(nearby, ()):
                        gateways["metros"][key].add(name)
        for key, profile in profiles.items():
            gateways["metros"][key].update(row["name"] for row in profile["gateways"]["rail"]
                                           if row["freight"] and row["name"] in corridors)
    return indexes, gateways
