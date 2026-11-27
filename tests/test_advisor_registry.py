import shutil
import subprocess
import unittest
from pathlib import Path


class AdvisorRegistryTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is needed to exercise the browser registry")
    def test_registry_and_geography_joins(self):
        subprocess.run(
            ["node", "tests/advisor_registry.mjs"],
            cwd=Path(__file__).resolve().parents[1], check=True,
        )
