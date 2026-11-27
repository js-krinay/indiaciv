import tempfile
import unittest
from pathlib import Path

from pipeline.india.transport import airport_rows, is_civil_airport, line_class, port_name


class CivilAirportTests(unittest.TestCase):
    def test_requires_a_verified_civil_airport(self):
        row = {"name": "Civil Airport", "iata": "DEL", "size": "large"}
        self.assertTrue(is_civil_airport(row))
        self.assertFalse(is_civil_airport({**row, "iata": None}))
        self.assertFalse(is_civil_airport({**row, "iata": "ZZZ"}))

    def test_excludes_military_names_types_and_keywords(self):
        row = {"name": "Civil Airport", "iata": "DEL", "size": "large"}
        for details in ({"name": "Example AFS"}, {"name": "Example Naval Air Station"},
                        {"keywords": "Civil terminal, Army"}, {"type": "military_airport"}):
            with self.subTest(details=details):
                self.assertFalse(is_civil_airport({**row, **details}))

    def test_civil_airport_municipalities_come_from_the_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "airports.csv"
            path.write_text(
                "id,name,iata_code,type,iso_country,municipality,scheduled_service,longitude_deg,latitude_deg\n"
                "1,Test Airport,BOM,large_airport,IN,Mumbai,yes,72.8,19.1\n"
                "2,Test Airport,GOX,large_airport,IN,Naval Station,yes,73.9,15.7\n"
            )
            civilian, filtered = list(airport_rows(path))
        self.assertEqual(civilian["city"], "Mumbai")
        self.assertIsNone(filtered["city"])

    def test_transport_features_require_public_civilian_tags(self):
        port = {"industrial": "port", "name": "Example Harbour"}
        self.assertEqual(port_name(port), "Example Harbour")
        self.assertIsNone(port_name({**port, "seamark:harbour:category": "naval"}))
        self.assertIsNone(port_name({**port, "access": "private"}))
        self.assertIsNone(line_class({"railway": "rail", "usage": "military"}))
