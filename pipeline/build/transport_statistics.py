"""Transcriptions of the MoPSW March cargo and PIB annual railway tables."""

AAI_JHARSUGUDA = "aai_vejh_20260806"
PREVIOUS_FY = "FY 2024-25 (1 Apr 2024 – 31 Mar 2025)"
AIRPORT_LABELS = {
    "passengers": "Airport share of reported AAI terminal passenger traffic",
    "freight": "Airport share of reported AAI freight handled",
    "change": "Airport terminal passenger traffic growth",
    "size": "OurAirports facility size class",
}
PORT_DIRECTION_LABELS = {"loaded": "Share of this port’s overseas cargo loaded",
                         "unloaded": "Share of this port’s overseas cargo unloaded"}
OPERATOR_LOCALITIES = "adani_port_addresses_fy25"
VERIFIED_PORT_LOCALITIES = {
    "n3732668135": "Muthukur",
    "r14718755": "Gangavaram",
}

PERIOD = dict(period_start="2025-04-01", period_end="2026-03-31",
              label="FY 2025-26 (1 Apr 2025 – 31 Mar 2026)")

# One marker per authority. Kolkata's row includes both docks.
# The coordinates locate the port facilities, independently of the cargo table.
PORTS = [
    ("deendayal", "Deendayal Port (Kandla)", 70.22, 23.02, 160_114_297),
    ("paradip", "Paradip Port", 86.68, 20.26, 156_450_830),
    ("jnpa", "Jawaharlal Nehru Port", 72.94, 18.95, 102_007_881),
    ("visakhapatnam", "Visakhapatnam Port", 83.29, 17.69, 91_166_346),
    ("mumbai", "Mumbai Port", 72.85, 18.95, 75_147_516),
    ("kolkata", "Syama Prasad Mookerjee Port (Kolkata and Haldia)", 88.31, 22.53, 70_697_660),
    ("chennai", "Chennai Port", 80.30, 13.10, 57_902_975),
    ("mangaluru", "New Mangalore Port", 74.81, 12.92, 50_049_129),
    ("kamarajar", "Kamarajar Port", 80.34, 13.26, 49_080_525),
    ("chidambaranar", "V.O. Chidambaranar Port", 78.22, 8.75, 43_210_136),
    ("cochin", "Cochin Port", 76.25, 9.96, 38_062_547),
    ("mormugao", "Mormugao Port", 73.80, 15.41, 20_837_353),
]

# MoPSW March Table 1, column 9, Coastal rows. Kolkata uses the
# authority total, which already includes Kolkata Dock and Haldia Dock.
COASTAL = {
    "deendayal": 21_932_146, "paradip": 65_805_489, "jnpa": 8_581_177,
    "visakhapatnam": 25_864_221, "mumbai": 22_359_872, "kolkata": 4_179_639,
    "chennai": 5_132_962, "mangaluru": 12_990_104, "kamarajar": 19_558_155,
    "chidambaranar": 10_416_846, "cochin": 13_063_047, "mormugao": 3_566_070,
}
PORT_TOTAL = sum(row[4] for row in PORTS)

# Facility localities, keyed by the same authority or featured port IDs.
PORT_CITIES = {
    "deendayal": "Kandla", "paradip": "Paradip", "jnpa": "Nhava Sheva",
    "visakhapatnam": "Visakhapatnam", "mumbai": "Mumbai", "kolkata": "Kolkata and Haldia",
    "chennai": "Chennai", "mangaluru": "Mangaluru", "kamarajar": "Ennore",
    "chidambaranar": "Thoothukudi", "cochin": "Kochi", "mormugao": "Vasco da Gama",
    "mundra": "Mundra", "hazira": "Hazira", "dahej": "Dahej", "dhamra": "Dhamra",
    "karaikal": "Karaikal",
}


def cargo_split(coastal, total):
    domestic = round(coastal / total, 8)
    return dict(domestic=domestic, foreign=round(1 - domestic, 8), **PERIOD,
                status="Advance estimate", source_id="mopsw_port_cargo", estimated=False)


# Published facility positions, converted to decimal degrees (longitude, latitude).
FEATURED_PORTS = [
    ("mundra", "Mundra Port", 69.693228, 22.738581, "featured_port_locations"),
    ("hazira", "Hazira Port", 72.616667, 21.100000, "featured_port_locations"),
    ("dahej", "Dahej Port", 72.506167, 21.683333, "featured_port_locations"),
    ("dhamra", "Dhamra Port", 86.964225, 20.828458, "featured_port_locations"),
    ("karaikal", "Karaikal Port", 79.853114, 10.848394, "featured_port_locations"),
]

FREIGHT = dict(estimated=False, **PERIOD, unit="million metric tonnes", source_id="pib_rail_freight",
               title="Indian Railways originating freight loading",
               zone_title="Rail originating freight loading by railway zone", total=1669.93, rows=[
    ["CR", "Central", 79.34],
    ["EC", "East Central", 203.42],
    ["ECO", "East Coast", 286.26],
    ["ER", "Eastern", 101.66],
    ["KR", "Konkan", 2.43],
    ["NC", "North Central", 20.97],
    ["NE", "North Eastern", 3.95],
    ["NF", "Northeast Frontier", 11.39],
    ["NR", "Northern", 52.26],
    ["NW", "North Western", 30.53],
    ["SC", "South Central", 147.87],
    ["SE", "South Eastern", 210.41],
    ["SEC", "South East Central", 261.25],
    ["SR", "Southern", 42.13],
    ["SW", "South Western", 52.46],
    ["WC", "West Central", 58.07],
    ["WR", "Western", 105.54],
])
