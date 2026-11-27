"""Pinned source assets for the layered terrain preparation step."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import file_digest
from pathlib import Path
import shutil
import subprocess
from urllib.request import urlopen
from zipfile import ZipFile

FIGSHARE = "https://ndownloader.figshare.com/files/"
NOAA = "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_surface_elev_gtif/"
CORAL = ("https://allencoralatlas.org/geoserver/ows?service=WMS&version=1.1.1&request=GetMap"
         "&layers=coral-atlas:geomorphic_data_verbose&styles=&srs=EPSG:4326")

ARCHIVES = {
    "climate.zip": (FIGSHARE + "61012822", "bb84453d4541f1a0bc5a804ead83f483c19ce70f16a5197f6d3a7b6a63e65562"),
    "flood.rar": (FIGSHARE + "12186356", "2bed88e1dee4b9f1b4077ac124757f53f7241b59573111d6162f7f421f9f7948"),
    "wetlands.zip": (FIGSHARE + "54001814", "5003d9e6603efd5b2e97ab91ef5e4a33c7ada544c73b7fe74d22a08847d88236"),
    "mangroves.zip": ("https://zenodo.org/api/records/6894273/files/gmw_v3_2020_gtiff.zip/content",
                      "97d783a0904fc97738d50bcb3b0a3e2ec0bfc87a2d5d09e349d59a330619f66b"),
}

ELEVATION = {
    "N15E060": "e017c961673fdcaeb361eaed185e7a644971ce3dac340ea6f08653fcaf9fb50a",
    "N15E075": "784b8e820e77574a2efebd219bf9d6b4945511678cbe48cc41cbbe44d23de142",
    "N15E090": "75795dd4a787b996698fe8efa717cd0d06b869dde4cf3c99e9ff3abb58457125",
    "N30E060": "1ef4242fb2369ed6e20db6b4d3e02eba7a76cb3f1c2573f0b9b7daf27fad9182",
    "N30E075": "cbb763175d331ed0222da35f357d3837aa8218aeda72e586974ef2a53f9027d4",
    "N30E090": "1137f43b1420917ed5771aa8cd9acbf9060efa73393d4bc422b7aaca84499df5",
    "N45E060": "ee60a106e40b40f744159519b4bac90df53d718cfda0e731d936842833695586",
    "N45E075": "27cdc5ae5b0851f25de45902a86145c7f22ab49435a79cf1f6ae5f8fdb62be1c",
    "N45E090": "4dd4fd30cd8ee5e7a1608f75e76a8a545c595c45812db5329934e4e1018b97ad",
}
REEFS = {
    "lakshadweep": ("72,8,74,13", 1000, 2500, "86feab5cec92018fbf2edfa353ce400f59d9ae7486cbfee13adcc688cf751b80"),
    "mannar": ("78,8,80.2,10", 1100, 1000, "79f2beca196c74cbd9f972c356a1b55809eb5b18952a92fbc7ce2a27349a5207"),
    "kutch": ("68.2,22,71,23.4", 1400, 700, "d22c8656053eea0c81de9de19124b5871dac84ba9e89cae26876851d8ee17c2e"),
    "andaman": ("92,10.3,94.5,14", 1250, 1850, "e68f034eec4ae6d40fd8fac9f66e105ceeb04997b18b7a8b42778bbfac17108e"),
    "nicobar": ("92,6.5,94,10.3", 1000, 1900, "1dcffbabc3a43ac618235db39c6d54bab82a877cba00d3c1cc874ee285817f46"),
}


def elevation_name(tile):
    return f"ETOPO_2022_v1_15s_{tile}_surface.tif"


def acquire(directory, name, url, expected):
    path = directory / name
    def matches(file):
        with file.open("rb") as stream:
            return file_digest(stream, "sha256").hexdigest() == expected

    if path.exists():
        if not matches(path):
            raise ValueError(f"Checksum mismatch for {path}. Replace it with the pinned asset from {url}")
        return
    temp = path.with_suffix(path.suffix + ".part")
    try:
        with urlopen(url, timeout=90) as source, temp.open("wb") as target:
            shutil.copyfileobj(source, target)
        if not matches(temp):
            raise ValueError(f"Checksum mismatch for {url}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def extract(source, member, output):
    temp = output.with_suffix(output.suffix + ".part")
    try:
        with ZipFile(source) as archive, archive.open(member) as stream, temp.open("wb") as target:
            shutil.copyfileobj(stream, target)
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)


def prepare_assets(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    jobs = dict(ARCHIVES)
    for tile, digest in ELEVATION.items():
        name = elevation_name(tile)
        jobs[name] = (NOAA + name, digest)
    for region, (bounds, width, height, digest) in REEFS.items():
        url = f"{CORAL}&bbox={bounds}&width={width}&height={height}&format=image/png&transparent=true"
        jobs[f"reef-{region}.png"] = (url, digest)
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda item: acquire(directory, item[0], *item[1]), jobs.items()))

    extract(directory / "climate.zip", "1991_2020/koppen_geiger_0p00833333.tif", directory / "climate.tif")
    extract(directory / "wetlands.zip", "GLWD_v2_0_combined_classes/GLWD_v2_0_main_class.tif",
            directory / "wetlands.tif")
    extract(directory / "wetlands.zip", "GLWD_v2_0_combined_classes/GLWD_v2_0_area_pct.tif",
            directory / "wetlands-area.tif")
    asia = directory / "flood-asia.zip"
    # macOS and other bsdtar builds support the source's RAR container.
    try:
        with asia.open("wb") as target:
            subprocess.run(["bsdtar", "-xOf", str(directory / "flood.rar"), "GFPLAIN TIFF/AS.zip"],
                           stdout=target, check=True)
        extract(asia, "AS.TIF", directory / "flood.tif")
    finally:
        asia.unlink(missing_ok=True)
