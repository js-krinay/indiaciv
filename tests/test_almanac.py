import shutil
import subprocess
import unittest
from pathlib import Path


class AlmanacTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is needed to exercise the Almanac")
    def test_index_and_routes(self):
        subprocess.run(
            ["node", "tests/almanac.mjs"],
            cwd=Path(__file__).resolve().parents[1], check=True,
        )
