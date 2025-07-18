import json
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# Use the app and db from the main application
from app import app, db, Exercise

def import_exercises_from_json():
    json_file_path = os.path.join(os.path.dirname(__file__), 'database', 'exercises.json')
    
    with app.app_context():
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        exercises_to_add = data.get('exercises', [])
        print(f"Found {len(exercises_to_add)} exercises in the JSON file.")

        imported_count = 0
        skipped_count = 0

        for ex_data in exercises_to_add:
            exercise_id = ex_data.get('id')
            if not exercise_id:
                skipped_count += 1
                continue

            existing_exercise = db.session.get(Exercise, exercise_id)
            if existing_exercise:
                # Update existing record
                existing_exercise.name = ex_data.get('name')
                existing_exercise.instructions = ex_data.get('instructions')
                existing_exercise.media_url = ex_data.get('gifUrl')
            else:
                # Create new record
                new_exercise = Exercise(
                    id=exercise_id,
                    name=ex_data.get('name'),
                    instructions=ex_data.get('instructions'),
                    media_url=ex_data.get('gifUrl')
                )
                db.session.add(new_exercise)
            
            imported_count += 1

        try:
            db.session.commit()
            print(f"Successfully imported/updated {imported_count} exercises.")
            if skipped_count > 0:
                print(f"Skipped {skipped_count} entries due to missing ID.")
        except IntegrityError as e:
            db.session.rollback()
            print(f"An error occurred during import: {e}")
        except Exception as e:
            db.session.rollback()
            print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    import_exercises_from_json() 