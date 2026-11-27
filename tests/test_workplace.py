import unittest

from pipeline.india.workplace import NIC, combined, industry_metrics, matched_ua, measures, observation, ua_members


class WorkplaceTests(unittest.TestCase):
    def test_restricted_and_mixed_sectors_cannot_change_civilian_scores(self):
        raw = self.source_row()
        mixed = {**raw, "ec13_emp_all": "501500", "ec13_count_all": "10020",
                 "ec13_emp_manuf": "500250", "ec13_emp_shric_72": "500100"}
        reference = observation(measures(raw), measures(raw))
        self.assertEqual(observation(measures(mixed), measures(raw)), reference)
        self.assertEqual(observation(measures(raw), measures(mixed)), reference)
        self.assertEqual(reference["jobs"], 1400)
        self.assertAlmostEqual(reference["manufacturing_share"], 150 / 1400)
        self.assertNotIn("establishments", reference)

    @staticmethod
    def source_row():
        return {**{f"ec13_emp_shric_{group}": "10" for group in NIC},
                "ec13_emp_all": "1500", "ec13_count_all": "20",
                "ec13_emp_manuf": "250", "ec13_emp_shric_72": "100"}

    def test_incomplete_national_numerator_does_not_narrow_the_denominator(self):
        local = self.source_row()
        national = {**local, "ec13_emp_shric_19": ""}
        record = observation(measures(local), measures(national))
        self.assertEqual(record["jobs"], 1400)
        self.assertNotIn("Coke and refined petroleum", record["industries"])
        self.assertEqual(record["industries"]["Electric power"]["lq"], 1)

    def test_pinned_india_workplace_universe(self):
        from pipeline.india.workplace import india_coverage

        self.assertEqual(india_coverage(109_933_023, 101_463_171), (8_469_852, 0.9229544338101209))
        with self.assertRaises(ValueError):
            india_coverage(109_933_023, 101_463_170)

    def test_establishments_are_comparable_only_with_no_excluded_jobs(self):
        raw = self.source_row() | {"ec13_emp_shric_72": "0"}
        record = observation(measures(raw), measures(raw))
        self.assertEqual(record["establishments"], 20)

    def test_missing_component_blocks_metric_and_zero_is_observed(self):
        self.assertEqual(combined([(10, 0), (20, None)], 2), (30, None))

    def test_lq_uses_matching_denominators_and_applies_badge_thresholds(self):
        self.assertEqual(industry_metrics(100, 1000, 200, 4000), {
            "local_share": 0.1, "national_share": 0.05, "lq": 2.0,
            "excess_jobs": 50, "qualifies": True,
        })
        self.assertIsNone(industry_metrics(None, 1000, 200, 4000))
        self.assertFalse(industry_metrics(10, 1000, 20, 4000)["qualifies"])

    def test_ua_uses_leaf_components_and_keeps_outgrowths(self):
        rows = [
            {"A": "01", "E": "123000000", "F": "Sample UA", "G": "0"},
            {"D": "800001", "E": "123000100", "G": "1"},
            {"D": "800001", "E": "123000101", "G": "2"},
            {"D": "000002", "E": "123000102", "G": "2"},
            {"D": "800003", "E": "123000200", "G": "1"},
        ]
        self.assertEqual(ua_members(rows), {
            ("01", "sample"): {"800001", "000002", "800003"},
        })

    def test_ua_counts_a_shared_shrid_once_only_when_all_owners_belong(self):
        keys = {"town": {"shared"}, "outgrowth": {"shared"}}
        owners = {"shared": {"town", "outgrowth"}}
        self.assertEqual(matched_ua({"town", "outgrowth"}, keys, owners, {"shared": (10, 3)}), (10, 3))
        self.assertIsNone(matched_ua({"town"}, keys, owners, {"shared": (10, 3)}))
