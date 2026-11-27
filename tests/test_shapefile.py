import struct
import unittest

from pipeline.core.geo import read_shapefile


def shp_bytes(records):
    """A polygon shapefile: records = list of parts lists (each part a list of (x, y)), or None for a null shape."""
    body = b""
    for n, parts in enumerate(records, 1):
        if parts is None:
            content = struct.pack("<i", 0)
        else:
            pts = [p for part in parts for p in part]
            starts, k = [], 0
            for part in parts:
                starts.append(k)
                k += len(part)
            content = struct.pack("<i4d2i", 5, 0, 0, 0, 0, len(parts), len(pts))
            content += struct.pack(f"<{len(parts)}i", *starts) + b"".join(struct.pack("<2d", *p) for p in pts)
        body += struct.pack(">2i", n, len(content) // 2) + content
    header = struct.pack(">7i", 9994, 0, 0, 0, 0, 0, (100 + len(body)) // 2) + struct.pack("<2i8d", 1000, 5, *[0.0] * 8)
    return header + body


def dbf_bytes(fields, rows):
    """fields = [(name, length)] (character fields); rows = list of tuples of str."""
    rlen = 1 + sum(ln for _, ln in fields)
    hlen = 32 + 32 * len(fields) + 1
    out = struct.pack("<4BIHH20x", 3, 126, 1, 1, len(rows), hlen, rlen)
    for name, ln in fields:
        out += name.encode().ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([ln]) + b"\0" * 15
    out += b"\r"
    for row in rows:
        out += b" " + b"".join(str(v).encode().ljust(ln) for v, (_, ln) in zip(row, fields))
    return out + b"\x1a"


class ReadShapefileTest(unittest.TestCase):
    def test_reads_polygon_parts_and_their_attributes(self):
        square = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
        hole = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.2)]
        island = [(5.0, 5.0), (5.0, 6.0), (6.0, 6.0), (5.0, 5.0)]
        shp = shp_bytes([[square, hole], [island], None])
        dbf = dbf_bytes([("ST_NM", 12), ("CODE", 3)], [("Goa", "30"), ("Lakshadweep", "31"), ("Empty", "0")])
        got = list(read_shapefile(shp, dbf))
        self.assertEqual([props for props, _ in got], [{"ST_NM": "Goa", "CODE": "30"}, {"ST_NM": "Lakshadweep", "CODE": "31"},
                                                        {"ST_NM": "Empty", "CODE": "0"}])
        self.assertEqual(got[0][1], [square, hole])
        self.assertEqual(got[1][1], [island])
        self.assertEqual(got[2][1], [])

    def test_rejects_a_file_that_is_not_a_shapefile(self):
        with self.assertRaises(ValueError):
            list(read_shapefile(b"\0" * 100, dbf_bytes([("A", 1)], [])))


if __name__ == "__main__":
    unittest.main()
