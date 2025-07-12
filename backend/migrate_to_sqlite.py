import json
from app import get_session, Client, Exercise, read_json_file, CLIENTS_FILE, EXERCISES_FILE  # Import models and paths

# Example for clients
clients = read_json_file(CLIENTS_FILE)
session = get_session()
for c in clients:
    client_data = {
        'id': c.get('id'),
        'name': c.get('name'),
        'email': c.get('email'),
        'unique_url': c.get('unique_url'),
        'features': json.dumps(c.get('features')),
        'points': c.get('points', 0),
        'daily_metrics': json.dumps(c.get('daily_metrics', {}))
        # Map other fields
    }
    session.add(Client(**client_data))
session.commit()

# Similar for exercises
exercises = read_json_file(EXERCISES_FILE)
for e in exercises:
    session.add(Exercise(**e))
session.commit()
session.close()
print('Migration complete.') 