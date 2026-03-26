import glob
import os
from pathlib import Path
from natsort import natsorted
from natsort import os_sorted

import pandas as pd
import string
import re
from bs4 import BeautifulSoup
from datetime import datetime
from itertools import product


def get_xml_files(path):
    files = [f for f in Path(path).iterdir() if f.is_file() and f.suffix.lower() == ".xml"]
    return os_sorted(files)

def soup_objects(file_paths):
    soups = []
    for path in file_paths:
        with path.open("r", encoding="utf-8") as xml:
            soups.append(BeautifulSoup(xml, "lxml-xml"))
    return soups

def tei_extractor(soup_ls, element, attributes=None, attribute_vals=None):
    attrib_dict = {}

    if attributes:
        if attribute_vals:
            if len(attributes) != len(attribute_vals):
                raise ValueError("attributes and attribute_vals must match")
            attrib_dict = dict(zip(attributes, attribute_vals))
        else:
            attrib_dict = {attr: True for attr in attributes}

    return [soup.find_all(element, attrib_dict) for soup in soup_ls]


def tei_values(object_lists, subelement=None, attribute=None, strip=True, flatten=False):
    
    results = []

    for sublist in object_lists:
        if not sublist:
            results.append([None])
            continue

        values = []
        for obj in sublist:
            if not obj:
                values.append(None)
                continue

            target = obj
            if subelement:
                target = obj.find(subelement)
                if not target:
                    values.append(None)
                    continue

            if attribute:
                val = target.get(attribute)
            else:
                val = target.get_text() if target else None

            if val and strip:
                val = val.strip()

            values.append(val if val else None)

        # Ensure at least one value per parent element
        if not values:
            values.append(None)

        results.append(values)

    if flatten:
        return [val for sublist in results for val in sublist]
    else:
        return results

def extract_values(soups, **kwargs):
    # Arguments for tei_extractor
    element = kwargs.get("element")
    attributes = kwargs.get("attributes")
    attribute_vals = kwargs.get("attribute_vals")

    # Arguments for tei_values
    subelement = kwargs.get("subelement")
    attribute = kwargs.get("attribute")
    flatten = kwargs.get("flatten", False)

    objs = tei_extractor(
        soups,
        element=element,
        attributes=attributes,
        attribute_vals=attribute_vals
    )

    return tei_values(
        objs,
        subelement=subelement,
        attribute=attribute,
        flatten=flatten
    )
    

def build_df(soups, schema):
    data = {}
    for col, params in schema.items():
        data[col] = extract_values(soups, **params)
    return pd.DataFrame(data)      

