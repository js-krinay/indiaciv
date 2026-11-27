import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from pipeline.release import release
from pipeline.release_graph import dependency_graph, javascript_imports
from pipeline.build.air_weather import monsoon_band
from pipeline.build.catalog import release_credits
from pipeline.build.yields import culture, production
from pipeline.core.paths import INTERIM, WEB, WEB_DATA
from pipeline.core.source import ODBL_URL
from pipeline.core.store import load_interim


class ReleaseTests(unittest.TestCase):
    def test_india_trailer_is_a_dev_only_page(self):
        page = (WEB / "dev/trailer.html").read_text()
        self.assertIn("<title>IndiaCiv trailer", page)
        self.assertIn('<meta name="robots" content="noindex">', page)

    def test_release_javascript_has_no_local_paths(self):
        local_path = re.compile(
            r"(?:/(?:Users|home|tmp|private)/|[A-Za-z]:\\(?:Users|Temp)\\|"
            r"\bweb/dev/|\bdata/(?:raw|interim)/|\.cache/|\btmp/issues/|\.local\.json\b)"
        )
        hits = [(name, number) for name in dependency_graph(WEB, ["index.html"]) if name.endswith(".js")
                for number, line in enumerate((WEB / name).read_text().splitlines(), 1)
                if local_path.search(line)]
        self.assertEqual(hits, [])

    def test_public_population_and_density_reconstruct_only_mapped_area(self):
        public = WEB_DATA / "lenses.json"
        if not public.exists() or not (INTERIM / "census_a01.json").exists():
            self.skipTest("Build district lenses with the prepared Census input first")
        districts = json.loads(public.read_text())["places"]["counties"]
        census = load_interim("census_a01")["districts"]
        leaked = []
        inconsistent = []
        for geoid, row in districts.items():
            if not row["population"] or not row["density"]:
                continue
            recovered = round(round(row["population"] / row["density"], 1))
            mapped = round(row["area_km2"])
            if recovered != mapped:
                inconsistent.append(geoid)
                if recovered == census[geoid]["area_km2"]:
                    leaked.append(geoid)
        self.assertEqual(leaked, [], "Census areas recoverable independently of DataMeet")
        self.assertEqual(inconsistent, [], "Density does not use the published mapped area")

    def test_odbl_credit_allows_intermediary_publisher(self):
        entry = release_credits({"id": "wonders_osm", "license": "ODbL 1.0",
                                 "publisher": "OpenStreetMap contributors via Mapcarta"})
        self.assertEqual(entry["license_url"], ODBL_URL)
        self.assertEqual(entry["publisher"], "© OpenStreetMap contributors via Mapcarta")

    def test_graph_follows_imports_and_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            web = Path(directory)
            files = {
                "index.html": "<script src=main.js></script><link rel=stylesheet href=css/main.css>",
                "main.js": """import {
                    one
                } from "./one.js";
                export * from "./two.js";
                import(/* lazy */ "./lazy.js");
                import "./side.js";
                fetch("data/map.json");
                new URL("./asset.svg", import.meta.url);
                // import(computed)
                const text = 'import("./ignored.js")';
                """,
                "one.js": "export { value } from './two.js';",
                "two.js": "", "lazy.js": "", "side.js": "",
                "asset.svg": "", "data/map.json": "{}",
                "css/main.css": '@import "other.css"; @import url(extra.css); div { background: url(../asset.svg) }',
                "css/other.css": "/* url(ignored.svg) */",
                "css/extra.css": "",
            }
            for name, value in files.items():
                path = web / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value)
            (web / "unused.js").touch()
            self.assertEqual(dependency_graph(web, ["index.html"]), set(files))

    def test_graph_rejects_computed_imports_and_private_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            web = Path(directory)
            path = web / "main.js"
            for code, error in (
                ('import("./" + name)', "Computed dynamic import.*main.js"),
                ('import("./dev/example.js")', "Excluded.*dev/example.js"),
                ('fetch("data/raw/source.json")', "Excluded.*data/raw/source.json"),
                ('fetch("data/soi_boundary_chart.json")', "Excluded.*soi_boundary_chart.json"),
                ('fetch(".cache/input.json")', "Excluded.*cache/input.json"),
                ('import("../outside.js")', "Outside.*outside.js"),
            ):
                with self.subTest(code=code):
                    path.write_text(code)
                    with self.assertRaisesRegex(ValueError, error):
                        dependency_graph(web, ["main.js"])

    def test_staged_release_resolves_every_import(self):
        if not (WEB_DATA / "world.json").exists():
            self.skipTest("Build the India atlas first")
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "release"
            release(out)
            self.assertTrue((out / "js/ui/wonderFacts.js").is_file())
            self.assertFalse((out / "dev").exists())
            self.assertFalse((out / "js/ext/cityView/screen.js").exists())
            for script in out.rglob("*.js"):
                name = script.relative_to(out).as_posix()
                for ref in javascript_imports(script.read_text(), name):
                    self.assertTrue((script.parent / ref.split("?")[0]).is_file(), (name, ref))
            with self.assertRaises(FileExistsError):
                release(out)

    def test_staged_release_loads_in_chrome(self):
        if not (WEB_DATA / "world.json").exists() or not shutil.which("node"):
            self.skipTest("Build the India atlas and install Node to run the Chrome smoke test")

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, _format, *args):
                pass

        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "release"
            release(out)
            handler = partial(QuietHandler, directory=out)
            port = int(os.environ.get("INDIACIV_RELEASE_TEST_PORT", 0))
            with ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
                thread = Thread(target=server.serve_forever)
                thread.start()
                try:
                    browser = subprocess.run(
                        ["node", str(Path(__file__).with_name("release_browser.mjs")),
                         f"http://127.0.0.1:{server.server_port}/"],
                        capture_output=True, text=True, timeout=90,
                    )
                finally:
                    server.shutdown()
                    thread.join()
            if browser.returncode == 77:
                self.skipTest(browser.stdout.strip())
            self.assertEqual(browser.returncode, 0, browser.stdout + browser.stderr)

    def test_missing_input_leaves_no_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "LICENSE").write_text("MIT notice")
            out = root / "release"
            with self.assertRaises(FileNotFoundError):
                release(out, root=root)
            self.assertFalse(out.exists())

    def test_monsoon_uses_broad_bands_instead_of_source_departures(self):
        self.assertEqual([monsoon_band(value) for value in (-61, -59, -20, -19, 19, 20, 59, 60)],
                         [-2, -1, -1, 0, 0, 1, 1, 2])

    def test_yield_scores_do_not_encode_exact_restricted_totals(self):
        self.assertEqual(culture(250_001, 3), culture(250_019, 3))
        self.assertEqual(production(10_001, 1_000, 10), production(10_019, 1_000, 10))
