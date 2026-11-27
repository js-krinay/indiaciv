import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from pipeline.build import catalog
from pipeline.build.advisor_statistics import national_statistics
from pipeline.build.state_metrics import civic_metrics, definitions
from pipeline.india.civic_sources import ABHA_PER_100, PMAYG_PER_1000, PMAYU2_PER_1000, PMJAY_PER_100, SOURCES
from pipeline.india.explorer_sources import INTERNET_SOURCE


class CivicMetricsTests(unittest.TestCase):
    def test_internet_uses_existing_derived_rates_with_projection_credit(self):
        metrics = civic_metrics("OD")
        self.assertEqual(metrics["internet_per_100"]["value"], 69.7)
        self.assertTrue(metrics["internet_per_100"]["estimated"])
        self.assertEqual(definitions()["internet_per_100"]["period_end"], "2026-06-30")

    def test_scheme_completions_use_total_population_and_preserve_zero(self):
        self.assertEqual(civic_metrics("BR")["pmayg_completions"]["value"], 31.672)
        self.assertEqual(civic_metrics("TS")["pmayg_completions"]["value"], 0)
        self.assertNotIn("pmayg_completions", civic_metrics("DL"))

    def test_national_poverty_is_a_nowcast_at_an_explicit_line(self):
        stats = national_statistics({}, 1_400_000_000, None)
        poverty = stats["poverty_nowcast"]
        self.assertAlmostEqual(poverty["value"], 0.01395)
        self.assertEqual(poverty["line"], "$3.00 per person per day (PPP)")
        self.assertTrue(poverty["estimated"])

    def test_scheme_coverage_and_phase_totals(self):
        self.assertEqual(len(ABHA_PER_100), 37)
        self.assertEqual(len(PMAYG_PER_1000), 34)
        self.assertEqual(len(PMAYU2_PER_1000), 34)
        self.assertEqual(len(PMJAY_PER_100), 15)
        self.assertNotIn("pmjay_cards", civic_metrics("IN"))
        self.assertEqual(civic_metrics("UP")["pmjay_cards"]["value"], 25.2)

    def test_catalog_cites_curated_snapshots_without_interims(self):
        with TemporaryDirectory() as folder, patch.object(catalog, "WEB_DATA", Path(folder)), \
             patch.object(catalog, "load_interim_payload", side_effect=FileNotFoundError), \
             patch.object(catalog, "read_manifest", return_value={}), patch.object(catalog, "write_web") as write:
            catalog.build()
        entries = {entry["id"] for entry in write.call_args.args[1]}
        self.assertTrue({INTERNET_SOURCE, *(source.id for source in SOURCES)} <= entries)
