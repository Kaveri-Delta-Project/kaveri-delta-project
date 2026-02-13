import os
from collections import defaultdict

from config import (
    BASE_DIR,
    MS_DIR,
    PERSONS_DIR,
    WORKS_DIR,
    PLACES_DIR,
    NSMAP,
    XML_CACHE,
)

from tei_helpers import (
    get_xml_tree,
    load_xml_by_id,
    get_cached_tree,
    extract_element_text,
    extract_attribute_values,
    get_main_file_data,
    extract_reference_data,
)

from render_index import (
    render_alphabet_nav,
    render_index_sections,
    render_page,
)

output_file = os.path.join(BASE_DIR, "build", "ms_index.html")
os.makedirs(os.path.join(BASE_DIR, "build"), exist_ok=True)

#mapping of work ID to persons and places associated with work
work_to_persons = defaultdict(list)
work_to_places = defaultdict(list)

#process the works files
for work_filename in sorted(os.listdir(WORKS_DIR)):
    
    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    work_data = get_main_file_data(work_filename, WORKS_DIR, NSMAP, "bibl", "title", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not work_data:
        continue
    wk_tree, wk_id_text, wk_name_text, wk_first_letter =  work_data

    #extract persons associated with this work and associate with work id
    work_persons = extract_reference_data(wk_tree, NSMAP, PERSONS_DIR, "editor", "persName", XML_CACHE)
    work_to_persons[wk_id_text].extend(work_persons)

    #extract places associated with this work and associate with work id
    work_places = extract_reference_data(wk_tree, NSMAP, PLACES_DIR, "pubPlace", "placeName", XML_CACHE)
    work_to_places[wk_id_text].extend(work_places)


#dictionary keyed by first letter (A–Z)
ms_by_letter = defaultdict(list)

#iterate through each manuscript TEI file
for filename in sorted(os.listdir(MS_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    main_data = get_main_file_data(filename, MS_DIR, NSMAP, "msDesc", "msName", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not main_data:
        continue
    ms_tree, ms_id_text, ms_name_text, ms_first_letter =  main_data

    #extract persons, places and works directly referenced in the manuscript TEI
    ms_persons = extract_reference_data(ms_tree, NSMAP, PERSONS_DIR, "persName", "persName", XML_CACHE)
    ms_places = extract_reference_data(ms_tree, NSMAP, PLACES_DIR, "origPlace", "placeName", XML_CACHE)
    ms_works = extract_reference_data(ms_tree, NSMAP, WORKS_DIR, "title", "title", XML_CACHE)

    #sort manuscript_works by id
    ms_works = sorted(ms_works, key=lambda x: x[0])

    #containers for data gathered from related works
    work_persons = []
    work_places = []

    #iterate through work ids associated with manuscript
    #extract related data from work files
    for wk_id, wk_name in ms_works:
        work_persons.extend(work_to_persons[wk_id])
        work_places.extend(work_to_places[wk_id])

    #add manuscript entry to the appropriate alphabetical group
    #add directly referenced data from manuscript file
    #add related data from other files
    ms_by_letter[ms_first_letter].append({
        "id": ms_id_text,
        "name": ms_name_text,
        "persons": ms_persons,
        "places": ms_places,
        "related works": ms_works,
        "related work persons": work_persons,
        "related work places": work_places
    })

#convert the structured index data into HTML sections
body_html = render_index_sections(
    ms_by_letter,
    include_keys=["persons", "places", "related works", "related work persons", "related work places"]
)

#wrap sections in full HTML document
html = render_page("Manuscripts Index", body_html)

#write final HTML file to disk
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"Index generated at {output_file}")

