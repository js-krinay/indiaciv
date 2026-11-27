"""Pinned public map exports from Global Energy Monitor's 2026 trackers."""

import csv
import hashlib
import json
import math
from collections import defaultdict

from ..core.source import Source, SourceInfo
from ..india.transport import MILITARY_FACILITY

PUBLISHER = "Global Energy Monitor"
LICENSE = "CC BY 4.0 (https://globalenergymonitor.org/creative-commons-license)"
CDN = "https://publicgemdata.nyc3.cdn.digitaloceanspaces.com/"
# CEA status edition 055c36d3-284e-4aeb-9b29-4f310477a0eb confirms these
# operating generators lack pumping operation. Keep them in conventional hydro.
NO_PUMPING = {"L100000601895", "L100000602025"}


def parse_sites(rows, kind):
    """Sum rated operating power units by project and fuel. Mines and fields are already site rows."""
    sites = defaultdict(list)
    seen = set()
    for row in rows:
        if row["country-area1"] != "India" or row["status"] != "operating":
            continue
        if row.get("location-accuracy") == "country-level only":
            continue
        project, name = row["project-id"], row["name"]
        if any(MILITARY_FACILITY.search(row.get(key) or "") for key in ("name", "owner", "operator")):
            continue
        unit = row.get("unit-id") or project
        if not project or not name or unit in seen:
            continue
        resource = row["asset-type"] if kind == "power" else kind
        if resource == "hydropower" and row.get("tech-type") == "pumped storage" and project not in NO_PUMPING:
            resource = "pumped_storage"
        if kind == "oil":
            label = name.removesuffix(" (India)").lower()
            resource = "oil_gas"
            if label.endswith(" oil field"):
                resource = "oil"
            elif label.endswith(" gas field") and not label.endswith("oil and gas field"):
                resource = "gas"
        if resource == "oil/gas":
            fuel = row["fuel"]
            if "fossil gas:" in fuel:
                resource = "gas_plant"
            elif "fossil liquids:" in fuel:
                resource = "oil_plant"
            else:
                continue
        try:
            lat, lon = float(row["Latitude"]), float(row["Longitude"])
            value = 1 if kind == "oil" else float(row["capacity"])
        except (ValueError, TypeError):
            continue
        if not (0 < lat <= 90 and 0 < lon <= 180 and math.isfinite(value) and value > 0):
            continue
        if kind == "iron":
            value /= 1000  # thousand tonnes per year → million tonnes per year
        seen.add(unit)
        sites[project, resource].append((value, name.removesuffix(" (India)"), lat, lon,
                                         row.get("location-accuracy") or ""))
    return [
        {"type": resource, "name": name, "lat": lat, "lon": lon, "location_accuracy": accuracy or None,
         "value": round(sum(u[0] for u in units), 6)}
        for (_, resource), units in sites.items()
        for _, name, lat, lon, accuracy in [max(units)]
    ]


class GemExport(Source):
    def fetch(self, force=False):
        self.download(CDN + self.path, self.path.rsplit("/", 1)[-1], force=force)

    def process(self):
        filename = self.path.rsplit("/", 1)[-1]
        path = self.raw_dir / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != self.checksum:
            raise ValueError(f"{self.id}: unexpected SHA-256 for {filename}")
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = csv.DictReader(f) if self.kind == "power" else (
                feature["properties"] for feature in json.load(f)["features"]
            )
            sites = parse_sites(rows, self.kind)
        return {"sites": sites, "vintage": self.vintage, "technology_version": 2, "_files": [filename]}


class GemPower(GemExport):
    kind = "power"
    vintage = "September 2026"
    path = "Current_maps/integrated-power/2026-09/integrated_map_2026-09.csv"
    checksum = "19018cdc52b3e7f61b563c3c91aec664a7eacbf18d738e867bbcba7d4b4418c0"
    info = SourceInfo(
        "gem_power", "Global Integrated Power Tracker", PUBLISHER,
        "https://globalenergymonitor.org/projects/global-integrated-power-tracker",
        LICENSE + ". Some solar records come from TransitionZero’s Solar Asset Mapper (CC BY-NC 4.0). "
        "IndiaCiv is a non-commercial site and applies the NC terms to all solar records in the map export.",
        "Operating generating units in the September 2026 map export. Rated MW are summed by plant and technology. "
        "Pumped storage uses the unit technology and the CEA pumping-status cross-check.",
        ["Power resources"],
    )


class GemCoal(GemExport):
    kind = "coal_mine"
    vintage = "August 2026"
    path = "Current_maps/gcmt-smp/gcmt-smp_map_2026-08.geojson"
    checksum = "56679de78a7405a513b13b364486bcd44b7bc63cc89c5f21ffb892b4fdaf7958"
    info = SourceInfo(
        "gem_coal", "Global Coal Mine Tracker", PUBLISHER,
        "https://globalenergymonitor.org/projects/global-coal-mine-tracker", LICENSE,
        "Operating coal mine locations and capacity in the August 2026 map export.",
        ["Coal mine resources"],
    )


class GemIron(GemExport):
    kind = "iron"
    vintage = "September 2026 (V1)"
    path = "Current_maps/giomt/giomt_map_2026-09.geojson"
    checksum = "3765ece79f10d73f15d58ba16431117748a343a96d1c34a00e54f4d27a395bc3"
    info = SourceInfo(
        "gem_iron", "Global Iron Ore Mines Tracker", PUBLISHER,
        "https://globalenergymonitor.org/projects/global-iron-ore-mines-tracker", LICENSE,
        "Operating iron ore mine locations and design capacity in the September 2026 map export.",
        ["Iron ore mine resources"],
    )


class GemOilGas(GemExport):
    kind = "oil"
    vintage = "March 2026"
    path = "interim_maps/goget_map_2026-03.geojson"
    checksum = "a91682aff0a60cc143d09c7f6c0c4d8236af6c523e1330ccf5a9329e531261f7"
    info = SourceInfo(
        "gem_oil_gas", "Global Oil and Gas Extraction Tracker", PUBLISHER,
        "https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker", LICENSE,
        "Oil and gas field locations and operating status in the March 2026 map export.",
        ["Oil and gas field resources"],
    )
