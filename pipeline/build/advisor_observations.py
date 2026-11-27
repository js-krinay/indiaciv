"""Observations selected from the atlas's published geography and data products."""

import math
from collections import defaultdict

from .advisor_inventory import FY, SNAPSHOT, column

MARCH = "1 March 2026"
MID = "mid-2026"
TG = "tg_projections"
UN = "un_wup_cities"
DM = "datameet"


def path_value(record, path):
    for key in path:
        record = record.get(key) if isinstance(record, dict) else None
    return record


def city_district_observations(cities, profiles):
    memberships, populations, plaques = defaultdict(list), {}, defaultdict(list)
    for city in cities:
        profile = profiles.get(city["id"], {})
        for row in profile.get("districts", []):
            populations[row["id"]] = row.get("district_population")
            if profile["method"] == "ghsl":
                memberships[row["id"]].append(city["name"])
        for row in profile.get("industry_plaques", []):
            plaques[row["district"]].append(row)
    return memberships, populations, plaques


def place_columns(level, row, ident, profile, lenses, protected_share, district_info, hex_area):
    out = {}
    is_city = level == "metros"
    is_state = level == "states"
    provenance = row.get("provenance", {})

    def add(key, label, fmt, unit, group, period, source, value, detail=None, **extra):
        record = column(label, fmt, unit, group, period, source, value, **extra)
        for meta in (detail or {}, provenance.get(key, {})):
            record.update({k: v for k, v in meta.items() if k in (
                "period", "source", "vintage", "estimated", "description", "lens", "scope", "status", "coverage", "sparse"
            ) and v is not None})
        out[key] = record

    def lens_detail(key):
        lens = lenses.get(key, {})
        return {**lens, "lens": key} if lens else {}

    add("name", "Place", "text", "place name", "Geography", SNAPSHOT, UN if is_city else DM, ident["name"])
    if not is_state:
        state = " · ".join(row.get("states", [])) if is_city else row.get("state")
        add("state", "State / UT", "text", "state or UT code", "Geography", SNAPSHOT, DM, state)
    population = row.get("population")
    add("population", "Population", "int", "people", "People", MID if is_city else MARCH,
        UN if is_city else TG, population, estimated=not (is_city or is_state),
        description="District census totals scaled by the state projection's population change through March 2026."
        if not (is_city or is_state) else "")
    if is_city:
        area = hex_area * sum(cell["hex_fraction"] for cell in profile.get("cells", [])) if profile.get("method") == "ghsl" else None
        density = population / area if area and population is not None else None
    else:
        area = row.get("area_km2")
        density = row.get("profile", {}).get("density") if is_state else row.get("density")
    add("density", "Population density", "float", "people / km²", "People", MID if is_city else MARCH,
        [UN, "city_footprints"] if is_city else TG, density, estimated=not is_state,
        lens=None if is_city else "state_density" if is_state else "density",
        description="Projected residents divided by mapped area. District and state areas each come from their own DataMeet boundaries.")
    add("area_km2", "Mapped area", "km2", "km²", "Land", "2026 snapshot", "city_footprints" if is_city else DM, area,
        description=("Area of the clipped GHSL proxy for the UN urban agglomeration, from its fractions of atlas hexes."
                     if is_city else "Area measured in the equal-area projection from DataMeet boundary rings."))
    if is_city or is_state:
        growth_lens = "city_growth" if is_city else "growth"
        growth = None
        if lenses.get(growth_lens, {}).get("period"):
            if is_city:
                if row.get("growth_period") and not any(provenance.get(key, {}).get("vintage") == "older"
                                                        for key in ("population", "projected_growth", "growth")):
                    growth = row.get("projected_growth")
            else:
                growth = row.get("profile", {}).get("growth")
        add("projected_growth", "Population growth", "signed", "%", "People", MARCH, TG, growth, lens_detail(growth_lens))
    if not is_city:
        if not is_state and (grazing := row.get("village_grazing")):
            add("village_grazing", "Permanent pasture and other grazing land (reporting rural villages)",
                "pct", "% of reported village area", "Land", grazing["period"], grazing["source"],
                grazing["value"], grazing, vintage="older", hide_rank=True)
        add("protected_share", "Mapped protected share", "pct", "share of area", "Geography", "2026 snapshot",
            ["osm_protected", "rsis_protected", DM], protected_share,
            description="Share of the DataMeet unit covered by available mapped Ramsar, park and tiger reserve extents, counting overlaps once.")
        for key, label, fmt, unit, lens, health in (
            ("sex_ratio", "Sex ratio", "int", "women per 1,000 men", "sex_ratio", False),
            ("age_0_14", "Aged 0–14", "pct", "share of residents", "children", False),
            ("age_60", "Aged 60+", "pct", "share of residents", "elderly", False),
            ("median_age", "Median age", "years", "years", "median_age", False),
            ("tfr", "Fertility", "float", "children per woman", "fertility", True),
            ("imr", "Infant mortality", "float", "deaths per 1,000 births", "infant_mortality", True),
            ("life_female", "Life expectancy of women", "years", "years", "life_female", True),
            ("life_male", "Life expectancy of men", "years", "years", "life_male", True),
        ):
            if is_state:
                detail = lens_detail(lens)
                if key == "median_age" and provenance.get(key, {}).get("vintage") == "older":
                    detail = {"description": "Median of Census 2011 residents with stated age in Leh and Kargil."}
                elif key in ("age_0_14", "age_60", "median_age") and row.get("age_source"):
                    detail = {"source": row["age_source"], "period": "2026", "estimated": True, "lens": lens}
                value = row.get("profile", {}).get(key) if not health or detail.get("period") else None
                if fmt == "pct" and value is not None:
                    value /= 100
            elif key == "median_age":
                detail, value = {}, row.get(key)
            else:
                continue
            add(key, label, fmt, unit, "Health" if health else "People", MARCH, TG, value, detail)
    if is_state:
        add("employed", "Employed residents", "int", "people", "Work", "1 Jul – 30 Sep 2026",
            ["plfs_2026_q3", TG], row.get("employed"), estimated=True,
            description="All-ages PLFS worker-population ratio applied to the projected 1 March 2026 population.")
        add("state_gsdp", "Nominal GSDP", "inr", "INR", "Economy", FY, "gsdp_fy26", path_value(row, ("yields", "gold")),
            path_value(row, ("yield_meta", "gold")),
            description="Nominal output at current prices. Where required, the latest available GSDP is grown at India's nominal GDP growth rate.")
        internet = path_value(row, ("metrics", "internet_per_100", "value"))
        add("internet_per_100", "Internet subscriptions per 100 residents", "decimal1", "subscriptions per 100 residents",
            "Daily life", "30 June 2026", ["trai_internet_june_2026", TG],
            internet if internet is not None else row.get("internet_per_100"), lens="internet_per_100", estimated=True,
            description="June subscriptions divided by the projected 1 March 2026 population. Includes all access types.")
    else:
        add("consumption_index", "Urban district consumption per person index (Uttar Pradesh urban = 100)",
            "float", "index", "Prosperity", "HCES 2022–23 (1 Aug 2022 to 31 Jul 2023)", "mospi_up_hces_pilot",
            row.get("consumption_index"), vintage="older", hide_rank=True,
            description="Urban residents of the reporting district. City entries represent a single urban member district.")
        cultivation = (path_value(profile, ("citizens", "cultivation")) if is_city else row.get("cultivation")) or {}
        add("cultivation_share", "Cultivators and agricultural labourers among urban district workers",
            "pct", "% of urban district workers", "Work", "Census 2011", "orgi_cultivation_pca",
            cultivation.get("value"), cultivation, vintage="older", hide_rank=True,
            description="Main and marginal workers. City entries combine urban member districts using Census worker counts.")
        monsoon = lenses.get("monsoon_2026", {})
        values = monsoon.get("values", {})
        if is_city:
            cell = row["cell"]
            band = values.get(str(cell)) if isinstance(values, dict) else values[cell] if cell < len(values) else None
        else:
            band = row.get("monsoon_2026")
        levels = ["Large deficit", "Deficit", "Near normal", "Excess", "Large excess"]
        add("monsoon_2026", "Monsoon rainfall band", "text", "band", "Air & weather", "Jun–Sep 2026", "imd_monsoon",
            levels[band + 2] if isinstance(band, int) and -2 <= band <= 2 else None, lens_detail("monsoon_2026"))
    if is_city:
        for key, label, unit, value in (
            ("kind", "Place type", "UN geography", "Urban agglomeration" if row.get("metro") else None),
            ("city_view", "Detailed City View coverage", "availability", "Available" if row.get("city_view") else None),
            ("capital", "Capital", "designation", "National capital" if row.get("capital") else None),
            ("city_type", "Agglomeration size class", "UN population class",
             "Million-plus" if population >= 1e6 else "Under one million"),
        ):
            add(key, label, "text", unit, "Geography", SNAPSHOT if key in ("city_view", "capital") else MID, UN, value)
        add("population_rank", "Atlas population rank", "int", "rank among mapped cities", "People", MID, UN,
            path_value(row, ("ranks", "population")))
        bad_air = path_value(lenses, ("city_bad_air", "city_values", row["id"]))
        air_detail = lens_detail("city_bad_air")
        if bad_air is None and (aqi := path_value(profile, ("air", "aqi"))) and "rank" not in aqi:
            bad_air = aqi["bad_days"] / aqi["valid_days"]
            air_detail = aqi
        add("city_bad_air", "Poor or worse AQI days", "pct", "share of reported days", "Air & weather",
            "Jan–Oct 2026", "cpcb_city_aqi", bad_air, air_detail)
        floods = profile.get("historical_flood_impacts", [])
        if floods:
            def flood_caption(event):
                phrase = f"{event['period']} · {event.get('label') or event['id']}"
                if event.get("casualties") is not None:
                    lower = "at least " if event.get("lower_bound") else ""
                    phrase += f" · {lower}{event['casualties']} deaths and injuries"
                return phrase

            add("city_historical_floods", "Historical flood impacts", "text", "selected member-district events",
                "Hazards", " · ".join(event["period"] for event in floods), "ifi_flood_impacts",
                " · ".join(map(flood_caption, floods)), vintage="older")
        if incidents := profile.get("hazards"):
            def incident_date(event):
                start, end = event.get("start_date"), event.get("end_date")
                return f"{start} – {end}" if start and end else start or f"Reported {event['reported_on']}"

            add("city_hazards", "Documented hazards", "text", "selected member-district incidents", "Hazards",
                " · ".join(dict.fromkeys(map(incident_date, incidents))),
                list(dict.fromkeys(event["source"] for event in incidents)),
                " · ".join(f"{event['label']} ({event['type']})" for event in incidents))
    elif not is_state:
        memberships, worldpop, plaques = district_info
        add("metro", "Overlapping modelled UAs", "text", "urban agglomerations", "Geography",
            "2026 snapshot", ["city_footprints", DM], " · ".join(memberships) or None)
        add("worldpop_district_population", "WorldPop district population", "int", "people", "People", MID,
            "city_population_grid", worldpop, estimated=True,
            description="Sum of population grid pixel centres within the district. Available for districts intersecting the modelled City View footprints.")
        add("district_pm25", "District PM₂.₅", "float", "µg/m³", "Air & weather", "Jan–Oct 2026",
            "cpcb_station_pm25", row.get("district_pm25"), lens_detail("district_pm25"), estimated=True)
        if plaques:
            add("districts", "Documented industry clusters", "text", "reviewed clusters", "Work",
                " · ".join(sorted({p["period"] for p in plaques})), list(dict.fromkeys(p["source"] for p in plaques)),
                " · ".join(dict.fromkeys(p["label"] for p in plaques)), estimated=any(p.get("estimated") for p in plaques))
    return out
