import sys
import os
from pathlib import Path

# Ensure project root is on PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.app import create_app
except ImportError:
    from app import create_app

# Create application instance
app = create_app()

# For Vercel compatibility
application = app

if __name__ == "__main__":
    app.run(debug=False) 