import os
import json
from bs4 import BeautifulSoup
from lxml import etree
from collections import defaultdict
from unidecode import unidecode

from config import (

    NSMAP,
    ENTITY_CONFIG
)


def build_search_index(all_entities, build_dir):
    """
    Build a JSON search index from the extracted entity data.

    Each entity is converted into a search record containing its type,
    XML ID, preferred name, alternative names, and index URL. Additional
    relationship data is included for persons, works, and inscriptions.

    Args:
        all_entities (dict): Dictionary mapping entity types to lists of
            extracted entity data.
        build_dir (str): Directory where the search index JSON file will
            be written.

    Returns:
        None:
            Writes the search index to 'search_index.json' in build_dir.
    """
    
    #collect the final search records for all entity types
    records = []

    #store residence information for persons so it can later be added
    #to works associated with those persons as authors
    resided_person_places = {}

    #build one search record for each extracted entity.
    for entity_type, items in all_entities.items():

        for item in items:

            xml_id = item.get("xml_id")
            if not xml_id:
                continue 

            #use the first preferred name as the display name. If no
            #preferred name is available, use the XML ID as a fallback
            name_list = item.get("name")
            name = name_list[0] if name_list else xml_id

            alt_names = item.get("alt_names", []) 

            #create the fields common to every search record
            record = {
                "type": entity_type,
                "id": xml_id,
                "name": name,
                "alt_names": alt_names,
                "url": f"indexes/{entity_type}_index.html#{xml_id}"
            }

            #entity-specific data

            #add affiliated places for persons and separately record
            #places where the person is identified as having resided
            if entity_type == "person":
                assoc_places = item.get("affiliations", [])
                places = []
                resided_places = []
                
                #process each person-place affiliation
                for assoc in assoc_places:
                    if assoc.get("placeName"):
                        #store the place name together with its XML ID
                        place = f"{assoc.get('placeName')} [{assoc.get('key')}]"
                        places.append(place)
                        
                        #keep residence affiliations for later work linking
                        if assoc.get("role") == "Resided":
                            resided_places.append(place)
                
                #store residence information under the same person reference
                #format that is used when persons are linked to works
                if resided_places:
                    resided_person_places[f"{name} [{xml_id}]"] = resided_places
                
                #add all affiliated places to the person search record
                record["places"] = places

            #add publication places and associated persons for works
            if entity_type == "work":
                assoc_places = item.get("pub_place")
                
                #combine each publication place name with its XML ID
                places = [f"{assoc.get('placeName')} [{assoc.get('key')}]" for assoc in assoc_places if assoc.get("placeName")]
                
                #retrieve the parallel lists containing person names,
                #XML IDs, and roles
                person_names =  item.get("editor_text")
                person_keys = item.get("editor_key")
                person_roles = item.get("editor_role")
                
                #combine each person's name with their XML ID
                persons = [f"{name} [{key}]" for name, key in zip(person_names, person_keys)]
                
                #add the work's places and associated persons to the record
                record["places"] = places
                record["persons"] = persons
                record["person_roles"] = person_roles

            #add places associated with inscriptions
            if entity_type == "inscription":
                assoc_places = item.get("location", [])
                assoc_place_keys = item.get("location_key", [])
                
                #pair each location with its corresponding place XML ID
                places = [f"{place} [{key}]" for place, key in zip(assoc_places, assoc_place_keys)]
                
                record["places"] = places

            records.append(record)

    #add residence places to works based on their associated authors
    #this second pass is needed because all person residence data must
    #be collected before it can be used by the work records   
    for record in records:
        if record["type"] == "work":
            
            #use a set to avoid duplicate residence places
            resided_places = set()
            
            #retrieve the persons and their corresponding roles from the
            #temporary fields added when the work was first processed
            persons = record.get("persons", [])
            person_roles = record.get("person_roles", [])
            
            #if a person related to work is an author, add their resided places
            #to the work as associated with work
            for person, role in zip(persons, person_roles):
                if role == "aut":
                    resided_places.update(resided_person_places.get(person, []))
            record["resided_places"] = sorted(resided_places)
            
            #remove the temporary role information now that it is no longer
            #needed in the final search record
            del record["person_roles"]

    output_path = os.path.join(build_dir, "search_index.json")

    #write all records to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_dir_data(entity_tag, directory):
    """
    Load extracted data for all XML files in an entity directory.

    Args:
        entity_tag (str): Configuration key identifying the entity type.
        directory (str): Directory containing the entity XML files.

    Returns:
        list:
            List of extracted entity data dictionaries, one for each
            XML file in the directory.
    """

    #collect the extracted data for all XML files in the directory
    all_data = []

    #retrieve the extraction configuration for this entity type
    tag_config = ENTITY_CONFIG[entity_tag] 

    for filename in sorted(os.listdir(directory)):

        if not filename.endswith(".xml") or filename.startswith("."):
            continue

        file_path = os.path.join(directory, filename)

        #extract the entity data according to the configured mapping
        data = load_entity(file_path, entity_tag, tag_config, NSMAP)

        #add the extracted entity data to the collection
        all_data.append(data)

    return all_data


def normalize_for_sort(text):
    """
    Normalize text for alphabetical sorting.

    Args:
        text (str): Text to normalize.

    Returns:
        str:
            Lowercase ASCII transliteration of the input text, or an
            empty string if no text is provided.
    """
    if not text:
        return ""
    return unidecode(text).lower()
    

def group_items_alphabetically(items):
    """
    Group entity items alphabetically by their preferred name.

    Names are normalized before determining the grouping letter and sorting
    items, allowing names with diacritics to be grouped consistently.

    Args:
        items (list): List of extracted entity data dictionaries.

    Returns:
        dict:
            Dictionary mapping alphabetical grouping letters to sorted
            lists of entity items. Items without a name are grouped under
            "#".
    """
    
    #create a dictionary where each grouping letter maps to a list of items
    grouped = defaultdict(list)

    #determine the grouping letter for each item from its preferred name
    for item in items:
        name_list = item.get("name")

        if name_list:
            name = name_list[0]
            normalized = normalize_for_sort(name)

            #use "#" for names that cannot produce a grouping letter
            first_letter = normalized[0].upper() if normalized else "#"
        else:
            #items without a preferred name are grouped under "#"
            first_letter = "#"

        grouped[first_letter].append(item)

    #sort items within each alphabetical group using normalized names
    for letter in grouped:
        grouped[letter].sort(
            key=lambda x: normalize_for_sort(x["name"][0]) if x.get("name") else ""
        )

    #sort the grouping letters themselves before returning the dictionary
    return dict(sorted(grouped.items()))


def create_entity_cache(entity_data):
    """
    Create a cache mapping entity XML IDs to their preferred names.

    The cache is used when validating links to ensure that referenced
    entities exist and that the linked text matches the preferred name.

    Args:
        entity_data (list): List of extracted entity data dictionaries.

    Returns:
        dict:
            Dictionary mapping each entity XML ID to its preferred name.
            If no preferred name is available, the XML ID is used instead.
    """
    
    #store the entity ID and corresponding preferred name
    entity_cache = {}

    #process each extracted entity
    for item in entity_data:
        xml_id = item.get("xml_id")
        name_list = item.get("name")

        #use the first preferred name when available; otherwise use the XML ID
        entity_cache[xml_id] = name_list[0] if name_list else xml_id

    return entity_cache


def remove_broken_links(html_path, entities_cache, exclude_classes=None):
    """
    Remove invalid internal entity links from a generated HTML file.

    Links are disabled when the referenced XML ID is missing from the
    entity cache or when the link text no longer matches the cached
    preferred name. Selected CSS classes can be excluded from validation.
    
    Args:
        html_path (str): Path to the generated HTML file.
        entities_cache (dict): Dictionary mapping XML IDs to preferred names.
        exclude_classes (list[str], optional): CSS classes whose links should
            be ignored during validation.

    Returns:
        None:
            Updates the HTML file in place if broken links are found.
    """
    
    #default to no excluded CSS classes    
    if exclude_classes is None:
        exclude_classes = []

    #parse the generated HTML file    
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    modified = False

    #check each internal link in the document
    for tag in soup.find_all("a", href=True):

        #skip links that should not be validated
        if any(item in tag.get("class", []) for item in exclude_classes):
            continue

        href = tag["href"]
        text = tag.get_text(strip=True)

        #ignore links that do not point to an internal page anchor
        if "#" not in href:
            continue

        file_part, id_part = href.split("#", 1)

        #skip map links
        if file_part == "/map.html":
            continue

        #treat anchor-only links as links within the current page
        if not file_part:
            file_part = os.path.basename(html_path)

        #disable links whose target entity is missing or whose displayed
        #text no longer matches the cached preferred name
        if id_part not in entities_cache or not text.startswith(entities_cache[id_part]):
            
            #remove the link but preserve the displayed text
            tag.attrs.pop("href", None)
            tag.attrs.pop("target", None)
            
            #mark the broken link in the rendered HTML
            if "[entity no longer indexed at location]" not in tag.text:
                tag.append(" [entity no longer indexed at location]")
            
            modified = True

    #rewrite the file only if broken links were removed
    if modified:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"Removed broken links in {html_path}")


def link_persons_to_places(entity_data):
    """
    Build a mapping of places to their associated persons.

    Each place XML ID is mapped to a list of people affiliated with that
    place, together with the affiliation dates and relationship role.

    Args:
        entity_data (list): List of extracted person entity dictionaries.

    Returns:
        dict:
            Dictionary mapping place XML IDs to lists of affiliated person
            records.
    """

    #store affiliated persons under each place XML ID
    place_dict = {}

    #process each person in the extracted data
    for person in entity_data:
        xml_id = person.get("xml_id")
        name_list = person.get("name")
        #use the first preferred name when available; otherwise use the XML ID
        name = name_list[0] if name_list else person.get("xml_id")
        affiliations = person.get("affiliations", [])

        #process each place affiliation for the current person
        for affil in affiliations:
            place_key = affil.get("key")
            if not place_key:
                continue

            #create a list for the place in place dict if not seen before
            if place_key not in place_dict:
                place_dict[place_key] = []

            #store the person's affiliation information under the place
            place_dict[place_key].append({
                "xml_id": xml_id,
                "name": name,
                "from": affil.get("from"),
                "to": affil.get("to"),
                "role": affil.get("role")
            })

    return place_dict


def link_inscriptions_to_places(entity_data):
    """
    Build a mapping of places to their associated inscriptions.

    Each place XML ID is mapped to a list of inscriptions associated with
    that place.

    Args:
        entity_data (list): List of extracted inscription entity dictionaries.

    Returns:
        dict:
            Dictionary mapping place XML IDs to lists of associated
            inscription records.
    """

    #store associated inscriptions under each place XML ID
    place_dict = {}

    #process each inscription in the extracted data
    for inscription in entity_data:
        xml_id = inscription.get("xml_id")
        inscription_list = inscription.get("name")
        
        #use the first preferred name when available; otherwise use the XML ID
        name = inscription_list[0] if inscription_list else inscription.get("xml_id")
        
        places = inscription.get("location", [])
        place_keys = inscription.get("location_key", [])

        #process each place associated with the current inscription
        for place, place_key in zip(places, place_keys):

            if not place_key:
                continue

            #create a list for the place in place_dict if not seen before
            if place_key not in place_dict:
                place_dict[place_key] = []

            #store the inscription information under the place
            place_dict[place_key].append({
                "xml_id": xml_id,
                "name": name,
            })

    return place_dict


def link_works_to_persons(work_data):
    """
    Build a mapping of persons to works they are associated with.

    Each person XML ID is mapped to a list of associated works, together
    with the work title and the person's role in the work.

    Args:
        work_data (list): List of extracted work entity dictionaries.

    Returns:
        dict:
            Dictionary mapping person XML IDs to lists of associated
            work records.
    """

    #store associated works under each person XML ID
    person_dict = {}

    #process each work in the extracted data
    for work in work_data:
        work_id = work.get("xml_id")
        #use the first preferred name when available; otherwise use the XML ID
        work_name = work.get("name")[0] if work.get("name") else work_id

        #retrieve the parallel lists containing person names, XML IDs, and roles
        editors = work.get("editor_text", []) 
        editor_keys = work.get("editor_key", []) 
        editor_roles = work.get("editor_role", [])

        #process each person associated with the current work
        for name, key, role in zip(editors, editor_keys, editor_roles):
            if not key:
                continue

            #create a list for the person in person_dict if not seen before
            if key not in person_dict:
                person_dict[key] = []

            #store the work information under the person's XML ID
            person_dict[key].append({
                "xml_id": work_id,
                "title": work_name,
                "role": role
            })

    return person_dict


def load_entity(file_path, entity_tag, config, nsmap):
    """
    Load structured data for a TEI entity from an XML file using a mapping specification.

    This function extracts data from a target TEI element (e.g. person, place, msDesc)
    according to a declarative mapping. Each mapping entry defines how a value should
    be retrieved (attribute, element text, or nested parent structure).

    Args:
        file_path (str): Path to the TEI XML file.
        entity_tag (str): Configuration key ("place", "work", etc)
        config (dict): Configuration dictionary for the entity type.
        nsmap (dict): Namespace mapping used for XPath queries.

    Mapping (dict):
        Extraction specification. Each key maps to a dict defining
            how to retrieve the value. Exactly one of the following must be provided:
            
            - "attr": Extract an attribute from the current element.
            - "element": Extract text content from a descendant element.
                - "element_attr" (optional): If provided, extract this attribute
                  instead of element text.
            - "parent_tag": Extract structured data from descendant elements
              using extract_from_parent().
            
            Optional keys:
            - "from_root" (bool): If True, search from the document root instead
              of the entity element.
            - "filter_attr" / "filter_value": Filter elements by attribute/value.
            - "all_results" (bool): Return all matches as a list instead of a single value.
            - "attributes", "child_elements", "child_attributes",
              "extract_parent_text": Passed to extract_from_parent().

    Returns:
        dict or None:
            Dictionary of extracted values keyed by mapping keys. Values may be:
            - str: single extracted value
            - list[str]: multiple values when "all_results" is True
            - list[dict]: structured results from "parent_tag"

            Returns None if the target entity element is not found.
    """

    #load extraction mapping for this entity type
    #this defines how each field should be retrieved from the XML
    mapping = config["mapping"]

    #determine the TEI element for this entity
    element_tag = config["element_tag"]

    tree = etree.parse(file_path)
    root = tree.getroot()
    
    #locate the first matching entity element in the document
    entity = tree.find(f".//tei:{element_tag}", namespaces=nsmap)
    if entity is None:
        return None

    data = {}

    #iterate over mapping definitions to extract fields
    for key, spec in mapping.items():

        #decide whether to search from root or from the entity element
        search_base = root if spec.get("from_root") else entity

        #initialise output structure based on expected result type
        #lists for multi-value or structured results, otherwise single value
        if spec.get("all_results") or "parent_tag" in spec:
            data[key] = []
        else:
            data[key] = None

        #attribute extraction from the current search base
        if "attr" in spec:
            data[key] = search_base.get(spec["attr"])
        
        #element-based extraction
        elif "element" in spec:
            
            #extract attribute(s) from matching elements
            if "element_attr" in spec:
                data[key] = extract_attribute_values(
                    search_base,
                    nsmap,
                    element=spec["element"],
                    filter_attr=spec["element_attr"],
                    all_results=spec.get("all_results", False)
                )
            
            #extract text content from matching elements
            else:
                data[key] = extract_element_text(
                    search_base,
                    nsmap,
                    element=spec["element"],
                    filter_attr=spec.get("filter_attr"),
                    filter_value=spec.get("filter_value"),
                    all_results=spec.get("all_results", False)
                )
        
        #structured extraction from nested parent elements
        elif "parent_tag" in spec:
            data[key] = extract_from_parent(
                search_base,
                nsmap,
                parent_tag=spec["parent_tag"],
                attributes=spec.get("attributes"),
                filter_attr=spec.get("filter_attr"),
                filter_value=spec.get("filter_value"),
                child_elements=spec.get("child_elements"),
                child_attributes=spec.get("child_attributes"),
                extract_parent_text=spec.get("extract_parent_text")
            )
    
    return data


def extract_element_text(parent, ns, element, filter_attr=None, filter_value=None, all_results=False):
    """
    Extract text content from TEI elements under a given parent, with optional attribute filtering.

    Args:
        parent (lxml.etree._Element): Parent element to search within.
        ns (dict): Namespace mapping for XPath.
        element (str): TEI element name (without namespace prefix).
        filter_attr (str or None): Attribute name to filter on.
        filter_value (str, optional): If provided, only elements with this attribute value are matched.
        If omitted, any element containing the attribute is matched.
        all_results (bool): If True, return all matches; otherwise return only the first.

    Returns:
        str or list[str] or None:
            - First matching text (default)
            - List of texts if all_results=True
            - None if no match (or empty list if all_results=True)
    """
    if parent is None:
        return [] if all_results else None
    
    #build XPath for target TEI element, optionally filtering by attribute
    xpath = f".//tei:{element}"
    #specific attribute and value if provided
    #otherwise match any element with the attribute present
    if filter_attr:
        if filter_value is not None:
            xpath += f'[@{filter_attr}="{filter_value}"]'
        else:
            xpath += f'[@{filter_attr}]'
    
    results = parent.xpath(xpath, namespaces=ns)
    texts = [el.text.strip() for el in results if el.text and el.text.strip()]

    #return all values or just the first match
    return texts if all_results else (texts[0] if texts else None)


def extract_attribute_values(parent, ns, element, filter_attr, all_results=False):
    """
    Extract attribute values from matching TEI elements under a given parent element.

    Args:
        parent (lxml.etree._Element): Parent element to search within.
        ns (dict): Namespace mapping for XPath.
        element (str): TEI element name (without namespace prefix).
        filter_attr (str): Attribute name to extract values from.
        all_results (bool): If True, return all matches; otherwise return only the first.

    Returns:
        str or list[str] or None:
            - First matching value (default)
            - List of values if all_results=True
            - None if no match (or empty list if all_results=True)
    """
    if parent is None:
        return [] if all_results else None
    
    #XPath directly selects attribute values from matching elements
    xpath = f".//tei:{element}/@{filter_attr}"
    
    results = parent.xpath(xpath, namespaces=ns)
    values = [val.strip() for val in results if val and val.strip()]

    #return all values or just the first match
    return values if all_results else (values[0] if values else None)


def extract_from_parent(
    parent,
    ns,
    parent_tag,
    *,
    attributes=None,
    child_elements=None,
    child_attributes=None,
    filter_attr=None,
    filter_value=None,
    extract_parent_text=False,
):
    """
    Extract structured data from specified parent TEI elements and their children.

    Optionally filters parent elements by attribute and extracts:
        - Parent attributes
        - Parent text
        - Child element text
        - Child element attributes

    Args:
        parent (lxml.etree._Element): Parent element to search within.
        ns (dict): Namespace mapping for XPath.
        parent_tag (str): Tag name of the parent element(s) to extract.
        attributes (list[str], optional): Attribute names to extract from each parent.
        child_elements (list[str], optional): Child element tags to extract text from.
        child_attributes (dict, optional): Dictionary mapping child/grandchild element tag names to lists of
                                           attribute names to extract from those child elements.
        filter_attr (str, optional): Attribute name to filter parent elements.
        filter_value (str, optional): If provided, only parents with this value are matched.
        If omitted, any parent with the attribute is matched.
        extract_parent_text (bool, optional): Whether to extract the parent element’s text.                                  

    Returns:
        list[dict]:
            One dictionary per parent element, containing requested fields.
            Missing values are set to None.
            Child attribute keys are formatted as "{child}_{attribute}".
    """

    results = []

    if parent is None:
        return results

    #build XPath for parent elements, optionally applying attribute filter
    xpath = f".//tei:{parent_tag}"
    if filter_attr:
        if filter_value is not None:
            xpath += f'[@{filter_attr}="{filter_value}"]'
        else:
            xpath += f'[@{filter_attr}]'

    #iterate over all matching parent elements
    for el in parent.xpath(xpath, namespaces=ns):
        item = {}

        #extract requested attributes from the parent element
        if attributes:
            for attr in attributes:
                val = el.get(attr)
                item[attr] = val.strip() if val else None

        #optionally extract the parent element’s own text content
        if extract_parent_text:
            parent_text = el.text.strip() if el.text and el.text.strip() else None
            item["parent_text"] = parent_text

        #extract text from the first matching descendant element (child, grandchild, etc.)
        #uses .find(), so only the first match is returned
        if child_elements:
            for child in child_elements:
                child_el = el.find(f".//tei:{child}", namespaces=ns)
                item[child] = child_el.text.strip() if child_el is not None and child_el.text else None

        #extract attributes from the first matching descendant element
        #if no matching element is found, populate keys with None
        if child_attributes:
            for child_name, attr_list in child_attributes.items():
                child_el = el.find(f".//tei:{child_name}", namespaces=ns)
                if child_el is not None:
                    for attr in attr_list:
                        val = child_el.get(attr)
                        item[f"{child_name}_{attr}"] = val.strip() if val else None
                else:
                    for attr in attr_list:
                        item[f"{child_name}_{attr}"] = None

        results.append(item)

    return results

