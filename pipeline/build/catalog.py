"""sources.json – the Almanac's bibliography, generated from the registry + manifests.

Each source cites only the raw files its latest process() used (interim "files"),
or every manifest entry if it did not say.
"""

import json
from pathlib import Path

from ..core.fetch import read_manifest
from ..core.paths import WEB_DATA
from ..core.source import ODBL_URL
from ..core.store import load_interim_payload, write_web
from ..india import ESTUARY_SOURCES, FEATURED_PORT_REFERENCES, LOCAL_SOURCES, SOI_POLITICAL_MAP, TERRAIN_SOURCES
from ..india import TRANSPORT_REFERENCE_FILES, TRANSPORT_SOURCES
from ..india.city_sources import CITY_PEOPLE_SOURCES, CLUSTER_REPORTS, CLUSTER_SOURCES
from ..india.advisor_sources import SOURCES as ADVISOR_SOURCES
from ..india.civic_sources import SOURCES as CIVIC_SOURCES
from ..india.city_conditions_sources import HOUSING_INFO, HPI_PERIOD
from ..india.disaster_sources import SOURCES as DISASTER_SOURCES
from ..india.explorer_sources import SOURCES as EXPLORER_SOURCES
from ..india.city_economy_sources import SOURCES as GSVA_SOURCES
from ..india.protected_land_catalog import MANIFEST as PROTECTED_MANIFEST, PERIODS as PROTECTED_PERIODS
from ..india.wonders import CREDITS as WONDER_CREDITS, SOURCE as WONDERS_SOURCE
from ..india.wonders import LICENSE as WONDERS_LICENSE, LICENSE_URL as WONDERS_LICENSE_URL
from ..india.yield_sources import SOURCES as YIELD_SOURCES
from ..sources import SOURCES
from ..sources.resource_references import REFERENCES as RESOURCE_REFERENCES
from .city_people import REGISTRATION_METHOD
from .state_metrics import FY
from .protected_land import SOURCE as PROTECTED_SOURCE

REQUIRES = [WONDERS_SOURCE]
PRODUCES = ["sources.json"]
RUN_LAST = True

CC_BY = "https://creativecommons.org/licenses/by/4.0/"
SOI_NOTICE = ("Source: Survey of India, Government of India. Generalised to hexes. "
              "Survey of India disclaims liability for use. Refer to the original chart for authoritative boundaries.")
DOWNLOADS = {
    "open_rivers": ("world", "Download the map database with ODbL river data"),
    "pulicat": ("world", "Download the map database with the ODbL lagoon footprint"),
    "hydrolakes": ("world", "Download the map database with CC BY 4.0 lake data"),
    "wonders_osm": ("wonders", "Download the landmark database with the ODbL anchor"),
    "india_wonders": ("wonders", "Download the CC BY-SA 4.0 landmark inventory"),
    "civic_office_points": ("nation", "Download national data with ODbL civic office points"),
}
LICENCE_LINKS = {
    "cea_fy26": "https://www.cea.nic.in/websitePolicy?lang=en",
    "census_a01": "https://censusindia.gov.in/census.website/en/node/286",
    "delhi_gsdp_fy26": "https://delhiplanning.delhi.gov.in/planning/copyright-policy",
    "delhi_gsva_fy26": "https://delhiplanning.delhi.gov.in/planning/copyright-policy",
    "gem_power": "https://globalenergymonitor.org/creative-commons-license",
    "tg_projections": "https://www.nhm.gov.in/NTCP/Manuals_Guidelines/index4.php?lang=1&level=0&lid=13&linkid=8",
    "un_wup_cities": "https://creativecommons.org/licenses/by/3.0/igo/",
    "soi_outline": "https://surveyofindia.gov.in/pages/copyright-policy",
    "soi_boundary_chart": "https://www.geospatial.dst.gov.in/Guidelines.aspx",
    "soi_political_map": "https://www.geospatial.dst.gov.in/Guidelines.aspx",
    "rsis_protected": "https://www.ramsar.org/licence-information",
}


def release_credits(entry):
    source_id = entry["id"]
    if source_id in DOWNLOADS:
        name, label = DOWNLOADS[source_id]
        entry.update(download_path=f"data/{name}.json", download_label=label)
    if entry["license"].startswith(("ODbL 1.0", "Open Database Licence (ODbL) 1.0")):
        entry["license_url"] = ODBL_URL
        entry["publisher"] = f"© {entry['publisher'].removeprefix('© ')}"
    elif source_id in LICENCE_LINKS:
        entry["license_url"] = LICENCE_LINKS[source_id]
    elif entry["license"].startswith("CC BY 4.0"):
        entry.setdefault("license_url", CC_BY)
    if source_id == "soi_outline":
        entry["description"] = f"{SOI_NOTICE} {entry['description']}"
    if source_id == "gem_power":
        entry["credit_link"] = {
            "label": "TransitionZero Solar Asset Mapper licensing and credit",
            "url": "https://www.transitionzero.org/terms/tz-sam-terms-of-use",
        }
    return entry


def build() -> None:
    out = []
    for s in SOURCES:
        try:
            payload = load_interim_payload(s.id)
        except FileNotFoundError:
            payload = {}
        manifest = read_manifest(s.id)
        used = payload.get("files")  # raw files the latest process() said it used, else cite them all
        names = sorted(manifest) if used is None else [f for f in sorted(used) if f in manifest]
        if used is not None and len(names) < len(used):
            print(f"    ! {s.id}: {len(used) - len(names)} used file(s) missing from manifest")
        files = [
            {"file": name, "url": m["url"], "retrieved": m["retrieved"], "sha256": m["sha256"], "bytes": m["bytes"]}
            for name in names
            for m in [manifest[name]]
        ]
        vintage = payload.get("vintage")
        out.append({**s.info.to_dict(), "vintage": vintage, "files": files})
    protected_files = json.loads(PROTECTED_MANIFEST.read_text())
    for info in [*LOCAL_SOURCES, *CITY_PEOPLE_SOURCES]:
        files = []
        try:
            if info in GSVA_SOURCES:
                vintage = FY
            elif info in (*YIELD_SOURCES, *ADVISOR_SOURCES, *CIVIC_SOURCES, *EXPLORER_SOURCES):
                vintage = None  # The pinned edition and period are in the source description.
            elif info in TERRAIN_SOURCES:
                load_interim_payload("india_layered_terrain")
                vintage = None  # Each source description records its own time period.
            elif info.id == "delhi_gsdp_fy26":
                load_interim_payload("gsdp_fy26")
                vintage = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
            elif info.id in PROTECTED_PERIODS:
                load_interim_payload(PROTECTED_SOURCE)
                vintage = PROTECTED_PERIODS[info.id]
                files = [{"file": file, **meta} for file, meta in protected_files.items() if meta["source"] == info.id]
            else:
                vintage = load_interim_payload(info.id).get("vintage")
        except FileNotFoundError:
            continue
        out.append({**info.to_dict(), "vintage": vintage, "files": files})
    out.extend({**info.to_dict(), "vintage": None, "files": []} for info in [*ESTUARY_SOURCES, *RESOURCE_REFERENCES])
    out.extend({**info.to_dict(), "vintage": "2026", "files": []} for info in DISASTER_SOURCES)
    out.append({**HOUSING_INFO.to_dict(), "vintage": HPI_PERIOD, "files": []})
    for info in CLUSTER_SOURCES:
        out.append({**info.to_dict(), "vintage": CLUSTER_REPORTS[info.id][2], "files": [],
                    "license_url": "https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=19&reg=48"})
    next(entry for entry in out if entry["id"] == CLUSTER_SOURCES[0].id)["description"] += " " + REGISTRATION_METHOD
    try:
        wonders_vintage = load_interim_payload(WONDERS_SOURCE)["vintage"]
    except FileNotFoundError:
        pass
    else:
        for info in WONDER_CREDITS:
            entry = {**info.to_dict(), "vintage": wonders_vintage, "files": []}
            if info.license == WONDERS_LICENSE:
                entry["license_url"] = WONDERS_LICENSE_URL
            out.append(entry)
    reference = json.loads(Path(__file__).with_name("soi_conformity.json").read_text())
    files = [{
        "file": "POL_MAP_4M_ENGLISH_13thEdn2026(1).pdf",
        **{key: reference[key] for key in ("url", "retrieved", "sha256", "bytes")},
    }]
    out.append({**SOI_POLITICAL_MAP.to_dict(), "vintage": "2026", "files": files})
    transport_path = WEB_DATA / "infrastructure.json"
    transport = json.loads(transport_path.read_text()) if transport_path.exists() else None
    if transport:
        for info in TRANSPORT_SOURCES:
            if info.id in {"mopsw_coastal_cargo", "pib_dfc_completion"} and not transport.get("trade"):
                continue
            if info.id == "pib_dfc_completion":
                vintage, files = "8 September 2026", []
            elif info.id == "osm_transport":
                payload = load_interim_payload(info.id)
                vintage, files = payload["vintage"], payload["data"]["files"]
            elif info.id == "featured_port_locations":
                vintage = None
                files = [dict(file=name, url=url, retrieved="2026-11-26", sha256=sha256, bytes=size)
                         for name, url, sha256, size in FEATURED_PORT_REFERENCES]
            else:
                name, url, sha256, size = TRANSPORT_REFERENCE_FILES[info.id]
                vintage = transport["vintage"]["airports"] if info.id == "ourairports" else None
                retrieved = "2026-11-27" if info.id == "mopsw_coastal_cargo" else "2026-11-26"
                files = [dict(file=name, url=url, retrieved=retrieved, sha256=sha256, bytes=size)]
            out.append({**info.to_dict(), "vintage": vintage, "files": files})
    write_web("sources.json", [release_credits(entry) for entry in out])
