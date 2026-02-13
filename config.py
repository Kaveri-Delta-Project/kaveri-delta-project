import os
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_DIR = os.path.join(BASE_DIR, "index")
TEI_TEMPLATES_DIR = os.path.join(BASE_DIR, "tei_templates")


#namespace settings

NS_TEI = "http://www.tei-c.org/ns/1.0"
NS_XML = "http://www.w3.org/XML/1998/namespace"

NSMAP = {
    "tei": NS_TEI,
    "xml": NS_XML,
}

DEFAULT_NSMAP = {None: NS_TEI}


#xml structure mappings

PERSON_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"}, 
    "sex": {"attr": "sex"},
    "names": {"element": "persName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "persName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "relationship": {"parent_tag": "trait", "attributes": ["type", "key"], "child_elements": ["label"]},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "birth_text": {"element": "birth", "all_results": True},
    "birth_when": {"element": "birth", "element_attr": "when", "all_results": True},
    "death_text": {"element": "death", "all_results": True},
    "death_when": {"element": "death", "element_attr": "when", "all_results": True},
    "floruit_text": {"element": "floruit", "all_results": True},
    "floruit_from": {"element": "floruit", "element_attr": "from", "all_results": True},
    "floruit_to": {"element": "floruit", "element_attr": "to", "all_results": True},
    "affiliations": {"parent_tag": "affiliation", "attributes": ["from", "to", "key"], "child_elements": ["placeName"]},
    "notes": {"element": "note", "all_results": True}
}

PLACE_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "names": {"element": "placeName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "placeName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "place_type": {"element": "desc", "filter_attr": "type", "filter_value": "function", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "coords": {"element": "note", "filter_attr": "type", "filter_value": "coordinates", "all_results": True},
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True}
}

WORK_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "title": {"element": "title", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_title": {"element": "title", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "editor_text": {"element": "editor", "all_results": True},
    "editor_key": {"element": "editor", "element_attr": "key", "all_results": True},
    "editor_role": {"element": "editor", "element_attr": "role", "all_results": True},
    "pub_place": {"parent_tag": "pubPlace", "attributes": ["key"], "child_elements": ["placeName"]},
    "genre": {"element": "note", "filter_attr": "type", "filter_value": "genre", "all_results": True},
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True}
}

MS_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "repository": {"element": "repository", "all_results": True},
    "idno": {"element": "idno", "all_results": True},
    "names": {"element": "msName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "msName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "work": {"parent_tag": "msItem", "child_elements": ["title"], "child_attributes": {"title": ["key"]}},
    "phys_desc": {"element": "p", "all_results": True},
    "date_text": {"element": "origDate", "all_results": True},
    "date_from": {"element": "origDate", "element_attr": "from", "all_results": True},
    "date_to": {"element": "origDate", "element_attr": "to", "all_results": True},
    "place": {"element": "origPlace", "all_results": True},
    "place_key": {"element": "origPlace", "element_attr": "key", "all_results": True},
    "notes": {"element": "note", "all_results": True},
    "person": {"parent_tag": "person", "attributes": ["role"], "child_elements": ["persName"], "child_attributes": {"persName": ["key"]}, "from_root": True}
}


#entity configs

ENTITY_CONFIG = {
    "person": {
        "dir": os.path.join(DATA_DIR, "persons"),
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_person.xml"),
        "mapping": PERSON_MAPPING,
        "child_order": ["person", "persName", "trait", "idno", "birth", "death", "floruit", "affiliation", "note"],
        "attribute_priority": {"preferred": 0, "variant": 1},
        "element_tag": "person",
        "name_tag": "persName",
        "container_tag": ".//tei:listPerson",
        "prefix": "p"
    },
    "place": {
        "dir": os.path.join(DATA_DIR, "places"),
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_place.xml"),
        "mapping": PLACE_MAPPING,
        "child_order": ["place", "placeName", "desc", "idno", "note"],
        "attribute_priority": {"preferred": 0, "variant": 1, "coordinates": 0, "general": 1},
        "element_tag": "place",
        "name_tag": "placeName",
        "container_tag": ".//tei:listPlace",
        "prefix": "l"

    },
    "work": {
        "dir": os.path.join(DATA_DIR, "works"),
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_work.xml"),
        "mapping": WORK_MAPPING,
        "child_order": ["title", "idno", "editor", "pubPlace", "note"],
        "attribute_priority": {"preferred": 0, "variant": 1, "genre": 0, "general": 1},
        "element_tag": "bibl",
        "name_tag": "title",
        "container_tag": ".//tei:listBibl",
        "prefix": "w"

    },
    "manuscript": {
        "dir": os.path.join(DATA_DIR, "manuscripts"),
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_manuscript.xml"),
        "mapping": MS_MAPPING,
        "child_order": ["repository", "idno", "msName", "msItem", "p", "origDate", "origPlace", "note", "person"],
        "attribute_priority": {"preferred": 0, "variant": 1},
        "element_tag": "msDesc",
        "name_tag": "msName",
        "container_tag": ".//tei:sourceDesc",
        "prefix": "ms"

    }
}
