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
from config import NS_TEI, NSMAP, ENTITY_CONFIG, RELATIONSHIP_INVERSES

from flask import flash


ISC_CONFIG = ENTITY_CONFIG["inscription"]
PLACE_CONFIG = ENTITY_CONFIG["place"]
PERSON_CONFIG = ENTITY_CONFIG["person"]
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,
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


@section_handler("dates")
def handle_dates(inscription, context, form_data):
    dates_text = form_data.get("dates_text")
    dates_from = form_data.get("dates_from")
    dates_to = form_data.get("dates_to")
    edit_index = form_data.get("edit_index")

    if not dates_text:
        flash("No dates text entered.", "dates-error")
        return {"ok": False}

    if not dates_from or not dates_to:
        flash("Both 'From' and 'To' dates are required.", "dates-error")
        return {"ok": False}

    if dates_from and not valid_date(dates_from):
        flash(f"Invalid 'From' date: {dates_from}", "dates-error")
        return {"ok": False}

    if dates_to and not valid_date(dates_to):
        flash(f"Invalid 'To' date: {dates_to}", "dates-error")
        return {"ok": False}

    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "dates-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=msorigin_el,
            tag="origDate",
            text=dates_text,
            ns=NS_TEI,
            update_attrs={"from": dates_from, "to": dates_to},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected date.", "dates-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="origDate",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=dates_text,
            attrs={"from": dates_from, "to": dates_to},
            allow_multiple=True
        )        
        
        insert_in_order(
            parent=msorigin_el,
            tag="origDate",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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


@section_handler("donor")
def handle_donor(inscription, context, form_data):
    donor_key = form_data.get("donor_key")
    edit_index = form_data.get("edit_index")

    if not donor_key:
        flash("No donor key selected.", "donor-error")
        return {"ok": False}

    donor_text = load_ent_name_by_key("person", PERSON_CONFIG, donor_key, "persName", NSMAP)
    if not donor_text:
        flash("Selected person could not be resolved.", "donor-error")
        return {"ok": False}

    ms_list_person_el = context["root"].find(".//tei:listPerson", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "donor-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=ms_list_person_el,
            tag="person",
            index=index,
            attr="key",
            match_attrs={"ana": "donor"},
            ns=NS_TEI,
            from_child=True
        )

        updated_el = update_build_section(
            parent=ms_list_person_el,
            item_tag="person",
            ns=NS_TEI,
            index=index,
            match_attrs={"ana": "donor"},
            element_attrs={"ana": "donor"},             
            child_tag="persName",
            child_text=donor_text,
            child_attrs={"key": donor_key, "role": "dnr"}
        )

        if updated_el is None:
            flash("Failed to update the selected donor.", "donor-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("person", old_key, context['xml_id'], "inscription")

    else:

        # Add new element
        el = build_section(
            parent=ms_list_person_el,
            item_tag="person",
            nsmap=NSMAP,
            ns=NS_TEI,
            attrs={"ana": "donor"}, 
            child_tag="persName",
            child_text=donor_text,
            child_attrs={"key": donor_key, "role": "dnr"}
        )
        
        insert_in_order(
            parent=ms_list_person_el,
            tag="person",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="ana",
            attr_priority=ATTR_PRIORITY
        )

    #update connection index
    update_connection_index("person", donor_key, context['xml_id'], "inscription", donor_text)

    return {"ok": True, "error": None}


@section_handler("assoc_person")
def handle_associated_person(inscription, context, form_data):
    assoc_person_key = form_data.get("assoc_person_key")
    assoc_person_role = form_data.get("assoc_person_role")
    edit_index = form_data.get("edit_index")

    if not assoc_person_key:
        flash("No associated person key selected.", "assoc-person-error")
        return {"ok": False}

    assoc_person_text = load_ent_name_by_key("person", PERSON_CONFIG, assoc_person_key, "persName", NSMAP)
    if not assoc_person_text:
        flash("Selected person could not be resolved.", "assoc-person-error")
        return {"ok": False}

    if not assoc_person_role:
        flash("Person role cannot be empty.", "assoc-person-error")
        return {"ok": False}

    ms_list_person_el = context["root"].find(".//tei:listPerson", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):        
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "assoc-person-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=ms_list_person_el,
            tag="person",
            index=index,
            attr="key",
            match_attrs={"ana": "associated"},
            ns=NS_TEI,
            from_child=True
        )

        updated_el = update_build_section(
            parent=ms_list_person_el,
            item_tag="person",
            ns=NS_TEI,
            index=index,
            match_attrs={"ana": "associated"},
            element_attrs={"ana": "associated"},            
            child_tag="persName",
            child_text=assoc_person_text,
            child_attrs={"key": assoc_person_key, "role": assoc_person_role}
        )

        if updated_el is None:
            flash("Failed to update the selected associated person.", "assoc-person-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("person", old_key, context['xml_id'], "inscription")

    else:

        # Add new element
        el = build_section(
            parent=ms_list_person_el,
            item_tag="person",
            nsmap=NSMAP,
            ns=NS_TEI,
            attrs={"ana": "associated"}, 
            child_tag="persName",
            child_text=assoc_person_text,
            child_attrs={"key": assoc_person_key, "role": assoc_person_role}
        )
        
        insert_in_order(
            parent=ms_list_person_el,
            tag="person",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            attr_priority=ATTR_PRIORITY
        )

    #update connection index
    update_connection_index("person", assoc_person_key, context['xml_id'], "inscription", assoc_person_text)

    return {"ok": True, "error": None}



@section_handler("language")
def handle_language(inscription, context, form_data): 
    language = form_data.get("language")
    edit_index = form_data.get("edit_index")

    if not language:
        flash("Language cannot be empty.", "language-error")
        return {"ok": False}

    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "language-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=msorigin_el,
            tag="lang",
            text=language,
            ns=NS_TEI,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected inscription language.", "language-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="lang",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=language,
            allow_multiple=True
        )

        insert_in_order(
            parent=msorigin_el, 
            tag="lang", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP 
        )

    return {
        "ok": True,
        "error": None
    }    


@section_handler("donation_type")
def handle_donation_type(inscription, context, form_data): 
    donation_type = form_data.get("donation_type")
    edit_index = form_data.get("edit_index")

    if not donation_type:
        flash("Donation type cannot be empty.", "donation-type-error")
        return {"ok": False}

    mshistory_el = context["root"].find(".//tei:history", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "donation-type-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=mshistory_el,
            tag="provenance",
            text=donation_type,
            ns=NS_TEI,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected donation type.", "donation-type-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=mshistory_el,
            tag="provenance",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=donation_type,
            allow_multiple=True
        )

        insert_in_order(
            parent=mshistory_el, 
            tag="provenance", 
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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

    location_text = load_ent_name_by_key("place", PLACE_CONFIG, location_key, "placeName", NSMAP)
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
            attr="key",
            ns=NS_TEI
        )

        updated_el = update_simple_element_attr(
            parent=msorigin_el,
            tag="origPlace",
            text=location_text,
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,
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
            ns=NS_TEI,
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
            nsmap=NSMAP,
            ns=NS_TEI,            
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


