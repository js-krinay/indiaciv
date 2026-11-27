import unittest
from importlib.util import find_spec
from unittest.mock import patch

try:
    import numpy as np
    import rasterio
except ImportError:
    rasterio = None


@unittest.skipIf(rasterio is None, "requires rasterio")
class NativeRasterTests(unittest.TestCase):
    def test_sampling_reads_native_pixel_when_overview_differs(self):
        from rasterio.enums import Resampling
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        from pipeline.india.terrain import native_samples

        pixels = np.full((32, 32), 5, dtype=np.uint8)
        pixels[1, 1] = 7
        with MemoryFile() as fixture:
            with fixture.open(driver="GTiff", width=32, height=32, count=1, dtype="uint8",
                              transform=from_origin(0, 32, 1, 1)) as dataset:
                dataset.write(pixels, 1)
                dataset.build_overviews([4], Resampling.mode)
                self.assertEqual(dataset.read(1, out_shape=(8, 8))[0, 0], 5)
                self.assertEqual(native_samples(dataset, [("hex", 1.5, 30.5)]), [("hex", 7)])

    @unittest.skipUnless(find_spec("tifffile"), "requires tifffile")
    def test_range_reader_fetches_only_blocks_occupied_by_points(self):
        from rasterio.io import MemoryFile
        from rasterio.transform import from_origin
        from pipeline.india.native_cog import read_cog
        from pipeline.india.terrain import native_samples

        pixels = np.full((1024, 1024), 5, dtype=np.uint8)
        pixels[1000, 1000] = 7
        with MemoryFile() as fixture:
            options = dict(driver="GTiff", width=1024, height=1024, count=1, dtype="uint8",
                           crs="EPSG:4326", transform=from_origin(70, 24, .001, .001),
                           tiled=True, blockxsize=128, blockysize=128)
            with fixture.open(**options) as dataset:
                dataset.write(pixels, 1)
            source = fixture.getbuffer()
            def fetch(url, start, stop):
                return start, len(source), bytes(source[start:stop])
            with patch("pipeline.india.native_cog.fetch_range", side_effect=fetch) as ranges:
                samples, downloaded = read_cog("fixture", [("hex", 71.0005, 22.9995)], native_samples)
            self.assertEqual(samples, [("hex", 7)])
            self.assertEqual(ranges.call_count, 2)
            self.assertLess(downloaded, len(source) * .6)
