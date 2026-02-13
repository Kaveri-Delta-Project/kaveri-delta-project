from utils import (
    add_simple_element_attr,
    insert_in_order,
    build_section,
    load_ent_name_by_key,
    valid_date,
    valid_identifier
)
from config import NSMAP, ENTITY_CONFIG

from flask import flash

MS_CONFIG = ENTITY_CONFIG["manuscript"]
CHILD_ORDER = MS_CONFIG["child_order"]
ATTR_PRIORITY = MS_CONFIG["attribute_priority"]


SECTION_HANDLERS = {}

def section_handler(name):
    def wrapper(func):
        SECTION_HANDLERS[name] = func
        return func
    return wrapper

@section_handler("preferred_ms_name")
def handle_preferred_title(manuscript, context, form_data):
    name = form_data.get("name")
    
    if not name:
        return {
            "ok": False,
            "error": "Manuscript name cannot be empty."
        }

    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)

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


@section_handler("add_ms_variant")
def handle_variant_name(manuscript, context, form_data):
    alt_name = form_data.get("alt_name")
    
    if not alt_name:
        return {
            "ok": False,
            "error": "Alternative name cannot be empty."
        }

    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)


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


@section_handler("repository")
def handle_repository(manuscript, context, form_data):
    repository = form_data.get("repository")

    if not repository:
        return {
            "ok": False,
            "error": "Repository cannot be empty."
        }

    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)

    el = add_simple_element_attr(
        parent=msIdentifier_el,
        tag="repository",
        text=repository,
        allow_multiple=False
    )
    insert_in_order(msIdentifier_el, "repository", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }

@section_handler("idno")
def handle_idno(manuscript, context, form_data):
    idno = form_data.get("idno")
    
    if not idno:
        return {
            "ok": False,
            "error": "Manuscript identifier cannot be empty."
        }

    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)

    el = add_simple_element_attr(
        parent=msIdentifier_el,
        tag="idno",
        text=idno,
        allow_multiple=False
    )
    insert_in_order(msIdentifier_el, "idno", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("works")
def handle_work(manuscript, context, form_data):
    work_key = form_data.get("work_key")
    work_text = load_ent_name_by_key("work", work_key, "title")

    if not work_key:
        flash("No work key selected.", "works-error")
        return {"ok": False}

    if not work_text:
        flash("Selected work could not be resolved.", "works-error")
        return {"ok": False}

    mscontents_el = context["root"].find(".//tei:msContents", namespaces=NSMAP)

    el = build_section(
        parent=mscontents_el,
        item_tag="msItem",
        child_tag="title",
        child_attrs={"key": work_key},        
        child_text=work_text,
    )
    insert_in_order(mscontents_el, "msItem", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("physical")
def handle_physical(manuscript, context, form_data):
    physical = form_data.get("physical")
    
    if not physical:
        return {
            "ok": False,
            "error": "Physical description cannot be empty."
        }

    msphys_el = context["root"].find(".//tei:physDesc", namespaces=NSMAP)

    el = add_simple_element_attr(
        parent=msphys_el,
        tag="p",
        text=physical,
        allow_multiple=True
    )
    insert_in_order(msphys_el, "p", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }

@section_handler("orig_date")
def handle_orig_date(manuscript, context, form_data):
    orig_date_text = form_data.get("orig_date_text")
    orig_date_from = form_data.get("orig_date_from")
    orig_date_to = form_data.get("orig_date_to")

    if not orig_date_text:
        flash("No creation period text entered.", "creation-time-error")
        return {"ok": False}

    if not orig_date_from or not orig_date_to:
        flash("Both 'From' and 'To' dates are required.", "creation-time-error")
        return {"ok": False}

    if orig_date_from and not valid_date(orig_date_from):
        flash(f"Invalid 'From' date: {orig_date_from}", "creation-time-error")
        return {"ok": False}

    if orig_date_to and not valid_date(orig_date_to):
        flash(f"Invalid 'To' date: {orig_date_to}", "creation-time-error")
        return {"ok": False}


    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)


    el = add_simple_element_attr(
        parent=msorigin_el,
        tag="origDate",
        text=orig_date_text,
        attrs={"from": orig_date_from, "to": orig_date_to},
        allow_multiple=False
    )
    insert_in_order(msorigin_el, "origDate", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }

@section_handler("orig_place")
def handle_orig_place(manuscript, context, form_data):
    orig_place_key = form_data.get("orig_place_key")
    orig_place_text = load_ent_name_by_key("place", orig_place_key, "placeName")

    if not orig_place_key:
        flash("No place key selected.", "orig-places-error")
        return {"ok": False}

    if not orig_place_text:
        flash("Selected place could not be resolved.", "orig-places-error")
        return {"ok": False}

    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    el = add_simple_element_attr(
        parent=msorigin_el,
        tag="origPlace",
        text=orig_place_text,
        attrs={"key": orig_place_key},
        allow_multiple=True
    )
    insert_in_order(msorigin_el, "origPlace", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("notes")
def handle_notes(manuscript, context, form_data):
    notes = form_data.get("notes")

    if not notes:
        return {
            "ok": False,
            "error": "Notes cannot be empty."
        }

    msadmin_el = context["root"].find(".//tei:adminInfo", namespaces=NSMAP)

    el = add_simple_element_attr(
        parent=msadmin_el,
        tag="note",
        text=notes,
        allow_multiple=True
    )
    insert_in_order(msadmin_el, "note", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("person")
def handle_person(manuscript, context, form_data):

    person_key = form_data.get("person_key")
    person_role = form_data.get("person_role")
    person_text = load_ent_name_by_key("person", person_key, "persName")

    if not person_key:
        flash("No person key selected.", "assoc-person-error")
        return {"ok": False}

    if not person_text:
        flash("Selected person could not be resolved.", "assoc-person-error")
        return {"ok": False}

    if not person_role:
        flash("Person role cannot be empty.", "assoc-person-error")
        return {"ok": False}

    mslistpers_el = context["root"].find(".//tei:listPerson", namespaces=NSMAP)

    el = build_section(
        parent=mslistpers_el,
        item_tag="person",
        attrs={"role": person_role},
        child_tag="persName",
        child_attrs={"key": person_key},
        child_text=person_text,
    )

    insert_in_order(mslistpers_el, "person", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


