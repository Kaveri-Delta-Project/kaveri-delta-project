import math
from pathlib import Path
from natsort import os_sorted
import pandas as pd
from bs4 import BeautifulSoup


def get_xml_files(path):
    """
    Return all XML file paths in a directory in natural sort order.

    Args:
        path (str or Path): Directory containing TEI XML files.

    Returns:
        list[Path]:
            List of XML file paths sorted in natural filename order.
    """

    #collect all XML files in the directory and return them in natural sort order
    files = [f for f in Path(path).iterdir() if f.is_file() and f.suffix.lower() == ".xml"]
    
    return os_sorted(files)


def soup_objects(file_paths):
    """
    Parse XML files into BeautifulSoup objects.

    Args:
        file_paths (list[Path]): List of XML file paths to parse.

    Returns:
        list[BeautifulSoup]:
            List of parsed BeautifulSoup objects representing the XML files.
    """

    soups = []
    
    #parse each XML file into a BeautifulSoup object
    for path in file_paths:
        with path.open("r", encoding="utf-8") as xml:
            soups.append(BeautifulSoup(xml, "lxml-xml"))
    return soups


def tei_extractor(soup_ls, element, attributes=None, attribute_vals=None):
    """
    Extract matching TEI elements from a list of parsed XML documents.

    Args:
        soup_ls (list[BeautifulSoup]): Parsed TEI XML documents.
        element (str): TEI element to extract.
        attributes (list[str], optional): Attribute names used to filter the elements.
        attribute_vals (list[str], optional): Attribute values corresponding to
            each attribute name.

    Returns:
        list[list[bs4.element.Tag]]:
            List of matching TEI elements for each XML document.
    """

    attrib_dict = {}

    #build the attribute filter used when searching for TEI elements
    if attributes:
        
        if attribute_vals:
            if len(attributes) != len(attribute_vals):
                raise ValueError("attributes and attribute_vals must match")
            
            #pair each attribute name with its corresponding value
            attrib_dict = dict(zip(attributes, attribute_vals))
        
        else:
            #match any element containing the specified attributes
            attrib_dict = {attr: True for attr in attributes}

    #return all matching elements from each parsed XML document
    return [soup.find_all(element, attrib_dict) for soup in soup_ls]


def scale_size(value, min_size=10, max_size=30):
    """
    Scale a numeric value to a marker size using a logarithmic scale.

    Args:
        value (int or float): Value used to determine the marker size.
        min_size (int, optional): Minimum marker size.
        max_size (int, optional): Maximum marker size.

    Returns:
        float:
            Marker size constrained between the minimum and maximum values.
    """

    #return the minimum size for zero or negative values
    if value <= 0:
        return min_size
    
    #scale larger values logarithmically while capping the maximum size
    return min(max_size, min_size + math.log(value + 1) * 6)


def tei_values(object_lists, subelement=None, attribute=None, strip=True, flatten=False):
    """
    Extract text or attribute values from TEI elements.

    Args:
        object_lists (list[list[bs4.element.Tag]]): TEI elements grouped by
            parent XML document.
        subelement (str, optional): Child element from which to extract
            the value.
        attribute (str, optional): Attribute from which to extract the value
            instead of element text.
        strip (bool, optional): Whether to remove leading and trailing
            whitespace from extracted values.
        flatten (bool, optional): Whether to flatten the results into a
            single list.

    Returns:
        list[list[str or None]] or list[str or None]:
            Extracted values grouped by document, or a flattened list
            when flatten is True.
    """
    
    results = []

    #process each group of extracted elements from an XML document
    for sublist in object_lists:

        #record a missing value when no matching elements were found
        if not sublist:
            results.append([None])
            continue

        values = []

        #process each matching element in the current document
        for obj in sublist:
            
            #record a missing value when the element is empty
            if not obj:
                values.append(None)
                continue

            target = obj

            #extract from a child element when a subelement is specified
            if subelement:
                target = obj.find(subelement)
                
                #record a missing value when the child element is absent
                if not target:
                    values.append(None)
                    continue

            #extract either an attribute value or the text of the element
            if attribute:
                val = target.get(attribute)
            else:
                val = target.get_text() if target else None

            #remove leading and trailing whitespace when requested
            if val and strip:
                val = val.strip()

            #store the extracted value, using None for empty values
            values.append(val if val else None)

        #ensure that each document has at least one returned value
        if not values:
            values.append(None)

        results.append(values)

    #flatten the document-level lists when requested
    if flatten:
        return [val for sublist in results for val in sublist]
    
    return results


def extract_values(soups, **kwargs):
    """
    Extract values from parsed TEI XML using the supplied extraction parameters.

    Args:
        soups (list[BeautifulSoup]): Parsed TEI XML documents.
        **kwargs: Parameters specifying the TEI elements, attributes, and
            extraction options to use.

    Returns:
        list:
            Extracted TEI values, grouped by XML document unless flatten is True.
    """

    #retrieve parameters used to identify the TEI elements to extract
    element = kwargs.get("element")
    attributes = kwargs.get("attributes")
    attribute_vals = kwargs.get("attribute_vals")

    #retrieve parameters used to extract values from the matched elements
    subelement = kwargs.get("subelement")
    attribute = kwargs.get("attribute")
    flatten = kwargs.get("flatten", False)

    #find the TEI elements matching the specified element and attributes
    objs = tei_extractor(
        soups,
        element=element,
        attributes=attributes,
        attribute_vals=attribute_vals
    )

    #extract text or attribute values from the matching elements
    return tei_values(
        objs,
        subelement=subelement,
        attribute=attribute,
        flatten=flatten
    )
    

def build_df(soups, schema):
    """
    Build a dataframe from parsed TEI XML using a field extraction schema.

    Args:
        soups (list[BeautifulSoup]): Parsed TEI XML documents.
        schema (dict): Schema defining the TEI elements and attributes
            to extract for each dataframe column.

    Returns:
        pandas.DataFrame:
            Dataframe containing the extracted TEI data.
    """

    data = {}
    
    #extract values for each dataframe column defined in the schema
    for col, params in schema.items():
        data[col] = extract_values(soups, **params)
    
    #convert the extracted data into a dataframe
    return pd.DataFrame(data)      

