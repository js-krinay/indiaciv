import unittest
from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

from pipeline.build.air_weather import inverse_distance, weather_lenses
from pipeline.core.hexgrid import SQRT3, HexGrid
from pipeline.india.air_weather import aqi_summary, monsoon_departures, station_summary


class AirWeatherTests(unittest.TestCase):
    def test_small_pm25_district_contributes_without_a_dominant_hex(self):
        grid = HexGrid(radius=18, cols=1, rows=1)
        world = {"owner": [0], "county": [0], "county_samples": [[0] * 6 + [1]]}
        inputs = {"cpcb_city_aqi": None, "cpcb_station_pm25": {"stations": {}}, "imd_monsoon": None}
        districts = [{}, {"rings": [[(-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)]]}]
        areas = [1000, 0.1 * 1.5 * SQRT3 * grid.radius ** 2]
        projection = lambda x, y: (x, y)
        with patch("pipeline.build.air_weather.load_interim", side_effect=inputs.__getitem__), \
                patch("pipeline.build.air_weather.district_pm25", return_value=[20, 90]):
            lenses = weather_lenses(world, grid, projection, districts, [], areas)
            world["county_samples"] = [[0] * 7]
            with_extra = weather_lenses(world, grid, projection, districts, [], areas)
        self.assertEqual(lenses[0]["values"], [30.0])
        self.assertEqual(lenses[0]["district_values"], [20, 90])
        self.assertEqual(with_extra[0]["values"], [27.0])

    def test_aqi_uses_distinct_valid_days_and_poor_threshold(self):
        rows = [[str(date(2026, 1, 1) + timedelta(days=i)), 201 if i < 2 else 200] for i in range(244)]
        self.assertIsNone(aqi_summary(rows[:-1] + [rows[0], ["2026-11-01", 300]]))
        self.assertEqual(aqi_summary(rows + [rows[0], ["2026-10-31", None]]), {"days": 244, "poor": 2})

    def test_pm25_uses_complete_enough_days_and_hour_ending_dates(self):
        rows = []
        for i in range(244):
            day = date(2026, 1, 1) + timedelta(days=i)
            for hour in range(7, 24):
                rows.append({"dateTime": f"{day}T{hour:02}:00:00.000Z", "Monitor": 10, "Sparse": 20})
            end = f"{day}T23:59:00.000Z" if i == 0 else f"{day + timedelta(days=1)}T00:00:00.000Z"
            rows.append({"dateTime": end, "Monitor": 28, "Sparse": None})
        data = {"unit": "µg/m³", "pollutant": "PM2.5", "stations": ["Monitor", "Sparse"], "rows": rows}
        self.assertEqual(station_summary(data), {"Monitor": {"days": 244, "mean": 11}})
        self.assertEqual(station_summary({**data, "rows": rows[:-1]}), {})

    def test_monsoon_csv_keeps_signed_departures_and_checks_window(self):
        header = "entity,series,period,value,unit\n"
        self.assertEqual(
            monsoon_departures(StringIO(header + "Odisha,Excess,2026-06-01/2026-09-30,29,% from normal\n"
                                               "Punjab,Deficient,2026-06-01/2026-09-30,-41,% from normal\n")),
            {"ODISHA": 29, "PUNJAB": -41},
        )
        with self.assertRaises(ValueError):
            monsoon_departures(StringIO(header + "Punjab,Deficient,2025-06-01/2025-09-30,-41,% from normal\n"))

    def test_estimate_weights_by_distance_with_a_cutoff(self):
        stations = [(10, 0, 20), (20, 0, 40), (151, 0, 100)]
        self.assertAlmostEqual(inverse_distance(0, 0, stations), 24)
        self.assertEqual(inverse_distance(10, 0, stations), 20)
        self.assertIsNone(inverse_distance(-200, 0, stations))
