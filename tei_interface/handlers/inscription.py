from utils import (
    add_simple_element_attr,
    insert_in_order,
    build_section,
    update_build_section,
    load_ent_name_by_key,
    valid_date,
    valid_identifier,
    load_or_create_entity,
    write_entity_to_file,
    update_simple_element_attr,
    get_element_attr_by_index
    )

from index_utils import update_connection_index, related_add, remove_connection_index
from config import NSMAP, ENTITY_CONFIG, RELATIONSHIP_INVERSES

from flask import flash


ISC_CONFIG = ENTITY_CONFIG["inscription"]
CHILD_ORDER = ISC_CONFIG["child_order"]
ATTR_PRIORITY = ISC_CONFIG["attribute_priority"]

SECTION_HANDLERS = {}

def section_handler(name):
    def wrapper(func):
        SECTION_HANDLERS[name] = func
        return func
    return wrapper

@section_handler("main_isc_name")
def handle_preferred_name(inscription, context, form_data):
    name = form_data.get("main_isc_name")
    edit_index = form_data.get("edit_index")

    if not name:
        flash("Inscription name cannot be empty.", "main-isc-name-error")
        return {"ok": False}
        
    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "main-isc-name-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=msIdentifier_el,
            tag="msName",
            text=name,
            match_attrs={"type": "preferred"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the inscription name.", "main-isc-name-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=msIdentifier_el,
            tag="msName",
            text=name,
            attrs={"type": "preferred"},
            rem_attrs={"type": "preferred"},
            allow_multiple=False
        )
        insert_in_order(
            parent=msIdentifier_el,
            tag="msName",
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


@section_handler("alt_isc_name")
def handle_variant_name(inscription, context, form_data):
    alt_name = form_data.get("alt_isc_name")
    edit_index = form_data.get("edit_index")

    if not alt_name:
        flash("Alternative name cannot be empty.", "alt-isc-name-error")
        return {"ok": False}

    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "alt-isc-name-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=msIdentifier_el,
            tag="msName",
            text=alt_name,
            match_attrs={"type": "variant"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update alternative name.", "alt-isc-name-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=msIdentifier_el,
            tag="msName",
            text=alt_name,
            attrs={"type": "variant"},
            allow_multiple=True
        )
        insert_in_order(
            parent=msIdentifier_el,
            tag="msName",
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

@section_handler("recipient")
def handle_recipient(inscription, context, form_data):
    recipient = form_data.get("recipient")
    recipient_other = form_data.get("recipient_other")
    edit_index = form_data.get("edit_index")

    if not recipient:
        flash("No recipient selected.", "recipient-error")
        return {"ok": False}

    if recipient == "Other" and recipient_other:
        text_value = recipient_other
        attrs = {"type": "recipient", "source": "other"}
    else:
        text_value = recipient
        attrs = {"type": "recipient"}

    ms_summary_el = context["root"].find(".//tei:summary", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "recipient-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=ms_summary_el,
            tag="orgName",
            text=text_value,
            match_attrs={"type": "recipient"},
            update_attrs=attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update recipient", "recipient-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=ms_summary_el,
            tag="orgName",
            text=text_value,
            attrs=attrs,
            allow_multiple=True
        )

        insert_in_order(
            parent=ms_summary_el,
            tag="orgName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )

    return {
        "ok": True,
        "error": None
    }

@section_handler("material")
def handle_material(inscription, context, form_data):
    material = form_data.get("material")
    material_other = form_data.get("material_other")
    edit_index = form_data.get("edit_index")

    if not material:
        flash("No material selected.", "material-error")
        return {"ok": False}

    if material == "Other" and material_other:
        text_value = material_other
        attrs = {"source": "other"}
    else:
        text_value = material
        attrs = None

    ms_physp_el = context["root"].find(".//tei:physDesc/tei:p", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "material-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=ms_physp_el,
            tag="material",
            text=text_value,
            update_attrs=attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update material.", "material-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=ms_physp_el,
            tag="material",
            text=text_value,
            attrs=attrs,
            allow_multiple=True
        )

        insert_in_order(
            parent=ms_physp_el,
            tag="material",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )

    return {
        "ok": True,
        "error": None
    }

@section_handler("location")
def handle_location(inscription, context, form_data):
    location_key = form_data.get("location_key")
    edit_index = form_data.get("edit_index")

    if not location_key:
        flash("No location key selected.", "location-error")
        return {"ok": False}

    location_text = load_ent_name_by_key("place", location_key, "placeName")
    if not location_text:
        flash("Selected location could not be resolved.", "location-error")
        return {"ok": False}

    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "location-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=msorigin_el,
            tag="origPlace",
            index=index,
            attr="key"
        )

        updated_el = update_simple_element_attr(
            parent=msorigin_el,
            tag="origPlace",
            text=location_text,
            update_attrs={"key": location_key},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected location.", "location-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("place", old_key, context["xml_id"], "inscription")

    else:
    
        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="origPlace",
            text=location_text,
            attrs={"key": location_key},
            allow_multiple=True
        )

        insert_in_order(
            parent=msorigin_el,
            tag="origPlace",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )

    update_connection_index("place", location_key, context['xml_id'], "inscription", location_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("reference")
def handle_reference(inscription, context, form_data): 
    reference = form_data.get("reference")
    edit_index = form_data.get("edit_index")

    if not reference:
        flash("Reference cannot be empty.", "reference-error")
        return {"ok": False}

    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "reference-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=msorigin_el,
            tag="note",
            text=reference,
            match_attrs={"type": "bibliographical"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected reference.", "reference-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="note",
            text=reference,
            attrs={"type": "bibliographical"},
            allow_multiple=True
        )

        insert_in_order(
            parent=msorigin_el, 
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

@section_handler("notes")
def handle_notes(inscription, context, form_data):
    notes = form_data.get("notes")
    edit_index = form_data.get("edit_index")

    if not notes:
        flash("Notes cannot be empty.", "notes-error")
        return {"ok": False}

    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "notes-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=msorigin_el,
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
            parent=msorigin_el,
            tag="note",
            text=notes,
            attrs={"type": "general"},
            allow_multiple=True
        )

        insert_in_order(
            parent=msorigin_el, 
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


