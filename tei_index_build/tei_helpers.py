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

    records = []

    for entity_type, items in all_entities.items():

        for item in items:

            xml_id = item.get("xml_id")
            if not xml_id:
                continue 

            name_list = item.get("name")
            name = name_list[0] if name_list else xml_id

            alt_names = item.get("alt_names") or []

            record = {
                "type": entity_type,
                "id": xml_id,
                "name": name,
                "alt_names": alt_names,
                "url": f"indexes/{entity_type}_index.html#{xml_id}"
            }

            if entity_type == "person":
                assoc_places = item.get("affiliations")
                places = [f"{assoc.get('placeName')} [{assoc.get('key')}]" for assoc in assoc_places if assoc.get("placeName")]
                record["places"] = places

            if entity_type == "work":
                assoc_places = item.get("pub_place")
                places = [f"{assoc.get('placeName')} [{assoc.get('key')}]" for assoc in assoc_places if assoc.get("placeName")]
                record["places"] = places


            records.append(record)


    output_path = os.path.join(build_dir, "search_index.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_dir_data(entity_tag, directory):

    all_data = []

    for filename in sorted(os.listdir(directory)):

        if not filename.endswith(".xml") or filename.startswith("."):
            continue

        file_path = os.path.join(directory, filename)

        data = load_entity(file_path, entity_tag)

        all_data.append(data)

    return all_data


def normalize_for_sort(text):
    if not text:
        return ""
    return unidecode(text).lower()
    

def group_items_alphabetically(items):
    grouped = defaultdict(list)

    for item in items:
        name_list = item.get("name")

        if name_list:
            name = name_list[0]
            normalized = normalize_for_sort(name)
            first_letter = normalized[0].upper() if normalized else "#"
        else:
            first_letter = "#"

        grouped[first_letter].append(item)

    for letter in grouped:
        grouped[letter].sort(
            key=lambda x: normalize_for_sort(x["name"][0]) if x.get("name") else ""
        )

    return dict(sorted(grouped.items()))


def create_entity_cache(entity_data):
    """Returns a cache of id and name (if present) for link validation."""
    entity_cache = {}

    for item in entity_data:
        xml_id = item.get("xml_id")
        name_list = item.get("name")

        entity_cache[xml_id] = (
            name_list[0] if name_list else xml_id
        )

    return entity_cache


def remove_broken_links(html_path, entities_cache):
    """
    Disable links whose ID is missing from cache or whose text
    does not match the cached preferred name.
    """
    
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    modified = False

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        text = tag.get_text(strip=True)

        if "#" not in href:
            continue

        file_part, id_part = href.split("#", 1)
        if not file_part:
            file_part = os.path.basename(html_path)

        if id_part not in entities_cache or not text.startswith(entities_cache[id_part]):
            #remove <a> but keep inner text
            tag.attrs.pop("href", None)
            tag.attrs.pop("target", None)
            if "[entity no longer indexed at location]" not in tag.text:
                tag.append(" [entity no longer indexed at location]")
            
            modified = True

    #save the file only if changes were made
    if modified:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"Removed broken links in {html_path}")


def link_persons_to_places(entity_data):
    """
    Build a dictionary mapping place XML IDs to lists of affiliated persons.
    """
    place_dict = {}

    for person in entity_data:
        xml_id = person.get("xml_id")
        name_list = person.get("name")
        name = name_list[0] if name_list else person.get("xml_id")
        affiliations = person.get("affiliations") or []

        for affil in affiliations:
            place_key = affil.get("key")
            if not place_key:
                continue

            # initialize list if key not already present
            if place_key not in place_dict:
                place_dict[place_key] = []

            # append person info
            place_dict[place_key].append({
                "xml_id": xml_id,
                "name": name,
                "from": affil.get("from"),
                "to": affil.get("to"),
                "role": affil.get("role")
            })

    return place_dict


def link_works_to_persons(work_data):
    """
    Build a mapping of person XML IDs to works they are associated with.
    """
    person_dict = {}

    for work in work_data:
        work_id = work.get("xml_id")
        work_name = work.get("name")[0] if work.get("name") else work_id

        # Associated persons in the work
        editors = work.get("editor_text") or []
        editor_keys = work.get("editor_key") or []
        editor_roles = work.get("editor_role") or []

        for name, key, role in zip(editors, editor_keys, editor_roles):
            if not key:
                continue

            if key not in person_dict:
                person_dict[key] = []

            person_dict[key].append({
                "xml_id": work_id,
                "title": work_name,
                "role": role
            })

    return person_dict


def load_entity(file_path, entity_tag):
    """
    Load a TEI entity from an XML file according to a specified mapping.

    Args:
        file_path (str): Path to the TEI XML file.
        entity_tag (str): The TEI element tag of the entity to load (e.g., 'person', 'place').
    
    Mapping:
            A dictionary defining how to extract data from the entity.
            Each key maps to a specification dict with one of:
                - "attr": extract the entity's attribute value.
                - "element": extract text content from a child element.
                - "element_attr": extract an attribute from a child element.
                - "parent_tag": extract data from nested child elements under a specific parent.
            Additional options in the spec:
                - "filter_attr" / "filter_value": filter elements by attribute/value.
                - "all_results": whether to return all matches as a list.
                - "attributes", "child_elements", "child_attributes": passed to extract_from_parent.

    Returns:
        dict or None: A dictionary of extracted data according to the mapping.
            Keys correspond to mapping keys. Values are:
                - str for single attribute/text values
                - list[str] for multiple matches if "all_results" is True
                - list[dict] for parent_tag extractions (nested elements/attributes)
            Returns None if the entity_tag element is not found in the XML.
    """

    config = ENTITY_CONFIG[entity_tag]
    container_tag = config["container_tag"]
    element_tag = config["element_tag"]
    mapping = config["mapping"]

    tree = etree.parse(file_path)
    root = tree.getroot()
    entity = tree.find(f".//tei:{element_tag}", namespaces=NSMAP)
    if entity is None:
        return None

    data = {}
    for key, spec in mapping.items():

        search_base = root if spec.get("from_root") else entity

        if spec.get("all_results") or "parent_tag" in spec:
            data[key] = []
        else:
            data[key] = None

        if "attr" in spec:
            data[key] = search_base.get(spec["attr"])
        elif "element" in spec:
            if "element_attr" in spec:
                data[key] = extract_attribute_values(
                    search_base,
                    NSMAP,
                    element=spec["element"],
                    filter_attr=spec["element_attr"],
                    all_results=spec.get("all_results", False)
                )
            else:
                data[key] = extract_element_text(
                    search_base,
                    NSMAP,
                    element=spec["element"],
                    filter_attr=spec.get("filter_attr"),
                    filter_value=spec.get("filter_value"),
                    all_results=spec.get("all_results", False)
                )
        elif "parent_tag" in spec:
            data[key] = extract_from_parent(
                search_base,
                NSMAP,
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
    Extract text content from matching TEI elements under a given parent element.

    Optionally filters by attribute presence/value.

    Args:
        parent (lxml.etree._Element): The parent element to search under.
        ns (dict): Namespace mapping for XPath.
        element (str): TEI element name (without namespace prefix).
        filter_attr (str or None): Attribute name to filter on.
        filter_value (str or None): Attribute value to match.
        all_results (bool): Whether to return all matches or only the first.

    Returns:
        str or list[str] or None:
            First matching text, list of texts, or None if no match.
    """
    if parent is None:
        return [] if all_results else None
    
    xpath = f".//tei:{element}"
    if filter_attr:
        if filter_value is not None:
            xpath += f'[@{filter_attr}="{filter_value}"]'
        else:
            xpath += f'[@{filter_attr}]'
    
    results = parent.xpath(xpath, namespaces=ns)
    texts = [el.text.strip() for el in results if el.text and el.text.strip()]

    return texts if all_results else (texts[0] if texts else None)


def extract_attribute_values(parent, ns, element, filter_attr, all_results=False):
    """
    Extract attribute values from matching TEI elements under a given parent element.

    Args:
        parent (lxml.etree._Element): The parent element to search under.
        ns (dict): Namespace mapping for XPath.
        element (str): TEI element name (without namespace prefix).
        filter_attr (str): Attribute name to extract.
        all_results (bool): Whether to return all matches or only the first.

    Returns:
        str or list[str] or None:
            First matching attribute value, list of values, or None if no match.
    """
    if parent is None:
        return [] if all_results else None
    
    xpath = f".//tei:{element}/@{filter_attr}"
    
    results = parent.xpath(xpath, namespaces=ns)
    values = [val.strip() for val in results if val and val.strip()]

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
    Extract information from parent elements and their children, optionally filtering parents by attribute.


    Args:
        parent (lxml.etree._Element): The parent element to search under.
        parent_tag (str): Tag name of the parent element(s) to extract.
        attributes (list[str], optional): List of attributes to extract from the parent element(s).
        child_elements (list[str], optional): List of child/grandchild element tag names to extract text from.
        child_attributes (dict, optional): Dictionary mapping child/grandchild element tag names to lists of
                                           attribute names to extract from those child elements.
        filter_attr (str, optional): Attribute name to filter parent elements by.
        filter_value (str, optional): Attribute value to match for filtering parent elements.
        extract_parent_text (bool, optional): Whether to extract the parent element’s own text.                                   
        namespaces (dict, optional): Namespace mapping for XPath searches (default: NSMAP).

    Returns:
        list[dict]: A list of dictionaries, one per parent element found, containing:
                    - Parent attributes (if requested)
                    - Child/grandchild element text (if requested)
                    - Child/grandchild element attributes (if requested)
                    Keys for child attributes are formatted as "{child_tag}_{attribute_name}".
                    Missing elements or attributes will have value None.
    """

    results = []

    if parent is None:
        return results

    xpath = f".//tei:{parent_tag}"
    if filter_attr:
        if filter_value is not None:
            xpath += f'[@{filter_attr}="{filter_value}"]'
        else:
            xpath += f'[@{filter_attr}]'

    for el in parent.xpath(xpath, namespaces=ns):
        item = {}

        # Extract parent attributes
        if attributes:
            for attr in attributes:
                val = el.get(attr)
                item[attr] = val.strip() if val else None

        if extract_parent_text:
            parent_text = el.text.strip() if el.text and el.text.strip() else None
            item["parent_text"] = parent_text

        # Extract child/grandchild elements text
        if child_elements:
            for child in child_elements:
                child_el = el.find(f".//tei:{child}", namespaces=ns)
                item[child] = child_el.text.strip() if child_el is not None and child_el.text else None

        # Extract child/grandchild element attributes
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

