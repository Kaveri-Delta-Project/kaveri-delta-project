import os
import json
import re
import string
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from config import ENTITY_CONFIG, NSMAP, KEYS_TO_LOWERCASE
from utils import (load_entity, 
            load_or_create_entity, 
            handle_deletions, 
            write_entity_to_file, 
            group_items_alphabetically,
            normalize_for_sort
            )
from handlers import person, place, work, inscription
from index_utils import (load_index, 
            get_index_file, 
            update_index_entry, 
            rebuild_entity_index, 
            delete_index_entry, 
            delete_connection_entry, 
            update_connection_files, 
            related_delete,
            remove_all_connections_from_index
            )

#maps entity types to their section-specific handlers
#used by update_section to dispatch form submissions
SECTION_HANDLERS = {
    "person": person.SECTION_HANDLERS,
    "place": place.SECTION_HANDLERS,
    "work": work.SECTION_HANDLERS,
    "inscription": inscription.SECTION_HANDLERS
}

app = Flask(__name__)

#secret key for session + flash messages
app.config["SECRET_KEY"] = "b7f8e1c9d3a142f59e6a8b2c4d1f7a6e"
#make Python's zip() available in Jinja templates
app.jinja_env.globals.update(zip=zip)


@app.route("/<entity>/refresh", methods=["POST"])
def refresh_entity_index(entity):
    if entity not in ENTITY_CONFIG:
        return "Unknown entity", 404

    rebuild_entity_index(entity)

    return redirect(url_for("entity_index", entity=entity))

@app.route("/")
def index():
    """
    Render the homepage overview of all entity types.

    For each entity defined in ENTITY_CONFIG, load its index data
    (a list of records from JSON) and pass the aggregated results
    to the template for display.

    Returns:
        HTML page of all entity types and index entries.
    """
    all_entities = {}

    for entity in ENTITY_CONFIG:
        all_entities[entity] = load_index(entity)

    return render_template("index_overview.html", all_entities=all_entities)

@app.route("/<entity>/index")
def entity_index(entity):
    """
    Render the index page for a specific entity type.

    Loads the entity's index data from JSON, optionally filters results
    using a normalized search query, and groups items alphabetically
    for display.

    Query Parameters:
        q (str, optional): Search term used to filter entity names.

    Returns:
        HTML page showing grouped and optionally filtered entity entries.
    """
    if entity not in ENTITY_CONFIG:
        return "Unknown entity", 404

    #get search query from query parameters and normalize for consistency
    query = request.args.get("q", "").strip().lower()
    norm_query = normalize_for_sort(query)

    #resolve path to JSON index file for entity
    path = get_index_file(entity)
    
    #load index items into list 
    items = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)


    #apply filtering only if a query exists
    if norm_query:
        #build regex for whole-word match using normalized query
        pattern = re.compile(rf"\b{re.escape(norm_query)}\b", re.IGNORECASE)

        #filter items using regex match on normalized names
        #only items containing whole word matches from query are kept
        items = [
            item
            for item in items
            if item.get("name")
            and pattern.search(normalize_for_sort(item["name"]))
        ]
                  
    #group items alphabetically in dictionary format
    grouped = group_items_alphabetically(items)

    #render template with entity, grouped results, and original query
    return render_template("entity_index.html", entity=entity, grouped_items=grouped, query=query)

@app.route("/api/<entity>/search")
def api_entity_search(entity):
    """
    API endpoint for searching entities of a given type.

    This endpoint loads a prebuilt JSON index file for the specified entity
    and returns a filtered list of items matching the query string.

    Query Parameters:
        q (str): Search term used for prefix matching against entity names

    Returns:
        JSON list of matching items, each typically containing:
            - name (str)
            - xml_id (str or int)
    """    
    if entity not in ENTITY_CONFIG:
        return jsonify([]), 404

    #get search query from query parameters and normalize for consistency
    query = request.args.get("q", "").strip().lower()
    norm_query = normalize_for_sort(query)
    
    #resolve path to JSON index file for entity
    path = get_index_file(entity)    
    
    #load index items into list 
    items = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)

    #if search query exists, filter items using prefix matching
    #only items whose normalized name starts with the normalized query are kept
    if norm_query:
        items = [
            item for item in items
            if item.get("name")
            and normalize_for_sort(item["name"]).startswith(norm_query)
        ]

    #sort alphabetically
    items.sort(key=lambda x: normalize_for_sort(x.get("name") or x["xml_id"]))
    
    #return JSON response to frontend (used by autocomplete UI)
    return jsonify(items)


@app.route("/<entity>/new", methods=["GET", "POST"])
def new_entity(entity):
    """
    Render and handle the form for creating a new entity.

    GET:
        - Renders an empty form for the specified entity type.

    POST:
        - Delegates form submission to update_entity() for processing
          (e.g. validation, saving data).

    Parameters:
        entity (str): The entity type (must exist in ENTITY_CONFIG)

    Returns:
        - HTML form (GET)
        - Result of update_entity() (POST)
        - 404 if entity is not recognised
    """
    config = ENTITY_CONFIG.get(entity)
    if not config:
        return "Unknown entity", 404

    if request.method == "POST":
        return update_entity(entity, config)

    return render_template(f"forms/{entity}.html", data=None, entity=entity)


@app.route("/<entity>/<xml_id>", methods=["GET", "POST"])
def edit_entity(entity, xml_id):
    """
    Render and handle the form for editing an existing entity.

    GET:
        - Loads entity data from its XML file
        - Renders the form pre-populated with existing values

    POST:
        - Submits updated form data to update_entity() for processing

    Parameters:
        entity (str): Entity type (must exist in ENTITY_CONFIG)
        xml_id (str): Unique identifier for the entity (used as filename)

    Returns:
        - HTML form populated with entity data (GET)
        - Result of update_entity() (POST)
        - 404 if entity or XML file is not found
    """
    config = ENTITY_CONFIG.get(entity)
    if not config:
        return "Unknown entity", 404

    file_path = os.path.join(config["dir"], f"{xml_id}.xml")

    if not os.path.exists(file_path):
        return f"{entity} not found", 404

    if request.method == "POST": 
        return update_entity(entity, config, xml_id=xml_id)

    #load entity data for pre-populating the form
    data = load_entity(file_path, entity, config["mapping"], NSMAP)

    return render_template(f"forms/{entity}.html", xml_id=xml_id, data=data, entity=entity)

@app.route("/<entity>/<xml_id>/delete", methods=["POST"])
def delete_file(entity, xml_id):
    """
    Delete an existing entity and remove all related index references.

    Parameters:
        entity (str): Entity type (must exist in ENTITY_CONFIG)
        xml_id (str): Unique identifier of the entity (used as filename)

    Returns:
        Redirect to entity index page on success
        404 if entity or file is not found
    """
    config = ENTITY_CONFIG.get(entity)
    if not config:
        return "Unknown entity", 404

    file_path = os.path.join(config["dir"], f"{xml_id}.xml")

    if not os.path.exists(file_path):
        return f"{entity} not found", 404

    #remove XML file
    os.remove(file_path)

    #remove references to this entity from all entity indexes
    for ent in ENTITY_CONFIG.keys():
        remove_all_connections_from_index(ent, xml_id)

    #remove the entity from its own index
    delete_index_entry(entity, xml_id)

    #redirect back to the entity index page
    return redirect(url_for("entity_index", entity=entity))


def update_section(entity, entity_elem, form_data, context):
    """
    Handles updating a section of the entity based on the form data.
    Returns True if a handler was called, False if no handler found.
    """
    section = form_data.get("section")
    handler = SECTION_HANDLERS.get(entity, {}).get(section)
    
    if not handler:
        app.logger.warning(f"Unknown section: {section}")
        return False

    return handler(entity_elem, context, form_data)
    

def update_entity(entity, config, xml_id=None):
    """
    Process form submission for creating or updating an entity.

    Handles:
    - Input normalization
    - Deletion requests
    - Section updates via handlers
    - Writing XML to file
    - Updating indexes and relationships

    Always redirects back to the edit view after processing.
    """

    #extract form data from POST request (submitted edit form)
    form_data = request.form.to_dict(flat=True)

    #normalise identifiers to lowercase
    for key in KEYS_TO_LOWERCASE:
        if key in form_data and form_data[key]:
            form_data[key] = form_data[key].strip().lower()

    #load existing TEI entity XML or create a new one from template
    #add to context along with identifier, file path, tree, root, entity element
    context = load_or_create_entity(
        entity_name=entity,
        entity_dir=config["dir"],
        template_path=config["template"],
        xml_id=xml_id,
        nsmap=NSMAP
    )
    
    if context is None:
        return f"{entity} not found", 404

    entity_elem = context["entity_elem"]

    #handle deletion requests before updates to file
    #using context, entity element and form data to specify deletion
    if handle_deletions(entity_elem, form_data, context):
        
        #persist deletion changes to xml file
        write_entity_to_file(context)

        #update index for this entity
        update_index_entry(entity, context["xml_id"])

        #remove any corresponding connected elements, e.g. related persons
        if form_data.get("connection") == "related":
            related_delete(xml_id, entity, form_data, config)
        #remove index entry for entity connected to another entity, e.g. person connected to place id(s)
        if form_data.get("connection") == "cascade":
            delete_connection_entry(xml_id, form_data)
        
        #redirect back to edit page (GET)
        return redirect(url_for("edit_entity", entity=context["entity_name"], xml_id=context["xml_id"]))

    #handle update requests via appropriate section handler
    #data validation and writing to appropriate section of xml file
    update_section(entity, entity_elem, form_data, context)

    #persist updates to xml file
    write_entity_to_file(context)

    #update index for this entity
    update_index_entry(entity, context["xml_id"])
    #when entity name changes, ensure all linked entities update the new name
    update_connection_files(entity, context["xml_id"])

    #redirect back to edit page (GET)
    return redirect(url_for("edit_entity", entity=context["entity_name"], xml_id=context["xml_id"]))


