import unittest

from pipeline.india.projections import parse

# Excerpts of `pdftotext -layout` output of the Technical Group report (2019), trimmed.
TEXT = """
  TABLE – 8
  1          2           3           4           5           6        7        8        9        10
2025      14,10,000   7,20,000    6,90,000      13,800      7,200    6,600    7,400    3,700    3,700
2026      14,23,435   7,29,604    6,93,831      13,896      7,256    6,640    7,450    3,725    3,725
                                                                                           TABLE-21
                                                Projected Total Population As on 1st March - India, States, Union Territories: 2011 – 2036 (‘000)
                                                                   2011                                                   2016                                  2021
                          INDIA                     1210855       623271       587585                      1290235      663346          626889      1361343   698959     662384
  01      Jammu & Kashmir (UT)                       12,267        6,484        5,783                       12,897        6,789          6,108       13,408    7,030      6,378
  25      Dadra & Nagar Haveli                         344          194          150                          452          262            190          608      363        245
                                                                                      TABLE-21 (contd…)
                                                Projected Total Population As on 1st March - India, States, Union Territories: 2011 – 2036 (‘000)
                                                                   2026                                                   2031                                    2036
                          INDIA                   1423435       729604      693831                         1475519       754893         720626       1518288     775702      742586
  01      Jammu & Kashmir (UT)                    13,896        7,256       6,640                             14,361         7,467           6,894      14,747      7,635        7,112
  25      Dadra & Nagar Haveli                    836           516         320                                1,178           753             425       1,702      1,128          574

                                                  TABLE-17A
                                       Demographic Indicators : 2011-2035
                                                       INDIA
                     Indicator                    2011-15           2016-20   2021-25     2026-30        2031-35
       Population growth rate                          12.7           10.7      8.9         7.2            5.7
       Infant Mortality Rate (IMR)                     42.9           38.5     35.3        32.3           29.7
       Total Fertility Rate (TFR)                      2.34           2.13     1.93        1.80           1.72

                                                            160
        Life expectancy of males                     66.87       68.37        69.37     70.37        71.17
        Life expectancy of females                   69.96       71.46        72.66     73.66        74.66
                                         T-17
            Projected Population Characteristics As On 1st March : 2011 - 2036
                                     UTTARAKHAND
             Indicator                 2011  2016              2021     2026      2031      2036
Population (000')
Total                                   10086        10755     11399    11993     12524     12974
Sex Ratio                                    963        957      952      949      948       947
Population by broad age-group
(000')
0-14                                     3134         2884      2709     2592     2542       2437
60+                                       894         1046      1209     1410     1652       1928
Proportion (percent)
0-14                                        31.1       26.8     23.8      21.6     20.3      18.8
60+                                          8.9        9.7     10.6      11.8     13.2      14.9
Median age (years)                       24.21        26.30    28.48     30.79    33.13     35.55
Dependency Ratio
Total (Young and old)                        665        576      524      500       503       507
                                       TABLE-18
          Projected Population By Age and Sex As on 01st March : 2011-2036 ('000)
                                        PUNJAB
   0-4           965   511       454        865   471       394         869     468        401
"""


class ParseProjectionsTest(unittest.TestCase):
    def setUp(self):
        self.p = parse(TEXT)

    def test_table21_has_2011_and_2026_persons_males_females_in_thousands(self):
        india = self.p["population"]["INDIA"]
        self.assertEqual(india["2011"], [1210855, 623271, 587585])
        self.assertEqual(india["2026"], [1423435, 729604, 693831])
        self.assertEqual(india["2031"], [1475519, 754893, 720626])
        self.assertEqual(self.p["population"]["Dadra & Nagar Haveli"]["2026"], [836, 516, 320])

    def test_table8_reads_both_annual_rows(self):
        self.assertEqual(self.p["annual_population"]["INDIA"], {"2025": 1410000, "2026": 1423435})

    def test_indicators_interpolate_to_2026_across_a_page_break(self):
        self.assertEqual(self.p["indicators"]["INDIA"],
                         {"imr": 33.5, "tfr": 1.852, "life_male": 69.97, "life_female": 73.26})

    def test_missing_earlier_endpoint_leaves_indicator_blank(self):
        data = parse(TEXT.replace("1.93        1.80", "  –         1.80"))
        self.assertNotIn("tfr", data["indicators"]["INDIA"])

    def test_state_profile_takes_the_2026_column_of_t17_by_section(self):
        self.assertEqual(self.p["profile"]["UTTARAKHAND"],
                         {"population": 11993, "sex_ratio": 949, "age_0_14": 21.6, "age_60": 11.8, "median_age": 30.79})

    def test_table_18_is_not_used(self):  # the report heads Uttarakhand's Table 18 "PUNJAB"
        self.assertNotIn("PUNJAB", self.p["profile"])


if __name__ == "__main__":
    unittest.main()
