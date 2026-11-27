"""Stage only required native GeoTIFF blocks in a local sparse file."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

from tifffile import TiffFile

import rasterio
from pyproj import Transformer

HEADER_BYTES = 512 * 1024
MAX_GAP = 8192
MAX_RANGE = 1024 * 1024


def fetch_range(url, start, stop):
    for attempt in range(3):
        try:
            request = Request(url, headers={"Range": f"bytes={start}-{stop - 1}"})
            with urlopen(request, timeout=45) as response:
                bounds = response.headers.get("Content-Range", "")
                if response.status != 206 or not bounds.startswith(f"bytes {start}-"):
                    raise OSError(f"Source did not serve a byte range: {url}")
                interval, size = bounds.removeprefix("bytes ").split("/")
                total = int(size)
                expected = min(stop, total)
                if interval != f"{start}-{expected - 1}":
                    raise OSError(f"Unexpected range {bounds}: {url}")
                data = response.read()
                if len(data) != expected - start:
                    raise OSError(f"Incomplete raster range: {url}")
                return start, total, data
        except (OSError, HTTPException):
            if attempt == 2:
                raise


def coalesce(blocks, header):
    spans = []
    for offset, length in sorted(set(blocks)):
        end = offset + length
        start = max(offset, header)
        if end <= start:
            continue
        if spans and start <= spans[-1][1] + MAX_GAP and end - spans[-1][0] <= MAX_RANGE:
            spans[-1] = (spans[-1][0], max(spans[-1][1], end))
        else:
            spans.append((start, end))
    return spans


def read_cog(url, points, native_samples):
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "source.tif"
        _, size, header = fetch_range(url, 0, HEADER_BYTES)
        with path.open("wb") as target:
            target.write(header)
            target.truncate(size)
        with rasterio.open(path) as dataset:
            transform = Transformer.from_crs("EPSG:4326", dataset.crs, always_xy=True)
            projected = [(cell, *transform.transform(lon, lat)) for cell, lon, lat in points]
            indices = [dataset.index(x, y) for _, x, y in projected]
            height, width = dataset.height, dataset.width
        with TiffFile(path) as tif:
            page = tif.pages[0]
            pages = [page, *(p for p in tif.pages if p.is_mask and p.shape == page.shape)]
            intervals = []
            for band in pages:
                vertical, horizontal = band.tilelength, band.tilewidth
                per_row = (width + horizontal - 1) // horizontal
                blocks = {row // vertical * per_row + col // horizontal
                          for row, col in indices if 0 <= row < height and 0 <= col < width}
                intervals.extend((band.dataoffsets[i], band.databytecounts[i]) for i in blocks)
        downloaded = len(header)
        with path.open("r+b") as target, ThreadPoolExecutor(max_workers=6) as workers:
            reads = {workers.submit(fetch_range, url, *span) for span in coalesce(intervals, len(header))}
            for read in as_completed(reads):
                offset, _, data = read.result()
                reads.remove(read)
                target.seek(offset)
                target.write(data)
                downloaded += len(data)
        with rasterio.open(path) as dataset:
            return native_samples(dataset, projected), downloaded
