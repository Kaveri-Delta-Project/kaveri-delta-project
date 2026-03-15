from lxml import etree
from unidecode import unidecode
import string
import os, re
from config import ENTITY_CONFIG, NS_TEI, NS_XML, NSMAP, DEFAULT_NSMAP
from flask import request, redirect, url_for
from collections import defaultdict



def normalize_for_sort(text):
    """
    Normalize a string for sorting or comparison:
    - Strip diacritics (é → e, Ł → L)
    - Lowercase
    """
    if not text:
        return ""
    return unidecode(text).lower()


def group_items_alphabetically(items):
    """
    Group a list of items alphabetically by the first letter of their name.
    Handles diacritics and sorts items within each group.
    
    Args:
        items (list[dict]): Each item should have at least 'name' and 'xml_id'.
        
    Returns:
        dict[str, list[dict]]: Keys are 'A'-'Z' plus '#' for non-letter starts.
    """
    # Initialize A-Z plus '#' for non-letter starting items
    grouped = {letter: [] for letter in string.ascii_uppercase}
    grouped["#"] = []

    for item in items:
        name = item.get("name") or ""
        normalized = normalize_for_sort(name)

        # Determine first letter for grouping
        if normalized and normalized[0].isalpha():
            first_letter = normalized[0].upper()
        else:
            first_letter = "#"

        grouped[first_letter].append(item)

    # Sort items within each group alphabetically
    for letter, items_in_group in grouped.items():
        items_in_group.sort(key=lambda x: normalize_for_sort(x.get("name") or x["xml_id"]))

    return grouped

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
    if not parent:
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
    if not parent:
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


def load_ent_name_by_key(entity_type, key, elem_name):
    """
    Load an entity XML file by key and return the preferred name text
    for the given element name (e.g. persName, placeName, title).
    """
    config = ENTITY_CONFIG[entity_type]
    path = os.path.join(config["dir"], f"{key}.xml")

    if not os.path.exists(path):
        return None

    tree = etree.parse(path)
    root = tree.getroot()

    name_elem = root.find(
        f".//tei:{elem_name}[@type='preferred']",
        namespaces=NSMAP
    )

    if name_elem is not None and name_elem.text:
        return name_elem.text.strip()

    return None

def valid_date(s):
    """
    Returns True if s is empty or matches:
    - Year only: YYYY (positive AD)
    - ISO date: YYYY-MM-DD
    """
    if not s:
        return True
    return re.match(r"^\d{4}(-\d{2}-\d{2})?$", s) is not None


def valid_identifier(value, id_type):
    """
    Validate an identifier value according to its identifier type.
    """
    if not value:
        return False

    if id_type == "VIAF":
        return re.fullmatch(r"^\d{1,22}$", value) is not None

    if id_type == "Wikidata":
        return re.fullmatch(r"^Q\d+$", value) is not None

    if id_type == "LCNAF":
        return re.fullmatch(r"n[a-z]?\d+", value) is not None

    if id_type == "TGN":
        return re.fullmatch(r"^\d{1,9}$", value) is not None

    return False

def valid_coordinates(coord_text):
    """
    Validate a coordinate string in the format 'lat, lon' using regex.

    Args:
        coord_text (str): The coordinate string, e.g. "52.200660245312285, 0.1525227968873202"

    Returns:
        bool: True if matches the 'lat, lon' decimal format, False otherwise
    """
    if not coord_text:
        return False

    pattern = r"^\s*-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?\s*$"
    return bool(re.match(pattern, coord_text))


def load_entity(file_path, entity_tag, mapping, nsmap):
    """
    Load a TEI entity from an XML file according to a specified mapping.

    Args:
        file_path (str): Path to the TEI XML file.
        entity_tag (str): The TEI element tag of the entity to load (e.g., 'person', 'msDesc', 'place').
        mapping (dict): A dictionary defining how to extract data from the entity.
            Each key maps to a specification dict with one of:
                - "attr": extract the entity's attribute value.
                - "element": extract text content from a child element.
                - "element_attr": extract an attribute from a child element.
                - "parent_tag": extract data from nested child elements under a specific parent.
            Additional options in the spec:
                - "filter_attr" / "filter_value": filter elements by attribute/value.
                - "all_results": whether to return all matches as a list.
                - "attributes", "child_elements", "child_attributes": passed to extract_from_parent.
        nsmap (dict): Namespace mapping for XPath queries.

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

    tree = etree.parse(file_path)
    root = tree.getroot()
    entity = tree.find(f".//tei:{element_tag}", namespaces=nsmap)
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


def insert_in_order(parent, tag, new_elem, child_order, nsmap,
                    sort_attr=None, attr_priority=None):
    """
    Insert a new element into a parent element, then sort all children
    by child_order and optionally by an attribute within the specified tag.

    Args:
        parent (lxml.etree._Element): Parent element.
        new_elem (lxml.etree._Element): Element to insert.
        child_order (list[str]): List of tag names defining order.
        nsmap (dict): Namespace mapping.
        tag (str, optional): Only apply attribute-based sorting for this tag.
        sort_attr (str, optional): Attribute to sort by.
        attr_priority (dict, optional): Mapping of attribute value to priority.
    """
    children = list(parent)
    if new_elem not in children:
        children.append(new_elem)

    sorted_children = []
    for el in children:
        if not isinstance(el.tag, str):
            continue
        tag_name = el.tag.split("}")[-1]
        tag_index = child_order.index(tag_name) if tag_name in child_order else len(child_order)
        attr_index = attr_priority.get(el.get(sort_attr, ""), 99) if tag and tag_name == tag and sort_attr and attr_priority else 0
        sorted_children.append((tag_index, attr_index, el))

    sorted_children.sort(key=lambda x: (x[0], x[1]))

    for el in list(parent):
        parent.remove(el)

    for _, _, el in sorted_children:
        parent.append(el)


def next_entity_file(prefix, directory, extension="xml"):
    """
    Generate the next available filename for an entity based on a numeric sequence.

    Filenames are expected to follow the pattern: <prefix>_<number>.<extension>
    e.g., "p_1.xml", "ms_2.xml", "w_10.xml".

    Args:
        prefix (str): The prefix for the entity type (e.g., "p", "ms", "w").
        directory (str): Path to the directory containing existing files.
        extension (str, optional): File extension (default is "xml").

    Returns:
        str: The next available filename with the given prefix and extension, 
             using the next number in sequence.
    """

    existing_numbers = []

    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)\.{re.escape(extension)}$")

    for f in os.listdir(directory):
        match = pattern.match(f)
        if match:
            try:
                existing_numbers.append(int(match.group(1)))
            except ValueError:
                pass

    next_num = max(existing_numbers, default=0) + 1
    return f"{prefix}_{next_num}.{extension}"


def delete_tei_attribute(
    *,
    tei_root,
    parent,
    file_path,
    tag,
    index,
    nsmap,
    attr_name,
    attr_value=None,
):
    """
    Delete a specified attribute from a TEI element within a parent element and save the XML.

    If the parent element itself matches the target tag, the function searches in the grandparent,
    in order to correctly parse and find the element.

    Args:
        tei_root (lxml.etree._Element): The root element of the TEI tree.
        parent (lxml.etree._Element): The parent element under which to search.
        file_path (str): Path to save the modified XML file.
        tag (str): Tag name of the element(s) whose attribute should be deleted.
        index (int): Index of the target element among all matching elements.
        nsmap (dict): Namespace mapping for XPath searches.
        attr_name (str): Name of the attribute to delete. Required.
        attr_value (str, optional): Only delete attribute if it matches this value.

    Returns:
        bool: True if the attribute was found and deleted; False otherwise.
    """

    parent_tag = etree.QName(parent).localname

    # If parent itself is the tag, adjust to search in grandparent
    if etree.QName(parent).localname == tag:
        grandparent = parent.getparent()
        if grandparent is not None:
            parent = grandparent

    # Build XPath
    xpath = f".//tei:{tag}"
    if attr_name and attr_value:
        xpath += f"[@{attr_name}='{attr_value}']"
    elif attr_name:
        xpath += f"[@{attr_name}]"

    elements = parent.xpath(xpath, namespaces=nsmap)

    if index is not None and 0 <= index < len(elements):
        element = elements[index]
        if attr_name in element.attrib:
            del element.attrib[attr_name]


        etree.ElementTree(tei_root).write(
            file_path,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )

        return True

    return False

def delete_tei_element(
    *,
    tei_root,
    parent,
    file_path,
    tag,
    index,
    nsmap,
    attr_name=None,
    attr_value=None, 
    ):

    """
    Delete a specified TEI element under a given parent element and save the XML.

    If the parent element itself matches the target tag, the function searches in the grandparent
    to correctly find the element.

    Args:
        tei_root (lxml.etree._Element): Root element of the TEI tree.
        parent (lxml.etree._Element): Parent element under which to search.
        file_path (str): Path to save the modified XML file.
        tag (str): Tag name of the element(s) to delete.
        index (int): Index of the target element among all matching elements.
        nsmap (dict): Namespace mapping for XPath searches.
        attr_name (str, optional): Only consider elements with this attribute.
        attr_value (str, optional): Only delete element if the attribute matches this value.

    Returns:
        bool: True if the element was found and deleted; False otherwise.
    """

    # Build XPath
    xpath = f".//tei:{tag}"
    if attr_name and attr_value:
        xpath += f"[@{attr_name}='{attr_value}']"
    elif attr_name:
        xpath += f"[@{attr_name}]"

    # Find matching elements
    elements = parent.xpath(xpath, namespaces=nsmap)

    if index is not None and 0 <= index < len(elements):
        element_to_delete = elements[index]
        element_parent = element_to_delete.getparent()
        element_parent.remove(element_to_delete)

        etree.ElementTree(tei_root).write(
            file_path,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )

        return True

    return False

def add_simple_element_attr(
    *,
    parent,
    tag,
    text=None,
    rem_attrs=None,
    attrs=None,
    allow_multiple=True
):
    """
    Create and insert a TEI-namespaced child element under a parent element.

    Optionally removes existing elements of the same tag, sets text content,
    and assigns attributes.

    Args:
        parent (lxml.etree._Element):
            Parent TEI element to insert into.
        tag (str):
            Local name of the TEI element to create (e.g. "birth", "idno").
        text (str, optional):
            Text content for the new element.
        attrs (dict[str, str], optional):
            Attribute names and values to set on the element.
        allow_multiple (bool, optional):
            If False, existing child elements with the same tag are removed
            before creating the new element.

    Returns:
        lxml.etree._Element:
            The newly created TEI element.
    """
    if not allow_multiple:
        for el in parent.findall(f"tei:{tag}", namespaces=NSMAP):
            if rem_attrs:
                # only remove if all attributes match
                if all(el.get(k) == v for k, v in rem_attrs.items()):
                    parent.remove(el)
            else:
                # no attribute filter → remove all
                parent.remove(el)

    el = etree.SubElement(parent, f"{{{NS_TEI}}}{tag}")
    if attrs:
        for k, v in attrs.items():
            el.set(k, v)
    if text:
        el.text = text

    return el

def build_section(
    *,
    parent,
    item_tag,
    text=None,
    attrs=None,
    rem_attrs=None,
    allow_multiple=True,
    child_tag=None,
    child_text=None,
    child_attrs=None
):
    """
    Add or replace a TEI element under a parent, optionally with a nested child.

    Args:
        parent (Element): Parent element
        item_tag (str): Tag of the element to create
        text (str, optional): Text content for the element
        attrs (dict, optional): Attributes for the element
        multiple (bool, optional): If False, replaces existing elements
        child_tag (str, optional): Nested child element tag
        child_text (str, optional): Text for the child element
        child_attrs (dict, optional): Attributes for the child element

    Returns:
        lxml.etree._Element: The newly created element
    """
    if not allow_multiple:
        for el in parent.findall(f"tei:{tag}", namespaces=NSMAP):
            if rem_attrs:
                # only remove if all attributes match
                if all(el.get(k) == v for k, v in rem_attrs.items()):
                    parent.remove(el)
            else:
                # no attribute filter → remove all
                parent.remove(el)

    el = etree.SubElement(parent, f"{{{NS_TEI}}}{item_tag}")

    if attrs:
        for k, v in attrs.items():
            el.set(k, v)

    if text:
        el.text = text

    if child_tag:
        child = etree.SubElement(el, f"{{{NS_TEI}}}{child_tag}")
        if child_attrs:
            for k, v in child_attrs.items():
                child.set(k, v)
        if child_text:
            child.text = child_text

    return el

def load_or_create_entity(entity_name, entity_dir, template_path, nsmap, xml_id=None):
    """Load existing TEI entity XML or create a new one from template."""
    
    config = ENTITY_CONFIG[entity_name]
    container_tag = config["container_tag"]
    element_tag = config["element_tag"]
    file_prefix = config["prefix"]

    context = {"entity_name": entity_name, "nsmap": nsmap}

    if xml_id:  # Load existing
        file_path = os.path.join(entity_dir, f"{xml_id}.xml")
        if not os.path.exists(file_path):
            return None
        tree = etree.parse(file_path)
        root = tree.getroot()
        entity_elem = root.find(f".//tei:{element_tag}[@xml:id='{xml_id}']",namespaces=nsmap)

        if entity_elem is None:
            raise RuntimeError(f"{element_tag} with xml:id='{xml_id}' not found in {file_path}")
    
    else:  # Create new
        file_name = next_entity_file(file_prefix, entity_dir)
        xml_id = file_name[:-4]
        file_path = os.path.join(entity_dir, file_name)
        
        tree = etree.parse(template_path)
        root = tree.getroot()
        
        container = root.find(container_tag, namespaces=nsmap)
        entity_elem = container.find(f"tei:{element_tag}", namespaces=nsmap)

        if f"{{{NS_XML}}}id" not in entity_elem.attrib:
            entity_elem.set(f"{{{NS_XML}}}id", xml_id)

    context.update({
        "xml_id": xml_id,
        "file_path": file_path,
        "tree": tree,
        "root": root,
        "entity_elem": entity_elem,
    })
    return context

def write_entity_to_file(context):
    """Save entity XML to disk."""
    etree.indent(context["root"], space="  ")
    etree.ElementTree(context["root"]).write(
        context["file_path"],
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True
    )


def handle_deletions(entity_elem, form_data, context):
    """
    Handles deletion of TEI elements or attributes based on form data.

    Returns True if a deletion occurred, False otherwise.
    """
    delete_index = form_data.get("delete_index")
    tei_root = context["root"]
    file_path = context["file_path"]

    search_from_root = form_data.get("from_root") == "1"
    parent = context["root"] if search_from_root else entity_elem

    # ----- Delete element -----
    delete_tag = form_data.get("delete")
    element_attr_name = form_data.get("element_attr_name")
    element_attr_value = form_data.get("element_attr_value")
    

    if delete_tag:
        try:
            index = int(delete_index)
        except (ValueError, TypeError):
            index = 0

        deleted_elem = delete_tei_element(
            tei_root=tei_root,
            parent=parent,
            file_path=file_path,
            tag=delete_tag,
            index=index,
            nsmap=NSMAP,
            attr_name=element_attr_name,
            attr_value=element_attr_value
        )
        if deleted_elem:
            return True

    # ----- Delete attribute -----
    delete_attribute_tag = form_data.get("delete_attribute_tag")
    delete_attribute = form_data.get("delete_attribute")
    delete_attribute_value = form_data.get("delete_attribute_value")

    if delete_attribute_tag:
        try:
            index = int(delete_index)
        except (ValueError, TypeError):
            index = 0

        deleted_attr = delete_tei_attribute(
            tei_root=tei_root,
            parent=parent,
            file_path=file_path,
            tag=delete_attribute_tag,
            index=index,
            nsmap=NSMAP,
            attr_name=delete_attribute,
            attr_value=delete_attribute_value
        )
        if deleted_attr:
            return True

    return False

