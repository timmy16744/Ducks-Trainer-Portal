import sys
import os
from pathlib import Path

# Ensure project root is on PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.app import create_app, socketio  # prefer packaged import
except ImportError:
    from app import create_app, socketio  # fallback when backend is not a package

app = create_app()

# For Vercel, we need to export the app object
# Vercel will handle the server startup
def handler(request):
    return app(request.environ, request.start_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[run.py] 🚀  Starting Ducks Trainer Portal backend on port {port}...")
    socketio.run(app, host='0.0.0.0', port=port)
