import json
import unittest

from pipeline.core import lens_values


class LensEncodingTest(unittest.TestCase):
    def test_repeated_and_sparse_values_round_trip_exactly(self):
        values = [None] * 50 + [0, -0.23456789] * 2 + [None] * 50 + [234_567] * 100
        encoded = lens_values.encode(values)
        self.assertLess(len(json.dumps(encoded)), len(json.dumps(values)))
        self.assertEqual(lens_values.decode(encoded, len(values)), values)

    def test_decode_rejects_negative_gaps_or_out_of_bounds_runs(self):
        for runs in ([0, 2, 12, -1, 2, 17], [0, 2, 12, 1, 2, 17]):
            with self.subTest(runs=runs), self.assertRaises(ValueError):
                lens_values.decode({"runs": runs}, 4)

    def test_runs_store_gaps_since_previous_end(self):
        encoded = {"runs": [2, 2, 1, 1, 2, 2, 0, 1, 3]}
        self.assertEqual(lens_values.decode(encoded, 8), [None, None, 1, 1, None, 2, 2, 3])
