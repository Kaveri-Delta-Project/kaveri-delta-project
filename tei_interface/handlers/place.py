from utils import (
    add_simple_element_attr,
    insert_in_order,
    build_section,
    update_build_section,
    load_ent_name_by_key,
    valid_date,
    valid_identifier,
    valid_coordinates,
    load_or_create_entity,
    write_entity_to_file,
    update_simple_element_attr,
    get_element_attr_by_index
    )

from index_utils import update_connection_index, related_add, remove_connection_index
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
    name = form_data.get("main_place_name")
    edit_index = form_data.get("edit_index")
    
    if not name:
        flash("Main place name cannot be empty.", "main-place-name-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "main-place-name-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=place,
            tag="placeName",
            text=name,
            match_attrs={"type": "preferred"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the main place name.", "main-place-name-error")
            return {"ok": False}

    else:

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


@section_handler("alt_place_name")
def handle_variant_name(place, context, form_data):
    alt_place_name = form_data.get("alt_place_name")
    edit_index = form_data.get("edit_index")

    if not alt_place_name:
        flash("Alternative place name cannot be empty.", "alt-place-name-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "alt-place-name-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=place,
            tag="placeName",
            text=alt_place_name,
            match_attrs={"type": "variant"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected alternative place name.", "alt-place-name-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=place,
            tag="placeName",
            text=alt_place_name,
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
    place_type_other = form_data.get("place_type_other")
    edit_index = form_data.get("edit_index")


    if not place_type:
        flash("No place type entered.", "place-type-error")
        return {"ok": False}

    if place_type == "other" and place_type_other:
        text_value = place_type_other.lower()
        attrs = {"type": "function", "source": "other"}
    else:
        text_value = place_type
        attrs = {"type": "function"}

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "place-type-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=place,
            tag="desc",
            text=text_value,
            match_attrs={"type": "function"},
            update_attrs=attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected place type", "place-type-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=place,
            tag="desc",
            text=text_value,
            attrs=attrs,
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
    idno = form_data.get("idno")
    edit_index = form_data.get("edit_index")

    if not idno_type:
        flash("No identifier type entered.", "idno-error")
        return {"ok": False}

    if not idno:
        flash("No identifier value entered.", "idno-error")
        return {"ok": False}

    if idno and not valid_identifier(idno, idno_type):
        flash(f"Invalid identifier of {idno} entered for {idno_type}.", "idno-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "idno-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=place,
            tag="idno",
            text=idno,
            update_attrs={"type": idno_type},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected identifier.", "idno-error")
            return {"ok": False}

    else:        

        el = add_simple_element_attr(
            parent=place,
            tag="idno",
            text=idno,
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
    edit_index = form_data.get("edit_index")

    if not coordinates:
        flash("No coordinates entered.", "coordinates-error")
        return {"ok": False}

    if coordinates and not valid_coordinates(coordinates):
        flash(f"Invalid coordinate format for {coordinates}.", "coordinates-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "coordinates-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=place,
            tag="note",
            text=coordinates,
            match_attrs={"type": "coordinates"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected coordinates.", "coordinates-error")
            return {"ok": False}

    else:       

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

@section_handler("reference")
def handle_reference(place, context, form_data):
    reference = form_data.get("reference")
    edit_index = form_data.get("edit_index")

    if not reference:
        flash("Reference cannot be empty.", "reference-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "reference-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=place,
            tag="bibl",
            text=reference,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected reference.", "reference-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=place,
            tag="bibl",
            text=reference,
            allow_multiple=True
        )

        insert_in_order(place, "bibl", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("notes")
def handle_notes(place, context, form_data):    
    notes = form_data.get("notes")
    edit_index = form_data.get("edit_index")

    if not notes:
        flash("Notes cannot be empty.", "notes-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "notes-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=place,
            tag="note",
            text=notes,
            match_attrs={"type": "general"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected notes.", "notes-error")
            return {"ok": False}

    else:   

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

