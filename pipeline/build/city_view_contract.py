"""Project existing Indian observations into the upstream City View shapes."""

from ..india.historical_sources import WORKPLACE_LICENSE, WORKPLACE_LICENSE_URL, WORKPLACE_PERIOD, WORKPLACE_SOURCE
from ..india import CITY_POPULATION_GRID
from ..india.city_sources import GOVERNMENT_SITE_SOURCE
from ..india.workplace import MIN_JOBS, MIN_LQ, MIN_SHARE
from .city_view import apportion


def metadata(record):
    return {key: record[key] for key in ("source", "period", "vintage", "estimated", "scope") if key in record}


def economy_column(label, fmt, unit, value, record, *, estimated=False, description=""):
    return {
        **metadata(record), "label": label, "format": fmt, "unit": unit, "group": "Economy",
        "value": value, "estimated": record.get("estimated", estimated),
        "description": record.get("description", description),
        **({"status": record["status"]} if record.get("status") else {}),
    }


SECTOR_LABELS = {
    "agriculture": "Agriculture & allied", "industry": "Industry", "services": "Services",
    "mining": "Mining & quarrying", "manufacturing": "Manufacturing",
    "construction": "Construction", "utilities": "Utilities",
}


def explorer_gsva_columns(mix):
    if not mix:
        return {}
    return {
        f"gsva_{key}_share": economy_column(
            f"State GSVA · {SECTOR_LABELS[key]}", "pct", "share of nominal state GSVA", value, mix,
            description="Share of the state’s total nominal GSVA. Cities show their primary state here.",
        )
        for key, value in mix["shares"].items() if key in ("agriculture", "industry", "services")
    }


def explorer_output_columns(city):
    columns = explorer_gsva_columns(city.get("state_sector_mix"))
    if gold := city.get("yield_meta", {}).get("gold"):
        columns["gdp"] = economy_column("Estimated city GDP", "inr", "INR", city.get("yields", {}).get("gold"), gold, estimated=True)
        columns["gdp_rank"] = economy_column("City GDP rank", "int", "rank among mapped urban agglomerations",
                                             city.get("ranks", {}).get("gdp"), gold, estimated=True)
        if city.get("gdp_per_capita") is not None:
            columns["gdp_per_resident"] = economy_column(
                "Estimated city GDP per resident", "inr", "INR per resident",
                city["gdp_per_capita"], gold, estimated=True,
                description="Nominal city output divided by the UN mid-2026 population.",
            )
    if output := city.get("sector_output"):
        for key, value in output["values"].items():
            if key in SECTOR_LABELS:
                columns[f"gdp_{key}"] = economy_column(f"City GDP · {SECTOR_LABELS[key]}", "inr", "INR",
                                                       value, output, estimated=True)
    for key, label, record in (
        ("economic_growth", "Nominal city output growth", city.get("output_growth")),
        ("share_national_gdp", "Share of India’s GDP", (city.get("national_shares") or {}).get("gdp")),
        ("share_national_population", "Share of India’s population", (city.get("national_shares") or {}).get("population")),
    ):
        if record:
            columns[key] = economy_column(label, "pct", "%", record.get("value"), record, estimated=True)
    return columns


def explorer_finance_columns(finances):
    description = ("Nominal state output allocated by projected urban population. "
                   "GDP per resident uses the UN mid-2026 projection.")
    return {
        "gdp_per_resident": economy_column("Estimated city GDP per resident", "inr", "INR per resident",
                                           finances.get("gdp_per_resident"), finances, estimated=True, description=description),
        "gdp_per_resident_rank": economy_column("City GDP per resident rank", "int", "rank among the original 50 City View cities",
                                                (finances.get("ranks") or {}).get("gdp_per_resident"), finances,
                                                estimated=True, description=description),
    }


def explorer_profile_columns(profile, district_names):
    columns = {}
    if age := profile["citizens"].get("age"):
        for key, label in (("0_14", "0–14"), ("15_59", "15–59"), ("60_plus", "60+"), ("midlife", "35–64")):
            columns[f"age_{key}_count"] = {
                **metadata(age), "group": "People", "format": "int", "unit": "people",
                "label": f"Residents aged {label}",
                "value": age["bands"].get(key) if key == "midlife" else age["counts"].get(key),
                "description": "WorldPop age shares within the modelled urban footprint, scaled to the UN city population.",
            }
        if band := age.get("median_band"):
            columns["median_age_band"] = {
                **metadata(age), "label": "Median age band", "group": "People", "format": "text", "unit": "years",
                "value": f"{band[0]}+" if band[1] is None else f"{band[0]}–{band[1]}",
            }
        if age.get("median") is not None:
            columns["median_age"] = {
                **metadata(age), "label": "Median age", "group": "People", "format": "years", "unit": "years",
                "value": age["median"], "description": "Interpolated within the WorldPop age band containing the median.",
            }
    if workforce := profile["citizens"].get("workforce"):
        columns["population_15_plus"] = {
            "period": "mid-2026", "source": "worldpop_age", **metadata(profile["citizens"].get("age") or {}),
            "label": "Residents aged 15+", "group": "People", "format": "int", "unit": "people",
            "value": workforce.get("population_15_plus"), "estimated": True,
        }
    if profile["method"] == "ghsl":
        common = {"group": "Geography", "format": "int", "unit": "districts", "period": "November 2026"}
        columns["member_district_count"] = {
            **common, "label": "Member districts", "source": "city_footprints", "value": len(profile["districts"]),
        }
        names = [district_names[row["id"]] for row in profile["districts"] if row["id"] in district_names]
        columns["n_districts"] = {
            **common, "label": "Districts in modelled footprint", "source": ["city_footprints", "datameet"],
            "value": len(names),
        }
        columns["footprint_districts"] = {
            "label": "Districts in the modelled footprint", "group": "Geography", "format": "text",
            "unit": "district names", "period": "2026 snapshot", "source": ["city_footprints", "datameet"],
            "value": " · ".join(names) or None,
        }
        for key, label, unit, period, sources in (
            ("footprint_share", "City footprint area by district", "share of city footprint area",
             "November 2026", ["city_footprints", "datameet"]),
            ("population_share", "District population inside city footprint", "share of each district’s modelled population",
             "mid-2026", ["city_footprints", "datameet", CITY_POPULATION_GRID]),
        ):
            values = [f'{district_names[row["id"]]} {row[key]:.1%}' for row in profile["districts"]
                      if row["id"] in district_names and row.get(key) is not None]
            if values:
                columns[f"member_{key}"] = {
                    "group": "Geography", "label": label, "unit": unit, "format": "text", "period": period,
                    "source": sources, "estimated": True, "value": " · ".join(values),
                }
        for key, name, source in (
            ("campus", "Campus", "research_points"),
            ("harbor", "Harbor", ["cwprs_port_locations", "featured_port_locations"]),
            ("aerodrome", "Aerodrome", "ourairports"),
            ("government_plaza", "Government plaza", GOVERNMENT_SITE_SOURCE),
        ):
            count = sum(badge["kind"] == key for badge in profile.get("district_badges", ()))
            if key == "government_plaza" and not count:
                continue
            columns[f"district_{key}"] = {
                **common, "label": f"{name} districts", "source": source,
                "value": count,
            }
    if plaques := profile.get("industry_plaques"):
        common = {
            "label": "Documented industry clusters", "group": "Work",
            "source": list(dict.fromkeys(row["source"] for row in plaques)),
            "estimated": any(row.get("estimated") for row in plaques),
        }
        columns["plaque_count"] = {
            **common, "format": "int", "unit": "reviewed clusters", "value": len(plaques),
            "period": " · ".join(sorted({row["period"] for row in plaques})),
        }
        columns["industry_plaques"] = {
            **common, "format": "text", "unit": "cluster names",
            "period": " · ".join(dict.fromkeys(row["period"] for row in plaques)),
            "value": " · ".join(row["label"] for row in plaques),
        }
    return columns


def explorer_work_columns(work):
    if not work:
        return {}
    common = {"group": "Work", **metadata(work)}
    mixed = len(work.get("states", ())) > 1
    columns = {}
    for key, label, unit, estimated in (
        ("employed_all_ages", "Employed residents", "people", True),
        ("employed_15_plus", "Employed residents aged 15+", "people", True),
        ("state_urban_wpr_all_ages", "Urban worker-population ratio benchmark (all ages)", "share of residents", False),
        ("state_urban_wpr_15_plus", "Urban worker-population ratio benchmark (15+)", "share of residents age 15+", False),
        ("state_urban_unemployment_15_plus", "Urban unemployment benchmark (15+)", "share of labour force age 15+", False),
    ):
        if work.get(key) is not None:
            detail = work.get("unemployment_benchmark") if key == "state_urban_unemployment_15_plus" else None
            columns[key] = {**common, **metadata(detail or {}), "label": label, "unit": unit,
                            "format": "int" if estimated else "pct",
                            **({"description": work["description"]} if estimated and work.get("description") else {}),
                            "value": work[key], "estimated": estimated or mixed}
    for row in work.get("industries", ()):
        key = row["sector"]
        if key not in ("agriculture", "industry", "services"):
            continue
        for suffix, value_key, label, unit, fmt, estimated in (
            ("workers", "employed", "workers", "resident workers age 15+", "int", True),
            ("share", "state_urban_share", "share (state urban)", "share of state urban workers age 15+", "pct", False),
        ):
            if row.get(value_key) is not None:
                columns[f"sector_{key}_{suffix}"] = {
                    **common, "label": f"{key.title()} {label}", "unit": unit, "format": fmt,
                    "value": row[value_key], "estimated": estimated or mixed,
                }
    return columns


def gdp_industry_fields(output):
    values = output["values"]
    sectors = {key: values[key] for key in ("agriculture", "industry", "services")}
    details = {key: values[key] for key in ("mining", "manufacturing", "construction", "utilities") if key in values}
    if details:
        remainder = sectors.pop("industry") - sum(details.values())
        if remainder < 0:
            if remainder < -2:
                raise ValueError("GDP sector details exceed the industry total")
            details[max(details, key=details.get)] += remainder
        if remainder > 0:
            sectors["Other industry"] = remainder
        sectors.update(details)
    return {"gdp_by_industry": sectors, "gdp_estimated": list(sectors)}


def urban_consumption(states, members, pilot):
    if states == ["UP"] and len(members) == 1 and (record := pilot.get(members[0])):
        return {**metadata(record), "value": record["urban"], "scope": "Urban member district"}
    return None


def cultivation_mix(members, districts):
    if not members or any(member not in districts for member in members):
        return None
    records = [districts[member] for member in members]
    workers = sum(record["workers"] for record in records)
    return {**metadata(records[0]), "scope": "Urban member districts",
            "value": sum(record["cultivation_workers"] for record in records) / workers}


def city_record(city, profile=None, owner=None, pilot=None):
    provenance = dict(city.get("provenance", {}))
    result = {"provenance": provenance}
    if profile:
        result.update(
            footprint=sorted({city["cell"], *(row["cell"] for row in profile["cells"]
                                              if owner is None or owner[row["cell"]] >= 0)}),
            counties=[row["id"] for row in profile["districts"]],
        )
        if pilot and (consumption := urban_consumption(city["states"], result["counties"], pilot)):
            result["consumption_index"] = consumption["value"]
            provenance["consumption_index"] = metadata(consumption)
    if city.get("projected_growth") is not None:
        result["growth"] = city["projected_growth"]
        result["growth_years"] = [2025, 2026]
        provenance["growth"] = provenance["projected_growth"]
    if city.get("yields", {}).get("gold") is not None:
        result["gdp"] = city["yields"]["gold"]
        result["gdp_year"] = 2026
        provenance["gdp"] = metadata(city["yield_meta"]["gold"])
    if city.get("population_2026"):
        result["pop_series"] = {"2026": city["population"]}
        provenance["pop_series"] = provenance.get("population")
    if work := city.get("resident_workforce"):
        result["advisor_columns"] = explorer_work_columns({**work, "industries": []})
        provenance["unemployment"] = metadata(work.get("unemployment_benchmark") or work)
        result["unemployment"] = work["state_urban_unemployment_15_plus"]
        if result["unemployment"] is not None:
            result["advisor_columns"]["unemployment"] = {
                **provenance["unemployment"], "label": "Unemployment rate", "group": "Work", "format": "pct",
                "unit": "%", "value": result["unemployment"], "description": "State urban PLFS benchmark for ages 15+.",
            }
        if work.get("employed_15_plus") is not None:
            result["jobs"] = {row["sector"]: row["employed"] for row in work["industries"]}
            result["employed"] = work["employed_15_plus"]
            provenance["jobs"] = provenance["employed"] = metadata(work)
        provenance["employed"] = {
            **provenance.get("employed", metadata(work)),
            "age_scope": "age 15+" if work.get("employed_15_plus") is not None else "all ages",
        }
    if output := city.get("sector_output"):
        record = metadata(output)
        if weights := output.get("input_weights"):
            label = weights["period"].split(" (", 1)[0]
            record.update(period=f'{output["period"]} · Mining and utilities use {label} weights',
                          input_weights=weights, description=output["description"], fields=output["fields"])
            for key, detail in output["fields"].items():
                provenance[f"gdp_{key}"] = {**detail, "status": f"Uses {label} weights"}
        provenance["gdp_by_industry"] = record
    if (growth := city.get("output_growth")) and growth.get("status") == "Separate fiscal series":
        provenance["economic_growth"] = {**metadata(growth), "status": growth["status"],
                                         "description": growth["description"]}
    return result


GROUPS = {
    "workforce": {
        "executive": "Executives and managers", "engineer": "Engineers and scientists",
        "scholar": "Education, law and arts", "healer": "Health", "service": "Service",
        "clerk": "Sales and office", "builder": "Construction and repair",
        "maker": "Production and transport",
    },
    "age": {"child": "Under 18", "young": "18–34", "midlife": "35–64", "elder": "65+"},
    "commute": {"walk": "On foot", "transit": "Bus and train", "other": "Other transport"},
    "education": {"less_than_hs": "Below secondary", "high_school": "Secondary or higher secondary",
                  "some_college": "Diploma below degree", "bachelors": "Graduate and above"},
    "nativity": {"born_in_state": "This census state", "other_state": "Other Indian state",
                 "foreign_born": "Born outside India"},
}

FIGURES = {"workforce": 20, "age": 10, "commute": 10, "education": 10, "nativity": 10}


def displayed_shares(key, shares):
    eligible = {name: shares[name] for name in GROUPS[key] if name in shares}
    denominator = sum(eligible.values())
    return {name: value / denominator for name, value in eligible.items()} if denominator else {}


def mix_row(key, record, shares, total=None, counts=None):
    shares = displayed_shares(key, shares)
    if not shares:
        return None
    result = {**metadata(record), "shares": shares, "figures": apportion(FIGURES[key], shares)}
    if total is not None:
        result.update(total=total, counts=counts)
    return result


EXPLORER_OCCUPATIONS = {
    'executive': 'Officials and managers',
    'engineer': 'Science, engineering and computing',
    'scholar': 'Teaching, legal and arts professionals',
    'healer': 'Health practitioners',
    'service': 'Personal service and sales',
    'clerk': 'Clerical occupations',
    'builder': 'Building trades and electrical repair',
    'maker': 'Production, transport and freight occupations',
    'other': 'Other or unclassified occupations',
}

def explorer_resident_columns(work):
    from .citizens import resident_industries

    columns = {}
    if record := work.get("occupations"):
        common = {**metadata(record), "group": "Resident occupations", "hide_rank": True,
                  "description": "Urban member-district main and marginal workers, excluding cultivators and agricultural labourers."}
        for key, label in EXPLORER_OCCUPATIONS.items():
            value = record["values"].get(key)
            if value is not None:
                columns[f"cz_{key}"] = {**common, "label": label, "format": "pct", "unit": "%", "value": value}
        if specialist := record.get("specialist"):
            label = EXPLORER_OCCUPATIONS[specialist["family"]]
            columns["cz_specialist"] = {
                **common, "label": "Most over-represented occupation", "format": "text",
                "unit": "local share ÷ urban India share", "value": f"{label} ×{specialist['ratio']:.2f}",
            }
    if record := work.get("industries"):
        for key, observation in resident_industries(record, record.get("details")).items():
            columns[f"census_resident_industry_{key}"] = {
                **observation, "group": "Resident industries", "scope": record["scope"],
                "description": "Census 2011 B-18. Fine NIC subtotals overlap their broad industry.",
            }
    return columns


def citizen_mix(citizens, ages, city):
    result = {}
    if record := citizens.get("census_work", {}).get("occupations"):
        result["workforce"] = mix_row("workforce", record, record["values"])
        if result["workforce"] and (benchmark := record.get("benchmark")):
            national = displayed_shares("workforce", benchmark)
            result["workforce"]["benchmark"] = national
            local = result["workforce"]["shares"]
            result["specialists"] = sorted(({
                "row": "workforce", "key": key, "ratio": share / national[key],
                "share": share, "national": national[key], **metadata(record),
            } for key, share in local.items()
                if national.get(key) and (share / national[key] >= 1.5 or share / national[key] <= 0.67)),
                key=lambda row: -row["ratio"])
    if ages and (age := citizens.get("age")):
        # WorldPop has ages 15–19 in one bin. Use 3/5 for ages 15–17.
        younger = 0.6 * ages.get(15, 0)
        weights = {
            "child": sum(v for k, v in ages.items() if k < 15) + younger,
            "young": sum(v for k, v in ages.items() if 15 <= k < 35) - younger,
            "midlife": sum(v for k, v in ages.items() if 35 <= k < 65),
            "elder": sum(v for k, v in ages.items() if k >= 65),
        }
        total = city["population"]
        counts = apportion(total, weights)
        result["age"] = mix_row("age", age, {k: v / total for k, v in counts.items()}, total, counts)
        if age.get("median") is not None:
            result["age"]["median"] = age["median"]
    civic = citizens.get("census_civic", {})
    if record := civic.get("commute"):
        values = record["values"]
        shares = {"walk": values["On foot"], "transit": values["Bus and train"], "other": sum(values[k] for k in (
                      "Bicycle", "Moped/Scooter/Motor Cycle", "Car/Jeep/Van", "Tempo/Autorickshaw/Taxi",
                      "Water transport", "Any other"))}
        result["commute"] = mix_row("commute", record, shares)
    if record := civic.get("education"):
        shares = {key: record["values"][name] for key, name in GROUPS["education"].items()}
        result["education"] = mix_row("education", record, shares)
        if result["education"]:
            result["education"]["bachelors_plus"] = shares["bachelors"]
    if record := civic.get("birthplace"):
        values = record["values"]
        shares = dict(zip(GROUPS["nativity"], (values[k] for k in (
            "Born in census state", "Born in another Indian state", "Born outside India")),
            strict=True))
        result["nativity"] = mix_row("nativity", record, shares)
    if result.get("nativity"):
        result["nativity"]["foreign_born"] = shares["foreign_born"]
    return {key: value for key, value in result.items() if value}


DISTRICT_TYPES = {
    "Scientific research and development": ("campus", "Campus", "Research City", "#2b4f8a"),
    "Water transport": ("harbor", "Harbor", "Port City", "#3d5f73"),
    "Air transport": ("aerodrome", "Aerodrome", "Aviation City", "#557f9a"),
    "Performing arts and entertainment": ("theater_square", "Theatre Square", "Arts City", "#5b3a7e"),
    "Accommodation": ("entertainment_complex", "Entertainment Complex", "Hospitality City", "#6e3a5e"),
    "Utilities (electricity, gas, steam and water)": ("aqueduct", "Aqueduct", "Utilities City", "#2a5f86"),
    "Electric power": ("aqueduct", "Aqueduct", "Power City", "#2a5f86"),
    "Basic metals and casting": ("industrial_zone", "Industrial Zone", "Metals City", "#9a5a22"),
    "Coke and refined petroleum": ("industrial_zone", "Industrial Zone", "Refining City", "#9a5a22"),
    "Pharmaceutical manufacturing": ("industrial_zone", "Industrial Zone", "Pharma City", "#9a5a22"),
}


SITE_DISTRICTS = {
    "campus": ("Campus", "#2b4f8a"),
    "harbor": ("Harbor", "#3d5f73"),
    "aerodrome": ("Aerodrome", "#557f9a"),
    "government_plaza": ("Government Plaza", "#5a6a7a"),
    "industrial_land_use": ("Mapped industrial land-use site", "#9a5a22"),
    "commercial_hub": ("Mapped commercial land-use site", "#786122"),
}


def add_district_roles(cities, catalog, profiles):
    for city_id, profile in profiles.items():
        sites = profile.get("district_badges", [])
        roles = profile.get("industry_plaques", [])
        capital = profile.get("capital_designation")
        if not sites and not roles and not capital:
            continue
        row = cities.setdefault(city_id, {"districts": [], "top": [], "badge": None})
        districts = {district["id"]: district for district in row["districts"]}
        for site in sites:
            key = site["kind"]
            name, color = SITE_DISTRICTS[key]
            name = site.get("label", name)
            catalog.setdefault(key, {"id": key, "name": name, "color": color, "sub": {}})
            if key not in districts:
                districts[key] = {"id": key, "via": "site"}
                row["districts"].append(districts[key])
            districts[key].setdefault("sites", []).append(site)
        if capital:
            row["capital_designation"] = capital
        if "emp" not in row:
            if capital:
                row["badge"] = capital.copy()
            elif roles:
                role = roles[0]
                row["badge"] = {**metadata(role), "label": role["label"], "text": role.get("evidence", role["label"])}
        if roles:
            row["roles"] = roles
        badge = row.get("badge") or {}
        captions = [*([capital] if capital and capital["label"] != badge.get("label") else []), *roles]
        if captions:
            row["role_caption"] = " · ".join(f"{role['label']} ({role['period']})" for role in captions)


def workplace_districts(workplace, profiles):
    cities = {}
    catalog = {}
    industries = {}
    provenance = {"period": WORKPLACE_PERIOD, "source": WORKPLACE_SOURCE, "vintage": "older"}
    for city_id, record in (workplace or {}).get("cities", {}).items():
        if city_id not in profiles:
            continue
        districts, top, badge = {}, [], None
        ranked = sorted(record["industries"].items(),
                        key=lambda item: (item[1]["lq"], item[1].get("excess_jobs", 0), item[0]),
                        reverse=True)
        for label, metrics in ranked:
            if label not in DISTRICT_TYPES or not metrics["local_share"]:
                continue
            jobs = round(record["jobs"] * metrics["local_share"])
            industries[label] = {"title": label}
            top.append({**provenance, "naics": label, "emp": jobs, "lq": metrics["lq"]})
            if not metrics["qualifies"]:
                continue
            key, name, city_type, color = DISTRICT_TYPES[label]
            catalog.setdefault(key, {"id": key, "name": name, "color": color, "sub": {}})["sub"][label] = label
            if key not in districts:
                districts[key] = {
                    **provenance,
                    "id": key, "via": "specialty", "sub": label, "sub_lq": metrics["lq"],
                    "sub_emp": jobs, "strength": metrics.get("excess_jobs"),
                }
            if badge is None:
                badge = {**provenance, "district": key, "label": city_type, "text": label}
        cities[city_id] = {**provenance, "emp": record["jobs"], "top": top[:8],
                           "districts": list(districts.values()), "badge": badge}
    add_district_roles(cities, catalog, profiles)
    return {
        **provenance, "license": WORKPLACE_LICENSE, "license_url": WORKPLACE_LICENSE_URL,
        "attribution": "MoSPI Sixth Economic Census via Development Data Lab, SHRUG v2.2 Pakora",
        "rule": {"text": f"Civilian specialisations require {MIN_JOBS} jobs, a {MIN_SHARE:.1%} local share and "
                         f"at least {MIN_LQ} times the national share. Highest LQ wins, with excess jobs breaking ties. "
                         "Verified sites and documented qualitative roles use dated inventories. "
                         "Job counts and location quotients apply to workplace specialisations."},
        "cities": cities, "catalog": list(catalog.values()), "industries": industries,
    }
