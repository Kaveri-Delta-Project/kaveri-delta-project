from lxml import etree
from unidecode import unidecode
import string
import os, re
from config import ENTITY_CONFIG, NS_TEI, NS_XML, NSMAP, DEFAULT_NSMAP
from flask import request, redirect, url_for, flash
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
    Group items alphabetically by the first letter of their normalized name.

    - Uses normalize_for_sort() to remove diacritics and lowercase
    - Groups under A–Z, with '#' for non-letter or missing names
    - Sorts items within each group alphabetically

    Args:
        items (list[dict]): Each item should have at least 'name' and 'xml_id'.
        
    Returns:
        dict[str, list[dict]]: Keys are 'A'-'Z' plus '#' for non-letter starts.
    """
    # Initialize A-Z plus '#' for non-letter starting items
    grouped = {letter: [] for letter in string.ascii_uppercase}
    grouped["#"] = []

    for item in items:
        #get name safely (fallback to empty string)
        name = item.get("name") or ""
        normalized = normalize_for_sort(name)

        #determine grouping key (first letter or '#')
        if normalized and normalized[0].isalpha():
            first_letter = normalized[0].upper()
        else:
            first_letter = "#"

        grouped[first_letter].append(item)

    #sort items within each group by normalized name (fallback to xml_id)
    for letter, items_in_group in grouped.items():
        items_in_group.sort(key=lambda x: normalize_for_sort(x.get("name") or x["xml_id"]))

    return grouped


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
    if not parent:
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
    if not parent:
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


def get_element_attr_by_index(parent, tag, index, attr, match_attrs=None):
    """
    Retrieve an attribute value from a child element by index.

    Elements are first filtered by tag name and optional attribute criteria,
    then the element at the given index is selected.

    Args:
        parent (lxml.etree._Element): Parent element to search within.
        tag (str): Tag name of child elements.
        index (int): Index within the filtered list of elements.
        attr (str): Attribute name to retrieve
        match_attrs (dict, optional): Attribute-value pairs used to filter elements.

    Returns:
        str or None: The attribute value, or None if not found or index is out of range.
    """
    match_attrs = match_attrs or {}

    #find direct child elements matching the tag
    elements = parent.findall(f"{{{NS_TEI}}}{tag}")

    #apply attribute filtering
    elements = [
        el for el in elements
        if all(el.get(k) == v for k, v in match_attrs.items())
    ]

    #return None if index is out of range
    if index < 0 or index >= len(elements):
        return None

    #return the requested attribute
    val = elements[index].get(attr)
    return val.strip() if val else None

def load_ent_name_by_key(entity_type, key, elem_name):
    """
    Load a TEI XML file and return the preferred name for a given element.

    Searches for the first matching element with @type="preferred"
    (e.g. persName, placeName, title) and returns its text content.

    Args:
        entity_type (str): Entity type key used in ENTITY_CONFIG.
        key (str): XML file identifier.
        elem_name (str): TEI element name to search for.

    Returns:
        str or None: Preferred name text, or None if not found.
    """
    
    #get configuration for the entity type
    config = ENTITY_CONFIG.get(entity_type)
    if not config:
        return None

    #build full path to the XML file for this entity
    path = os.path.join(config["dir"], f"{key}.xml")

    #ensure file exists before attempting to parse
    if not os.path.exists(path):
        return None
    try:
        tree = etree.parse(path)
    except Exception:
        return None
    
    root = tree.getroot()

    #find the first TEI element matching the name with @type="preferred"
    name_elem = root.find(
        f".//tei:{elem_name}[@type='preferred']",
        namespaces=NSMAP
    )

    #return stripped text if found and non-empty
    if name_elem is not None and name_elem.text:
        return name_elem.text.strip()

    return None

def valid_date(s):
    """
    Returns True if the input is empty or matches a valid date format.

    Supported formats:
        - Year only: YYYY (e.g. 1666)
        - Full ISO date: YYYY-MM-DD (e.g. 1666-10-14)

    Args:
        s (str): Date string to validate.

    Returns:
        bool: True if valid or empty, otherwise False.
    """
    if not s:
        return True
    return re.match(r"^\d{4}(-\d{2}-\d{2})?$", s) is not None


def valid_identifier(value, id_type):
    """
    Validate an identifier value according to its identifier type.

    Supports:
        - VIAF: numeric string (up to 22 digits)
        - Wikidata: Q followed by digits (e.g. Q123)
        - LCNAF: starts with 'n', optional letter, then digits
        - TGN: numeric string (up to 9 digits)

    Returns:
        bool: True if valid, otherwise False
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
    Validate a coordinate string in the format 'lat, lon'.

    Accepts decimal latitude/longitude pairs.

    Args:
        coord_text (str): Coordinate string.

    Returns:
        bool: True if format is valid, otherwise False.
    """
    if not coord_text:
        return False

    #match "number, number" with optional decimals and whitespace
    pattern = r"^\s*-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?\s*$"
    return bool(re.fullmatch(pattern, coord_text))


def load_entity(file_path, entity_tag, mapping, nsmap):
    """
    Load structured data for a TEI entity from an XML file using a mapping specification.

    This function extracts data from a target TEI element (e.g. person, place, msDesc)
    according to a declarative mapping. Each mapping entry defines how a value should
    be retrieved (attribute, element text, or nested parent structure).

    Args:
        file_path (str): Path to the TEI XML file.
        entity_tag (str): Key used in ENTITY_CONFIG to identify the entity type.
        mapping (dict): Extraction specification. Each key maps to a dict defining
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

        nsmap (dict): Namespace mapping used for XPath queries.

    Returns:
        dict or None:
            Dictionary of extracted values keyed by mapping keys. Values may be:
            - str: single extracted value
            - list[str]: multiple values when "all_results" is True
            - list[dict]: structured results from "parent_tag"

            Returns None if the target entity element is not found.
    """

    #get configuration for the entity type
    config = ENTITY_CONFIG.get(entity_tag)
    if not config:
        return None

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


def insert_in_order(parent, tag, new_elem, child_order, nsmap,
                    sort_attr=None, attr_priority=None):
    """
    Insert an element into a parent and reorder all children based on
    a predefined tag order and optional attribute priority.

    Children are sorted primarily by their tag name according to
    `child_order`. Elements whose tag is not in `child_order` are placed
    at the end.

    Optionally, elements of a specific tag can be secondarily sorted
    using an attribute and a priority mapping.

    Args:
        parent (lxml.etree._Element): The parent element whose children will be reordered.
        tag (str): Tag name to which attribute-based sorting should apply
                   (only used when sort_attr and attr_priority are provided).
        new_elem (lxml.etree._Element): Element to insert into the parent.
        child_order (list[str]): Ordered list of tag names defining the primary sort order.
        nsmap (dict): Namespace mapping.
        sort_attr (str, optional): Attribute name used for secondary sorting.
        attr_priority (dict, optional): Mapping of attribute values to priority.

    Returns:
        None: The parent element is modified in place.
    """

    #get current children as a list
    children = list(parent)
    #add new element if it is not already present
    if new_elem not in children:
        children.append(new_elem)

    sorted_children = []
    
    #build sortable tuples for each child
    for el in children:
        if not isinstance(el.tag, str):
            continue

        #extract local tag name 
        tag_name = el.tag.split("}")[-1]

        #primary sort: position in child_order
        #unknown tags are placed at the end
        tag_index = child_order.index(tag_name) if tag_name in child_order else len(child_order)

        #secondary sort: attribute-based priority (only for matching tag)
        if tag and tag_name == tag and sort_attr and attr_priority:
            attr_value = el.get(sort_attr, "")
            attr_index = attr_priority.get(attr_value, 99)
        else:
            attr_index = 0
        
        #store sorting tuple
        sorted_children.append((tag_index, attr_index, el))

    #sort tuples first by tag order, then attribute priority
    sorted_children.sort(key=lambda x: (x[0], x[1]))

    #clear existing children from parent
    for el in list(parent):
        parent.remove(el)

    #re-append children in sorted order
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
        str: The next available filename using the next number in sequence.
    """

    existing_numbers = []

    #match filenames like "prefix_123.extension"
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)\.{re.escape(extension)}$")

    #collect numeric suffixes from matching filenames
    for f in os.listdir(directory):
        match = pattern.match(f)
        if match:
            existing_numbers.append(int(match.group(1)))

    #determine next number in sequence
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

def update_simple_element_attr(parent, tag, text, update_attrs=None, match_attrs=None, index=0, error_category=None):
    """
    Update the text of an existing child element matching tag + attrs at a given index.

    Args:
        parent: XML/TEI element to update.
        tag (str): The child tag name.
        text (str): New text content.
        update_attrs (dict): Attributes to set on the element.
        match_attrs (dict): Optional attributes to filter which elements to consider.
        index (int): Which matching element to update.
        error_category (str): Optional flash category for errors.

    Returns:
        bool: True if update succeeded, False otherwise.
    """
    
    match_attrs = match_attrs or {}
    update_attrs = update_attrs or {}


    # Find all matching elements
    elements = [
        el for el in parent.findall(f"{{{NS_TEI}}}{tag}")
        if all(el.get(k) == v for k, v in match_attrs.items())
    ]

    if index < 0 or index >= len(elements):
        if error_category:
            flash("Edit index out of range.", error_category)
        return None

    el = elements[index]

    if text is not None:
        el.text = text

    for k, v in update_attrs.items():
        el.set(k, v)

    # Remove old attributes not present in the new attrs
    for k in list(el.attrib.keys()):
        if k not in update_attrs and k not in match_attrs:
            del el.attrib[k]

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



def update_build_section(
    *,
    parent,
    item_tag,
    index=0,
    match_attrs=None,
    text=None,
    element_attrs=None,
    child_tag=None,
    child_text=None,
    child_attrs=None,
    error_category=None
):
    """
    Update an existing TEI element by index from a filtered list, or create it if needed.
    Mirrors build_section logic for attributes and children.

    Args:
        parent: Parent XML element
        item_tag: Tag of element to update
        index: Which matching element to update
        match_attrs: Attributes to filter elements
        text: Text to set on the element
        element_attrs: Attributes to update/set on the element itself
        child_tag: Optional child element tag
        child_text: Optional child element text
        child_attrs: Optional child element attributes
        error_category: Optional flash category

    Returns:
        lxml.etree._Element: The updated element
    """
    match_attrs = match_attrs or {}
    element_attrs = element_attrs or {}

    # Filter elements by match_attrs
    elements = [
        el for el in parent.findall(f"{{{NS_TEI}}}{item_tag}")
        if all(el.get(k) == v for k, v in match_attrs.items())
    ]

    # Check index
    if index < 0 or index >= len(elements):
        if error_category:
            flash("Edit index out of range.", error_category)
        return None

    # Pick the element
    el = elements[index]

    # Update element attributes
    for k, v in element_attrs.items():
        if v is None:
            if k in el.attrib:
                del el.attrib[k]
        else:
            el.set(k, v)

    # Remove old attributes not present in the new attrs
    for k in list(el.attrib.keys()):
        if k not in element_attrs and k not in match_attrs:
            del el.attrib[k]

    # Update text
    if text is not None:
        el.text = text

    # Update or create child element
    if child_tag:
        child = el.find(f"{{{NS_TEI}}}{child_tag}")
        if child is None:
            child = etree.SubElement(el, f"{{{NS_TEI}}}{child_tag}")
        if child_attrs:
            for k, v in child_attrs.items():
                child.set(k, v)
        if child_text is not None:
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

