import math
import unittest

from pipeline.core.geo import Laea, MapProjection
from pipeline.core.hexgrid import SQRT3, HexGrid

# lon/lat → km from pyproj "+proj=laea +lat_0=22 +lon_0=82 +datum=WGS84" (independent reference).
PYPROJ = [
    ((82, 22), (0.0, 0.0)),
    ((72.8777, 19.076), (-958.9562, -296.1004)),
    ((77.209, 28.6139), (-469.1662, 740.0706)),
    ((93.7, 6.8), (1301.8340, -1635.6568)),
    ((74.8, 34.1), (-667.4894, 1356.0495)),
    ((68.1, 23.7), (-1412.7531, 253.5757)),
    ((97.4, 28.2), (1507.2896, 767.4585)),
]


class LaeaTest(unittest.TestCase):
    def test_matches_pyproj_within_a_metre(self):
        laea = Laea()
        for (lon, lat), (x, y) in PYPROJ:
            gx, gy = laea(lon, lat)
            self.assertLess(math.hypot(gx - x, gy - y), 0.001, (lon, lat))


class MapProjectionTest(unittest.TestCase):
    def test_flips_y_and_shifts_to_the_top_left(self):
        proj = MapProjection(min_x=-1500.0, max_y=1700.0, margin=200.0)
        x, y = proj(82, 22)
        self.assertAlmostEqual(x, 1700.0, places=6)
        self.assertAlmostEqual(y, 1900.0, places=6)
        _, y_north = proj(77.209, 28.6139)
        self.assertLess(y_north, y)  # north is up: smaller y

    def test_hex_aligned_projection_puts_axial_centres_on_grid_centres(self):
        radius = 18.0
        proj = MapProjection.hex_aligned(-1405.8, 1685.6, 200.0, radius)
        grid = HexGrid(radius, 200, 200)
        for q, r in [(0, 0), (-41, 42), (12, -7), (3, 5), (-20, -33)]:
            # IndiaCiv's axial grid: centre in projected km, y north.
            ax, ay = SQRT3 * radius * (q + r / 2), 1.5 * radius * r
            mx, my = proj.from_projected(ax, ay)
            cell = grid.cell_at(mx, my)
            self.assertGreaterEqual(cell, 0)
            cx, cy = grid.center(*grid.col_row(cell))
            self.assertLess(math.hypot(cx - mx, cy - my), 1e-6, (q, r))


if __name__ == "__main__":
    unittest.main()
