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

output_file = os.path.join(BASE_DIR, "build", "places_index.html")
os.makedirs(os.path.join(BASE_DIR, "build"), exist_ok=True)

#mapping of place ID to related works
#and persons associated with related works
place_to_works = defaultdict(list)
place_to_work_persons = defaultdict(list)

#mapping of place ID to related manuscripts
#and persons associated with related manuscripts
place_to_manuscripts = defaultdict(list)
place_to_manuscript_persons = defaultdict(list)

#process the works files
for work_filename in sorted(os.listdir(WORKS_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    work_data = get_main_file_data(work_filename, WORKS_DIR, NSMAP, "bibl", "title", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not work_data:
        continue
    wk_tree, wk_id_text, wk_name_text, wk_first_letter =  work_data

    #extract ids for places associated with this work
    work_places = extract_attribute_values(wk_tree, NSMAP, element="pubPlace", filter_attr="key", all_results=True)

    #extract persons associated with this work
    work_persons = extract_reference_data(wk_tree, NSMAP, PERSONS_DIR, "editor", "persName", XML_CACHE)

    #associate works and work persons with each referenced place for work
    for place_id in work_places:
        place_to_works[place_id].append((wk_id_text, wk_name_text))
        place_to_work_persons[place_id].extend(work_persons)

#process the manuscript files
for ms_filename in sorted(os.listdir(MS_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    ms_data = get_main_file_data(ms_filename, MS_DIR, NSMAP, "msDesc", "msName", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not ms_data:
        continue
    ms_tree, ms_id_text, ms_name_text, ms_first_letter =  ms_data

    #extract ids for places associated with this manuscript
    ms_places = extract_attribute_values(ms_tree, NSMAP, element="origPlace", filter_attr="key", all_results=True)

    #extract persons associated with this manuscript
    ms_persons = extract_reference_data(ms_tree, NSMAP, PERSONS_DIR, "persName", "persName", XML_CACHE)

    #associate manuscripts and manuscript persons with each referenced place for manuscript
    for place_id in ms_places:
        place_to_manuscripts[place_id].append((ms_id_text, ms_name_text))
        place_to_manuscript_persons[place_id].extend(ms_persons)


#dictionary keyed by first letter (A–Z)
places_by_letter = defaultdict(list)

#iterate through each place TEI file
for filename in sorted(os.listdir(PLACES_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    main_data = get_main_file_data(filename, PLACES_DIR, NSMAP, "place", "placeName", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not main_data:
        continue
    tree, id_text, name_text, first_letter =  main_data

    #add place entry to the appropriate alphabetical group
    #use place id to extract related data from other files
    places_by_letter[first_letter].append({
        "id": id_text,
        "name": name_text,
        "related manuscripts": place_to_manuscripts[id_text],
        "related manuscript persons": place_to_manuscript_persons[id_text],
        "related works": place_to_works[id_text],
        "related work persons": place_to_work_persons[id_text]
    })

#convert the structured index data into HTML sections
body_html = render_index_sections(
    places_by_letter,
    include_keys=["related manuscripts", "related manuscript persons", "related works", "related work persons"]
)

#wrap sections in full HTML document
html = render_page("Places Index", body_html)

#write final HTML file to disk
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"Index generated at {output_file}")

