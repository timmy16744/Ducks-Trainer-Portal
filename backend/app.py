from flask import Flask
from .extensions import db
from flask_migrate import Migrate
from flask_caching import Cache
from flask_cors import CORS
from flask_socketio import SocketIO
import os

# Ask Flask-Migrate to use “batch” mode (required for SQLite refactors later)
migrate = Migrate(render_as_batch=True)
cache = Cache()
socketio = SocketIO()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE='SimpleCache',
    )

    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + db_path.replace('\\', '/'))

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    cache.init_app(app)
    
    allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,https://ducks-trainer-portal.vercel.app").split(',')
    CORS(app,
         supports_credentials=True,
         resources={r"/api/*": {
             "origins": allowed_origins,
             "allow_headers": ["Content-Type", "Authorization"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
         }})
    socketio.init_app(app, cors_allowed_origins=allowed_origins, async_mode='eventlet')

    with app.app_context():
        from . import routes
        from . import models

        return app



