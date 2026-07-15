import os
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
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

TEXT_ELEMS = ["title", "persName", "placeName", "label", "editor"]

KEYS_TO_LOWERCASE = ["rel_persons_key", "affiliation_key", "editor_key", 
                    "pub_place_key", "work_key", "orig_place_key", "person_key", "person_ref_key", "work_ref_key"]

#filename api

API_URL = "https://filename-service.onrender.com"

#xml structure mappings

PERSON_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"}, 
    "sex": {"attr": "sex"},
    "preferred_name": {"element": "persName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_name": {"element": "persName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "relationship": {"parent_tag": "trait", "attributes": ["type", "key", "from", "to"], "child_elements": ["label"]},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "birth_text": {"element": "birth", "all_results": True},
    "birth_when": {"element": "birth", "element_attr": "when", "all_results": True},
    "death_text": {"element": "death", "all_results": True},
    "death_when": {"element": "death", "element_attr": "when", "all_results": True},
    "floruit_text": {"element": "floruit", "all_results": True},
    "floruit_from": {"element": "floruit", "element_attr": "from", "all_results": True},
    "floruit_to": {"element": "floruit", "element_attr": "to", "all_results": True},
    "associated_place": {"parent_tag": "affiliation", "attributes": ["from", "to", "key", "role"], "child_elements": ["placeName"]},
    "reference" : {
        "parent_tag": "bibl",  
        "attributes": ["subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        }, 
    "notes": {"element": "note", "all_results": True},
    "record_contributor": {"parent_tag": "respStmt", "child_elements": ["name", "resp"], "from_root": True}
}

RELATIONSHIP_INVERSES = {
    "associate": "associate",
    "ancestor": "descendant",
    "beneficiary": "patron",
    "brother": "brother",
    "collaborator": "collaborator",
    "contemporary of": "contemporary of",
    "descendant": "ancestor",
    "disciple": "mentor",
    "father": "son",
    "grandfather": "grandson",
    "grandson": "grandfather",
    "member of family": "member of family",
    "mentor": "disciple",
    "other": "other",
    "patron": "beneficiary",
    "rival": "rival",
    "son": "father",
    "teacher": "student",
    "student": "teacher",
}

PLACE_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "main_name": {"element": "placeName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_name": {"element": "placeName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "place_type": {"element": "desc", "filter_attr": "type", "filter_value": "function", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "coordinates": {"element": "note", "filter_attr": "type", "filter_value": "coordinates", "all_results": True},
    "reference" : {
        "parent_tag": "bibl",  
        "attributes": ["subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        },
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True},
}

WORK_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "title": {"element": "title", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_title": {"element": "title", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "idno_value": {"element": "idno", "all_results": True},
    "idno_type": {"element": "idno", "element_attr": "type", "all_results": True},
    "dates_text": {"element": "date", "all_results": True},
    "dates_from": {"element": "date", "element_attr": "from", "all_results": True},
    "dates_to": {"element": "date", "element_attr": "to", "all_results": True},
    "activity": {"element": "date", "element_attr": "type", "all_results": True},
    "editor_text": {"element": "editor", "all_results": True},
    "editor_key": {"element": "editor", "element_attr": "key", "all_results": True},
    "editor_role": {"element": "editor", "element_attr": "role", "all_results": True},
    "person_ref": {"parent_tag": "persName", "attributes": ["key", "role"], "child_elements": ["note"], "extract_parent_text": True},
    "work_ref": {"parent_tag": "rs", "attributes": ["key", "role"], "child_elements": ["note"], "extract_parent_text": True},
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
    "reference" : {
        "parent_tag": "note", 
        "filter_attr": "type", 
        "filter_value": "bibliographical", 
        "attributes": ["type", "subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        }, 
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True},
    "record_contributor": {"parent_tag": "respStmt", "child_elements": ["name", "resp"], "from_root": True}
}

ISC_MAPPING = {
    "xml_id": {"attr": f"{{{NS_XML}}}id"},
    "name":   {"element": "msName", "filter_attr": "type", "filter_value": "preferred", "all_results": True},
    "alt_name": {"element": "msName", "filter_attr": "type", "filter_value": "variant", "all_results": True},
    "dates_text": {"element": "origDate", "all_results": True},
    "dates_from": {"element": "origDate", "element_attr": "from", "all_results": True},
    "dates_to": {"element": "origDate", "element_attr": "to", "all_results": True},
    "donor": {
        "parent_tag": "person",
        "filter_attr": "ana", 
        "filter_value": "donor",
        "child_elements": ["persName"], 
        "child_attributes": {"persName": ["key", "role"]}, 
        "from_root": True
        },
    "assoc_person": {
        "parent_tag": "person",
        "filter_attr": "ana", 
        "filter_value": "associated",
        "child_elements": ["persName"], 
        "child_attributes": {"persName": ["key", "role"]}, 
        "from_root": True
        },
    "recipient": {"element": "orgName", "filter_attr": "type", "filter_value": "recipient", "all_results": True},
    "language": {"element": "lang", "all_results": True},    
    "donation_type": {"element": "provenance", "all_results": True},
    "material": {"element": "material", "all_results": True},
    "location": {"element": "origPlace", "all_results": True},
    "location_key": {"element": "origPlace", "element_attr": "key", "all_results": True},
    "reference" : {
        "parent_tag": "note", 
        "filter_attr": "type", 
        "filter_value": "bibliographical", 
        "attributes": ["type", "subtype", "n"],
        "extract_parent_text": True, 
        "all_results": True
        },
    "notes": {"element": "note", "filter_attr": "type", "filter_value": "general", "all_results": True},
    "record_contributor": {"parent_tag": "respStmt", "child_elements": ["name", "resp"], "from_root": True}
}

#entity configs

ENTITY_CONFIG = {
    "person": {
        "dir": os.path.join(DATA_DIR, "persons"),
        "title_ent": "people",
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_person.xml"),
        "mapping": PERSON_MAPPING,
        "child_order": ["person", "persName", "trait", "idno", "birth", "death", "floruit", "affiliation", "bibl", "note", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1},
        "element_tag": "person",
        "name_tag": "persName",
        "container_tag": ".//tei:listPerson",
        "prefix": "p"
    },
    "place": {
        "dir": os.path.join(DATA_DIR, "places"),
        "title_ent": "place",
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_place.xml"),
        "mapping": PLACE_MAPPING,
        "child_order": ["place", "placeName", "desc", "idno", "bibl", "note", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1, "coordinates": 0, "general": 1},
        "element_tag": "place",
        "name_tag": "placeName",
        "container_tag": ".//tei:listPlace",
        "prefix": "l"

    },
    "work": {
        "dir": os.path.join(DATA_DIR, "works"),
        "title_ent": "work",
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_work.xml"),
        "mapping": WORK_MAPPING,
        "child_order": ["title", "idno", "date", "editor", "persName", "rs", "pubPlace", "note", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1, "genre": 0, "subject": 1, "bibliographical": 2, "general": 3},
        "element_tag": "bibl",
        "name_tag": "title",
        "container_tag": ".//tei:listBibl",
        "prefix": "w"
    },
    "inscription": {
        "dir": os.path.join(DATA_DIR, "inscriptions"),
        "title_ent": "inscription",
        "template": os.path.join(TEI_TEMPLATES_DIR, "tei_inscription.xml"),
        "mapping": ISC_MAPPING,
        "child_order": ["msName", "orgName", "material", "origDate", "origPlace", "note", "lang", "origin", "provenance", "person", "name", "resp"],
        "attribute_priority": {"preferred": 0, "variant": 1, "bibliographical": 0, "general": 1, "donor": 0, "associated": 1},
        "element_tag": "msDesc",
        "name_tag": "msName",
        "container_tag": ".//tei:sourceDesc",
        "prefix": "isc"
    }
}

#template configs

TEMPLATE_CONFIG = {
    "bibliographical_references": [
        ("", "-- Select Reference --"),
        ("Duquette, Jonathan. Debates in the Delta: An Intellectual History of Late Advaita. Brill, forthcoming.", "Debates in the Delta: An Intellectual History of Late Advaita"),
        ("Raghavan, Venkataraman. Śāhendravilāsa of Śrīdhara Veṅkaṭeśa (A Poem on the Life of King Śāhaji of Tanjore, 1684-1710). Tiruchi: The Kalyan Press, 1952.", "Śāhendravilāsa of Śrīdhara Veṅkaṭeśa"),
        ("Sastri, T. S. Kuppuswami Sastri. ‘Ramabhadra-Dikshita and the Southern Poets of his Time.’ Indian Antiquary, Vol. XXXIII, pp. 126-142 and pp. 176-196, 2004.", "Ramabhadra-Dikshita and the Southern Poets of his Time"),
        ("Thiruvengadathan, A. Rāmabhadra Dīkṣita and His Works: A Study. Chennai: The Kuppuswami Sastri Research Institute, 2002.", "Rāmabhadra Dīkṣita and His Works: A Study"),
        ("New Catalogus Catalogurum (NCC). Vols 1-36.", "New Catalogus Catalogurum (NCC)"),
        ("A Descriptive Catalogue of the Sanskrit Manuscripts in the Sarasvati Mahal Library, Tanjore (Tanjore). Vols. 1–19.", "A Descriptive Catalogue of the Sanskrit Manuscripts in the Sarasvati Mahal Library"),
        ("Descriptive Catalogue of the Sanskrit Manuscripts in the Government Oriental Manuscripts Library, Madras (GOML). Vols. 1–25.", "Descriptive Catalogue of the Sanskrit Manuscripts in the Government Oriental Manuscripts Library, Madras (GOML)"),
        ("Lists of Sanskrit Manuscripts in Private Libraries of Southern India (Oppert). Vols 1–2", "Lists of Sanskrit Manuscripts in Private Libraries of Southern India"),
        ("Descriptive Catalogue of Sanskrit Manuscripts in the Adyar Library (Adyar). Vols. 1–13.", "Descriptive Catalogue of Sanskrit Manuscripts in the Adyar Library (Adyar)"),
    ],
}

