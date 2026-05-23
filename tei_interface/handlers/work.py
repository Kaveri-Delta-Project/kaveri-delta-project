from utils import (
    add_simple_element_attr,
    update_simple_element_attr,
    insert_in_order,
    build_section,
    update_build_section,
    load_ent_name_by_key,
    valid_date,
    valid_identifier,
    load_or_create_entity,
    write_entity_to_file,
    get_element_attr_by_index
    )

from index_utils import (
    update_connection_index,
    related_add,
    remove_connection_index
    )

from config import NS_TEI, NSMAP, ENTITY_CONFIG

from flask import flash

PERSON_CONFIG = ENTITY_CONFIG["person"]
PLACE_CONFIG = ENTITY_CONFIG["place"]
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
    title = form_data.get("main_title")
    edit_index = form_data.get("edit_index")
    
    if not title:
        flash("Main title cannot be empty.", "main-title-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "main-title-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=work,
            tag="title",
            text=title,
            ns=NS_TEI,
            match_attrs={"type": "preferred"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected main title.", "main-title-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=work,
            tag="title",
            nsmap=NSMAP,
            ns=NS_TEI,            
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


@section_handler("alt_title")
def handle_variant_title(work, context, form_data):
    alt_title = form_data.get("alt_title")
    edit_index = form_data.get("edit_index")

    if not alt_title:
        flash("Alternative title cannot be empty.", "alt-title-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):        
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "alt-title-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=work,
            tag="title",
            text=alt_title,
            ns=NS_TEI,
            match_attrs={"type": "variant"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected alternative title.", "alt-title-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=work,
            tag="title",
            nsmap=NSMAP,
            ns=NS_TEI,            
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
            parent=work,
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
            parent=work,
            tag="idno",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=idno,
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
    edit_index = form_data.get("edit_index")


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

    if activity == "Other" and activity_other:
        activity = activity_other
        attrs = {"type": activity, "source": "other"}
    else:
        attrs = {"type": activity}

    attrs.update({
        "from": dates_from,
        "to": dates_to
        })

    if edit_index not in (None, "", "None"):
        
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "dates-error")
            return {"ok": False}
            
        updated_el = update_simple_element_attr(
            parent=work,
            tag="date",
            text=dates_text,
            ns=NS_TEI,
            update_attrs=attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected date.", "dates-error")
            return {"ok": False}
    else:

        el = add_simple_element_attr(
            parent=work,
            tag="date",
            nsmap=NSMAP,
            ns=NS_TEI,            
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
    edit_index = form_data.get("edit_index")

    if not editor_key:
        flash("No person key selected.", "editor-error")
        return {"ok": False}

    editor_text = load_ent_name_by_key("person", PERSON_CONFIG, editor_key, "persName", NSMAP)
    if not editor_text:
        flash("Selected person could not be resolved.", "editor-error")
        return {"ok": False}

    if not editor_role:
        flash("Person role cannot be empty.", "editor-error")
        return {"ok": False}


    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "editor-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=work,
            tag="editor",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        updated_el = update_simple_element_attr(
            parent=work,
            tag="editor",
            text=editor_text,
            ns=NS_TEI,
            update_attrs={"key": editor_key, "role": editor_role},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected person.", "editor-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("person", old_key, context["xml_id"], "work")

    else:

        el = add_simple_element_attr(
            parent=work,
            tag="editor",
            nsmap=NSMAP,
            ns=NS_TEI,            
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


@section_handler("person_ref")
def handle_person_ref(work, context, form_data):
    person_ref_key = form_data.get("person_ref_key")
    person_ref_type = form_data.get("person_ref_type")
    person_ref_type_other = form_data.get("person_ref_type_other")
    edit_index = form_data.get("edit_index")

    if not person_ref_key:
        flash("No person key selected.", "person-ref-error")
        return {"ok": False}

    person_ref_text = load_ent_name_by_key("person", PERSON_CONFIG, person_ref_key, "persName", NSMAP)
    if not person_ref_text:
        flash("Selected person could not be resolved.", "person-ref-error")
        return {"ok": False}

    if not person_ref_type:
        flash("Reference type cannot be empty.", "person-ref-error")
        return {"ok": False}

    if person_ref_type == "Other" and person_ref_type_other:
        element_attrs = {
            "key": person_ref_key,
            "role": person_ref_type_other,
            "type": 'referenced'
        }

    else:
        element_attrs = {
            "key": person_ref_key,
            "role": person_ref_type,
            "type": 'referenced'
        }


    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "person-ref-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=work,
            tag="persName",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        updated_el = update_simple_element_attr(
            parent=work,
            tag="persName",
            text=person_ref_text,
            ns=NS_TEI,
            update_attrs=element_attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected person.", "person-ref-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("person", old_key, context["xml_id"], "work")

    else:

        el = add_simple_element_attr(
            parent=work,
            tag="persName",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=person_ref_text,
            attrs=element_attrs,
            allow_multiple=True
        )

        insert_in_order(work, "persName", el, CHILD_ORDER, NSMAP)

    update_connection_index("person", person_ref_key, context['xml_id'], "work", person_ref_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("work_ref")
def handle_work_ref(work, context, form_data):
    work_ref_key = form_data.get("work_ref_key")
    work_ref_type = form_data.get("work_ref_type")
    work_ref_type_other = form_data.get("work_ref_type_other")
    edit_index = form_data.get("edit_index")

    if not work_ref_key:
        flash("No work key selected.", "work-ref-error")
        return {"ok": False}

    work_ref_text = load_ent_name_by_key("work", WORK_CONFIG, work_ref_key, "title", NSMAP)
    if not work_ref_text:
        flash("Selected work could not be resolved.", "work-ref-error")
        return {"ok": False}

    if not work_ref_type:
        flash("Reference type cannot be empty.", "work-ref-error")
        return {"ok": False}

    if work_ref_type == "Other" and work_ref_type_other:
        element_attrs = {
            "key": work_ref_key,
            "role": work_ref_type_other,
        }
    else:
        element_attrs = {
            "key": work_ref_key,
            "role": work_ref_type,
        }


    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "work-ref-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=work,
            tag="rs",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        updated_el = update_simple_element_attr(
            parent=work,
            tag="rs",
            text=work_ref_text,
            ns=NS_TEI,
            update_attrs=element_attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected work.", "work-ref-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("work", old_key, context["xml_id"], "work")

    else:

        el = add_simple_element_attr(
            parent=work,
            tag="rs",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=work_ref_text,
            attrs=element_attrs,
            allow_multiple=True
        )

        insert_in_order(work, "rs", el, CHILD_ORDER, NSMAP)

    update_connection_index("work", work_ref_key, context['xml_id'], "work", work_ref_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("pub_place")
def handle_pub_place(work, context, form_data):
    pub_place_key = form_data.get("pub_place_key")
    connection = form_data.get("connection")
    connection_other = form_data.get("connection_other")
    edit_index = form_data.get("edit_index")

    if not pub_place_key:
        flash("No place key selected.", "pub-place-error")
        return {"ok": False}

    pub_place_text = load_ent_name_by_key("place", PLACE_CONFIG, pub_place_key, "placeName", NSMAP)
    if not pub_place_text:
        flash("Selected place could not be resolved.", "pub-place-error")
        return {"ok": False}

    if not connection:
        flash("Place connection cannot be empty.", "pub-place-error")
        return {"ok": False} 

    # Determine element attributes
    if connection == "Other" and connection_other:
        element_attrs = {"key": pub_place_key, "role": connection_other}
    else:
        element_attrs = {"key": pub_place_key, "role": connection}

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "pub-place-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=work,
            tag="pubPlace",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        updated_el = update_build_section(
            parent=work,
            item_tag="pubPlace",
            ns=NS_TEI,
            index=index,
            element_attrs=element_attrs,
            child_tag="placeName",
            child_text=pub_place_text,
        )        
        if updated_el is None:
            flash("Failed to update the selected place.", "pub-place-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("place", old_key, context['xml_id'], "work")
 
    else:
        # Add new element
        el = build_section(
            parent=work,
            item_tag="pubPlace",
            nsmap=NSMAP,
            ns=NS_TEI,
            attrs=element_attrs,
            child_tag="placeName",
            child_text=pub_place_text
        )
        
        insert_in_order(work, "pubPlace", el, CHILD_ORDER, NSMAP)

    # Update connection index
    update_connection_index("place", pub_place_key, context['xml_id'], "work", pub_place_text)

    return {"ok": True, "error": None}


@section_handler("genre")
def handle_genre(work, context, form_data):
    genre = form_data.get("genre")
    genre_other = form_data.get("genre_other")
    genre_commentary_key = form_data.get("genre_commentary_id")
    edit_index = form_data.get("edit_index")

    genre_commentary_text = None
    if genre_commentary_key:
        genre_commentary_text = load_ent_name_by_key("work", WORK_CONFIG, genre_commentary_key, "title", NSMAP)


    if not genre:
        flash("No genre entered.", "genre-error")
        return {"ok": False}

    if genre == "Other" and genre_other:
        text_value = genre_other
        attrs = {"type": "genre", "source": "other"}

    elif genre == "Commentary" and genre_commentary_key:
        text_value = genre_commentary_text
        attrs = {"type": "genre", "source": "commentary", "key": genre_commentary_key}

    else:
        text_value = genre
        attrs = {"type": "genre"}


    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "genre-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=work,
            tag="note",
            index=index,
            attr="key",
            ns=NS_TEI

        )

        updated_el = update_build_section(
            parent=work,
            item_tag="note",
            ns=NS_TEI,
            text=text_value,            
            match_attrs={"type": "genre"},
            element_attrs=attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected genre.", "genre-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("work", old_key, context["xml_id"], "work")
    else:

        el = build_section(
            parent=work,
            item_tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,
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

    if genre == "Commentary" and genre_commentary_key:
        update_connection_index("work", genre_commentary_key, context['xml_id'], "work", genre_commentary_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("subject")
def handle_subject(work, context, form_data):
    subject = form_data.get("subject")
    subject_other = form_data.get("subject_other")
    edit_index = form_data.get("edit_index")

    if not subject:
        flash("No subject entered.", "subject-error")
        return {"ok": False}

    if subject == "Other" and subject_other:
        text_value = subject_other
        attrs = {"type": "subject", "source": "other"}
    else:
        text_value = subject
        attrs = {"type": "subject"}

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "subject-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=work,
            tag="note",
            text=text_value,
            ns=NS_TEI,
            match_attrs={"type": "subject"},
            update_attrs=attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected subject", "subject-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=work,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
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

@section_handler("reference")
def handle_reference(work, context, form_data): 
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
            parent=work,
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
            parent=work,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=reference,
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
            parent=work,
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
            parent=work,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
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


@section_handler("record_contributor")
def handle_record_contributor(work, context, form_data):
    record_contributor = form_data.get("record_contributor")
    edit_index = form_data.get("edit_index")

    if not record_contributor:
        flash("Record contributor cannot be empty.", "record-contributor-error")
        return {"ok": False}

    worktitlestmt_el = context["root"].find(".//tei:titleStmt", namespaces=NSMAP)

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid record contributor index.", "record-contributor-error")
            return {"ok": False}

        updated_el = update_build_section(
            parent=worktitlestmt_el,
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
            parent=worktitlestmt_el,
            item_tag="respStmt",
            nsmap=NSMAP,
            ns=NS_TEI,
            child_tag="name",
            child_text=record_contributor,
        )

        insert_in_order(
            parent=worktitlestmt_el,
            tag="respStmt",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )
 

        all_contributors = context["root"].findall(".//tei:respStmt", namespaces=NSMAP)
        workresptmt_el = all_contributors[-1] if all_contributors else None

        el = add_simple_element_attr(
            parent=workresptmt_el,
            tag="resp",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text="Contributor"
        )

        insert_in_order(
            parent=workresptmt_el, 
            tag="resp", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP)

    return {
        "ok": True,
        "error": None
    }        
