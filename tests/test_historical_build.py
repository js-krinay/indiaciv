import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import __main__ as cli
from pipeline.build import city_view
from pipeline.india import IFI_SOURCE


class HistoricalBuildTests(unittest.TestCase):
    def test_city_view_becomes_stale_when_flood_interim_is_installed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in city_view.REQUIRES + city_view.PRODUCES:
                path = root / name
                path.touch()
                stamp = 200 if name in city_view.PRODUCES else 100
                os.utime(path, (stamp, stamp))
            with patch.object(cli, "output_path", side_effect=lambda name: root / name):
                with patch.object(cli, "helper_files", return_value=set()):
                    self.assertFalse(cli.is_stale(city_view))
                    (root / IFI_SOURCE).touch()
                    self.assertTrue(cli.is_stale(city_view))
