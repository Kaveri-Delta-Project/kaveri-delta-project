from lxml import etree
from unidecode import unidecode
import string
import requests
import os, re
from flask import request, redirect, url_for, flash
from collections import defaultdict

from config import API_URL
API_KEY = "MivIraDr46"


#1. Text and grouping utilities


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



#2. Validation utilities


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



#3.  Lower level XML extraction utilities


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


def get_element_attr_by_index(parent, tag, index, attr, ns, match_attrs=None, from_child=False):
    """
    Retrieve an attribute value from a child element by index.

    Elements are first filtered by tag name and optional attribute criteria,
    then the element at the given index is selected.

    Optionally retrieves the attribute from the first child element instead
    of the matched element itself.

    Args:
        parent (lxml.etree._Element): Parent element to search within.
        tag (str): Tag name of child elements.
        index (int): Index within the filtered list of elements.
        attr (str): Attribute name to retrieve
        ns (str): Namespace URI used when matching elements.
        match_attrs (dict, optional): Attribute-value pairs used to filter elements.
        from_child (bool, optional): If True, retrieve attribute from the first child element.

    Returns:
        str or None: The attribute value, or None if not found or index is out of range.
    """
    match_attrs = match_attrs or {}

    #find direct child elements matching the tag
    elements = parent.findall(f"{{{ns}}}{tag}")

    #apply attribute filtering
    elements = [
        el for el in elements
        if all(el.get(k) == v for k, v in match_attrs.items())
    ]

    #return None if index is out of range
    if index < 0 or index >= len(elements):
        return None

    el = elements[index]

    #optionally switch to first child for attribute retrieval
    if from_child:
        # filter children to include only real element nodes
        children = [c for c in el if isinstance(c.tag, str)]
        if children:
            el = children[0]
        else:
            return None

    #return the requested attribute
    val = el.get(attr)
    return val.strip() if val else None


#4. Entity Loading / High-level Extraction


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


def load_ent_name_by_key(entity_type, config, key, elem_name, nsmap):
    """
    Load a TEI XML file and return the preferred name for a given element.

    Searches for the first matching element with @type="preferred"
    (e.g. persName, placeName, title) and returns its text content.

    Args:
        entity_type (str): Configuration key ("place", "work", etc)
        config (dict): Configuration dictionary for the entity type.
            Must include:
                - "dir" (str): Directory where entity XML files are stored.
        key (str): Identifier of the XML file (without ".xml").
        elem_name (str): Local name of the TEI element to search for.
        nsmap (dict): Namespace mapping for XPath queries.

    Returns:
        str | None: The stripped text content of the preferred name element,
            or None if the file does not exist, parsing fails, or no matching
            element with text is found.
    """

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
        namespaces=nsmap
    )

    #return stripped text if found and non-empty
    if name_elem is not None and name_elem.text:
        return name_elem.text.strip()

    return None


def load_or_create_entity(entity_name, config, nsmap, ns_xml, xml_id=None):
    """
    Initialise and return a working context for a TEI entity.

    The function either loads an existing entity XML file (when `xml_id` is provided)
    or creates a new one from a template. In both cases, it prepares a consistent
    context dictionary containing the parsed XML tree, root element, target entity
    element, and file metadata.

    This context is intended to be passed to downstream functions for reading,
    editing, or writing entity data.

    Args:
        entity_name (str): Configuration key ("place", "work", etc)
        config (dict): Configuration dictionary for the entity type. Must include:
            - "dir": Directory containing entity files
            - "template": Path to the TEI template file
            - "container_tag": XPath to the container element
            - "element_tag": Tag name of the entity element
            - "prefix": Filename prefix for new entities
        nsmap (dict): Namespace mapping for XPath queries.
        ns_xml (str): Namespace URI for XML attributes (e.g. xml:id).
        xml_id (str, optional): Identifier of an existing entity (without ".xml").

    Returns: dict | None:
        Context dictionary containing:
            - "xml_id": Entity identifier
            - "file_path": Path to the XML file
            - "tree": Parsed ElementTree
            - "root": Root element
            - "entity_elem": Target entity element

        Returns None if loading an existing file fails.
    """
    
    #extract entity-specific configuration from config dict 
    entity_dir = config["dir"]
    template_path = config["template"]
    container_tag = config["container_tag"]
    element_tag = config["element_tag"]
    file_prefix = config["prefix"]

    #initialise shared context used for both loading and creating entities
    context = {"entity_name": entity_name, "nsmap": nsmap}

    if xml_id:
        
        #load existing entity XML file
        file_path = os.path.join(entity_dir, f"{xml_id}.xml")        
        if not os.path.exists(file_path):
            return None
        
        tree = etree.parse(file_path)
        root = tree.getroot()
        
        #locate the entity element by xml:id within the document
        entity_elem = root.find(f".//tei:{element_tag}[@xml:id='{xml_id}']",namespaces=nsmap)

        if entity_elem is None:
            raise RuntimeError(f"{element_tag} with xml:id='{xml_id}' not found in {file_path}")
    
    else:

        #create new entity from template file 
        file_name = next_entity_file(file_prefix)
        xml_id = file_name[:-4]
        file_path = os.path.join(entity_dir, file_name)

        #prevent accidental file overwrite
        if os.path.exists(file_path):
            raise FileExistsError(
                f"Entity file already exists: {file_path}. "
                f"Check counter sync or existing corpus state."
            )
        
        tree = etree.parse(template_path)
        root = tree.getroot()
        
        #locate entity container in template and extract base entity element
        container = root.find(container_tag, namespaces=nsmap)
        entity_elem = container.find(f"tei:{element_tag}", namespaces=nsmap)

        #assign xml:id if not already present
        if f"{{{ns_xml}}}id" not in entity_elem.attrib:
            entity_elem.set(f"{{{ns_xml}}}id", xml_id)

    #populate and return full entity context
    context.update({
        "xml_id": xml_id,
        "file_path": file_path,
        "tree": tree,
        "root": root,
        "entity_elem": entity_elem,
    })
    
    return context



#5. XML Mutation (write helpers)


def add_simple_element_attr(
    *,
    parent,
    tag,
    nsmap,
    ns,
    text=None,
    rem_attrs=None,
    attrs=None,
    allow_multiple=True
):
    """
    Create and insert a TEI-namespaced child element under a parent element.

    Optionally removes existing elements of the same tag (and optionally matching
    attribute filters), sets text content, and assigns attributes.

    Args:
        parent (lxml.etree._Element): Parent TEI element to insert into.
        tag (str): Local name of the TEI element to create.
        nsmap (dict): Namespace mapping used for XPath queries and element searches.
        ns (str): Namespace URI used when constructing new elements.
        text (str, optional): Text content for the new element.
        rem_attrs (dict[str, str], optional): If provided and allow_multiple is False, only existing elements whose
            attributes match all key-value pairs are removed before insertion.
        attrs (dict[str, str], optional): Attribute names and values to set on the element.
        allow_multiple (bool, optional): If False, existing matching elements are removed before creating the new element.

    Returns:
        lxml.etree._Element: The newly created element.
    """
    
    #if duplicates are not allowed, remove existing matching elements first
    if not allow_multiple:
        for el in parent.findall(f"tei:{tag}", namespaces=nsmap):
            
            #if attribute filters are provided, only remove elements that fully match
            if rem_attrs:
                if all(el.get(k) == v for k, v in rem_attrs.items()):
                    parent.remove(el)
            else:
                #if no attribute filters then remove all elements with this tag
                parent.remove(el)

    #create new element using full namespace URI
    el = etree.SubElement(parent, f"{{{ns}}}{tag}")
    
    #add attributes if provided
    if attrs:
        for k, v in attrs.items():
            el.set(k, v)
    
    #set text content if provided
    if text:
        el.text = text

    return el


def update_simple_element_attr(parent, tag, text, ns, update_attrs=None, match_attrs=None, index=0, error_category=None):
    """
    Update the text and attributes of a matching TEI child element.

    Elements are selected by tag name and optionally filtered by attribute
    values. If multiple matches exist, a specific element is selected using
    the provided index.

    Args:
        parent (lxml.etree._Element): Parent TEI element containing children.
        tag (str): Local tag name of child elements to search for.
        text (str): New text content to assign to the element.
            If None, existing text is left unchanged.
        ns (str): Namespace URI used when matching elements.
        update_attrs (dict): Attributes to set on the selected element. 
            Existing attributes not included here may be removed.
        match_attrs (dict): Attribute filter used to restrict which elements are eligible for updating.
        index (int): Index of the matching element to update (default is 0).
        error_category (str): Flask flash category used if the index is out of range.

    Returns:
        lxml.etree._Element | None: The updated element if successful, otherwise None.
    """
    
    match_attrs = match_attrs or {}
    update_attrs = update_attrs or {}

    #find all elements matching tag and namespace
    #then apply optional attribute-based filtering
    elements = [
        el for el in parent.findall(f"{{{ns}}}{tag}")
        if all(el.get(k) == v for k, v in match_attrs.items())
    ]

    #validate index before attempting update
    if index < 0 or index >= len(elements):
        if error_category:
            flash("Edit index out of range.", error_category)
        return None

    #select target element
    el = elements[index]

    #update text content only if explicitly provided
    if text is not None:
        el.text = text

    #apply attribute updates (overwrite / add)
    for k, v in update_attrs.items():
        el.set(k, v)

    #remove stale attributes:
    # - not in update_attrs
    # - not part of selection filter (match_attrs)
    for k in list(el.attrib.keys()):
        if k not in update_attrs and k not in match_attrs:
            del el.attrib[k]

    return el


def build_section(
    *,
    parent,
    item_tag,
    nsmap,
    ns,
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

    If `allow_multiple` is False, existing elements with the same tag are removed
    before inserting the new element. Removal can be restricted to elements
    matching specific attributes.

    If `child_tag` is provided, a single child element is created
    under the new element. Child attributes and text are applied if provided.

    Args:
        parent (lxml.etree._Element): Parent TEI element to insert into.
        item_tag (str): Local name of the TEI element to create.
        nsmap (dict):  Namespace mapping used for element lookup.
        ns (str): Namespace URI used when constructing new elements.
        text (str, optional): Text content for the new element.
        attrs (dict[str, str], optional): Attribute names and values to set on the element.
        rem_attrs (dict[str, str], optional): If provided and allow_multiple is False, only existing elements whose
            attributes match all key-value pairs are removed before insertion.
        allow_multiple (bool, optional): If False, existing matching elements are removed before creating the new element.
        child_tag (str, optional): Local name of a nested child element to create.
        child_text (str, optional): Text content for the child element.
        child_attrs (dict, optional): Attributes for the child element.

    Returns:
        lxml.etree._Element: The newly created parent element. If `child_tag` is provided,
            the returned element will contain the created child element.
    """
    
    #if duplicates are not allowed, remove existing elements first
    if not allow_multiple:
        for el in parent.findall(f"tei:{item_tag}", namespaces=nsmap):
            
            #if attribute filters are provided, only remove elements that fully match
            if rem_attrs:
                if all(el.get(k) == v for k, v in rem_attrs.items()):
                    parent.remove(el)
            else:
                #if no attribute filter then remove all elements with this tag
                parent.remove(el)

    #create new element using full namespace URI
    el = etree.SubElement(parent, f"{{{ns}}}{item_tag}")

    #add attributes if provided
    if attrs:
        for k, v in attrs.items():
            el.set(k, v)

    #set text content if provided
    if text:
        el.text = text

    #optionally create a nested child element 
    if child_tag:
        child = etree.SubElement(el, f"{{{ns}}}{child_tag}")
        
        #apply attributes to child element if provided
        if child_attrs:
            for k, v in child_attrs.items():
                child.set(k, v)
        
        #set child text content if provided
        if child_text:
            child.text = child_text

    return el


def update_build_section(
    *,
    parent,
    item_tag,
    ns,
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
    Update the text and attributes of a matching TEI element,
    and update or create child elements, text and attributes if provided. 

    Elements are first filtered by `item_tag` and optional `match_attrs`. The element
    at the specified index is then updated. This function mirrors `build_section`
    behaviour by updating attributes, text content, and optionally a nested child element.

    Args:
        parent (lxml.etree._Element): Parent TEI element containing children.
        item_tag (str): Local tag name of child elements to search for.
        ns (str): Namespace URI used when matching elements.
        index (int): Index of the matching element to update (default is 0).
        match_attrs (dict): Attribute filter used to restrict which elements are eligible for updating.
        text (str): New text content to assign to the element.
            If None, existing text is left unchanged.
        element_attrs (dict[str, str | None], optional): Attributes to set on the selected element. 
            Existing attributes not included here may be removed.
        child_tag (str, optional): Local name of a nested child element to update or create.
        child_text (str, optional): Text content for the child element.
        child_attrs (dict[str, str], optional): Attributes to set on the child element.
        error_category (str, optional): Flask flash category used if the index is out of range.

    Returns:
        lxml.etree._Element | None: The updated element if successful, otherwise None.
    """
    
    match_attrs = match_attrs or {}
    element_attrs = element_attrs or {}

    #find all elements matching tag and namespace
    #then apply optional attribute-based filtering
    elements = [
        el for el in parent.findall(f"{{{ns}}}{item_tag}")
        if all(el.get(k) == v for k, v in match_attrs.items())
    ]

    #validate index before attempting update
    if index < 0 or index >= len(elements):
        if error_category:
            flash("Edit index out of range.", error_category)
        return None

    #select target element
    el = elements[index]

    #update text content only if explicitly provided
    if text is not None:
        el.text = text

    #apply attribute updates (overwrite / add)
    for k, v in element_attrs.items():
        if v is None:
            #remove attribute if explicitly set to None
            if k in el.attrib:
                del el.attrib[k]
        else:
            el.set(k, v)

    #remove stale attributes:
    # - not in element_attrs
    # - not part of selection filter (match_attrs)
    for k in list(el.attrib.keys()):
        if k not in element_attrs and k not in match_attrs:
            del el.attrib[k]

    #optionally update or create a nested child element
    if child_tag:
        child = el.find(f"{{{ns}}}{child_tag}")
        
        #create child if it does not exist
        if child is None:
            child = etree.SubElement(el, f"{{{ns}}}{child_tag}")
        
        #apply attributes to child element if provided
        if child_attrs:
            for k, v in child_attrs.items():
                child.set(k, v)
        
        #set child text if explicitly provided
        if child_text is not None:
            child.text = child_text

    return el



#6. Deletion Logic


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
    Delete an attribute from a TEI element selected by tag and index, then save the XML.

    Elements are selected using an XPath query under the given parent,
    filtered by the presence of an attribute and/or a specific attribute value.
    The element at the specified index in the resulting list is targeted.

    If the provided parent element already matches the target tag, the search is
    performed from its parent (i.e. the grandparent) to avoid selecting the same
    node and to allow correct indexing among sibling elements.

    Args:
        tei_root (lxml.etree._Element): Root element of the TEI document.
        parent (lxml.etree._Element): Element under which to search.
        file_path (str): Path to save the modified XML file
        tag (str): Tag name of the target elements.
        index (int): Index within the filtered list of matching elements.
        nsmap (dict): Namespace mapping for XPath queries.
        attr_name (str): Name of the attribute to delete.
        attr_value (str, optional): If provided, only elements with this attribute
            value are considered.

    Returns:
        bool: True if a matching element was found (the file is updated if the attribute exists)
        False otherwise.
    """

    #if parent is already the target tag, move up one level
    #to avoid selecting the same node and to allow correct indexing
    if etree.QName(parent).localname == tag:
        grandparent = parent.getparent()
        if grandparent is not None:
            parent = grandparent

    #build XPath to select target elements
    xpath = f".//tei:{tag}"
    
    #apply attribute filtering:
    #- if attr_value is provided match specific value
    #- otherwise match elements that simply have the attribute
    if attr_name and attr_value:
        xpath += f"[@{attr_name}='{attr_value}']"
    elif attr_name:
        xpath += f"[@{attr_name}]"

    #execute XPath query
    elements = parent.xpath(xpath, namespaces=nsmap)

    #check that index is valid within the filtered results
    if index is not None and 0 <= index < len(elements):
        element = elements[index]
        
        #delete attribute if it exists on the selected element
        if attr_name in element.attrib:
            del element.attrib[attr_name]

        #write updated XML back to file
        etree.ElementTree(tei_root).write(
            file_path,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )

        return True

    #no matching element/attribute found or index out of range
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
    delete_parent=False
    ):

    """
    Delete a TEI element selected by tag and index, then save the XML.

    Elements are selected using an XPath query under the given parent,
    optionally filtered by attribute presence and/or value. The element
    at the specified index in the resulting list is removed.

    If `delete_parent` is True, the immediate parent of the matched element
    is deleted instead of the element itself.

    Args:
        tei_root (lxml.etree._Element): Root element of the TEI document.
        parent (lxml.etree._Element): Element under which to search.
        file_path (str): Path to save the modified XML file.
        tag (str): Tag name of the target elements.
        index (int): Index within the filtered list of matching elements.
        nsmap (dict): Namespace mapping for XPath queries.
        attr_name (str, optional): Only consider elements with this attribute.
        attr_value (str, optional): If provided, only elements with this attribute
            value are considered.
        delete_parent (bool, optional): If True, deletes the immediate parent of the
            matched element instead of the element itself.

    Returns:
        bool: True if a matching element was found and deleted, False otherwise.
    """

    #build XPath to select target elements
    xpath = f".//tei:{tag}"
    
    #apply attribute filtering:
    #- if attr_value is provided match specific value
    #- otherwise match elements that simply have the attribute
    if attr_name and attr_value:
        xpath += f"[@{attr_name}='{attr_value}']"
    elif attr_name:
        xpath += f"[@{attr_name}]"

    #execute XPath query
    elements = parent.xpath(xpath, namespaces=nsmap)

    #check that index is valid within the filtered results
    if index is not None and 0 <= index < len(elements):
        element_to_delete = elements[index]

        #decide target (self vs parent)
        if delete_parent:
            element_to_delete = element_to_delete.getparent()
        
        #remove the selected element from its parent node
        element_parent = element_to_delete.getparent()
        element_parent.remove(element_to_delete)

        #write updated XML back to file
        etree.ElementTree(tei_root).write(
            file_path,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )

        return True
    
    #no matching element/attribute found or index out of range
    return False


def handle_deletions(entity_elem, form_data, context, nsmap):
    """
    Handles deletion of TEI elements or attributes based on submitted form data.

    Supports two operations:
    - Deleting a TEI element selected by tag, optional attribute filters, and index
    - Deleting a TEI attribute from a selected element

    The target search scope can be switched between the entity element and the
    full TEI document root using the `from_root` form flag.

    If `delete_index` is missing or invalid, index defaults to 0.

    Args:
        entity_elem (lxml.etree._Element): Current entity element.
        form_data (dict): Submitted form data containing deletion instructions.
        context (dict): Runtime TEI context containing:
            - "root": TEI document root element
            - "file_path": Path to XML file
        nsmap (dict): Namespace mapping for XPath queries.
        
    Returns:
        bool: True if a deletion (element or attribute) was performed, False otherwise.    
    """
    
    #extract deletion index
    delete_index = form_data.get("delete_index")
    #safe index fallback (0 if missing)
    index = int(delete_index or 0)
    
    #access TEI document root and file path from runtime context
    tei_root = context["root"]
    file_path = context["file_path"]

    #determine search scope (entity vs full document)
    search_from_root = form_data.get("from_root") == "1"
    parent = context["root"] if search_from_root else entity_elem

    #optional flag: delete parent of matched element instead of element itself
    delete_parent = form_data.get("delete_parent") == "1"

    #delete TEI element
    
    #element deletion parameters from form
    delete_tag = form_data.get("delete")
    element_attr_name = form_data.get("element_attr_name")
    element_attr_value = form_data.get("element_attr_value")

    if delete_tag:

        #attempt deletion of selected element
        deleted_elem = delete_tei_element(
            tei_root=tei_root,
            parent=parent,
            file_path=file_path,
            tag=delete_tag,
            index=index,
            nsmap=nsmap,
            attr_name=element_attr_name,
            attr_value=element_attr_value,
            delete_parent=delete_parent
        )
        
        #early exit if deletion succeeded
        if deleted_elem:
            return True

    #delete TEI attribute

    #attribute deletion parameters from form
    delete_attribute_tag = form_data.get("delete_attribute_tag")
    delete_attribute = form_data.get("delete_attribute")
    delete_attribute_value = form_data.get("delete_attribute_value")

    if delete_attribute_tag:

        #attempt deletion of attribute on selected element
        deleted_attr = delete_tei_attribute(
            tei_root=tei_root,
            parent=parent,
            file_path=file_path,
            tag=delete_attribute_tag,
            index=index,
            nsmap=nsmap,
            attr_name=delete_attribute,
            attr_value=delete_attribute_value
        )
        
        #early exit if deletion succeeded
        if deleted_attr:
            return True

    #no deletion performed
    return False



#7. File / Persistence


def write_entity_to_file(context):
    """Save entity XML to disk."""
    etree.indent(context["root"], space="  ")
    etree.ElementTree(context["root"]).write(
        context["file_path"],
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True
    )


def next_entity_file(prefix, extension="xml"):
    """
    Get next filename from central counter service.

    Args:
        prefix (str): entity prefix (e.g. "w", "isc", "p")
        extension (str): file extension (default "xml")

    Returns:
        str: next filename in format "<prefix>_<number>.<extension>"
    """
    
    #sanitize inputs (prevents hidden encoding issues)
    prefix = (prefix or "").strip()
    key = (API_KEY or "").strip()

    #optional safety check: detect pre-encoded keys
    if "%" in key:
        raise ValueError("API_KEY looks URL-encoded (invalid state)")

    try:
        #call central counter API (single source of truth for numbering)
        r = requests.get(
            f"{API_URL}/next-id",
            params={
                "prefix": prefix,
                "key": API_KEY
            }
        )

        if not r.ok:
            print("STATUS:", r.status_code)
            print("RESPONSE:", r.text)
            print("REQUEST URL:", r.url)

        #raise error for HTTP failures (4xx / 5xx)
        r.raise_for_status()
        
        #parse JSON response from API
        data = r.json()

        filename = data["filename"]

        if not filename:
            raise ValueError("Empty filename returned from API")

        #allow optional extension override (e.g. xml to txt)
        if extension != "xml":
            filename = filename.replace(".xml", f".{extension}")

        return filename

    except requests.exceptions.RequestException as e:
        #covers network errors, DNS issues, connection failures, etc.
        raise RuntimeError(f"Filename service unavailable: {e}")

    except (KeyError, ValueError) as e:
        #covers malformed or unexpected API responses
        raise RuntimeError(f"Invalid response from filename service: {e}")


#8. Ordering / Structure Control


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
        nsmap (dict): Namespace mapping for XPath queries.
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

