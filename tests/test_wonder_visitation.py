import unittest

from pipeline.india.wonder_visitation import ticketed_ranks


class WonderVisitationTest(unittest.TestCase):
    def test_rank_uses_both_visitor_classes_in_fiscal_year(self):
        text = (
            "Table 4.2.3: Number of Visitors\n"
            "1  Alpha  200  20  200  50  0  150\n"
            "2  Beta  20  0  180  100  800  -\n"
            "3  Missing  -  -  -  -  -  -\n"
            "Grand Total  220  20  380  150  1  1"
        )
        self.assertEqual(ticketed_ranks(text, 3), ({1: 2, 2: 1}, 2))
