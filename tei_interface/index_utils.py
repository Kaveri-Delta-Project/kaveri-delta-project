import os
import json
from lxml import etree

from utils import load_ent_name_by_key, load_or_create_entity, write_entity_to_file, build_section, insert_in_order

from config import ENTITY_CONFIG, NSMAP, BASE_DIR, DATA_DIR, INDEX_DIR, RELATIONSHIP_INVERSES, TEXT_ELEMS


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


def update_connection_index(entity, linked_id, xml_id, entity_type, entity_text):

    entity_ind_name = f"{entity}_connections"

    path = get_index_file(entity_ind_name)

    index_data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            index_data = json.load(f)

    index_data.setdefault(linked_id, []).append([xml_id, entity_type, entity_text])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def update_connection_files(entity, key):

    connections_name = f"{entity}_connections"
    
    index_path = get_index_file(entity)
    connections_path = get_index_file(connections_name)

    if not os.path.exists(index_path) or not os.path.exists(connections_path):
        return

    with open(index_path, encoding="utf-8") as f:
        index_data = json.load(f)

    with open(connections_path, encoding="utf-8") as f:
        connections_data = json.load(f)

    index_name = next((item["name"] for item in index_data if item["xml_id"] == key), None)

    if index_name is None:
        return 

    connections = connections_data.get(key)

    if not connections:
        return

    updated_connections = []

    for connection in connections:

        linked_id, linked_ent, orig_name = connection

        config = ENTITY_CONFIG[linked_ent]

        context = load_or_create_entity(
            entity_name=linked_ent,
            entity_dir=config["dir"],
            template_path=config["template"],
            xml_id=linked_id,
            nsmap=NSMAP
        )

        if not context:
            updated_connections.append([linked_id, linked_ent, orig_name])
            continue

        if entity == "person" and linked_ent == "manuscript":
            entity_elem = context["root"].find(".//tei:listPerson", namespaces=NSMAP)
        else:
            entity_elem = context["entity_elem"]

        changed = False

        for elem in entity_elem.xpath(f'.//*[@key="{key}"]'):
            if elem.text and elem.text.strip() == orig_name:
                elem.text = index_name
                changed = True
            else:
                for tag in TEXT_ELEMS:
                    candidates = elem.xpath(f".//*[local-name()='{tag}']")
                    for c in candidates:
                        if c.text and c.text.strip() == orig_name:
                            c.text = index_name
                            changed = True

        if changed:
            write_entity_to_file(context)

        updated_connections.append([linked_id, linked_ent, index_name])

    connections_data[key] = updated_connections

    with open(connections_path, "w", encoding="utf-8") as f:
        json.dump(connections_data, f, indent=2, ensure_ascii=False)


def delete_connection_entry(xml_id, form_data):


    key = form_data.get("key")
    entity = form_data.get("name_type")
    entity_name = form_data.get("name")

    entity_ind_name = f"{entity}_connections"

    path = get_index_file(entity_ind_name)

    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        index_data = json.load(f)

    if key in index_data and isinstance(index_data[key], list):
        for i, item in enumerate(index_data[key]):
            if item[0] == xml_id and item[2] == entity_name:
                del index_data[key][i]
                break

    with open(path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)


def related_add(relationship, key, person_a_key, person_a_text, reverse_type, config, person_a_from=None, person_a_to=None):    

    context = load_or_create_entity(
        entity_name="person",
        entity_dir=config["dir"],
        template_path=config["template"],
        xml_id=key,
        nsmap=NSMAP
    )
    if context:
        person_b = context["entity_elem"]

        if not person_a_key or not person_a_text:
            flash("Record needs to be saved with name to create relationship.", "rel-persons-error")
            return {"ok": False}

        element_attrs = {
            "type": reverse_type,
            "key": person_a_key,
        }

        if person_a_from and person_a_to:
            element_attrs.update({
                "from": person_a_from,
                "to": person_a_to
        })

        el = build_section(
            parent=person_b,
            item_tag="trait",
            attrs=element_attrs,
            child_tag="label",
            child_text=person_a_text,
        )

        child_order = config["child_order"]

        insert_in_order(person_b, "trait", el, child_order, NSMAP)

        write_entity_to_file(context)
        update_index_entry("person", context["xml_id"])

        return {"ok": True}


def related_delete(entity_a_key, entity, form_data, config):

    key = form_data.get("key")
    type = form_data.get("name_type")

    context = load_or_create_entity(
        
        entity_name=entity,
        entity_dir=config["dir"],
        template_path=config["template"],
        xml_id=key,
        nsmap=NSMAP
    )

    if context:
        entity = context["entity_elem"]

    reverse_type = RELATIONSHIP_INVERSES.get(type)


    if not context:
        flash("Related record could not be loaded.", "rel-persons-error")
        return {"ok": False}

    removed = False

    for trait in entity.findall(".//tei:trait", namespaces=NSMAP):
        if trait.get("type") == reverse_type and trait.get("key") == entity_a_key:
            entity.remove(trait)
            removed = True

    if removed:
        write_entity_to_file(context)

        path = get_index_file("person_connections")
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as f:
            index_data = json.load(f)

        for i, item in enumerate(index_data.get(key, [])):
            if item[0] == entity_a_key:
                del index_data[key][i]
                break

        for i, item in enumerate(index_data.get(entity_a_key, [])):
            if item[0] == key:
                del index_data[entity_a_key][i]
                break

        with open(path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    return {"ok": removed}


def remove_connection_index(entity, key, xml_id, target_type):
    """
    Remove a connection entry from the index for a given key + xml_id.

    Args:
        entity (str): e.g. "place"
        key (str): entity key
        xml_id (str): current record id
        target_type (str): e.g. "work"
    """

    entity_ind_name = f"{entity}_connections"
    path = get_index_file(entity_ind_name)

    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        index_data = json.load(f)

    if key not in index_data:
        return

def remove_connection_index(entity, key, xml_id, target_type):
    entity_ind_name = f"{entity}_connections"
    path = get_index_file(entity_ind_name)

    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        index_data = json.load(f)

    if key not in index_data:
        return

    # Remove only ONE matching entry
    for i, item in enumerate(index_data[key]):
        if item[0] == xml_id and item[1] == target_type:
            del index_data[key][i]
            break

    # Clean up if empty
    if not index_data[key]:
        del index_data[key]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

def remove_all_connections_from_index(entity, xml_id):
    """
    Remove all entries in a specific entity connection index that reference the given xml_id.

    Args:
        entity (str): Entity type, e.g., "place", "person", "work".
        xml_id (str): The ID of the entity being deleted.
    """

    index_name = f"{entity}_connections"
    path = get_index_file(index_name)

    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        index_data = json.load(f)


    changed = False
    for key, entries in list(index_data.items()):
        # Keep only entries not matching xml_id
        new_entries = [entry for entry in entries if entry[0] != xml_id]
        if len(new_entries) != len(entries):
            changed = True
            if new_entries:
                index_data[key] = new_entries
            else:
                del index_data[key]

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)


