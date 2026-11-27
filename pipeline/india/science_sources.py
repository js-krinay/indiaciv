"""Public institution inventory for Science, frozen on 27 November 2026."""

import json
from hashlib import sha256
from pathlib import Path

from ..core.geo import Shape
from ..core.source import SourceInfo

# Each entry is a short institution name, state or UT code, and published city or locality.
# Locations without verified point coordinates count at state level.
ROSTER = {
    "IIT": [
        ("IIT Bhilai", "CG", "Bhilai"),
        ("IIT Bhubaneswar", "OD", "Bhubaneswar"),
        ("IIT Bombay", "MH", "Mumbai"),
        ("IIT Delhi", "DL", "New Delhi"),
        ("IIT Dhanbad", "JH", "Dhanbad"),
        ("IIT Dharwad", "KA", "Dharwad"),
        ("IIT Gandhinagar", "GJ", "Gandhinagar"),
        ("IIT Goa", "GA", "Farmagudi"),
        ("IIT Guwahati", "AS", "Guwahati"),
        ("IIT Hyderabad", "TS", "Kandi"),
        ("IIT Indore", "MP", "Indore"),
        ("IIT Jammu", "JK", "Jammu"),
        ("IIT Jodhpur", "RJ", "Jodhpur"),
        ("IIT Kanpur", "UP", "Kanpur"),
        ("IIT Kharagpur", "WB", "Kharagpur"),
        ("IIT Madras", "TN", "Chennai"),
        ("IIT Mandi", "HP", "Mandi"),
        ("IIT Palakkad", "KL", "Palakkad"),
        ("IIT Patna", "BR", "Patna"),
        ("IIT Roorkee", "UK", "Roorkee"),
        ("IIT Ropar", "PB", "Rupnagar"),
        ("IIT Tirupati", "AP", "Tirupati"),
        ("IIT BHU", "UP", "Varanasi"),
    ],
    "IISc": [("IISc", "KA", "Bengaluru")],
    "IISER": [
        ("IISER Berhampur", "OD", "Berhampur"),
        ("IISER Bhopal", "MP", "Bhopal"),
        ("IISER Kolkata", "WB", "Mohanpur"),
        ("IISER Mohali", "PB", "Mohali"),
        ("IISER Pune", "MH", "Pune"),
        ("IISER Thiruvananthapuram", "KL", "Vithura"),
        ("IISER Tirupati", "AP", "Tirupati"),
    ],
    "NIT": [
        ("NIT Agartala", "TR", "Agartala"),
        ("NIT Andhra Pradesh", "AP", "Tadepalligudem"),
        ("NIT Arunachal Pradesh", "AR", "Jote"),
        ("NIT Calicut", "KL", "Kozhikode"),
        ("NIT Delhi", "DL", "Delhi"),
        ("NIT Durgapur", "WB", "Durgapur"),
        ("NIT Goa", "GA", "Cuncolim"),
        ("NIT Hamirpur", "HP", "Hamirpur"),
        ("NIT Jalandhar", "PB", "Jalandhar"),
        ("NIT Jamshedpur", "JH", "Jamshedpur"),
        ("NIT Karnataka", "KA", "Surathkal"),
        ("NIT Kurukshetra", "HR", "Kurukshetra"),
        ("NIT Manipur", "MN", "Imphal"),
        ("NIT Meghalaya", "ML", "Sohra"),
        ("NIT Mizoram", "MZ", "Aizawl"),
        ("NIT Nagaland", "NL", "Chümoukedima"),
        ("NIT Patna", "BR", "Patna"),
        ("NIT Puducherry", "PY", "Karaikal"),
        ("NIT Raipur", "CG", "Raipur"),
        ("NIT Rourkela", "OD", "Rourkela"),
        ("NIT Sikkim", "SK", "Ravangla"),
        ("NIT Silchar", "AS", "Silchar"),
        ("NIT Srinagar", "JK", "Srinagar"),
        ("NIT Tiruchirappalli", "TN", "Tiruchirappalli"),
        ("NIT Uttarakhand", "UK", "Srinagar (Garhwal)"),
        ("NIT Warangal", "TS", "Warangal"),
        ("MANIT", "MP", "Bhopal"),
        ("MNIT", "RJ", "Jaipur"),
        ("MNNIT", "UP", "Prayagraj"),
        ("SVNIT", "GJ", "Surat"),
        ("VNIT", "MH", "Nagpur"),
    ],
    "AIIMS": [
        ("AIIMS Bathinda", "PB", "Bathinda"),
        ("AIIMS Bhopal", "MP", "Bhopal"),
        ("AIIMS Bhubaneswar", "OD", "Bhubaneswar"),
        ("AIIMS Bibinagar", "TS", "Bibinagar"),
        ("AIIMS Bilaspur", "HP", "Bilaspur"),
        ("AIIMS Deoghar", "JH", "Deoghar"),
        ("AIIMS Delhi", "DL", "New Delhi"),
        ("AIIMS Gorakhpur", "UP", "Gorakhpur"),
        ("AIIMS Guwahati", "AS", "Guwahati"),
        ("AIIMS Jammu", "JK", "Vijaypur"),
        ("AIIMS Jodhpur", "RJ", "Jodhpur"),
        ("AIIMS Kalyani", "WB", "Kalyani"),
        ("AIIMS Madurai", "TN", "Madurai"),
        ("AIIMS Mangalagiri", "AP", "Mangalagiri"),
        ("AIIMS Nagpur", "MH", "Nagpur"),
        ("AIIMS Patna", "BR", "Patna"),
        ("AIIMS Raebareli", "UP", "Raebareli"),
        ("AIIMS Raipur", "CG", "Raipur"),
        ("AIIMS Rajkot", "GJ", "Rajkot"),
        ("AIIMS Rishikesh", "UK", "Rishikesh"),
    ],
    "AIIMS under development": [
        ("AIIMS Awantipora", "JK", "Awantipora"),
        ("AIIMS Darbhanga", "BR", "Darbhanga"),
        ("AIIMS Rewari", "HR", "Majra"),
    ],
    "CSIR": [
        ("AMPRI", "MP", "Bhopal"),
        ("CBRI", "UK", "Roorkee"),
        ("CDRI", "UP", "Lucknow"),
        ("CCMB", "TS", "Hyderabad"),
        ("CECRI", "TN", "Karaikudi"),
        ("CEERI", "RJ", "Pilani"),
        ("CFTRI", "KA", "Mysuru"),
        ("CGCRI", "WB", "Kolkata"),
        ("CIMAP", "UP", "Lucknow"),
        ("CIMFR", "JH", "Dhanbad"),
        ("CLRI", "TN", "Chennai"),
        ("CMERI", "WB", "Durgapur"),
        ("CRRI", "DL", "New Delhi"),
        ("CSIO", "CH", "Chandigarh"),
        ("CSMCRI", "GJ", "Bhavnagar"),
        ("IGIB", "DL", "Delhi"),
        ("IHBT", "HP", "Palampur"),
        ("IICB", "WB", "Kolkata"),
        ("IICT", "TS", "Hyderabad"),
        ("IIIM", "JK", "Jammu"),
        ("IIP", "UK", "Dehradun"),
        ("IITR", "UP", "Lucknow"),
        ("IMMT", "OD", "Bhubaneswar"),
        ("IMTECH", "CH", "Chandigarh"),
        ("NAL", "KA", "Bengaluru"),
        ("NBRI", "UP", "Lucknow"),
        ("NCL", "MH", "Pune"),
        ("NEERI", "MH", "Nagpur"),
        ("NEIST", "AS", "Jorhat"),
        ("NGRI", "TS", "Hyderabad"),
        ("NIIST", "KL", "Thiruvananthapuram"),
        ("NIO", "GA", "Dona Paula"),
        ("NIScPR", "DL", "New Delhi"),
        ("NML", "JH", "Jamshedpur"),
        ("NPL", "DL", "New Delhi"),
        ("SERC", "TN", "Chennai"),
        ("NIDSA", "KA", "Bengaluru"),
    ],
    "ISRO and DoS": [
        ("DoS and ISRO HQ", "KA", "Bengaluru"),
        ("HSFC", "KA", "Bengaluru"),
        ("IIRS", "UK", "Dehradun"),
        ("IISU", "KL", "Thiruvananthapuram"),
        ("IPRC", "TN", "Mahendragiri"),
        ("ISTRAC", "KA", "Bengaluru"),
        ("LEOS", "KA", "Bengaluru"),
        ("LPSC", "KL", "Thiruvananthapuram"),
        ("MCF", "KA", "Hassan"),
        ("NRSC", "TS", "Hyderabad"),
        ("SDSC SHAR", "AP", "Sriharikota"),
        ("SAC", "GJ", "Ahmedabad"),
        ("URSC", "KA", "Bengaluru"),
        ("VSSC", "KL", "Thiruvananthapuram"),
        ("IIST", "KL", "Thiruvananthapuram"),
        ("NARL", "AP", "Tirupati"),
        ("NE-SAC", "ML", "Ri Bhoi District"),
        ("PRL", "GJ", "Ahmedabad"),
    ],
}

FACTS = "Publisher copyright applies to the website. IndiaCiv uses cited establishment and locality facts."
POINT_FILE = Path(__file__).with_name("config") / "science_points.json"
POINT_SHA256 = "836f6f4ef3458265f267da336c3df2a7f0a72e183066b50c4e0f9c8b7d1a942a"


def research_points(datameet, district_state):
    raw = POINT_FILE.read_bytes()
    if sha256(raw).hexdigest() != POINT_SHA256:
        raise ValueError("Science point inventory checksum mismatch")
    points = json.loads(raw)
    known = {name: (kind, state) for kind, rows in ROSTER.items() for name, state, _ in rows}
    needed = {point["district"] for point in points.values()}
    districts = {key: Shape(row["rings"]) for row in datameet["districts"]
                 if (key := f"{row['state_code']:02d}-{row['code']:03d}") in needed}
    for name, point in points.items():
        kind, state = known[name]
        district = point["district"]
        if district_state.get(district) != state or not districts[district].contains(point["lon"], point["lat"]):
            raise ValueError(f"Science location for {name} does not match its verified district")
        yield {"name": name, "kind": kind, **point}


SOURCES = [
    SourceInfo("research_campuses", "Department of Higher Education annual report 2024-25",
               "Ministry of Education",
               "https://www.education.gov.in/sites/upload_files/mhrd/files/document-reports/MoE_AR_En.pdf",
               FACTS, "Central Universities and Institutions chapter and Citizen Charter 2025 annex. "
               "IISc, 23 IITs and seven IISERs in the 27 Nov 2026 inventory.", ["Science"]),
    SourceInfo("research_nits", "NITSER Council institute roster", "Ministry of Education / NITSER Council",
               "https://www.nitcouncil.org.in/annualreport", FACTS,
               "27 Nov 2026 roster snapshot. Localities from the institutes' published addresses. "
               "31 NITs; IIEST Shibpur is a separate institute.", ["Science"]),
    SourceInfo("research_aiims", "Status of AIIMS", "Ministry of Health and Family Welfare / PMSSY",
               "https://pmssy.mohfw.gov.in/index.php?slide=117", FACTS,
               "27 Nov 2026 snapshot. The 22 PMSSY institutes plus AIIMS New Delhi. "
               "The three institutes listed under development are tracked separately.", ["Science"]),
    SourceInfo("research_csir", "CSIR Laboratories and Institutes",
               "Council of Scientific and Industrial Research", "https://www.csir.res.in/en/csir-labs-unit",
               FACTS, "Edition updated 25 Nov 2026, 37 national laboratories and institutes.", ["Science"]),
    SourceInfo("research_isro", "Department of Space Centres and Units",
               "Department of Space / ISRO", "https://www.isro.gov.in/ISRO_EN/isro_centre.html", FACTS,
               "27 Nov 2026 roster snapshot, cross-checked against the Department of Space annual report "
               "2025-26. Counts 14 centres and units and four autonomous bodies, excluding companies and "
               "the promotion and authorisation centre.", ["Science"]),
    SourceInfo("research_points", "IndiaCiv public research institution locations",
               "Institute websites, Wikidata and OpenStreetMap contributors", "https://www.wikidata.org/",
               "Wikidata CC0, OpenStreetMap ODbL 1.0, and cited establishment facts from institute websites.",
               f"27 Nov 2026 snapshot, SHA-256 {POINT_SHA256}. Per-point citations and DataMeet district checks "
               "are recorded in the local roster. IndiaCiv publishes research counts, district campus badge labels, "
               "and a verified subset of IISc, IIT and IISER locations for Wonders.",
               ["City Science", "City View district badges", "Wonders"]),
]
