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

output_file = os.path.join(BASE_DIR, "build", "persons_index.html")
os.makedirs(os.path.join(BASE_DIR, "build"), exist_ok=True)

#mapping of person ID to related works
#and places associated with related works
person_to_works = defaultdict(list)
person_to_work_places = defaultdict(list)

#mapping of person ID to related manuscripts
#and places associated with related manuscripts
person_to_manuscripts = defaultdict(list)
person_to_manuscript_places = defaultdict(list)

#process the works files
for work_filename in sorted(os.listdir(WORKS_DIR)):
    
    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    work_data = get_main_file_data(work_filename, WORKS_DIR, NSMAP, "bibl", "title", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not work_data:
        continue
    wk_tree, wk_id_text, wk_name_text, wk_first_letter =  work_data

    #extract ids for persons associated with this work
    work_persons = extract_attribute_values(wk_tree, NSMAP, element="editor", filter_attr="key", all_results=True)

    #extract places associated with this work (e.g. publication places)
    work_places = extract_reference_data(wk_tree, NSMAP, PLACES_DIR, "pubPlace", "placeName", XML_CACHE)

    #associate works and work places with each referenced person for work
    for person_id in work_persons:
        person_to_works[person_id].append((wk_id_text, wk_name_text))
        person_to_work_places[person_id].extend(work_places)

#process the manuscript files
for ms_filename in sorted(os.listdir(MS_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    ms_data = get_main_file_data(ms_filename, MS_DIR, NSMAP, "msDesc", "msName", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not ms_data:
        continue
    ms_tree, ms_id_text, ms_name_text, ms_first_letter =  ms_data

    #extract ids for persons associated with this manuscript
    ms_persons = extract_attribute_values(ms_tree, NSMAP, element="persName", filter_attr="key", all_results=True)

    #extract places associated with this manuscript (e.g. place of origin)
    ms_places = extract_reference_data(ms_tree, NSMAP, PLACES_DIR, "origPlace", "placeName", XML_CACHE)

    #associate manuscripts and manuscript places with each referenced person for manuscript
    for person_id in ms_persons:
        person_to_manuscripts[person_id].append((ms_id_text, ms_name_text))
        person_to_manuscript_places[person_id].extend(ms_places)


#dictionary keyed by first letter (A–Z)
persons_by_letter = defaultdict(list)

#iterate through each person TEI file
for filename in sorted(os.listdir(PERSONS_DIR)):

    #extract: parsed XML tree, xml:id, display name, first letter for alphabetical grouping
    main_data = get_main_file_data(filename, PERSONS_DIR, NSMAP, "person", "persName", XML_CACHE)
    #skip files that fail to parse or lack required data
    if not main_data:
        continue
    tree, id_text, name_text, first_letter =  main_data

    #extract affiliated places directly referenced in the person TEI file
    affiliations = extract_reference_data(tree, NSMAP, PLACES_DIR, "affiliation", "placeName", XML_CACHE)

    #add person entry to the appropriate alphabetical group
    #add directly referenced data from person file
    #add related data from other files
    persons_by_letter[first_letter].append({
        "id": id_text,
        "name": name_text,
        "affiliations": affiliations,
        "related manuscripts": person_to_manuscripts[id_text],
        "related manuscript places": person_to_manuscript_places[id_text],
        "related works": person_to_works[id_text],
        "related work places": person_to_work_places[id_text]
    })

#convert the structured index data into HTML sections
body_html = render_index_sections(
    persons_by_letter,
    include_keys=["affiliations", "related manuscripts", "related manuscript places", "related works", "related work places"]
)

#wrap sections in full HTML document
html = render_page("Persons Index", body_html)

#write final HTML file to disk
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"Index generated at {output_file}")




