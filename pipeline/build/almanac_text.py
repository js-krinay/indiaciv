"""Indian map methods and landmark notes from the Almanac."""

NOTES = {
    'Cities': (
        'Cities are urban agglomerations mapped using UN DESA coordinates and mid-2026 population '
        'projections. A city’s state comes from its UN location. When two agglomerations fall in one hex, the '
        "larger one is shown. India's population is the official projection for 1 March 2026 (Technical Group "
        'on Population Projections, MoHFW).',
    ),
    'Yields': (
        'Yield points use the scales shown in each entry. Map panels and national reports show underlying '
        'values and flag IndiaCiv estimates.',
    ),
    'States': (
        "Click any land hex without a city to open its state or union territory. The borders are today's 28 "
        "states and 8 union territories, from DataMeet's community maps (unofficial).",
        'Population, sex ratio and age use the Technical Group (MoHFW) projections for 1 March 2026. State '
        'and national growth compare the projected totals on 1 March 2025 and 1 March 2026. The seven smaller '
        'North-East states share one combined age and health profile. WorldPop supplies 2026 age estimates '
        'for Goa, Andaman & Nicobar, Chandigarh, Puducherry, Lakshadweep and Dadra and Nagar Haveli and Daman '
        'and Diu.',
        'Every union territory and each detached part of Puducherry and of Dadra and Nagar Haveli and Daman '
        'and Diu has a tile. When a part would have no tile, it takes the hex it overlaps most. Detached '
        'islands without a land hex get one based on the Survey of India outline.',
    ),
    'Terrain': (
        'The base describes the climate or water class. Relief describes the shape of the ground. Features '
        'show vegetation, landforms and sites that can coexist on the same tile.',
        'Shading uses elevation differences with neighbouring hexes, lit from the north-west. Neighbouring '
        'countries (Natural Earth) are drawn under light fog for context. India’s extent follows the Survey '
        'of India outline.',
    ),
    'Lenses': (
        "Population is estimated per district: each district's census count grown at its state's projected "
        'rate to 1 March 2026, over its area. Each hex is sampled at 7 points and takes the mean of the '
        'districts under them, so a hex split between two districts gets a blend. A small district that no '
        "sample hits is blended into the hex holding its centre by its share of the hex's area. State, union "
        'territory and health lenses show the region’s projection or estimate across its hexes.',
        'The city population and growth lenses colour only city hexes. They show the UN mid-2026 population '
        'projection for each urban agglomeration and its projected growth from 1 July 2025 to 1 July 2026.',
        'Health uses IndiaCiv estimates for 2026. For each indicator, we place the two Technical Group '
        'five-year averages at their midpoints and interpolate linearly, three-fifths of the way from the '
        'earlier midpoint to the later one. Values with a missing endpoint stay blank.',
        'The legend shows how many hexes fall at each value. Hover or drag on it to show only that range on '
        'the map.',
    ),
    'Resources': (
        'Press R to show or hide resource markers. Zoom in to '
        'see more locations. Hover or tap a marker for its period and source.',
        'IndiaCiv estimates place crop markers on representative tiles within documented growing areas. These '
        'markers show where a crop is grown. Power and mine figures shown as capacities use rated or design '
        'capacity.',
    ),
    'Trade': (
        'Turn on Trade in Map layers. Amber lines follow the operating Eastern and Western Dedicated Freight '
        'Corridors on the OpenStreetMap rail grid. © OpenStreetMap contributors, ODbL 1.0.',
        'Cyan branches show domestic coastal cargo handled by each major port authority. Width uses a '
        'square-root scale so smaller ports stay readable. The shared dashed sea lane is schematic and '
        'carries no cargo weight. Hover over a branch for its port and volume.',
    ),
    'Wonders': (
        'Explore built landmarks and natural sites across India, plus Mount Kailash in Tibet. Use the Wonders switch in Map layers. '
        'Hover over a wonder marker for details.',
        'The November 2026 inventory includes UNESCO inscriptions, wetlands and other sites chosen for '
        'regional coverage. The derived inventory is licensed under CC BY-SA 4.0.',
    ),
    'Rivers': (
        'Rivers follow hex edges. Larger streams have wider channels. Hover over a named river or lake to '
        'identify it.',
        'River courses come from OpenStreetMap and Natural Earth. Channel width follows a cartographic rank '
        'by named course. Lake and reservoir outlines come from HydroLAKES and © OpenStreetMap contributors.',
    ),
    'Protected land': (
        'Green tint marks hexes with at least 30% coverage by a mapped Ramsar wetland, national park or tiger '
        'reserve. Dots mark located sites without a qualifying hex. Dots scale with the published site area, '
        'and wetland outlines appear as you zoom in.',
        'The October 2026 Ramsar list supplies site locations, areas and available published boundaries. Park '
        'and tiger reserve designations come from WII and NTCA. © OpenStreetMap contributors supply available '
        'park and reserve geometry and fallback locations under ODbL 1.0. Wikidata supplies additional point '
        'locations under CC0. An OpenStreetMap extent must be within 25% of the official area to contribute '
        'to the tint or Explorer shares.',
        'Explorer reports the share of each DataMeet state or district covered by the union of available '
        'extents from the 2026 snapshots. Point markers contribute no area. These shares describe mapped '
        'coverage and can be lower than legal protected-area totals.',
    ),
    'About this map': (
        'The Survey of India political map decides whether charted water exceeds combined land in each hex. '
        'On land, the larger national share wins. Indian localities in the reference fixture keep an Indian '
        'land hex if they would otherwise fall in water or beyond the border. Uncovered detached islands '
        'retain land tiles. Where samples cross state lines, the state with the largest DataMeet overlap '
        'wins. A union territory or named detached part that would have no tile takes the hex it overlaps '
        'most. District density uses the geographic sample points.',
    ),
    'Railways': (
        'OpenStreetMap supplies operating rail lines, expressways, national highways and mapped port '
        'locations. The national view shows trunk rail corridors, expressways and Golden Quadrilateral '
        'highways. Zoom in for other main lines and secondary tracks. Parallel tracks can share a hex link. © '
        'OpenStreetMap contributors, ODbL 1.0.',
        'IndiaCiv divides the March report’s coastal cargo by total cargo for each major port authority. '
        'Kolkata includes both Kolkata and Haldia docks. The Ministry of Ports, Shipping and Waterways '
        'supplies the advance estimates. Named port localities are matched by authority or facility ID. State '
        'and UT labels join facility coordinates to DataMeet boundaries, with a coastal placement fallback. '
        'Airports use OurAirports size classes.',
        'Originating freight by railway comes from the Ministry of Railways via the Press Information Bureau.',
    ),
}

WONDER_NOTES = {
    'gateway-of-india': (
        'Approach the arch from the city and the harbour opens up beyond it. Its waterfront position explains '
        "why a ceremonial entrance became one of the clearest visual landmarks on Mumbai's shore."
    ),
    'hawa-mahal': (
        'The building reads as a wall of windows from the street. Look for the repeated projecting bays and '
        'the way each tier narrows towards the top, giving the facade its distinctive stepped profile.'
    ),
    'india-gate': (
        'The arch is best read together with the long avenue it terminates. The low skyline around Kartavya '
        'Path leaves the memorial clearly visible on the central axis of New Delhi.'
    ),
    'jatayu': (
        'The bird lies across the summit, so the outline of its wings follows the land rather than rising '
        'above it like a standing monument. The choice of hilltop makes the story legible from several '
        'approaches.'
    ),
    'mount-kailash': (
        'The solitary summit is a sacred landmark for Hindu, Buddhist, Jain and Bön traditions. It is mapped '
        'on the Tibet side of the Himalaya, where its silhouette can be read in relation to the surrounding '
        'plateau.'
    ),
    'statue-of-unity': (
        'The figure overlooks the Narmada valley from its river setting near the dam. Its scale changes how '
        'the site reads from across the water, where the standing silhouette is visible against the hills.'
    ),
    'whc-252': (
        'A long garden axis leads to the marble tomb, with the Yamuna immediately beyond. The dome and its '
        'four minarets give the building its symmetry, while the river sets the far edge of the complex.'
    ),
    'whc-1056': (
        'The temple and Bodhi tree form the centre of an active pilgrimage landscape at Bodh Gaya. The tower '
        'gives the compound a vertical marker, while the tree identifies the place associated with the '
        'awakening.'
    ),
    'whc-1101': (
        'Read Champaner and Pavagadh together. The hill carries defensive and sacred sites, while the former '
        "city below preserves its mosques and water systems. The rise between them is part of the site's "
        'structure.'
    ),
    'whc-1321': (
        "The civic buildings occupy the northern end of Chandigarh's grid. Their large concrete forms and the "
        'open spaces between them give government a distinct place in the planned city.'
    ),
    'whc-1338': (
        'The instruments at Jaipur are buildings you can walk around. Their carefully set angles turn a clear '
        'view of the sky into readings of time and celestial position.'
    ),
    'whc-1342': (
        'This entry represents a chain of landscapes along the western escarpment. Elevation and rainfall '
        'vary along the range, shaping the patches of forest that harbour much of its distinctive '
        'biodiversity.'
    ),
    'whc-1375': (
        'The buildings at Santiniketan share their role with courtyards and outdoor teaching spaces. That '
        "relationship between learning and the landscape helps explain the character of Tagore's settlement."
    ),
    'whc-1406': (
        'Valley floors and forest give way to meadows and exposed ridges as you climb. The difference in '
        'elevation is the defining feature of this protected section of the western Himalaya.'
    ),
    'whc-1480': (
        'The open Oval Maidan is the best guide to the ensemble. Look across it to compare the older Gothic '
        'public buildings with the later, lower Art Deco street fronts.'
    ),
    'whc-1502': (
        'The archaeological remains show how teaching and religious life shared the same complex. The '
        'repeated brick courts of the monasteries sit alongside the more prominent shrine structures.'
    ),
    'whc-1513': (
        'The mountain is part of a larger landscape of glaciers, valleys and settlements. The heritage '
        'designation includes both the natural range and the sacred associations that give it meaning in '
        'Sikkim.'
    ),
    'whc-1551': (
        "Ahmedabad's older quarters are organised through lanes, courtyards and traditional neighbourhoods. "
        'The Sultanate monuments sit within that dense urban fabric, giving the site its character as a '
        'living city.'
    ),
    'whc-1570': (
        'A raised platform lets the sculpted exterior be read as you circle the temple. The composition '
        'brings the masonry, bracket figures and carved walls together in a compact enclosure.'
    ),
    'whc-1605': (
        "The gates and market streets make Jaipur's planned layout easy to follow. Long commercial streets "
        'organise the blocks, with gateways marking the transition through the walled city.'
    ),
    'whc-1645': (
        "Dholavira's reservoirs make the settlement's approach to scarce water visible. Stone walls divide "
        'the city, and the location within the Rann helps explain why water storage mattered.'
    ),
    'whc-1670': (
        'The star-shaped plans create a long succession of angled exterior walls. Those faces give the carved '
        'bands room to unfold as visitors walk around the Hoysala temples.'
    ),
    'whc-1711': (
        'The raised forms of the Charaideo burial mounds mark chambers beneath the surface. Their spacing and '
        'relation to the surrounding ground make the burial landscape legible as a whole.'
    ),
    'whc-1739': (
        'The group can be read as a network of defensive positions. High forts use ridges and escarpments, '
        'while coastal ones command approaches by water.'
    ),
    'whc-231': (
        'The red walls give the fort its city-facing silhouette. Inside, courts, audience halls and palace '
        'spaces show how the ramparts enclosed a seat of Mughal government as well as a residence.'
    ),
    'whc-232': (
        "At Humayun's Tomb, the path towards the dome follows the geometry of the garden. Causeways and "
        'channels divide the grounds and keep the tomb at their centre.'
    ),
    'whc-233': (
        'The tower rises above a wider group of early Sultanate monuments. Its fluted shaft is the most '
        'visible element, while the lower buildings reveal the scale of the site around it.'
    ),
    'whc-234': (
        "The churches are reminders of Old Goa's place in Portuguese maritime networks. Read the group as an "
        'ecclesiastical district, with buildings of different scales occupying the former city.'
    ),
    'whc-239': (
        'At Pattadakal, contrasting tower profiles can be compared within walking distance along the river. '
        'Their proximity makes the ensemble a good place to see different temple forms together.'
    ),
    'whc-240': (
        'The temples of Khajuraho are composed in layers, from bands of carving at walking height to '
        'clustered towers above. The effect is especially clear when seen in profile across the grounds.'
    ),
    'whc-241': (
        "Hampi's monuments occupy a terrain of granite boulders and river crossings. The surviving temples "
        'and royal precincts make more sense when read as parts of a city spread across that landscape.'
    ),
    'whc-242': (
        'The ravine gives the Ajanta caves a continuous curved frontage. Their interiors preserve different '
        'kinds of Buddhist spaces, including halls for worship and chambers linked to monastic life.'
    ),
    'whc-243': (
        "Ellora's religious buildings share the same rock escarpment. In the Kailasa temple, excavation left "
        'a freestanding mass of stone that could be shaped into a complete architectural form.'
    ),
    'whc-244': (
        'The harbour crossing is part of the setting of the Elephanta caves. Inside the main cave, the '
        'multi-faced Shiva image is the focus of a much larger rock-cut interior.'
    ),
    'whc-246': (
        'Konark makes the chariot idea visible at building scale. The huge stone wheels and horses establish '
        'the design, and their relief work rewards a closer view from the ground.'
    ),
    'whc-247': (
        'The forts use steep slopes to extend their defences. Their interior spaces also tell a story about '
        'life inside the walls, where palaces and other settlement buildings occupied the protected ground.'
    ),
    'whc-249': (
        "The shore is central to Mahabalipuram's setting. The group lets visitors compare freestanding "
        'shrines, excavated forms and large reliefs within one Pallava coastal settlement.'
    ),
    'whc-250': (
        'The Chola temple towers dominate their enclosures and the surrounding ground. Their height and '
        'sculpted profiles make the central sanctuaries identifiable at a distance.'
    ),
    'whc-251': (
        'From the Yamuna side, the fort reads as a long wall above the water. Move through its gates and the '
        'scale changes to courts, audience halls and palace buildings that show how the Mughal court used the '
        'enclosure.'
    ),
    'whc-255': (
        'Fatehpur Sikri is organised as a former capital rather than a single palace. Its courts, open spaces '
        'and ceremonial gateway establish distinct routes through the red sandstone complex.'
    ),
    'whc-335': (
        'The protected landscapes around Nanda Devi range from flower-rich alpine meadows to high rock and '
        'ice. Their different elevations account for much of the variation visible on the map.'
    ),
    'whc-337': (
        "Kaziranga's grasslands depend on the seasonal movement of water across the Brahmaputra floodplain. "
        'The mosaic of grass, wet ground and higher refuges helps explain why it is important rhinoceros '
        'habitat.'
    ),
    'whc-338': (
        'In Manas, rivers run out of the foothills and across a changing mix of grassland and forest. The '
        "park's border setting connects these habitats to the landscape immediately north in Bhutan."
    ),
    'whc-340': (
        "Keoladeo's water levels are managed. Shallow flooded ground and drier margins change through the "
        'seasons and give different groups of waterbirds places to feed and rest.'
    ),
    'whc-452': (
        'The Sundarbans are easiest to read as a network of tidewater channels. The mangroves sit on the '
        'ground between them, where salt water and river sediment continually reshape the edges.'
    ),
    'whc-524': (
        'The carved gateways at Sanchi mark the approaches to the stupa. Movement around the mound brings '
        'visitors past each gate in turn, with the plain visible from the hill outside.'
    ),
    'whc-922': (
        'Rani-ki-Vav uses steps and terraces to lead down towards the water. The descent reveals successive '
        'bands of sculpture and makes the well into an extended architectural space.'
    ),
    'whc-925': (
        'The Bhimbetka paintings occupy sheltered rock faces rather than constructed interiors. The sandstone '
        'formations and their protected recesses explain why traces of repeated human use survive here.'
    ),
    'whc-927': (
        'At Sarnath the stupas and monastery remains occupy the wider setting of the place associated with '
        "the Buddha's first discourse. The site records both pilgrimage and established religious "
        'communities.'
    ),
    'whc-944': (
        'Hill railways solve the climb through curves, loops and changes of direction. Their alignment shows '
        'how railway builders used limited space on steep slopes to hold manageable gradients.'
    ),
    'whc-945': (
        'The terminus combines an ornate public front with the practical requirements of a working railway. '
        'Its large interior spans and exposed ornament make those two roles visible in the same complex.'
    ),
    'golconda-fort': (
        'The route to the citadel climbs through the defences in stages. Granite slopes and masonry work '
        'together, making the hill itself part of the fortress.'
    ),
    'udayagiri-khandagiri': (
        'The chambers cut into the two hills alternate with more elaborate carved fronts. The paired hills '
        'show the extent of the site beyond any single cave entrance.'
    ),
    'barren': (
        "Barren Island's central cone sits inside a breached caldera. The surrounding sea makes the outer "
        'flanks and volcanic profile especially clear from offshore.'
    ),
    'cellular-jail': (
        'The wings of the former prison were laid out to make the cells easy to supervise. In the surviving '
        'buildings, the repeating rows of isolated cells still convey the purpose of the plan.'
    ),
    'charminar': (
        'The four towers mark a junction as much as a building. Streets approach its arches from different '
        "directions, keeping the monument visible within Hyderabad's older commercial centre."
    ),
    'chilika': (
        'From the shore, Chilika looks like a lake, but its opening to the sea is central to its character. '
        "The balance of fresh and salt water helps shape the lagoon's bird and fish habitats."
    ),
    'golden-temple': (
        'Approaching the shrine means first crossing the water on the causeway. The pool opens a clear view '
        'of the gilded building and gives the pilgrimage complex its central space.'
    ),
    'lepakshi': (
        'The stone columns and painted ceilings are best read from inside the halls. The nearby monolithic '
        'Nandi makes the temple part of a wider collection of carved sites around the village.'
    ),
    'majuli': (
        'The island is bordered by active Brahmaputra channels. Erosion and new deposits shift those edges '
        "over time, so its outline is part of the river's story rather than a fixed boundary."
    ),
    'mawsmai': (
        'The cave passages follow openings enlarged by water in limestone. Inside, narrow walls and mineral '
        'formations show the process at a scale that is hard to see on the surface.'
    ),
    'root-bridge': (
        'The two crossings at Nongriat occupy different heights over the same stream. They were made by '
        'guiding living roots across the gap, so their structure continues to grow.'
    ),
    'sirpur': (
        "The brick shrine's masonry makes a contrast with its carved doorway. The building is one part of an "
        'archaeological landscape that preserves several kinds of worship and settlement.'
    ),
    'st-marys': (
        'At the shore, the ends of the rock columns show their polygonal form. The platforms and broken faces '
        'make the jointing visible from several angles as you move around the islands.'
    ),
    'thembang': (
        'The walls and gates follow the terrain around the village. They give the Monpa settlement a clear '
        'perimeter and recall the practical importance of controlling approaches through the hills.'
    ),
    'unakoti': (
        'The hillside is the surface for the carved faces and figures. Different rock exposures create a '
        'sequence of images through the wooded site rather than a single enclosed monument.'
    ),
    'loktak': (
        'The floating vegetation mats are part of what distinguishes Loktak from nearby lakes. Their outlines '
        'and position can change with water conditions, which gives the surface a shifting patchwork.'
    ),
    'lonar': (
        'The bowl of the crater is clearest from the rim. Below it, the enclosed lake marks the low point '
        'left by the impact in the basalt of the Deccan.'
    ),
    'tso-moriri': (
        'The lake occupies an open basin in the high Changthang. Its water and shore sit in marked contrast '
        'with the dry slopes surrounding them.'
    ),
    'aayi-mandapam': (
        'The pavilion stands in a public garden, where its open form can be read from several paths. Its '
        'scale and central position make it a reference point within the old town.'
    ),
    'dal-lake': (
        'Dal Lake is a working waterscape as well as a landmark. Channels connect the floating gardens and '
        "settled edges, so the lake's internal routes are part of Srinagar's geography."
    ),
    'dinosaur-fossils': (
        'The Siwalik sediments preserve remains of prehistoric mammals. The geological setting matters '
        'because successive layers preserve evidence of life in the foothills over a long interval.'
    ),
    'diu-fort': (
        'The fort makes sense from the water approach to Diu. Its ramparts face the harbour entrance, where '
        'it could command the narrow coastal passage.'
    ),
    'dzu': (
        'The valley opens above the surrounding forest into long grassy slopes. Seasonal flowers accent that '
        'change in vegetation, and the ridges make the valley easy to recognise on the map.'
    ),
    'hundru-falls': (
        'The river follows the plateau before dropping over its steep edge. The fall gives a clear view of '
        'the change in elevation that shapes this part of the Subarnarekha valley.'
    ),
    'jog': (
        'The separate falls share the same escarpment, with their relative flow changing through the seasons. '
        'A view across the gorge gives the clearest sense of their height and arrangement.'
    ),
    'minicoy-light': (
        "The lighthouse rises above Minicoy's low island profile. Its place near the southern end makes it a "
        'marker for vessels passing close to the island.'
    ),
    'morni': (
        'The Tikkar Tal lakes sit in hollows between Siwalik ridges. The change from the plains to the narrow '
        "basins is visible even at the atlas's coarse scale."
    ),
    'murlen': (
        "Murlen's forest follows a succession of ridges and valleys along eastern Mizoram. The folds of the "
        'hills give the protected forest its shape.'
    ),
    'nohkalikai': (
        'The waterfall leaves the high ground near Sohra and plunges into a deep, wooded gorge. The rock edge '
        'and open drop are the most legible parts of the landscape from across the valley.'
    ),
    'rann': (
        'The flat terrain makes the seasonal change in water especially visible. As shallow flooding recedes, '
        'salt remains exposed across a broad surface between the surrounding land and tidal inlets.'
    ),
}
