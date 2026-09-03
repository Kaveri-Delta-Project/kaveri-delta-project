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
ISC_CONFIG = ENTITY_CONFIG["inscription"]
PLACE_CONFIG = ENTITY_CONFIG["place"]
PERSON_CONFIG = ENTITY_CONFIG["person"]
CHILD_ORDER = ISC_CONFIG["child_order"]
ATTR_PRIORITY = ISC_CONFIG["attribute_priority"]

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


@section_handler("main_isc_name")
def handle_preferred_name(inscription, context, form_data):
    """
    Add or update the preferred inscription name.

    Validates the submitted inscription name, determines whether the
    request is an edit or a new addition, and ensures that only one
    preferred inscription name exists.
    """    

    name = form_data.get("main_isc_name")

    if not name:
        flash("Inscription name cannot be empty.", "main-isc-name-error")
        return failure()

    #retrieve the manuscript identifier element from the TEI document
    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "main-isc-name-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected preferred inscription name
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
            return failure()

    else:

        #add a new preferred inscription name, replacing any existing preferred name
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
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=msIdentifier_el,
            tag="msName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("alt_isc_name")
def handle_variant_name(inscription, context, form_data):
    """
    Add or update a variant inscription name.

    Validates the submitted inscription name and determines whether the
    request is an edit or a new addition. Allows multiple variant
    inscription names to exist for the inscription.
    """

    alt_name = form_data.get("alt_isc_name")

    if not alt_name:
        flash("Alternative name cannot be empty.", "alt-isc-name-error")
        return failure()

    #retrieve the manuscript identifier element from the TEI document
    msIdentifier_el = context["root"].find(".//tei:msIdentifier", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "alt-isc-name-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected variant inscription name
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
            return failure()

    else:

        #add a new variant inscription name
        el = add_simple_element_attr(
            parent=msIdentifier_el,
            tag="msName",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=alt_name,
            attrs={"type": "variant"},
            allow_multiple=True
        )
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=msIdentifier_el,
            tag="msName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="type",
            attr_priority=ATTR_PRIORITY
        )

    return success()


@section_handler("dates")
def handle_dates(inscription, context, form_data):
    """
    Add or update an inscription date.

    Validates the submitted date description and date range, determines
    whether the request is an edit or a new addition, and stores the
    date range as attributes on the TEI origDate element. Allows multiple
    inscription dates to exist.
    """

    dates_text = form_data.get("dates_text")
    dates_from = form_data.get("dates_from")
    dates_to = form_data.get("dates_to")

    #validate the date description
    if not dates_text:
        flash("No dates text entered.", "dates-error")
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

    #retrieve the origin element from the TEI document
    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "dates-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected date entry and attributes        
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
            return failure()

    else:

        #add a new date entry and attributes
        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="origDate",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=dates_text,
            attrs={"from": dates_from, "to": dates_to},
            allow_multiple=True
        )        
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=msorigin_el,
            tag="origDate",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )

    return success()


@section_handler("recipient")
def handle_recipient(inscription, context, form_data):
    """
    Add or update a recipient for an inscription.

    Validates the selected recipient, handles custom recipient values,
    and determines whether the request is an edit or a new addition.
    Creates a recipient entry. Allows multiple recipients to exist
    for the inscription.
    """

    recipient = form_data.get("recipient")
    recipient_other = form_data.get("recipient_other")

    #validate the selected recipient
    if not recipient:
        flash("No recipient selected.", "recipient-error")
        return failure()

    #build the recipient text and attributes
    #handle custom recipient values
    if recipient == "Other" and recipient_other:
        text_value = recipient_other
        attrs = {"type": "recipient", "source": "other"}
    else:
        text_value = recipient
        attrs = {"type": "recipient"}

    #retrieve the summary element from the TEI document
    ms_summary_el = context["root"].find(".//tei:summary", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "recipient-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected recipient and attributes
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
            flash("Failed to update recipient.", "recipient-error")
            return failure()

    else:

        #add a new recipient and attributes
        el = add_simple_element_attr(
            parent=ms_summary_el,
            tag="orgName",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=text_value,
            attrs=attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=ms_summary_el,
            tag="orgName",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )

    return success()


@section_handler("donor")
def handle_donor(inscription, context, form_data):
    """
    Add or update a donor associated with an inscription.

    Validates the selected donor, resolves the donor's display name from
    the person entity file, and determines whether the request is an edit
    or a new addition. Creates a donor person entry, maintains the
    connection index when the donor relationship changes. Allows
    multiple donors to exist for the inscription.
    """

    donor_key = form_data.get("donor_key")

    #validate the selected donor key
    if not donor_key:
        flash("No donor key selected.", "donor-error")
        return failure()

    #resolve the donor's display name from the person entity file
    donor_text = load_ent_name_by_key("person", PERSON_CONFIG, donor_key, "persName", NSMAP)
    if not donor_text:
        flash("Selected person could not be resolved.", "donor-error")
        return failure()

    #retrieve the listPerson element from the TEI document
    ms_list_person_el = context["root"].find(".//tei:listPerson", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "donor-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing donor key before updating
        old_key = get_element_attr_by_index(
            parent=ms_list_person_el,
            tag="person",
            index=index,
            attr="key",
            match_attrs={"ana": "donor"},
            ns=NS_TEI,
            from_child=True
        )

        #update the selected donor and attributes
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
            return failure()

        #remove the old connection if the donor has changed
        if old_key:
            remove_connection_index("person", old_key, context['xml_id'], "inscription")

    else:

        #add a new donor entry and attributes
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
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=ms_list_person_el,
            tag="person",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            sort_attr="ana",
            attr_priority=ATTR_PRIORITY
        )

    #update the connection index for this donor and inscription relationship
    update_connection_index("person", donor_key, context['xml_id'], "inscription", donor_text)

    return success()


@section_handler("assoc_person")
def handle_associated_person(inscription, context, form_data):
    """
    Add or update an associated person for an inscription.

    Validates the selected person and role, resolves the person's display
    name from the person entity file, and determines whether the request
    is an edit or a new addition. Creates an associated person entry,
    maintains the connection index when the relationship changes.
    Allows multiple associated persons to exist for the inscription.
    """

    assoc_person_key = form_data.get("assoc_person_key")
    assoc_person_role = form_data.get("assoc_person_role")

    #validate the selected person key
    if not assoc_person_key:
        flash("No associated person key selected.", "assoc-person-error")
        return failure()

    #resolve the person's display name from the person entity file
    assoc_person_text = load_ent_name_by_key("person", PERSON_CONFIG, assoc_person_key, "persName", NSMAP)
    if not assoc_person_text:
        flash("Selected person could not be resolved.", "assoc-person-error")
        return failure()

    #validate the selected person role
    if not assoc_person_role:
        flash("Person role cannot be empty.", "assoc-person-error")
        return failure()

    #retrieve the listPerson element from the TEI document
    ms_list_person_el = context["root"].find(".//tei:listPerson", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "assoc-person-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing person key before updating
        old_key = get_element_attr_by_index(
            parent=ms_list_person_el,
            tag="person",
            index=index,
            attr="key",
            match_attrs={"ana": "associated"},
            ns=NS_TEI,
            from_child=True
        )

        #update the selected associated person and attributes
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
            return failure()

        #remove the old connection if the associated person has changed
        if old_key:
            remove_connection_index("person", old_key, context['xml_id'], "inscription")

    else:

        #add a new associated person and attributes
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
        
        #maintain the TEI child element ordering
        insert_in_order(
            parent=ms_list_person_el,
            tag="person",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP,
            attr_priority=ATTR_PRIORITY
        )

    #update the connection index for this person and inscription relationship
    update_connection_index("person", assoc_person_key, context['xml_id'], "inscription", assoc_person_text)

    return success()


@section_handler("language")
def handle_language(inscription, context, form_data):
    """
    Add or update a language for an inscription.

    Validates the language value and determines whether the request is
    an edit or a new addition. Creates a language entry. Allows
    multiple languages to exist for the inscription.
    """

    #validate the language value
    language = form_data.get("language")

    if not language:
        flash("Language cannot be empty.", "language-error")
        return failure()

    #retrieve the origin element from the TEI document
    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "language-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected language
        updated_el = update_simple_element_attr(
            parent=msorigin_el,
            tag="lang",
            text=language,
            ns=NS_TEI,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected language.", "language-error")
            return failure()

    else:

        #add a new language
        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="lang",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=language,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=msorigin_el, 
            tag="lang", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP 
        )

    return success()   


@section_handler("donation_type")
def handle_donation_type(inscription, context, form_data):
    """
    Add or update a donation type for an inscription.

    Validates the donation type and determines whether the request is
    an edit or a new addition. Creates a donation type entry and allows
    multiple donation types to exist for the inscription.
    """

    donation_type = form_data.get("donation_type")

    #validate the donation type
    if not donation_type:
        flash("Donation type cannot be empty.", "donation-type-error")
        return failure()

    #retrieve the history element from the TEI document
    mshistory_el = context["root"].find(".//tei:history", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "donation-type-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected donation type
        updated_el = update_simple_element_attr(
            parent=mshistory_el,
            tag="provenance",
            text=donation_type,
            ns=NS_TEI,
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected donation type.", "donation-type-error")
            return failure()

    else:

        #add a new donation type
        el = add_simple_element_attr(
            parent=mshistory_el,
            tag="provenance",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=donation_type,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=mshistory_el, 
            tag="provenance", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP 
        )

    return success()   


@section_handler("material")
def handle_material(inscription, context, form_data):
    """
    Add or update a material for an inscription.

    Validates the selected material, handles custom material values,
    and determines whether the request is an edit or a new addition.
    Creates a material entry. Allows multiple materials to exist
    for the inscription.
    """

    material = form_data.get("material")
    material_other = form_data.get("material_other")

    #validate the selected material
    if not material:
        flash("No material selected.", "material-error")
        return failure()

    #build the material text and attributes
    #handle custom material values    
    if material == "Other" and material_other:
        text_value = material_other
        attrs = {"source": "other"}
    else:
        text_value = material
        attrs = None

    #retrieve the physical description paragraph from the TEI document
    ms_physp_el = context["root"].find(".//tei:physDesc/tei:p", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited    
    index = get_edit_index(form_data, "material-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected material and attributes
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
            return failure()

    else:

        #add a new material and attributes
        el = add_simple_element_attr(
            parent=ms_physp_el,
            tag="material",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=text_value,
            attrs=attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering        
        insert_in_order(
            parent=ms_physp_el,
            tag="material",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )

    return success()


@section_handler("location")
def handle_location(inscription, context, form_data):
    """
    Add or update a location associated with an inscription.

    Validates the selected location and location type: inscription or donation related
    to inscription, resolves the location name from the place entity file, 
    and determines whether the request is an edit or a new addition. 
    Creates a location entry, maintains the connection index
    when the relationship changes. Allows multiple locations to exist
    for the inscription.
    """

    location_key = form_data.get("location_key")
    location_type = form_data.get("location_type")

    #validate the selected location key
    if not location_key:
        flash("No location key selected.", "location-error")
        return failure()

    #resolve the location name from the place entity file
    location_text = load_ent_name_by_key("place", PLACE_CONFIG, location_key, "placeName", NSMAP)
    if not location_text:
        flash("Selected location could not be resolved.", "location-error")
        return failure()

    #validate the location type
    if not location_type:
        flash("No location type entered.", "location-type-error")
        return failure()

    #retrieve the origin element from the TEI document
    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "location-error")
    if index is False:
        return failure()

    if index is not None:

        #retrieve the existing location key before updating
        old_key = get_element_attr_by_index(
            parent=msorigin_el,
            tag="origPlace",
            index=index,
            attr="key",
            ns=NS_TEI
        )

        #update the selected location and attributes
        updated_el = update_simple_element_attr(
            parent=msorigin_el,
            tag="origPlace",
            text=location_text,
            ns=NS_TEI,
            update_attrs={"key": location_key, "type": location_type},
            index=index
        )

        if updated_el is None:
            flash("Failed to update the selected location.", "location-error")
            return failure()

        #remove the old connection if the location has changed
        if old_key:
            remove_connection_index("place", old_key, context["xml_id"], "inscription")

    else:
    
        #add a new location and attributes
        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="origPlace",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=location_text,
            attrs={"key": location_key, "type": location_type},
            allow_multiple=True
        )

        #maintain the TEI child element ordering        
        insert_in_order(
            parent=msorigin_el,
            tag="origPlace",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )

    #update the connection index for this place and inscription relationship
    update_connection_index("place", location_key, context['xml_id'], "inscription", location_text)

    return success()


@section_handler("reference")
def handle_reference(inscription, context, form_data):
    """
    Add or update a bibliographical reference for an inscription.

    Validates the reference entry, handles custom references, and includes
    optional volume and page information as attributes. Determines whether
    the request is an edit or a new addition, and creates a bibliographical
    reference entry. Allows multiple references to exist for the inscription.
    """

    reference = form_data.get("reference")
    reference_other = form_data.get("reference_other")
    ref_vol = form_data.get("volume")
    ref_page = form_data.get("page")

    #validate the reference value
    if not reference:
        flash("Reference cannot be empty.", "reference-error")
        return failure()

    #retrieve the origin element from the TEI document
    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

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
            parent=msorigin_el,
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
            parent=msorigin_el,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,
            text=text_value,
            attrs=element_attrs,
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=msorigin_el, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY)

    return success()


@section_handler("notes")
def handle_notes(inscription, context, form_data):
    """
    Add or update general notes for an inscription.

    Validates the note text and determines whether the request is
    an edit or a new addition. Creates a general note entry and allows
    multiple notes to exist for the inscription.
    """    

    notes = form_data.get("notes")

    #validate the note text
    if not notes:
        flash("Notes cannot be empty.", "notes-error")
        return failure()

    #retrieve the origin element from the TEI document
    msorigin_el = context["root"].find(".//tei:origin", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "notes-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected general note text
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
            return failure()

    else:

        #add a new general note
        el = add_simple_element_attr(
            parent=msorigin_el,
            tag="note",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text=notes,
            attrs={"type": "general"},
            allow_multiple=True
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=msorigin_el, 
            tag="note", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP, 
            sort_attr="type", 
            attr_priority=ATTR_PRIORITY)

    return success()

    
@section_handler("record_contributor")
def handle_record_contributor(inscription, context, form_data):
    """
    Add or update a record contributor for an inscription.

    Validates the contributor name and determines whether the request is
    an edit or a new addition. Creates a responsibility statement entry
    containing the contributor name and adds the corresponding contributor
    role. Allows multiple contributors to exist for the inscription.
    """

    record_contributor = form_data.get("record_contributor")

    #validate the contributor name
    if not record_contributor:
        flash("Record contributor cannot be empty.", "record-contributor-error")
        return failure()

    #retrieve the title statement element from the TEI document
    mstitlestmt_el = context["root"].find(".//tei:titleStmt", namespaces=NSMAP)

    #determine whether this is an edit or a new addition
    #index represents the position of the item being edited
    index = get_edit_index(form_data, "record-contributor-error")
    if index is False:
        return failure()

    if index is not None:

        #update the selected record contributor name
        updated_el = update_build_section(
            parent=mstitlestmt_el,
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
            parent=mstitlestmt_el,
            item_tag="respStmt",
            nsmap=NSMAP,
            ns=NS_TEI,
            child_tag="name",
            child_text=record_contributor,
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=mstitlestmt_el,
            tag="respStmt",
            new_elem=el,
            child_order=CHILD_ORDER,
            nsmap=NSMAP
        )
 
        #retrieve the newly created responsibility statement
        all_contributors = context["root"].findall(".//tei:respStmt", namespaces=NSMAP)
        msresptmt_el = all_contributors[-1] if all_contributors else None

        #add the contributor responsibility type
        el = add_simple_element_attr(
            parent=msresptmt_el,
            tag="resp",
            nsmap=NSMAP,
            ns=NS_TEI,            
            text="Contributor"
        )

        #maintain the TEI child element ordering
        insert_in_order(
            parent=msresptmt_el, 
            tag="resp", 
            new_elem=el, 
            child_order=CHILD_ORDER, 
            nsmap=NSMAP)

    return success()



