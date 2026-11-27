"""Checksum-pinned WorldPop R2025A v1 age estimates for Goa and five union territories."""

import hashlib
import json

from ..core.source import Source, SourceInfo

SOURCE_ID = "worldpop_age"
URL = "https://api.worldpop.org/v3/countries/IND/units?year=2026&include=agesex"
FILENAME = "ind-agesex-2026.json"
SHA256 = "86557b7e6f1cd47584ad6a5dbd0c8f2dfe8c139e88814635bd935ffdfa26a14f"

# WorldPop unit IDs → DataMeet state names.
UNITS = {
    1027: "Dadra and Nagar Haveli and Daman and Diu",
    1029: "Goa",
    1032: "Puducherry",
    1034: "Lakshadweep",
    1035: "Andaman & Nicobar",
    1038: "Chandigarh",
}


def median_age(counts: dict[int, float]) -> float:
    """Interpolate within the band containing half of the population."""
    half = sum(counts.values()) / 2
    below = 0
    for age, count in sorted(counts.items()):
        if count > 0 and below + count >= half:
            width = {0: 1, 1: 4}.get(age, 5)
            return age + width * (half - below) / count
        below += count
    raise ValueError("WorldPop age counts have no median")


def parse_profiles(data: dict) -> dict:
    if data["iso3"] != "IND" or data["data_year"] != 2026:
        raise ValueError("Expected WorldPop estimates for India in 2026")
    profiles = {}
    for unit in data["units"]:
        name = UNITS.get(unit["unit_id"])
        if name is None:
            continue
        counts = {int(band["class"]): band["female"] + band["male"] for band in unit["agesex_pyramid"]}
        median = median_age(counts)
        total = sum(counts.values())
        profiles[name] = {
            "age_0_14": 100 * sum(n for age, n in counts.items() if age < 15) / total,
            "age_60": 100 * sum(n for age, n in counts.items() if age >= 60) / total,
            "median_age": median,
        }
    return profiles


class WorldPopAge(Source):
    info = SourceInfo(
        SOURCE_ID, "India – Age and Sex Structures (R2025A v1)",
        "Bondarenko et al. (2025), WorldPop, University of Southampton",
        "https://doi.org/10.5258/SOTON/WP00841",
        "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)",
        "2026 age and sex estimates aggregated to WorldPop administrative units. IndiaCiv sums both sexes to derive "
        "age shares and interpolates median age within the band containing half of the population.",
        ["Age lenses", "State profiles"],
    )

    def fetch(self, force=False):
        self.download(URL, FILENAME, force=force)

    def process(self):
        raw = (self.raw_dir / FILENAME).read_bytes()
        if hashlib.sha256(raw).hexdigest() != SHA256:
            raise ValueError(f"{self.id}: unexpected SHA-256 for {FILENAME}")
        profiles = parse_profiles(json.loads(raw))
        if profiles.keys() != set(UNITS.values()):
            raise ValueError(f"{self.id}: missing age profiles for selected units")
        return {"profiles": profiles, "vintage": "2026 estimate", "_files": [FILENAME]}
