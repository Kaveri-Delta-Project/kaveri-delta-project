import os
from collections import defaultdict
from tei_helpers import load_entity, load_dir_data, group_items_alphabetically, create_entity_cache, remove_broken_links
from render_index import render_index_sections, render_page

from config import (
    BASE_DIR,
    MS_DIR,
    PERSONS_DIR,
    WORKS_DIR,
    PLACES_DIR,
    BUILD_DIR
)


file_directories = {
    "person": PERSONS_DIR,
    "manuscript": MS_DIR,
    "work": WORKS_DIR,
    "place": PLACES_DIR    
}

entities_cache = {}

for entity_tag, directory in file_directories.items():
    entity_data = load_dir_data(entity_tag, directory)

    entity_cache = create_entity_cache(entity_data)
    entities_cache.update(entity_cache)

    ent_data_alpha = group_items_alphabetically(entity_data)

    body_html = render_index_sections(ent_data_alpha, entity_tag)

    index_title = (f"{entity_tag} Index").title()
    index_html = render_page(index_title, body_html)

    output_path = os.path.join(BUILD_DIR, f"{entity_tag}_index.html")
    os.makedirs(os.path.join(BUILD_DIR), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_html))
        print(f"Index built in {output_path}")

for entity_tag in file_directories.keys():
    
    html_path = os.path.join(BUILD_DIR, f"{entity_tag}_index.html")
    remove_broken_links(html_path, entities_cache)




	
