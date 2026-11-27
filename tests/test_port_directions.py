import unittest

from pipeline.india.port_directions import major_port_directions, state_directions


class PortDirectionTests(unittest.TestCase):
    def test_authority_combines_docks_before_dividing_and_excludes_coastal_cargo(self):
        report = (
            "Table 2.1.3\n    SMPA Kolkata Dock System\n"
            "Total 0 0 0 0 0 0 0 0 0 0 0 0 3 1 4 50 50 100\n\f"
            "Table 2.1.3\n    SMPA Haldia Dock Complex\n"
            "Total 0 0 0 0 0 0 0 0 0 0 0 0 1 5 6 50 50 100\n"
        )
        self.assertEqual(major_port_directions(report), {"kolkata": (4, 6)})

    def test_state_joins_matching_overseas_rows_and_uses_last_year(self):
        report = (
            "Table 3.1.3\n GUJARAT\n Overseas 19 60\n Coastal 10 500\n"
            " ODISHA\n Overseas 20 70\n\f"
            "Table 3.1.4\n GUJARAT\n Overseas 2 40\n Coastal 20 900\n"
        )
        self.assertEqual(state_directions(report), {"Gujarat": (60, 40)})
