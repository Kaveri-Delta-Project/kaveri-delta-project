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
    name = form_data.get("preferred_name")
    edit_index = form_data.get("edit_index")
    
    if not name:
        flash("Preferred name cannot be empty.", "preferred-name-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "preferred-name-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=person,
            tag="persName",
            text=name,
            match_attrs={"type": "preferred"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the preferred name.", "preferred-name-error")
            return {"ok": False}

    else:

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


@section_handler("alt_name")
def handle_variant_name(person, context, form_data):
    alt_name = form_data.get("alt_name")
    edit_index = form_data.get("edit_index")

    if not alt_name:
        flash("Alternative name cannot be empty.", "alt-name-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):
        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "alt-name-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=person,
            tag="persName",
            text=alt_name,
            match_attrs={"type": "variant"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected alternative name.", "alt-name-error")
            return {"ok": False}

    else:

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
    date_from = form_data.get("rel_persons_from")
    date_to = form_data.get("rel_persons_to")

    if not rel_persons_key:
        flash("No person key selected.", "rel-persons-error")
        return {"ok": False}

    rel_persons_text = load_ent_name_by_key("person", rel_persons_key, "persName")

    if not rel_persons_text:
        flash("Selected person could not be resolved.", "rel-persons-error")
        return {"ok": False}

    if not relationships:
        flash("Relationship cannot be empty.", "rel-persons-error")
        return {"ok": False}

    if bool(date_from) != bool(date_to):
        flash("'From' and 'To' dates must both be entered if dates included.", "rel-persons-error")
        return {"ok": False}

    if date_from and not valid_date(date_from):
        flash(f"Invalid 'From' date: {date_from}", "rel-persons-error")
        return {"ok": False}

    if date_to and not valid_date(date_to):
        flash(f"Invalid 'To' date: {date_to}", "rel-persons-error")
        return {"ok": False}


    element_attrs = {
        "type": relationships,
        "key": rel_persons_key,
    }

    if date_from and date_to:
        element_attrs.update({
            "from": date_from,
            "to": date_to
    })

    el = build_section(
        parent=person,
        item_tag="trait",
        attrs=element_attrs,
        child_tag="label",
        child_text=rel_persons_text,
    )
    
    insert_in_order(person, "trait", el, CHILD_ORDER, NSMAP)

    update_connection_index("person", rel_persons_key, context['xml_id'], "person", rel_persons_text)

    reverse_type = RELATIONSHIP_INVERSES.get(relationships)
    if reverse_type:
        person_a_key = context["xml_id"]
        person_a_text = load_ent_name_by_key("person", person_a_key, "persName")

        if not person_a_key or not person_a_text:
            flash("Record needs to be saved with name to create relationship.", "rel-persons-error")
            return {"ok": False}


        related_build = related_add(
            relationship=relationships,
            key=rel_persons_key,       
            person_a_key=person_a_key, 
            person_a_text=person_a_text,
            person_a_from=date_from,
            person_a_to=date_to,
            reverse_type=reverse_type,
            config=ENTITY_CONFIG["person"]
        )

        if not related_build.get("ok"):
            return related_build

        update_connection_index("person", person_a_key, rel_persons_key, "person", person_a_text)

    return {
        "ok": True,
        "error": None
    }


@section_handler("idno")
def handle_idno(person, context, form_data):
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
            parent=person,
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
            parent=person,
            tag="idno",
            text=idno,
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
    edit_index = form_data.get("edit_index")

    if not birth_text:
        flash("No birth text entered.", "birth-error")
        return {"ok": False}

    if not birth_when:
        flash("No birth date in ISO format entered.", "birth-error")
        return {"ok": False}

    if birth_when and not valid_date(birth_when):
        flash(f"Invalid birth date in ISO format: {birth_when}", "birth-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "birth-error")
            return {"ok": False}
        
        updated_el = update_simple_element_attr(
            parent=person,
            tag="birth",
            text=birth_text,
            update_attrs={"when": birth_when},
            index=index
        )

        if updated_el is None:
            flash("Failed to update birth.", "birth-error")
            return {"ok": False}

    else:

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
    edit_index = form_data.get("edit_index")


    if not death_text:
        flash("No death text entered.", "death-error")
        return {"ok": False}

    if not death_when:
        flash("No death date in ISO format entered.", "death-error")
        return {"ok": False}

    if death_when and not valid_date(death_when):
        flash(f"Invalid death date in ISO format: {death_when}", "death-error")
        return {"ok": False}

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "death-error")
            return {"ok": False}
        
        updated_el = update_simple_element_attr(
            parent=person,
            tag="death",
            text=death_text,
            update_attrs={"when": death_when},
            index=index
        )

        if updated_el is None:
            flash("Failed to update death.", "death-error")
            return {"ok": False}

    else:

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
    edit_index = form_data.get("edit_index")


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

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "floruit-error")
            return {"ok": False}

        updated_el = update_simple_element_attr(
            parent=person,
            tag="floruit",
            text=floruit_text,
            update_attrs={"from": floruit_from, "to": floruit_to},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected date.", "floruit-error")
            return {"ok": False}

    else:

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


@section_handler("associated_place")
def handle_associated_place(person, context, form_data):
    place_key = form_data.get("associated_place_key")
    association = form_data.get("association")
    association_other = form_data.get("association_other")
    date_from = form_data.get("associated_place_from")
    date_to = form_data.get("associated_place_to")
    edit_index = form_data.get("edit_index")

    
    if not place_key:
        flash("No associated place key selected.", "associated-place-error")
        return {"ok": False}

    place_text = load_ent_name_by_key("place", place_key, "placeName")
    if not place_text:
        flash("Selected associated place could not be resolved.", "associated-place-error")
        return {"ok": False}

    if not association:
        flash("Association type cannot be empty.", "associated-place-error")
        return {"ok": False}         

    if bool(date_from) != bool(date_to):
        flash("'From' and 'To' dates must both be entered if dates included.", "associated-place-error")
        return {"ok": False}

    if date_from and not valid_date(date_from):
        flash(f"Invalid 'From' date: {date_from}", "associated-place-error")
        return {"ok": False}

    if date_to and not valid_date(date_to):
        flash(f"Invalid 'To' date: {date_to}", "associated-place-error")
        return {"ok": False}

    if association == "other" and association_other:
        element_attrs = {"key": place_key, "role": association_other.lower()}
    else:
        element_attrs = {"key": place_key, "role": association}

    if date_from and date_to:
        element_attrs.update({
            "from": date_from,
            "to": date_to
        })

    if edit_index not in (None, "", "None"):

        try:
            index = int(edit_index)
        except ValueError:
            flash("Invalid edit index.", "associated-place-error")
            return {"ok": False}

        old_key = get_element_attr_by_index(
            parent=person,
            tag="affiliation",
            index=index,
            attr="key"
        )

        updated_el = update_build_section(
            parent=person,
            item_tag="affiliation",
            index=index,
            element_attrs=element_attrs,
            child_tag="placeName",
            child_text=place_text,
        )

        if updated_el is None:
            flash("Failed to update the selected place.", "associated-place-error")
            return {"ok": False}

        if old_key:
            remove_connection_index("place", old_key, context['xml_id'], "person")

    else:

        el = build_section(
            parent=person,
            item_tag="affiliation",
            attrs=element_attrs,
            child_tag="placeName",
            child_text=place_text,
            )
        
        insert_in_order(person, "affiliation", el, CHILD_ORDER, NSMAP)

    update_connection_index("place", place_key, context['xml_id'], "person", place_text)

    return {
        "ok": True,
        "error": None,
    }

@section_handler("reference")
def handle_reference(person, context, form_data):
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
            parent=person,
            tag="bibl",
            text=reference,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected reference.", "reference-error")
            return {"ok": False}

    else:

        el = add_simple_element_attr(
            parent=person,
            tag="bibl",
            text=reference,
            allow_multiple=True
        )

        insert_in_order(person, "bibl", el, CHILD_ORDER, NSMAP)

    return {
        "ok": True,
        "error": None
    }


@section_handler("notes")
def handle_notes(person, context, form_data):
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
            parent=person,
            tag="note",
            text=notes,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected notes.", "notes-error")
            return {"ok": False}

    else:

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
