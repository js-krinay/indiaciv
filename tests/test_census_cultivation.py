import unittest

from pipeline.india.census_cultivation import cultivation_share


class CensusCultivationTest(unittest.TestCase):
    def test_share_includes_all_main_and_marginal_workers(self):
        row = dict(TOT_WORK_P=100, MAINWORK_P=80, MARGWORK_P=20, MAIN_CL_P=5, MAIN_AL_P=8,
                   MARG_CL_P=2, MARG_AL_P=5)
        self.assertEqual(cultivation_share(row), 0.2)
