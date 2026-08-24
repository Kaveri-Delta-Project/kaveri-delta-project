import os
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
    BUILD_DIR,
    ENTITY_CONFIG
    )


#build a dictionary mapping each entity type to its configured directory
file_directories = {
    key: config["dir"]
    for key, config in ENTITY_CONFIG.items()
}

#build a dictionary mapping each entity type to its configured title
title_ents = {
    key: config["title_ent"]
        for key, config in ENTITY_CONFIG.items()
}

#store the preferred name alongside XML ID for each entity
entities_cache = {}

#store all extracted entity data by entity type
all_entities = {}

#store data used to link entities to related entities
ref_cache = {}

#define the relationships between entity types
#e.g. persons related to places are stored in place entities
#so they can be displayed in the place index
cross_refs = {
    "person": [("place", link_persons_to_places)],
    "inscription": [("place", link_inscriptions_to_places)],
    "work": [("person", link_works_to_persons)]
}

#load and process the data for each entity type
for entity_tag, directory in file_directories.items():
    
    #load the extracted data from the entity directory
    entity_data = load_dir_data(entity_tag, directory)
    all_entities[entity_tag] = entity_data

    #create and store a cache of entity IDs and preferred names
    entity_cache = create_entity_cache(entity_data)
    entities_cache.update(entity_cache)

    #build cross-reference data for entity types with defined relationships
    if entity_tag in cross_refs:
        for linked_ent, ref_function in cross_refs[entity_tag]: 
            ref_data = ref_function(entity_data)
            ref_cache[(linked_ent, entity_tag)] = ref_data

#loop through again and add cross-reference data to each entity
for entity_tag, entity_data in all_entities.items():

    #find reference data that belongs to the current entity type
    ref_matches = {
        k: v for k, v in ref_cache.items()
        if k[0] == entity_tag
    }

    #add each matching reference list to its corresponding entity
    for ref_ent, data in ref_matches.items():
        
        #convert the reference entity types into a field name
        ref_ent_str = "_".join(ref_ent)

        #for each entity item find its reference data
        for ent in entity_data:
            key = ent["xml_id"]
            ent[ref_ent_str] = data.get(key, [])

    #group the entities alphabetically by their preferred name
    ent_data_alpha = group_items_alphabetically(entity_data)

    #render the grouped entities into index sections
    body_html = render_index_sections(ent_data_alpha, entity_tag)

    #create the title for the entity index page
    index_title = (f"{title_ents[entity_tag]} Index").title()
    index_html = render_page(index_title, body_html)

    #create the output path for the entity index
    output_path = os.path.join(BUILD_DIR, f"{entity_tag}_index.html")
    os.makedirs(os.path.join(BUILD_DIR), exist_ok=True)
    
    #write the generated index page to the build directory
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_html))
        print(f"Index built in {output_path}")

    #remove invalid entity links from the generated index
    #while excluding links marked as references
    remove_broken_links(output_path, entities_cache, exclude_classes=["reference"])
    
#build the JSON search index after all entity data has been processed
build_search_index(all_entities, BUILD_DIR)

