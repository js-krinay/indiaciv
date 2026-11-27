import unittest

from pipeline.build.district_values import district_sample_values
from pipeline.build.states import district_states


def square(x0, y0, x1, y1):
    return [[(x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)]]


class DistrictStatesTest(unittest.TestCase):
    def test_a_district_goes_to_the_state_holding_most_of_it(self):
        states = [{"name": "Andhra Pradesh", "rings": square(0, 0, 4, 4)}, {"name": "Telangana", "rings": square(0, 4, 4, 8)}]
        districts = [
            {"name": "Hyderabad", "rings": square(1, 4.5, 2, 6)},   # wholly in the newer state
            {"name": "Straddling", "rings": square(1, 2, 2, 5)},    # two thirds in the first state
            {"name": "Offshore", "rings": square(10, 10, 11, 11)},  # in no state
        ]
        self.assertEqual(district_states(districts, states), [1, 0, -1])

    def test_a_district_of_small_islands_votes_with_its_island_centres(self):
        islands = square(0, 0, 0.1, 0.1) + square(5, 5, 5.1, 5.1)  # the lattice points all fall in the sea between
        states = [{"name": "Lakshadweep", "rings": islands}]
        self.assertEqual(district_states([{"name": "Lakshadweep", "rings": islands}], states), [0])


class DensityValuesTest(unittest.TestCase):
    def test_mean_of_the_sample_districts_null_off_india_and_where_no_sample_has_a_district(self):
        owner = [0, 0, -1, 0]
        samples = [[0, 0, 1], [1, -1, 1], [], [-1, -1, -1]]
        density = [100, 400]
        self.assertEqual(district_sample_values(owner, samples, density), [200.0, 400.0, None, None])

    def test_a_district_no_sample_hits_is_blended_in_by_its_area_share(self):
        # A city district covering 10% of the hex at 20,000/km² around suburbs at 2,000/km²: 0.1·20,000 + 0.9·2,000.
        values = district_sample_values([0], [[0] * 7], [2000], extra={0: [(20000, 0.1)]})
        self.assertAlmostEqual(values[0], 3800.0)

    def test_districts_without_a_density_are_skipped(self):
        self.assertEqual(district_sample_values([0], [[0, 1]], [None, 50]), [50.0])


if __name__ == "__main__":
    unittest.main()
