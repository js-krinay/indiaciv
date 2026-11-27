# IA-01 boundary source decision

## Owner decision, 2026-11-27: unofficial boundaries are acceptable

The owner approved using unofficial data. State and union-territory borders and Census 2011 districts now come from
[DataMeet's community maps](https://github.com/datameet/maps) (CC BY 4.0), pinned to commit `b3fbbde`: `States/Admin2`
(36 states and UTs; Ladakh and J&K updated in 2021) and `Districts/Census_2011/2011_Dist`. All 640 A-01 districts
join by census district code; the state codes agree; seven names differ only in spelling. One DataMeet J&K polygon
("Data Not Available", code 0) has no district. India's outer extent still follows the Survey of India outline below.
The generated map data stays local (git-ignored); publication remains the owner's decision. The sections below are
the original review of the official sources.

## 18 km hex ownership

The 2026 Survey of India political map supplies charted Indian land, neighbouring land and
water areas. Water wins when it exceeds both land shares combined. On land, the larger
national share wins. The Survey of India outline, Natural Earth and elevation samples
classify cells with incomplete or tied chart coverage. The fixed grid
is shifted 4 km west and 4 km south of the Lambert origin so the cell containing Itanagar
has majority overlap with Arunachal Pradesh. The same grid is used for terrain sampling.
DataMeet decides state ownership by overlap in hexes whose samples cross state lines.
An uncovered SoI polygon gets a land hex at its largest overlap when it is disjoint
from the mainland. Its owner comes from DataMeet, using the nearest state outline when
a small island is outside its geometry.

After island and union-territory coverage, an Indian locality in the political-map
fixture retains its containing hex if it would otherwise be foreign or water. Named
area controls that describe a hex are comparisons only. The Almanac lists the cells
retained by the locality rule.

| Retained hex | Localities | Indian land (km²) | Foreign land (km²) | Water (km²) | Uncharted (km²) |
| --- | --- | ---: | ---: | ---: | ---: |
| 3973 | Kalapani and Lipulekh Pass | 214.910 | 626.847 | 0.000 | 0.020 |
| 6656 | Sir Creek east bank | 293.436 | 0.000 | 487.898 | 60.442 |

`pipeline check` compares the final ownership to the chart majority and records the
area shares and deciding rule for every crossed hex in the local
`data/interim/_boundary_check.csv`.

A union territory with no tile takes the hex it overlaps most. This also applies to each
DataMeet district corresponding to a detached part of Puducherry or of Dadra and Nagar
Haveli and Daman and Diu. Equal overlaps favour the cell containing the largest polygon's
centroid. The selected hex is a coarse representation and is displayed at full tile size.
The population lens keeps the geographic district samples for these hexes.

The build checker compares named locations with the Survey of India Political Map of
India, English 13th edition (2026, 1:4,000,000). The fixture tests rendered ownership
of the containing cells, including locations of former enclaves transferred under the
Land Boundary Agreement and land and water controls around the mouth of Sir Creek.
Poaturkuthi in India and Dasiar Chhara in Bangladesh share a cell at this resolution.
The cell has a single owner, so the map cannot show both locations on their respective sides.
[Land Boundary Agreement implementation](https://www.mea.gov.in/Uploads/PublicationDocs/25354_scan0006.pdf) · [Official political map](https://surveyofindia.gov.in/UserFiles/files/POL_MAP_4M_ENGLISH_13thEdn2026%281%29.pdf)

Checked 2026-11-26.

## Current national and state/UT geography

The [2021 geospatial guidelines](https://onlinemaps.surveyofindia.gov.in/GeospatialGuidelines.aspx) describe SoI as the standard for political maps and permit compliant map publication. The [1:15M national vector notice](https://www.surveyofindia.gov.in/documents/ibd-vectorformat.pdf) explicitly includes website use and excludes commercial use. The [site copyright policy](https://surveyofindia.gov.in/pages/copyright-policy) requires written permission to reproduce site materials and specifies attribution.

The [digital products catalog](https://onlinemaps.surveyofindia.gov.in/Digital_Products.aspx) lists an all-India district-level Administrative Boundary Database. The inspected catalog path exposes a purchase action. The [portal FAQ](https://onlinemaps.surveyofindia.gov.in/FAQs.aspx) also describes a Quick Access path for ABDB downloads. The Quick Access listing identifies the district product as OVSF/1M/7. Its download action returned HTML in this session, so the archive and its terms remain unverified.

**Release decision:** Pending the edition and terms of the SoI administrative product, including whether simplified geometry can be served as a downloadable browser asset on Cloudflare. Obtain the release, record its effective date and checksum, confirm the applicable terms, and verify the outline, islands, and boundary styles against the official specimen. The SoI portal support contact is named in its FAQ.

The [national outline archive](https://surveyofindia.gov.in/documents/OUTLINE_OF_INDIA.zip) was downloaded and inspected. Its metadata is dated 2025-12-11 and identifies the national outline as a dissolve of an ABDB 2.0 state boundary layer. The local conversion retains 1,150 polygon parts. Archive SHA-256 is `9e657f0c20ac4f4168e261b2c7d3fed4ed927a638a2fd411be9f6257463faf45`.

## Census 2011 district geography

[SHRUG v2.2 district polygons](https://docs.devdatalab.org/SHRUG-Metadata/Open%20Polygons%20and%20Spatial%20Statistics/Tables/open-poly-metadata/) carry 2011 state and district codes. These are harmonized research polygons. The [publisher's license](https://docs.devdatalab.org/Getting-Started/license/) allows noncommercial adaptations under CC BY-NC-SA 4.0. Confirm the project's use fits those terms or arrange a separate license. Then check SoI boundary conformity and compare the district code coverage to the actual Census extract before enabling the lens.

[ORGI A-01 district totals](https://censusindia.gov.in/nada/index.php/catalog/42526) have been extracted locally. These records use 2011 identifiers and preserve their workbook row references. They do not resolve the geometric or licensing questions above.

**Release decision:** Pending permitted geometry and a verified code join. Preserve separate vintage-specific identifiers and retain nulls for unmatched records.
