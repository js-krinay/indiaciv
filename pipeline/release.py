"""Stage the India entry point and its audited runtime dependencies."""

import gzip
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from .core.paths import ROOT
from .release_graph import checked_input, dependency_graph, local_path

# The templated data loader cannot enumerate its inputs from URL syntax.
# Seed the graph with the audited public build outputs, never the whole data directory.
PUBLIC_DATA = (
    "data/advisor_tables.json",
    "data/almanac.json",
    "data/cities.json",
    "data/citizens.json",
    "data/city_view.json",
    "data/counties.json",
    "data/disasters.json",
    "data/districts.json",
    "data/infrastructure.json",
    "data/trade.json",
    "data/lens_catalog.json",
    "data/lenses.json",
    "data/military.json",
    "data/nation.json",
    "data/protected_land.json",
    "data/protected_ramsar.json",
    "data/resources.json",
    "data/sources.json",
    "data/states.json",
    "data/wonders.json",
    "data/workplace.json",
    "data/world.json",
)
ENTRY_ASSETS = ("index.html", "favicon.svg", "social-preview.png")


def release(out_dir: Path, *, root: Path = ROOT) -> tuple[int, int]:
    """Write a clean package and return its raw and per-file gzip byte counts."""
    if out_dir.is_symlink() or out_dir.exists():
        raise FileExistsError(f"Release destination already exists: {out_dir}")
    web = root / "web"
    names = dependency_graph(web, (*ENTRY_ASSETS, *PUBLIC_DATA))
    catalogue = checked_input(web, "data/sources.json")
    downloads = []
    for entry in json.loads(catalogue.read_text(encoding="utf-8")):
        if ref := entry.get("download_path"):
            name = local_path(ref, "index.html")
            if name is None or not name.startswith("data/"):
                raise ValueError(f"Unexpected catalogue download: {ref}")
            downloads.append(name)
    names.update(dependency_graph(web, downloads))
    inputs = [(name, web / name) for name in sorted(names)]
    licence = root / "LICENSE"
    if licence.is_symlink():
        raise ValueError(f"Unexpected release input: {licence}")
    if not licence.is_file():
        raise FileNotFoundError(f"Missing release input: {licence}")
    inputs.append(("LICENSE", licence))

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    raw = compressed = 0
    with TemporaryDirectory(dir=out_dir.parent) as staging:
        package = Path(staging) / "site"
        for name, source in inputs:
            target = package / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            contents = target.read_bytes()
            raw += len(contents)
            compressed += len(gzip.compress(contents, mtime=0))
        package.rename(out_dir)
    return raw, compressed
