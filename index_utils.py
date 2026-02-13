import os
import json

from utils import load_ent_name_by_key

from config import ENTITY_CONFIG, NSMAP, BASE_DIR, DATA_DIR, INDEX_DIR


os.makedirs(INDEX_DIR, exist_ok=True)


def get_index_file(entity):
    """Return path to the JSON index file for a given entity."""
    return os.path.join(INDEX_DIR, f"{entity}.json")

def rebuild_entity_index(entity):
    config = ENTITY_CONFIG[entity]
    entity_dir = config["dir"]
    element_tag = config["element_tag"]
    name_tag = config.get("name_tag")
    
    index_data = []

    for filename in sorted(os.listdir(entity_dir)):
        if not filename.endswith(".xml"):
            continue

        xml_id = filename[:-4]
        file_path = os.path.join(entity_dir, filename)

        name = load_ent_name_by_key(entity, xml_id, name_tag)

        if not name:
            name = xml_id

        index_data.append({
            "xml_id": xml_id,
            "name": name
        })

    # Sort alphabetically by name
    index_data.sort(key=lambda x: x["name"].lower())

    # Save index
    with open(get_index_file(entity), "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

def load_index(entity):
    """Load JSON index for entity type; rebuild if missing."""
    path = get_index_file(entity)
    if not os.path.exists(path):
        rebuild_entity_index(entity)
    
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def update_index_entry(entity, xml_id):
    """Incrementally update JSON index for a single entity."""
    
    config = ENTITY_CONFIG[entity]
    name_tag = config.get("name_tag")
    path = get_index_file(entity)
    index_data = []

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            index_data = json.load(f)

        # Remove any existing entry for this XML ID
        index_data = [entry for entry in index_data if entry["xml_id"] != xml_id]

    name = load_ent_name_by_key(entity, xml_id, name_tag)

    if not name:
        name = xml_id

    # Append updated entry
    index_data.append({"xml_id": xml_id, "name": name})

    # Sort by name
    index_data.sort(key=lambda x: x["name"].lower())

    with open(path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

def delete_index_entry(entity, xml_id):
    """Remove an entry from the JSON index for a single entity."""
    path = get_index_file(entity)
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        index_data = json.load(f)

    # Remove the entry with matching xml_id
    index_data = [entry for entry in index_data if entry["xml_id"] != xml_id]

    # Save back to JSON
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


