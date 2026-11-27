import unittest

from pipeline.india import household_costs


class HouseholdCostsTest(unittest.TestCase):
    def test_district_pilot_joins_renamed_district_and_excludes_carved_boundaries(self):
        rows = [["District", "MPCE (Rural)", "MPCE (Urban)"], ["FH", "SFH", "FH", "SFH"],
                ["Prayagraj", "2000", "3191", "3000", "5040"],
                ["Moradabad", "3572", "3582", "4096", "4086"]]
        districts = [{"state_code": 9, "code": 175, "name": "Allahabad"},
                     {"state_code": 9, "code": 135, "name": "Moradabad"}]
        self.assertEqual(household_costs.district_pilot(rows, districts, (3191, 5040)),
                         {"09-175": {"rural": 100, "urban": 100}})

    def test_poverty_keeps_rural_and_urban_within_one_threshold_method(self):
        rows = [
            ["State", "Rural 2009-10", "Urban 2009-10", "Rural 2011-12", "Urban 2011-12",
             "Rural 2022-23", "Urban 2022-23"],
            ["Andhra Pradesh", "27.0", "30.5", "12.7", "15.6", "1.2", "2.2"],
            ["Assam", "42.9", "40.2", "42.0", "34.2", "8.7", "5.5"],
            ["Bihar", "65.1", "55.0", "40.1", "50.8", "5.9", "9.1"],
            ["Note: Andhra Pradesh includes Telangana"],
        ]
        self.assertEqual(household_costs.poverty_indexes(rows),
                         {"rangarajan_poverty_rural": {"Assam": 119.18, "Bihar": 80.82},
                          "rangarajan_poverty_urban": {"Assam": 75.34, "Bihar": 124.66}})

    def test_rent_indexes_skip_changed_boundaries(self):
        report = ("Statement 24.5: Average monthly rent\n"
                  "Jammu & Kashmir 874 1,337 1,277\n"
                  "Andhra Pradesh 1,491 3,064 2,606\n"
                  "all-India 1,424 3,306 3,056")
        self.assertEqual(household_costs.rental_indexes(report)["rent_index_urban"],
                         {"Andhra Pradesh": 92.68, "India": 100})

    def test_health_coverage_uses_nfhs6_household_total(self):
        text = ("India - Key Indicators\n"
                "7. Households with any usual member covered under a health insurance/financing scheme (%)"
                "    56.4   62.0   60.2   41.0")
        self.assertEqual(household_costs.health_financing(text), {"India": 39.8})

    def test_health_factsheet_only_reads_first_page_for_missing_text(self):
        text = "Provisional results\fAndhra Pradesh - Key Indicators\fAndhra Pradesh - Key Indicators"
        self.assertEqual(household_costs.fact_sheet_pages(text), {"Andhra Pradesh": 2})

    def test_health_period_uses_wrapped_dates_from_state_appendix(self):
        def line(serial, state, start, end):
            return f"{serial:<14}{state:<16}{'':28}{start:<19}{end}"

        text = "\n".join(["Duration of Survey Fieldwork",
                          line("", "Andaman and", "", "12 February,"),
                          line("1", "", "17 July, 2023", ""),
                          line("", "Nicobar Islands", "", "2024")])
        self.assertEqual(household_costs.health_periods(text),
                         {"Andaman & Nicobar": "NFHS-6 (17 Jul 2023 to 12 Feb 2024)"})

    def test_fixed_wifi_uses_all_households(self):
        self.assertEqual(household_costs.fixed_wifi(86.3, 14.9), 12.8587)

    def test_sector_index_uses_matching_reference(self):
        self.assertEqual(household_costs.sector_index(3670, 4122), 89.03)

    def test_wrapped_state_name_joins_current_union_territory(self):
        text = "Dadra & Nagar\nHaveli & Daman &     94.7  4.3  97.4  4.1\nDiu"
        rows = household_costs.table_rows(text, 4)
        self.assertEqual(rows["Dadra and Nagar Haveli and Daman and Diu"], [94.7, 4.3, 97.4, 4.1])
