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

output_file = os.path.join(BASE_DIR, "build", "works_index.html")
os.makedirs(os.path.join(BASE_DIR, "build"), exist_ok=True)

#mapping of work ID to related manuscripts
#and persons / places associated with related manuscripts
work_to_manuscripts = defaultdict(list)
manuscript_to_persons = defaultdict(list)
manuscript_to_places = defaultdict(list)

#process the manuscript files
for ms_filename in sorted(os.listdir(MS_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    ms_data = get_main_file_data(ms_filename, MS_DIR, NSMAP, "msDesc", "msName", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not ms_data:
        continue
    ms_tree, ms_id_text, ms_name_text, ms_first_letter =  ms_data

    #extract ids for works associated with this manuscript
    ms_works = extract_attribute_values(ms_tree, NSMAP, element="title", filter_attr="key", all_results=True)

    #extract persons associated with this manuscript
    ms_persons = extract_reference_data(ms_tree, NSMAP, PERSONS_DIR, "persName", "persName", XML_CACHE)

    #extract places associated with this manuscript (e.g. place of origin)
    ms_places = extract_reference_data(ms_tree, NSMAP, PLACES_DIR, "origPlace", "placeName", XML_CACHE)

    #sort work ids alphabetically
    ms_works = sorted(ms_works)

    #associate manuscripts, manuscript persons and manuscript places with each referenced work for manuscript
    for work_id in ms_works:
        work_to_manuscripts[work_id].append((ms_id_text, ms_name_text))
        manuscript_to_persons[work_id].extend(ms_persons)
        manuscript_to_places[work_id].extend(ms_places)


#dictionary keyed by first letter (A–Z)
works_by_letter = defaultdict(list)

#iterate through each work TEI file
for filename in sorted(os.listdir(WORKS_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    main_data = get_main_file_data(filename, WORKS_DIR, NSMAP, "bibl", "title", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not main_data:
        continue
    tree, id_text, name_text, first_letter =  main_data

    #extract persons and places directly referenced in the work TEI file
    work_persons = extract_reference_data(tree, NSMAP, PERSONS_DIR, "editor", "persName", XML_CACHE)
    work_places = extract_reference_data(tree, NSMAP, PLACES_DIR, "pubPlace", "placeName", XML_CACHE)

    #add work entry to the appropriate alphabetical group
    #add directly referenced data from work file
    #use work id to extract related data from other files
    works_by_letter[first_letter].append({
        "id": id_text,
        "name": name_text,
        "persons": work_persons,
        "places": work_places,
        "related manuscripts": work_to_manuscripts[id_text],
        "related manuscript persons": manuscript_to_persons[id_text],
        "related manuscript places": manuscript_to_places[id_text],
    })

#convert the structured index data into HTML sections
body_html = render_index_sections(
    works_by_letter,
    include_keys=["persons", "places", "related manuscripts", "related manuscript persons", "related manuscript places"]
)

#wrap sections in full HTML document
html = render_page("Works Index", body_html)

#write final HTML file to disk
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"Index generated at {output_file}")

