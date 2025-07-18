import json
import os
import uuid
from app import app, db, Client, WorkoutTemplate, ProgramAssignment, WorkoutLog, Exercise

# --- Configuration ---
CLIENTS_FILE = os.path.join("database", "clients.json")
EXERCISES_FILE = os.path.join("database", "exercises.json")
WORKOUT_TEMPLATES_FILE = os.path.join("database", "workout_templates.json")

def read_json_file(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
            # Handle cases where the JSON might be an object with a key, e.g., {"exercises": [...]}
            if isinstance(data, dict) and "exercises" in data:
                return data["exercises"]
            return data # Assume it's a list directly if not an object with "exercises"
        except json.JSONDecodeError:
            return [] # Return empty list if JSON is invalid

def migrate_data():
    with app.app_context():
        db.create_all()

        # Migrate clients
        clients_data = read_json_file(CLIENTS_FILE)
        for client_data in clients_data:
            if not isinstance(client_data, dict): # Skip if not a dictionary
                continue
            
            # Check if client with this email already exists
            existing_client = Client.query.filter_by(email=client_data.get('email')).first()
            if existing_client:
                print(f"Skipping client {client_data.get('name')} due to duplicate email: {client_data.get('email')}")
                continue

            client = Client(
                id=client_data.get('id', str(uuid.uuid4())),
                name=client_data.get('name'),
                email=client_data.get('email'),
                unique_url=f"http://localhost:3000/client/{str(uuid.uuid4())}", # Generate new unique URL
                features=json.dumps(client_data.get('features', {})),
                points=client_data.get('points', 0),
                daily_metrics=json.dumps(client_data.get('daily_metrics', {})),
                archived=client_data.get('archived', False)
            )
            db.session.add(client)

        # Migrate workout templates
        templates_data = read_json_file(WORKOUT_TEMPLATES_FILE)
        for template_data in templates_data:
            if not isinstance(template_data, dict): # Skip if not a dictionary
                continue
            
            # Check if template with this ID already exists
            existing_template = WorkoutTemplate.query.get(template_data.get('id'))
            if existing_template:
                print(f"Skipping workout template {template_data.get('name')} due to duplicate ID: {template_data.get('id')}")
                continue

            # Prepare days field – support legacy 'exercises' key by wrapping into a single-day structure
            if 'days' in template_data:
                days_json = json.dumps(template_data['days'])
            elif 'exercises' in template_data:
                # Legacy flat exercises list -> wrap into a single day with one group
                legacy_exercises = template_data['exercises']
                days_json = json.dumps([
                    {
                        "dayName": "Day 1",
                        "groups": [
                            {
                                "groupName": "Exercises",
                                "exercises": legacy_exercises
                            }
                        ]
                    }
                ])
            else:
                days_json = json.dumps([])

            template = WorkoutTemplate(
                id=template_data.get('id', f"wt_{uuid.uuid4()}"),
                name=template_data.get('name'),
                description=template_data.get('description'),
                days=days_json,
                tags=json.dumps(template_data.get('tags', []))
            )
            db.session.add(template)

        # Migrate exercises
        exercises_data = read_json_file(EXERCISES_FILE)
        for exercise_data in exercises_data:
            if not isinstance(exercise_data, dict): # Skip if not a dictionary
                continue
            
            # Check if exercise with this ID already exists
            existing_exercise = Exercise.query.get(exercise_data.get('id'))
            if existing_exercise:
                print(f"Skipping exercise {exercise_data.get('name')} due to duplicate ID: {exercise_data.get('id')}")
                continue

            exercise = Exercise(
                id=exercise_data.get('id', f"exr_{uuid.uuid4()}"),
                name=exercise_data.get('name'),
                instructions=exercise_data.get('instructions'),
                media_url=exercise_data.get('gifUrl'), # Corrected key from gifUrl
                body_part=exercise_data.get('bodyPart'),
                equipment=exercise_data.get('equipment'),
                category=exercise_data.get('target'), # Using target as category for now
                muscles=json.dumps(exercise_data.get('secondaryMuscles', [])) # Corrected key from secondaryMuscles
            )
            db.session.add(exercise)

        db.session.commit()
        print("Data migration completed successfully!")

if __name__ == '__main__':
    migrate_data()