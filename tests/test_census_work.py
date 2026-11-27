import unittest

from pipeline.india.census_work import index_rows, industry_family, join_occupations, observation, occupation_family, partition


class CensusWorkTest(unittest.TestCase):
    def test_occupation_excludes_sensitive_jobs_and_preserves_residual(self):
        def row(code, total, urban):
            return ("B0425A", "27", "001", "", *code, "", total, None, None,
                    total - urban, None, None, urban)
        rows = [
            row(("0", "00", "000", "0000"), 100, 60),
            row(("2", "21", "214", "0000"), 40, 30),
            row(("2", "21", "214", "2141"), 40, 30),
            row(("5", "51", "516", "0000"), 20, 10),
            row(("5", "51", "516", "5162"), 18, 9),
        ]
        indexed = index_rows("main", rows)
        record = observation("occupations", partition("occupations", indexed)["27-001", "Urban"])
        self.assertEqual({key: share for key, share in record["values"].items() if share},
                         {"engineer": .6, "other": .4})
        self.assertEqual((record["vintage"], record["period"]), ("older", "Census 2011"))
        self.assertIsNone(occupation_family(("8", "82", "822", "8222")))

    def test_industry_civilian_groups_and_mixed_codes(self):
        self.assertEqual(industry_family(("84", "841", "8411")), "public_admin")
        self.assertIsNone(industry_family(("84", "842", "8421")))
        self.assertIsNone(industry_family(("25", "252", "2520")))
        self.assertIsNone(industry_family(("45", "451", "4510")))
        self.assertEqual(industry_family(("46", "461", "4610")), "wholesale")

    def test_benchmark_requires_overrepresentation_and_ignores_excluded_counts(self):
        from collections import Counter
        from pipeline.build.city_view import valid_census_work

        local = Counter(published=1100, engineer=200, other=800, excluded=100)
        urban_india = Counter(published=1000, engineer=100, other=900)
        record = observation("occupations", local, urban_india)
        self.assertEqual(record["specialist"], {"family": "engineer", "ratio": 2})
        self.assertTrue(valid_census_work({"occupations": record}))
        record["values"]["defence"] = 0
        self.assertFalse(valid_census_work({"occupations": record}))

    def test_join_matches_codes_and_keeps_sparse_detail(self):
        main = {"27-001": {(): (10, 6, 4), ("1",): (4, 2, 2)}}
        marginal = {"27-001": {(): (5, 3, 2), ("1",): (2, 1, 1), ("4",): (1, 0, 1)}}
        joined = join_occupations(main, marginal)
        counts = partition("occupations", joined)["27-001", "Urban"]
        self.assertEqual(counts, {"published": 6, "executive": 3, "clerk": 1, "other": 2})

    def test_mixed_classes_are_removed_from_mumbai_shares(self):
        def row(division, group, detail, main, marginal=0):
            return ("B0118", "27", "517", "", division, group, detail, "",
                    main, 0, 0, 0, 0, 0, main, 0, 0, marginal, 0, 0, 0, 0, 0, marginal)

        rows = [row("00", "000", "0000", 8_408_520),
                row("85", "000", "0000", 260_000, 17_058),
                row("30", "000", "0000", 11_260),
                row("30", "301", "0000", 8_000),
                row("30", "301", "3011", 8_000),
                row("30", "303", "0000", 3_260),
                row("30", "303", "3030", 3_260)]
        counts = partition("industries", index_rows("industry", rows))["27-517", "Urban"]
        self.assertEqual(counts["excluded"], 11_260)
        self.assertEqual(observation("industries", counts)["values"]["education"],
                         round(277_058 / 8_397_260, 7))
        for code in ("2029", "2520", "2829", "3011", "3030", "3040", "8422"):
            with self.subTest(code=code):
                self.assertIsNone(industry_family((code[:2], code[:3], code)))

    def test_hospitals_and_specialist_retail_remain_in_the_civilian_mix(self):
        self.assertEqual(industry_family(("86", "861", "8610")), "health")
        self.assertEqual(industry_family(("47", "477", "4773")), "retail")

    def test_occupation_families_cover_professionals_repair_and_transport(self):
        for group, expected in (("242", "scholar"), ("245", "scholar"), ("724", "builder"),
                                ("833", "maker"), ("834", "maker"), ("933", "maker")):
            with self.subTest(group=group):
                self.assertEqual(occupation_family((group[0], group[:2], group)), expected)
