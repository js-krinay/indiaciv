"""Lossless JSON encoding for numeric lens grids."""

import json
import math
from itertools import groupby


def encode(values):
    runs = []
    gap = 0
    for value, cells in groupby(values):
        length = sum(1 for _ in cells)
        if value is None:
            gap += length
        else:
            runs.extend((gap, length, value))
            gap = 0
    packed = {"runs": runs}
    size = lambda value: len(json.dumps(value, separators=(",", ":")))
    return min((values, packed), key=size)


def decode(encoded, size):
    """Expand sparse runs, leaving unlisted cells null. Accept legacy dense arrays."""
    if isinstance(encoded, list):
        if len(encoded) != size:
            raise ValueError(f"expected {size} values, got {len(encoded)}")
        return encoded
    runs = encoded.get("runs") if isinstance(encoded, dict) else None
    if not isinstance(runs, list) or len(runs) % 3:
        raise ValueError("expected a flat array of gap, length, value triples")
    values = [None] * size
    end = 0
    for gap, length, value in zip(runs[::3], runs[1::3], runs[2::3]):
        if type(gap) is not int or type(length) is not int or gap < 0 or length < 1 or end + gap + length > size:
            raise ValueError("run gaps and lengths must stay within the grid")
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("run values must be finite numbers")
        start = end + gap
        end = start + length
        values[start:end] = [value] * length
    return values
