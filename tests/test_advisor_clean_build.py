import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pipeline.__main__ import cmd_build
from pipeline.build import BUILDERS


class AdvisorCleanBuildTests(unittest.TestCase):
    def test_clean_build_materializes_advisor_inputs_before_reading_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = {output for module in BUILDERS.values() for output in module.PRODUCES}

            def build(module):
                for required in module.REQUIRES:
                    if required in outputs:
                        self.assertTrue((root / required).exists(), required)
                for output in module.PRODUCES:
                    (root / output).touch()

            builders = {
                name: SimpleNamespace(REQUIRES=module.REQUIRES, PRODUCES=module.PRODUCES,
                                      build=lambda module=module: build(module))
                for name, module in BUILDERS.items()
            }
            cmd_build(["advisor_tables"], force=True, with_deps=True, builders=builders)
            self.assertTrue((root / "advisor_tables.json").exists())
