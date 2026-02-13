import string

#HTML rendering helpers

def render_alphabet_nav():
    """
    Render an alphabetical navigation bar (A–Z).

    Returns:
        list[str]: A list of HTML strings representing a navigation
        element containing buttons for each uppercase letter.
    """
    html = ["  <nav class='alphabet' id='alphabet-nav'>"]
    for letter in string.ascii_uppercase:
        html.append(f"    <button data-letter='{letter}'>{letter}</button>")
    html.append("  </nav>")
    return html


def render_index_sections(items_by_letter, include_keys, name_key="name", id_key="id"):
    """
    Render grouped index sections organized by initial letter.

    Each section corresponds to a letter (A–Z) and contains a list of
    indexed items. Each item displays a name, identifier, and expandable
    detail sections for related data.

    Args:
        items_by_letter (dict[str, list[dict]]): Mapping of uppercase
            letters to lists of item dictionaries.
        include_keys (list[str]): Keys in each item whose values should
            be rendered as detail lists.
        name_key (str, optional): Dictionary key used for the display
            name of each item. Defaults to "name".
        id_key (str, optional): Dictionary key used for the identifier
            of each item. Defaults to "id".

    Returns:
        list[str]: A list of HTML strings representing the rendered
        index sections, including no entry placeholders for letters
        without
    """
    html = []

    for letter in string.ascii_uppercase:

        html.append(f"    <section class='letter-group' id='letter-{letter}'>")
        html.append(f"      <h2>{letter}</h2>")
        html.append("      <ul class='index-list'>")


        if letter in items_by_letter:
            for item in sorted(items_by_letter[letter], key=lambda d: d[name_key]):
                html.append("        <li class='index-item'>")
                html.append("          <div class='item-header'>")
                html.append(
                    f"            <span class='item-name'><strong>{item[name_key]} ({item[id_key]})</strong></span>"
                )
                html.append("            <button class='toggle' aria-label='Show details'>▸</button>")
                html.append("          </div>")
                html.append("          <div class='item-details'>")

                for key in include_keys:
                    values = item.get(key)
                    if not values:
                        continue

                    html.append(f"            <h4>{key.title()}</h4>")
                    html.append(f"            <ul class='{key}'>")

                    for identifier, name in sorted(set(values), key=lambda t: t[1]):
                        html.append(f"              <li>{name} ({identifier})</li>")

                    html.append("            </ul>")

                html.append("          </div>")
                html.append("        </li>")
        else:
            html.append("        <li class='no-items'>No entries under this letter.</li>")

        html.append("      </ul>")
        html.append("    </section>")

    return html


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
        "</head>",
        "<body>",
        f"  <h1>{title}</h1>",
        *render_alphabet_nav(),
        "  <main>",
        *body_html,
        "  </main>",
        "  <script src='../static/js/index.js'></script>",
        "</body>",
        "</html>",
    ]
