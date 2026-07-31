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

from index_utils import (
    update_connection_index,
    related_add,
    remove_connection_index
    )

from handler_utils import (
    get_edit_index,
    success,
    failure
    )

from config import NS_TEI, NSMAP, ENTITY_CONFIG, RELATIONSHIP_INVERSES

from flask import flash

# Handlers for processing form submissions and updating TEI XML entities.
#
# All handlers follow the signature:
#
#     handler(entity, context, form_data)
#
# entity:
#     The XML element being modified (e.g. work, person, or place).
#
# context:
#     Dictionary containing request-level information such as XML root
#     and entity identifiers.
#
# form_data:
#     Submitted form values used to create or update TEI elements.
#
# Handlers return:
#     {"ok": True, "error": None} on success
#     {"ok": False} on failure


#load entity-specific configuration values used by handlers
PLACE_CONFIG = ENTITY_CONFIG["place"]
PERSON_CONFIG = ENTITY_CONFIG["person"]
CHILD_ORDER = PERSON_CONFIG["child_order"]
ATTR_PRIORITY = PERSON_CONFIG["attribute_priority"]

#registry used to dynamically dispatch submitted form sections
SECTION_HANDLERS = {}

def section_handler(name):
    """
    Register a function as a handler for a specific form section.

    The decorator stores the decorated function in the SECTION_HANDLERS
    registry using the supplied section name as the lookup key. This allows
    form sections to be dynamically mapped to their corresponding handler
    functions.

    Args:
        name (str):
            The name of the form section handled by the function.

    Returns:
        function:
            A decorator that registers the handler function and returns it
            unchanged.
    """

    def wrapper(func):
        SECTION_HANDLERS[name] = func
        return func
    return wrapper


@section_handler("preferred_name")
def handle_preferred_name(person, context, form_data):
    """
    Add or update the preferred name for a person.

    Validates the submitted name and determines whether the request is
    an edit or a new addition. Creates a preferred name entry and ensures
    that only one preferred name exists for the person.
    """

    name = form_data.get("preferred_name")
    
    if not name:
        flash("Preferred name cannot be empty.", "preferred-name-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "preferred-name-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected preferred person name
        updated_el = update_simple_element_attr(
            parent=person,
            tag="persName",
            text=name,
            ns=NS_TEI,
            match_attrs={"type": "preferred"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the preferred name.", "preferred-name-error")
            return failure()

    else:

        #add a new preferred person name, replacing any existing preferred name
        el = add_simple_element_attr(
            parent=person,
            tag="persName",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=name,
            attrs={"type": "preferred"},
            rem_attrs={"type": "preferred"},
            allow_multiple=False
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=person,
            tag="persName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("alt_name")
def handle_variant_name(person, context, form_data):
    """
    Add or update a variant name for a person.

    Validates the submitted name and determines whether the request is
    an edit or a new addition. Creates a variant name entry and allows
    multiple variant names to exist for the person.
    """

    alt_name = form_data.get("alt_name")

    if not alt_name:
        flash("Alternative name cannot be empty.", "alt-name-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "alt-name-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected variant person name
        updated_el = update_simple_element_attr(
            parent=person,
            tag="persName",
            text=alt_name,
            ns=NS_TEI,
            match_attrs={"type": "variant"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected alternative name.", "alt-name-error")
            return failure()

    else:

        #add a new variant person name
        el = add_simple_element_attr(
            parent=person,
            tag="persName",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=alt_name,
            attrs={"type": "variant"},
            allow_multiple=True
        )
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=person,
            tag="persName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("related_persons")
def handle_editor(person, context, form_data):
    """
    Add a relationship between two people.

    Validates the selected related person, relationship type, and optional
    date range. Creates a relationship entry for the current person,
    updates the person connection index, and, where a reverse relationship
    is defined, automatically creates the reciprocal relationship in the
    related person's record. Maintains the connection index for both
    directions of the relationship. Allows multiple relationships to exist
    for the person.
    """

    rel_persons_key = form_data.get("rel_persons_key")
    relationships = form_data.get("relationships")
    date_from = form_data.get("rel_persons_from")
    date_to = form_data.get("rel_persons_to")

    #validate the selected related person
    if not rel_persons_key:
        flash("No person key selected.", "rel-persons-error")
        return failure()

    #resolve the related person's display name from the entity file
    rel_persons_text = load_ent_name_by_key("person", PERSON_CONFIG, rel_persons_key, "persName", NSMAP)
    if not rel_persons_text:
        flash("Selected person could not be resolved.", "rel-persons-error")
        return failure()

    #validate the relationship type
    if not relationships:
        flash("Relationship cannot be empty.", "rel-persons-error")
        return failure()

    #validate the optional relationship date range
    if bool(date_from) != bool(date_to):
        flash("'From' and 'To' dates must both be entered if dates included.", "rel-persons-error")
        return failure()

    if date_from and not valid_date(date_from):
        flash(f"Invalid 'From' date: {date_from}", "rel-persons-error")
        return failure()

    if date_to and not valid_date(date_to):
        flash(f"Invalid 'To' date: {date_to}", "rel-persons-error")
        return failure()

    #build the relationship attributes
    element_attrs = {
        "type": relationships,
        "key": rel_persons_key,
    }

    #add the optional relationship date range
    if date_from and date_to:
        element_attrs.update({
            "from": date_from,
            "to": date_to
    })

    #add the relationship and attributes to the current person's record
    el = build_section(
        parent=person,
        item_tag="trait",
        nsmap=NSMAP,
        ns=NS_TEI,
        attrs=element_attrs,
        child_tag="label",
        child_text=rel_persons_text,
    )
    
    #maintain the TEI child element ordering
    insert_in_order(person, "trait", el, CHILD_ORDER, NSMAP)

    #update the connection index for this relationship
    update_connection_index("person", rel_persons_key, context['xml_id'], "person", rel_persons_text)

    #create the reciprocal relationship
    reverse_type = RELATIONSHIP_INVERSES.get(relationships)
    if reverse_type:
        person_a_key = context["xml_id"]
        #resolve the current person's display name
        person_a_text = load_ent_name_by_key("person", PERSON_CONFIG, person_a_key, "persName", NSMAP)

        #ensure the current record can be resolved before creating the reverse relationship
        if not person_a_key or not person_a_text:
            flash("Record needs to be saved with name to create relationship.", "rel-persons-error")
            return failure()

        #add the relationship and attributes to the related person's record
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

        #return if the reciprocal relationship could not be created
        if not related_build.get("ok"):
            return related_build

        #update the reverse connection index
        update_connection_index("person", person_a_key, rel_persons_key, "person", person_a_text)

    return success()


@section_handler("idno")
def handle_idno(person, context, form_data):
    """
    Add or update an identifier for a person.

    Validates the identifier type and value, checks that the identifier
    format is valid, and determines whether the request is an edit or a
    new addition. Ensures that only one identifier exists for the person.
    """

    idno_type = form_data.get("idno_type")
    idno = form_data.get("idno")

    #validate the identifier type
    if not idno_type:
        flash("No identifier type entered.", "idno-error")
        return failure()

    #validate the identifier value
    if not idno:
        flash("No identifier value entered.", "idno-error")
        return failure()

    #validate the identifier value format
    if idno and not valid_identifier(idno, idno_type):
        flash(f"Invalid identifier of {idno} entered for {idno_type}.", "idno-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "idno-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected identifier value and type
        updated_el = update_simple_element_attr(
            parent=person,
            tag="idno",
            text=idno,
            ns=NS_TEI,
            update_attrs={"type": idno_type},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected identifier.", "idno-error")
            return failure()

    else:

        #add an identifier value and type, replacing any existing identifier
        el = add_simple_element_attr(
            parent=person,
            tag="idno",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=idno,
            attrs={"type": idno_type},
            allow_multiple=False
        )
        
        #maintain the TEI child element ordering
        insert_in_order(person, "idno", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("gender")
def handle_gender(person, context, form_data):
    """
    Add or update the person's gender.

    Validates the selected gender and stores it as the TEI "sex"
    attribute on the person element.
    """

    sex = form_data.get("sex")
    
    #validate the selected gender
    if sex:
        #store the gender as the person's sex attribute
        person.set("sex", sex)
        return success()
    else:
        flash("No gender selected.", "gender-error")
        return failure()


@section_handler("birth")
def handle_birth(person, context, form_data):
    """
    Add or update the person's birth information.

    Validates the birth description and ISO date, then determines
    whether the request is an edit or a new addition. Creates 
    a birth element. Only a single birth entry can exist
    for the person.
    """

    birth_text = form_data.get("birth_text")
    birth_when = form_data.get("birth_when")

    #validate the birth description
    if not birth_text:
        flash("No birth text entered.", "birth-error")
        return failure()

    #validate the birth date
    if not birth_when:
        flash("No birth date in ISO format entered.", "birth-error")
        return failure()
    
    if birth_when and not valid_date(birth_when):
        flash(f"Invalid birth date in ISO format: {birth_when}", "birth-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited        
    index = get_edit_index(form_data, "birth-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected birth entry and attribute
        updated_el = update_simple_element_attr(
            parent=person,
            tag="birth",
            text=birth_text,
            ns=NS_TEI,
            update_attrs={"when": birth_when},
            index=index
        )

        if updated_el is None:
            flash("Failed to update birth.", "birth-error")
            return failure()

    else:

        #add a new birth entry and attribute
        el = add_simple_element_attr(
            parent=person,
            tag="birth",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=birth_text,
            attrs={"when": birth_when},
            allow_multiple=False
        )
    
        #maintain the TEI child element ordering
        insert_in_order(person, "birth", el, CHILD_ORDER, NSMAP)

    return success()
    

@section_handler("death")
def handle_death(person, context, form_data):
    """
    Add or update the person's death information.

    Validates the death description and ISO date, then determines
    whether the request is an edit or a new addition. Creates
    a death element. Only a single death entry can exist
    for the person.
    """

    death_text = form_data.get("death_text")
    death_when = form_data.get("death_when")

    #validate the death description
    if not death_text:
        flash("No death text entered.", "death-error")
        return failure()

    #validate the death date
    if not death_when:
        flash("No death date in ISO format entered.", "death-error")
        return failure()

    if death_when and not valid_date(death_when):
        flash(f"Invalid death date in ISO format: {death_when}", "death-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "death-error")
    if index is False:
        return failure()

    if index is not None:
        
        #update the selected death entry and attributes
        updated_el = update_simple_element_attr(
            parent=person,
            tag="death",
            text=death_text,
            ns=NS_TEI,
            update_attrs={"when": death_when},
            index=index
        )

        if updated_el is None:
            flash("Failed to update death.", "death-error")
            return failure()

    else:

        #add a new death entry and attributes
        el = add_simple_element_attr(
            parent=person,
            tag="death",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=death_text,
            attrs={"when": death_when},
            allow_multiple=False
        )
        
        #maintain the TEI child element ordering
        insert_in_order(person, "death", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("floruit")
def handle_floruit(person, context, form_data):
    """
    Add or update the person's floruit period.

    Validates the floruit description and date range, then determines
    whether the request is an edit or a new addition. Creates
    a floruit element. Only a single floruit entry can exist for
    the person.
    """

    floruit_text = form_data.get("floruit_text")
    floruit_from = form_data.get("floruit_from")
    floruit_to = form_data.get("floruit_to")

    #validate the floruit description
    if not floruit_text:
        flash("No floruit text entered.", "floruit-error")
        return failure()

    #validate that both dates are provided
    if not floruit_from or not floruit_to:
        flash("Both 'From' and 'To' dates are required.", "floruit-error")
        return failure()

    #validate the floruit date range
    if floruit_from and not valid_date(floruit_from):
        flash(f"Invalid 'From' date: {floruit_from}", "floruit-error")
        return failure()

    if floruit_to and not valid_date(floruit_to):
        flash(f"Invalid 'To' date: {floruit_to}", "floruit-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "floruit-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected floruit entry and attributes
        updated_el = update_simple_element_attr(
            parent=person,
            tag="floruit",
            text=floruit_text,
            ns=NS_TEI,
            update_attrs={"from": floruit_from, "to": floruit_to},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected date.", "floruit-error")
            return failure()

    else:

        #add a new floruit entry and attributes
        el = add_simple_element_attr(
            parent=person,
            tag="floruit",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=floruit_text,
            attrs={"from": floruit_from, "to": floruit_to},
            allow_multiple=False
        )
        
        #maintain the TEI child element ordering
        insert_in_order(person, "floruit", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("associated_place")
def handle_associated_place(person, context, form_data):
    """
    Add or update an associated place for a person.

    Validates the selected place, association type, and optional date
    range, determines whether the request is an edit or a new addition. 
    Creates an affiliation entry, maintains the place
    connection index, and removes outdated connections when an existing
    association is changed. Allows multiple associated places.
    """

    place_key = form_data.get("associated_place_key")
    association = form_data.get("association")
    association_other = form_data.get("association_other")
    date_from = form_data.get("associated_place_from")
    date_to = form_data.get("associated_place_to")
    
    #validate the selected place
    if not place_key:
        flash("No associated place key selected.", "associated-place-error")
        return failure()

    #resolve the place display name from the entity file
    place_text = load_ent_name_by_key("place", PLACE_CONFIG, place_key, "placeName", NSMAP)
    if not place_text:
        flash("Selected associated place could not be resolved.", "associated-place-error")
        return failure()

    #validate the association type
    if not association:
        flash("Association type cannot be empty.", "associated-place-error")
        return failure()         

    #validate the optional association date range
    if bool(date_from) != bool(date_to):
        flash("'From' and 'To' dates must both be entered if dates included.", "associated-place-error")
        return failure()

    if date_from and not valid_date(date_from):
        flash(f"Invalid 'From' date: {date_from}", "associated-place-error")
        return failure()

    if date_to and not valid_date(date_to):
        flash(f"Invalid 'To' date: {date_to}", "associated-place-error")
        return failure()

    #build the affiliation attributes
    #use custom association type if "Other" is selected
    if association == "Other" and association_other:
        element_attrs = {"key": place_key, "role": association_other}
    else:
        element_attrs = {"key": place_key, "role": association}

    #add the optional association date range
    if date_from and date_to:
        element_attrs.update({
            "from": date_from,
            "to": date_to
        })

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "associated-place-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the old place key before updating
        old_key = get_element_attr_by_index(
            parent=person,
            tag="affiliation",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        #update the selected affiliation and attributes
        updated_el = update_build_section(
            parent=person,
            item_tag="affiliation",
            ns=NS_TEI,
            index=index,
            element_attrs=element_attrs,
            child_tag="placeName",
            child_text=place_text,
        )

        if updated_el is None:
            flash("Failed to update the selected place.", "associated-place-error")
            return failure()

        #remove the previous place connection if the place changed
        if old_key:
            remove_connection_index("place", old_key, context['xml_id'], "person")

    else:

        #add a new affiliation entry and attributes
        el = build_section(
            parent=person,
            item_tag="affiliation",
            nsmap=NSMAP,
            ns=NS_TEI,
            attrs=element_attrs,
            child_tag="placeName",
            child_text=place_text,
            )
        
        #maintain the TEI child element ordering
        insert_in_order(person, "affiliation", el, CHILD_ORDER, NSMAP)

    #update the place connection index
    update_connection_index("place", place_key, context['xml_id'], "person", place_text)

    return success()
    

@section_handler("reference")
def handle_reference(person, context, form_data):
    """
    Add or update a bibliographical reference for a person.

    Validates the reference entry, handles custom references, and includes
    optional volume and page information as attributes. Determines whether
    the request is an edit or a new addition, and creates a bibliographical
    reference entry. Allows multiple references to exist for the person.
    """

    reference = form_data.get("reference")
    reference_other = form_data.get("reference_other")
    ref_vol = form_data.get("volume")
    ref_page = form_data.get("page")

    #validate the reference value
    if not reference:
        flash("Reference cannot be empty.", "reference-error")
        return failure()

    #build the reference text and attributes
    #handle custom references
    if reference == "Other" and reference_other:
        text_value = reference_other
        element_attrs = {"source": "other"}
    else:
        text_value = reference
        element_attrs = {}

    #add optional volume and page attributes
    if ref_vol:
        element_attrs.update({"subtype": ref_vol})

    if ref_page:
        element_attrs.update({"n": ref_page})

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "reference-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected reference and attributes
        updated_el = update_simple_element_attr(
            parent=person,
            tag="bibl",
            text=text_value,
            ns=NS_TEI,
            update_attrs=element_attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected reference.", "reference-error")
            return failure()

    else:

        #add a new reference and attributes
        el = add_simple_element_attr(
            parent=person,
            tag="bibl",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=text_value,
            attrs=element_attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(person, "bibl", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("notes")
def handle_notes(person, context, form_data):
    """
    Add or update general notes for a person.

    Validates the note text and determines whether the request is
    an edit or a new addition. Creates a general note entry and allows
    multiple notes to exist for the person.
    """

    notes = form_data.get("notes")

    #validate the note text
    if not notes:
        flash("Notes cannot be empty.", "notes-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "notes-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected general note text
        updated_el = update_simple_element_attr(
            parent=person,
            tag="note",
            text=notes,
            ns=NS_TEI,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected notes.", "notes-error")
            return failure()

    else:

        #add a new general note
        el = add_simple_element_attr(
            parent=person,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=notes,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(person, "note", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("record_contributor")
def handle_record_contributor(person, context, form_data):
    """
    Add or update a record contributor for a person.

    Validates the contributor name and determines whether the request is
    an edit or a new addition. Creates a responsibility statement entry
    containing the contributor name and adds the corresponding contributor
    role. Allows multiple contributors to exist for the person.
    """

    record_contributor = form_data.get("record_contributor")

    #validate the contributor name
    if not record_contributor:
        flash("Record contributor cannot be empty.", "record-contributor-error")
        return failure()

    #retrieve the title statement element from the TEI document
    perstitlestmt_el = context["root"].find(".//tei:titleStmt", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "record-contributor-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected record contributor name
        updated_el = update_build_section(
            parent=perstitlestmt_el,
            item_tag="respStmt",
            ns=NS_TEI,
            index=index,           
            child_tag="name",
            child_text=record_contributor,
        )

        if updated_el is None:
            flash("Failed to update the selected record contributor.", "record-contributor-error")
            return failure()

    else:

        #add a new responsibility statement containing the contributor name
        el = build_section(
            parent=perstitlestmt_el,
            item_tag="respStmt",
            nsmap=NSMAP,
            ns=NS_TEI,
            child_tag="name",
            child_text=record_contributor,
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=perstitlestmt_el,
            tag="respStmt",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )
 
        #retrieve the newly created responsibility statement
        all_contributors = context["root"].findall(".//tei:respStmt", namespaces=NSMAP)
        persresptmt_el = all_contributors[-1] if all_contributors else None

        #add the contributor responsibility type
        el = add_simple_element_attr(
            parent=persresptmt_el,
            tag="resp",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text="Contributor"
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=persresptmt_el, 
            tag="resp", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP)

    return success()
