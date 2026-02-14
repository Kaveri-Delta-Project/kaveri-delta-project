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

PERSON_CONFIG = ENTITY_CONFIG["person"]
CHILD_ORDER = PERSON_CONFIG["child_order"]
ATTR_PRIORITY = PERSON_CONFIG["attribute_priority"]


SECTION_HANDLERS = {}

def section_handler(name):
    def wrapper(func):
        SECTION_HANDLERS[name] = func
        return func
    return wrapper



@section_handler("preferred_name")
def handle_preferred_name(person, context, form_data):
    name = form_data.get("name")
    
    if not name:
        flash("Preferred name cannot be empty.", "pref-name-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=person,
        tag="persName",
        text=name,
        attrs={"type": "preferred"},
        rem_attrs={"type": "preferred"},
        allow_multiple=False
    )
    insert_in_order(
        parent=person,
        tag="persName",
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
def handle_variant_name(person, context, form_data):
    alt_name = form_data.get("alt_name")

    if not alt_name:
        flash("Alternative name cannot be empty.", "alt-names-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=person,
        tag="persName",
        text=alt_name,
        attrs={"type": "variant"},
        allow_multiple=True
    )
    insert_in_order(
        parent=person,
        tag="persName",
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

@section_handler("related_persons")
def handle_editor(person, context, form_data):

    rel_persons_key = form_data.get("rel_persons_key")
    relationships = form_data.get("relationships")
    rel_persons_text = load_ent_name_by_key("person", rel_persons_key, "persName")

    if not rel_persons_key:
        flash("No person key selected.", "rel-persons-error")
        return {"ok": False}

    if not rel_persons_text:
        flash("Selected person could not be resolved.", "rel-persons-error")
        return {"ok": False}

    if not relationships:
        flash("Relationship cannot be empty.", "rel-persons-error")
        return {"ok": False}   

    el = build_section(
        parent=person,
        item_tag="trait",
        attrs={
            "type": relationships,
            "key": rel_persons_key,
        },
        child_tag="label",
        child_text=rel_persons_text,
    )
    
    insert_in_order(person, "trait", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("idno")
def handle_idno(person, context, form_data):
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
        parent=person,
        tag="idno",
        text=idno_value,
        attrs={"type": idno_type},
        allow_multiple=False
    )
    insert_in_order(person, "idno", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }

@section_handler("gender")
def handle_gender(person, context, form_data):
    sex = form_data.get("sex")
    if sex:
        person.set("sex", sex)
        return {"ok": True, "error": None}
    else:
        flash("No gender selected.", "gender-error")
        return {"ok": False, "error": "No gender selected."}

@section_handler("birth")
def handle_birth(person, context, form_data):
    birth_text = form_data.get("birth_text")
    birth_when = form_data.get("birth_when")

    if not birth_text:
        flash("No birth text entered.", "birth-error")
        return {"ok": False}

    if not birth_when:
        flash("No birth date in ISO format entered.", "birth-error")
        return {"ok": False}

    if birth_when and not valid_date(birth_when):
        flash(f"Invalid birth date in ISO format: {birth_when}", "birth-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=person,
        tag="birth",
        text=birth_text,
        attrs={"when": birth_when},
        allow_multiple=False
    )
    insert_in_order(person, "birth", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }

@section_handler("death")
def handle_death(person, context, form_data):
    death_text = form_data.get("death_text")
    death_when = form_data.get("death_when")

    if not death_text:
        flash("No death text entered.", "death-error")
        return {"ok": False}

    if not death_when:
        flash("No death date in ISO format entered.", "death-error")
        return {"ok": False}

    if death_when and not valid_date(death_when):
        flash(f"Invalid death date in ISO format: {death_when}", "death-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=person,
        tag="death",
        text=death_text,
        attrs={"when": death_when},
        allow_multiple=False
    )
    insert_in_order(person, "death", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("floruit")
def handle_floruit(person, context, form_data):
    floruit_text = form_data.get("floruit_text")
    floruit_from = form_data.get("floruit_from")
    floruit_to = form_data.get("floruit_to")

    if not floruit_text:
        flash("No floruit text entered.", "floruit-error")
        return {"ok": False}

    if not floruit_from or not floruit_to:
        flash("Both 'From' and 'To' dates are required.", "floruit-error")
        return {"ok": False}

    if floruit_from and not valid_date(floruit_from):
        flash(f"Invalid 'From' date: {floruit_from}", "floruit-error")
        return {"ok": False}

    if floruit_to and not valid_date(floruit_to):
        flash(f"Invalid 'To' date: {floruit_to}", "floruit-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=person,
        tag="floruit",
        text=floruit_text,
        attrs={"from": floruit_from, "to": floruit_to},
        allow_multiple=False
    )
    insert_in_order(person, "floruit", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("affiliation")
def handle_affiliation(person, context, form_data):
    key = form_data.get("affiliation_key")
    affil_text = load_ent_name_by_key("place", key, "placeName")
    
    if not key:
        flash("No affiliation key selected.", "affiliation-error")
        return {"ok": False}

    if not affil_text:
        flash("Selected affiliation could not be resolved.", "affiliation-error")
        return {"ok": False}
        

    date_from = form_data.get("affiliation_from")
    date_to = form_data.get("affiliation_to")

    if not date_to and not date_from:

        el = build_section(
            parent=person,
            item_tag="affiliation",
            attrs={"key": key,},
            child_tag="placeName",
            child_text=affil_text,
        )

    else:

        if date_to and not date_from:
            flash(f"'From' and 'To' dates must both be entered if dates included.", "affiliation-error")
            return {"ok": False}

        if date_from and not date_to:
            flash(f"'From' and 'To' dates must both be entered if dates included.", "affiliation-error")
            return {"ok": False}

        if date_from and not valid_date(date_from):
            flash(f"Invalid 'From' date: {date_from}", "affiliation-error")
            return {"ok": False}

        if date_to and not valid_date(date_to):
            flash(f"Invalid 'To' date: {date_to}", "affiliation-error")
            return {"ok": False}


        el = build_section(
            parent=person,
            item_tag="affiliation",
            attrs={
                "from": date_from,
                "to": date_to,
                "key": key,
            },
            child_tag="placeName",
            child_text=affil_text,
            )
    
    insert_in_order(person, "affiliation", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }



@section_handler("notes")
def handle_notes(person, context, form_data):
    notes = form_data.get("notes")

    if not notes:
        flash("Notes cannot be empty.", "notes-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=person,
        tag="note",
        text=notes,
        allow_multiple=True
    )

    insert_in_order(person, "note", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }
