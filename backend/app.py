import os
import uuid
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from functools import wraps
from wger_service import WgerService
from achievements_service import check_for_new_pbs, add_achievements_to_client
from exercisedb_service import sync_exercises_from_exercisedb
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

with app.app_context():
    db.create_all()

def client_to_dict(client):
    return {
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'unique_url': client.unique_url,
        'features': json.loads(client.features) if client.features else {},
        'points': client.points,
        'daily_metrics': json.loads(client.daily_metrics) if client.daily_metrics else {},
        'archived': client.archived
    }

def program_to_dict(program):
    return {
        'id': program.id,
        'name': program.name,
        'description': program.description,
        'weeks': json.loads(program.weeks) if program.weeks else []
    }

def recipe_to_dict(recipe):
    return {
        'id': recipe.id,
        'name': recipe.name,
        'ingredients': json.loads(recipe.ingredients) if recipe.ingredients else [],
        'instructions': recipe.instructions,
        'macros': json.loads(recipe.macros) if recipe.macros else {}
    }

def meal_plan_to_dict(meal_plan):
    return {
        'id': meal_plan.id,
        'client_id': meal_plan.client_id,
        'recipe_id': meal_plan.recipe_id,
        'assigned_date': meal_plan.assigned_date
    }

def nutrition_log_to_dict(log):
    return {
        'id': log.id,
        'client_id': log.client_id,
        'log_date': log.log_date,
        'food_item': log.food_item,
        'macros': json.loads(log.macros) if log.macros else {}
    }

def body_stat_to_dict(stat):
    return {
        'id': stat.id,
        'client_id': stat.client_id,
        'date': stat.date,
        'weight': stat.weight,
        'measurements': json.loads(stat.measurements) if stat.measurements else {}
    }

def license_to_dict(license):
    return {
        'key': license.key,
        'issued_at': license.issued_at,
        'is_valid': license.is_valid
    }

def prospect_to_dict(prospect):
    return {
        'id': prospect.id,
        'name': prospect.name,
        'email': prospect.email,
        'status': prospect.status
    }

def resource_to_dict(resource):
    return {
        'id': resource.id,
        'title': resource.title,
        'filename': resource.filename,
        'uploaded_at': resource.uploaded_at
    }

def daily_checkin_to_dict(checkin):
    return {
        'id': checkin.id,
        'client_id': checkin.client_id,
        'checkin_date': checkin.checkin_date,
        'metrics': json.loads(checkin.metrics) if checkin.metrics else {}
    }

def workout_template_to_dict(template):
    days_data = []
    tags_data = []
    try:
        if template.days:
            days_data = json.loads(template.days)
    except json.JSONDecodeError:
        # If data is not valid JSON, leave as empty list
        pass
    try:
        if template.tags:
            tags_data = json.loads(template.tags)
    except json.JSONDecodeError:
        pass

    return {
        'id': template.id,
        'name': template.name,
        'description': template.description,
        'days': days_data,
        'tags': tags_data
    }

def alert_to_dict(alert):
    return {
        'id': alert.id,
        'client_id': alert.client_id,
        'type': alert.type,
        'message': alert.message,
        'details': json.loads(alert.details) if alert.details else {},
        'timestamp': alert.timestamp
    }

# More robust CORS configuration
# More robust CORS configuration
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

# Replace previous CORS setup line with permissive for demo
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": allowed_origins}})
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Configuration ---
# In a real application, this would be a more secure way to handle secrets
TRAINER_PASSWORD = os.environ.get("TRAINER_PASSWORD", "duck")
WGER_API_KEY = os.environ.get("WGER_API_KEY", "397683a6bb806f7e4c2d1c0b5a210a8a3f07b442")


# Initialize WGER service
wger_service = WgerService(WGER_API_KEY)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# --- Database Models ---

class Client(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    unique_url = db.Column(db.String(200), unique=True, nullable=False)
    features = db.Column(db.Text, default='{}')
    points = db.Column(db.Integer, default=0)
    daily_metrics = db.Column(db.Text, default='{}')
    archived = db.Column(db.Boolean, default=False)

class Exercise(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"exr_{uuid.uuid4()}")
    name = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text)
    media_url = db.Column(db.String(200))
    body_part = db.Column(db.String(100))
    equipment = db.Column(db.String(100))
    category = db.Column(db.String(100))
    muscles = db.Column(db.Text, default='[]') # JSON string of muscle IDs

class WorkoutTemplate(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"wt_{uuid.uuid4()}")
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    days = db.Column(db.Text, default='[]')
    tags = db.Column(db.Text, default='[]') # Storing tags as a JSON string

class ProgramAssignment(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"pa_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    template_id = db.Column(db.String, db.ForeignKey('workout_template.id'), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    current_day_index = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    client = db.relationship('Client', backref=db.backref('program_assignments', lazy=True))
    template = db.relationship('WorkoutTemplate', backref=db.backref('program_assignments', lazy=True))

class WorkoutLog(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"log_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    assignment_id = db.Column(db.String, db.ForeignKey('program_assignment.id'), nullable=False)
    day_index_completed = db.Column(db.Integer, nullable=False)
    actual_date = db.Column(db.String(20), nullable=False)
    performance_data = db.Column(db.Text, default='{}') # Storing performance data as a JSON string

    client = db.relationship('Client', backref=db.backref('workout_logs', lazy=True))
    assignment = db.relationship('ProgramAssignment', backref=db.backref('workout_logs', lazy=True))

class Recipe(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"rec_{uuid.uuid4()}")
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, default='[]') # JSON string of ingredients
    instructions = db.Column(db.Text)
    macros = db.Column(db.Text, default='{}') # JSON string of macros

class MealPlan(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"mp_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    recipe_id = db.Column(db.String, db.ForeignKey('recipe.id'), nullable=False)
    assigned_date = db.Column(db.String(20), nullable=False)

    client = db.relationship('Client', backref=db.backref('meal_plans', lazy=True))
    recipe = db.relationship('Recipe', backref=db.backref('meal_plans', lazy=True))

class NutritionLog(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"nl_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    log_date = db.Column(db.String(20), nullable=False)
    food_item = db.Column(db.String(200), nullable=False)
    macros = db.Column(db.Text, default='{}') # JSON string of macros

    client = db.relationship('Client', backref=db.backref('nutrition_logs', lazy=True))

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    issued_at = db.Column(db.String(50), default=lambda: str(datetime.now()))
    is_valid = db.Column(db.Boolean, default=True)

class Prospect(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='New')

class Resource(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.String(50), default=lambda: str(datetime.now()))

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

    new_client = Client(
        name=data['name'],
        email=data['email'],
        unique_url=f"http://localhost:3000/client/{uuid.uuid4()}",
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify(client_to_dict(new_client)), 201

@app.route("/api/clients", methods=["GET"])
@protected
def get_clients():
    """
    Lists all managed clients.
    Accepts an 'status' query parameter to filter by 'active' or 'archived'.
    Defaults to 'active'.
    """
    status = request.args.get('status', 'active')
    if status == 'active':
        clients_query = Client.query.filter_by(archived=False)
    elif status == 'archived':
        clients_query = Client.query.filter_by(archived=True)
    else:
        clients_query = Client.query
    
    clients = [client_to_dict(c) for c in clients_query.all()]
    return jsonify(clients)

@app.route("/api/clients/<client_id>", methods=["PUT"])
@protected
def update_client(client_id):
    """Updates a client's details."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    client = Client.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404

    client.name = data.get("name", client.name)
    client.email = data.get("email", client.email)
    db.session.commit()
    return jsonify(client_to_dict(client))

@app.route("/api/clients/<client_id>/archive", methods=["PUT"])
@protected
def archive_client(client_id):
    """Toggles the archive status of a client."""
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404

    client.archived = not client.archived
    db.session.commit()
    return jsonify(client_to_dict(client))


@app.route("/api/clients/<client_id>/features", methods=["PUT"])
@protected
def update_client_features(client_id):
    """Updates the feature toggles for a specific client."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    client = Client.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404

    client.features = json.dumps(data)
    db.session.commit()
    return jsonify(client_to_dict(client))















@app.route("/api/client/<client_id>", methods=["GET"])
def get_client(client_id):
    """Gets a specific client's data."""
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    return jsonify(client_to_dict(client))

@app.route("/api/exercises", methods=["GET"])
@cache.cached(timeout=3600, key_prefix='exercises_all')
@protected
def get_exercises():
    exercises = Exercise.query.all()
    return jsonify([{
        "id": e.id,
        "name": e.name,
        "instructions": e.instructions,
        "mediaUrl": e.media_url,
        "bodyPart": e.body_part,
        "equipment": e.equipment,
        "category": e.category,
        "muscles": json.loads(e.muscles)
    } for e in exercises])

@app.route("/api/client/<client_id>/exercises", methods=["GET"])
def get_client_exercises(client_id):
    """Gets exercises assigned to a specific client via their active program."""
    program_assignment = ProgramAssignment.query.filter_by(client_id=client_id, active=True).first()
    if not program_assignment:
        return jsonify([])

    workout_template = WorkoutTemplate.query.get(program_assignment.template_id)
    if not workout_template:
        return jsonify([])

    template_exercises = json.loads(workout_template.days)
    exercise_ids = [ex['id'] for day in template_exercises for group in day['groups'] for ex in group['exercises']]

    exercises = Exercise.query.filter(Exercise.id.in_(exercise_ids)).all()
    return jsonify([{
        "id": e.id,
        "name": e.name,
        "instructions": e.instructions,
        "mediaUrl": e.media_url,
        "bodyPart": e.body_part,
        "equipment": e.equipment,
        "category": e.category,
        "muscles": json.loads(e.muscles)
    } for e in exercises])

@app.route("/api/exercises", methods=["POST"])
@protected
def add_exercise():
    """Adds a new exercise to the library."""
    data = request.get_json()
    if not data or not data.get("name") or not data.get("instructions"):
        return jsonify({"message": "Name and instructions are required!"}), 400

    new_exercise = Exercise(
        name=data["name"],
        instructions=data["instructions"],
        media_url=data.get("mediaUrl"),
        body_part=data.get("bodyPart"),
        equipment=data.get("equipment"),
        category=data.get("category"),
        muscles=json.dumps(data.get("muscles", []))
    )
    db.session.add(new_exercise)
    db.session.commit()
    return jsonify({"exercise": new_exercise}), 201

# --- WGER Integration Endpoints ---

@app.route("/api/wger/sync", methods=["POST"])
@protected
def sync_wger_exercises():
    try:
        sync_result = wger_service.sync_exercises()
        if sync_result.get("status") == "success":
            return jsonify({"message": sync_result["message"]}), 200
        else:
            return jsonify({"message": sync_result["message"]}), 500
    except Exception as e:
        app.logger.error(f"Error during WGER sync: {e}")
        return jsonify({"message": f"Internal server error during WGER sync: {str(e)}"}), 500

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
        exercises = Exercise.query.all()
        # Assuming categories, muscles, equipment are properties of Exercise model or fetched separately
        # For now, returning dummy data for categories, muscles, equipment
        return jsonify({
            "exercises": [{"id": e.id, "name": e.name, "instructions": e.instructions, "bodyPart": e.body_part, "equipment": e.equipment, "category": e.category, "muscles": json.loads(e.muscles)} for e in exercises],
            "categories": [{"id": 1, "name": "Strength"}, {"id": 2, "name": "Cardio"}],
            "muscles": [{"id": 1, "name": "Biceps"}, {"id": 2, "name": "Triceps"}],
            "equipment": [{"id": 1, "name": "Barbell"}, {"id": 2, "name": "Dumbbell"}],
            "sync_info": {}
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ExerciseDB API sync endpoint
@app.route('/api/exercisedb/sync', methods=['POST'])
def sync_exercisedb_data():
    try:
        sync_result = sync_exercises_from_exercisedb()
        if sync_result.get("status") == "success":
            return jsonify({"message": sync_result["message"]}), 200
        else:
            return jsonify({"message": sync_result["message"]}), 500
    except Exception as e:
        app.logger.error(f"Error during ExerciseDB sync: {e}")
        return jsonify({"message": f"Internal server error during ExerciseDB sync: {str(e)}"}), 500

@app.route("/api/client/<client_id>/program/active", methods=["GET"])
def get_client_active_program(client_id):
    """Gets the client's active program, which functions as their 'playlist'."""
    program_assignment = ProgramAssignment.query.filter_by(client_id=client_id, active=True).first()

    if not program_assignment:
        return jsonify({"workout": {"id": "default-empty", "templateName": "No workout scheduled", "days": []}})

    workout_template = WorkoutTemplate.query.get(program_assignment.template_id)
    if not workout_template:
        return jsonify({"message": "Workout template not found!"}), 404

    all_days = json.loads(workout_template.days)

    return jsonify({"workout": {
        "id": program_assignment.id,
        "templateName": workout_template.name,
        "days": all_days, # Return all days
        "currentDayIndex": program_assignment.current_day_index,
        "assignmentId": program_assignment.id # Include assignment ID for logging
    }})


@app.route("/api/workout-templates", methods=["POST"])
@protected
def create_workout_template():
    """Creates a new workout template."""
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"message": "Name is required!"}), 400

    new_template = WorkoutTemplate(
        name=data["name"],
        days=json.dumps(data.get("days", [])),
        description=data.get("description", ""),
        tags=json.dumps(data.get("tags", []))
    )
    db.session.add(new_template)
    db.session.commit()
    return jsonify({"id": new_template.id, "name": new_template.name}), 201

def program_assignment_to_dict(assignment):
    return {
        'id': assignment.id,
        'client_id': assignment.client_id,
        'template_id': assignment.template_id,
        'start_date': assignment.start_date,
        'current_day_index': assignment.current_day_index,
        'active': assignment.active
    }

@app.route("/api/workout-assignments", methods=["GET"])
@protected
def get_workout_assignments():
    """Retrieves all workout assignments."""
    assignments = ProgramAssignment.query.all()
    return jsonify([program_assignment_to_dict(a) for a in assignments])

@app.route("/api/workout-templates", methods=["GET"])
@protected
def get_workout_templates():
    """Retrieves all workout templates."""
    templates = WorkoutTemplate.query.all()
    return jsonify([workout_template_to_dict(t) for t in templates])

@app.route("/api/workout-templates/<template_id>", methods=["GET"])
@protected
def get_workout_template(template_id):
    """Retrieves a single workout template."""
    template = WorkoutTemplate.query.get(template_id)
    if not template:
        return jsonify({"message": "Template not found!"}), 404
    return jsonify(workout_template_to_dict(template))

@app.route("/api/workout-templates/<template_id>", methods=["PUT"])
@protected
def update_workout_template(template_id):
    """Updates an existing workout template."""
    template = db.session.get(WorkoutTemplate, template_id)
    if not template:
        return jsonify({"message": "Template not found!"}), 404
    
    data = request.get_json()
    template.name = data.get("name", template.name)
    template.description = data.get("description", template.description)
    
    # Safely handle days update
    current_days = []
    if template.days:
        try:
            current_days = json.loads(template.days)
        except (json.JSONDecodeError, TypeError):
            pass
    template.days = json.dumps(data.get("days", current_days))
    
    # Safely handle tags update
    current_tags = []
    if template.tags:
        try:
            current_tags = json.loads(template.tags)
        except (json.JSONDecodeError, TypeError):
            pass
    template.tags = json.dumps(data.get("tags", current_tags))
    
    db.session.commit()
    return jsonify({"message": "Template updated successfully!"})

@app.route("/api/workout-templates/<template_id>", methods=["DELETE"])
@protected
def delete_workout_template(template_id):
    """Deletes a workout template."""
    template = WorkoutTemplate.query.get(template_id)
    if not template:
        return jsonify({"message": "Template not found!"}), 404

    db.session.delete(template)
    db.session.commit()
    return jsonify({"message": "Template deleted successfully!"})

@app.route("/api/workout-templates/<template_id>/duplicate", methods=["POST"])
@protected
def duplicate_workout_template(template_id):
    """Duplicates a workout template."""
    template_to_duplicate = WorkoutTemplate.query.get(template_id)

    if not template_to_duplicate:
        return jsonify({"message": "Template not found!"}), 404

    new_template = WorkoutTemplate(
        name=f"{template_to_duplicate.name} (Copy)",
        description=template_to_duplicate.description,
        days=template_to_duplicate.days,
        tags=template_to_duplicate.tags
    )
    db.session.add(new_template)
    db.session.commit()
    return jsonify(new_template), 201

@app.route("/api/client/<client_id>/personal-records", methods=["GET"])
def get_personal_records(client_id):
    """Gets all personal records for a specific client."""
    # For now, returning an empty list as personal records are not yet migrated/implemented in DB
    return jsonify([])

@app.route("/api/client/<client_id>/program", methods=["GET"])
def get_client_program(client_id):
    """Gets the client's currently assigned program and enriches it with
    the last logged data for each exercise.
    """
    program_assignment = ProgramAssignment.query.filter_by(client_id=client_id, active=True).first()

    if not program_assignment:
        return jsonify({"message": "No program assigned to this client."}), 404

    workout_template = WorkoutTemplate.query.get(program_assignment.template_id)
    if not workout_template:
        return jsonify({"message": "Workout template not found!"}), 404

    # For each exercise in the program, find the last time it was logged
    # This part needs to be refactored to query WorkoutLog model
    # For now, returning the template exercises directly
    template_exercises = json.loads(workout_template.days)

    return jsonify({
        "id": program_assignment.id,
        "client_id": program_assignment.client_id,
        "template_id": program_assignment.template_id,
        "name": workout_template.name,
        "description": workout_template.description,
        "start_date": program_assignment.start_date,
        "days": template_exercises, # This is a direct copy
        "current_day_index": program_assignment.current_day_index
    })

@app.route("/api/client/<client_id>/program/log", methods=["POST"])
def log_client_workout(client_id):
    """
    Logs a completed workout session for a client. The client specifies which
    day was completed. Optionally, the client can tell the server what the 
    next day should be.
    """
    data = request.get_json()
    if not data or "assignment_id" not in data or "day_index_completed" not in data:
        return jsonify({"message": "Missing required logging data."}), 400

    assignment = ProgramAssignment.query.get(data["assignment_id"])
    if not assignment:
        return jsonify({"message": "Program assignment not found!"}), 404

    new_log = WorkoutLog(
        client_id=client_id,
        assignment_id=data["assignment_id"],
        day_index_completed=data["day_index_completed"],
        actual_date=datetime.now().isoformat(),
        performance_data=json.dumps(data.get("performance_data", {}))
    )
    db.session.add(new_log)

    # If the frontend specifies what the next workout should be, update the assignment
    if "next_day_index" in data:
        workout_template = WorkoutTemplate.query.get(assignment.template_id)
        if workout_template:
            total_days = len(json.loads(workout_template.days))
            if data["next_day_index"] < total_days:
                assignment.current_day_index = data["next_day_index"]
            else:
                # If the next index is out of bounds, the program is complete
                assignment.active = False

    db.session.commit()
    
    # We need a workout_log_to_dict helper, for now returning a simple dict
    return jsonify({
        "id": new_log.id,
        "client_id": new_log.client_id,
        "assignment_id": new_log.assignment_id,
        "day_index_completed": new_log.day_index_completed,
        "actual_date": new_log.actual_date
    }), 201


# --- Nutrition Endpoints ---

@app.route("/api/recipes", methods=["POST"])
@protected
def create_recipe():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"message": "Recipe name is required!"}), 400
    new_recipe = Recipe(
        name=data["name"],
        ingredients=json.dumps(data.get("ingredients", [])),
        instructions=data.get("instructions"),
        macros=json.dumps(data.get("macros", {}))
    )
    db.session.add(new_recipe)
    db.session.commit()
    return jsonify(recipe_to_dict(new_recipe)), 201



@app.route("/api/clients/<client_id>/meal-plan", methods=["POST"])
@protected
def assign_meal_plan(client_id):
    data = request.get_json()
    if not data or not data.get("recipe_id") or not data.get("assigned_date"):
        return jsonify({"message": "Recipe ID and assigned date are required!"}), 400

    new_meal_plan = MealPlan(
        client_id=client_id,
        recipe_id=data["recipe_id"],
        assigned_date=data["assigned_date"]
    )
    db.session.add(new_meal_plan)
    db.session.commit()
    return jsonify(meal_plan_to_dict(new_meal_plan)), 201

@app.route("/api/clients/<client_id>/meal-plan", methods=["GET"])
@protected
def get_meal_plan(client_id):
    meal_plans = MealPlan.query.filter_by(client_id=client_id).all()
    return jsonify([meal_plan_to_dict(mp) for mp in meal_plans])

@app.route("/api/clients/<client_id>/nutrition-log", methods=["POST"])
def log_nutrition(client_id):
    data = request.get_json()
    if not data or not data.get("food_item") or not data.get("log_date"):
        return jsonify({"message": "Food item and log date are required!"}), 400

    new_log = NutritionLog(
        client_id=client_id,
        log_date=data["log_date"],
        food_item=data["food_item"],
        macros=json.dumps(data.get("macros", {}))
    )
    db.session.add(new_log)
    db.session.commit()
    return jsonify(nutrition_log_to_dict(new_log)), 201

@app.route("/api/clients/<client_id>/nutrition-log", methods=["GET"])
def get_nutrition_log(client_id):
    nutrition_logs = NutritionLog.query.filter_by(client_id=client_id).all()
    return jsonify([nutrition_log_to_dict(nl) for nl in nutrition_logs])

class BodyStat(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    weight = db.Column(db.Float)
    measurements = db.Column(db.Text, default='{}') # JSON string of measurements

    client = db.relationship('Client', backref=db.backref('body_stats', lazy=True))

@app.route("/api/clients/<client_id>/body-stats", methods=["GET"])
def get_body_stats(client_id):
    body_stats = BodyStat.query.filter_by(client_id=client_id).all()
    return jsonify([body_stat_to_dict(b) for b in body_stats])

@app.route("/api/clients/<client_id>/body-stats", methods=["POST"])
def add_body_stat(client_id):
    data = request.get_json()
    if not data or not data.get("date") or not data.get("weight"):
        return jsonify({"message": "Date and weight are required!"}), 400

    new_body_stat = BodyStat(
        client_id=client_id,
        date=data["date"],
        weight=data["weight"],
        measurements=json.dumps(data.get("measurements", {}))
    )
    db.session.add(new_body_stat)
    db.session.commit()
    return jsonify(body_stat_to_dict(new_body_stat)), 201

# --- Progress Photo Endpoints ---

class ProgressPhoto(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().isoformat())

    client = db.relationship('Client', backref=db.backref('progress_photos', lazy=True))

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/api/clients/<client_id>/progress-photos", methods=["POST"])
def upload_progress_photo(client_id):
    if 'photo' not in request.files:
        return jsonify({"message": "No photo part in the request"}), 400
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({"message": "No selected photo"}), 400
    if photo:
        filename = str(uuid.uuid4()) + os.path.splitext(photo.filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)

        new_photo = ProgressPhoto(
            client_id=client_id,
            filename=filename
        )
        db.session.add(new_photo)
        db.session.commit()
        return jsonify({"message": "Photo uploaded successfully", "filename": filename}), 201

    return jsonify({"message": "Client not found!"}), 404

@app.route("/api/clients/<client_id>/progress-photos", methods=["GET"])
def get_progress_photos(client_id):
    photos = ProgressPhoto.query.filter_by(client_id=client_id).all()
    return jsonify([{"filename": p.filename, "timestamp": p.timestamp} for p in photos])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



@app.route("/api/purchase-license", methods=["POST"])
@protected
def purchase_license():
    """Simulates a license purchase and generates a new cryptographic license key."""
    new_license = License()
    db.session.add(new_license)
    db.session.commit()
    return jsonify({
        "message": "License purchased and generated successfully!",
        "license_key": new_license.key
    }), 201

@app.route("/api/validate-license", methods=["POST"])
def validate_license():
    """Validates a given license key."""
    data = request.get_json()
    license_key = data.get("license_key")
    if not license_key:
        return jsonify({"message": "License key is required!"}), 400

    license_entry = License.query.filter_by(key=license_key, is_valid=True).first()
    if license_entry:
        return jsonify({"message": "License valid!", "is_valid": True}), 200
    return jsonify({"message": "License invalid or not found!", "is_valid": False}), 401

# --- Prospect Management Endpoints ---

@app.route("/api/prospects", methods=["GET"])
@protected
def get_prospects():
    """Lists all prospects."""
    prospects = Prospect.query.all()
    return jsonify([prospect_to_dict(p) for p in prospects])

@app.route("/api/prospects", methods=["POST"])
@protected
def add_prospect():
    """Adds a new prospect."""
    data = request.get_json()
    if not data or not data.get("name") or not data.get("email"):
        return jsonify({"message": "Name and email are required!"}), 400

    new_prospect = Prospect(
        name=data["name"],
        email=data["email"],
        status=data.get("status", "New")
    )
    db.session.add(new_prospect)
    db.session.commit()
    return jsonify(prospect_to_dict(new_prospect)), 201

@app.route("/api/prospects/<prospect_id>/status", methods=["PUT"])
@protected
def update_prospect_status(prospect_id):
    """Updates the status of a prospect."""
    data = request.get_json()
    if not data or not data.get("status"):
        return jsonify({"message": "Status is required!"}), 400

    prospect = Prospect.query.get(prospect_id)
    if not prospect:
        return jsonify({"message": "Prospect not found!"}), 404

    prospect.status = data["status"]
    db.session.commit()
    return jsonify(prospect_to_dict(prospect))

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

        new_resource = Resource(title=title, filename=filename)
        db.session.add(new_resource)
        db.session.commit()

        return jsonify({
            "message": "Resource uploaded successfully",
            "resource": resource_to_dict(new_resource)
        }), 201

    return jsonify({"message": "Resource upload failed!"}), 500

@app.route("/api/resources", methods=["GET"])
@protected
def get_resources():
    """Lists all resources."""
    resources = Resource.query.all()
    return jsonify([resource_to_dict(r) for r in resources])

@app.route('/resources/<filename>')
def serve_resource(filename):
    return send_from_directory(app.config['RESOURCES_UPLOAD_FOLDER'], filename)

# --- Daily Check-in Endpoints ---

class DailyCheckin(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    checkin_date = db.Column(db.String(20), nullable=False)
    metrics = db.Column(db.Text, default='{}') # JSON string of metrics

    client = db.relationship('Client', backref=db.backref('daily_checkins', lazy=True))

@app.route("/api/clients/<client_id>/daily-checkin", methods=["POST"])
def add_daily_checkin(client_id):
    data = request.get_json()
    if not data or not data.get("date"):
        return jsonify({"message": "Date is required!"}), 400

    new_checkin = DailyCheckin(
        client_id=client_id,
        checkin_date=data["date"],
        metrics=json.dumps(data.get("metrics", {}))
    )
    db.session.add(new_checkin)
    db.session.commit()
    return jsonify(daily_checkin_to_dict(new_checkin)), 201

@app.route("/api/clients/<client_id>/daily-checkin", methods=["GET"])
def get_daily_checkins(client_id):
    checkins = DailyCheckin.query.filter_by(client_id=client_id).all()
    return jsonify([daily_checkin_to_dict(c) for c in checkins])

# --- Group Management Endpoints ---

class Group(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    client_ids = db.Column(db.Text, default='[]') # JSON string of client IDs

@app.route("/api/groups", methods=["POST"])
@protected
def create_group():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"message": "Group name is required!"}), 400

    new_group = Group(
        name=data["name"],
        description=data.get("description"),
        client_ids=json.dumps(data.get("client_ids", []))
    )
    db.session.add(new_group)
    db.session.commit()
    return jsonify(new_group), 201

@app.route("/api/groups", methods=["GET"])
@protected
def get_groups():
    groups = Group.query.all()
    return jsonify(groups)

@app.route("/api/groups/<group_id>", methods=["GET"])
@protected
def get_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"message": "Group not found!"}), 404
    return jsonify(group)

@app.route("/api/groups/<group_id>", methods=["PUT"])
@protected
def update_group(group_id):
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data!"}), 400

    group = Group.query.get(group_id)
    if not group:
        return jsonify({"message": "Group not found!"}), 404

    group.name = data.get("name", group.name)
    group.description = data.get("description", group.description)
    group.client_ids = json.dumps(data.get("client_ids", []))
    db.session.commit()
    return jsonify(group)

@app.route("/api/groups/<group_id>", methods=["DELETE"])
@protected
def delete_group(group_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"message": "Group not found!"}), 404

    db.session.delete(group)
    db.session.commit()
    return jsonify({"message": "Group deleted successfully!"})

@app.route("/api/groups/<group_id>/clients", methods=["POST"])
@protected
def add_client_to_group(group_id):
    data = request.get_json()
    client_id = data.get("client_id")
    if not client_id:
        return jsonify({"message": "Client ID is required!"}), 400

    group = Group.query.get(group_id)
    if not group:
        return jsonify({"message": "Group not found!"}), 404

    client_ids = json.loads(group.client_ids)
    if client_id not in client_ids:
        client_ids.append(client_id)
        group.client_ids = json.dumps(client_ids)
        db.session.commit()
        return jsonify(group)
    else:
        return jsonify({"message": "Client already in group!"}), 400

@app.route("/api/groups/<group_id>/clients/<client_id>", methods=["DELETE"])
@protected
def remove_client_from_group(group_id, client_id):
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"message": "Group not found!"}), 404

    client_ids = json.loads(group.client_ids)
    if client_id in client_ids:
        client_ids.remove(client_id)
        group.client_ids = json.dumps(client_ids)
        db.session.commit()
        return jsonify(group)
    else:
        return jsonify({"message": "Client not in group!"}), 400

# --- Alert Management Endpoints ---

class Alert(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, default='{}') # JSON string of details
    timestamp = db.Column(db.String(50), default=lambda: datetime.now().isoformat())

    client = db.relationship('Client', backref=db.backref('alerts', lazy=True))

@app.route("/api/alerts/check", methods=["POST"])
@protected
def check_alerts():
    """
    Checks for conditions that should trigger an alert (e.g., missed check-ins).
    NOTE: This is a placeholder and needs to be fully implemented.
    """
    # This function needs significant refactoring to use DB models for clients, workouts, etc.
    # For now, it will return a dummy response.
    return jsonify({"message": "Alert checking logic not yet implemented."}), 200

@app.route("/api/alerts", methods=["GET"])
@protected
def get_alerts():
    """Lists all current alerts."""
    alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    return jsonify([alert_to_dict(a) for a in alerts])

@app.route("/api/alerts/<alert_id>", methods=["DELETE"])
@protected
def delete_alert(alert_id):
    """Deletes an alert."""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({"message": "Alert not found!"}), 404

    db.session.delete(alert)
    db.session.commit()
    return jsonify({"message": "Alert deleted successfully"})

# --- Program Management Endpoints ---

class Program(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"prog_{uuid.uuid4()}")
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    weeks = db.Column(db.Text, default='[]') # JSON string of weeks

@app.route("/api/programs", methods=["POST"])
@protected
def create_program():
    """Creates a new program."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"message": "Missing program name"}), 400

    new_program = Program(
        name=data["name"],
        description=data.get("description", ""),
        weeks=json.dumps(data.get("weeks", []))
    )
    db.session.add(new_program)
    db.session.commit()
    return jsonify(program_to_dict(new_program)), 201


@app.route("/api/programs", methods=["GET"])
@protected
def get_programs():
    """Lists all programs."""
    programs = Program.query.all()
    return jsonify([program_to_dict(p) for p in programs])


@app.route("/api/programs/<program_id>", methods=["GET"])
@protected
def get_program(program_id):
    """Gets a single program by its ID."""
    program = Program.query.get(program_id)
    if program:
        return jsonify(program_to_dict(program))
    return jsonify({"message": "Program not found"}), 404


@app.route("/api/programs/<program_id>", methods=["PUT"])
@protected
def update_program(program_id):
    """Updates an existing program."""
    program = Program.query.get(program_id)
    if not program:
        return jsonify({"message": "Program not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid data"}), 400

    program.name = data.get("name", program.name)
    program.description = data.get("description", program.description)
    if "weeks" in data:
        program.weeks = json.dumps(data["weeks"])

    db.session.commit()
    return jsonify(program_to_dict(program))


@app.route("/api/programs/<program_id>", methods=["DELETE"])
@protected
def delete_program(program_id):
    """Deletes a program."""
    program = Program.query.get(program_id)
    if not program:
        return jsonify({"message": "Program not found"}), 404

    db.session.delete(program)
    db.session.commit()
    return jsonify({"message": "Program deleted successfully"})


@app.route("/api/clients/<client_id>/assign-program", methods=["POST"])
@protected
def assign_program_to_client(client_id):
    """
    Assigns a program template to a client, creating a new, editable
    copy for that client.
    """
    data = request.get_json()
    template_id = data.get("template_id")
    start_date_str = data.get("start_date")

    if not all([template_id, start_date_str]):
        return jsonify({"message": "Template ID and Start Date are required!"}), 400

    template = WorkoutTemplate.query.get(template_id)
    if not template:
        return jsonify({"message": "Workout template not found!"}), 404

    # Deactivate any existing active program assignments for this client
    existing_assignments = ProgramAssignment.query.filter_by(client_id=client_id, active=True).all()
    for assignment in existing_assignments:
        assignment.active = False
    db.session.commit()

    new_assignment = ProgramAssignment(
        client_id=client_id,
        template_id=template_id,
        start_date=start_date_str,
        current_day_index=0, # Start from the first day
        active=True
    )
    db.session.add(new_assignment)
    db.session.commit()

    return jsonify({
        "id": new_assignment.id,
        "client_id": new_assignment.client_id,
        "template_id": new_assignment.template_id,
        "start_date": new_assignment.start_date,
        "current_day_index": new_assignment.current_day_index,
        "active": new_assignment.active
    }), 201

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
        # The following lines for reading/writing messages to a file are now obsolete
        # and should be replaced with database logic if message persistence is needed.
        # For now, we will just emit the message.
        # messages = read_messages()
        # messages.append(message)
        # write_messages(messages)
        emit('message', message, room=client_id)
    else:
        print("Error: 'room' key not found in data or data is not a dictionary in on_message")

if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)



