from .models import db, Achievement, WorkoutLog

def check_for_new_pbs(client_id, new_performance_data):
    """
    Checks if a new workout log contains any new Personal Bests (PBs)
    by comparing against historical workout logs in the database.
    """
    newly_unlocked = []

    for exercise_id, sets in new_performance_data.items():
        # Find the exercise name from the workout log itself if possible, or query
        # This part might need adjustment depending on how exercise names are stored/passed
        
        max_new_weight = 0
        for s in sets:
            weight = float(s.get("weight", 0))
            if weight > max_new_weight:
                max_new_weight = weight
        
        if max_new_weight == 0:
            continue

        # Query historical max weight for this exercise from WorkoutLog
        historical_max = db.session.query(db.func.max(db.func.json_extract(WorkoutLog.performance_data, f'$.{exercise_id}[*].weight'))) \
            .filter(WorkoutLog.client_id == client_id) \
            .scalar()
        
        historical_max_weight = float(historical_max) if historical_max else 0
                        
        if max_new_weight > historical_max_weight:
            # This logic assumes we can get the exercise name. 
            # For now, using ID as a placeholder.
            achievement = Achievement(
                client_id=client_id,
                type="PB",
                title=f"New PB for Exercise {exercise_id}",
                description=f"You lifted {max_new_weight}kg!",
                icon="🏋️"
            )
            newly_unlocked.append(achievement)
            
    return newly_unlocked

def add_achievements_to_client(client_id, achievements):
    """
    Adds a list of achievements to a client's profile in the database.
    """
    if not achievements:
        return

    for ach in achievements:
        # To avoid duplicates, you might want to check if a similar achievement exists
        # This is simplified; a more robust check might be needed
        existing = Achievement.query.filter_by(client_id=client_id, title=ach.title).first()
        if not existing:
            db.session.add(ach)
    
    db.session.commit() 