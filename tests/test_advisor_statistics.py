import unittest
from pathlib import Path

from pipeline.__main__ import helper_files
from pipeline.build import states
from pipeline.build.advisor_statistics import civic_offices_in_footprint, national_statistics, veteran_estimate
from pipeline.india import advisor_sources
from pipeline.india.city_labour import broad_industry


class AdvisorStatisticsTests(unittest.TestCase):
    def test_curated_source_updates_invalidate_state_build(self):
        self.assertIn(Path(advisor_sources.__file__), helper_files(Path(states.__file__)))

    def test_national_budget_and_civic_roster_reconcile(self):
        stats = national_statistics({}, 1_400_000_000, 340_000_000_000_000)
        self.assertEqual(stats["cantonment_boards"], 61)
        budget = stats["defence_budget"]
        self.assertAlmostEqual(sum(budget["heads"].values()), budget["total"], places=2)
        self.assertEqual(stats["veterans"]["coverage"], 32)
        self.assertAlmostEqual(stats["defence_budget_per_resident"]["value"], 4865.78764, places=5)
        self.assertAlmostEqual(stats["defence_budget_share_gdp"]["value"], 0.020035596, places=8)

    def test_civic_offices_require_verified_footprint_membership(self):
        offices = [{"x": 1, "y": 1, "name": "Inside"}, {"x": 3, "y": 3, "name": "Outside"}]
        rings = [[(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]]
        self.assertEqual(civic_offices_in_footprint(offices, rings), ["Inside"])
        self.assertIsNone(civic_offices_in_footprint(offices, []))
        self.assertIsNone(civic_offices_in_footprint(offices[1:], rings))

    def test_carries_forward_matching_registration_counts(self):
        self.assertEqual(veteran_estimate(78148, 80878), 83608)
        self.assertIsNone(veteran_estimate(100, None))
        self.assertIsNone(veteran_estimate(100, 40))

    def test_reads_combined_persons_and_preserves_published_rounding(self):
        page = """Table (4): Percentage distribution
rural+urban             person$    July-September 2026
Andhra Pradesh  37.6 24.6 37.7 100.0
all-India       41.7 24.7 33.5 100.0"""
        rows = broad_industry(page, expected_states=1)
        self.assertEqual(rows, {"AP": [37.6, 24.6, 37.7], "IN": [41.7, 24.7, 33.5]})
