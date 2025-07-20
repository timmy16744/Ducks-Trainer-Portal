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
from flask_socketio import join_room, leave_room, emit
from flask import request
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
    macros_data = json.loads(log.macros) if log.macros else {}
    return {
        'id': log.id,
        'client_id': log.client_id,
        'log_date': log.log_date.isoformat() if log.log_date else None,
        'food_item': log.food_item,
        'macros': macros_data,
        'calories': macros_data.get('calories', 0),
        'protein': macros_data.get('protein', 0),
        'carbs': macros_data.get('carbs', 0),
        'fat': macros_data.get('fat', 0),
        'fiber': macros_data.get('fiber', 0),
        'sugar': macros_data.get('sugar', 0),
        'sodium': macros_data.get('sodium', 0),
        'serving_size': macros_data.get('serving_size', ''),
        'meal_type': macros_data.get('meal_type', 'other')
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

@app.route("/api/client/<client_id>/today", methods=["GET"])
def get_client_today(client_id):
    """Gets all of a client's tasks for the current day."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    today = date.today()
    
    # Get workout for today (simplified for now)
    try:
        assignment = ProgramAssignment.query.filter_by(client_id=client.id, active=True).first()
        workout = None
        if assignment:
            workout = {
                "assigned": True,
                "templateName": "Today's Workout",
                "exercises": 8,
                "estimatedDuration": 45
            }
    except Exception:
        workout = None

    # Get today's metrics (simplified)
    todays_metrics = { "water_glasses": 0, "steps": 0 }
    
    response = {
        "workout": workout,
        "metrics": todays_metrics,
        "macros": {},
        "achievements": []
    }
    return jsonify(response)

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

# --- Nutrition Log Endpoints ---
@app.route("/api/clients/<client_id>/nutrition-logs", methods=["GET"])
def get_nutrition_logs(client_id):
    """Get nutrition logs for a client, optionally filtered by date."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    date_param = request.args.get('date')
    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            logs = NutritionLog.query.filter_by(client_id=client.id, log_date=target_date).all()
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        # Default to today's logs
        today = date.today()
        logs = NutritionLog.query.filter_by(client_id=client.id, log_date=today).all()
    
    return jsonify([nutrition_log_to_dict(log) for log in logs])

@app.route("/api/clients/<client_id>/nutrition-logs", methods=["POST"])
def add_nutrition_log(client_id):
    """Add a new nutrition log entry."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    try:
        # Create nutrition log entry
        nutrition_log = NutritionLog(
            client_id=client.id,
            log_date=date.today() if not data.get('log_date') else datetime.strptime(data.get('log_date'), '%Y-%m-%d').date(),
            food_item=data.get('food_item', ''),
            macros=json.dumps({
                'calories': float(data.get('calories', 0)),
                'protein': float(data.get('protein', 0)),
                'carbs': float(data.get('carbs', 0)),
                'fat': float(data.get('fat', 0)),
                'fiber': float(data.get('fiber', 0)),
                'sugar': float(data.get('sugar', 0)),
                'sodium': float(data.get('sodium', 0)),
                'serving_size': data.get('serving_size', ''),
                'meal_type': data.get('meal_type', 'other')
            })
        )
        
        db.session.add(nutrition_log)
        db.session.commit()
        
        return jsonify({
            "message": "Nutrition log added successfully",
            "log": nutrition_log_to_dict(nutrition_log)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding nutrition log: {e}")
        return jsonify({"message": "Failed to add nutrition log"}), 500

@app.route("/api/clients/<client_id>/nutrition-logs/<log_id>", methods=["PUT"])
def update_nutrition_log(client_id, log_id):
    """Update an existing nutrition log entry."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    log = NutritionLog.query.filter_by(id=log_id, client_id=client.id).first()
    if not log:
        return jsonify({"message": "Nutrition log not found!"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    try:
        # Update nutrition log
        if 'food_item' in data:
            log.food_item = data['food_item']
        
        if any(key in data for key in ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium', 'serving_size', 'meal_type']):
            current_macros = json.loads(log.macros) if log.macros else {}
            current_macros.update({
                'calories': float(data.get('calories', current_macros.get('calories', 0))),
                'protein': float(data.get('protein', current_macros.get('protein', 0))),
                'carbs': float(data.get('carbs', current_macros.get('carbs', 0))),
                'fat': float(data.get('fat', current_macros.get('fat', 0))),
                'fiber': float(data.get('fiber', current_macros.get('fiber', 0))),
                'sugar': float(data.get('sugar', current_macros.get('sugar', 0))),
                'sodium': float(data.get('sodium', current_macros.get('sodium', 0))),
                'serving_size': data.get('serving_size', current_macros.get('serving_size', '')),
                'meal_type': data.get('meal_type', current_macros.get('meal_type', 'other'))
            })
            log.macros = json.dumps(current_macros)
        
        db.session.commit()
        return jsonify({
            "message": "Nutrition log updated successfully",
            "log": nutrition_log_to_dict(log)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating nutrition log: {e}")
        return jsonify({"message": "Failed to update nutrition log"}), 500

@app.route("/api/clients/<client_id>/nutrition-logs/<log_id>", methods=["DELETE"])
def delete_nutrition_log(client_id, log_id):
    """Delete a nutrition log entry."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    log = NutritionLog.query.filter_by(id=log_id, client_id=client.id).first()
    if not log:
        return jsonify({"message": "Nutrition log not found!"}), 404
    
    try:
        db.session.delete(log)
        db.session.commit()
        return jsonify({"message": "Nutrition log deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting nutrition log: {e}")
        return jsonify({"message": "Failed to delete nutrition log"}), 500

@app.route("/api/clients/<client_id>/nutrition-goals", methods=["GET"])
def get_nutrition_goals(client_id):
    """Get nutrition goals for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    # For now, return default goals based on client data
    # In a real app, these would be stored in the database
    goals = {
        'calories': 2000,
        'protein': 150,
        'carbs': 200,
        'fat': 65,
        'fiber': 25,
        'water': 8  # glasses
    }
    
    return jsonify(goals)

@app.route("/api/clients/<client_id>/nutrition-goals", methods=["PUT"])
def update_nutrition_goals(client_id):
    """Update nutrition goals for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    # For now, just return success
    # In a real app, these would be stored in the database
    return jsonify({"message": "Nutrition goals updated successfully"}), 200

# --- Body Stats Endpoints ---
@app.route("/api/clients/<client_id>/body-stats", methods=["GET"])
def get_body_stats(client_id):
    """Get body stats for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    stats = BodyStat.query.filter_by(client_id=client.id).order_by(BodyStat.date.desc()).all()
    return jsonify([{
        'id': stat.id,
        'client_id': stat.client_id,
        'date': stat.date.isoformat() if stat.date else None,
        'weight': stat.weight,
        'measurements': json.loads(stat.measurements) if stat.measurements else {}
    } for stat in stats])

@app.route("/api/clients/<client_id>/body-stats", methods=["POST"])
def add_body_stat(client_id):
    """Add a new body stat entry."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400
    
    try:
        # Create body stat entry
        body_stat = BodyStat(
            client_id=client.id,
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else date.today(),
            weight=float(data.get('weight')) if data.get('weight') else None,
            measurements=json.dumps({
                'chest': float(data.get('chest', 0)) if data.get('chest') else None,
                'waist': float(data.get('waist', 0)) if data.get('waist') else None,
                'hips': float(data.get('hips', 0)) if data.get('hips') else None,
                'arms': float(data.get('arms', 0)) if data.get('arms') else None,
                'thighs': float(data.get('thighs', 0)) if data.get('thighs') else None,
                'neck': float(data.get('neck', 0)) if data.get('neck') else None,
                'body_fat': float(data.get('body_fat', 0)) if data.get('body_fat') else None,
                'muscle_mass': float(data.get('muscle_mass', 0)) if data.get('muscle_mass') else None
            })
        )
        
        db.session.add(body_stat)
        db.session.commit()
        
        return jsonify({
            "message": "Body stat added successfully",
            "stat": {
                'id': body_stat.id,
                'client_id': body_stat.client_id,
                'date': body_stat.date.isoformat(),
                'weight': body_stat.weight,
                'measurements': json.loads(body_stat.measurements)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding body stat: {e}")
        return jsonify({"message": "Failed to add body stat"}), 500

# --- Progress Photos Endpoints ---
@app.route("/api/clients/<client_id>/progress-photos", methods=["GET"])
def get_progress_photos(client_id):
    """Get progress photos for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    photos = ProgressPhoto.query.filter_by(client_id=client.id).order_by(ProgressPhoto.timestamp.desc()).all()
    return jsonify([{
        'id': photo.id,
        'client_id': photo.client_id,
        'filename': photo.filename,
        'timestamp': photo.timestamp.isoformat() if photo.timestamp else None,
        'url': f'/uploads/{photo.filename}'  # Assuming files are served from uploads folder
    } for photo in photos])

@app.route("/api/clients/<client_id>/progress-photos", methods=["POST"])
def upload_progress_photo(client_id):
    """Upload a progress photo."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        try:
            import os
            import uuid
            from werkzeug.utils import secure_filename
            
            # Create unique filename
            filename = secure_filename(file.filename)
            unique_filename = f"{client.id}_{uuid.uuid4().hex}_{filename}"
            
            # Ensure upload directory exists
            upload_folder = os.path.join('backend', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # Save to database
            progress_photo = ProgressPhoto(
                client_id=client.id,
                filename=unique_filename,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(progress_photo)
            db.session.commit()
            
            return jsonify({
                "message": "Photo uploaded successfully",
                "photo": {
                    'id': progress_photo.id,
                    'client_id': progress_photo.client_id,
                    'filename': progress_photo.filename,
                    'timestamp': progress_photo.timestamp.isoformat(),
                    'url': f'/uploads/{progress_photo.filename}'
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error uploading photo: {e}")
            return jsonify({"message": "Failed to upload photo"}), 500
    
    return jsonify({"message": "Invalid file type"}), 400

def allowed_file(filename):
    """Check if file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Workout History Endpoints ---
@app.route("/api/clients/<client_id>/workout-history", methods=["GET"])
def get_workout_history(client_id):
    """Get workout history for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    # Debug: Log the client lookup
    app.logger.info(f"Looking up workout history for client_id: {client_id}, resolved to internal ID: {client.id}")
    
    logs = WorkoutLog.query.filter_by(client_id=client.id).order_by(WorkoutLog.actual_date.desc()).limit(50).all()
    
    # Debug: Log the number of logs found
    app.logger.info(f"Found {len(logs)} workout logs for client {client.id}")
    
    return jsonify([workout_log_to_dict(log) for log in logs])

@app.route("/api/workout-logs/debug", methods=["GET"])
def debug_workout_logs():
    """Debug endpoint to check all workout logs."""
    total_logs = WorkoutLog.query.count()
    recent_logs = WorkoutLog.query.order_by(WorkoutLog.actual_date.desc()).limit(5).all()
    
    return jsonify({
        "total_workout_logs": total_logs,
        "recent_logs": [workout_log_to_dict(log) for log in recent_logs]
    })

@app.route("/api/workout-logs/test-create", methods=["POST"])
def test_create_workout_log():
    """Test endpoint to create a sample workout log."""
    try:
        # Find the first client
        client = Client.query.first()
        if not client:
            return jsonify({"message": "No clients found"}), 404
        
        # Create a test workout log
        test_log = WorkoutLog(
            client_id=client.id,
            assignment_id="test_assignment",
            day_index_completed=0,
            actual_date=date.today(),
            performance_data=json.dumps({
                'performanceLog': {'ex1': [{'reps': 10, 'weight': 50, 'completed': True}]},
                'exerciseNotes': {'ex1': 'Test workout'},
                'elapsedTime': 1800
            })
        )
        
        db.session.add(test_log)
        db.session.commit()
        
        return jsonify({
            "message": "Test workout log created",
            "log": workout_log_to_dict(test_log)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating test workout log: {e}")
        return jsonify({"message": f"Failed to create test log: {str(e)}"}), 500

# --- Personal Records Endpoints ---
@app.route("/api/clients/<client_id>/personal-records", methods=["GET"])
def get_personal_records(client_id):
    """Get personal records for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    # Calculate personal records from workout logs
    logs = WorkoutLog.query.filter_by(client_id=client.id).all()
    personal_records = {}
    
    for log in logs:
        if log.performance_data:
            try:
                performance_data = json.loads(log.performance_data)
                performance_log = performance_data.get('performanceLog', {})
                
                for exercise_id, sets in performance_log.items():
                    if isinstance(sets, list):
                        for set_data in sets:
                            if set_data.get('completed') and set_data.get('weight') and set_data.get('reps'):
                                weight = float(set_data['weight'])
                                reps = int(set_data['reps'])
                                
                                # Calculate 1RM using Epley formula
                                one_rm = weight * (1 + reps / 30)
                                
                                if exercise_id not in personal_records or one_rm > personal_records[exercise_id]['one_rm']:
                                    personal_records[exercise_id] = {
                                        'weight': weight,
                                        'reps': reps,
                                        'one_rm': round(one_rm, 1),
                                        'date': log.actual_date.isoformat(),
                                        'exercise_id': exercise_id
                                    }
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
    
    return jsonify(list(personal_records.values()))

# --- Achievement System ---
@app.route("/api/clients/<client_id>/achievements", methods=["GET"])
def get_achievements(client_id):
    """Get achievements for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    # Calculate achievements based on workout logs and other data
    logs = WorkoutLog.query.filter_by(client_id=client.id).all()
    body_stats = BodyStat.query.filter_by(client_id=client.id).all()
    
    achievements = []
    
    # Workout-based achievements
    total_workouts = len(logs)
    if total_workouts >= 1:
        achievements.append({
            'id': 'first_workout',
            'title': 'First Workout',
            'description': 'Completed your first workout!',
            'icon': '🏋️‍♀️',
            'earned': True,
            'date_earned': logs[0].actual_date.isoformat() if logs else None
        })
    
    if total_workouts >= 10:
        achievements.append({
            'id': 'ten_workouts',
            'title': 'Consistency Champion',
            'description': 'Completed 10 workouts!',
            'icon': '🔥',
            'earned': True,
            'date_earned': None
        })
    
    if total_workouts >= 50:
        achievements.append({
            'id': 'fifty_workouts',
            'title': 'Fitness Warrior',
            'description': 'Completed 50 workouts!',
            'icon': '💪',
            'earned': True,
            'date_earned': None
        })
    
    # Weight tracking achievements
    if len(body_stats) >= 5:
        achievements.append({
            'id': 'weight_tracker',
            'title': 'Progress Tracker',
            'description': 'Logged weight 5 times!',
            'icon': '📊',
            'earned': True,
            'date_earned': None
        })
    
    return jsonify(achievements)

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
        # Try alternative field names that might be used
        assignment_id = data.get('assignmentId') or data.get('program_assignment_id')
        
    if not assignment_id:
        app.logger.warning(f"No assignment ID found in workout data: {data}")
        return jsonify({"message": "Assignment ID required"}), 400

    # Debug: Log the data being received
    app.logger.info(f"Logging workout for client: {client_id} (resolved to {client.id}), assignment_id: {assignment_id}")
    app.logger.info(f"Workout data keys: {list(data.keys())}")
    
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
        app.logger.info(f"Successfully logged workout with ID: {workout_log.id}")
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

# --- Message Endpoints ---
@app.route("/api/clients/<client_id>/messages", methods=["GET"])
def get_messages(client_id):
    """Get messages for a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    messages = Message.query.filter_by(client_id=client.id).order_by(Message.timestamp.asc()).all()
    return jsonify([message_to_dict(message) for message in messages])

@app.route("/api/clients/<client_id>/messages", methods=["POST"])
def send_message(client_id):
    """Send a message to/from a client."""
    client = find_client(client_id)
    if not client:
        return jsonify({"message": "Client not found!"}), 404
    
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({"message": "Message text is required"}), 400
    
    try:
        message = Message(
            client_id=client.id,
            sender_type=data.get('sender_type', 'client'),
            text=data['text']
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Emit the message to all connected clients for this client_id
        message_data = message_to_dict(message)
        socketio.emit('new_message', message_data, room=f"client_{client.id}")
        
        return jsonify(message_data), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error sending message: {e}")
        return jsonify({"message": "Failed to send message"}), 500

# --- Socket.IO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")

@socketio.on('join')
def handle_join(data):
    """Join a client-specific room for real-time messaging."""
    client_id = data.get('client_id')
    if client_id:
        # Normalize client ID for room naming
        client = find_client(client_id)
        if client:
            room = f"client_{client.id}"
            join_room(room)
            print(f"Client {request.sid} joined room {room}")
        else:
            print(f"Invalid client_id for join: {client_id}")

@socketio.on('message')
def handle_message(data):
    """Handle incoming socket message."""
    client_id = data.get('client_id')
    sender_type = data.get('sender_type', 'client')
    text = data.get('text', '').strip()
    
    if not client_id or not text:
        return
    
    client = find_client(client_id)
    if not client:
        return
    
    try:
        # Save message to database
        message = Message(
            client_id=client.id,
            sender_type=sender_type,
            text=text
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Broadcast message to room
        message_data = message_to_dict(message)
        socketio.emit('new_message', message_data, room=f"client_{client.id}")
        
    except Exception as e:
        app.logger.error(f"Error handling socket message: {e}")
        db.session.rollback() 