import os
import hjson
from lxml import etree
from flask import request, redirect, url_for, flash

from utils import load_ent_name_by_key, load_or_create_entity, write_entity_to_file, build_section, insert_in_order

from config import ENTITY_CONFIG, NSMAP, NS_TEI, NS_XML, BASE_DIR, DATA_DIR, INDEX_DIR, RELATIONSHIP_INVERSES, TEXT_ELEMS


os.makedirs(INDEX_DIR, exist_ok=True)


def get_index_file(entity):
    """Return path to the HJSON index file for a given entity."""
    return os.path.join(INDEX_DIR, f"{entity}.hjson")


def write_hjson(data, path):
    """
    Write data to an HJSON file.

    Args:
        data: Python object to serialise.
        path (str): Destination file path.

    Returns:
        None
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(hjson.dumps(data, indent=2))


def read_hjson(path):
    """Load HJSON file"""
    with open(path, encoding="utf-8") as f:
        return hjson.load(f)


def load_index(entity):
    """Load HJSON index for entity type; rebuild if missing."""
    path = get_index_file(entity)
    if not os.path.exists(path):
        rebuild_entity_index(entity)
    return read_hjson(path)


def rebuild_entity_index(entity):
    """
    Rebuild an entity index by scanning XML files.

    Reads all XML files for an entity type, extracts their IDs and
    display names, sorts the entries, and writes the rebuilt index
    to HJSON.

    Args:
        entity (str): Entity type to rebuild the index for.

    Returns:
        None
    """
    
    #load configuration details for this entity type
    config = ENTITY_CONFIG[entity]
    entity_dir = config["dir"]
    name_tag = config.get("name_tag")

    data = []

    #scan the entity directory and collect index entries from XML files
    for filename in sorted(os.listdir(entity_dir)):
        if not filename.endswith(".xml"):
            continue

        xml_id = filename[:-4]

        #extract the display name from the XML record
        #fall back to the ID if no name can be found
        name = load_ent_name_by_key(
            entity, config, xml_id, name_tag, NSMAP
        ) or xml_id

        data.append({
            "xml_id": xml_id,
            "name": name
        })

    #keep index entries alphabetically ordered for predictable lookup/display
    data.sort(key=lambda x: x["name"].lower())
    
    #replace the existing index with the rebuilt version
    write_hjson(data, get_index_file(entity))


def update_index_entry(entity, xml_id):
    """
    Update or add a single entity entry in the HJSON index.

    Removes any existing entry with the same XML ID, then adds
    the current entity name and rewrites the index.

    Args:
        entity (str): Entity type being indexed (e.g. "person", "place", "work").
            Used to select the correct configuration and index file.
        xml_id (str): Unique XML identifier of the entity being updated.

    Returns:
        None
    """

    #load configuration details for this entity type
    config = ENTITY_CONFIG[entity]
    name_tag = config.get("name_tag")
    index_path = get_index_file(entity)
    
    data = []

    #load the current index if it exists
    #if no index exists yet, start with an empty list
    if os.path.exists(index_path):
        index_data = read_hjson(index_path)

        #remove any existing entry for this XML ID
        new_index_data = [entry for entry in index_data if entry["xml_id"] != xml_id]

    else:
        new_index_data = []

    #extract the display name from the XML record
    #fall back to the ID if no name can be found
    name = load_ent_name_by_key(
        entity, config, xml_id, name_tag, NSMAP
        ) or xml_id

    #append updated entry
    new_index_data.append({"xml_id": xml_id, "name": name})

    #keep index entries alphabetically ordered for predictable lookup/display
    new_index_data.sort(key=lambda x: x["name"].lower())

    #save the updated index back to disk.
    write_hjson(new_index_data, index_path)


def delete_index_entry(entity, xml_id):
    """
    Remove a single entity entry from the HJSON index.

    If the index file does not exist, or no matching XML ID is found,
    the function exits without making changes.

    Args:
        entity (str): Entity type being indexed (e.g. "person", "place", "work").
            Used to determine which index file should be updated.
        xml_id (str): Unique XML identifier of the entity entry to remove.

    Returns:
        None: Updates the index file directly if an entry is removed.
    """

    index_path = get_index_file(entity)
    
    #no index file means there is nothing to delete
    if not os.path.exists(index_path):
        return

    #load existing index entries
    index_data = read_hjson(index_path)

    #create a new index excluding the requested XML ID.
    new_index_data = [entry for entry in index_data if entry["xml_id"] != xml_id]

    #if the length has not changed, no matching entry was found.
    if len(new_index_data) == len(index_data):
        return

    #save the updated index without the removed entry.
    write_hjson(new_index_data, index_path)


def update_connection_index(entity, linked_id, xml_id, entity_type, entity_text):
    """
    Add a connection entry to an entity relationship index.

    Connection indexes store which records reference a particular entity.
    If the index file does not exist, a new one is created.

    Args:
        entity (str): Entity type whose connection index is being updated
            (e.g. "person", "place", "work"). Determines the index file.
        linked_id (str): XML ID of the entity being linked to.
            Used as the key in the connection index.
        xml_id (str): XML ID of the entity making the reference.
        entity_type (str): Type of the referencing entity.
            Used to identify where the connection originates.
        entity_text (str): Display text/name of the linked entity
            at the time the connection is created.

    Returns:
        None
    """

    #connection indexes are stored separately from normal entity indexes.
    entity_ind_name = f"{entity}_connections"

    index_path = get_index_file(entity_ind_name)

    #load existing connections or start a new index.
    index_data = {}
    if os.path.exists(index_path):
        index_data = read_hjson(index_path)

    #add this connection under the linked entity's ID.
    #multiple entities can reference the same target, so store a list.
    index_data.setdefault(linked_id, []).append([xml_id, entity_type, entity_text])

    #save the updated connection index.
    write_hjson(index_data, index_path)


def update_connection_files(entity, key):
    """
    Update all files that reference an entity after its name changes.

    Uses the connection index to find records linked to the entity,
    updates any matching text references in their XML files, and refreshes
    the stored connection names.

    Args:
        entity (str): Entity type being updated (e.g. "person", "place", "work").
            Determines which connection index should be checked.
        key (str): XML ID of the entity whose references should be updated.

    Returns:
        None: Updates linked XML files and the connection index directly.
    """

    #connection indexes are stored separately from normal entity indexes
    connections_name = f"{entity}_connections"
    
    index_path = get_index_file(entity)
    connections_path = get_index_file(connections_name)

    #if either index is missing, there is nothing to update
    if not os.path.exists(index_path) or not os.path.exists(connections_path):
        return

    #load the entity index to find the current display name
    index_data = read_hjson(index_path)

    #load all stored references to this entity
    connections_data = read_hjson(connections_path)

    #find the current entity name from the main index
    index_name = next((item["name"] for item in index_data if item["xml_id"] == key), None)

    if index_name is None:
        return 

    #retrieve all records that reference this entity in connections index
    connections = connections_data.get(key)

    if not connections:
        return

    updated_connections = []

    #process each record that contains a reference to this entity
    for connection in connections:

        linked_id, linked_ent, orig_name = connection

        config = ENTITY_CONFIG[linked_ent]

        #load the XML file containing the reference.
        context = load_or_create_entity(
            entity_name=linked_ent,
            config=config,
            nsmap=NSMAP,
            ns_xml=NS_XML,
            xml_id=linked_id
        )

        #if the linked record no longer exists, preserve the connection
        #rather than losing information from the index.
        if not context:
            updated_connections.append([linked_id, linked_ent, orig_name])
            continue

        #most entities store their XML element in "entity_elem".
        #inscriptions store person references inside listPerson instead.
        if entity == "person" and linked_ent == "inscription":
            entity_elem = context["root"].find(".//tei:listPerson", namespaces=NSMAP)
        else:
            entity_elem = context["entity_elem"]

        changed = False

        #find elements in linked files that reference this entity using the key attribute.
        for elem in entity_elem.xpath(f'.//*[@key="{key}"]'):
            #update direct text content if it matches the old name.
            if elem.text and elem.text.strip() == orig_name:
                elem.text = index_name
                changed = True
            else:
                #some references store the displayed name in a child element
                #(for example persName, placeName etc.)
                #search these nested text elements as well
                for tag in TEXT_ELEMS:
                    candidates = elem.xpath(f".//*[local-name()='{tag}']")
                    
                    for c in candidates:
                        if c.text and c.text.strip() == orig_name:
                            c.text = index_name
                            changed = True

        #only rewrite XML files that actually changed
        if changed:
            write_entity_to_file(context)

        #update the stored connection name to the new value
        updated_connections.append([linked_id, linked_ent, index_name])

    #replace the old connection entries with refreshed names.
    connections_data[key] = updated_connections

    #save the updated connection index.
    write_hjson(connections_data, connections_path)


def delete_connection_entry(xml_id, form_data):
    """
    Remove a single connection from an entity connection index.

    The connection is identified by the XML ID of the referencing entity
    together with the stored display name.

    Args:
        xml_id (str): XML ID of the entity whose connection should be removed.
        form_data (dict): Form submission containing the linked entity key,
            entity type, and display name.

    Returns:
        None
    """

    key = form_data.get("key")
    entity = form_data.get("name_type")
    entity_name = form_data.get("name")

    #determine the appropriate connection index
    entity_ind_name = f"{entity}_connections"
    path = get_index_file(entity_ind_name)

    #nothing to do if the connection index does not exist.
    if not os.path.exists(path):
        return

    #load the existing connection index.
    index_data = read_hjson(path)

    #find and remove the matching connection entry
    if key in index_data and isinstance(index_data[key], list):
        for i, item in enumerate(index_data[key]):
            if item[0] == xml_id and item[2] == entity_name:
                del index_data[key][i]
                break

    #save the updated connection index.
    write_hjson(index_data, path)


def related_add(relationship, key, person_a_key, person_a_text, reverse_type, config, person_a_from=None, person_a_to=None):    

    context = load_or_create_entity(
        entity_name="person",
        config=config,
        nsmap=NSMAP,
        ns_xml=NS_XML,
        xml_id=key,
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
            nsmap=NSMAP,
            ns=NS_TEI,
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
        config=config,
        nsmap=NSMAP,
        ns_xml=NS_XML,
        xml_id=key,
    )

    if context:
        entity = context["entity_elem"]

    reverse_type = RELATIONSHIP_INVERSES.get(type)


    if not context:
        flash("Related record could not be loaded, perhaps deleted in other location.", "rel-persons-error")
        return {"ok": False}

    removed = False

    for trait in entity.findall(".//tei:trait", namespaces=NSMAP):
        if trait.get("type") == reverse_type and trait.get("key") == entity_a_key:
            entity.remove(trait)
            removed = True
            break

    if removed:
        write_entity_to_file(context)

        path = get_index_file("person_connections")
        if not os.path.exists(path):
            return
        index_data = read_hjson(path)

        for i, item in enumerate(index_data.get(key, [])):
            if item[0] == entity_a_key:
                del index_data[key][i]
                break

        for i, item in enumerate(index_data.get(entity_a_key, [])):
            if item[0] == key:
                del index_data[entity_a_key][i]
                break

        write_hjson(index_data, path)

    return {"ok": removed}


def remove_connection_index(entity, key, xml_id, target_type):
    entity_ind_name = f"{entity}_connections"
    path = get_index_file(entity_ind_name)

    if not os.path.exists(path):
        return

    index_data = read_hjson(path)

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

    write_hjson(index_data, path)


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

    index_data = read_hjson(path)

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
        write_hjson(index_data, path)



