"""Stable pointy-top hex grid in India-centered WGS 84 Lambert equal-area metres."""

from math import cos, pi, sin, sqrt

CRS = "+proj=laea +lat_0=22 +lon_0=82 +datum=WGS84 +units=m +no_defs +type=crs"
RADIUS_METRES = 18_000
# Fixed phase of the national grid, in Lambert metres east and north.
ORIGIN_X, ORIGIN_Y = -4_000, -4_000
CELL_AREA_KM2 = 3 * sqrt(3) / 2 * (RADIUS_METRES / 1000) ** 2


def center(q, r):
    """Return the projected coordinates at the center of an axial cell."""
    return (
        ORIGIN_X + sqrt(3) * RADIUS_METRES * (q + r / 2),
        ORIGIN_Y + 1.5 * RADIUS_METRES * r,
    )


def vertices(q, r):
    x, y = center(q, r)
    return tuple(
        (
            x + RADIUS_METRES * cos(angle),
            y + RADIUS_METRES * sin(angle),
        )
        for angle in (pi / 6 + i * pi / 3 for i in range(6))
    )


def cell_at(x, y):
    """Return axial indices for a point already transformed into the grid CRS."""
    x, y = x - ORIGIN_X, y - ORIGIN_Y
    q = (sqrt(3) * x / 3 - y / 3) / RADIUS_METRES
    r = 2 * y / (3 * RADIUS_METRES)
    s = -q - r
    rounded_q, rounded_r, rounded_s = round(q), round(r), round(s)
    errors = abs(rounded_q - q), abs(rounded_r - r), abs(rounded_s - s)
    largest = errors.index(max(errors))
    if largest == 0:
        rounded_q = -rounded_r - rounded_s
    elif largest == 1:
        rounded_r = -rounded_q - rounded_s
    return rounded_q, rounded_r
