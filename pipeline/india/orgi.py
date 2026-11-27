"""Read pinned ORGI workbooks and key counts by Census geography."""

from dataclasses import dataclass
from hashlib import file_digest


@dataclass(frozen=True)
class Workbook:
    filename: str
    checksum: str
    table: str

    def rows(self, path):
        """Read cell values across all sheets of a verified XLS or XLSX."""
        with path.open("rb") as content:
            digest = file_digest(content, "sha256").hexdigest()
        if digest != self.checksum:
            raise ValueError(f"Unexpected SHA-256 for {self.filename}: {digest}")
        if path.suffix.lower() == ".xls":
            import xlrd

            book = xlrd.open_workbook(str(path), on_demand=True)
            try:
                for sheet in book.sheets():
                    for row in sheet.get_rows():
                        yield tuple(cell.value for cell in row)
            finally:
                book.release_resources()
        elif path.suffix.lower() == ".xlsx":
            import openpyxl

            book = openpyxl.load_workbook(path, read_only=True, data_only=True)
            try:
                for sheet in book.worksheets:
                    yield from sheet.values
            finally:
                book.close()
        else:
            raise ValueError(f"Unsupported workbook format: {path.suffix}")


def integer(value):
    if isinstance(value, (int, float)) and int(value) == value and value >= 0:
        return int(value)
    if isinstance(value, str) and value.strip().isascii() and value.strip().isdigit():
        return int(value)
    raise ValueError(f"Expected a nonnegative integer, got {value!r}")


def area_code(state, district, *, town=False):
    state = integer(state)
    district = integer(district)
    width = 6 if town else 3
    if state > 99 or district >= 10 ** width:
        raise ValueError(f"Invalid Census area code: {state}, {district}")
    return f"{state:02d}-{district:0{width}d}"


def count(value):
    if value is None or str(value).strip() in {"", "-", "–", "NA"}:
        return None
    return integer(value)


def group_rows(rows, table, *, residence, category, columns, town=False,
               include=lambda row: True, fixed_residence="Total"):
    """Index one table by historic area, residence and published category."""
    groups = {}
    for row in rows:
        if not row or row[0] != table or not include(row):
            continue
        area = area_code(row[1], row[2], town=town)
        scope = str(row[residence]).strip() if residence is not None else fixed_residence
        if scope not in {"Total", "Rural", "Urban"}:
            raise ValueError(f"Invalid residence for {area}: {scope!r}")
        label = str(row[category]).strip() if category is not None else ""
        entries = groups.setdefault((area, scope), {})
        if label in entries:
            raise ValueError(f"Duplicate {table} row for {area}, {scope}, {label}")
        entries[label] = tuple(count(row[column]) for column in columns)
    return groups
