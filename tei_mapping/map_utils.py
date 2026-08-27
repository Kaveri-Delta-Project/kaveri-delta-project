import folium
from folium import Element, IFrame, CssLink, JavascriptLink
from config import CSS_PATH, BASE_DIR

#output location for the generated Folium map
OUTPUT_PATH =  BASE_DIR / "tei_mapping" / "map.html"

#fixed labels displayed on the map (river names and their coordinates)
LABELS = {
    "Kaveri River": [(10.919786, 78.498563), (10.873635, 79.049462)],
    "Kollidam River": [(11.081690, 79.409749)]
}

#labels displayed with larger text for major places/features
LARGE_LABELS = {"Kaveri River", "Madurai", "Thanjavur"}

#colour palette used for each place type on the map
TYPE_COLOURS = {
    "city/town": "rgba(228, 26, 28, 0.7)",
    "settlement": "rgba(255, 217, 47, 0.7)",
    "matha": "rgba(166, 86, 40, 0.7)",
    "temple": "rgba(148, 103, 189, 0.7)",
    "other": "rgba(247, 129, 191, 0.7)"
}


#load popup CSS so it can be embedded in Folium popups
with open(CSS_PATH) as f:
    POPUP_CSS = f.read()


def make_scrollable_popup(html_content, width=300, height=200):
    """
    Create a scrollable Folium popup with embedded CSS styling.

    Args:
        html_content (str): HTML content to display inside the popup.
        width (int, optional): Width of the popup iframe in pixels.
        height (int, optional): Height of the popup iframe in pixels.

    Returns:
        folium.Popup:
            Folium popup containing the supplied HTML content in a
            fixed-size iframe.
    """

    full_html = f"""
    <html>
    <head>
        <style>
        {POPUP_CSS}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    #wrap the HTML in a Folium iframe and popup
    iframe = IFrame(html=full_html, width=width, height=height)
    return folium.Popup(iframe, max_width=width)


def get_svg(shape_type, colour, size, works, people, inscriptions):
    """
    Return an SVG marker for a map node.

    Args:
        shape_type (str): Place type used to determine the marker shape.
        colour (str): Fill colour for the marker.
        size (int): Width and height of the SVG marker.
        works (int): Number of associated works, stored as a data attribute for scaling.
        people (int): Number of associated people, stored as a data attribute for scaling.
        inscriptions (int): Number of associated inscriptions, stored as a data attribute for scaling.

    Returns:
        str:
            SVG markup for the map marker.
    """
    
    shape_type = shape_type.lower()

    #use a circle for cities/towns, settlements, and other places
    if shape_type in ["city/town", "settlement", "other"]:
        return f"""
        <svg class="map-node"
             data-works="{works}"
             data-people="{people}"
             data-inscriptions="{inscriptions}"
             data-type="{shape_type}"
             width="{size}" height="{size}">
            <circle cx="{size/2}" cy="{size/2}" r="{(size/2)-1}"
            style="fill:{colour};stroke:black;stroke-width:1"/>
        </svg>
        """
    
    #use a square for mathas
    elif shape_type == "matha":
        return f"""
        <svg class="map-node"
             data-works="{works}"
             data-people="{people}"
             data-inscriptions="{inscriptions}"
             width="{size}" height="{size}">
            <rect x="1" y="1" width="{size-2}" height="{size-2}"
            style="fill:{colour};stroke:black;stroke-width:1"/>
        </svg>
        """
    
    #use a triangle for temples
    elif shape_type == "temple":
        return f"""
        <svg class="map-node"
             data-works="{works}"
             data-people="{people}"
             data-inscriptions="{inscriptions}"
             width="{size}" height="{size}">
            <polygon points="{size/2},0 {size},{size} 0,{size}"
            style="fill:{colour};stroke:black;stroke-width:1"/>
        </svg>
        """

def get_svg_legend(shape_type, colour):
    """
    Return a fixed-size SVG marker for the map legend.

    Args:
        shape_type (str): Place type used to determine the marker shape.
        colour (str): Fill colour for the marker.

    Returns:
        str:
            SVG markup for the legend marker.
    """

    shape_type = shape_type.lower()
    
    #use a circle for cities/towns, settlements, and other places
    if shape_type in ["city/town", "settlement", "other"]:
        return f"""
        <svg width="16" height="16">
            <circle cx="8" cy="8" r="7" style="fill:{colour};stroke:black;stroke-width:1"/>
        </svg>
        """

    #use a square for mathas
    elif shape_type == "matha":
        return f"""
        <svg width="16" height="16">
            <rect x="1" y="1" width="14" height="14" style="fill:{colour};stroke:black;stroke-width:1"/>
        </svg>
        """
    
    #use a triangle for temples
    elif shape_type == "temple":
        return f"""
        <svg width="16" height="16">
            <polygon points="8,0 16,16 0,16" style="fill:{colour};stroke:black;stroke-width:1"/>
        </svg>
        """


def generate_place_links(place):
    """
    Generate links to the place record and associated entities.

    Args:
        place (dict): Place data containing the place ID and name.

    Returns:
        dict:
            Dictionary containing links for the place, associated people,
            works, and inscriptions.
    """

    place_id = place["place_id"]
    place_name = place["place_name"]

    return {
        "place": f"https://kaveri-delta-project.github.io/kaveri-delta-project/indexes/place_index.html#{place_id}",
        "person": f"https://kaveri-delta-project.github.io/kaveri-delta-project/search_results?q={place_name} {place_id}&category=person",
        "work": f"https://kaveri-delta-project.github.io/kaveri-delta-project/search_results?q={place_name} {place_id}&category=work",
        "inscription": f"https://kaveri-delta-project.github.io/kaveri-delta-project/search_results?q={place_name} {place_id}&category=inscription",
    }


def generate_alt_names_html(place):
    """
    Generate HTML displaying a place's alternative names.

    Args:
        place (dict): Place data containing alternative names.

    Returns:
        str:
            HTML for the alternative names, or an empty string if none exist.
    """

    if not place.get("alt_name"):
        return ""

    #remove empty values from the list of alternative names
    alt_names_clean = [name for name in place["alt_name"] if name]

    if not alt_names_clean:
        return ""

    alt_html = "".join(f"<li>{name}</li>" for name in alt_names_clean)

    return f"""
    <details>
        <summary><b>Alternative Place Names</b></summary>
        <ul>{alt_html}</ul>
    </details>
    """


def generate_association_html(label, count, link):
    """
    Generate HTML for an associated entity count and link.

    Args:
        label (str): Label describing the associated entity type.
        count (int): Number of associated entities.
        link (str): URL for the associated entity search.

    Returns:
        str:
            HTML displaying the count as a link, or "None" if the count is zero.
    """

    if count > 0:
        return (
            f"<li><b>{label}:</b> "
            f"<a href='{link}' target='_blank'>{count}</a></li>"
        )

    return f"<li><b>{label}:</b> None</li>"


def generate_popup_html(place):
    """
    Generate HTML for a place popup containing its metadata and links.

    Args:
        place (dict): Place data containing place names, alternative names, 
            coordinates, and associated works, people, and inscriptions.

    Returns:
        str:
            HTML markup for the place popup.
    """
    
    #generate the links used for the place record and associated entities
    links = generate_place_links(place)

    html = f'<div class="popup-title">{place["place_name"]}</div>'
    metadata_html = ""

    #add alternative place names when they are available
    metadata_html += generate_alt_names_html(place)

    #add the place coordinates to the metadata
    metadata_html += f"<li><b>Coordinates:</b> {place['lat']:.5f}, {place['lon']:.5f}</li>"

    #retrieve the number of works, people, and inscriptions associated with the place
    num_works = place.get("num_works", 0)
    num_people = place.get("num_people", 0)
    num_inscriptions = place.get("num_inscriptions", 0)

    #add links to the associated works, people, and inscriptions
    metadata_html += generate_association_html(
        "Associated Works",
        num_works,
        links["work"]
    )

    metadata_html += generate_association_html(
        "Associated People",
        num_people,
        links["person"]
    )

    metadata_html += generate_association_html(
        "Associated Inscriptions",
        num_inscriptions,
        links["inscription"]
    )

    #add a link to the full place record
    metadata_html += f"""
    <li><b>Place Record:</b>
        <a href="{links['place']}" target="_blank">View full record</a>
    </li>
    """

    #wrap the metadata in the popup structure
    html += f"""
    <div>
        <summary class="popup-subtitle">Place Metadata</summary>
        <ul>{metadata_html}</ul>
    </div>
    """

    return f'<div class="popup-content">{html}</div>'


def generate_legend_html(type_colours):
    """
    Generate HTML for the map legend showing each place type and its marker.

    Args:
        type_colours (dict): Dictionary mapping place types to marker colours.

    Returns:
        str:
            HTML markup for the map legend.
    """

    #start the legend container and add its heading
    legend_html = '<div class="map-legend">'
    legend_html += "<b>Place Types</b>"

    #add a legend item for each place type and its corresponding marker shape
    for t, colour in type_colours.items():
        shape = get_svg_legend(t, colour)
        legend_html += f"""
        <div class='legend-item'>
            {shape}
            <span class='legend-item-text'>{t.capitalize()}</span>
        </div>
        """
    
    #close the legend container and return the completed HTML
    legend_html += "</div>"
    return legend_html 


def generate_scale_selector_html():
    """
    Generate HTML for the map control used to select node scaling.

    Returns:
        str:
            HTML markup for the node scaling selector.
    """
    
    #start the selector container and add the available scaling options
    selector_html = '<div class="scale-selector">'
    selector_html += f""" 
                    <b>Scale nodes by:</b><br>
                      <select class="scale-menu" id="scaleSelector">
                        <option value="normal">No Filter</option>
                         <option value="works">Works</option>
                         <option value="people">People</option>
                         <option value="inscriptions">Inscription</option>
                      </select>
                      """
    
    #close the selector container and return the completed HTML
    selector_html += "</div>"
    return selector_html                


def create_kaveri_map(nodes_df, gdf_layers, output_path=OUTPUT_PATH):
    """
    Create a Folium map with geographic layers, place markers, labels,
    popups, layer controls, and map interface elements.

    Args:
        nodes_df (pandas.DataFrame): Dataframe containing place data for mapping
            and node metadata.
        gdf_layers (dict): Dictionary containing the GeoDataFrames used for
            the river and Tamil Nadu boundary layers.
        output_path (str or Path, optional): File path where the generated
            HTML map will be saved.

    Returns:
        folium.Map:
            The generated Folium map object.
    """


    #create the base Folium map centred on the Kaveri Delta region
    m = folium.Map(location=[11.0, 78.5], zoom_start=7, tiles=None)

    #create custom panes to control the drawing order of map layers
    folium.map.CustomPane("rivers", z_index=400).add_to(m)
    folium.map.CustomPane("tamil_nadu", z_index=450).add_to(m)
    folium.map.CustomPane("places", z_index=600).add_to(m)
    folium.map.CustomPane("labels", z_index=650).add_to(m)

    #add the historical Survey of India map as a selectable base layer
    folium.TileLayer(
        tiles="https://geo.nls.uk/mapdata3/india-combined/{z}/{x}/{y}.png",
        attr="National Library of Scotland", name="Survey of India, 1912-1950", overlay=False, control=True,
    ).add_to(m)

    #add satellite imagery as an alternative selectable base layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri", name="Satellite", overlay=False, control=True
    ).add_to(m)

    #add the Kaveri Delta waterways to the rivers pane
    folium.GeoJson(
        gdf_layers["rivers_gdf"],
        name="Kaveri Delta Waterways",
        style_function=lambda f: {"color": "#1f78b4", "weight": 2.5, "opacity": 0.8},
        pane="rivers"
    ).add_to(m)

    #add the Tamil Nadu boundary to the map
    folium.GeoJson(
        gdf_layers["tamil_nadu_gdf"],
        name="Tamil Nadu",
        style_function=lambda f: {"color": "#f0f0f0", "weight": 2, "opacity": 0.8, "fill": False},
        pane="tamil_nadu"
    ).add_to(m)
    
    #add fixed geographic labels such as rivers and major cities
    for item, coords_list in LABELS.items():
        
        #use a larger CSS class for selected prominent labels
        size_class = "label-large" if item in LARGE_LABELS else "label-small"

        #add the label at each configured coordinate
        for coord in coords_list:
            folium.Marker(
                location=coord,
                icon=folium.DivIcon(
                    icon_size=(150,36),
                    icon_anchor=(0,0),
                    html=f'<div class="map-label {size_class}">{item}</div>'
                ),
                pane="labels"
            ).add_to(m)

    #create a separate feature group for each place type so that
    #place types can be switched on and off using the layer control
    placetype_fgs = {t: folium.FeatureGroup(name=f"Place Type: {t.capitalize()}") for t in TYPE_COLOURS}

    #create a map marker for each place in the dataset
    for _, row in nodes_df.iterrows():

        #retrieve the place type used to determine the marker shape and colour
        row_type = row["type_filled"]
        
        #if multiple types are present, use the first recognised place type
        if isinstance(row_type, list):
            row_type = next((t for t in row_type if t in placetype_fgs), None)

        #normalise the place type to lowercase for comparison
        if row_type:
            row_type = row_type.lower()

        #treat any place type containing "matha" as the matha category
        if row_type and "matha" in row_type:
            row_type = "matha"

        #use "other" when no recognised place type is available
        if not row_type or row_type not in placetype_fgs:
            row_type = "other"

        #retrieve the colour associated with the place type
        colour = TYPE_COLOURS.get(row_type, TYPE_COLOURS["other"])
        
        #set the default marker size
        size = 14

        #generate the SVG marker, including association counts as
        #data attributes for later JavaScript interaction
        shape_svg = get_svg(
            row_type,
            colour,
            size,
            row["num_works"],
            row["num_people"],
            row["num_inscriptions"]
        )

        item = row["place_name"]

        #make popups containing alternative names slightly taller
        popup_height = 205 if any(row["alt_name"]) else 180

        #use larger labels for major places and city/town markers
        size_class = "label-large" if item in LARGE_LABELS or row_type == "city/town" else "label-small"

        #add the marker to the FeatureGroup for its place type so it can be toggled
        #using the layer control
        folium.Marker(
            
            #place the marker using the latitude and longitude from the place record
            location=[row["lat"], row["lon"]],
            
            #use a custom SVG marker together with a text label
            icon=folium.DivIcon(
                html=f"""
                <div>
                    {shape_svg}
                    <div class="map-label {size_class}">{item}</div>
                </div>
                """,
                icon_size=(40, 40),
                icon_anchor=(10, 10)
            ),
            
            #attach the scrollable popup containing the place metadata
            popup=make_scrollable_popup(row["popup_html"], width=300, height=popup_height),
            
            #display the place name when the marker is hovered over
            tooltip=row["place_name"],
            
            #draw the marker in the dedicated places pane
            pane="places"
        ).add_to(placetype_fgs[row_type])


    #add each place-type feature group to the map
    for fg in placetype_fgs.values():
        fg.add_to(m)

    #add controls allowing users to toggle map layers
    folium.LayerControl(collapsed=False, position="bottomright").add_to(m)

    #link the external CSS file containing the map styling
    m.get_root().header.add_child(CssLink("static/css/map.css"))

    #link the external JavaScript file controlling map interactions
    m.get_root().html.add_child(JavascriptLink("static/js/map.js"))

    #generate and add the place-type legend to the map
    legend_html = generate_legend_html(TYPE_COLOURS)
    m.get_root().html.add_child(Element(legend_html))

    #generate and add the selector used to scale nodes by association type
    scale_selector_html = generate_scale_selector_html()
    m.get_root().html.add_child(Element(scale_selector_html))

    #save the completed map as an HTML file
    m.save(output_path)

    print(f"Map saved to {output_path}")
    
    return m