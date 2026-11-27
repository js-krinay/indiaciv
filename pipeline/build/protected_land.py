"""Serve the registered protected-land inventory and independently licensed spatial data."""

import json
import re
from math import isfinite

from ..core.paths import WEB_DATA
from ..core.store import load_interim, write_web
from .city_view import grid_fingerprint

SOURCE = "protected_land"
REQUIRES = ["world.json", SOURCE]
PRODUCES = ["protected_land.json", "protected_ramsar.json"]
MILITARY_NAME = re.compile(r"\b(?:air (?:force |naval )?base|air force station|naval (?:base|station)|"
                           r"military (?:base|installation|range|station)|restricted (?:area|zone))\b", re.I)


def qualifying_cells(intersections, hex_area):
    return sorted(cell for cell, area in intersections if area / hex_area >= 0.3 - 1e-12)


def official_area_matches(mapped_km2, official_km2):
    return official_km2 > 0 and 0.75 * official_km2 <= mapped_km2 <= 1.25 * official_km2


def polygon_candidate(designation, tags):
    name = " ".join(tags.get(key, "") for key in ("name", "name:en", "designation")).casefold()
    if re.search(r"\b(core|buffer|corridor|proposed|esz)\b", name):
        return False
    boundary = tags.get("boundary")
    if not (boundary in {"national_park", "protected_area"} or tags.get("leisure") == "nature_reserve"):
        return False
    if designation == "national_park":
        return boundary == "national_park" or "national park" in name
    if designation == "tiger_reserve":
        return "tiger reserve" in name and not re.search(r"national park|wls|wildlife sanctuary", name)
    return designation == "ramsar" and "ramsar" in name


def civilian_site(tags):
    return ("military" not in tags and tags.get("landuse") != "military"
            and not any(MILITARY_NAME.search(tags.get(key, "")) for key in ("name", "name:en", "official_name")))


def site_metadata(site):
    if site.get("ramsar_id"):
        return site
    prefix = site["id"].split("-", 1)[0]
    source, period, authority, status = {
        "rsis": ("rsis_protected", "October 2026", "Ramsar Sites Information Service", "Designated Ramsar site"),
        "wii": ("wii_protected", "November 2026", "Wildlife Institute of India", "Notified national park"),
        "ntca": ("ntca_protected", "November 2026", "National Tiger Conservation Authority", "Notified tiger reserve"),
    }[prefix]
    return dict(site, authority_source=source, authority=authority, period=period, status=status, estimated=False)


def build():
    from ..core.source import osm_notice

    try:
        prepared = load_interim(SOURCE)
    except FileNotFoundError:
        prepared = {}
    if prepared and prepared["grid"] != grid_fingerprint(json.loads((WEB_DATA / "world.json").read_text())):
        raise ValueError("Reprepare protected land for the current grid (see README).")
    write_web("protected_land.json", {
        **prepared.get("osm", {}),
        "sites": [site_metadata(site) for site in prepared.get("osm", {}).get("sites", [])],
        "osm_license": osm_notice("OSM-derived site boundaries and locations, and mapped protection shares"),
    })
    write_web("protected_ramsar.json", {
        **prepared.get("ramsar", {}),
        "sites": [site_metadata(site) for site in prepared.get("ramsar", {}).get("sites", [])],
        "attribution": "Secretariat of the Convention on Wetlands (RSIS)",
        "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
    })


def check(web_dir):
    paths = [web_dir / name for name in PRODUCES]
    if not all(path.exists() for path in paths):
        return []
    osm, ramsar = [json.loads(path.read_text()) for path in paths]
    sites = osm["sites"] + ramsar["sites"]
    if not sites:
        return [("NOTE", "optional protection inputs are absent")]
    world = json.loads((web_dir / "world.json").read_text())
    size = world["grid"]["cols"] * world["grid"]["rows"]
    wonder_path = web_dir / "wonders.json"
    wonder_ids = {w["id"] for w in json.loads(wonder_path.read_text())["wonders"]} if wonder_path.exists() else None
    ramsar_ids = {site["id"] for site in ramsar["sites"]}
    ids = [site["id"] for site in sites]
    if len(set(ids)) != len(ids):
        return [("FAIL", "duplicate protected site IDs")]
    for site in sites:
        if not civilian_site({"name": site["name"]}):
            return [("FAIL", f"operational military detail in protected site {site['id']}")]
        cells = site["cells"] or []
        if cells != sorted(set(cells)) or any(not (type(i) is int and 0 <= i < size) for i in cells):
            return [("FAIL", f"invalid protected cells on {site['id']}")]
        x, y, cell = (site[key] for key in ("x", "y", "cell"))
        if (x, y, cell) != (None, None, None) and not (type(cell) is int and 0 <= cell < size
                and all(isinstance(n, (int, float)) and isfinite(n) for n in (x, y))):
            return [("FAIL", f"invalid protected location on {site['id']}")]
        if site.get("ramsar_id") and site["ramsar_id"] not in ramsar_ids:
            return [("FAIL", f"unlinked Ramsar geometry on {site['id']}")]
        if wonder_ids is not None and site["wonder"] and site["wonder"] not in wonder_ids:
            return [("FAIL", f"unknown associated wonder on {site['id']}")]
    for group, key in (("states", "abbr"), ("counties", "geoid")):
        shares = osm["shares"][group]
        if set(shares) != {row[key] for row in world[group]} or any(
            share is not None and not 0 <= share <= 1 for share in shares.values()
        ):
            return [("FAIL", f"invalid protected shares for {group}")]
    return [("PASS", f"{len(sites)} registered protected sites and valid regional shares")]
