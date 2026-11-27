import unittest

from pipeline.build.disasters import advisor_inventory


class AdvisorDisastersTests(unittest.TestCase):
    def test_event_affecting_multiple_states_is_counted_once(self):
        summary = {"count": 1, "by_type": {"Flood": 1}, "last_date": "2026-09-15"}
        doc = advisor_inventory({
            "period": "2026", "coverage": "Selected reports",
            "events": [{"id": "event", "start_date": None, "reported_on": "2026-09-15",
                        "states": ["AS", "ML"], "type": "Flood", "label": "Flooding",
                        "districts": ["18-001"], "source": "source"}],
            "states": {"AS": summary, "ML": summary}, "districts": {"18-001": summary},
        })
        self.assertEqual(doc["fema"]["total"], 1)
        self.assertEqual(doc["fema"]["by_type"], {"Flood": 1})
        self.assertEqual(doc["fema"]["counties"]["rows"], [["18-001", 1, "2026-09-15", 1]])
        self.assertTrue(doc["fema"]["recent"][0]["report_only"])

    def test_report_date_caption_preserves_sort_date(self):
        doc = advisor_inventory({
            "period": "2026", "coverage": "Selected reports",
            "events": [{"id": "event", "start_date": None, "reported_on": "2026-09-15",
                        "states": ["AS"], "type": "Flood", "label": "Flooding",
                        "districts": ["18-001"], "source": "source"}],
            "states": {}, "districts": {},
        })
        row = doc["fema"]["recent"][0]
        self.assertEqual(row["date"], "2026-09-15")
        self.assertEqual(row["date_caption"], "Reported 2026-09-15")
