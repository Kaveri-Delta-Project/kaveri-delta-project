import string
import html
from config import ROLES

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
        "      <button type='button' id='search-clear' class='btn btn-secondary search-button'>Clear</button>",
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
    Render a list of items as a vertical block using <div> for each item.

    Args:
        items (list[str]): The items to render.
        css_class (str, optional): CSS class applied to each <div> item.

    Returns:
        str: HTML string for the list, or empty string if no items.
    """
    if not items:
        return ''

    cls_attr = f' class="{esc(css_class)}"' if css_class else ''
    html = []
    for item in items:
        html.append(f"<div{cls_attr}>{esc(item)}</div>")

    return '\n'.join(html)


def make_entity_url(entity_type, key, single_page=True):
    if single_page:
        return f"#{esc(key)}"
    return f"{entity_type}_index.html#{esc(key)}"


def render_place(place):
    
    html = []
    
    xml_id = place.get("xml_id")
    name = first(place.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")

    html.append("<div class='entry-header'>")
    if name:
        html.append(f"<span class='entry-title'>{esc(name)}</span>")
        html.append(f"<span class='entry-id'>({esc(xml_id)})</span>")
    else:
        html.append(f"<span class='entry-title'>{esc(xml_id)}</span>")
    html.append("  <button class='toggle' aria-label='Show details'>▸</button>")
    html.append("</div>")

    html.append("<div class='item-details'>")


    alt_names_html = render_list(place.get("alt_names"), "item-name")
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Place Names</span>")
        html.append(alt_names_html)
        html.append("</div>")

    idno_value = first(place.get("idno_value"))
    idno_type = first(place.get("idno_type"))
    if idno_value and idno_type:
        html.append("<div class='entry-block entry-idno'>")
        html.append("<span class='subheading'>Authority Identifier</span>")
        html.append(f"<span class='item-name'>{esc(idno_value)} ({esc(idno_type)})</span>")
        html.append("</div>")

    coordinates = first(place.get("coords"))
    if coordinates:
        html.append("<div class='entry-block entry-coords'>")
        html.append("<span class='subheading'>Coordinates</span>")
        html.append(f"<span class='item-name'>{esc(coordinates)}</span>")
        html.append("</div>")


    place_types_html = render_list(place.get("place_type"), "item-name")
    if place_types_html:
        html.append("<div class='entry-block entry-place-types'>")
        html.append("<span class='subheading'>Place Types</span>")
        html.append(place_types_html)
        html.append("</div>")

    linked_data = place.get("linked_data")
    if linked_data:
        html.append("<div class='entry-block entry-place-pers'>")
        html.append("<span class='subheading'>Affiliated Persons</span>")
        for affil in linked_data:
            key = affil.get("xml_id")
            person_name = affil.get("name")
            affil_from = affil.get("from")
            affil_to = affil.get("to")
            affil_role = affil.get("role")

            if not key or not person_name:
                continue
            
            url = make_entity_url("person", key, single_page=False)

            data_attrs = ""
            data_attrs_contents = ""

            if affil_from and affil_to:
                data_attrs += f" data-from='{esc(affil_from)}'"
                data_attrs += f" data-to='{esc(affil_to)}'"
                if affil_from == affil_to:
                    data_attrs_contents += f" ({esc(affil_from)})"
                else:
                    data_attrs_contents += f" ({esc(affil_from)}-{esc(affil_to)})"
            
            if affil_role:
                data_attrs += f" data-role='{esc(affil_role)}'"
                data_attrs_contents += f" (connection: {esc(affil_role)})"

            if affil_from or affil_to or affil_role:
                html.append(
                    f"<a href='{url}' target='_blank' class='item-name' {data_attrs}>"
                    f"{esc(person_name)} ({esc(key)}) {data_attrs_contents}</a>"
                )
            else:
                html.append(
                    f"<a href='{url}' target='_blank' class='item-name'>{esc(person_name)} ({esc(key)})</a>"
                )

    notes_html = render_list(place.get("notes"), "item-name")
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")

    html.append("</div>")
    return "\n".join(html)



def render_person(person):
    
    html = []

    xml_id = person.get("xml_id")
    name = first(person.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")

    html.append("<div class='entry-header'>")
    if name:
        html.append(f"<span class='entry-title'>{esc(name)}</span>")
        html.append(f"<span class='entry-id'>({esc(xml_id)})</span>")
    else:
        html.append(f"<span class='entry-title'>{esc(xml_id)}</span>")
    html.append("  <button class='toggle' aria-label='Show details'>▸</button>")
    html.append("</div>")

    html.append("<div class='item-details'>")

    alt_names_html = render_list(person.get("alt_names"), "item-name")
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Names</span>")
        html.append(alt_names_html)
        html.append("</div>")     


    gender = person.get("sex")
    if gender:
        html.append("<div class='entry-block entry-gender'>")
        html.append("<span class='subheading'>Gender</span>")
        html.append(f"<span class='item-name'>{esc(gender)}</span>")
        html.append("</div>")

    relationships = person.get("relationship")
    if relationships:
        html.append("<div class='entry-block entry-relationships'>")
        html.append("<span class='subheading'>Related Persons</span>")
        for rel in relationships:
            key = rel["key"]
            url = make_entity_url("person", key, single_page=True)
            connection = rel["type"]
            rel_name = rel["label"]
            html.append(f"<div class='item-name'>")
            html.append(f"  <span>relationship: {esc(connection)} of</span>")
            html.append(f"  <a href='{esc(url)}' target='_blank'>{esc(rel_name)} ({esc(key)})</a>")
            html.append(f"</div>")
        html.append("</div>")


    idno_value = first(person.get("idno_value"))
    idno_type = first(person.get("idno_type"))
    if idno_value and idno_type:
        html.append("<div class='entry-block entry-idno'>")
        html.append("<span class='subheading'>Authority Identifier</span>")
        html.append(f"<span class='item-name'>{esc(idno_value)} ({esc(idno_type)})</span>")
        html.append("</div>")


    birth_text = first(person.get("birth_text"))
    birth_num = first(person.get("birth_when"))
    if birth_text and birth_num:
        html.append("<div class='entry-block entry-birth'>")
        html.append("<span class='subheading'>Birth Date</span>")
        html.append(f"<span data-when='{esc(birth_num)}' class='item-name'>{esc(birth_text)}</span>")
        html.append("</div>")

    death_text = first(person.get("death_text"))
    death_num = first(person.get("death_when"))
    if death_text and death_num:
        html.append("<div class='entry-block entry-death'>")
        html.append("<span class='subheading'>Death Date</span>")
        html.append(f"<span data-when='{esc(death_num)}' class='item-name'>{esc(death_text)}</span>")
        html.append("</div>")

    floruit_text = first(person.get("floruit_text"))
    floruit_from = first(person.get("floruit_from"))  
    floruit_to = first(person.get("floruit_to"))
    if floruit_text and floruit_from and floruit_to:
        html.append("<div class='entry-block entry-floruit'>")
        html.append("<span class='subheading'>Floruit (Period of Activity)</span>")
        html.append(f"<span data-from='{esc(floruit_from)}' data-to='{esc(floruit_to)}' class='item-name'>{esc(floruit_text)}</span>")
        html.append("</div>")

    affiliations = person.get("affiliations")
    if affiliations:
        html.append("<div class='entry-block entry-affils'>")
        html.append("<span class='subheading'>Affiliated Places</span>")
        for affil in affiliations:
            key = affil.get("key")
            place_name = affil.get("placeName")
            affil_from = affil.get("from")
            affil_to = affil.get("to")
            affil_role = affil.get("role")

            if not key or not place_name:
                continue

            url = make_entity_url("place", key, single_page=False)

            data_attrs = ""
            data_attrs_contents = ""
            if affil_from and affil_to:
                data_attrs += f" data-from='{esc(affil_from)}'"
                data_attrs += f" data-to='{esc(affil_to)}'"
                if affil_from == affil_to:
                    data_attrs_contents += f" ({esc(affil_from)})"
                else:    
                    data_attrs_contents += f" ({esc(affil_from)}-{esc(affil_to)})"
            if affil_role:
                data_attrs += f" data-role='{esc(affil_role)}'"
                data_attrs_contents += f" (connection: {esc(affil_role)})"

            if affil_from or affil_to or affil_role:
                html.append(f"<a href='{esc(url)}' target='_blank' class='item-name' {data_attrs}>{esc(place_name)} ({esc(key)}) {data_attrs_contents}</a>")
            else:
                html.append(f"<a href='{esc(url)}' target='_blank' class='item-name'>{esc(place_name)} ({esc(key)})</a>")
        html.append("</div>")

    linked_data = person.get("linked_data")
    if linked_data:
        html.append("<div class='entry-block entry-person-works'>")
        html.append("<span class='subheading'>Associated Works</span>")
        for work in linked_data:
            key = work.get("xml_id")
            title = work.get("title")
            role = ROLES.get(work.get("role"))

            if not key or not title:
                continue

            url = make_entity_url("work", key, single_page=False)

            # Append role if available
            role_text = f" (role: {esc(role)})" if role else ""
            html.append(
                f"<a href='{esc(url)}' target='_blank' class='item-name'>{esc(title)} ({esc(key)}){role_text}</a>"
            )
        html.append("</div>")

    notes_html = render_list(person.get("notes"), "item-name")
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")

    html.append("</div>")
    return "\n".join(html)    


def render_manuscript(manuscript):

    html = []

    xml_id = manuscript.get("xml_id")
    name = first(manuscript.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")

    html.append("<div class='entry-header'>")
    if name:
        html.append(f"<span class='entry-title'>{esc(name)}</span>")
        html.append(f"<span class='entry-id'>({esc(xml_id)})</span>")
    else:
        html.append(f"<span class='entry-title'>{esc(xml_id)}</span>")
    html.append("  <button class='toggle' aria-label='Show details'>▸</button>")
    html.append("</div>")

    html.append("<div class='item-details'>")


    alt_names_html = render_list(manuscript.get("alt_names"), "item-name")
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Manuscript Names</span>")
        html.append(alt_names_html)
        html.append("</div>")

    repository = first(manuscript.get("repository"))
    if repository:
        html.append("<div class='entry-block entry-repo'>")
        html.append("<span class='subheading'>Repository</span>")
        html.append(f"<span class='item-name'>{esc(repository)}</span>")
        html.append("</div>")

    classmark = first(manuscript.get("idno"))
    if classmark:
        html.append("<div class='entry-block entry-idno'>")
        html.append("<span class='subheading'>Classmark</span>")
        html.append(f"<span class='item-name'>{esc(classmark)}</span>")
        html.append("</div>")

    works = manuscript.get("work")
    if works:
        html.append("<div class='entry-block entry-works'>")
        html.append("<span class='subheading'>Associated Works</span>")
        for work in works:
            key = work.get("title_key")
            url = make_entity_url("work", key, single_page=False)
            work_title = work.get("title")
            html.append(f"<a href='{esc(url)}' target='_blank' class='item-name'>{esc(work_title)} ({esc(key)})</a>")
        html.append("</div>")


    physical_html = render_list(manuscript.get("phys_desc"), "item-name")
    if physical_html:
        html.append("<div class='entry-block entry-phys'>")
        html.append("<span class='subheading'>Physical Description</span>")
        html.append(physical_html)
        html.append("</div>")


    date_text = first(manuscript.get("date_text"))
    date_from = first(manuscript.get("date_from"))
    date_to = first(manuscript.get("date_to"))
    if date_text and date_from and date_to:
        html.append("<div class='entry-block entry-dates'>")
        html.append("<span class='subheading'>Manuscript Creation Period</span>")
        html.append(f"<span data-from='{esc(date_from)}' data-to='{esc(date_to)}' class='item-name'>{esc(date_text)}</span>")
        html.append("</div>")

   
    places = manuscript.get("place")
    place_keys = manuscript.get("place_key")
    if places and place_keys:
        html.append("<div class='entry-block entry-places'>")
        html.append("<span class='subheading'>Associated Places</span>")
        for place, key in zip(places, place_keys):
            url = make_entity_url("place", key, single_page=False)
            html.append(f"<a href='{esc(url)}' target='_blank' class='item-name'>{esc(place)} ({esc(key)})</a>")
        html.append("</div>")


    persons = manuscript.get("person")
    if persons:
        html.append("<div class='entry-block entry-persons'>")
        html.append("<span class='subheading'>Associated Persons</span>")
        for person in persons:
            key = person.get("persName_key")
            role = ROLES.get(person.get("role"))
            url = make_entity_url("person", key, single_page=False)
            person_name = person.get("persName")
            html.append(f"<a href='{esc(url)}' target='_blank' class='item-name'>{esc(person_name)} ({esc(key)}) (role: {esc(role)})</a>")
        html.append("</div>")


    notes_html = render_list(manuscript.get("notes"), "item-name")
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")

    html.append("</div>")
    return "\n".join(html)   


def render_work(work):

    html = []

    xml_id = work.get("xml_id")
    name = first(work.get("name"))

    html.append(f"<div class='index-entry' id='{esc(xml_id)}'>")

    html.append("<div class='entry-header'>")
    if name:
        html.append(f"<span class='entry-title'>{esc(name)}</span>")
        html.append(f"<span class='entry-id'>({esc(xml_id)})</span>")
    else:
        html.append(f"<span class='entry-title'>{esc(xml_id)}</span>")
    html.append("  <button class='toggle' aria-label='Show details'>▸</button>")
    html.append("</div>")

    html.append("<div class='item-details'>")

    alt_names_html = render_list(work.get("alt_names"), "item-name")
    if alt_names_html:
        html.append("<div class='entry-block entry-alt-names'>")
        html.append("<span class='subheading'>Alternative Titles</span>")
        html.append(alt_names_html)
        html.append("</div>")

    idno_value = first(work.get("idno_value"))
    idno_type = first(work.get("idno_type"))
    if idno_value and idno_type:
        html.append("<div class='entry-block entry-idno'>")
        html.append("<span class='subheading'>Authority Identifier</span>")
        html.append(f"<span class='item-name'>{esc(idno_value)} ({esc(idno_type)})</span>")
        html.append("</div>")


    dates_text = work.get("dates_text")
    dates_from = work.get("dates_from")  
    dates_to = work.get("dates_to")
    activity = work.get("activity")
    if dates_text and dates_from and dates_to and activity:
        html.append("<div class='entry-block entry-dates'>")
        html.append("<span class='subheading'>Associated Dates</span>")
        for text, date_from, date_to, act in zip(dates_text, dates_from, dates_to, activity):
            html.append(f"<span data-from='{esc(date_from)}' data-to='{esc(date_to)}' class='item-name'>{esc(text)} ({esc(act)})</span>")
        html.append("</div>")


    editor_names = work.get("editor_text")
    editor_keys = work.get("editor_key")
    editor_roles = work.get("editor_role")
    if editor_names and editor_keys and editor_roles:
        html.append("<div class='entry-block entry-editors'>")
        html.append("<span class='subheading'>Associated Persons</span>")
        for name, key, role in zip(editor_names, editor_keys, editor_roles):
            role = ROLES.get(role)
            url = make_entity_url("person", key, single_page=False)
            html.append(f"<a href='{esc(url)}' target='_blank' class='item-name'>{esc(name)} ({esc(key)}) (role: {esc(role)})</a>")
        html.append("</div>")

    places = work.get("pub_place")
    if places:
        html.append("<div class='entry-block entry-places'>")
        html.append("<span class='subheading'>Associated Places</span>")
        for place in places:
            key = place.get("key")
            place_name = place.get("placeName")
            role = place.get("role")
            url = make_entity_url("place", key, single_page=False)
            if role:
                html.append(f"<a href='{esc(url)}' role='{esc(role)}' target='_blank' class='item-name'>{esc(place_name)} ({esc(key)}) (connection: {esc(role)})</a>")
            else:
                html.append(f"<a href='{esc(url)}' target='_blank' class='item-name'>{esc(place_name)} ({esc(key)})</a>")
        html.append("</div>")

    genres = work.get("genre")
    if genres:
        html.append("<div class='entry-block entry-genre'>")
        html.append("<span class='subheading'>Genre</span>")
        for genre in genres:
            type = genre.get("type")
            source = genre.get("source")
            linked_key = genre.get("key")
            linked_text = genre.get("parent_text")

            if source == "commentary" and linked_key and linked_text:
                url = make_entity_url("work", linked_key, single_page=False)
                html.append(f"<div class='item-name'>")
                html.append(f"  <span>commentary on </span>")
                html.append(f"  <a href='{esc(url)}' target='_blank'>{esc(linked_text)} ({esc(linked_key)})</a>")
                html.append(f"</div>")
            else:
                html.append(f"<div class='item-name'>{esc(linked_text)}</div>")
        html.append("</div>")


    subject_html = render_list(work.get("subject"), "item-name")
    if subject_html:
        html.append("<div class='entry-block entry-subject'>")
        html.append("<span class='subheading'>Subject</span>")
        html.append(subject_html)
        html.append("</div>")

    notes_html = render_list(work.get("notes"), "item-name")
    if notes_html:
        html.append("<div class='entry-block entry-notes'>")
        html.append("<span class='subheading'>Notes</span>")
        html.append(notes_html)
        html.append("</div>")

    html.append("</div>")

    html.append("</div>")
    return "\n".join(html)   


def render_index_sections(items_by_letter, entity_tag):
    renderers = {
        "person": render_person,
        "manuscript": render_manuscript,
        "work": render_work,
        "place": render_place
    }

    html = []
    # Single list container for all entries
    html.append("<ul class='index-list list-unstyled' id='all-entries'>")

    for letter in string.ascii_uppercase:
        if letter in items_by_letter:
            for item_data in items_by_letter[letter]:
                html_renderer = renderers[entity_tag]
                rendered_html = html_renderer(item_data)
                # Add data-letter for filtering
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
    return [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "  <meta charset='UTF-8'>",
        f"  <title>{title}</title>",
        "  <link rel='stylesheet' href='../static/css/index.css'>",
        "   <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css' rel='stylesheet' integrity='sha384-rbsA2VBKQhggwzxH7pPCaAqO46MgnOM80zW1RWuH61DGLwZJEdK2Kadq2F9CUG65' crossorigin='anonymous'>",
        "</head>",
        "<body>",
        "<div class='sticky-top bg-white border-bottom'>",
        "<div class='index-header d-flex justify-content-between align-items-center'>",
        f"  <h1>{title}</h1>",
        *render_search(),
        "</div>",
        *render_alphabet_nav(),
        "</div>",
        "  <main>",
        body_html,
        "  </main>",
        "  <script src='https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js' integrity='sha384-kenU1KFdBIe4zVF0s0G1M5b4hcpxyD9F7jL+jjXkk+Q2h455rYXK/7HAuoJl+0I4' crossorigin='anonymous'></script>",
        "  <script src='../static/js/index.js'></script>",
        "</body>",
        "</html>",
    ]

