import requests
import json
from datetime import datetime, timezone
import os
from .models import db, Exercise, Category, Muscle, Equipment
import pathlib
from urllib.parse import urlparse

# TODO: For production, store this securely (e.g., environment variable)
EXERCISEDB_API_KEY = "d609e59cdemshf0bba6158527178p1f3dd5jsn2048dd3f9fa0"
EXERCISEDB_BASE_URL = "https://exercisedb.p.rapidapi.com"

def sync_exercises_from_exercisedb():
    """
    Fetches all exercises from the ExerciseDB API, transforms them,
    and saves them into the database efficiently.
    """
    # --- Step 1: Fetch all data from API ---
    all_exercises_data = []
    offset = 0
    limit = 100

    headers = {
        "x-rapidapi-host": "exercisedb.p.rapidapi.com",
        "x-rapidapi-key": EXERCISEDB_API_KEY
    }
    url = f"{EXERCISEDB_BASE_URL}/exercises"

    print("Starting exercise fetch from ExerciseDB API...")
    while True:
        params = {"limit": limit, "offset": offset}
        try:
            print(f"Fetching exercises with offset: {offset}...")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            batch = response.json()

            if not batch:
                print("No more exercises to fetch.")
                break
            
            all_exercises_data.extend(batch)
            offset += len(batch)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from ExerciseDB API: {e}")
            return {"status": "error", "message": f"Failed to fetch data: {e}"}

    print(f"Successfully fetched {len(all_exercises_data)} exercises from API. Processing...")

    # --- Step 2: Process and save data in a single transaction ---
    
    # Caches to hold newly created related items (category, muscle, etc.)
    # to avoid redundant database queries within the loop.
    category_cache = {}
    equipment_cache = {}
    muscle_cache = {}

    media_root = pathlib.Path(__file__).parent / 'uploads' / 'exercise_media'
    media_root.mkdir(parents=True, exist_ok=True)

    def get_or_create_local(session, model, name, cache):
        """
        Local helper to get an object from cache or DB, 
        or create it without committing.
        """
        if not name:
            return None
        if name in cache:
            return cache[name]
        
        instance = session.query(model).filter_by(name=name).first()
        if instance:
            cache[name] = instance
            return instance
        else:
            instance = model(name=name)
            session.add(instance)
            cache[name] = instance
            return instance

    synced_count = 0
    updated_any = False
    try:
        for ex_data in all_exercises_data:
            exercise_id = f"exr_exercisedb_{ex_data['id']}"
            
            # Skip if exercise already exists
            if existing := db.session.query(Exercise).get(exercise_id):
                # Update media path if missing
                if existing.local_media_path is None:
                    # Attempt to download
                    gif_url = ex_data.get("gifUrl", "").strip()
                    local_path = None
                    if gif_url:
                        file_ext = pathlib.Path(urlparse(gif_url).path).suffix or '.gif'
                        filename = f"{exercise_id}{file_ext}"
                        file_path = media_root / filename
                        if not file_path.exists():
                            try:
                                resp = requests.get(gif_url, stream=True, timeout=20)
                                resp.raise_for_status()
                                with open(file_path, 'wb') as fd:
                                    for chunk in resp.iter_content(chunk_size=8192):
                                        if chunk:
                                            fd.write(chunk)
                            except Exception as dl_e:
                                print(f"Failed to download {gif_url}: {dl_e}")
                        if file_path.exists():
                            local_path = str(file_path.relative_to(pathlib.Path(__file__).parent))
                    if local_path:
                        existing.local_media_path = local_path
                        updated_any = True
                # Update instructions if they are not stored as JSON array yet
                try:
                    json.loads(existing.instructions)
                except Exception:
                    # Reformat instructions
                    instructions_data = ex_data.get("instructions", [])
                    if isinstance(instructions_data, str):
                        instructions_data = [instructions_data]
                    existing.instructions = json.dumps([str(step).strip() for step in instructions_data if str(step).strip()])
                    updated_any = True

                continue

            # Get or create related objects using the local helper
            category = get_or_create_local(db.session, Category, ex_data.get("bodyPart"), category_cache)
            equipment = get_or_create_local(db.session, Equipment, ex_data.get("equipment"), equipment_cache)
            
            target_muscle = get_or_create_local(db.session, Muscle, ex_data.get("target"), muscle_cache)
            
            secondary_muscles = [
                get_or_create_local(db.session, Muscle, m_name, muscle_cache) 
                for m_name in ex_data.get("secondaryMuscles", [])
            ]

            all_muscles = {m for m in [target_muscle] + secondary_muscles if m}

            # Download media
            local_path = None
            gif_url = ex_data.get("gifUrl", "").strip()
            if gif_url:
                file_ext = pathlib.Path(urlparse(gif_url).path).suffix or '.gif'
                filename = f"{exercise_id}{file_ext}"
                file_path = media_root / filename
                if not file_path.exists():
                    try:
                        resp = requests.get(gif_url, stream=True, timeout=20)
                        resp.raise_for_status()
                        with open(file_path, 'wb') as fd:
                            for chunk in resp.iter_content(chunk_size=8192):
                                if chunk:
                                    fd.write(chunk)
                    except Exception as dl_e:
                        print(f"Failed to download {gif_url}: {dl_e}")
                if file_path.exists():
                    local_path = str(file_path.relative_to(pathlib.Path(__file__).parent))

            # Ensure instructions are stored as a JSON array of strings
            instructions_data = ex_data.get("instructions", [])
            if isinstance(instructions_data, str):
                instructions_data = [instructions_data]
            instructions_str = json.dumps([str(step).strip() for step in instructions_data if str(step).strip()])

            new_exercise = Exercise(
                id=exercise_id,
                name=ex_data.get("name", "Unknown Exercise"),
                instructions=instructions_str,
                media_url=gif_url,
                local_media_path=local_path,
                category=category,
                equipment=equipment,
                muscles=list(all_muscles)
            )
            db.session.add(new_exercise)
            synced_count += 1
        
        # --- Step 3: Commit the entire transaction ---
        if synced_count > 0 or updated_any:
            print(f"Committing changes to the database (new: {synced_count}, updated: {updated_any})...")
            db.session.commit()
            print(f"Successfully synced and saved {synced_count} new exercises.")
            return {"status": "success", "message": f"Synced {synced_count} new exercises. Updated media for existing exercises."}
        else:
            print("No new exercises to add or media to update. Database is already up-to-date.")
            return {"status": "success", "message": "Database is already up-to-date."}

    except Exception as e:
        db.session.rollback()
        print(f"An unexpected error occurred during database processing: {e}")
        return {"status": "error", "message": f"Database processing failed: {e}"}


if __name__ == '__main__':
    # This part needs to be run within a Flask app context to work
    # from app import app
    # with app.app_context():
    #     sync_exercises_from_exercisedb()
    print("This script must be run within a Flask application context.") 