import requests
import json
from datetime import datetime, timezone
import os

# TODO: For production, store this securely (e.g., environment variable)
EXERCISEDB_API_KEY = "d609e59cdemshf0bba6158527178p1f3dd5jsn2048dd3f9fa0"
EXERCISEDB_BASE_URL = "https://exercisedb.p.rapidapi.com"

def sync_exercises_from_exercisedb():
    """
    Fetches all exercises from the ExerciseDB API using pagination, transforms them,
    and saves them to backend/database/exercises.json.
    """
    all_exercises = []
    offset = 0
    limit = 10  # Max limit for the Basic plan per request

    headers = {
        "x-rapidapi-host": "exercisedb.p.rapidapi.com",
        "x-rapidapi-key": EXERCISEDB_API_KEY
    }
    url = f"{EXERCISEDB_BASE_URL}/exercises"

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
            
            all_exercises.extend(batch)
            offset += limit

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from ExerciseDB API: {e}")
            return {"status": "error", "message": f"Failed to fetch data from ExerciseDB: {e}"}

    print(f"Successfully fetched a total of {len(all_exercises)} exercises from API.")
    
    exercisedb_data = all_exercises
    
    # Initialize the new exercises.json structure
    new_exercises_data = {
        "exercises": [],
        "categories": [],
        "muscles": [],
        "equipment": [],
        "sync_info": {
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "source_api": "ExerciseDB",
            "total_exercises_synced": 0
        }
    }

    # Helper dictionaries to keep track of existing categories, muscles, and equipment
    category_map = {}
    muscle_map = {}
    equipment_map = {}

    category_id_counter = 1
    muscle_id_counter = 1
    equipment_id_counter = 1

    for ex in exercisedb_data:
        # Map ExerciseDB fields to your local schema
        instructions_text = "\\n".join(ex.get("instructions", []))
        
        # Using bodyPart as category
        category_name = ex.get("bodyPart")
        if category_name and category_name not in category_map:
            category_map[category_name] = category_id_counter
            new_exercises_data["categories"].append({"id": category_id_counter, "name": category_name})
            category_id_counter += 1
        
        # Handle target muscles
        exercise_muscles = []
        target_muscle = ex.get("target")
        if target_muscle and target_muscle not in muscle_map:
            muscle_map[target_muscle] = muscle_id_counter
            new_exercises_data["muscles"].append({"id": muscle_id_counter, "name": target_muscle})
            muscle_id_counter += 1
        if target_muscle:
            exercise_muscles.append(muscle_map[target_muscle])

        # Handle secondary muscles
        exercise_secondary_muscles = []
        for sec_muscle in ex.get("secondaryMuscles", []):
            if sec_muscle and sec_muscle not in muscle_map:
                muscle_map[sec_muscle] = muscle_id_counter
                new_exercises_data["muscles"].append({"id": muscle_id_counter, "name": sec_muscle})
                muscle_id_counter += 1
            if sec_muscle:
                exercise_secondary_muscles.append(muscle_map[sec_muscle])

        # Handle equipment
        exercise_equipment = []
        equipment_name = ex.get("equipment")
        if equipment_name and equipment_name not in equipment_map:
            equipment_map[equipment_name] = equipment_id_counter
            new_exercises_data["equipment"].append({"id": equipment_id_counter, "name": equipment_name})
            equipment_id_counter += 1
        if equipment_name:
            exercise_equipment.append(equipment_map[equipment_name])


        new_exercises_data["exercises"].append({
            "id": f"exr_exercisedb_{ex['id']}",
            "exercisedb_id": ex["id"],
            "name": ex.get("name", "Unknown Exercise"),
            "instructions": instructions_text,
            "gifUrl": ex.get("gifUrl", ""), 
            "bodyPart": category_name,
            "target": target_muscle,
            "equipment": equipment_name,
            "secondaryMuscles": ex.get("secondaryMuscles", []),
            "difficulty": ex.get("difficulty", "intermediate"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_custom": False
        })

    new_exercises_data["sync_info"]["total_exercises_synced"] = len(new_exercises_data["exercises"])

    try:
        # Define the correct path relative to the backend script
        db_path = os.path.join(os.path.dirname(__file__), 'database', 'exercises.json')
        db_dir = os.path.dirname(db_path)

        # Ensure the database directory exists
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # Overwrite the old database/exercises.json
        if os.path.exists(db_path):
            os.remove(db_path)
        
        with open(db_path, "w") as f:
            json.dump(new_exercises_data, f, indent=2)
        
        print(f"Successfully synced and saved {len(new_exercises_data['exercises'])} exercises.")
        return {"status": "success", "message": f"Successfully synced {len(new_exercises_data['exercises'])} exercises from ExerciseDB."}
    except IOError as e:
        print(f"Error writing to exercises.json: {e}")
        return {"status": "error", "message": f"Failed to write exercises to file: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}

if __name__ == '__main__':
    sync_exercises_from_exercisedb() 