import unittest

from pipeline.build.disasters import event_summary, index_events
from pipeline.build.city_conditions import member_events


class DisasterTests(unittest.TestCase):
    def test_state_index_counts_each_incident_once_without_spreading_to_districts(self):
        first = {"id": "flood", "districts": ["a", "b"], "states": ["ST"]}
        second = {"id": "heat", "districts": [], "states": ["ST"]}
        states, districts = index_events([first, second], {"a": "ST", "b": "ST", "c": "ST"})
        self.assertEqual(states["ST"], [first, second])
        self.assertEqual(districts, {"a": [first], "b": [first]})

    def test_summary_uses_incident_dates_before_publication_dates(self):
        events = [
            {"type": "Flood", "start_date": "2026-04-02", "reported_on": "2026-04-20"},
            {"type": "Heatwave", "start_date": None, "reported_on": "2026-04-10"},
        ]
        self.assertEqual(event_summary(events), {
            "count": 2, "by_type": {"Flood": 1, "Heatwave": 1},
            "last_date": "2026-04-10", "last_report_only": True,
        })
        self.assertIsNone(event_summary([]))

    def test_impact_stays_in_its_reported_district(self):
        event = {"districts": ["a", "b"], "impact": {"district": "a", "deaths": 8}}
        self.assertNotIn("impact", member_events({"b"}, [event])[0])
        self.assertEqual(member_events({"a"}, [event])[0]["impact"], event["impact"])
