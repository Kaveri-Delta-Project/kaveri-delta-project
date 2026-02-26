from utils import (
    add_simple_element_attr,
    insert_in_order,
    build_section,
    load_ent_name_by_key,
    valid_date,
    valid_identifier,
    valid_coordinates,
    load_or_create_entity,
    write_entity_to_file,
    )

from index_utils import update_connection_index, related_add
from config import NSMAP, ENTITY_CONFIG

from flask import flash

PLACE_CONFIG = ENTITY_CONFIG["place"]
CHILD_ORDER = PLACE_CONFIG["child_order"]
ATTR_PRIORITY = PLACE_CONFIG["attribute_priority"]


SECTION_HANDLERS = {}

def section_handler(name):
    def wrapper(func):
        SECTION_HANDLERS[name] = func
        return func
    return wrapper



@section_handler("main_place_name")
def handle_preferred_name(place, context, form_data):
    name = form_data.get("name")
    
    if not name:
        flash("Main name cannot be empty.", "main-name-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=place,
        tag="placeName",
        text=name,
        attrs={"type": "preferred"},
        rem_attrs={"type": "preferred"},
        allow_multiple=False
    )
    insert_in_order(
        parent=place,
        tag="placeName",
        new_elem=el,
        child_order=CHILD_ORDER,
        nsmap=NSMAP,
        sort_attr="type",
        attr_priority=ATTR_PRIORITY
    )

    return {
        "ok": True,
        "error": None
    }



@section_handler("add_variant")
def handle_variant_name(place, context, form_data):
    alt_name = form_data.get("alt_name")
    
    if not alt_name:
        flash("Alternative name cannot be empty.", "alt-names-error")
        return {"ok": False}


    el = add_simple_element_attr(
        parent=place,
        tag="placeName",
        text=alt_name,
        attrs={"type": "variant"},
        allow_multiple=True
    )
    insert_in_order(
        parent=place,
        tag="placeName",
        new_elem=el,
        child_order=CHILD_ORDER,
        nsmap=NSMAP,
        sort_attr="type",
        attr_priority=ATTR_PRIORITY
    )

    return {
        "ok": True,
        "error": None
    }


@section_handler("place_type")
def handle_place_type(place, context, form_data):
    place_type = form_data.get("place_type")

    if not place_type:
        flash("No place type entered.", "place-type-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=place,
        tag="desc",
        text=place_type,
        attrs={"type": "function"},
        allow_multiple=True
    )

    insert_in_order(place, "desc", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("idno")
def handle_idno(place, context, form_data):
    idno_type = form_data.get("idno_type")
    idno_value = form_data.get("idno_value")

    if not idno_type:
        flash("No identifier type entered.", "idno-error")
        return {"ok": False}

    if not idno_value:
        flash("No identifier value entered.", "idno-error")
        return {"ok": False}

    if idno_value and not valid_identifier(idno_value, idno_type):
        flash(f"Invalid identifier of {idno_value} entered for {idno_type}.", "idno-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=place,
        tag="idno",
        text=idno_value,
        attrs={"type": idno_type},
        allow_multiple=False
    )
    insert_in_order(place, "idno", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("coordinates")
def handle_coordinates(place, context, form_data):
    coordinates = form_data.get("coordinates")
    
    if not coordinates:
        flash("No coordinates entered.", "coordinates-error")
        return {"ok": False}

    if coordinates and not valid_coordinates(coordinates):
        flash(f"Invalid coordinate format for {coordinates}.", "coordinates-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=place,
        tag="note",
        text=coordinates,
        attrs={"type": "coordinates"},
        rem_attrs={"type": "coordinates"},
        allow_multiple=False
    )
    insert_in_order(
        parent=place, 
        tag="note", 
        new_elem=el, 
        child_order=CHILD_ORDER, 
        nsmap=NSMAP, 
        sort_attr="type", 
        attr_priority=ATTR_PRIORITY
    )

    return {
        "ok": True,
        "error": None
    }



@section_handler("notes")
def handle_notes(place, context, form_data):
    
    notes = form_data.get("notes")

    if not notes:
        flash("Notes cannot be empty.", "notes-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=place,
        tag="note",
        text=notes,
        attrs={"type": "general"},
        allow_multiple=True
    )
    
    insert_in_order(
        parent=place, 
        tag="note", 
        new_elem=el, 
        child_order=CHILD_ORDER, 
        nsmap=NSMAP, 
        sort_attr="type", 
        attr_priority=ATTR_PRIORITY)

    return {
        "ok": True,
        "error": None
    }

