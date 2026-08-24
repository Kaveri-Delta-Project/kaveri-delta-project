import string
import html
import re
from config import ROLES, TEMPLATE_CONFIG
from tei_helpers import normalize_for_sort

#bibliographical reference lookup, used for correct formatting
REFS = TEMPLATE_CONFIG.get("bibliographical_references", {})

#HTML rendering helpers

def render_alphabet_nav():
    """
    Render an alphabetical navigation bar (A–Z).

    Returns:
        list[str]: A list of HTML strings representing a navigation
        element containing buttons for each uppercase letter.
    """
    html = ["  <div class='alphabet mb-3 d-flex flex-wrap gap-2' id='alphabet-nav'>"]
    for letter in string.ascii_uppercase:
        html.append(f"    <button class='btn btn-sm btn-outline-secondary alphabet-btn' data-letter='{letter}'>{letter}</button>")
    html.append("   <button type='button' class='btn btn-sm btn-outline-primary show-all alphabet-btn' data-letter='all'>Show All</button>")
    html.append("  </div>")
    return html


def render_search():
    """
    Render a search box with a clear button for the index.

    Returns:
        list[str]: HTML lines for a search form.
    """
    html = [
        "  <form id='index-search-form' class='d-flex mt-3 mt-md-0 index-search-form' onsubmit='return false;'>",
        "    <div class='input-group input-group-sm search-group'>",
        "      <input type='text' id='index-search' class='search-input form-control' placeholder='Search by name, diacritics ignored..' autocomplete='off'>",
        "      <button type='button' id='search-clear' class='btn btn-secondary search-button search-clear-btn'>Clear</button>",
        "    </div>",
        "  </form>"
    ]
    return html


def first(lst):
    """Return the first item of a list or None if empty."""
    return lst[0] if lst else None


def esc(value):
    """Escape a string for safe HTML insertion."""
    return html.escape(str(value)) if value else ""


def render_list(items, css_class=None):
    """
    Sort and render a list of items as a vertical block using <div> for each item.

    Parameters:
        items (list[str]): The items to render.
        css_class (str, optional): CSS class applied to each <div> item.

    Returns:
        str: HTML string for the list, or empty string if no items.
    """
    if not items:
        return ''

    #sort displayed values consistently using normalization function
    items = sorted(items, key=normalize_for_sort)

    cls_attr = f' class="{esc(css_class)}"' if css_class else ''
    
    html = []
    for item in items:
        html.append(f"<div{cls_attr}>{esc(item)}</div>")

    return '\n'.join(html)


def render_entry_header(xml_id, name):
    """
    Render the standard header for an index entry.

    The header displays the entity name, if present, and XML identifier, 
    followed by a toggle button used to show or hide the entry details.

    Parameters:
        xml_id (str): Unique XML identifier for the entity.
        name (str): Display name for the entity.

    Returns:
        str: HTML string containing the entry header.
    """
    html = ["<div class='entry-header'>"]

    #display the preferred name when available, otherwise use the XML identifier
    if name:
        html.append(f"<span class='entry-title'>{esc(name)}</span>")
        html.append(f"<span class='entry-id'>({esc(xml_id)})</span>")
    else:
        html.append(f"<span class='entry-title'>{esc(xml_id)}</span>")

    html.append("  <button class='toggle' aria-label='Show details'>▸</button>")
    html.append("</div>")

    return "\n".join(html)


def make_entity_url(entity_type, key, single_page=True):
    """
    Build an internal URL for an entity index entry.

    Parameters:
        entity_type (str): Type of entity being linked to, e.g. person or place.
        key (str): XML identifier of the entity.
        single_page (bool): If True, link to the entity anchor on the current
            page; otherwise link to the entity's separate index page.

    Returns:
        str: URL pointing to the entity index entry.
    """
    #use a local anchor when all entity types are displayed on the same page
    if single_page:
        return f"#{esc(key)}"
    #otherwise link to the separate index page for the entity type
    return f"{entity_type}_index.html#{esc(key)}"


def make_map_url(coordinates, filename="/map.html"):
    """
    Build an internal map URL using the supplied coordinates.

    Parameters:
        coordinates (str): Coordinates used as the map page anchor.
        filename (str): Map page filename or path.

    Returns:
        str: URL pointing to the supplied coordinates on the map page.
    """
    coordinates = coordinates.replace(' ', '')
    return f"{filename}#{coordinates}"


def make_reference_url(identifier):
    """
    Build an internal URL for a bibliographical reference.

    Parameters:
        identifier (str): Identifier of the reference entry.

    Returns:
        str: URL pointing to the reference entry on the references page.
    """
    return f"../references.html#{esc(identifier)}"


def render_place(place):
    """
    Render a place as an expandable index entry.

    Builds the HTML for a single place, including its standard entry
    header and any available descriptive or relational information.

    Includes:
        - Alternative place names
        - Authority identifiers
        - Coordinates and map link
        - Place types
        - Associated persons and inscriptions
        - Notes
        - Bibliographical references

    Args:
        place (dict): Place data loaded from the entity index.

    Returns:
        str: HTML string representing the complete place index entry.
    """
    
    html = []
    
    #basic entry information used for the index heading and anchor
    xml_id = place.get("xml_id")
    name = first(place.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")
    
    #render the standard entry heading and details container
    html.append(render_entry_header(xml_id, name))
    html.append("<div class='item-details'>")

    
    #render alternative names when available
    alt_names_html = render_list(place.get("alt_names"), "item-name")
    
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Place Names</span>")
        html.append(alt_names_html)
        html.append("</div>")

    
    #render authority identifier when both identifier value and type are available
    idno_value = first(place.get("idno_value"))
    idno_type = first(place.get("idno_type"))
    
    if idno_value and idno_type:
        html.append("<div class='entry-block entry-idno'>")
        html.append("<span class='subheading'>Authority Identifier</span>")
        html.append(f"<span class='item-name'>{esc(idno_value)} ({esc(idno_type)})</span>")
        html.append("</div>")

    
    #render coordinates and link to the map page
    coordinates = first(place.get("coords"))
    
    if coordinates:
        map_url = make_map_url(coordinates)

        html.append("<div class='entry-block entry-coords'>")
        html.append("<span class='subheading'>Coordinates</span>")
        html.append(f"<span class='item-name'>{esc(coordinates)}</span>")
        html.append(f"<a class='map-link item-name' target='map-page' href='{map_url}'>View on map</a>")
        html.append("</div>")

    #render place types when available
    place_types_html = render_list(place.get("place_type"), "item-name")
    
    if place_types_html:
        html.append("<div class='entry-block entry-place-types'>")
        html.append("<span class='subheading'>Place Types</span>")
        html.append(place_types_html)
        html.append("</div>")

    #render associated persons, sorted alphabetically by person name
    #each person may include an optional date range and relationship role,
    #which are stored as data attributes for frontend filtering and also
    #displayed alongside the person's name
    #each person is linked to its own index entry
    linked_person = place.get("place_person")
    linked_person = sorted(linked_person, key=lambda x: normalize_for_sort(x.get("name")))

    if linked_person:
        html.append("<div class='entry-block entry-place-pers'>")
        html.append("<span class='subheading'>Associated Persons</span>")
        for affil in linked_person:
            key = affil.get("xml_id")
            person_name = affil.get("name")
            affil_from = affil.get("from")
            affil_to = affil.get("to")
            affil_role = affil.get("role")

            #skip incomplete relationship records that cannot be linked
            if not key or not person_name:
                continue
            
            url = make_entity_url("person", key, single_page=False)

            data_attrs = ""
            data_attrs_contents = ""

            #add date information as data attributes for filtering and
            #as visible text, using a single year when the range is identical
            if affil_from and affil_to:
                data_attrs += f" data-from='{esc(affil_from)}'"
                data_attrs += f" data-to='{esc(affil_to)}'"
                if affil_from == affil_to:
                    data_attrs_contents += f" ({esc(affil_from)})"
                else:
                    data_attrs_contents += f" ({esc(affil_from)}-{esc(affil_to)})"
            
            #add the relationship role as both a data attribute and
            #visible connection information
            if affil_role:
                data_attrs += f" data-role='{esc(affil_role)}'"
                data_attrs_contents += f" (connection: {esc(affil_role)})"

            #include the additional date/role text only when relationship
            #metadata is available
            if affil_from or affil_to or affil_role:
                html.append(
                    f"<a href='{esc(url)}' target='person-index' class='item-name' {data_attrs}>"
                    f"{esc(person_name)} ({esc(key)}) {data_attrs_contents}</a>"
                )
            else:
                html.append(
                    f"<a href='{esc(url)}' target='person-index' class='item-name'>{esc(person_name)} ({esc(key)})</a>"
                )
        html.append("</div>")

    #render associated inscriptions, sorted alphabetically by inscription name
    #each inscription is linked to its own index entry
    linked_inscriptions = place.get("place_inscription")
    linked_inscriptions = sorted(linked_inscriptions, key=lambda x: normalize_for_sort(x.get("name")))

    if linked_inscriptions:
        html.append("<div class='entry-block entry-place-insc'>")
        html.append("<span class='subheading'>Associated Inscriptions</span>")
        for inscription in linked_inscriptions:
            key = inscription.get("xml_id")
            inscription_name = inscription.get("name")

            #skip incomplete inscription records that cannot be linked
            if not key or not inscription_name:
                continue
            
            url = make_entity_url("inscription", key, single_page=False)

            html.append(f"<a href='{esc(url)}' target='inscription-index' class='item-name'>{esc(inscription_name)} ({esc(key)})</a>")
        
        html.append("</div>")

    #render notes when available
    notes_html = render_list(place.get("notes"), "item-name")
    
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")

    #render bibliographical references using configured reference formatting
    #references are sorted alphabetically by their source text
    references = place.get("reference")
    references = sorted(references, key=lambda x: normalize_for_sort(x.get("reference")))

    if references:
        html.append("<div class='entry-block entry-reference'>")
        html.append("<span class='subheading'>References</span>")
        
        for reference in references:
            ref_raw = reference.get("parent_text")

            #look up the reference in the configured bibliography so that
            #the formatted HTML text and reference identifier can be used
            ref = REFS.get(ref_raw, None)

            if ref:
                ref_text = ref.get("html", ref_raw)
                ref_id = ref.get("identifier")
            else:
                #fall back to the original reference text when no
                #configured bibliography entry is available
                ref_text = ref_raw
                ref_id = None

            ref_vol = reference.get("subtype")
            ref_page = reference.get("n")

            data_attrs = ""
            data_attrs_contents = ""

            #add volume and page information as data attributes for
            #frontend filtering and as visible text alongside the reference
            if ref_vol and ref_page:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)}, Page(s) {esc(ref_page)})"

            #include volume information when no page number is supplied
            elif ref_vol:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)})"

            #include page information when no volume number is supplied
            elif ref_page:
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Page(s) {esc(ref_page)})"

            #use a link when the reference has a configured identifier
            #otherwise render the reference as plain text
            tag = "a" if ref_id else "span"

            link_attr = f" href='{make_reference_url(ref_id)}' target='reference-page'" if ref_id else ""

            attrs = f"{link_attr}{data_attrs}"

            html.append(
                f"<{tag} class='item-name reference'{attrs}>"
                f"{ref_text}"
                f"{data_attrs_contents if (ref_vol or ref_page) else ''}"
                f"</{tag}>"
            )
                    
        html.append("</div>")

    html.append("</div>")
    return "\n".join(html)


def render_person(person):
    """
    Render a person as an expandable index entry.

    Builds the HTML for a single person, including the standard entry
    header and any available descriptive or relational information.

    Includes:
        - Alternative names
        - Gender
        - Associated persons
        - Authority identifiers
        - Birth, death, and floruit dates
        - Associated places
        - Associated works
        - Notes
        - Bibliographical references

    Args:
        person (dict): Person data loaded from the entity index.

    Returns:
        str: HTML string representing the complete person index entry.
    """

    html = []

    #basic entry information used for the index heading and anchor
    xml_id = person.get("xml_id")
    name = first(person.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")

    #render the standard entry heading and details container
    html.append(render_entry_header(xml_id, name))
    html.append("<div class='item-details'>")

    
    #render alternative names when available
    alt_names_html = render_list(person.get("alt_names"), "item-name")
    
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Names</span>")
        html.append(alt_names_html)
        html.append("</div>")     

    
    #render gender when value available
    gender = person.get("sex")
    
    if gender:
        html.append("<div class='entry-block entry-gender'>")
        html.append("<span class='subheading'>Gender</span>")
        html.append(f"<span class='item-name'>{esc(gender)}</span>")
        html.append("</div>")


    #render associated persons, sorted alphabetically by person name
    #each relationship may include a connection type and optional date range,
    #which are stored as data attributes and displayed alongside the person
    #each person is linked to their own index entry
    relationships = person.get("relationship")
    relationships = sorted(relationships, key=lambda x: normalize_for_sort(x.get("label")))

    if relationships:
        html.append("<div class='entry-block entry-relationships'>")
        html.append("<span class='subheading'>Associated Persons</span>")

        for rel in relationships:
            key = rel.get("key")
            connection = rel.get("type")
            rel_name = rel.get("label")
            rel_from = rel.get("from")
            rel_to = rel.get("to")

            url = make_entity_url("person", key, single_page=True)

            html.append("<div class='item-name'>")

            data_attrs = ""
            data_attrs_contents = ""

            #store the relationship type as a data attribute for frontend use
            if connection:
                data_attrs += f" data-connection='{esc(connection)}'"

            #add relationship dates as data attributes and visible text
            if rel_from and rel_to:
                data_attrs += f" data-from='{esc(rel_from)}'"
                data_attrs += f" data-to='{esc(rel_to)}'"

                if rel_from == rel_to:
                    data_attrs_contents += f" ({esc(rel_from)})"
                else:
                    data_attrs_contents += f" ({esc(rel_from)}-{esc(rel_to)})"

            #remove "of" from the stored relationship type so that it can
            #be inserted into the displayed "relationship: ... of" wording       
            clean_connection = re.sub(r'\bof\b', '', connection).strip()
            
            html.append(f"  <span>relationship: {esc(clean_connection)} of</span>")
            html.append(
                f"  <a href='{esc(url)}' {data_attrs}>"
                f"{esc(rel_name)} ({esc(key)}) {data_attrs_contents}</a>"
            )

            html.append("</div>")

        html.append("</div>")

    
    #render the authority identifier when both its value and type are available
    idno_value = first(person.get("idno_value"))
    
    idno_type = first(person.get("idno_type"))
    if idno_value and idno_type:
        html.append("<div class='entry-block entry-idno'>")
        html.append("<span class='subheading'>Authority Identifier</span>")
        html.append(f"<span class='item-name'>{esc(idno_value)} ({esc(idno_type)})</span>")
        html.append("</div>")

    
    #render the birth date using the human-readable text and machine-readable
    #date value stored in the data-when attribute
    birth_text = first(person.get("birth_text"))
    birth_num = first(person.get("birth_when"))
    
    if birth_text and birth_num:
        html.append("<div class='entry-block entry-birth'>")
        html.append("<span class='subheading'>Birth Date</span>")
        html.append(f"<span data-when='{esc(birth_num)}' class='item-name'>{esc(birth_text)}</span>")
        html.append("</div>")

    
    #render the death date using the human-readable text and machine-readable
    #date value stored in the data-when attribute
    death_text = first(person.get("death_text"))
    death_num = first(person.get("death_when"))
    
    if death_text and death_num:
        html.append("<div class='entry-block entry-death'>")
        html.append("<span class='subheading'>Death Date</span>")
        html.append(f"<span data-when='{esc(death_num)}' class='item-name'>{esc(death_text)}</span>")
        html.append("</div>")


    #render the floruit period using the human-readable text and machine-readable
    #date range stored in data attributes for frontend use
    floruit_text = first(person.get("floruit_text"))
    floruit_from = first(person.get("floruit_from"))  
    floruit_to = first(person.get("floruit_to"))
    
    if floruit_text and floruit_from and floruit_to:
        html.append("<div class='entry-block entry-floruit'>")
        html.append("<span class='subheading'>Floruit (Period of Activity)</span>")
        html.append(f"<span data-from='{esc(floruit_from)}' data-to='{esc(floruit_to)}' class='item-name'>{esc(floruit_text)}</span>")
        html.append("</div>")


    #render associated places, sorted alphabetically by place name
    #each place may include an optional date range and relationship role,
    #which are stored as data attributes and displayed alongside the place
    #each place is linked to its own index entry
    affiliations = person.get("affiliations")
    affiliations = sorted(affiliations, key=lambda x: normalize_for_sort(x.get("placeName")))

    if affiliations:
        html.append("<div class='entry-block entry-affils'>")
        html.append("<span class='subheading'>Associated Places</span>")
        
        for affil in affiliations:
            key = affil.get("key")
            place_name = affil.get("placeName")
            affil_from = affil.get("from")
            affil_to = affil.get("to")
            affil_role = affil.get("role")

            #skip incomplete affiliation records that cannot be linked
            if not key or not place_name:
                continue

            url = make_entity_url("place", key, single_page=False)

            data_attrs = ""
            data_attrs_contents = ""
            
            #add affiliation dates as data attributes and visible text
            if affil_from and affil_to:
                data_attrs += f" data-from='{esc(affil_from)}'"
                data_attrs += f" data-to='{esc(affil_to)}'"
                
                if affil_from == affil_to:
                    data_attrs_contents += f" ({esc(affil_from)})"
                else:    
                    data_attrs_contents += f" ({esc(affil_from)}-{esc(affil_to)})"
            
            #add the affiliation role as both a data attribute and
            #visible connection information
            if affil_role:
                data_attrs += f" data-role='{esc(affil_role)}'"
                data_attrs_contents += f" (connection: {esc(affil_role)})"

            if affil_from or affil_to or affil_role:
                html.append(f"<a href='{esc(url)}' target='place-index' class='item-name' {data_attrs}>{esc(place_name)} ({esc(key)}) {data_attrs_contents}</a>")
            else:
                html.append(f"<a href='{esc(url)}' target='place-index' class='item-name'>{esc(place_name)} ({esc(key)})</a>")
        
        html.append("</div>")


    #render associated works, sorted alphabetically by work title
    #each work is linked to its own index entry and may include a configured role
    linked_work = person.get("person_work")
    linked_work = sorted(linked_work, key=lambda x: normalize_for_sort(x.get("title")))

    if linked_work:
        html.append("<div class='entry-block entry-person-works'>")
        html.append("<span class='subheading'>Associated Works</span>")
        for work in linked_work:
            key = work.get("xml_id")
            title = work.get("title")
            
            #look up the role in the configured work roles
            #the configured values are based on MARC relator codes
            #and provide the human-readable role displayed in the index
            role = ROLES.get(work.get("role"))

            #skip incomplete work records that cannot be linked
            if not key or not title:
                continue

            url = make_entity_url("work", key, single_page=False)

            #append the configured role when one is available
            role_text = f" (role: {esc(role)})" if role else ""
            
            html.append(
                f"<a href='{esc(url)}' target='work-index' class='item-name'>{esc(title)} ({esc(key)}){role_text}</a>"
            )
        
        html.append("</div>")

    
    #render notes when available
    notes_html = render_list(person.get("notes"), "item-name")
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")

    
    #render bibliographical references using configured reference formatting
    #references are sorted alphabetically by their source text
    references = person.get("reference")
    references = sorted(references, key=lambda x: normalize_for_sort(x.get("reference")))

    if references:
        html.append("<div class='entry-block entry-reference'>")
        html.append("<span class='subheading'>References</span>")
        for reference in references:
            ref_raw = reference.get("parent_text")

            #look up the reference in the configured bibliography so that
            #the formatted HTML text and reference identifier can be used
            ref = REFS.get(ref_raw, None)

            if ref:
                ref_text = ref.get("html", ref_raw)
                ref_id = ref.get("identifier")
            else:
                #fall back to the original reference text when no
                #configured bibliography entry is available
                ref_text = ref_raw
                ref_id = None
            
            ref_vol = reference.get("subtype")
            ref_page = reference.get("n")

            data_attrs = ""
            data_attrs_contents = ""

            #add volume and page information as data attributes for
            #frontend filtering and as visible text alongside the reference
            if ref_vol and ref_page:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)}, Page(s) {esc(ref_page)})"

            #include volume information when no page number is supplied
            elif ref_vol:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)})"

            #include page information when no volume number is supplied
            elif ref_page:
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Page(s) {esc(ref_page)})"

            #use a link when the reference has a configured identifier
            #otherwise render the reference as plain text
            tag = "a" if ref_id else "span"

            link_attr = f" href='{make_reference_url(ref_id)}' target='reference-page'" if ref_id else ""

            attrs = f"{link_attr}{data_attrs}"

            html.append(
                f"<{tag} class='item-name reference'{attrs}>"
                f"{ref_text}"
                f"{data_attrs_contents if (ref_vol or ref_page) else ''}"
                f"</{tag}>"
            )
        
        html.append("</div>")

    html.append("</div>")
    return "\n".join(html)    


def render_work(work):
    """
    Render a work as an expandable index entry.

    Builds the HTML for a single work, including the standard entry
    header and any available descriptive or relational information.

    Includes:
        - Alternative titles
        - Authority identifiers
        - Associated dates
        - Associated persons
        - Persons referenced in the work
        - Other works referenced in the work
        - Associated places
        - Genre
        - Subject
        - Notes
        - Bibliographical references

    Args:
        work (dict): Work data loaded from the entity index.

    Returns:
        str: HTML string representing the complete work index entry.
    """

    html = []

    #basic entry information used for the index heading and anchor
    xml_id = work.get("xml_id")
    name = first(work.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")

    #render the standard entry heading and details container
    html.append(render_entry_header(xml_id, name))
    html.append("<div class='item-details'>")

    
    #render alternative names when available
    alt_names_html = render_list(work.get("alt_names"), "item-name")
    
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Titles</span>")
        html.append(alt_names_html)
        html.append("</div>")


    #render the authority identifier when both its value and type are available
    idno_value = first(work.get("idno_value"))
    idno_type = first(work.get("idno_type"))

    if idno_value and idno_type:
        html.append("<div class='entry-block entry-idno'>")
        html.append("<span class='subheading'>Authority Identifier</span>")
        html.append(f"<span class='item-name'>{esc(idno_value)} ({esc(idno_type)})</span>")
        html.append("</div>")


    #render associated dates and activities related to dates
    dates_text = work.get("dates_text")
    dates_from = work.get("dates_from")  
    dates_to = work.get("dates_to")
    activity = work.get("activity")

    #date ranges are added as data attributes for frontend filtering
    #while the activity type is displayed alongside the formatted date text
    #the date fields are stored as parallel lists, with each position
    #representing one date/activity combination
    if dates_text and dates_from and dates_to and activity:
        html.append("<div class='entry-block entry-dates'>")
        html.append("<span class='subheading'>Associated Dates</span>")
        
        for text, date_from, date_to, act in zip(dates_text, dates_from, dates_to, activity):
            html.append(f"<span data-from='{esc(date_from)}' data-to='{esc(date_to)}' class='item-name'>{esc(text)} ({esc(act)})</span>")
        html.append("</div>")


    #render associated persons, sorted alphabetically by person name
    #each person is linked to the corresponding person index entry
    #and includes the person's configured work role
    editor_names = work.get("editor_text")
    editor_keys = work.get("editor_key")
    editor_roles = work.get("editor_role")

    #the person fields are stored as parallel lists, with each position
    #representing one person/role combination
    if editor_names and editor_keys and editor_roles:
        editors = sorted(zip(editor_names, editor_keys, editor_roles), key=lambda x: normalize_for_sort(x[0]))

        html.append("<div class='entry-block entry-editors'>")
        html.append("<span class='subheading'>Associated Persons</span>")

        #display each person's name and identifier together with
        #their role in the work
        for name, key, role in editors:
            #look up the role in the configured work roles
            #the configured values are based on MARC relator codes
            #and provide the human-readable role displayed in the index
            role = ROLES.get(role)
            url = make_entity_url("person", key, single_page=False)    
            html.append(f"<a href='{esc(url)}' target='person-index' class='item-name'>{esc(name)} ({esc(key)}) (role: {esc(role)})</a>")
        
        html.append("</div>")


    #render persons referenced in the work, sorted alphabetically
    #by the displayed person name
    #each referenced person is linked to the person index entry and
    #includes the reference type and any optional note
    person_refs = work.get("person_ref")
    person_refs = sorted(person_refs, key=lambda x: normalize_for_sort(x.get("parent_text")))

    if person_refs:
        html.append("<div class='entry-block entry-person-refs'>")
        html.append("<span class='subheading'>Persons Referenced in Work</span>")
        
        for person_ref in person_refs:
            key = person_ref.get("key")
            person_name = person_ref.get("parent_text")
            person_type = person_ref.get("role")
            note = person_ref.get("note")
            
            url = make_entity_url("person", key, single_page=False)
            
            #display the person's name, identifier and reference type
            #include the optional note when one has been recorded for
            #the reference relationship
            if note:
                html.append(f"<a href='{esc(url)}' target='person-index' class='item-name'>{esc(person_name)} ({esc(key)}) (reference type: {esc(person_type)}) (notes: {esc(note)})</a>")

            else:
                html.append(f"<a href='{esc(url)}' target='person-index' class='item-name'>{esc(person_name)} ({esc(key)}) (reference type: {esc(person_type)})</a>")
        
        html.append("</div>")  


    #render other works referenced in the work, sorted alphabetically
    #by the displayed work title
    #each referenced work is linked to its work index entry and
    #includes the reference type and any optional note
    work_refs = work.get("work_ref")
    work_refs = sorted(work_refs, key=lambda x: normalize_for_sort(x.get("parent_text")))

    if work_refs:
        html.append("<div class='entry-block entry-work-refs'>")
        html.append("<span class='subheading'>Other Works Referenced in Work</span>")
        for work_ref in work_refs:
            key = work_ref.get("key")
            work_name = work_ref.get("parent_text")
            work_type = work_ref.get("role")
            note = work_ref.get("note")

            url = make_entity_url("work", key, single_page=False)
            
            #display the work's title, identifier and reference type
            #include the optional note when one has been recorded for
            #the reference relationship
            if note:
                html.append(f"<a href='{esc(url)}' target='work-index' class='item-name'>{esc(work_name)} ({esc(key)}) (reference type: {esc(work_type)}) (notes: {esc(note)})</a>")
            else:
                html.append(f"<a href='{esc(url)}' target='work-index' class='item-name'>{esc(work_name)} ({esc(key)}) (reference type: {esc(work_type)})</a>")
        
        html.append("</div>")    


    #render associated places, sorted alphabetically by place name
    #each place is linked to the place index entry and may include
    #an optional connection role describing the relationship
    places = work.get("pub_place")
    places = sorted(places, key=lambda x: normalize_for_sort(x.get("placeName")))

    if places:
        html.append("<div class='entry-block entry-places'>")
        html.append("<span class='subheading'>Associated Places</span>")
        for place in places:
            key = place.get("key")
            place_name = place.get("placeName")
            role = place.get("role")
            
            url = make_entity_url("place", key, single_page=False)
            
            #display the place's name and identifier
            #include the connection role when one has been recorded
            if role:
                html.append(f"<a href='{esc(url)}' role='{esc(role)}' target='place-index' class='item-name'>{esc(place_name)} ({esc(key)}) (connection: {esc(role)})</a>")
            else:
                html.append(f"<a href='{esc(url)}' target='place-index' class='item-name'>{esc(place_name)} ({esc(key)})</a>")
        
        html.append("</div>")


    #render genres, sorted alphabetically by genre
    #genres may also represent commentary relationships to another work,
    #in which case the related work is linked to its work index entry
    genres = work.get("genre")
    genres = sorted(genres, key=lambda x: normalize_for_sort(x.get("parent_text")))

    if genres:
        html.append("<div class='entry-block entry-genre'>")
        html.append("<span class='subheading'>Genre</span>")
        for genre in genres:
            source = genre.get("source")
            linked_key = genre.get("key")
            linked_text = genre.get("parent_text")

            #render commentary genres as links to the referenced work
            #only create the link when both the referenced work identifier
            #and displayed work title are available
            if source == "commentary" and linked_key and linked_text:
                url = make_entity_url("work", linked_key, single_page=False)
                
                #display the commentary relationship followed by a link
                #to the referenced work's index entry
                html.append(f"<div class='item-name'>")
                html.append(f"  <span>commentary on </span>")
                html.append(f"  <a href='{esc(url)}' target='work-index'>{esc(linked_text)} ({esc(linked_key)})</a>")
                html.append(f"</div>")
            
            #render all other genres as plain text when they do not
            #represent a linked commentary relationship
            else:
                html.append(f"<div class='item-name'>{esc(linked_text)}</div>")
        
        html.append("</div>")


    #render subjects as a list of item names
    subject_html = render_list(work.get("subject"), "item-name")
    if subject_html:
        html.append("<div class='entry-block entry-subject'>")
        html.append("<span class='subheading'>Subject</span>")
        html.append(subject_html)
        html.append("</div>")


    #render notes when available
    notes_html = render_list(work.get("notes"), "item-name")
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")


    #render bibliographical references using configured reference formatting
    #references are sorted alphabetically by their source text
    references = work.get("reference")
    references = sorted(references, key=lambda x: normalize_for_sort(x.get("reference")))

    if references:
        html.append("<div class='entry-block entry-reference'>")
        html.append("<span class='subheading'>References</span>")
        for reference in references:
            ref_raw = reference.get("parent_text")

            #look up the reference in the configured bibliography so that
            #the formatted HTML text and reference identifier can be used
            ref = REFS.get(ref_raw, None)

            if ref:
                ref_text = ref.get("html", ref_raw)
                ref_id = ref.get("identifier")
            else:
                #fall back to the original reference text when no
                #configured bibliography entry is available
                ref_text = ref_raw
                ref_id = None

            ref_vol = reference.get("subtype")
            ref_page = reference.get("n")

            data_attrs = ""
            data_attrs_contents = ""

            #add volume and page information as data attributes for
            #frontend filtering and as visible text alongside the reference
            if ref_vol and ref_page:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)}, Page(s) {esc(ref_page)})"

            #include volume information when no page number is supplied
            elif ref_vol:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)})"

            #include page information when no volume number is supplied
            elif ref_page:
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Page(s) {esc(ref_page)})"

            #use a link when the reference has a configured identifier
            #otherwise render the reference as plain text
            tag = "a" if ref_id else "span"

            link_attr = f" href='{make_reference_url(ref_id)}' target='reference-page'" if ref_id else ""

            attrs = f"{link_attr}{data_attrs}"

            html.append(
                f"<{tag} class='item-name reference'{attrs}>"
                f"{ref_text}"
                f"{data_attrs_contents if (ref_vol or ref_page) else ''}"
                f"</{tag}>"
            )
        
        html.append("</div>")

    html.append("</div>")
    return "\n".join(html)

def render_inscription(inscription):
    """
    Render an inscription as an expandable index entry.

    Builds the HTML for a single inscription, including the standard entry
    header and any available descriptive, chronological, relational, and
    bibliographical information.

    Includes:
        - Alternative titles
        - Associated dates
        - Donors
        - Associated persons
        - Recipient
        - Language
        - Donation type
        - Material
        - Locations
        - Notes
        - Bibliographical references

    Args:
        inscription (dict): Inscription data loaded from the entity index.

    Returns:
        str: HTML string representing the complete inscription index entry.
    """

    html = []

    #basic entry information used for the index heading and anchor
    xml_id = inscription.get("xml_id")
    name = first(inscription.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")

    #render the standard entry heading and details container
    html.append(render_entry_header(xml_id, name))
    html.append("<div class='item-details'>")

    
    #render alternative names when available
    alt_names_html = render_list(inscription.get("alt_names"), "item-name")
    
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Titles</span>")
        html.append(alt_names_html)
        html.append("</div>")


    #render date periods using the human-readable text and machine-readable
    #date range stored in data attributes for frontend use
    dates_text = inscription.get("dates_text")
    dates_from = inscription.get("dates_from")  
    dates_to = inscription.get("dates_to")
    
    #keep each displayed date paired with its corresponding start
    #and end dates when generating the individual date entries
    if dates_text and dates_from and dates_to:
        html.append("<div class='entry-block entry-dates'>")
        html.append("<span class='subheading'>Associated Dates</span>")
        for text, date_from, date_to in zip(dates_text, dates_from, dates_to):
            html.append(f"<span data-from='{esc(date_from)}' data-to='{esc(date_to)}' class='item-name'>{esc(text)}</span>")
        html.append("</div>")


    #render donors, sorted alphabetically by donor name
    #each donor is linked to the corresponding person index entry
    donors = inscription.get("donor")
    donors = sorted(donors, key=lambda x: normalize_for_sort(x.get("persName")))

    if donors:
        html.append("<div class='entry-block entry-donors'>")
        html.append("<span class='subheading'>Donors</span>")
        for donor in donors:
            key = donor.get("persName_key")
            donor_name = donor.get("persName")

            #skip incomplete donor records that cannot be linked
            if not key or not donor_name:
                continue

            url = make_entity_url("person", key, single_page=False)

            html.append(f"<a href='{esc(url)}' target='person-index' class='item-name'>{esc(donor_name)} ({esc(key)})</a>")

        html.append("</div>")


    #render associated persons, sorted alphabetically by person name
    #each person is linked to the corresponding person index entry
    #and includes the person's inscription role
    assoc_persons = inscription.get("assoc_person")
    assoc_persons = sorted(assoc_persons, key=lambda x: normalize_for_sort(x.get("persName")))

    if assoc_persons:
        html.append("<div class='entry-block entry-assoc-persons'>")
        html.append("<span class='subheading'>Associated Persons</span>")
        for assoc_person in assoc_persons:
            key = assoc_person.get("persName_key")
            assoc_person_name = assoc_person.get("persName")
            role = assoc_person.get("persName_role")

            #skip incomplete association records where the person
            #identifier, name, or role is unavailable
            if not key or not assoc_person_name or not role:
                continue

            url = make_entity_url("person", key, single_page=False)

            html.append(f"<a href='{esc(url)}' target='person-index' class='item-name'>{esc(assoc_person_name)} ({esc(key)}) (role: {esc(role)})</a>")

        html.append("</div>")    

    
    #render recipients as a list of item names
    recipient_html = render_list(inscription.get("recipient"), "item-name")
    
    if recipient_html:
        html.append("<div class='entry-block entry-recipient'>")
        html.append("<span class='subheading'>Recipient</span>")
        html.append(recipient_html)
        html.append("</div>")

    
    #render languages as a list of item names
    language_html = render_list(inscription.get("language"), "item-name")
    
    if language_html:
        html.append("<div class='entry-block entry-language'>")
        html.append("<span class='subheading'>Language</span>")
        html.append(language_html)
        html.append("</div>")

    
    #render donation types as a list of item names
    donation_type_html = render_list(inscription.get("donation_type"), "item-name")
    
    if donation_type_html:
        html.append("<div class='entry-block entry-donation-type'>")
        html.append("<span class='subheading'>Donation Type</span>")
        html.append(donation_type_html)
        html.append("</div>")

    
    #render materials as a list of item names
    material_html = render_list(inscription.get("material"), "item-name")
    
    if material_html:
        html.append("<div class='entry-block entry-material'>")
        html.append("<span class='subheading'>Material</span>")
        html.append(material_html)
        html.append("</div>")


    #render associated places, sorted alphabetically by place name
    #location names and identifiers are kept paired using zip so that
    #each place remains associated with its correct identifier and links
    #to the corresponding place index entry
    location_names = inscription.get("location")
    location_keys = inscription.get("location_key")
    
    if location_names and location_keys:
        locations = sorted(zip(location_names, location_keys), key=lambda x: normalize_for_sort(x[0]))

        html.append("<div class='entry-block entry-locations'>")
        html.append("<span class='subheading'>Locations</span>")

        for place_name, key in locations:
            
            url = make_entity_url("place", key, single_page=False)

            html.append(
                f"<a href='{esc(url)}' target='place-index' class='item-name'>"
                f"{esc(place_name)} ({esc(key)})"
                f"</a>"
            )

        html.append("</div>")


    #render notes when available
    notes_html = render_list(inscription.get("notes"), "item-name")
    
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")

    #render bibliographical references using configured reference formatting
    #references are sorted alphabetically by their source text
    references = inscription.get("reference")
    references = sorted(references, key=lambda x: normalize_for_sort(x.get("reference")))

    if references:
        html.append("<div class='entry-block entry-reference'>")
        html.append("<span class='subheading'>References</span>")
        for reference in references:
            ref_raw = reference.get("parent_text")

            #look up the reference in the configured bibliography so that
            #the formatted HTML text and reference identifier can be used
            ref = REFS.get(ref_raw, None)

            if ref:
                ref_text = ref.get("html", ref_raw)
                ref_id = ref.get("identifier")
            else:
                #fall back to the original reference text when no
                #configured bibliography entry is available
                ref_text = ref_raw
                ref_id = None

            ref_vol = reference.get("subtype")
            ref_page = reference.get("n")

            data_attrs = ""
            data_attrs_contents = ""

            #add volume and page information as data attributes for
            #frontend filtering and as visible text alongside the reference
            if ref_vol and ref_page:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)}, Page(s) {esc(ref_page)})"

            #include volume information when no page number is supplied
            elif ref_vol:
                data_attrs += f" data-vol='{esc(ref_vol)}'"
                data_attrs_contents += f" (Volume {esc(ref_vol)})"

            #include page information when no volume number is supplied
            elif ref_page:
                data_attrs += f" data-page='{esc(ref_page)}'"
                data_attrs_contents += f" (Page(s) {esc(ref_page)})"

            #use a link when the reference has a configured identifier
            #otherwise render the reference as plain text
            tag = "a" if ref_id else "span"

            link_attr = f" href='{make_reference_url(ref_id)}' target='reference-page'" if ref_id else ""

            attrs = f"{link_attr}{data_attrs}"

            html.append(
                f"<{tag} class='item-name reference'{attrs}>"
                f"{ref_text}"
                f"{data_attrs_contents if (ref_vol or ref_page) else ''}"
                f"</{tag}>"
            )
        
        html.append("</div>")

    html.append("</div>")
    return "\n".join(html)   


def render_index_sections(items_by_letter, entity_tag):
    """
    Render grouped entity entries as a single index list.

    Iterates through the alphabet in order and uses the entity type to
    dispatch each item to its corresponding renderer.

    Args:
        items_by_letter (dict): Entity entries grouped by initial letter.
        entity_tag (str): Entity type used to select the appropriate renderer.

    Returns:
        str: HTML string containing the complete index list.
    """

    #map each entity type to its corresponding rendering function
    renderers = {
        "person": render_person,
        "work": render_work,
        "place": render_place,
        "inscription": render_inscription
    }

    html = []
    
    #use a single list container for all entries
    html.append("<ul class='index-list list-unstyled' id='all-entries'>")

    #iterate through the alphabet in order so that entries remain grouped
    #according to their initial letter in the rendered index
    for letter in string.ascii_uppercase:
        if letter in items_by_letter:
            for item_data in items_by_letter[letter]:
                
                #select the renderer for the current entity type and use it
                #to build the HTML for the individual index entry
                html_renderer = renderers[entity_tag]
                rendered_html = html_renderer(item_data)
                
                #store the entry's initial letter as a data attribute so
                #that frontend filtering can show or hide entries by letter
                first_letter = letter
                
                html.append(
                    f"<li class='letter-entry' data-letter='{first_letter}'>{rendered_html}</li>"
                )
    
    html.append("</ul>")

    return "\n".join(html)


def render_page(title, body_html):
    """
    Render a complete HTML page.

    Args:
        title (str): Page title displayed in the <title> tag and as an <h1>.
        body_html (list[str]): List of HTML strings to be inserted
            inside the <main> element.

    Returns:
        list[str]: A list of HTML strings representing a complete
        HTML document.
    """

    #build the document structure as a list of HTML strings so that
    #individual page components can be assembled and rendered together
    return [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"  <title>{esc(title)}</title>",

        #load the index-specific stylesheet and Bootstrap
        "  <link rel='stylesheet' href='../static/css/index.css'>",
        "   <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css' rel='stylesheet' integrity='sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65' crossorigin='anonymous'>",
        "</head>",
        "<body>",

        #keep the index controls fixed at the top of the page while
        #the user scrolls through the entity entries
        "<div class='sticky-top bg-white border-bottom'>",
        "<div class='index-header d-flex flex-column flex-md-row justify-content-between align-items-md-center'>",
        f"  <h1>{esc(title)}</h1>",

        #render the search controls and alphabetical navigation used
        #to filter and navigate the index entries
        *render_search(),
        "</div>",
        *render_alphabet_nav(),

        #provide a container for the frontend to display the current
        #number of visible results after filtering
        "  <div id='entry-count' class='px-2 py-2 results-num'></div>",
        "</div>",

        #insert the rendered index entries into the main page content
        "  <main>",
        body_html,
        "  </main>",

        #load Bootstrap's JavaScript bundle followed by the custom
        #index JavaScript responsible for search and filtering behaviour
        "  <script src='https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js' integrity='sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4' crossorigin='anonymous'></script>",
        "  <script src='../static/js/index.js'></script>",
        "</body>",
        "</html>",
    ]

