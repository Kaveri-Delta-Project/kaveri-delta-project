from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "tei_mapping" / "outputs"

DATA_PATHS = {
    "places": DATA_DIR / "places",
    "persons": DATA_DIR / "persons",
    "works": DATA_DIR / "works",
}


PLACE_SCHEMA = {
    "place_id": dict(element="place", attribute="xml:id", flatten=True),
    "place_name": dict(element="placeName", attributes=["type"], attribute_vals=["preferred"], flatten=True),
    "alt_name": dict(element="placeName", attributes=["type"], attribute_vals=["variant"]),
    "coords": dict(element="note", attributes=["type"], flatten=True),
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
}

WORK_SCHEMA = {
    "work_id": dict(element="bibl", attribute="xml:id", flatten=True),
    "work_name": dict(element="title", attributes=["type"], attribute_vals=["preferred"], flatten=True),
    "alt_name": dict(element="title", attributes=["type"], attribute_vals=["variant"]),
    "work_person": dict(element="editor"),
    "genre": dict(element="note", attributes=["type"], attribute_vals=["genre"]),
    "subject": dict(element="note", attributes=["type"], attribute_vals=["subject"]),
    "place_id": dict(element="pubPlace", attribute="key"),
}