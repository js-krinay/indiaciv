import unittest

from pipeline.check import valid_older_period
from pipeline.india import historical_floods


class HistoricalFloodTests(unittest.TestCase):
    def test_single_district_report_has_derived_casualties_and_own_dates(self):
        report = {"UEI": "UEI-IMD-FL-2023-0001", "State": "Bihar", "Districts": "Patna",
                  "District_LGD_Codes": "230", "Start Date": "01-08-2023 00:00",
                  "End Date": "29-08-2023 00:00", "Human fatality": "2", "Human injured": "3"}
        district_keys = {("bihar", "patna"): "10-230"}
        events = historical_floods.event_impacts([report], district_keys)
        event, = events["10-230"]
        self.assertEqual(event["casualties"], 5)
        self.assertTrue(valid_older_period(event["period"]))
        self.assertEqual(event["period"], "1 Aug 2023 to 29 Aug 2023")
        self.assertEqual(event["vintage"], "older")
        self.assertNotIn("cost", event)

    def test_multi_district_loss_is_not_assigned_to_a_single_district(self):
        report = {"UEI": "UEI-IMD-FL-2023-0001", "State": "Bihar", "Districts": "Patna, Gaya",
                  "District_LGD_Codes": "230, 231", "Start Date": "01-08-2023 00:00",
                  "End Date": "02-08-2023 00:00", "Human fatality": "2", "Human injured": "3"}
        self.assertEqual(historical_floods.event_impacts([report], {("bihar", "patna"): "10-230"}), {})


    def test_declines_tentative_and_contradictory_narratives(self):
        from collections import Counter

        dates = {"Start Date": "01-08-2023 00:00", "End Date": "02-08-2023 00:00"}
        fields = dates | {"State": "Bihar", "Districts": "Patna", "District_LGD_Codes": "230"}
        reports = [
            fields | {"UEI": "UEI-IMD-FL-2023-0001", "Human fatality": "40", "Human injured": "",
                      "Description of Casualties/injured": "About 40 people feared died"},
            fields | {"UEI": "UEI-IMD-FL-2023-0002", "Human fatality": "6", "Human injured": "6",
                      "Description of Casualties/injured": "6 members of a family drowned."},
            fields | {"UEI": "UEI-IMD-FL-2023-0003", "Human fatality": "2", "Human injured": "",
                      "Description of Casualties/injured": "2 people died."},
        ]
        excluded = Counter()
        events = historical_floods.event_impacts(reports, {("bihar", "patna"): "10-230"}, excluded)
        event, = events["10-230"]
        self.assertTrue(event["lower_bound"])
        self.assertEqual(event["casualties"], 2)
        self.assertEqual(excluded, {"tentative": 1, "unconfirmed": 1})
