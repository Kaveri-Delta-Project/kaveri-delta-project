from pathlib import Path


#project directories
#BASE_DIR points to the repository root
BASE_DIR = Path(__file__).resolve().parent.parent


#data and static assets used by the application
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "tei_mapping" / "static"

CSS_PATH = STATIC_DIR / "css" / "map.css"
GIS_PATH = STATIC_DIR / "gis"


#data directories for each TEI entity type
DATA_PATHS = {
    "places": DATA_DIR / "places",
    "persons": DATA_DIR / "persons",
    "works": DATA_DIR / "works",
    "inscriptions": DATA_DIR / "inscriptions"
}


#schemas defining which TEI elements and attributes are extracted
#for each entity type

PLACE_SCHEMA = {
    "place_id": dict(element="place", attribute="xml:id", flatten=True),
    "place_name": dict(element="placeName", attributes=["type"], attribute_vals=["preferred"], flatten=True),
    "alt_name": dict(element="placeName", attributes=["type"], attribute_vals=["variant"]),
    "coords": dict(element="note", attributes=["type"], attribute_vals=["coordinates"],  flatten=True),
    "type": dict(element="desc", attributes=["type"], attribute_vals=["function"]),
}

PERSON_SCHEMA = {
    "person_id": dict(element="person", attribute="xml:id", flatten=True),
    "person_name": dict(element="persName", attributes=["type"], attribute_vals=["preferred"], flatten=True),
    "alt_name": dict(element="persName", attributes=["type"], attribute_vals=["variant"]),
    "birth_date": dict(element="birth", flatten=True),
    "death_date": dict(element="death", flatten=True),
    "floruit": dict(element="floruit", flatten=True),
    "related": dict(element="trait", subelement="label"),
    "place_id": dict(element="affiliation", attribute="key"),
    "place_role": dict(element="affiliation", attribute="role"),
}

WORK_SCHEMA = {
    "work_id": dict(element="bibl", attribute="xml:id", flatten=True),
    "work_name": dict(element="title", attributes=["type"], attribute_vals=["preferred"], flatten=True),
    "alt_name": dict(element="title", attributes=["type"], attribute_vals=["variant"]),
    "person_id": dict(element="editor", attribute="key"),
    "person_role": dict(element="editor", attribute="role"),
    "genre": dict(element="note", attributes=["type"], attribute_vals=["genre"]),
    "subject": dict(element="note", attributes=["type"], attribute_vals=["subject"]),
    "place_id": dict(element="pubPlace", attribute="key"),
}

ISC_SCHEMA = {
    "inscription_id": dict(element="msDesc", attribute="xml:id", flatten=True),
    "inscription_name": dict(element="msName", attributes=["type"], attribute_vals=["preferred"], flatten=True),
    "alt_name": dict(element="msName", attributes=["type"], attribute_vals=["variant"]),
    "recipient": dict(element="orgName", attributes=["type"], attribute_vals=["recipient"]),
    "material": dict(element="material"),
    "place_id": dict(element="origPlace", attribute="key")
}
