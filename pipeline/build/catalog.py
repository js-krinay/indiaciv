"""sources.json – the Almanac's bibliography, generated from the registry + manifests.

Each source cites only the raw files its latest process() used (interim "files"),
or every manifest entry if it did not say.
"""

import json
import math
from decimal import Decimal
from pathlib import Path

from ..core.fetch import read_manifest
from ..core.paths import WEB_DATA
from ..core.source import ODBL_URL
from ..core.store import load_interim_payload, write_web
from ..india import ESTUARY_SOURCES, FEATURED_PORT_REFERENCES, LOCAL_SOURCES, SOI_POLITICAL_MAP, TERRAIN_SOURCES
from ..india import TRANSPORT_REFERENCE_FILES, TRANSPORT_SOURCES
from ..india.city_sources import (ANNUAL_LABOUR_INFO, ANNUAL_LABOUR_PERIOD, CITY_PEOPLE_SOURCES, CLUSTER_REPORTS,
                                  CLUSTER_SOURCES, GOVERNMENT_SITE_INFO)
from ..india.advisor_sources import OLDER_REGISTRATIONS, OLDER_REGISTRATION_PERIOD, SOURCES as ADVISOR_SOURCES
from ..india.census_work_sources import INTERIM as CENSUS_WORK
from ..india.census_work_sources import SOURCES as WORK_SOURCES, workbook_manifest as work_manifest
from ..india.civic_sources import SOURCES as CIVIC_SOURCES
from ..india.census_civic_sources import INTERIM as CENSUS_CIVIC, PERIOD as CENSUS_PERIOD
from ..india.census_civic_sources import SOURCES as CENSUS_SOURCES, TENURE_PERIOD, workbook_manifest
from ..india.city_conditions_sources import HOUSING_INFO, HPI_PERIOD
from ..india.disaster_sources import SOURCES as DISASTER_SOURCES
from ..india.explorer_sources import SOURCES as EXPLORER_SOURCES
from ..india.household_cost_sources import INTERIM as HOUSEHOLD_COSTS, PERIODS as HOUSEHOLD_PERIODS
from ..india.household_cost_sources import (DISTRICT_HEALTH, DISTRICT_INTERIM, DISTRICT_MPI, DISTRICT_TAPS,
                                           PILOT, PILOT_INTERIM, REPORTS as HOUSEHOLD_REPORTS)
from ..india.military_sources import SOURCES as MILITARY_SOURCES, STRENGTH, STRENGTH_SOURCE
from ..india.city_economy_sources import SOURCES as GSVA_SOURCES
from ..india.city_economy_sources import HISTORICAL_DETAIL_PERIODS
from ..india.protected_land_catalog import MANIFEST as PROTECTED_MANIFEST, PERIODS as PROTECTED_PERIODS
from ..india.wonders import CREDITS as WONDER_CREDITS, SOURCE as WONDERS_SOURCE
from ..india.wonders import LICENSE as WONDERS_LICENSE, LICENSE_URL as WONDERS_LICENSE_URL
from ..india.yield_sources import SOURCES as YIELD_SOURCES
from ..india.historical_sources import WORKPLACE_LICENSE_URL, WORKPLACE_SOURCE
from ..india.historical_sources import PORT_PERIOD, PORT_SHA256, PORT_SOURCE, PORT_URL
from ..india.historical_sources import VILLAGE_LAND_PERIOD, VILLAGE_LAND_SOURCE
from ..sources import SOURCES
from ..sources.resource_references import REFERENCES as RESOURCE_REFERENCES
from .city_people import REGISTRATION_METHOD
from .districts import COMMERCIAL_API, COMMERCIAL_INFO, COMMERCIAL_SHA256, LAND_USE_PERIOD
from .districts import NIRF_INFO, NIRF_PERIOD, NIRF_SHA256
from .advisor_inventory import indian_number
from .state_metrics import FY
from .protected_land import SOURCE as PROTECTED_SOURCE

REQUIRES = [WONDERS_SOURCE, HOUSEHOLD_COSTS, "nation.json", "infrastructure.json", "wonders.json"]
OPTIONAL_REQUIRES = [VILLAGE_LAND_SOURCE, DISTRICT_INTERIM, DISTRICT_TAPS]
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
        entry["description"] += " The vintage of the TransitionZero contribution is unresolved."
        entry["credit_link"] = {
            "label": "TransitionZero Solar Asset Mapper licensing and credit",
            "url": "https://www.transitionzero.org/terms/tz-sam-terms-of-use",
        }
        entry["credit_links"] = [
            entry["credit_link"],
            {"label": "CC BY-NC 4.0 licence deed", "url": "https://creativecommons.org/licenses/by-nc/4.0/"},
        ]
    return entry


def advisor_notes(statistics):
    notes = {}
    if budget := statistics.get("defence_budget"):
        heads = ", ".join(f"{name} ₹{amount:.2f} crore" for name, amount in budget["heads"].items())
        note = f"Union Budget Estimate for {budget['period']} by head: {heads}."
        if per_resident := statistics.get("defence_budget_per_resident"):
            note += (f" IndiaCiv estimate of ₹{per_resident['value']:,.0f} per resident, using population "
                     f"projected for {per_resident['denominator_period']}.")
        notes[budget["source"]] = note
    if schools := statistics.get("sainik_schools"):
        notes[schools["source"]] = (
            f"{schools['value']} affiliated and operational new partnership schools, {schools['period']}."
        )
    if boards := statistics.get("cantonment_boards"):
        notes["cantonment_boards"] = f"{boards} public civic boards listed in the directory checked 27 Nov 2026."
    if offices := statistics.get("civic_offices"):
        names = ", ".join(office["name"] for office in offices)
        notes["civic_office_points"] = f"Selected public offices checked 27 Nov 2026: {names}."
    if poverty := statistics.get("poverty_nowcast"):
        notes[poverty["source"]] = (
            f"India poverty nowcast: {poverty['value']:.3%} at {poverty['line']}, "
            f"calendar {poverty['period']}, {poverty['vintage']} edition."
        )
    if cards := statistics.get("pmjay_cards"):
        lower_bound = math.floor(cards["value"] * 10) / 10
        notes[cards["source"][0]] = (
            f"IndiaCiv estimate of at least {lower_bound:.1f} cards per 100 residents, cumulative to "
            f"{cards['period']}, using population projected for {cards['denominator_period']}."
        )
    if industry := statistics.get("industry"):
        agriculture, industry_share, services = industry
        notes["plfs_2026_q3"] = (
            f"India, 1 Jul – 30 Sep 2026, rural and urban workers aged 15+: agriculture {agriculture:g}%, "
            f"industry {industry_share:g}%, services {services:g}%. Shares use published rounding."
        )
    return notes


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
    census_files = workbook_manifest()
    for info in [*LOCAL_SOURCES, *CITY_PEOPLE_SOURCES]:
        files = []
        try:
            if info.id in HOUSEHOLD_PERIODS:
                intermediate = {PILOT: PILOT_INTERIM, DISTRICT_HEALTH: DISTRICT_INTERIM,
                                DISTRICT_MPI: DISTRICT_INTERIM, DISTRICT_TAPS: DISTRICT_TAPS}
                load_interim_payload(intermediate.get(info.id, HOUSEHOLD_COSTS))
                filename, checksum, size = HOUSEHOLD_REPORTS[info.id]
                files = [{"file": filename, "sha256": checksum, "url": info.homepage,
                          "retrieved": "2026-11-27", "bytes": size}]
                out.append({**info.to_dict(), "vintage": None if info.id == DISTRICT_TAPS else "older",
                            "period": HOUSEHOLD_PERIODS[info.id],
                            "files": files})
                continue
            elif info.id == VILLAGE_LAND_SOURCE:
                load_interim_payload(VILLAGE_LAND_SOURCE)
                out.append({**info.to_dict(), "vintage": "older", "period": VILLAGE_LAND_PERIOD, "files": files})
                continue
            elif info.id in HISTORICAL_DETAIL_PERIODS:
                out.append({**info.to_dict(), "vintage": "older",
                            "period": HISTORICAL_DETAIL_PERIODS[info.id], "files": files})
                continue
            elif info in GSVA_SOURCES:
                vintage = FY
            elif info == GOVERNMENT_SITE_INFO:
                vintage = "November 2026"
            elif info == ANNUAL_LABOUR_INFO:
                load_interim_payload(info.id)
                out.append({**info.to_dict(), "vintage": "older", "period": ANNUAL_LABOUR_PERIOD, "files": files})
                continue
            elif info in CENSUS_SOURCES:
                load_interim_payload(CENSUS_CIVIC)
                period = TENURE_PERIOD if info.id == "orgi_civic_tenure" else CENSUS_PERIOD
                files = [{"file": name, "sha256": checksum, "url": url, "bytes": size,
                          "retrieved": "2026-11-27"} for series, _, name, checksum, url, size in census_files
                         if info.id == f"orgi_civic_{series}"]
                out.append({**info.to_dict(), "vintage": "older", "period": period, "files": files})
                continue
            elif info in WORK_SOURCES:
                load_interim_payload(CENSUS_WORK)
                kinds = {"industry"} if info.id == "orgi_work_industries" else {"main", "marginal"}
                files = [{"file": name, "sha256": checksum, "url": url, "bytes": size,
                          "retrieved": "2026-11-27"} for kind, _, name, checksum, url, size in work_manifest()
                         if kind in kinds]
                out.append({**info.to_dict(), "vintage": "older", "period": CENSUS_PERIOD, "files": files})
                continue
            elif info in (*YIELD_SOURCES, *ADVISOR_SOURCES, *CIVIC_SOURCES, *EXPLORER_SOURCES, *MILITARY_SOURCES):
                vintage = None  # The pinned edition and period are in the source description.
            elif info in TERRAIN_SOURCES:
                load_interim_payload("india_layered_terrain")
                vintage = None  # Each source description records its own time period.
            elif info.id == "delhi_gsdp_fy26":
                load_interim_payload("gsdp_fy26")
                vintage = "FY 2025-26 (1 Apr 2025 – 31 Mar 2026)"
            elif info.id == PORT_SOURCE:
                vintage = PORT_PERIOD
                files = [dict(file="Basic Port Statistics of India 2024-25.pdf", url=PORT_URL,
                              sha256=PORT_SHA256, bytes=2_469_332, retrieved="2026-11-27")]
            elif info.id == "census_2011_ua_keys":
                load_interim_payload(WORKPLACE_SOURCE)
                vintage = "Census 2011"
            elif info.id in PROTECTED_PERIODS:
                load_interim_payload(PROTECTED_SOURCE)
                vintage = PROTECTED_PERIODS[info.id]
                files = [{"file": file, **meta} for file, meta in protected_files.items() if meta["source"] == info.id]
            else:
                vintage = load_interim_payload(info.id).get("vintage")
        except FileNotFoundError:
            continue
        extra = {}
        if info.id == WORKPLACE_SOURCE:
            coverage = load_interim_payload(WORKPLACE_SOURCE)["data"]
            extra = {"license_url": WORKPLACE_LICENSE_URL, "description": (
                f"SHRIC 72 includes defence and civilian activity. Its exclusion removes "
                f"{coverage['excluded_jobs']:,} India jobs ({1 - coverage['civilian_coverage']:.2%}), "
                f"leaving {coverage['national']['jobs']:,} ({coverage['civilian_coverage']:.2%}). "
                "The publisher’s harmonised manufacturing total includes the whole group, so the same "
                f"subtraction applies before dividing by civilian jobs. {info.description}"
            )}
        out.append({**info.to_dict(), "vintage": vintage, "files": files, **extra})
    out.extend({**info.to_dict(), "vintage": None, "files": []} for info in [*ESTUARY_SOURCES, *RESOURCE_REFERENCES])
    out.extend({**info.to_dict(), "vintage": "2026", "files": []} for info in DISASTER_SOURCES)
    out.append({**HOUSING_INFO.to_dict(), "vintage": HPI_PERIOD, "files": []})
    out.append({**NIRF_INFO.to_dict(), "vintage": "older", "period": NIRF_PERIOD, "files": [
        {"file": "SDG.pdf", "url": NIRF_INFO.homepage, "sha256": NIRF_SHA256, "bytes": 11_006,
         "retrieved": "2026-11-28"},
    ]})
    out.append({**COMMERCIAL_INFO.to_dict(), "vintage": LAND_USE_PERIOD, "files": [
        {"file": "126018393.json", "url": COMMERCIAL_API, "sha256": COMMERCIAL_SHA256, "bytes": 2_588,
         "retrieved": "2026-11-28"},
    ]})
    for info in CLUSTER_SOURCES:
        out.append({**info.to_dict(), "vintage": CLUSTER_REPORTS[info.id][2], "files": []})
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
            elif info.id == "aai_vejh_20260806":
                vintage, files = "6 August 2026", []
            elif info.id == "adani_port_addresses_fy25":
                vintage, files = "FY 2024-25 annual report", []
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
    nation_path = WEB_DATA / "nation.json"
    nation = json.loads(nation_path.read_text()) if nation_path.exists() else {}
    notes = advisor_notes(nation.get("advisor_statistics", {}))
    from ..core.source import SourceInfo
    from .disasters import COLD_PERIOD, COLD_SOURCE, DROUGHT_PERIOD, DROUGHT_SOURCE, FIRE_PERIOD, FIRE_SOURCE
    from .wonders import FAITH_SOURCE, NIRF_SOURCE, PARK_VISIT_PERIOD, PARK_VISIT_SOURCE

    place_sources = (
        (SourceInfo(COLD_SOURCE, "Delhi monthly weather report, January 2026", "India Meteorological Department",
                    "https://mausam.imd.gov.in/newdelhi/archive/2026-02-03/press_release_en.pdf",
                    "Credited individual public observations. Report text and charts are not reproduced.",
                    "3 February 2026 edition, Significant Weather Observations, reporting days with cold-wave conditions.",
                    ["Hazards"]), COLD_PERIOD,
         ("Delhi January 2026 weather report.pdf", 1_234_179,
          "331e43899548f3e6cb6fdc06b016b6028eb2754630d7f87e42cffecf7771f828")),
        (SourceInfo(DROUGHT_SOURCE, "Kharif drought Notification II", "Karnataka Revenue Department",
                    "https://slbckarnataka.com/UserFiles/slbc/23%20taluks%20Kharif%202026%20Notification%20%281%29.pdf",
                    "Credited derived district counts only. No annex table or boundary redistribution.",
                    "Order RD 586 TNR 2026 (Part-1), 17 September 2026. Count distinct annex taluks by their named districts.",
                    ["Hazards"]), DROUGHT_PERIOD,
         ("Kharif 2026 Notification II.pdf", 1_503_937,
          "13357a5344f3465c16d7159157284bdd6e1e0e8fdf6a56405eb497edcaf4a4c7")),
        (SourceInfo(FIRE_SOURCE, "India State of Forest Report 2023, volume I", "Forest Survey of India",
                    "https://fsi.nic.in/uploads/isfr2023/isfr_book_eng-vol-1_2023.pdf",
                    "Credited derived shares only. No source table redistribution.",
                    "Tables 4.4 and 4.6. Divide each matched district count by the same-season national SNPP-VIIRS total.",
                    ["Hazards"]), FIRE_PERIOD,
         ("India State of Forest Report 2023 volume I.pdf", 20_145_512,
          "09a76c890e42aabdd7607ea62b7cef523c3a1b16a76b226502a0e7918bc1a78f")),
        (SourceInfo(PARK_VISIT_SOURCE, "Kaziranga October attendance bulletin", "Akashvani",
                    "https://newsonair.gov.in/as/২০২৬-২৭-পৰ্যটন-বৰ্ষৰ-প্ৰথ/",
                    "Credited individual reported fact. No bulletin redistribution.",
                    "3 November 2026 Assamese bulletin, first month of the 2026–27 visitor season. October lower bound only.",
                    ["Wonders", "Culture"]), PARK_VISIT_PERIOD,
         ("Akashvani 3 November 2026 bulletin.html", 74_951,
          "8cd52d0d2709f38ea5de46d66d7320a7cf6847ddebaece40ee7aa85b6f44d2f4")),
        (SourceInfo(NIRF_SOURCE, "NIT Rourkela India Rankings 2025 submission", "Ministry of Education / NIT Rourkela",
                    "https://www.nirfindia.org/nirfpdfcdn/2025/pdf/SDGInstitutions/IR-B-U-0357.pdf",
                    "Credited derived measure using public institutional facts.",
                    "Submission IR-B-U-0357, sponsored research section. Divide receipts by project count for FY 2023-24.",
                    ["Wonders"]), "FY 2023-24 (1 Apr 2023 – 31 Mar 2024)", None),
        (SourceInfo(FAITH_SOURCE, "C-01 population by religious community, India", "Registrar General and Census Commissioner",
                    "https://censusindia.gov.in/nada/index.php/catalog/11361/download/14474/DDW00C-01%20MDDS.XLS",
                    "Credited derived shares from Census 2011. No source workbook redistribution.",
                    "PC11_C01-00 national Total/Persons row, with religion not stated included in the denominator.",
                    ["Culture"]), "Census 2011",
         ("DDW00C-01 MDDS.XLS", 52_736, "c3fee2bb235f4ef511d9aaeceaf5f8026b48908f813c6d1cc06413a6c8a0d9cd")),
    )
    for info, period, snapshot in place_sources:
        files = []
        if snapshot:
            filename, size, checksum = snapshot
            files.append(dict(file=filename, bytes=size, sha256=checksum, url=info.homepage, retrieved="2026-11-28"))
        older = info.id in {FIRE_SOURCE, NIRF_SOURCE, FAITH_SOURCE}
        out.append({**info.to_dict(), "period": period, "vintage": "older" if older else period, "files": files})

    from .military import public_designation

    for entry in out:
        source = entry["id"]
        if source == "cantonment_boards" or source.startswith("command_hq_"):
            entry["marker_designation"] = public_designation(source)

    older_counts = ", ".join(f"{name} {indian_number(Decimal(OLDER_REGISTRATIONS[code]))}"
                             for code, name in (("MN", "Manipur"), ("PB", "Punjab")))
    notes["registered_veterans_pib"] = f"Reported registrations as of {OLDER_REGISTRATION_PERIOD}: {older_counts}."
    notes[STRENGTH_SOURCE] = " ".join(
        f"{label} ({period}) had {indian_number(Decimal(value))} personnel. {description}"
        for value, label, period, description in STRENGTH.values())
    if freight := (transport or {}).get("freight"):
        zones = ", ".join(f"{label} {value:g}" for _, label, value in freight["rows"])
        notes[freight["source_id"]] = (
            f"Originating rail freight loading by zone, {freight['label']} ({freight['unit']}): {zones}."
        )
    if direction := (transport or {}).get("overseas_direction_by_state", {}).get("India"):
        notes[direction["source_id"]] = (
            f"India overseas port cargo, {direction['period']}: {direction['unloaded']:.1%} unloaded, "
            f"{direction['loaded']:.1%} loaded."
        )
    for entry in out:
        if note := notes.get(entry["id"]):
            entry["description"] += " " + note
    write_web("sources.json", [release_credits(entry) for entry in out])
