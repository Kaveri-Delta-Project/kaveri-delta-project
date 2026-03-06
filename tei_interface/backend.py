import os
import json
import re
import string
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from config import ENTITY_CONFIG, NSMAP, KEYS_TO_LOWERCASE
from utils import load_entity, load_or_create_entity, handle_deletions, write_entity_to_file, group_items_alphabetically
from handlers import person, place, work, manuscript
from index_utils import (load_index, 
            get_index_file, 
            update_index_entry, 
            rebuild_entity_index, 
            delete_index_entry, 
            delete_connection_entry, 
            update_connection_files, 
            related_delete
            )

SECTION_HANDLERS = {
    "person": person.SECTION_HANDLERS,
    "place": place.SECTION_HANDLERS,
    "work": work.SECTION_HANDLERS,
    "manuscript": manuscript.SECTION_HANDLERS
}

app = Flask(__name__)
app.config["SECRET_KEY"] = "b7f8e1c9d3a142f59e6a8b2c4d1f7a6e"
app.jinja_env.globals.update(zip=zip)


@app.route("/<entity>/refresh", methods=["POST"])
def refresh_entity_index(entity):
    if entity not in ENTITY_CONFIG:
        return "Unknown entity", 404

    rebuild_entity_index(entity)

    return redirect(url_for("entity_index", entity=entity))

@app.route("/")
def index():
    all_entities = {}

    for entity in ENTITY_CONFIG:
        all_entities[entity] = load_index(entity)

    return render_template("index_overview.html", all_entities=all_entities)

@app.route("/<entity>/index")
def entity_index(entity):
    if entity not in ENTITY_CONFIG:
        return "Unknown entity", 404

    path = get_index_file(entity)
    items = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)

    query = request.args.get("q", "").strip().lower()

    if query:
        # Use regex to match whole words (case-insensitive)
        pattern = re.compile(rf"\b{re.escape(query)}\b", re.IGNORECASE)
        filtered_items = []
        for item in items:
            if item.get("name") and pattern.search(item["name"]):
                filtered_items.append(item)
        items = filtered_items

    #sort alphabetically by name, fallback to xml_id
    items.sort(key=lambda x: (x.get("name") or x["xml_id"]).lower())

    grouped = {letter: [] for letter in string.ascii_uppercase}
    grouped["#"] = []

    for item in items:
        name = item.get("name")

        if name and name[0].upper() in grouped:
            letter = name[0].upper()
        else:
            letter = "#"

        grouped[letter].append(item)

    return render_template("entity_index.html", entity=entity, grouped_items=grouped, query=query)

@app.route("/api/<entity>/search")
def api_entity_search(entity):
    if entity not in ENTITY_CONFIG:
        return jsonify([]), 404

    query = request.args.get("q", "").strip().lower()
    path = get_index_file(entity)
    items = []

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)

    # filter by name containing query
    if query:
        items = [item for item in items if item.get("name") and query in item["name"].lower()]

    # optionally sort alphabetically
    items.sort(key=lambda x: x.get("name", x["xml_id"]).lower())

    return jsonify(items)


@app.route("/<entity>/new", methods=["GET", "POST"])
def new_entity(entity):
    config = ENTITY_CONFIG.get(entity)
    if not config:
        return "Unknown entity", 404

    if request.method == "POST":
        return update_entity(entity, config)

    return render_template(f"forms/{entity}.html", data=None, entity=entity)


@app.route("/<entity>/<xml_id>", methods=["GET", "POST"])
def edit_entity(entity, xml_id):

    config = ENTITY_CONFIG.get(entity)
    if not config:
        return "Unknown entity", 404

    file_path = os.path.join(config["dir"], f"{xml_id}.xml")

    if not os.path.exists(file_path):
        return f"{entity} not found", 404

    if request.method == "POST": 
        print("Form submitted:", request.form)
        return update_entity(entity, config, xml_id=xml_id)

    data = load_entity(file_path, entity, config["mapping"], NSMAP)

    return render_template(f"forms/{entity}.html", xml_id=xml_id, data=data, entity=entity)

@app.route("/<entity>/<xml_id>/delete", methods=["POST"])
def delete_file(entity, xml_id):
    config = ENTITY_CONFIG.get(entity)
    if not config:
        return "Unknown entity", 404

    file_path = os.path.join(config["dir"], f"{xml_id}.xml")

    if not os.path.exists(file_path):
        return f"{entity} not found", 404

    os.remove(file_path)
    delete_index_entry(entity, xml_id)

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

    form_data = request.form.to_dict(flat=True)

    for key in KEYS_TO_LOWERCASE:
        if key in form_data and form_data[key]:
            form_data[key] = form_data[key].strip().lower()

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

    if handle_deletions(entity_elem, form_data, context):
        write_entity_to_file(context)
        update_index_entry(entity, context["xml_id"])
        if form_data.get("connection") == "related":
            related_delete(xml_id, entity, form_data, config)
        if form_data.get("connection") == "cascade":
            delete_connection_entry(xml_id, form_data)
        
        return redirect(url_for("edit_entity", entity=context["entity_name"], xml_id=context["xml_id"]))

    update_section(entity, entity_elem, form_data, context)

    write_entity_to_file(context)
    update_index_entry(entity, context["xml_id"])
    update_connection_files(entity, context["xml_id"])

    return redirect(url_for("edit_entity", entity=context["entity_name"], xml_id=context["xml_id"]))


