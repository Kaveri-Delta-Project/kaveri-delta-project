import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
ISC_DIR = os.path.join(DATA_DIR, "inscriptions")
PERSONS_DIR = os.path.join(DATA_DIR, "persons")
WORKS_DIR = os.path.join(DATA_DIR, "works")
PLACES_DIR = os.path.join(DATA_DIR, "places")
BUILD_DIR = os.path.join(BASE_DIR, "build")

NS_TEI = "http://www.tei-c.org/ns/1.0"
NS_XML = "http://www.w3.org/XML/1998/namespace"

NSMAP = {
    "tei": NS_TEI,
    "xml": NS_XML,
}


PERSON_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"}, 
    "sex": {"attr": "sex"},
    "name": {"element": "persName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
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
    "affiliations": {"parent_tag": "affiliation", "attributes": ["from", "to", "key", "role"], "child_elements": ["placeName"]},
    "reference": {"element": "bibl", "all_results": True},
    "notes": {"element": "note", "all_results": True}
}

PLACE_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "name": {"element": "placeName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "placeName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "place_type": {"element": "desc", "filter_attr": "type", "filter_value": "function", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "coords": {"element": "note", "filter_attr": "type", "filter_value": "coordinates", "all_results": True},
    "reference": {"element": "bibl", "all_results": True},
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True}
}

WORK_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "name": {"element": "title", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "title", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "dates_text": {"element": "date", "all_results": True},
    "dates_from": {"element": "date", "element_attr": "from", "all_results": True},
    "dates_to": {"element": "date", "element_attr": "to", "all_results": True},
    "activity": {"element": "date", "element_attr": "type", "all_results": True},
    "editor_text": {"element": "editor", "all_results": True},
    "editor_key": {"element": "editor", "element_attr": "key", "all_results": True},
    "editor_role": {"element": "editor", "element_attr": "role", "all_results": True},
    "pub_place": {"parent_tag": "pubPlace", "attributes": ["key", "role"], "child_elements": ["placeName"]},
    "genre" : {
        "parent_tag": "note", 
        "filter_attr": "type", 
        "filter_value": "genre", 
        "attributes": ["type", "source", "key"],
        "extract_parent_text": True, 
        "all_results": True
        },    
    "subject": {"element": "note", "filter_attr": "type", "filter_value": "subject", "all_results": True},
    "reference": {"element": "note", "filter_attr": "type", "filter_value": "bibliographical", "all_results": True},
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True}
}

ISC_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "name":   {"element": "msName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_names": {"element": "msName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "recipient": {"element": "orgName", "filter_attr": "type", "filter_value": "recipient", "all_results": True},
    "material": {"element": "material", "all_results": True},
    "location": {"element": "origPlace", "all_results": True},
    "location_key": {"element": "origPlace", "element_attr": "key", "all_results": True},
    "reference": {"element": "note", "filter_attr": "type", "filter_value": "bibliographical", "all_results": True},
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True}
}

ROLES = {
    "ann": "Annotator",
    "arr": "Arranger",
    "att": "Attributed Author",
    "aut": "Author",
    "att": "Attributed Author",
    "csl": "Advisor/Minister",
    "com": "Compiler",
    "ctb": "Contributor",
    "edt": "Editor",
    "fmo": "Former owner",
    "ill": "Illustrator",
    "oth": "Other",
    "own": "Owner",
    "pat": "Patron",
    "pbl": "Publisher",
    "scr": "Scribe",
    "trl": "Translator",
    "wac": "Writer of added commentary",
    "wst": "Writer of supplementary textual content"
}


#entity configs

ENTITY_CONFIG = {
    "person": {
        "dir": os.path.join(DATA_DIR, "persons"),
        "mapping": PERSON_MAPPING,
        "child_order": ["person", "persName", "trait", "idno", "birth", "death", "floruit", "affiliation", "bibl", "note"],
        "attribute_priority": {"preferred": 0, "variant": 1},
        "element_tag": "person",
        "name_tag": "persName",
        "container_tag": ".//tei:listPerson",
        "prefix": "p"
    },
    "place": {
        "dir": os.path.join(DATA_DIR, "places"),
        "mapping": PLACE_MAPPING,
        "child_order": ["place", "placeName", "desc", "idno", "bibl", "note"],
        "attribute_priority": {"preferred": 0, "variant": 1, "coordinates": 0, "general": 1},
        "element_tag": "place",
        "name_tag": "placeName",
        "container_tag": ".//tei:listPlace",
        "prefix": "l"

    },
    "work": {
        "dir": os.path.join(DATA_DIR, "works"),
        "mapping": WORK_MAPPING,
        "child_order": ["title", "idno", "date" "editor", "pubPlace", "note"],
        "attribute_priority": {"preferred": 0, "variant": 1, "genre": 0, "subject": 1, "bibliographical": 2, "general": 3},
        "element_tag": "bibl",
        "name_tag": "title",
        "container_tag": ".//tei:listBibl",
        "prefix": "w"

    },
        "inscription": {
        "dir": os.path.join(DATA_DIR, "inscriptions"),
        "mapping": ISC_MAPPING,
        "child_order": ["msName", "orgName", "material", "origDate", "origPlace", "note"],
        "attribute_priority": {"preferred": 0, "variant": 1, "bibliographical": 0, "general": 1},
        "element_tag": "msDesc",
        "name_tag": "msName",
        "container_tag": ".//tei:sourceDesc",
        "prefix": "isc"
    }
}
