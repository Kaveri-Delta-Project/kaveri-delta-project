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
    get_element_attr_by_index,
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

from config import NS_TEI, NSMAP, ENTITY_CONFIG

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
PERSON_CONFIG = ENTITY_CONFIG["person"]
PLACE_CONFIG = ENTITY_CONFIG["place"]
WORK_CONFIG = ENTITY_CONFIG["work"]
CHILD_ORDER = WORK_CONFIG["child_order"]
ATTR_PRIORITY = WORK_CONFIG["attribute_priority"]


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


@section_handler("preferred_title")
def handle_preferred_title(work, context, form_data):
    """
    Add or update the preferred title for a work.

    Validates the submitted title, determines whether the request is an
    edit or a new addition, and ensures that only one preferred title
    exists for the work.
    """

    title = form_data.get("main_title")
    
    if not title:
        flash("Main title cannot be empty.", "main-title-error")
        return failure()
    
    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "main-title-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected preferred title
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
            return failure()

    else:

        #add a new preferred title, replacing any existing preferred title
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
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=work,
            tag="title",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("alt_title")
def handle_variant_title(work, context, form_data):
    """
    Add or update a variant title for a work.

    Validates the submitted title and determines whether the request is an
    edit or a new addition. Allows multiple variant titles to exist for the
    work.
    """

    alt_title = form_data.get("alt_title")

    if not alt_title:
        flash("Alternative title cannot be empty.", "alt-title-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "alt-title-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected variant title
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
            return failure()

    else:

        #add a new variant title
        el = add_simple_element_attr(
            parent=work,
            tag="title",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=alt_title,
            attrs={"type": "variant"},
            allow_multiple=True
        )
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=work,
            tag="title",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("idno")
def handle_idno(work, context, form_data):
    """
    Add or update an identifier for a work.

    Validates the identifier type and value, checks that the identifier
    format is valid, and determines whether the request is an edit or a
    new addition. Ensures that only one identifier exists for the work.
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
            parent=work,
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
            parent=work,
            tag="idno",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=idno,
            attrs={"type": idno_type},
            allow_multiple=False
        )
        
        #maintain the TEI child element ordering
        insert_in_order(work, "idno", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("dates")
def handle_dates(work, context, form_data):
    """
    Add or update a date entry for a work.

    Validates the date information and activity type, handles custom activity
    values, and determines whether the request is an edit or a new addition.
    Stores the date range and activity information as attributes on the TEI
    date element. Allows multiple dates to exist for the work.
    """

    dates_text = form_data.get("dates_text")
    dates_from = form_data.get("dates_from")
    dates_to = form_data.get("dates_to")
    activity = form_data.get("activity")
    activity_other = form_data.get("activity_other")

    #validate the date description
    if not dates_text:
        flash("No dates text entered.", "dates-error")
        return failure()

    #validate the activity type
    if not activity:
        flash("No activity entered.", "dates-error")
        return failure()

    #validate that both start and end dates are provided
    if not dates_from or not dates_to:
        flash("Both 'From' and 'To' dates are required.", "dates-error")
        return failure()

    #validate the date formats
    if dates_from and not valid_date(dates_from):
        flash(f"Invalid 'From' date: {dates_from}", "dates-error")
        return failure()

    if dates_to and not valid_date(dates_to):
        flash(f"Invalid 'To' date: {dates_to}", "dates-error")
        return failure()

    #create the TEI attributes for the date element
    #use custom activity value if "Other" is selected
    if activity == "Other" and activity_other:
        activity = activity_other
        attrs = {"type": activity, "source": "other"}
    else:
        attrs = {"type": activity}

    #add ISO dates as attributes
    attrs.update({
        "from": dates_from,
        "to": dates_to
        })

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "dates-error")
    if index is False:
        return failure()

    if index is not None:
            
        #update the selected date entry and attributes        
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
            return failure()
    else:

        #add a new date entry and attributes
        el = add_simple_element_attr(
            parent=work,
            tag="date",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=dates_text,
            attrs=attrs,
            allow_multiple=True
        )
        
        #maintain the TEI child element ordering
        insert_in_order(work, "date", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("editor")
def handle_editor(work, context, form_data):
    """
    Add or update a person associated with a work.

    Validates the selected person and role, resolves the person's display
    name from person files, and determines whether the request is an edit or a new addition.
    Maintains the connection index when a person relationship is changed.
    Allows multiple connected persons to exist for the work.
    """
    
    editor_key = form_data.get("editor_key")
    editor_role = form_data.get("editor_role")

    #validate the selected person key
    if not editor_key:
        flash("No person key selected.", "editor-error")
        return failure()

    #resolve the person's display name from the person's entity file
    editor_text = load_ent_name_by_key("person", PERSON_CONFIG, editor_key, "persName", NSMAP)
    if not editor_text:
        flash("Selected person could not be resolved.", "editor-error")
        return failure()

    #validate the person role
    if not editor_role:
        flash("Person role cannot be empty.", "editor-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "editor-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing person key before updating
        old_key = get_element_attr_by_index(
            parent=work,
            tag="editor",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        #update the selected person and attributes
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
            return failure()

        #remove the old connection if the person has changed
        if old_key:
            remove_connection_index("person", old_key, context["xml_id"], "work")

    else:

        #add a new person and attributes
        el = add_simple_element_attr(
            parent=work,
            tag="editor",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=editor_text,
            attrs={"key": editor_key, "role": editor_role},
            allow_multiple=True
        )
        
        #maintain the TEI child element ordering
        insert_in_order(work, "editor", el, CHILD_ORDER, NSMAP)

    #update the connection index for this person and work relationship
    update_connection_index("person", editor_key, context['xml_id'], "work", editor_text)

    return success()


@section_handler("person_ref")
def handle_person_ref(work, context, form_data):
    """
    Add or update a referenced person associated with a work.

    Validates the selected person, resolves the person's display name from
    the entity file, and determines whether the request is an edit or a new
    addition. Creates a referenced person entry with an optional note and
    maintains the connection index when the relationship is changed.
    Allows multiple referenced persons to exist for the work.
    """    

    person_ref_key = form_data.get("person_ref_key")
    person_ref_note = form_data.get("person_ref_note")

    #validate the selected person key
    if not person_ref_key:
        flash("No person key selected.", "person-ref-error")
        return failure()

    #resolve the person's display name from the person's entity file
    person_ref_text = load_ent_name_by_key("person", PERSON_CONFIG, person_ref_key, "persName", NSMAP)
    if not person_ref_text:
        flash("Selected person could not be resolved.", "person-ref-error")
        return failure()

    #build the attributes for the referenced person
    element_attrs = {
        "key": person_ref_key,
        "role": "mention",
        "type": 'referenced'
    }

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "person-ref-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing person key before updating
        old_key = get_element_attr_by_index(
            parent=work,
            tag="persName",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        #update the selected referenced person and note
        updated_el = update_build_section(
            parent=work,
            item_tag="persName",
            ns=NS_TEI,
            text=person_ref_text,
            index=index,
            element_attrs=element_attrs,
            child_tag="note",
            child_text=person_ref_note
        )

        if updated_el is None:
            flash("Failed to update the selected person.", "person-ref-error")
            return failure()

        #remove the old connection if the referenced person has changed
        if old_key:
            remove_connection_index("person", old_key, context["xml_id"], "work")

    else:

        #add a new referenced person and optional note
        el = build_section(
            parent=work,
            item_tag="persName",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=person_ref_text,
            attrs=element_attrs,
            child_tag="note",
            child_text=person_ref_note,
        )

        #maintain the TEI child element ordering
        insert_in_order(work, "persName", el, CHILD_ORDER, NSMAP)

    #update the connection index for this person and work relationship
    update_connection_index("person", person_ref_key, context['xml_id'], "work", person_ref_text)

    return success()


@section_handler("work_ref")
def handle_work_ref(work, context, form_data):
    """
    Add or update a referenced work associated with a work.

    Validates the selected work and reference type, handles custom reference type, 
    resolves the work's display title from the entity file, and determines whether the request
    is an edit or a new addition. Creates a referenced work entry with an
    optional note, maintains the connection index when the relationship is
    changed. Allows multiple referenced works to exist for the work.
    """

    work_ref_key = form_data.get("work_ref_key")
    work_ref_type = form_data.get("work_ref_type")
    work_ref_type_other = form_data.get("work_ref_type_other")
    work_ref_note = form_data.get("work_ref_note")

    #validate the selected work key
    if not work_ref_key:
        flash("No work key selected.", "work-ref-error")
        return failure()

    #resolve the work's title from the work entity file
    work_ref_text = load_ent_name_by_key("work", WORK_CONFIG, work_ref_key, "title", NSMAP)
    if not work_ref_text:
        flash("Selected work could not be resolved.", "work-ref-error")
        return failure()

    #validate the reference type
    if not work_ref_type:
        flash("Reference type cannot be empty.", "work-ref-error")
        return failure()

    #build the attributes for the referenced work
    #use custom reference type if "Other" is selected
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


    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "work-ref-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing work key before updating
        old_key = get_element_attr_by_index(
            parent=work,
            tag="rs",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        #update the selected referenced work, attributes and note
        updated_el = update_build_section(
            parent=work,
            item_tag="rs",
            ns=NS_TEI,
            text=work_ref_text,
            index=index,
            element_attrs=element_attrs,
            child_tag="note",
            child_text=work_ref_note
        )

        if updated_el is None:
            flash("Failed to update the selected work.", "work-ref-error")
            return failure()

        #remove the old connection if the referenced work has changed
        if old_key:
            remove_connection_index("work", old_key, context["xml_id"], "work")

    else:

        #add a new referenced work, attributes and optional note
        el = build_section(
            parent=work,
            item_tag="rs",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=work_ref_text,
            attrs=element_attrs,
            child_tag="note",
            child_text= work_ref_note,
            )

        #maintain the TEI child element ordering
        insert_in_order(work, "rs", el, CHILD_ORDER, NSMAP)

    #update the connection index for this work-to-work relationship
    update_connection_index("work", work_ref_key, context['xml_id'], "work", work_ref_text)

    return success()


@section_handler("pub_place")
def handle_pub_place(work, context, form_data):
    """
    Add or update an associated place associated with a work.

    Validates the selected place and connection type, handles custom
    connection types, resolves the place name from the entity file, and
    determines whether the request is an edit or a new addition. Creates
    a place entry, maintains the connection index when the
    relationship changes. Allows multiple associated places to exist
    for the work.
    """

    pub_place_key = form_data.get("pub_place_key")
    connection = form_data.get("connection")
    connection_other = form_data.get("connection_other")

    #validate the selected place key
    if not pub_place_key:
        flash("No place key selected.", "pub-place-error")
        return failure()

    #resolve the place name from the place entity file
    pub_place_text = load_ent_name_by_key("place", PLACE_CONFIG, pub_place_key, "placeName", NSMAP)
    if not pub_place_text:
        flash("Selected place could not be resolved.", "pub-place-error")
        return failure()

    #validate the connection type
    if not connection:
        flash("Place connection cannot be empty.", "pub-place-error")
        return failure() 

    #build the attributes for the associated place
    #use custom connection type if "Other" is selected
    if connection == "Other" and connection_other:
        element_attrs = {"key": pub_place_key, "role": connection_other}
    else:
        element_attrs = {"key": pub_place_key, "role": connection}

    
    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "pub-place-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing place key before updating
        old_key = get_element_attr_by_index(
            parent=work,
            tag="pubPlace",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        #update the selected associated place and attributes
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
            return failure()

        #remove the old connection if the referenced place has changed
        if old_key:
            remove_connection_index("place", old_key, context['xml_id'], "work")
 
    else:
        
        #add a new associated place and attributes
        el = build_section(
            parent=work,
            item_tag="pubPlace",
            nsmap=NSMAP,
            ns=NS_TEI,
            attrs=element_attrs,
            child_tag="placeName",
            child_text=pub_place_text
        )
        
        #maintain the TEI child element ordering
        insert_in_order(work, "pubPlace", el, CHILD_ORDER, NSMAP)

    #update the connection index for this place and work relationship
    update_connection_index("place", pub_place_key, context['xml_id'], "work", pub_place_text)

    return success()  


@section_handler("genre")
def handle_genre(work, context, form_data):
    """
    Add or update a genre for a work.

    Validates the selected genre, handles custom genres and commentary
    references, and determines whether the request is an edit or a new
    addition. Creates a genre entry, maintains the connection index when
    a commentary relationship changes. Allows multiple genres to
    exist for the work.
    """

    genre = form_data.get("genre")
    genre_other = form_data.get("genre_other")
    genre_commentary_key = form_data.get("genre_commentary_id")

    
    #resolve the commentary work title from the work entity file
    genre_commentary_text = None
    if genre_commentary_key:
        genre_commentary_text = load_ent_name_by_key("work", WORK_CONFIG, genre_commentary_key, "title", NSMAP)

    #validate the selected genre
    if not genre:
        flash("No genre entered.", "genre-error")
        return failure()

    #build the genre text and attributes
    #handle custom genres and commentary references
    if genre == "Other" and genre_other:
        text_value = genre_other
        attrs = {"type": "genre", "source": "other"}

    elif genre == "Commentary" and genre_commentary_key:
        text_value = genre_commentary_text
        attrs = {"type": "genre", "source": "commentary", "key": genre_commentary_key}

    else:
        text_value = genre
        attrs = {"type": "genre"}

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "genre-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing commentary key before updating
        old_key = get_element_attr_by_index(
            parent=work,
            tag="note",
            index=index,
            attr="key",
            ns=NS_TEI

        )

        #update the selected genre and attributes
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
            return failure()

        #remove the old connection if the commentary reference has changed
        if old_key:
            remove_connection_index("work", old_key, context["xml_id"], "work")
    else:

        #add a new genre and attributes
        el = build_section(
            parent=work,
            item_tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=text_value,
            attrs=attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=work, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY
        )

    #update the connection index for this commentary relationship
    if genre == "Commentary" and genre_commentary_key:
        update_connection_index("work", genre_commentary_key, context['xml_id'], "work", genre_commentary_text)

    return success()


@section_handler("subject")
def handle_subject(work, context, form_data):
    """
    Add or update a subject for a work.

    Validates the selected subject, handles custom subjects, and
    determines whether the request is an edit or a new addition.
    Creates a subject entry and allows multiple subjects to exist
    for the work.
    """

    subject = form_data.get("subject")
    subject_other = form_data.get("subject_other")

    #validate the selected subject
    if not subject:
        flash("No subject entered.", "subject-error")
        return failure()

    #build the subject text and attributes
    #handle custom subjects
    if subject == "Other" and subject_other:
        text_value = subject_other
        attrs = {"type": "subject", "source": "other"}
    else:
        text_value = subject
        attrs = {"type": "subject"}

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "subject-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected subject and attributes
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
            return failure()

    else:

        #add a new subject and attributes
        el = add_simple_element_attr(
            parent=work,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=text_value,
            attrs=attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=work, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("reference")
def handle_reference(work, context, form_data):
    """
    Add or update a bibliographical reference for a work.

    Validates the reference entry, handles custom references, and includes
    optional volume and page information as attributes. Determines whether
    the request is an edit or a new addition, and creates a bibliographical
    reference entry. Allows multiple references to exist for the work.
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
        element_attrs = {"type": "bibliographical", "source": "other"}
    else:
        text_value = reference
        element_attrs = {"type": "bibliographical"}
    
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
            parent=work,
            tag="note",
            text=text_value,
            ns=NS_TEI,
            match_attrs={"type": "bibliographical"},
            update_attrs=element_attrs,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected reference.", "reference-error")
            return failure()

    else:

        #add a new reference and attributes
        el = add_simple_element_attr(
            parent=work,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=text_value,
            attrs=element_attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=work, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY)

    return success()


@section_handler("notes")
def handle_notes(work, context, form_data):
    """
    Add or update general notes for a work.

    Validates the note text and determines whether the request is an edit
    or a new addition. Creates a general note entry. Allows multiple
    notes to exist for the work.
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
            parent=work,
            tag="note",
            text=notes,
            ns=NS_TEI,
            match_attrs={"type": "general"},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected notes.", "notes-error")
            return failure()

    else:

        #add a new general note
        el = add_simple_element_attr(
            parent=work,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=notes,
            attrs={"type": "general"},
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=work, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY)

    return success() 


@section_handler("record_contributor")
def handle_record_contributor(work, context, form_data):
    """
    Add or update a record contributor for a work.

    Validates the contributor name and determines whether the request is
    an edit or a new addition. Creates a responsibility statement entry with
    the contributor name and adds the corresponding contributor role to this section.
    Allows multiple contributors to exist for the work.
    """

    record_contributor = form_data.get("record_contributor")

    #validate the contributor name
    if not record_contributor:
        flash("Record contributor cannot be empty.", "record-contributor-error")
        return failure()

    #retrieve the title statement element from the TEI document
    worktitlestmt_el = context["root"].find(".//tei:titleStmt", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "record-contributor-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected record contributor name
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
            return failure()

    else:

        #add a new responsibility statement containing the contributor name
        el = build_section(
            parent=worktitlestmt_el,
            item_tag="respStmt",
            nsmap=NSMAP,
            ns=NS_TEI,
            child_tag="name",
            child_text=record_contributor,
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=worktitlestmt_el,
            tag="respStmt",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )
 

        #retrieve the newly created responsibility statement
        all_contributors = context["root"].findall(".//tei:respStmt", namespaces=NSMAP)
        workresptmt_el = all_contributors[-1] if all_contributors else None

        #add the contributor role to the responsibility statement
        el = add_simple_element_attr(
            parent=workresptmt_el,
            tag="resp",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text="Contributor"
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=workresptmt_el, 
            tag="resp", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP)

    return success()       
