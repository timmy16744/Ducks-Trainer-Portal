import json
import os
from datetime import datetime

# --- Constants ---
CLIENTS_FILE = os.path.join(os.path.dirname(__file__), "database", "clients.json")
EXERCISES_FILE = os.path.join(os.path.dirname(__file__), "database", "exercises.json")
WORKOUT_ASSIGNMENTS_FILE = os.path.join(os.path.dirname(__file__), "database", "workout_assignments.json")

# --- Helper Functions ---
def read_json_file(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding='utf-8') as f:
        return json.load(f)

def write_json_file(file_path, data):
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Main Achievement Logic ---
def check_for_new_pbs(client_id, new_logged_data):
    """
    Checks if a new workout log contains any new Personal Bests (PBs).
    """
    all_assignments = read_json_file(WORKOUT_ASSIGNMENTS_FILE)
    all_exercises = read_json_file(EXERCISES_FILE)
    
    client_assignments = [a for a in all_assignments if a.get("client_id") == client_id and a.get("status") == "completed"]
    
    newly_unlocked = []

    for exercise_id, new_log_list in new_logged_data.items():
        # Find the exercise name
        exercise_info = next((e for e in all_exercises if str(e.get("id")) == str(exercise_id)), None)
        if not exercise_info:
            continue
        
        exercise_name = exercise_info.get("name", "Unknown Exercise")
        
        # Find max weight from the new log
        max_new_weight = 0
        for s in new_log_list:
            weight = float(s.get("weight", 0))
            if weight > max_new_weight:
                max_new_weight = weight
        
        if max_new_weight == 0:
            continue

        # Find historical max weight for this exercise
        historical_max_weight = 0
        for assignment in client_assignments:
            # Skip the current log by checking completion time proximity
            if "logged_data" in assignment and exercise_id in assignment["logged_data"]:
                for s in assignment["logged_data"][exercise_id]:
                    weight = float(s.get("weight", 0))
                    if weight > historical_max_weight:
                        historical_max_weight = weight
                        
        if max_new_weight > historical_max_weight:
            achievement = {
                "id": f"ach_pb_{exercise_id}_{datetime.now().timestamp()}",
                "type": "PB",
                "title": f"New PB: {exercise_name}",
                "description": f"You lifted {max_new_weight}kg!",
                "unlocked_at": datetime.now().isoformat(),
                "icon": "🏋️"
            }
            newly_unlocked.append(achievement)
            
    return newly_unlocked

def add_achievements_to_client(client_id, achievements):
    """
    Adds a list of achievements to a client's profile.
    """
    if not achievements:
        return

    clients = read_json_file(CLIENTS_FILE)
    for client in clients:
        if client["id"] == client_id:
            if "achievements" not in client:
                client["achievements"] = []
            
            # Avoid adding duplicate achievements
            existing_ids = {ach["id"] for ach in client["achievements"]}
            for ach in achievements:
                if ach["id"] not in existing_ids:
                    client["achievements"].append(ach)
            
            write_json_file(CLIENTS_FILE, clients)
            break 