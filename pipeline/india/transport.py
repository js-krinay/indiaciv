"""Prepare transport geometry from the pinned OSM and OurAirports snapshots."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from . import TRANSPORT_REFERENCE_FILES
from .transport_corridors import RailTopology, source_connections
from ..core.store import save_interim

AIRPORT_DATE = "26 November 2026"
NATIONAL_REF = re.compile(r"(?:^|[;,/ ])N[HE][ -]?\d", re.IGNORECASE)
NETWORK_DATE = date(2026, 11, 26)
LIFECYCLE_PREFIXES = ("construction", "proposed", "disused", "abandoned")
MILITARY_FACILITY = re.compile(
    r"\b(?:armed forces|air[\s_-]*force|air[\s_-]*base|afs|iaf|ins|naval|navy|army|"
    r"military|cantonment|defen[cs]e (?:base|airfield|facility))\b", re.IGNORECASE
)

# OurAirports identifiers matched to standalone civilian airports in AAI's
# 16 Jan 2026 operational inventory. Civil enclaves are outside this subset.
CIVIL_IATA = frozenset("""
    AGX AMD AYJ BBI BDQ BHO BHU BLR BOM CCJ CCU CDP CJB CNN COK DED DEL DGH
    DIB DMU GAU GAY GBI GDB GOX HBX HGI HJR HSR HYD IDR IMF IXA IXE IXG IXI
    IXK IXM IXR IXY JAI JLG JLR JRG KJB KLH KQH KUU LKO MAA MYQ
    PAT PGH PNY RJA RPR SAG SHL STV TCR TIR TRV TRZ UDR VGA VNS
""".split())


def is_civil_airport(row):
    return row.get("iata") in CIVIL_IATA and not any(
        MILITARY_FACILITY.search((row.get(key) or "").replace("_", " "))
        for key in ("name", "keywords", "type")
    )


def public_label(value):
    return value.strip() if value and value.strip() and not MILITARY_FACILITY.search(value) else None


def military_transport_tags(tags):
    return (tags.get("military") not in (None, "no")
            or any(MILITARY_FACILITY.search(tags.get(key, ""))
                   for key in ("name", "name:en", "usage", "operator", "seamark:harbour:category")))


def unresolved_lifecycle(tags):
    if not any(key.startswith(LIFECYCLE_PREFIXES) for key in tags):
        return False
    status_key = "railway:status" if tags.get("railway") == "rail" else "highway:status"
    if tags.get(status_key, "").lower() in {"open", "operating", "operational", "active", "in_service"}:
        return False
    try:
        return date.fromisoformat(tags.get("opening_date", "")) >= NETWORK_DATE
    except ValueError:
        return True


def line_class(tags):
    if unresolved_lifecycle(tags) or military_transport_tags(tags):
        return None
    if tags.get("railway") == "rail" and not tags.get("service"):
        if tags.get("usage") not in {"industrial", "military", "tourism", "test", "education",
                                     "siding", "yard", "spur", "crossover"}:
            return "rail", 0 if tags.get("usage") == "main" else 1
    if tags.get("access") in {"no", "private"}:
        return None
    if tags.get("highway") == "motorway":
        return "roads", 0
    if tags.get("highway") == "trunk" and NATIONAL_REF.search(tags.get("ref", "")):
        return "roads", 1
    return None


def verify(path, expected):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"{path}: expected SHA-256 {expected}, got {actual}")


def port_name(tags):
    if military_transport_tags(tags) or tags.get("access") in {"private", "no"}:
        return None
    if tags.get("landuse") == "construction" or any(
            tags.get(key) == "yes" for key in ("disused", "abandoned", "construction", "proposed")):
        return None
    harbour_class = tags.get("seamark:harbour:category", "")
    if tags.get("port:type") == "dryport" or tags.get("leisure") == "marina" or "marina" in harbour_class:
        return None
    if (tags.get("industrial") == "port" or tags.get("harbour") in {"yes", "commercial"}
            or tags.get("seamark:type") == "harbour"):
        name = tags.get("name:en") or tags.get("name")
        if name and not re.search(r"\b(?:terminal|ferry|ghat|shipyards?|fishing)\b", name, re.IGNORECASE):
            return name
    return None


def rail_facility(tags):
    """Preserve identifiable freight tracks and the Chenab crossing through simplification."""
    name = tags.get("name", "").casefold()
    ref = tags.get("ref", "").upper()
    if ref == "WDFC" or "western dedicated freight corridor" in name:
        return "WDFC"
    if ref == "EDFC" or "eastern dedicated freight corridor" in name:
        return "EDFC"
    if tags.get("bridge") not in {None, "no"} and "chenab bridge" in name:
        return "Chenab"
    return None


def feature_points(feature):
    if feature["type"] == "relation":
        return [point for member in feature["members"] if member["role"] != "inner"
                for point in feature_points(member)]
    if feature["type"] == "node":
        return [(feature["lon"], feature["lat"])] if "lon" in feature else []
    return [(point["lon"], point["lat"]) for point in feature.get("geometry", []) if point]


def prepare_osm(manifest_path, directory):
    manifest = json.loads(manifest_path.read_text())
    if not manifest["responses"]:
        raise ValueError("The Overpass manifest has no pinned regions")
    seen = set()
    lines, ports = [], []
    rail_nodes = Counter()
    node_points = {}
    topologies = {kind: RailTopology() for kind in ("rail", "EDFC", "WDFC")}
    files = []
    lifecycle_audit = {"excluded": 0, "admitted_unresolved_way_ids": []}
    for region in manifest["responses"]:
        path = directory / region["file"]
        verify(path, region["sha256"])
        response = json.loads(path.read_text())
        stamp = response["osm3s"]["timestamp_osm_base"]
        if response.get("remark") or stamp != region["timestamp"]:
            raise ValueError(f"Incomplete Overpass response or mismatched timestamp: {path}")
        files.append(dict(file=path.name, url=region["endpoint"] + "?" + urlencode({"data": region["query"]}),
                          retrieved=region["retrieved"], sha256=region["sha256"], bytes=path.stat().st_size,
                          query=region["query"], timestamp=stamp))
        for feature in response["elements"]:
            key = feature["type"], feature["id"]
            if key in seen:
                continue
            seen.add(key)
            tags = feature.get("tags", {})
            name = port_name(tags)
            classification = line_class(tags) if key[0] == "way" else None
            if key[0] == "way" and (tags.get("railway") == "rail" or tags.get("highway") in {"motorway", "trunk"}):
                if unresolved_lifecycle(tags):
                    if classification:
                        lifecycle_audit["admitted_unresolved_way_ids"].append(key[1])
                    else:
                        lifecycle_audit["excluded"] += 1
            if not (name or classification):
                continue
            coords = feature_points(feature)
            if not coords:
                continue
            if name:
                lon, lat = (sum(axis) / len(coords) for axis in zip(*coords))
                ports.append([f"{key[0][0]}{key[1]}", name, lon, lat])
            if classification:
                kind, tier = classification
                facility = rail_facility(tags) if kind == "rail" else None
                if facility in {"EDFC", "WDFC", "Chenab"}:
                    tier = 0
                name = tags.get("name:en") or tags.get("name")
                lines.append([kind, tier, tags.get("ref"), coords, facility, name, tags.get("network")])
                if kind == "rail":
                    nodes = feature["nodes"]
                    rail_nodes.update(set(nodes))
                    node_points.update(zip(nodes, coords, strict=True))
                    topologies["rail"].add(key[1], nodes)
                    if facility in {"EDFC", "WDFC"}:
                        topologies[facility].add(key[1], nodes)
    junctions = [node_points[node] for node, count in rail_nodes.items() if count > 1]
    save_interim("osm_transport", dict(lines=lines, ports=ports, junctions=junctions, files=files,
                                       lifecycle_audit=lifecycle_audit,
                                       source_connections=source_connections(topologies, node_points)),
                 vintage=manifest["vintage"])
    print(f"Prepared {len(lines):,} ways and {len(ports):,} port candidates")


def airport_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["iso_country"] == "IN" and row["type"] in {"large_airport", "medium_airport", "small_airport"}:
                civil = {**row, "iata": row["iata_code"]}
                if is_civil_airport(civil) and (row["scheduled_service"] == "yes" or row["type"] == "large_airport"):
                    yield dict(id=row["id"], name=row["name"], iata=row["iata_code"] or None,
                               scheduled_service=row["scheduled_service"] == "yes",
                               civil_verified=True,
                               city=public_label(row.get("municipality")),
                               size=row["type"].split("_")[0], lon=float(row["longitude_deg"]),
                               lat=float(row["latitude_deg"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("airports", type=Path)
    parser.add_argument("--overpass-dir", type=Path)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("transport_overpass.json"))
    args = parser.parse_args()
    verify(args.airports, TRANSPORT_REFERENCE_FILES["ourairports"][2])
    save_interim("ourairports", dict(airports=list(airport_rows(args.airports))), vintage=AIRPORT_DATE)
    if args.overpass_dir:
        prepare_osm(args.manifest, args.overpass_dir)


if __name__ == "__main__":
    main()
