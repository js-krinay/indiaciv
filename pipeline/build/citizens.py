"""Dated resident-workforce and commute analogues for City View."""

from ..india.census_work import DETAIL_LABELS


INDUSTRIES = {
    "mining": "Mining",
    "construction": "Construction",
    "manufacturing": "Manufacturing",
    "wholesale": "Wholesale excluding motor vehicles",
    "retail": "Retail excluding motor vehicles",
    "transportation": "Transport, storage and post",
    "utilities": "Utilities and waste",
    "information": "Information and communication",
    "finance": "Finance and insurance",
    "real_estate": "Real estate",
    "professional": "Professional, scientific and technical services",
    "professional_excluding_head_offices": "Professional, scientific and technical services excluding head offices",
    "management": "Head offices (NIC 701)",
    "admin": "Administrative and support services",
    "education": "Education",
    "health": "Health and social work",
    "arts": "Arts, entertainment and recreation",
    "accommodation": "Accommodation and food service",
    "other": "Other industries",
    "public_admin": "Civilian administration and compulsory social security",
}


def share(record, label, value):
    return {"label": label, "value": round(value, 3 if abs(value) < .1 else 2),
            "unit": "%", "format": "pct", "hide_rank": True,
            **{key: record[key] for key in ("period", "vintage", "source")}}


def commute_analogues(record):
    values = record.get("values", {})
    return {f"cz_{column}": {**share(record, label, values[key]), "group": "Census civic measures",
                            "scope": "All Census Other workers"}
            for column, key, label in (
                ("car", "Car/Jeep/Van", "Car, jeep or van commuters among Census Other workers"),
                ("tempo", "Tempo/Autorickshaw/Taxi", "Tempo, autorickshaw or taxi commuters among Census Other workers"),
                ("home", "No travel", "Other workers reporting no travel to work"),
            ) if values.get(key) is not None}


def resident_industries(record, details=None):
    values = dict(record.get("values", {}))
    details = details or {}
    if "701" in details and "professional" in values and details["701"] <= values["professional"]:
        values["professional_excluding_head_offices"] = round(values["professional"] - details["701"], 7)
        values["management"] = details["701"]
    labels = {**INDUSTRIES, **{code: f"{label} (NIC {code})" for code, label in DETAIL_LABELS.items() if code != "701"}}
    values.update({code: value for code, value in details.items() if code != "701"})
    scope = "Share of eligible urban member-district resident workers"
    return {key: {**share(record, f"{label} {scope.lower()}", values[key]), "short_label": label, "caption": scope}
            for key, label in labels.items() if values.get(key) is not None}
