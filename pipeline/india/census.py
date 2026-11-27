"""Extract the published district totals from the pinned ORGI A-01 workbook."""

import argparse
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pipeline.core.store import save_interim

SOURCE = "https://censusindia.gov.in/nada/index.php/catalog/42526"
WORKBOOK = SOURCE + "/download/46152/A-1_NO_OF_VILLAGES_TOWNS_HOUSEHOLDS_POPULATION_AND_AREA.xlsx"
CHECKSUM = "6b649697ed5993da834b674173dab68e1ef9abb97e234155a80884c2fa4584f5"


def read_rows(book):
    strings = [
        "".join(part.text or "" for part in item.findall(".//{*}t"))
        for item in ET.fromstring(book.read("xl/sharedStrings.xml"))
    ]
    with book.open("xl/worksheets/sheet1.xml") as sheet:
        for _, row in ET.iterparse(sheet, events=("end",)):
            if not row.tag.endswith("}row"):
                continue
            cells = {}
            for cell in row:
                value = cell.findtext("{*}v")
                if value is not None:
                    column = cell.attrib["r"].rstrip("0123456789")
                    cells[column] = strings[int(value)] if cell.get("t") == "s" else value
            yield int(row.attrib["r"]), cells
            row.clear()


def number(value):
    if value is None or value.strip() in {"", "-", "–", "NA"}:
        return None
    result = Decimal(value)
    if not result.is_finite() or result < 0:
        raise ValueError(f"Invalid Census measure {value!r}")
    return result


def load_districts(path):
    digest = sha256(path.read_bytes()).hexdigest()
    if digest != CHECKSUM:
        raise ValueError(f"Unexpected A-01 workbook SHA-256: {digest}")
    districts = {}
    with ZipFile(path) as book:
        for row, cells in read_rows(book):
            if cells.get("D") != "DISTRICT" or cells.get("F") != "Total":
                continue
            code = f"{cells['A']}-{cells['B']}"
            if not re.fullmatch(r"\d{2}-\d{3}", code) or code in districts:
                raise ValueError(f"Invalid or duplicate district ID {code} on row {row}")
            population = number(cells.get("K"))
            area = number(cells.get("N"))
            density = number(cells.get("O"))
            districts[code] = {
                "name": cells["E"],
                "population": int(population) if population is not None else None,
                "area_km2": float(area) if area is not None else None,
                "people_per_km2": int(density) if area and density is not None else None,
                "workbook_row": row,
            }
    if len(districts) != 640:
        raise ValueError(f"Expected 640 district totals, found {len(districts)}")
    return {
        "publisher": "Office of the Registrar General & Census Commissioner, India",
        "table": "PC11_A01",
        "source": SOURCE,
        "download": WORKBOOK,
        "sha256": digest,
        "sheet": "Sheet1",
        "geography": "census-2011",
        "districts": districts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    args = parser.parse_args()
    save_interim("census_a01", load_districts(args.workbook), vintage="Census of India 2011, table A-01")
