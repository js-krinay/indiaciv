"""Prepare UN DESA's File 22 projections for Indian urban agglomerations."""

from datetime import date
from hashlib import sha256
from pathlib import Path
import sys

from pipeline.core.store import save_interim
from pipeline.build.projection import CITY_GROWTH_PERIOD
from pipeline.india import WUP_CHECKSUM, WUP_SOURCE
from pipeline.india.grid import CRS

INDIA_CODE = 356


def parse_places(rows, project):
    """Read India's projected populations and convert workbook thousands to people."""
    rows = iter(rows)
    header = next(row for row in rows if "Urban Agglomeration" in row)
    country, code, name, lat, lon, year25, year26 = (
        header.index(key) for key in
        ("Country Code", "City Code", "Urban Agglomeration", "Latitude", "Longitude", 2025, 2026)
    )
    year27 = header.index(2027) if 2027 in header else None
    july25, july26, july27 = (date(year, 7, 1) for year in (2025, 2026, 2027))
    start, end = date(2026, 1, 1), date(2026, 12, 31)
    before = (july26 - start).days / (july26 - july25).days
    after = (end - july26).days / (july27 - july26).days
    places = []
    for row in rows:
        if row[country] != INDIA_CODE:
            continue
        p25, p26 = row[year25], row[year26]
        if not isinstance(p26, (int, float)) or p26 <= 0:
            continue
        x, y = project(row[lon], row[lat])
        places.append({
            "id": str(int(row[code])),
            "name": row[name],
            "population": round(p26 * 1000),
            "projected_growth": p26 / p25 - 1 if isinstance(p25, (int, float)) and p25 > 0 else None,
            "growth_period": CITY_GROWTH_PERIOD,
            "capital": row[name] == "Delhi",
            "x": round(x),
            "y": round(y),
        })
        if isinstance(p25, (int, float)) and p25 > 0:
            places[-1]["population_midyear"] = {"2025": round(p25 * 1000), "2026": round(p26 * 1000)}
        p27 = row[year27] if year27 is not None else None
        if all(isinstance(p, (int, float)) and p > 0 for p in (p25, p27)):
            places[-1]["population_2026"] = {
                "values": {
                    start.isoformat(): round(1000 * (p26 - (p26 - p25) * before)),
                    july26.isoformat(): round(1000 * p26),
                    end.isoformat(): round(1000 * (p26 + (p27 - p26) * after)),
                },
                "source": WUP_SOURCE, "estimated": True, "period": "1 Jan – 31 Dec 2026",
            }
    if not places or len({place["id"] for place in places}) != len(places):
        raise ValueError("Missing Indian agglomerations or duplicate UN city codes")
    return places


def cities(path):
    import xlrd
    from pyproj import Transformer

    content = path.read_bytes()
    if sha256(content).hexdigest() != WUP_CHECKSUM:
        raise ValueError("Unexpected UN World Urbanization Prospects File 22 workbook")
    sheet = xlrd.open_workbook(file_contents=content).sheet_by_name("Data")
    project = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    return parse_places((sheet.row_values(i) for i in range(sheet.nrows)), project.transform)


if __name__ == "__main__":
    save_interim(WUP_SOURCE, {"places": cities(Path(sys.argv[1]))}, vintage="Projected for mid-2026")
