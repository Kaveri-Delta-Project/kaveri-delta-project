import folium
from folium import Element, IFrame, CssLink, JavascriptLink
from config import OUTPUT_DIR, CSS_PATH, JS_PATH


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "kaveri_map.html"

#read CSS from relative path
with open(CSS_PATH) as f:
    POPUP_CSS = f.read()

def make_scrollable_popup(html_content, width=300, height=200):
    """
    Create a scrollable Folium popup with CSS injected from a relative file.
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
    iframe = IFrame(html=full_html, width=width, height=height)
    return folium.Popup(iframe, max_width=width)


def get_svg(shape_type, color):
    """Return SVG marker for each place type with consistent fill and black stroke."""
    if shape_type in ["city", "town", "village", "other"]:
        # Circle
        return f"""
        <svg width="16" height="16">
            <circle cx="8" cy="8" r="7" style="fill:{color};stroke:black;stroke-width:1"/>
        </svg>
        """
    elif shape_type == "matha":
        # Square
        return f"""
        <svg width="16" height="16">
            <rect x="1" y="1" width="14" height="14" style="fill:{color};stroke:black;stroke-width:1"/>
        </svg>
        """
    elif shape_type == "temple":
        # Triangle
        return f"""
        <svg width="16" height="16">
            <polygon points="8,0 16,16 0,16" style="fill:{color};stroke:black;stroke-width:1"/>
        </svg>
        """
    else:
        # Pentagon
        return f"""
        <svg width="16" height="16">
            <polygon points="8,0 16,6 12,16 4,16 0,6" style="fill:{color};stroke:black;stroke-width:1"/>
        </svg>
        """


def generate_popup_html(place):
    place_link = f"https://kaveri-delta-project.github.io/kaveri-delta-project/indexes/place_index.html#{place['place_id']}"
    pers_place_link = f"https://kaveri-delta-project.github.io/kaveri-delta-project/search_results?q={place['place_id']}&category=person"
    work_place_link = f"https://kaveri-delta-project.github.io/kaveri-delta-project/search_results?q={place['place_id']}&category=work"

    html = f'<div class="popup-title">{place["place_name"]}</div>'
    metadata_html = ""

    # Alternative names
    if place.get("alt_name"):
        alt_names_clean = [a for a in place["alt_name"] if a]
        if alt_names_clean:
            alt_html = "".join(f"<li>{a}</li>" for a in alt_names_clean)
            metadata_html += f"""
            <details>
                <summary><b>Alternative Place Names</b></summary>
                <ul>{alt_html}</ul>
            </details>
            """

    # Coordinates
    metadata_html += f"<li><b>Coordinates:</b> {place['lat']:.5f}, {place['lon']:.5f}</li>"

    # Works & People
    num_works = place.get("num_works", 0)
    num_people = place.get("num_people", 0)

    if num_works > 0:
        metadata_html += (
            f"<li><b>Associated Works:</b> "
            f"<a href='{work_place_link}' target='_blank'>{num_works}</a></li>"
        )
    else:
        metadata_html += "<li><b>Associated Works:</b> None</li>"

    if num_people > 0:
        metadata_html += (
            f"<li><b>Associated People:</b> "
            f"<a href='{pers_place_link}' target='_blank'>{num_people}</a></li>"
        )
    else:
        metadata_html += "<li><b>Associated People:</b> None</li>"

    metadata_html += f"""
    <li><b>Place Record:</b>
        <a href="{place_link}" target="_blank">View full record</a>
    </li>
    """

    html += f"""
    <details>
        <summary class="popup-subtitle">Place Metadata</summary>
        <ul>{metadata_html}</ul>
    </details>
    """

    return f'<div class="popup-content">{html}</div>'


def generate_legend_html(type_colors):
    legend_html = '<div class="map-legend">'
    legend_html += "<b>Place Types</b>"

    for t, color in type_colors.items():
        shape = get_svg(t, color)
        legend_html += f"""
        <div class='legend-item'>
            {shape}
            <span class='legend-item-text'>{t.capitalize()}</span>
        </div>
        """

    legend_html += "</div>"
    return legend_html


def create_kaveri_map(nodes_df, rivers_gdf, output_path=OUTPUT_PATH):
    """
    Create a Folium map with rivers, place markers, labels, and legend.
    nodes_df must contain 'lat', 'lon', 'type_filled', 'popup_html', 'place_name'.
    rivers_gdf is a GeoDataFrame of river geometries.
    """
    # Base map
    m = folium.Map(location=[11.0, 78.5], zoom_start=7, tiles=None)

    # Custom panes
    folium.map.CustomPane("rivers", z_index=400).add_to(m)
    folium.map.CustomPane("places", z_index=600).add_to(m)
    folium.map.CustomPane("labels", z_index=650).add_to(m)

    # Satellite layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri", name="Satellite", overlay=False, control=True
    ).add_to(m)

    # Rivers
    folium.GeoJson(
        rivers_gdf,
        name="Kaveri Delta Waterways",
        style_function=lambda f: {"color": "#1f78b4", "weight": 2, "opacity": 0.7},
        pane="rivers"
    ).add_to(m)

    # Labels
    labels = {
        "Kaveri River": [(10.919786, 78.498563), (10.873635, 79.049462)],
        "Kollidam River": [(11.081690, 79.409749)],
        "Kumbakonam": [(10.962807, 79.384513)],
        "Mannargudi": [(10.664908, 79.448423)],
        "Thanjavur": [(10.792270, 79.136594)],
        "Madurai": [(9.928649, 78.122132)]
    }
    
    for item, coords_list in labels.items():
        size_class = "label-large" if item in ["Kaveri River", "Madurai", "Thanjavur"] else "label-small"

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

    # Place markers
    type_colors = {
        "city": "rgba(228, 26, 28, 0.7)",
        "town": "rgba(255, 127, 0, 0.7)",
        "village": "rgba(255, 217, 47, 0.7)",
        "matha": "rgba(166, 86, 40, 0.7)",
        "temple": "rgba(148, 103, 189, 0.7)",
        "other": "rgba(247, 129, 191, 0.7)"
    }

    placetype_fgs = {t: folium.FeatureGroup(name=f"Place Type: {t.capitalize()}") for t in type_colors}

    for idx, row in nodes_df.iterrows():
        color = type_colors.get(row["type_filled"], type_colors["other"])
        shape_svg = get_svg(row["type_filled"], color)

        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.DivIcon(html=shape_svg, icon_size=(20, 20)),
            popup=make_scrollable_popup(row["popup_html"], width=250, height=100),
            tooltip=row["place_name"],
            pane="places"
        ).add_to(placetype_fgs[row["type_filled"]])

    for fg in placetype_fgs.values():
        fg.add_to(m)

    # Layer control
    folium.LayerControl(collapsed=False, position="bottomright").add_to(m)

    # Link external CSS
    m.get_root().header.add_child(CssLink(CSS_PATH))

    # Link external JS
    m.get_root().html.add_child(JavascriptLink(JS_PATH))

    # Legend
    legend_html = generate_legend_html(type_colors)
    m.get_root().html.add_child(Element(legend_html))

    # Save
    m.save(output_path)
    print(f"Map saved to {output_path}")
    return m