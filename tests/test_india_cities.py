import unittest

from pipeline.build.cities import city_state_lookup, place_cities
from pipeline.core.geo import MapProjection
from pipeline.core.hexgrid import HexGrid

GRID = HexGrid(18.0, 6, 6)
LAND = 0


def delhi_state(x, y):
    return "DL", "Delhi"


def owner_with_water(*water_cells):
    owner = [LAND] * GRID.size
    for i in water_cells:
        owner[i] = -1
    return owner


def place(pid, name, population, cell, capital=False, region="Region"):
    # Places carry projected metres; the test projection maps them straight onto map km.
    x, y = GRID.center(*GRID.col_row(cell))
    return {"id": pid, "name": name, "region": region, "population": population, "capital": capital, "x": x * 1000, "y": y * 1000}


def identity(x, y):
    return x, y


class PlaceCitiesTest(unittest.TestCase):
    def test_kottayam_collision_keeps_both_cities_in_kerala(self):
        # UN projected metre coordinates on the 18 km India grid.
        grid = HexGrid(18, 109, 139)
        project = MapProjection(min_x=-1425.199555884469, max_y=1686, margin=200)
        places = [
            {**place("21312", "Kottayam", 914_278, 14), "x": -605105, "y": -1362123},
            {**place("21215", "Cherthala", 958_336, 14), "x": -624708, "y": -1350475},
        ]
        for agglomeration, cell in zip(places, [13113, 13112]):
            self.assertEqual(grid.cell_at(*project.from_projected(agglomeration["x"] / 1000,
                                                                  agglomeration["y"] / 1000)), cell)
        owners = [1] * grid.size
        owners[13112] = -1
        owners[13113] = owners[13221] = 0
        cities, relocated = place_cities(places, grid, owners, project.from_projected,
                                        lambda x, y: ("KL", "Kerala"), ["KL", "TN"])
        self.assertEqual([c["name"] for c in cities], ["Cherthala", "Kottayam"])
        self.assertEqual([c["cell"] for c in cities], [13113, 13221])
        self.assertEqual(relocated, ["Kottayam"])

    def test_no_free_in_state_neighbour_keeps_both_cities_on_the_tile(self):
        places = [place("2", "New Delhi", 300_000, 14, capital=True), place("1", "Delhi", 15_000_000, 14)]
        owners = [1] * GRID.size
        owners[14] = 0
        cities, relocated = place_cities(places, GRID, owners, identity, delhi_state, ["DL", "HR"])
        self.assertEqual([c["cell"] for c in cities], [14, 14])
        self.assertEqual([c["capital"] for c in cities], [False, True])
        self.assertEqual(relocated, [])

    def test_full_name_uses_the_resolved_state(self):
        cities, _ = place_cities([place("1", "Gurugram", 900_000, 7, region="Haryana")], GRID, owner_with_water(), identity, delhi_state, ["DL"])
        self.assertEqual(cities[0]["full"], "Gurugram, Delhi")  # the resolved state wins over the input region

    def test_kannur_keeps_kerala_when_its_banner_snaps_to_mahe(self):
        owners = [-1] * GRID.size
        owners[GRID.neighbours(14)[0]] = 1
        x, y = GRID.center(*GRID.col_row(14))
        coast = [(x - 2, y - 2), (x + 2, y - 2), (x + 2, y + 2), (x - 2, y + 2)]
        datameet = {"states": [{"name": "Kerala", "rings": [coast]}]}
        state_at = city_state_lookup(datameet, identity)
        cities, _ = place_cities([place("1", "Kannur", 900_000, 14)], GRID, owners, identity, state_at, ["KL", "PY"])
        self.assertEqual(owners[cities[0]["cell"]], 1)
        self.assertEqual(cities[0]["states"], ["KL"])
        self.assertEqual(cities[0]["full"], "Kannur, Kerala")

    def test_place_on_water_snaps_to_the_nearest_land_cell(self):
        cities, _ = place_cities([place("1", "Port", 500_000, 14)], GRID, owner_with_water(14), identity, delhi_state, ["DL"])
        self.assertIn(cities[0]["cell"], GRID.neighbours(14))
        self.assertEqual(cities[0]["footprint"], [cities[0]["cell"]])

    def test_sorted_by_population_with_population_ranks_and_peers(self):
        places = [place(str(k), f"C{k}", 1000 * (k + 1), k) for k in range(8)]
        cities, _ = place_cities(places, GRID, owner_with_water(), identity, delhi_state, ["DL"])
        self.assertEqual([c["population"] for c in cities], sorted((c["population"] for c in cities), reverse=True))
        self.assertEqual([c["ranks"]["population"] for c in cities], list(range(1, 9)))
        self.assertIsNone(cities[0]["ranks"]["gdp"])
        self.assertEqual(cities[0]["peers"], ["6", "5", "4", "3", "2"])
        for c in cities:
            self.assertEqual(len(set(c["peers"])), 5)
            self.assertNotIn(c["id"], c["peers"])

    def test_city_keeps_forward_growth_and_displays_current_spelling(self):
        source = place("1", "Dehra Dun", 1_000_000, 14)
        source["projected_growth"] = 0.025
        source["growth_period"] = "1 Jul 2025 – 1 Jul 2026"
        cities, _ = place_cities([source], GRID, owner_with_water(), identity, delhi_state, ["DL"])
        self.assertEqual(cities[0]["name"], "Dehradun")
        self.assertEqual(cities[0]["projected_growth"], 0.025)
        self.assertIsNone(cities[0]["growth_years"])

    def test_places_without_a_population_are_left_out(self):
        cities, _ = place_cities([place("1", "Ghost", 0, 3), place("2", "Town", 20_000, 4)], GRID, owner_with_water(), identity, delhi_state, ["DL"])
        self.assertEqual([c["name"] for c in cities], ["Town"])


if __name__ == "__main__":
    unittest.main()
