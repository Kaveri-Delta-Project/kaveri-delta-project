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
PLACE_CONFIG = ENTITY_CONFIG["place"]
CHILD_ORDER = PLACE_CONFIG["child_order"]
ATTR_PRIORITY = PLACE_CONFIG["attribute_priority"]

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


@section_handler("main_place_name")
def handle_preferred_name(place, context, form_data):
    """
    Add or update the preferred name for a place.

    Validates the submitted place name, determines whether the
    request is an edit or a new addition, and ensures that only one
    preferred place name exists.
    """

    name = form_data.get("main_place_name")
    
    if not name:
        flash("Main place name cannot be empty.", "main-place-name-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "main-place-name-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected preferred place name
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
            return failure()

    else:

        #add a new preferred place name, replacing any existing place name
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

        #maintain the TEI child element ordering
        insert_in_order(
            parent=place,
            tag="placeName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("alt_place_name")
def handle_variant_name(place, context, form_data):
    """
    Add or update a variant name for a place.

    Validates the submitted place name and determines whether the request is
    an edit or a new addition. Creates a variant place name entry and allows
    multiple variant names to exist for the place.
    """


    alt_place_name = form_data.get("alt_place_name")

    if not alt_place_name:
        flash("Alternative place name cannot be empty.", "alt-place-name-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "alt-place-name-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected variant place name
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
            return failure()

    else:

        #add a new variant place name
        el = add_simple_element_attr(
            parent=place,
            tag="placeName",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=alt_place_name,
            attrs={"type": "variant"},
            allow_multiple=True
        )
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=place,
            tag="placeName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("place_type")
def handle_place_type(place, context, form_data):
    """
    Add or update a place type for a place.

    Validates the selected place type, handles custom place types,
    and determines whether the request is an edit or a new addition.
    Creates a place type entry. Allows multiple place
    types to exist for the place.
    """

    place_type = form_data.get("place_type")
    place_type_other = form_data.get("place_type_other")

    #validate the selected place type
    if not place_type:
        flash("No place type entered.", "place-type-error")
        return failure()

    #build the place type attributes
    #use custom place type if "Other" is selected
    if place_type == "Other" and place_type_other:
        text_value = place_type_other
        attrs = {"type": "function", "source": "other"}
    else:
        text_value = place_type
        attrs = {"type": "function"}

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "place-type-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected place type entry and attributes
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
            return failure()

    else:

        #add a new place type entry and attributes
        el = add_simple_element_attr(
            parent=place,
            tag="desc",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=text_value,
            attrs=attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(place, "desc", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("idno")
def handle_idno(place, context, form_data):
    """
    Add or update an identifier for a place.

    Validates the identifier type and value, checks that the identifier
    format is valid, and determines whether the request is an edit or a
    new addition. Ensures that only one identifier exists for the place.
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
            parent=place,
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
            parent=place,
            tag="idno",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=idno,
            attrs={"type": idno_type},
            allow_multiple=False
        )
        
        #maintain the TEI child element ordering
        insert_in_order(place, "idno", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("coordinates")
def handle_coordinates(place, context, form_data):
    """
    Add or update coordinates for a place.

    Validates the coordinates, checks that the coordinate format is valid,
    and determines whether the request is an edit or a new addition.
    Creates a coordinates entry and ensures that only one set of
    coordinates exists for the place.
    """

    coordinates = form_data.get("coordinates")

    #validate the coordinates value
    if not coordinates:
        flash("No coordinates entered.", "coordinates-error")
        return failure()

    #validate the coordinate format
    if coordinates and not valid_coordinates(coordinates):
        flash(f"Invalid coordinate format for {coordinates}.", "coordinates-error")
        return failure()

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "coordinates-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected coordinates
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
            return failure()

    else:       

        #add a new coordinates entry
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
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=place, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY
        )

    return success()
    

@section_handler("reference")
def handle_reference(place, context, form_data):
    """
    Add or update a bibliographical reference for a place.

    Validates the reference entry, handles custom references, and includes
    optional volume and page information as attributes. Determines whether
    the request is an edit or a new addition, and creates a bibliographical
    reference entry. Allows multiple references to exist for the place.
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
            parent=place,
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
            parent=place,
            tag="bibl",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=text_value,
            attrs=element_attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(place, "bibl", el, CHILD_ORDER, NSMAP)

    return success()


@section_handler("notes")
def handle_notes(place, context, form_data):
    """
    Add or update general notes for a place.

    Validates the note text and determines whether the request is
    an edit or a new addition. Creates a general note entry and allows
    multiple notes to exist for the place.
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
            parent=place,
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
            parent=place,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=notes,
            attrs={"type": "general"},
            allow_multiple=True
        )
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=place, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY)

    return success()

