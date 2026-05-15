import os
from collections import defaultdict
from render_index import render_index_sections, render_page

from tei_helpers import (
    load_entity, 
    load_dir_data,
    group_items_alphabetically,
    create_entity_cache, 
    remove_broken_links, 
    build_search_index,
    link_persons_to_places,
    link_inscriptions_to_places,
    link_works_to_persons
    )

from config import (
    BASE_DIR,
    ISC_DIR,
    PERSONS_DIR,
    WORKS_DIR,
    PLACES_DIR,
    BUILD_DIR
    )


file_directories = {
    "inscription": ISC_DIR,
    "person": PERSONS_DIR,
    "work": WORKS_DIR,
    "place": PLACES_DIR    
    }

entities_cache = {}
all_entities = {}
ref_cache = {}

cross_refs = {
    "person": [("place", link_persons_to_places)],
    "inscription": [("place", link_inscriptions_to_places)],
    "work": [("person", link_works_to_persons)]
}

for entity_tag, directory in file_directories.items():
    entity_data = load_dir_data(entity_tag, directory)
    all_entities[entity_tag] = entity_data

    entity_cache = create_entity_cache(entity_data)
    entities_cache.update(entity_cache)

    if entity_tag in cross_refs:
        for linked_ent, ref_function in cross_refs[entity_tag]: 
            ref_data = ref_function(entity_data)
            ref_cache[(linked_ent, entity_tag)] = ref_data

for entity_tag, entity_data in all_entities.items():

    ref_matches = {
        k: v for k, v in ref_cache.items()
        if k[0] == entity_tag
    }

    for ref_ent, data in ref_matches.items():
        ref_ent_str = "_".join(ref_ent)

        for ent in entity_data:
            key = ent["xml_id"]
            ent[ref_ent_str] = data.get(key, [])

    ent_data_alpha = group_items_alphabetically(entity_data)

    body_html = render_index_sections(ent_data_alpha, entity_tag)

    index_title = (f"{entity_tag} Index").title()
    index_html = render_page(index_title, body_html)

    output_path = os.path.join(BUILD_DIR, f"{entity_tag}_index.html")
    os.makedirs(os.path.join(BUILD_DIR), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_html))
        print(f"Index built in {output_path}")

    remove_broken_links(output_path, entities_cache)
    
build_search_index(all_entities, BUILD_DIR)



	
