import os
import uuid
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from functools import wraps
from wger_service import WgerService

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Configuration ---
# In a real application, this would be a more secure way to handle secrets
TRAINER_PASSWORD = os.environ.get("TRAINER_PASSWORD", "password")
WGER_API_KEY = os.environ.get("WGER_API_KEY", "397683a6bb806f7e4c2d1c0b5a210a8a3f07b442")
CLIENTS_FILE = os.path.join("database", "clients.json")
EXERCISES_FILE = os.path.join("database", "exercises.json")
WORKOUT_TEMPLATES_FILE = os.path.join("database", "workout_templates.json")
WORKOUT_ASSIGNMENTS_FILE = os.path.join("database", "workout_assignments.json")
GROUPS_FILE = os.path.join("database", "groups.json")
ALERTS_FILE = os.path.join("database", "alerts.json")
PROGRAMS_FILE = os.path.join("database", "programs.json")

# Initialize WGER service
wger_service = WgerService(WGER_API_KEY)

# --- Helper Functions ---

def read_json_file(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as f:
        return json.load(f)

def write_json_file(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def read_clients():
    """Reads the clients from the JSON file."""
    data = read_json_file(CLIENTS_FILE)
    return data if isinstance(data, list) else []

def write_clients(clients):
    """Writes the clients to the JSON file."""
    write_json_file(CLIENTS_FILE, clients)

def read_exercises():
    """Reads the exercises from the JSON file."""
    data = read_json_file(EXERCISES_FILE)
    return data if isinstance(data, list) else []

def write_exercises(exercises):
    """Writes the exercises to the JSON file."""
    write_json_file(EXERCISES_FILE, exercises)

def read_workout_templates():
    """Reads the workout templates from the JSON file."""
    data = read_json_file(WORKOUT_TEMPLATES_FILE)
    return data if isinstance(data, list) else []

def write_workout_templates(templates):
    """Writes the workout templates to the JSON file."""
    write_json_file(WORKOUT_TEMPLATES_FILE, templates)

def read_workout_assignments():
    """Reads the workout assignments from the JSON file."""
    data = read_json_file(WORKOUT_ASSIGNMENTS_FILE)
    return data if isinstance(data, list) else []

def write_workout_assignments(assignments):
    """Writes the workout assignments to the JSON file."""
    write_json_file(WORKOUT_ASSIGNMENTS_FILE, assignments)

def read_groups():
    """Reads the groups from the JSON file."""
    data = read_json_file(GROUPS_FILE)
    return data if isinstance(data, list) else []

def write_groups(groups):
    """Writes the groups to the JSON file."""
    write_json_file(GROUPS_FILE, groups)

def read_alerts():
    """Reads the alerts from the JSON file."""
    data = read_json_file(ALERTS_FILE)
    return data if isinstance(data, list) else []

def write_alerts(alerts):
    """Writes the alerts to the JSON file."""
    write_json_file(ALERTS_FILE, alerts)

def read_programs():
    """Reads the programs from the JSON file."""
    data = read_json_file(PROGRAMS_FILE)
    return data if isinstance(data, list) else []

def write_programs(programs):
    """Writes the programs to the JSON file."""
    write_json_file(PROGRAMS_FILE, programs)

# --- Decorators ---

def protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == "trainer" and auth.password == TRAINER_PASSWORD):
            return jsonify({"message": "Authentication required!"}), 401
        return f(*args, **kwargs)
    return decorated

# --- API Endpoints ---

@app.route("/api/login", methods=["POST"])
def login():
    """Secure endpoint for trainer login."""
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"message": "Invalid credentials!"}), 400
    if data["username"] == "trainer" and data["password"] == TRAINER_PASSWORD:
        return jsonify({"message": "Login successful!"})
    return jsonify({"message": "Invalid credentials!"}), 401

@app.route("/api/clients", methods=["POST"])
@protected
def add_client():
    """Adds a new client."""
    data = request.get_json()
    if not data or not data.get("name") or not data.get("email"):
        return jsonify({"message": "Name and email are required!"}), 400

    clients = read_clients()
    client_id = str(uuid.uuid4())
    new_client = {
        "id": client_id,
        "name": data["name"],
        "email": data["email"],
        "unique_url": f"http://localhost:3000/client/{client_id}",
        "features": {
            "gamification": False,
            "calendar": False,
            "workout_logging": False,
            "nutrition_tracker": False,
            "nutrition_mode": "tracker",
        },
        "points": 0
    }
    clients.append(new_client)
    write_clients(clients)
    return jsonify(new_client), 201

@app.route("/api/clients", methods=["GET"])
@protected
def get_clients():
    """Lists all managed clients."""
    clients = read_clients()
    return jsonify(clients)

@app.route("/api/clients/<client_id>/features", methods=["PUT"])
@protected
def update_client_features(client_id):
    """Updates the feature toggles for a specific client."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            client["features"] = data
            write_clients(clients)
            return jsonify(client)

    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/client/<client_id>", methods=["GET"])
def get_client(client_id):
    """Gets a specific client's data."""
    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            return jsonify(client)
    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/client/<client_id>/complete_task", methods=["POST"])
def complete_task(client_id):
    """Completes a task for a client and awards points."""
    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            client["points"] += 10
            write_clients(clients)
            return jsonify(client)
    return jsonify({"message": "Client not found!"}), 404

# --- Exercise Library Endpoints ---

@app.route("/api/exercises", methods=["GET"])
def get_exercises():
    """Lists all exercises in the library."""
    exercises = read_exercises()
    return jsonify(exercises)

@app.route("/api/exercises", methods=["POST"])
@protected
def add_exercise():
    """Adds a new exercise to the library."""
    data = request.get_json()
    if not data or not data.get("name") or not data.get("instructions"):
        return jsonify({"message": "Name and instructions are required!"}), 400

    exercises = read_exercises()
    new_exercise = {
        "id": f"exr_{uuid.uuid4()}",
        "name": data["name"],
        "instructions": data["instructions"],
        "mediaUrl": data.get("mediaUrl", "")
    }
    
    if 'exercises' not in exercises:
        exercises['exercises'] = []

    exercises['exercises'].append(new_exercise)
    write_exercises(exercises)
    return jsonify({"exercise": new_exercise}), 201

# --- WGER Integration Endpoints ---

@app.route("/api/wger/sync", methods=["POST"])
@protected
def sync_wger_exercises():
    """Syncs exercises from WGER API."""
    data = request.get_json()
    limit = data.get("limit", 100) if data else 100
    
    try:
        result = wger_service.sync_exercises(limit=limit)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/api/wger/status", methods=["GET"])
@protected
def get_wger_sync_status():
    """Gets the current WGER sync status."""
    try:
        status = wger_service.get_sync_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/api/exercises/enhanced", methods=["GET"])
def get_enhanced_exercises():
    """Gets exercises with enhanced WGER data including categories, muscles, and equipment."""
    try:
        with open(EXERCISES_FILE, 'r') as f:
            data = json.load(f)
        
        # Return the full enhanced structure
        return jsonify({
            "exercises": data.get("exercises", []),
            "categories": data.get("categories", []),
            "muscles": data.get("muscles", []),
            "equipment": data.get("equipment", []),
            "sync_info": data.get("sync_info", {})
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Workout Template Endpoints ---

@app.route("/api/workout-templates", methods=["POST"])
@protected
def create_workout_template():
    """Creates a new workout template."""
    data = request.get_json()
    if not data or not data.get("name") or not data.get("exercises"):
        return jsonify({"message": "Name and exercises are required!"}), 400

    templates = read_workout_templates()
    new_template = {
        "id": f"wt_{uuid.uuid4()}",
        "name": data["name"],
        "description": data.get("description", ""),
        "exercises": data["exercises"]
    }
    templates.append(new_template)
    write_workout_templates(templates)
    return jsonify(new_template), 201

@app.route("/api/workout-templates", methods=["GET"])
@protected
def get_workout_templates():
    """Lists all workout templates."""
    templates = read_workout_templates()
    return jsonify(templates)

@app.route("/api/workout-templates/<template_id>", methods=["GET"])
@protected
def get_workout_template(template_id):
    """Gets a single workout template."""
    templates = read_workout_templates()
    template = next((t for t in templates if t["id"] == template_id), None)
    if template:
        return jsonify(template)
    return jsonify({"message": "Template not found!"}), 404

@app.route("/api/workout-templates/<template_id>", methods=["PUT"])
@protected
def update_workout_template(template_id):
    """Updates a workout template."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    templates = read_workout_templates()
    for template in templates:
        if template["id"] == template_id:
            template["name"] = data.get("name", template["name"])
            template["description"] = data.get("description", template["description"])
            template["exercises"] = data.get("exercises", template["exercises"])
            write_workout_templates(templates)
            return jsonify(template)

    return jsonify({"message": "Template not found!"}), 404

@app.route("/api/workout-templates/<template_id>", methods=["DELETE"])
@protected
def delete_workout_template(template_id):
    """Deletes a workout template."""
    templates = read_workout_templates()
    updated_templates = [t for t in templates if t["id"] != template_id]
    
    if len(updated_templates) == len(templates):
        return jsonify({"message": "Template not found!"}), 404

    write_workout_templates(updated_templates)
    return jsonify({"message": "Template deleted successfully!"})

@app.route("/api/workout-templates/<template_id>/duplicate", methods=["POST"])
@protected
def duplicate_workout_template(template_id):
    """Duplicates a workout template."""
    templates = read_workout_templates()
    template_to_duplicate = next((t for t in templates if t["id"] == template_id), None)

    if not template_to_duplicate:
        return jsonify({"message": "Template not found!"}), 404

    new_template = {
        "id": f"wt_{uuid.uuid4()}",
        "name": f"{template_to_duplicate['name']} (Copy)",
        "description": template_to_duplicate.get("description", ""),
        "notes": template_to_duplicate.get("notes", ""),
        "tags": template_to_duplicate.get("tags", []),
        "exercises": template_to_duplicate["exercises"]
    }
    templates.append(new_template)
    write_workout_templates(templates)
    return jsonify(new_template), 201

# --- Workout Assignment Endpoints ---

@app.route("/api/workout-assignments", methods=["GET", "POST"])
@protected
def assign_workout():
    if request.method == 'GET':
        assignments = read_workout_assignments()
        return jsonify(assignments)

    """Assigns a workout template to a client for a specific day."""
    data = request.get_json()
    if not data or not data.get("client_id") or not data.get("template_id") or not data.get("date"):
        return jsonify({"message": "Client ID, template ID, and date are required!"}), 400

    assignments = read_workout_assignments()
    new_assignment = {
        "id": f"wa_{uuid.uuid4()}",
        "client_id": data["client_id"],
        "template_id": data["template_id"],
        "date": data["date"],
        "logged_data": {}
    }
    assignments.append(new_assignment)
    write_workout_assignments(assignments)
    return jsonify(new_assignment), 201

@app.route("/api/client/<client_id>/workouts", methods=["GET"])
def get_client_workouts(client_id):
    """Gets all workout assignments for a specific client."""
    assignments = read_workout_assignments()
    client_assignments = [a for a in assignments if a["client_id"] == client_id]
    return jsonify(client_assignments)

@app.route("/api/workout-assignments/<assignment_id>/log", methods=["POST"])
def log_workout(assignment_id):
    """Logs a client's performance for a specific workout assignment."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    assignments = read_workout_assignments()
    for assignment in assignments:
        if assignment["id"] == assignment_id:
            assignment["logged_data"] = data
            write_workout_assignments(assignments)
            return jsonify(assignment)

    return jsonify({"message": "Workout assignment not found!"}), 404

# --- Nutrition Endpoints ---

RECIPES_FILE = os.path.join("database", "recipes.json")

def read_recipes():
    """Reads the recipes from the JSON file."""
    return read_json_file(RECIPES_FILE)

@app.route("/api/recipes", methods=["GET"])
def get_recipes():
    """Lists all recipes in the library."""
    recipes = read_recipes()
    return jsonify(recipes)

@app.route("/api/clients/<client_id>/meal-plan", methods=["POST"])
@protected
def assign_meal_plan(client_id):
    """Assigns a meal plan to a client."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            client["meal_plan"] = data
            write_clients(clients)
            return jsonify(client)

    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/clients/<client_id>/nutrition-log", methods=["POST"])
def log_nutrition(client_id):
    """Logs a client's nutrition data."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            if "nutrition_log" not in client:
                client["nutrition_log"] = []
            client["nutrition_log"].append(data)
            write_clients(clients)
            return jsonify(client)

    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/clients/<client_id>/body-stats", methods=["GET"])
def get_body_stats(client_id):
    """Gets a client's body statistics."""
    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            return jsonify(client.get("body_stats", []))
    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/clients/<client_id>/body-stats", methods=["POST"])
def add_body_stat(client_id):
    """Adds a new body statistic for a client."""
    data = request.get_json()
    if not data or not data.get("date") or not data.get("weight"):
        return jsonify({"message": "Date and weight are required!"}), 400

    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            if "body_stats" not in client:
                client["body_stats"] = []
            client["body_stats"].append(data)
            write_clients(clients)
            return jsonify(client), 201

    return jsonify({"message": "Client not found!"}), 404

# --- Progress Photo Endpoints ---

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/api/clients/<client_id>/progress-photos", methods=["POST"])
def upload_progress_photo(client_id):
    """Uploads a progress photo for a client."""
    if 'photo' not in request.files:
        return jsonify({"message": "No photo part in the request"}), 400
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({"message": "No selected photo"}), 400
    if photo:
        filename = str(uuid.uuid4()) + os.path.splitext(photo.filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)

        clients = read_clients()
        for client in clients:
            if client["id"] == client_id:
                if "progress_photos" not in client:
                    client["progress_photos"] = []
                client["progress_photos"].append({"filename": filename, "timestamp": str(datetime.now())})
                write_clients(clients)
                return jsonify({"message": "Photo uploaded successfully", "filename": filename}), 201

    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/clients/<client_id>/progress-photos", methods=["GET"])
def get_progress_photos(client_id):
    """Gets all progress photos for a client."""
    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            return jsonify(client.get("progress_photos", []))
    return jsonify({"message": "Client not found!"}), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

MESSAGES_FILE = os.path.join("database", "messages.json")
LICENSES_FILE = os.path.join("database", "licenses.json")
PROSPECTS_FILE = os.path.join("database", "prospects.json")
RESOURCES_FILE = os.path.join("database", "resources.json")

def read_messages():
    """Reads the messages from the JSON file."""    
    data = read_json_file(MESSAGES_FILE)
    return data if isinstance(data, list) else []

def write_messages(messages):
    """Writes the messages to the JSON file."""
    write_json_file(MESSAGES_FILE, messages)

def read_licenses():
    """Reads the licenses from the JSON file."""
    return read_json_file(LICENSES_FILE).get("licenses", [])

def write_licenses(licenses):
    """Writes the licenses to the JSON file."""
    write_json_file(LICENSES_FILE, {"licenses": licenses})

def read_prospects():
    """Reads the prospects from the JSON file."""
    return read_json_file(PROSPECTS_FILE).get("prospects", [])

def write_prospects(prospects):
    """Writes the prospects to the JSON file."""
    write_json_file(PROSPECTS_FILE, {"prospects": prospects})

def read_resources():
    """Reads the resources from the JSON file."""
    return read_json_file(RESOURCES_FILE).get("resources", [])

def write_resources(resources):
    """Writes the resources to the JSON file."""
    write_json_file(RESOURCES_FILE, {"resources": resources})

@app.route("/api/purchase-license", methods=["POST"])
@protected
def purchase_license():
    """Simulates a license purchase and generates a new cryptographic license key."""
    license_key = str(uuid.uuid4())
    licenses = read_licenses()
    licenses.append({"key": license_key, "issued_at": str(datetime.now()), "is_valid": True})
    write_licenses(licenses)
    return jsonify({"message": "License purchased and generated successfully!", "license_key": license_key}), 201

@app.route("/api/validate-license", methods=["POST"])
def validate_license():
    """Validates a given license key."""
    data = request.get_json()
    license_key = data.get("license_key")
    if not license_key:
        return jsonify({"message": "License key is required!"}), 400

    licenses = read_licenses()
    for license in licenses:
        if license["key"] == license_key and license["is_valid"]:
            return jsonify({"message": "License valid!", "is_valid": True}), 200
    return jsonify({"message": "License invalid or not found!", "is_valid": False}), 401

# --- Prospect Management Endpoints ---

@app.route("/api/prospects", methods=["GET"])
@protected
def get_prospects():
    """Lists all prospects."""
    prospects = read_prospects()
    return jsonify(prospects)

@app.route("/api/prospects", methods=["POST"])
@protected
def add_prospect():
    """Adds a new prospect."""
    data = request.get_json()
    if not data or not data.get("name") or not data.get("email"):
        return jsonify({"message": "Name and email are required!"}), 400

    prospects = read_prospects()
    new_prospect = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "email": data["email"],
        "status": data.get("status", "New")
    }
    prospects.append(new_prospect)
    write_prospects(prospects)
    return jsonify(new_prospect), 201

@app.route("/api/prospects/<prospect_id>/status", methods=["PUT"])
@protected
def update_prospect_status(prospect_id):
    """Updates the status of a prospect."""
    data = request.get_json()
    if not data or not data.get("status"):
        return jsonify({"message": "Status is required!"}), 400

    prospects = read_prospects()
    for prospect in prospects:
        if prospect["id"] == prospect_id:
            prospect["status"] = data["status"]
            write_prospects(prospects)
            return jsonify(prospect)

    return jsonify({"message": "Prospect not found!"}), 404

# --- Resource Management Endpoints ---

RESOURCES_UPLOAD_FOLDER = os.path.join(app.root_path, 'resources')
app.config['RESOURCES_UPLOAD_FOLDER'] = RESOURCES_UPLOAD_FOLDER

@app.route("/api/resources", methods=["POST"])
@protected
def upload_resource():
    """Uploads a new resource."""
    if 'resource' not in request.files:
        return jsonify({"message": "No resource part in the request"}), 400
    resource_file = request.files['resource']
    title = request.form.get('title')

    if resource_file.filename == '':
        return jsonify({"message": "No selected resource file"}), 400
    if not title:
        return jsonify({"message": "Resource title is required!"}), 400

    if resource_file:
        filename = str(uuid.uuid4()) + os.path.splitext(resource_file.filename)[1]
        filepath = os.path.join(app.config['RESOURCES_UPLOAD_FOLDER'], filename)
        resource_file.save(filepath)

        resources = read_resources()
        new_resource = {
            "id": str(uuid.uuid4()),
            "title": title,
            "filename": filename,
            "uploaded_at": str(datetime.now())
        }
        resources.append(new_resource)
        write_resources(resources)
        return jsonify({"message": "Resource uploaded successfully", "resource": new_resource}), 201

    return jsonify({"message": "Resource upload failed!"}), 500

@app.route("/api/resources", methods=["GET"])
@protected
def get_resources():
    """Lists all resources."""
    resources = read_resources()
    return jsonify(resources)

@app.route('/resources/<filename>')
def serve_resource(filename):
    return send_from_directory(app.config['RESOURCES_UPLOAD_FOLDER'], filename)

# --- Daily Check-in Endpoints ---

@app.route("/api/clients/<client_id>/daily-checkin", methods=["POST"])
def add_daily_checkin(client_id):
    """Adds a new daily check-in for a client."""
    data = request.get_json()
    if not data or not data.get("date"):
        return jsonify({"message": "Date is required!"}), 400

    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            if "daily_checkins" not in client:
                client["daily_checkins"] = []
            client["daily_checkins"].append(data)
            write_clients(clients)
            return jsonify(client), 201

    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/clients/<client_id>/daily-checkin", methods=["GET"])
def get_daily_checkins(client_id):
    """Gets all daily check-ins for a client."""
    clients = read_clients()
    for client in clients:
        if client["id"] == client_id:
            return jsonify(client.get("daily_checkins", []))
    return jsonify({"message": "Client not found!"}), 404

# --- Group Management Endpoints ---

@app.route("/api/groups", methods=["POST"])
@protected
def create_group():
    """Creates a new group."""
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"message": "Group name is required!"}), 400

    groups = read_groups()
    new_group = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "description": data.get("description", ""),
        "client_ids": data.get("client_ids", [])
    }
    groups.append(new_group)
    write_groups(groups)
    return jsonify(new_group), 201

@app.route("/api/groups", methods=["GET"])
@protected
def get_groups():
    """Lists all groups."""
    groups = read_groups()
    return jsonify(groups)

@app.route("/api/groups/<group_id>", methods=["GET"])
@protected
def get_group(group_id):
    """Gets a single group."""
    groups = read_groups()
    for group in groups:
        if group["id"] == group_id:
            return jsonify(group)
    return jsonify({"message": "Group not found!"}), 404

@app.route("/api/groups/<group_id>", methods=["PUT"])
@protected
def update_group(group_id):
    """Updates a group."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    groups = read_groups()
    for group in groups:
        if group["id"] == group_id:
            group["name"] = data.get("name", group["name"])
            group["description"] = data.get("description", group["description"])
            group["client_ids"] = data.get("client_ids", group["client_ids"])
            write_groups(groups)
            return jsonify(group)

    return jsonify({"message": "Group not found!"}), 404

@app.route("/api/groups/<group_id>", methods=["DELETE"])
@protected
def delete_group(group_id):
    """Deletes a group."""
    groups = read_groups()
    updated_groups = [group for group in groups if group["id"] != group_id]
    
    if len(updated_groups) == len(groups):
        return jsonify({"message": "Group not found!"}), 404

    write_groups(updated_groups)
    return jsonify({"message": "Group deleted successfully!"})

@app.route("/api/groups/<group_id>/clients", methods=["POST"])
@protected
def add_client_to_group(group_id):
    """Adds a client to a group."""
    data = request.get_json()
    client_id = data.get("client_id")
    if not client_id:
        return jsonify({"message": "Client ID is required!"}), 400

    groups = read_groups()
    for group in groups:
        if group["id"] == group_id:
            if client_id not in group["client_ids"]:
                group["client_ids"].append(client_id)
                write_groups(groups)
                return jsonify(group)
            else:
                return jsonify({"message": "Client already in group!"}), 400

    return jsonify({"message": "Group not found!"}), 404

@app.route("/api/groups/<group_id>/clients/<client_id>", methods=["DELETE"])
@protected
def remove_client_from_group(group_id, client_id):
    """Removes a client from a group."""
    groups = read_groups()
    for group in groups:
        if group["id"] == group_id:
            if client_id in group["client_ids"]:
                group["client_ids"].remove(client_id)
                write_groups(groups)
                return jsonify(group)
            else:
                return jsonify({"message": "Client not in group!"}), 400

    return jsonify({"message": "Group not found!"}), 404

# --- Alert Management Endpoints ---

@app.route("/api/alerts/check", methods=["POST"])
@protected
def check_alerts():
    """Checks for client non-adherence and creates alerts."""
    clients = read_clients()
    workouts = read_workouts()
    alerts = read_alerts()
    
    for client in clients:
        # Check for missed workouts
        assigned_workouts = [w for w in workouts if w["client_id"] == client["id"]]
        for workout in assigned_workouts:
            if not workout.get("logged_data"):
                alert_exists = any(a["type"] == "missed_workout" and a["client_id"] == client["id"] and a["details"]["workout_id"] == workout["id"] for a in alerts)
                if not alert_exists:
                    new_alert = {
                        "id": str(uuid.uuid4()),
                        "client_id": client["id"],
                        "type": "missed_workout",
                        "message": f"Client {client['name']} missed a workout on {workout['date']}.",
                        "details": {"workout_id": workout["id"]},
                        "timestamp": str(datetime.now())
                    }
                    alerts.append(new_alert)

        # Check for no recent check-ins
        if "daily_checkins" in client and client["daily_checkins"]:
            last_checkin_date = max(datetime.fromisoformat(c["date"]) for c in client["daily_checkins"])
            if (datetime.now() - last_checkin_date).days > 3:
                alert_exists = any(a["type"] == "no_recent_checkin" and a["client_id"] == client["id"] for a in alerts)
                if not alert_exists:
                    new_alert = {
                        "id": str(uuid.uuid4()),
                        "client_id": client["id"],
                        "type": "no_recent_checkin",
                        "message": f"Client {client['name']} has not checked in for more than 3 days.",
                        "details": {},
                        "timestamp": str(datetime.now())
                    }
                    alerts.append(new_alert)

    write_alerts(alerts)
    return jsonify(alerts), 201

@app.route("/api/alerts", methods=["GET"])
@protected
def get_alerts():
    """Lists all alerts."""
    alerts = read_alerts()
    return jsonify(alerts)

@app.route("/api/alerts/<alert_id>", methods=["DELETE"])
@protected
def delete_alert(alert_id):
    """Deletes an alert."""
    alerts = read_alerts()
    updated_alerts = [alert for alert in alerts if alert["id"] != alert_id]
    
    if len(updated_alerts) == len(alerts):
        return jsonify({"message": "Alert not found!"}), 404

    write_alerts(updated_alerts)
    return jsonify({"message": "Alert deleted successfully!"})

# --- Program Management Endpoints ---

@app.route("/api/programs", methods=["POST"])
@protected
def create_program():
    """Creates a new program."""
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"message": "Program name is required!"}), 400

    programs = read_programs()
    new_program = {
        "id": f"prog_{uuid.uuid4()}",
        "name": data["name"],
        "description": data.get("description", ""),
        "weeks": data.get("weeks", []) # Expects a list of weeks, each with days
    }
    programs.append(new_program)
    write_programs(programs)
    return jsonify(new_program), 201

@app.route("/api/programs", methods=["GET"])
@protected
def get_programs():
    """Lists all programs."""
    programs = read_programs()
    return jsonify(programs)

@app.route("/api/programs/<program_id>", methods=["GET"])
@protected
def get_program(program_id):
    """Gets a single program."""
    programs = read_programs()
    program = next((p for p in programs if p["id"] == program_id), None)
    if program:
        return jsonify(program)
    return jsonify({"message": "Program not found!"}), 404

@app.route("/api/programs/<program_id>", methods=["PUT"])
@protected
def update_program(program_id):
    """Updates a program."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    programs = read_programs()
    for i, program in enumerate(programs):
        if program["id"] == program_id:
            programs[i]["name"] = data.get("name", program["name"])
            programs[i]["description"] = data.get("description", program["description"])
            programs[i]["weeks"] = data.get("weeks", program["weeks"])
            write_programs(programs)
            return jsonify(programs[i])

    return jsonify({"message": "Program not found!"}), 404

@app.route("/api/programs/<program_id>", methods=["DELETE"])
@protected
def delete_program(program_id):
    """Deletes a program."""
    programs = read_programs()
    updated_programs = [p for p in programs if p["id"] != program_id]
    
    if len(updated_programs) == len(programs):
        return jsonify({"message": "Program not found!"}), 404

    write_programs(updated_programs)
    return jsonify({"message": "Program deleted successfully!"})

@app.route("/api/clients/<client_id>/assign-program", methods=["POST"])
@protected
def assign_program_to_client(client_id):
    """Assigns a program to a client and creates all the workout assignments."""
    data = request.get_json()
    program_id = data.get("program_id")
    start_date_str = data.get("start_date") # Expects YYYY-MM-DD

    if not all([program_id, start_date_str, client_id]):
        return jsonify({"message": "Client ID, Program ID, and Start Date are required!"}), 400

    programs = read_programs()
    program = next((p for p in programs if p["id"] == program_id), None)
    if not program:
        return jsonify({"message": "Program not found!"}), 404

    clients = read_clients()
    client = next((c for c in clients if c["id"] == client_id), None)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
        
    start_date = datetime.fromisoformat(start_date_str).date()
    assignments = read_workout_assignments()
    
    # Store program assignment on the client
    if "assigned_programs" not in client:
        client["assigned_programs"] = []
    client["assigned_programs"].append({
        "program_id": program_id,
        "start_date": start_date_str,
        "assignment_id": f"pa_{uuid.uuid4()}"
    })
    write_clients(clients)

    # Create individual workout assignments
    for week_index, week in enumerate(program.get("weeks", [])):
        for day_index, day in enumerate(week.get("days", [])):
            if day.get("template_id"):
                assignment_date = start_date + timedelta(weeks=week_index, days=day_index)
                new_assignment = {
                    "id": f"wa_{uuid.uuid4()}",
                    "client_id": client_id,
                    "program_id": program_id,
                    "template_id": day["template_id"],
                    "date": assignment_date.isoformat(),
                    "week": week_index + 1,
                    "day": day_index + 1,
                    "logged_data": {}
                }
                assignments.append(new_assignment)

    write_workout_assignments(assignments)
    return jsonify({"message": f"Program '{program['name']}' assigned to client {client['name']}."}), 201

@socketio.on('join')
def on_join(data):
    client_id = data['room']

@socketio.on('message')
def on_message():
    data = request.event['args'][0]
    if isinstance(data, dict) and 'room' in data:
        client_id = data['room']
        sender = data['sender']
        text = data['text']
        message = {'room': client_id, 'sender': sender, 'text': text, 'timestamp': str(datetime.now())}
        messages = read_messages()
        messages.append(message)
        write_messages(messages)
        emit('message', message, room=client_id)
    else:
        print("Error: 'room' key not found in data or data is not a dictionary in on_message")

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
