from flask import current_app as app, jsonify, request, send_from_directory
from functools import wraps
import json
from datetime import date, datetime
import uuid
import os
import urllib.parse
import pathlib

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from .achievements_service import check_for_new_pbs, add_achievements_to_client
from .exercisedb_service import sync_exercises_from_exercisedb

from .app import db, socketio, cache
from .models import (Client, Exercise, WorkoutTemplate, ProgramAssignment, WorkoutLog,
                     Recipe, MealPlan, NutritionLog, BodyStat, ProgressPhoto, License,
                     Prospect, Resource, Message, Achievement, DailyCheckin, Group, Alert, Program,
                     Category, Muscle, Equipment)


# --- to_dict helpers ---
def client_to_dict(client):
    return {
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'unique_url': client.unique_url,
        'features': json.loads(client.features) if client.features else {},
        'points': client.points,
        'daily_metrics': json.loads(client.daily_metrics) if client.daily_metrics else {},
        'archived': client.archived,
        'deleted': client.deleted,
        'phone': client.phone,
        'age': client.age,
        'gender': client.gender,
        'height': client.height,
        'weight': client.weight,
        'bodyfat': client.bodyfat,
        'goals': client.goals,
        'medical_history': client.medical_history,
        'injuries': client.injuries,
        'lifestyle': client.lifestyle,
        'hours_sleep': client.hours_sleep,
        'stress_level': client.stress_level,
        'hydration_level': client.hydration_level,
        'nutrition_habits': client.nutrition_habits,
        'workout_history': client.workout_history,
        'workout_frequency': client.workout_frequency,
        'workout_preference': client.workout_preference,
        'workout_availability': client.workout_availability
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
        'assigned_date': meal_plan.assigned_date.isoformat() if meal_plan.assigned_date else None,
        'recipe_name': meal_plan.recipe.name if meal_plan.recipe else "Unknown Recipe"
    }

def nutrition_log_to_dict(log):
    return {
        'id': log.id,
        'client_id': log.client_id,
        'log_date': log.log_date.isoformat() if log.log_date else None,
        'food_item': log.food_item,
        'macros': json.loads(log.macros) if log.macros else {}
    }

def body_stat_to_dict(stat):
    return {
        'id': stat.id,
        'client_id': stat.client_id,
        'date': stat.date.isoformat() if stat.date else None,
        'weight': stat.weight,
        'measurements': json.loads(stat.measurements) if stat.measurements else {}
    }

def license_to_dict(license):
    return {
        'key': license.key,
        'issued_at': license.issued_at.isoformat() if license.issued_at else None,
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
        'uploaded_at': resource.uploaded_at.isoformat() if resource.uploaded_at else None
    }

def group_to_dict(group):
    return {
        'id': group.id,
        'name': group.name,
        'description': group.description,
        'client_ids': json.loads(group.client_ids) if group.client_ids else []
    }

def daily_checkin_to_dict(checkin):
    return {
        'id': checkin.id,
        'client_id': checkin.client_id,
        'checkin_date': checkin.checkin_date.isoformat() if checkin.checkin_date else None,
        'metrics': json.loads(checkin.metrics) if checkin.metrics else {}
    }

def workout_template_to_dict(template):
    days_data = []
    tags_data = []
    try:
        if template.days:
            days_data = json.loads(template.days)
    except json.JSONDecodeError:
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
        'timestamp': alert.timestamp.isoformat() if alert.timestamp else None
    }

def workout_log_to_dict(log):
    return {
        'id': log.id,
        'client_id': log.client_id,
        'assignment_id': log.assignment_id,
        'day_index_completed': log.day_index_completed,
        'actual_date': log.actual_date.isoformat() if log.actual_date else None,
        'performance_data': json.loads(log.performance_data) if log.performance_data else {}
    }

def message_to_dict(message):
    return {
        'id': message.id,
        'client_id': message.client_id,
        'sender_type': message.sender_type,
        'text': message.text,
        'timestamp': message.timestamp.isoformat() if message.timestamp else None
    }

def achievement_to_dict(achievement):
    return {
        'id': achievement.id,
        'client_id': achievement.client_id,
        'type': achievement.type,
        'title': achievement.title,
        'description': achievement.description,
        'unlocked_at': achievement.unlocked_at.isoformat() if achievement.unlocked_at else None,
        'icon': achievement.icon
    }

def exercise_to_dict(exercise):
    # Determine URL for media - prefer local file if available
    gif_url = exercise.media_url
    if exercise.local_media_path:
        filename = os.path.basename(exercise.local_media_path)
        gif_url = f"/media/exercises/{urllib.parse.quote(filename)}"
    
    instructions_raw = exercise.instructions
    instructions = []
    if isinstance(instructions_raw, str):
        # First replace literal "\\n" with real newlines then attempt JSON parse
        cleaned = instructions_raw.replace("\\n", "\n")
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                instructions = [str(step).strip() for step in parsed if str(step).strip()]
            else:
                instructions = [str(parsed).strip()]
        except json.JSONDecodeError:
            instructions = [step.strip() for step in cleaned.split("\n") if step.strip()]
    elif isinstance(instructions_raw, list):
        instructions = [str(step).strip() for step in instructions_raw if str(step).strip()]

    # Parse muscle information
    muscles = []
    if exercise.secondaryMuscles:
        try:
            parsed = json.loads(exercise.secondaryMuscles)
            if isinstance(parsed, list):
                muscles = parsed
            elif isinstance(parsed, str):
                muscles = [parsed]
        except json.JSONDecodeError:
            muscles = [m.strip() for m in exercise.secondaryMuscles.split(',') if m.strip()]

    # Include target muscle if not already present
    if exercise.target and exercise.target not in muscles:
        muscles.append(exercise.target)

    return {
        "id": exercise.id,
        "name": exercise.name,
        "instructions": instructions,
        "mediaUrl": gif_url,
        "gifUrl": gif_url,
        "category": exercise.bodyPart,
        "equipment": exercise.equipment,
        "muscles": muscles,
        "bodyPart": exercise.bodyPart
    }

def program_assignment_to_dict(assignment):
    return {
        'id': assignment.id,
        'client_id': assignment.client_id,
        'template_id': assignment.template_id,
        'start_date': assignment.start_date.isoformat() if assignment.start_date else None,
        'current_day_index': assignment.current_day_index,
        'active': assignment.active
    }

# --- Helper Functions ---
def find_client(identifier):
    """Fetch a client by primary key ID or unique_url."""
    return Client.query.filter(or_(Client.id == identifier, Client.unique_url == identifier), Client.deleted == False).first()

# In a real application, this would be a more secure way to handle secrets
TRAINER_PASSWORD = os.environ.get("TRAINER_PASSWORD", "duck")

LEGACY_JSON_DIR = pathlib.Path(__file__).resolve().parent / 'database'
WORKOUT_ASSIGNMENTS_PATH = LEGACY_JSON_DIR / 'workout_assignments.json'
WORKOUT_TEMPLATES_PATH = LEGACY_JSON_DIR / 'workout_templates.json'

def _read_legacy_workout_assignments():
    try:
        import json
        if WORKOUT_ASSIGNMENTS_PATH.exists():
            with open(WORKOUT_ASSIGNMENTS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        app.logger.error(f"Error reading legacy workout assignments: {e}")
    return []

def _read_legacy_workout_templates():
    try:
        import json
        if WORKOUT_TEMPLATES_PATH.exists():
            with open(WORKOUT_TEMPLATES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        app.logger.error(f"Error reading legacy workout templates: {e}")
    return []

def _normalize_client_id(raw_id):
    return raw_id.replace('/client/','') if raw_id.startswith('/client/') else raw_id

# --- Decorators ---
def protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            # Respond to the CORS preflight request
            response = jsonify({'message': 'CORS preflight successful'})
            response.status_code = 200
            # Let Flask-CORS add the necessary headers
            return response

        auth = request.authorization
        if not auth or not (auth.username == "trainer" and auth.password == TRAINER_PASSWORD):
            return jsonify({"message": "Authentication required!"}), 401
        return f(*args, **kwargs)
    return decorated

# --- Input Sanitizers ---
def _to_int(value):
    try:
        return int(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None

def _to_float(value):
    try:
        return float(value) if value not in (None, "") else None
    except (ValueError, TypeError):
        return None

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

@app.route('/api/exercisedb/sync', methods=['POST'])
@protected
def sync_exercisedb_data():
    """Synchronizes exercises from the external exercise database."""
    try:
        sync_exercises_from_exercisedb()
        return jsonify({"message": "Exercises synchronized successfully!"}), 200
    except Exception as e:
        app.logger.error(f"Error synchronizing exercises: {e}")
        return jsonify({"message": "Failed to synchronize exercises."}), 500

@app.route("/api/clients", methods=["POST"])
@protected
def add_client():
    """Adds a new client."""
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"message": "Missing name or email"}), 400

    new_id = str(uuid.uuid4())
    unique_url = f"{uuid.uuid4()}" # Simpler unique URL

    # Map request payload keys directly if they exist
    client_kwargs = {
        'id': new_id,
        'name': data['name'],
        'email': data['email'],
        'unique_url': unique_url,
        'phone': data.get('phone'),
        'age': _to_int(data.get('age')),
        'gender': data.get('gender'),
        'height': _to_float(data.get('height')),
        'weight': _to_float(data.get('weight')),
        'bodyfat': _to_float(data.get('bodyfat')),
        'goals': data.get('goals'),
        'medical_history': data.get('medical_history'),
        'injuries': data.get('injuries'),
        'lifestyle': data.get('lifestyle'),
        'hours_sleep': _to_int(data.get('hours_sleep')),
        'stress_level': data.get('stress_level'),
        'hydration_level': _to_float(data.get('hydration_level')),
        'nutrition_habits': data.get('nutrition_habits'),
        'workout_history': data.get('workout_history'),
        'workout_frequency': _to_int(data.get('workout_frequency')),
        'workout_preference': data.get('workout_preference'),
        'workout_availability': data.get('workout_availability'),
    }

    new_client = Client(**client_kwargs)
    
    try:
        db.session.add(new_client)
        db.session.commit()
        return jsonify(client_to_dict(new_client)), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Client with this email already exists."}), 409
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding client: {e}")
        return jsonify({"message": "An unexpected error occurred on the server."}), 500

@app.route("/api/clients/<client_id>", methods=["DELETE"])
@protected
def delete_client(client_id):
    """Soft deletes a client by setting their 'deleted' flag to True."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    client.deleted = True
    db.session.commit()
    return jsonify({"message": "Client soft-deleted successfully!"}), 200


@app.route("/api/clients", methods=["GET"])
@protected
def get_clients():
    """
    Lists all managed clients.
    Accepts an 'status' query parameter to filter by 'active', 'archived', or 'all'.
    Defaults to 'active'.
    """
    status = request.args.get('status', 'active')
    
    clients_query = Client.query.filter_by(deleted=False) # Exclude soft-deleted clients by default

    if status == 'active':
        clients_query = clients_query.filter_by(archived=False)
    elif status == 'archived':
        clients_query = clients_query.filter_by(archived=True)
    
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

    # Update core and extended fields if provided
    for field in [
        'name','email','phone','age','gender','height','weight','bodyfat','goals','medical_history','injuries',
        'lifestyle','hours_sleep','stress_level','hydration_level','nutrition_habits','workout_history',
        'workout_frequency','workout_preference','workout_availability']:
        if field in data:
            value = data[field]
            if field in ['age','hours_sleep','workout_frequency']:
                value = _to_int(value)
            elif field in ['height','weight','bodyfat','hydration_level']:
                value = _to_float(value)
            setattr(client, field, value)
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
    """Gets a specific client's data. Supports both id and unique_url."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    return jsonify(client_to_dict(client))

@app.route("/api/exercises", methods=["GET"])
@cache.cached(timeout=3600, key_prefix='exercises_all')
@protected
def get_exercises():
    exercises = Exercise.query.all()
    return jsonify([exercise_to_dict(e) for e in exercises])

@app.route("/api/exercises/enhanced", methods=["GET"])
@protected
def get_exercises_enhanced():
    exercises = Exercise.query.all()
    data = [exercise_to_dict(ex) for ex in exercises]

    # Derive unique lists directly from exercise data
    categories = sorted({ex.bodyPart for ex in exercises if ex.bodyPart})

    muscles_set = set()
    for ex in data:
        muscles_set.update(ex["muscles"])
    muscles = sorted(muscles_set)

    equipment_set = {ex.equipment for ex in exercises if ex.equipment}
    equipment = sorted(equipment_set)

    return jsonify({
        "exercises": data,
        "categories": categories,
        "muscles": muscles,
        "equipment": equipment
    })

@app.route("/api/templates", methods=["GET"])
@protected
def get_templates():
    templates = WorkoutTemplate.query.order_by(WorkoutTemplate.name).all()
    return jsonify([template.to_dict() for template in templates])

@app.route("/api/templates/<template_id>", methods=["GET"])
@protected
def get_template(template_id):
    template = WorkoutTemplate.query.get(template_id)
    if not template:
        return jsonify({"message": "Template not found"}), 404
    return jsonify(template.to_dict())

@app.route("/api/templates", methods=["POST"])
@protected
def create_template():
    data = request.get_json()
    new_template = WorkoutTemplate(
        name=data.get('name', 'Untitled Template'),
        days=data.get('days', '[]')
    )
    db.session.add(new_template)
    db.session.commit()
    return jsonify(new_template.to_dict()), 201

@app.route("/api/templates/<template_id>", methods=["PUT"])
@protected
def update_template(template_id):
    template = WorkoutTemplate.query.get(template_id)
    if not template:
        return jsonify({"message": "Template not found"}), 404
    
    data = request.get_json()
    template.name = data.get('name', template.name)
    template.days = data.get('days', template.days)
    
    db.session.commit()
    return jsonify(template.to_dict())

@app.route("/api/workout-assignments", methods=["GET"])
@protected
def get_workout_assignments():
    assignments = ProgramAssignment.query.all()
    return jsonify([a.to_dict() for a in assignments])

@app.route("/api/clients/<client_id>/exercises", methods=["GET"])
def get_client_exercises(client_id):
    """Gets exercises assigned to a specific client via their active program."""
    norm_id = _normalize_client_id(client_id)
    # Attempt to fetch active assignment; if DB not migrated, ignore error
    try:
        assignment = ProgramAssignment.query.filter_by(client_id=norm_id, active=True).first()
    except Exception as e:
        app.logger.warning(f"DB access error for ProgramAssignment: {e}. Falling back to legacy assignments.")
        assignment = None

    if not assignment:
        # Fallback: legacy JSON assignments file
        legacy_assignments = _read_legacy_workout_assignments()
        legacy = next((a for a in legacy_assignments if a['client_id'] == client_id), None)
        if legacy:
            template = WorkoutTemplate.query.get(legacy['template_id'])
            if template:
                try:
                    days_data = json.loads(template.days) if template.days else []
                except json.JSONDecodeError:
                    days_data = []
                return jsonify({
                    "assignmentId": legacy['id'],
                    "startDate": legacy.get('date'),
                    "currentDayIndex": 0,
                    "workout": {
                        "id": template.id,
                        "templateId": template.id,
                        "templateName": template.name,
                        "days": days_data
                    }
                })
        # else continue to default-empty response
        return jsonify({
            "workout": {
                "id": "default-empty",
                "templateId": "default-empty",
                "templateName": "No workout scheduled",
                "days": []
            }
        })

    template = WorkoutTemplate.query.get(assignment.template_id)

    if not template:
        return jsonify({
            "workout": {
                "id": "default-empty",
                "templateId": "default-empty",
                "templateName": "No workout scheduled",
                "days": []
            }
        })

    try:
        days_data = json.loads(template.days) if template.days else []
    except json.JSONDecodeError:
        days_data = []

    payload = {
        "assignmentId": assignment.id,
        "startDate": assignment.start_date.isoformat() if assignment.start_date else None,
        "currentDayIndex": assignment.current_day_index,
        "workout": {
            "id": template.id,
            "templateId": template.id,
            "templateName": template.name,
            "days": days_data
        }
    }

    return jsonify(payload)

@app.route("/api/exercises", methods=["POST"])
@protected
def add_exercise():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"message": "Name is required!"}), 400

    # This assumes muscleIds, categoryId, equipmentId are passed
    new_exercise = Exercise(
        name=data["name"],
        instructions=data.get("instructions"),
        media_url=data.get("mediaUrl"),
        category_id=data.get("categoryId"),
        equipment_id=data.get("equipmentId"),
        muscles=[Muscle.query.get(muscle_id) for muscle_id in data.get("muscleIds", [])]
    )
    db.session.add(new_exercise)
    db.session.commit()
    return jsonify({"exercise": exercise_to_dict(new_exercise)}), 201

@app.route('/media/exercises/<path:filename>')
def serve_exercise_media(filename):
    media_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'exercise_media')
    return send_from_directory(media_dir, filename)

# --- New Endpoints for Program & Meal Plan ---

# 1. Get the active workout program for a client
@app.route("/api/clients/<client_id>/program/active", methods=["GET"])
def get_active_program(client_id):
    # Resolve client_id to actual internal id (handles unique_url)
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    norm_id = client.id  # Use resolved internal id
    # Attempt to fetch active assignment; if DB not migrated, ignore error
    try:
        assignment = ProgramAssignment.query.filter_by(client_id=norm_id, active=True).first()
    except Exception as e:
        app.logger.warning(f"DB access error for ProgramAssignment: {e}. Falling back to legacy assignments.")
        assignment = None

    if not assignment:
        # Fallback: legacy JSON assignments file
        legacy_assignments = _read_legacy_workout_assignments()
        # match by exact id or by stripping '/client/' prefix
        identifier_variants = {client_id}
        if client_id.startswith('/client/'):
            identifier_variants.add(client_id.replace('/client/',''))
        legacy = next((a for a in legacy_assignments if a['client_id'] in identifier_variants), None)
        if legacy:
            template = WorkoutTemplate.query.get(legacy['template_id'])
            if template is None:
                # attempt to read from JSON file
                legacy_templates = _read_legacy_workout_templates()
                template_dict = next((t for t in legacy_templates if t['id'] == legacy['template_id']), None)
                if template_dict:
                    # Build days_data from legacy structure
                    if 'days' in template_dict and template_dict['days']:
                        days_data = template_dict['days']
                    elif 'exercises' in template_dict and template_dict['exercises']:
                        days_data = [{
                            "name": "Day 1",
                            "groups": template_dict['exercises']
                        }]
                    else:
                        days_data = []
                    return jsonify({
                        "assignmentId": legacy['id'],
                        "startDate": legacy.get('date'),
                        "currentDayIndex": 0,
                        "workout": {
                            "id": template_dict['id'],
                            "templateId": template_dict['id'],
                            "templateName": template_dict.get('name','Legacy Workout'),
                            "days": days_data
                        }
                    })
            else:
                try:
                    days_data = json.loads(template.days) if template.days else []
                except json.JSONDecodeError:
                    days_data = []
                return jsonify({
                    "assignmentId": legacy['id'],
                    "startDate": legacy.get('date'),
                    "currentDayIndex": 0,
                    "workout": {
                        "id": template.id,
                        "templateId": template.id,
                        "templateName": template.name,
                        "days": days_data
                    }
                })
        # else continue to default-empty response
        return jsonify({
            "workout": {
                "id": "default-empty",
                "templateId": "default-empty",
                "templateName": "No workout scheduled",
                "days": []
            }
        })

    template = WorkoutTemplate.query.get(assignment.template_id)

    if not template:
        return jsonify({
            "workout": {
                "id": "default-empty",
                "templateId": "default-empty",
                "templateName": "No workout scheduled",
                "days": []
            }
        })

    try:
        days_data = json.loads(template.days) if template.days else []
    except json.JSONDecodeError:
        days_data = []

    payload = {
        "assignmentId": assignment.id,
        "startDate": assignment.start_date.isoformat() if assignment.start_date else None,
        "currentDayIndex": assignment.current_day_index,
        "workout": {
            "id": template.id,
            "templateId": template.id,
            "templateName": template.name,
            "days": days_data
        }
    }

    return jsonify(payload)


# 2. Get the most recent meal-plan for a client
@app.route("/api/clients/<client_id>/meal-plan", methods=["GET"])
def get_client_meal_plan(client_id):
    """Returns the latest assigned meal-plan for the given client (or 204 if none)."""
    meal_plan = MealPlan.query.filter_by(client_id=client_id).order_by(MealPlan.assigned_date.desc()).first()

    if not meal_plan:
        # 204 No Content is handled specially by the front-end helper so it resolves to `null`
        return "", 204

    return jsonify(meal_plan_to_dict(meal_plan))

@app.route('/api/clients/<client_id>/programs/assign', methods=['POST','OPTIONS'])
@protected
def assign_program_to_client(client_id):
    data = request.get_json() or {}
    template_id = data.get('template_id')
    start_date_str = data.get('start_date')

    if not template_id:
        return jsonify({'message': 'template_id is required'}), 400

    # Robust date parsing
    start_date = date.today()
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Please use YYYY-MM-DD.'}), 400

    # Deactivate existing assignment
    # Remove any previous assignments (active or inactive) to avoid unique constraints or duplicates
    norm_id = _normalize_client_id(client_id)
    existing_assignments = ProgramAssignment.query.filter_by(client_id=norm_id).all()
    for old in existing_assignments:
        db.session.delete(old)
    db.session.commit()

    assignment = ProgramAssignment(
        client_id=norm_id,
        template_id=template_id,
        start_date=start_date,
        active=True,
        current_day_index=0
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify(assignment.to_dict()), 201

@app.route('/api/clients/<client_id>/programs/unassign', methods=['DELETE','OPTIONS'])
@protected
def unassign_program_from_client(client_id):
    """Deactivates (or removes) the active workout assignment for the client.
    Works for both SQL-backed ProgramAssignment and legacy JSON file."""
    norm_id = _normalize_client_id(client_id)
    # First attempt SQL
    try:
        active_assignment = ProgramAssignment.query.filter_by(client_id=norm_id, active=True).first()
        if active_assignment:
            db.session.delete(active_assignment)
            db.session.commit()
            return jsonify({"message": "Program unassigned (DB)."})
    except Exception as e:
        app.logger.warning(f"DB error while unassigning program: {e}")

    # Legacy JSON workflow
    legacy_assignments = _read_legacy_workout_assignments()
    original_len = len(legacy_assignments)
    legacy_assignments = [a for a in legacy_assignments if a.get('client_id') != client_id]
    if len(legacy_assignments) != original_len:
        import json
        try:
            with open(WORKOUT_ASSIGNMENTS_PATH, 'w', encoding='utf-8') as f:
                json.dump(legacy_assignments, f, indent=4)
            return jsonify({"message": "Program unassigned (legacy JSON)."})
        except Exception as e:
            return jsonify({"message": f"Failed to save legacy assignments: {e}"}), 500

    return jsonify({"message": "No active assignment found."}), 404

@app.route("/api/workout-templates", methods=["GET"])
@protected
def alias_get_workout_templates():
    """Alias for legacy front-end: returns list of workout templates."""
    return get_templates()

@app.route("/api/workout-templates/<template_id>", methods=["GET"])
@protected
def alias_get_workout_template(template_id):
    """Alias for legacy front-end: returns single template details."""
    return get_template(template_id)

# ----------------- Program Endpoints -----------------
@app.route('/api/programs', methods=['GET'])
@protected
def get_programs():
    programs = Program.query.order_by(Program.name).all()
    return jsonify([program_to_dict(p) for p in programs])

@app.route('/api/programs', methods=['POST'])
@protected
def create_program():
    data = request.get_json() or {}
    new_program = Program(
        name=data.get('name', 'Untitled Program'),
        description=data.get('description'),
        weeks=json.dumps(data.get('weeks', []))
    )
    db.session.add(new_program)
    db.session.commit()
    return jsonify(program_to_dict(new_program)), 201

@app.route('/api/programs/<program_id>', methods=['DELETE'])
@protected
def delete_program(program_id):
    program = Program.query.get(program_id)
    if not program:
        return jsonify({'message': 'Program not found'}), 404
    db.session.delete(program)
    db.session.commit()
    return '', 204

# --- Workout Statistics Endpoint ---
@app.route("/api/clients/<client_id>/program/<assignment_id>/stats", methods=["GET"])
@protected
def get_program_stats(client_id, assignment_id):
    """Returns the number of times each day of the assignment has been performed.

    Response example:
    {
        "day_counts": [2, 1, 0, 0, 0, 0, 0]
    }
    """
    # Fetch the assignment and related template to know how many days exist
    assignment = ProgramAssignment.query.filter_by(id=assignment_id, client_id=client_id).first()
    if not assignment:
        return jsonify({"message": "Assignment not found"}), 404

    template = WorkoutTemplate.query.get(assignment.template_id)
    if not template:
        return jsonify({"message": "Template not found"}), 404

    try:
        days = json.loads(template.days) if template.days else []
    except json.JSONDecodeError:
        days = []

    total_days = len(days)
    # Initialize counts list
    day_counts = [0] * total_days

    # Aggregate counts from WorkoutLog
    logs = WorkoutLog.query.filter_by(client_id=client_id, assignment_id=assignment_id).all()
    for log in logs:
        if 0 <= log.day_index_completed < total_days:
            day_counts[log.day_index_completed] += 1

    return jsonify({"day_counts": day_counts})

# --- Workout Logging Endpoint ---
@app.route("/api/clients/<client_id>/program/log", methods=["POST"])
def log_workout(client_id):
    """Logs a completed workout for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    assignment_id = data.get('assignment_id')
    if not assignment_id:
        return jsonify({"message": "Assignment ID required"}), 400

    # Create workout log entry
    workout_log = WorkoutLog(
        client_id=client.id,
        assignment_id=assignment_id,
        day_index_completed=data.get('day_index_completed', 0),
        actual_date=date.today(),
        performance_data=json.dumps({
            'performanceLog': data.get('performanceLog', {}),
            'exerciseNotes': data.get('exerciseNotes', {}),
            'elapsedTime': data.get('elapsedTime', 0)
        })
    )
    
    try:
        db.session.add(workout_log)
        db.session.commit()
        return jsonify({"message": "Workout logged successfully", "log_id": workout_log.id}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error logging workout: {e}")
        return jsonify({"message": "Failed to log workout"}), 500

# --- Workout Session Management ---
@app.route("/api/clients/<client_id>/workout-session/save", methods=["POST"])
def save_workout_progress(client_id):
    """Saves in-progress workout data for later resumption."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        # Store session data in client's session field or create a separate session table
        # For now, using a simple approach with a session file per client
        import os
        session_dir = os.path.join('backend', 'sessions')
        os.makedirs(session_dir, exist_ok=True)
        
        session_file = os.path.join(session_dir, f'client_{client.id}_session.json')
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'workout_data': data,
            'client_id': client.id
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
            
        return jsonify({"message": "Workout progress saved"}), 200
    except Exception as e:
        app.logger.error(f"Error saving workout session: {e}")
        return jsonify({"message": "Failed to save workout session"}), 500

@app.route("/api/clients/<client_id>/workout-session", methods=["GET"])
def get_workout_session(client_id):
    """Retrieves saved workout session data."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404

    try:
        import os
        session_file = os.path.join('backend', 'sessions', f'client_{client.id}_session.json')
        
        if not os.path.exists(session_file):
            return jsonify({"session": None}), 200
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
            
        # Check if session is recent (within 24 hours)
        from datetime import datetime, timedelta
        session_time = datetime.fromisoformat(session_data['timestamp'])
        if datetime.now() - session_time > timedelta(hours=24):
            # Session too old, delete it
            os.remove(session_file)
            return jsonify({"session": None}), 200
            
        return jsonify({"session": session_data}), 200
    except Exception as e:
        app.logger.error(f"Error retrieving workout session: {e}")
        return jsonify({"session": None}), 200

@app.route("/api/clients/<client_id>/workout-session", methods=["DELETE"])
def clear_workout_session(client_id):
    """Clears saved workout session data."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404

    try:
        import os
        session_file = os.path.join('backend', 'sessions', f'client_{client.id}_session.json')
        
        if os.path.exists(session_file):
            os.remove(session_file)
            
        return jsonify({"message": "Session cleared"}), 200
    except Exception as e:
        app.logger.error(f"Error clearing workout session: {e}")
        return jsonify({"message": "Failed to clear session"}), 500

# --- Exercise History Endpoint ---
@app.route("/api/clients/<client_id>/exercise/<exercise_id>/history", methods=["GET"])
def get_exercise_history(client_id, exercise_id):
    """Gets the exercise history for a specific client and exercise."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404

    # Get all workout logs for this client
    logs = WorkoutLog.query.filter_by(client_id=client.id).order_by(WorkoutLog.actual_date.desc()).all()
    
    exercise_history = []
    for log in logs:
        try:
            performance_data = json.loads(log.performance_data) if log.performance_data else {}
            performance_log = performance_data.get('performanceLog', {})
            
            if exercise_id in performance_log:
                sets_data = performance_log[exercise_id]
                exercise_history.append({
                    'date': log.actual_date.isoformat(),
                    'sets': sets_data,
                    'day_index': log.day_index_completed
                })
        except json.JSONDecodeError:
            continue
    
    return jsonify(exercise_history)

# --- Get Previous Workout Data ---
@app.route("/api/clients/<client_id>/exercise/<exercise_id>/previous", methods=["GET"])
def get_previous_exercise_data(client_id, exercise_id):
    """Gets the most recent data for a specific exercise."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404

    # Get most recent workout log for this client with this exercise
    logs = WorkoutLog.query.filter_by(client_id=client.id).order_by(WorkoutLog.actual_date.desc()).all()
    
    for log in logs:
        try:
            performance_data = json.loads(log.performance_data) if log.performance_data else {}
            performance_log = performance_data.get('performanceLog', {})
            
            if exercise_id in performance_log:
                sets_data = performance_log[exercise_id]
                # Get the best set (highest weight or reps)
                best_set = max(sets_data, key=lambda s: float(s.get('weight', 0)) * float(s.get('reps', 0)), default={})
                return jsonify({
                    'weight': best_set.get('weight', ''),
                    'reps': best_set.get('reps', ''),
                    'date': log.actual_date.isoformat()
                })
        except (json.JSONDecodeError, ValueError):
            continue
    
    return jsonify({'weight': '', 'reps': '', 'date': None})

# ... (all other routes and socketio handlers) ... 