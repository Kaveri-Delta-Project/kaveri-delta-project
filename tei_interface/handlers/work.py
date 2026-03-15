from utils import (
    add_simple_element_attr,
    insert_in_order,
    build_section,
    load_ent_name_by_key,
    valid_date,
    valid_identifier,
    load_or_create_entity,
    write_entity_to_file,
    )

from index_utils import update_connection_index, related_add
from config import NSMAP, ENTITY_CONFIG

from flask import flash

WORK_CONFIG = ENTITY_CONFIG["work"]
CHILD_ORDER = WORK_CONFIG["child_order"]
ATTR_PRIORITY = WORK_CONFIG["attribute_priority"]


SECTION_HANDLERS = {}

def section_handler(name):
    def wrapper(func):
        SECTION_HANDLERS[name] = func
        return func
    return wrapper



@section_handler("preferred_title")
def handle_preferred_title(work, context, form_data):
    title = form_data.get("title")
    
    if not title:
        flash("Main title cannot be empty.", "main-title-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=work,
        tag="title",
        text=title,
        attrs={"type": "preferred"},
        rem_attrs={"type": "preferred"},
        allow_multiple=False
    )
    insert_in_order(
        parent=work,
        tag="title",
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


@section_handler("add_work_variant")
def handle_variant_title(work, context, form_data):
    alt_title = form_data.get("alt_title")

    if not alt_title:
        flash("Alternative title cannot be empty.", "alt-titles-error")
        return {"ok": False}


    el = add_simple_element_attr(
        parent=work,
        tag="title",
        text=alt_title,
        attrs={"type": "variant"},
        allow_multiple=True
    )
    insert_in_order(
        parent=work,
        tag="title",
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

@section_handler("idno")
def handle_idno(work, context, form_data):
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
        parent=work,
        tag="idno",
        text=idno_value,
        attrs={"type": idno_type},
        allow_multiple=False
    )
    insert_in_order(work, "idno", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("dates")
def handle_dates(work, context, form_data):
    dates_text = form_data.get("dates_text")
    dates_from = form_data.get("dates_from")
    dates_to = form_data.get("dates_to")
    activity = form_data.get("activity")
    activity_other = form_data.get("activity_other")


    if not dates_text:
        flash("No dates text entered.", "dates-error")
        return {"ok": False}

    if not activity:
        flash("No activity entered.", "dates-error")
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

    if activity == "other" and activity_other:
        activity = activity_other.lower()
        attrs = {"type": activity, "source": "other"}
    else:
        attrs = {"type": activity}

    attrs.update({
        "from": dates_from,
        "to": dates_to
        })

    el = add_simple_element_attr(
        parent=work,
        tag="date",
        text=dates_text,
        attrs=attrs,
        allow_multiple=True
    )
    
    insert_in_order(work, "date", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }



@section_handler("editor")
def handle_editor(work, context, form_data):

    editor_key = form_data.get("editor_key")
    editor_role = form_data.get("editor_role")
    editor_text = load_ent_name_by_key("person", editor_key, "persName")

    if not editor_key:
        flash("No person key selected.", "editor-error")
        return {"ok": False}

    if not editor_text:
        flash("Selected person could not be resolved.", "editor-error")
        return {"ok": False}

    if not editor_role:
        flash("Person role cannot be empty.", "editor-error")
        return {"ok": False}   

    el = add_simple_element_attr(
        parent=work,
        tag="editor",
        text=editor_text,
        attrs={"key": editor_key, "role": editor_role},
        allow_multiple=True
    )
    insert_in_order(work, "editor", el, CHILD_ORDER, NSMAP)

    update_connection_index("person", editor_key, context['xml_id'], "work", editor_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("pub_place")
def handle_pub_place(work, context, form_data):
    pub_place_key = form_data.get("pub_place_key")
    connection = form_data.get("connection")
    connection_other = form_data.get("connection_other")
    pub_place_text = load_ent_name_by_key("place", pub_place_key, "placeName")

    if not pub_place_key:
        flash("No place key selected.", "pub-places-error")
        return {"ok": False}

    if not pub_place_text:
        flash("Selected place could not be resolved.", "pub-places-error")
        return {"ok": False}

    if not connection:
        flash("Place connection cannot be empty.", "pub-places-error")
        return {"ok": False}  

    if connection == "other" and connection_other:
        attrs = {"key": pub_place_key, "role": connection_other.lower()}
    else:
        attrs = {"key": pub_place_key, "role": connection}

    el = build_section(
        parent=work,
        item_tag="pubPlace",
        attrs=attrs,
        child_tag="placeName",
        child_text=pub_place_text
        )
    
    insert_in_order(work, "pubPlace", el, CHILD_ORDER, NSMAP)

    update_connection_index("place", pub_place_key, context['xml_id'], "work", pub_place_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("genre")
def handle_genre(work, context, form_data):
    genre = form_data.get("genre")
    genre_other = form_data.get("genre_other")
    genre_commentary_key = form_data.get("genre_commentary_id")
    genre_commentary_text = load_ent_name_by_key("work", genre_commentary_key, "title")


    if not genre:
        flash("No genre entered.", "genre-error")
        return {"ok": False}

    if genre == "other" and genre_other:
        text_value = genre_other.lower()
        attrs = {"type": "genre", "source": "other"}

    elif genre == "commentary" and genre_commentary_key:
        text_value = genre_commentary_text
        attrs = {"type": "genre", "source": "commentary", "key": genre_commentary_key}

    else:
        text_value = genre.lower()
        attrs = {"type": "genre"}

    el = build_section(
        parent=work,
        item_tag="note",
        text=text_value,
        attrs=attrs,
        allow_multiple=True
    )

    insert_in_order(
        parent=work, 
        tag="note", 
        new_elem=el, 
        child_order=CHILD_ORDER, 
        nsmap=NSMAP, 
        sort_attr="type", 
        attr_priority=ATTR_PRIORITY
    )

    if genre == "commentary" and genre_commentary_key:
        update_connection_index("work", genre_commentary_key, context['xml_id'], "work", genre_commentary_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("subject")
def handle_genre(work, context, form_data):
    subject = form_data.get("subject")
    subject_other = form_data.get("subject_other")

    if not subject:
        flash("No subject entered.", "subject-error")
        return {"ok": False}

    if subject == "other" and subject_other:
        text_value = subject_other.lower()
        attrs = {"type": "subject", "source": "other"}
    else:
        text_value = subject
        attrs = {"type": "subject"}

    el = add_simple_element_attr(
        parent=work,
        tag="note",
        text=text_value,
        attrs=attrs,
        allow_multiple=True
    )

    insert_in_order(
        parent=work, 
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

@section_handler("references")
def handle_references(work, context, form_data):
    references = form_data.get("references")

    if not references:
        flash("References cannot be empty.", "references-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=work,
        tag="note",
        text=references,
        attrs={"type": "bibliographical"},
        allow_multiple=True
    )

    insert_in_order(
        parent=work, 
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
def handle_notes(work, context, form_data):
    
    notes = form_data.get("notes")

    if not notes:
        flash("Notes cannot be empty.", "notes-error")
        return {"ok": False}

    el = add_simple_element_attr(
        parent=work,
        tag="note",
        text=notes,
        attrs={"type": "general"},
        allow_multiple=True
    )

    insert_in_order(
        parent=work, 
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


