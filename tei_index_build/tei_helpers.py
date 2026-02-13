import os
from lxml import etree


#1. XML loading helpers

def get_xml_tree(filename, directory):
    """
    Load an XML file by filename from a directory.

    Hidden files and non-XML files are ignored.

    Args:
        filename (str): Name of the XML file.
        directory (str): Directory containing the XML files.

    Returns:
        lxml.etree._ElementTree or None:
            Parsed XML tree, or None if the file is missing or invalid.
    """
    if not filename.endswith(".xml") or filename.startswith("."):
        return None
    path = os.path.join(directory, filename)
    if not os.path.isfile(path):
        return None
    
    return etree.parse(path)

def load_xml_by_id(identifier, directory, cache):
    """
    Load an XML file using an identifier mapped to <identifier>.xml,
    with caching to avoid repeated parsing.

    The identifier is sanitized to prevent path traversal.

    Args:
        identifier (str): XML identifier (without .xml extension).
        directory (str): Directory containing the XML files.
        cache (dict): Dictionary to store parsed XML trees for reuse.

    Returns:
        lxml.etree._ElementTree or None:
            Parsed XML tree if the file exists and is valid; otherwise None.
    """
    safe_id = os.path.basename(identifier)
    filename = f"{safe_id}.xml"
    path = os.path.join(directory, filename)
    if not os.path.isfile(path):
        return None
    tree = get_cached_tree(filename, directory, cache)

    return tree

def get_cached_tree(filename, directory, cache):
    """
    Load an XML file and cache its parsed tree to avoid repeated parsing.

    If the file has already been loaded during this run, the cached
    tree is returned instead of re-parsing the file from disk.

    Args:
        filename (str): Name of the XML file.
        directory (str): Directory containing the XML files.
        cache (dict[str, lxml.etree._ElementTree]): Dictionary used to
            store cached XML trees keyed by filename.

    Returns:
        lxml.etree._ElementTree or None:
            Parsed XML tree, or None if the file is missing or invalid.
    """
    if filename not in cache:
        tree = get_xml_tree(filename, directory)
        if tree is None:
            return None
        cache[filename] = tree
    
    return cache[filename]

#2. Element and attribute extractors

def extract_element_text(tree, ns, element, filter_attr=None, filter_value=None, all_results=False):
    """
    Extract text content from matching TEI elements.

    Optionally filters by attribute presence/value.

    Args:
        tree (lxml.etree._ElementTree): XML tree to query.
        ns (dict): Namespace mapping for XPath.
        element (str): TEI element name (without namespace prefix).
        filter_attr (str or None): Attribute name to filter on.
        filter_value (str or None): Attribute value to match.
        all_results (bool): Whether to return all matches or only the first.

    Returns:
        str or list[str] or None:
            First matching text, list of texts, or None if no match.
    """
    if not tree:
        return [] if all_results else None
    
    xpath = f"//tei:{element}"
    if filter_attr:
        if filter_value is not None:
            xpath += f'[@{filter_attr}="{filter_value}"]'
        else:
            xpath += f'[@{filter_attr}]'
    
    results = tree.xpath(xpath, namespaces=ns)
    texts = [el.text.strip() for el in results if el.text and el.text.strip()]

    return texts if all_results else (texts[0] if texts else None)

def extract_attribute_values(tree, ns, element, filter_attr, all_results=False):
    """
    Extract attribute values from matching TEI elements and attribute names.

    Args:
        tree (lxml.etree._ElementTree): XML tree to query.
        ns (dict): Namespace mapping for XPath.
        element (str): TEI element name.
        filter_attr (str): Attribute name to extract.
        all_results (bool): Whether to return all matches or only the first.

    Returns:
        str or list[str] or None:
            First matching attribute value, list of values, or None if no match.
    """
    if not tree:
        return [] if all_results else None
    
    xpath = f"//tei:{element}/@{filter_attr}"
    
    results = tree.xpath(xpath, namespaces=ns)
    values = [val.strip() for val in results if val and val.strip()]

    return values if all_results else (values[0] if values else None)

#3. Mid-level helpers

def get_main_file_data(filename, directory, ns, id_elem, name_elem, cache):
    """
    Extract key metadata from a TEI XML file for indexing purposes.

    Retrieves the parsed XML tree (using the cache if available), the XML ID,
    the preferred name, and the first letter of the preferred name (for alphabetical grouping).

    Args:
        filename (str): XML filename.
        directory (str): Directory containing XML files.
        ns (dict): Namespace mapping for XPath.
        id_elem (str): Element containing the xml:id attribute.
        name_elem (str): Element containing the preferred name.
        cache (dict): Dictionary to store parsed XML trees for reuse.

    Returns:
        tuple or None:
            (tree, id_text, name_text, first_letter) or None if missing data.
    """ 
    tree = get_cached_tree(filename, directory, cache)
    if not tree:
        return None

    id_text = extract_attribute_values(tree, ns, element=id_elem, filter_attr="xml:id", all_results=False)
    if not id_text:
        return None

    name_text = extract_element_text(tree, ns, element=name_elem, filter_attr="type", filter_value="preferred", all_results=False)
    if not name_text:
        return None

    first_letter = name_text[0].upper()

    return tree, id_text, name_text, first_letter

def extract_reference_data(tree, ns, directory, id_elem, name_elem, cache):
    """
    Extract direct reference data to indexed items in another directory
    from an XML tree. Checks for and extracts all references.

    Each reference is resolved to its target XML file and its preferred name 
    The target XML file is loaded (using caching to avoid repeated parsing)
    and its preferred name is extracted.

    Args:
        tree (lxml.etree._ElementTree): Source XML tree.
        ns (dict): Namespace mapping for XPath.
        directory (str): Directory containing target XML files.
        id_elem (str): Element containing @key references in source tree.
        name_elem (str): Element containing preferred names in target files.
        cache (dict): Dictionary to store parsed XML trees for reuse.

    Returns:
        list[tuple[str, str]]:
            List of (identifier, preferred_name) tuples.
    """
    data = []

    target_ids = extract_attribute_values(tree, ns, element=id_elem, filter_attr="key", all_results=True)

    for target_id in target_ids:
        target_tree = load_xml_by_id(target_id, directory, cache)
        if not target_tree:
            continue
        name_text = extract_element_text(target_tree, ns, element=name_elem, filter_attr="type", filter_value="preferred", all_results=False)
        if not name_text:
            continue
        data.append((target_id, name_text))

    return data
