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
from config import NS_TEI, NSMAP, ENTITY_CONFIG

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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,
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

    if place_type == "Other" and place_type_other:
        text_value = place_type_other
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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
            ns=NS_TEI,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected reference.", "reference-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=place,
            tag="bibl",
            nsmap=NSMAP,
            ns=NS_TEI,
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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

@section_handler("record_contributor")
def handle_record_contributor(place, context, form_data):
    record_contributor = form_data.get("record_contributor")
    edit_index = form_data.get("edit_index")

    if not record_contributor:
        flash("Record contributor cannot be empty.", "record-contributor-error")
        return {"ok": False}

    placetitlestmt_el = context["root"].find(".//tei:titleStmt", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid record contributor index.", "record-contributor-error")
            return {"ok": False}

        updated_el = update_build_section(
            parent=placetitlestmt_el,
            item_tag="respStmt",
            ns=NS_TEI,
            index=index,           
            child_tag="name",
            child_text=record_contributor,
        )

        if updated_el is None:
            flash("Failed to update the selected record contributor.", "record-contributor-error")
            return {"ok": False}

    else:

        el = build_section(
            parent=placetitlestmt_el,
            item_tag="respStmt",
            nsmap=NSMAP,
            ns=NS_TEI,
            child_tag="name",
            child_text=record_contributor,
        )

        insert_in_order(
            parent=placetitlestmt_el,
            tag="respStmt",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )
 

        all_contributors = context["root"].findall(".//tei:respStmt", namespaces=NSMAP)
        placeresptmt_el = all_contributors[-1] if all_contributors else None

        el = add_simple_element_attr(
            parent=placeresptmt_el,
            tag="resp",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text="Contributor"
        )

        insert_in_order(
            parent=placeresptmt_el, 
            tag="resp", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP)

    return {
        "ok": True,
        "error": None
    }


