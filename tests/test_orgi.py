from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pipeline.india.orgi import Workbook, area_code, group_rows


class OrgiTests(unittest.TestCase):
    def test_checks_bytes_before_opening_workbook(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.xls"
            path.write_bytes(b"unexpected")
            book = Workbook("sample.xls", sha256(b"pinned").hexdigest(), "T")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                list(book.rows(path))

    def test_normalizes_numeric_and_text_area_codes(self):
        self.assertEqual(area_code("01", 3.0), "01-003")
        self.assertEqual(area_code(28, "000"), "28-000")
        with self.assertRaises(ValueError):
            area_code(1, 3.5)

    def test_keeps_residence_and_historic_state_in_the_key(self):
        rows = [("title",), ("T", 28, 532, "Urban", "count", 9)]
        self.assertEqual(
            group_rows(rows, "T", residence=3, category=4, columns=(5,)),
            {("28-532", "Urban"): {"count": (9,)}},
        )

    def test_rejects_duplicate_area_residence_category(self):
        row = ("T", "01", "003", "Total", "count", 0)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            group_rows([row, row], "T", residence=3, category=4, columns=(5,))

    def test_keeps_missing_counts_distinct_from_zero(self):
        row = ("T", "01", "003", "Total", "count", "-", 0)
        self.assertEqual(
            group_rows([row], "T", residence=3, category=4, columns=(5, 6)),
            {("01-003", "Total"): {"count": (None, 0)}},
        )
