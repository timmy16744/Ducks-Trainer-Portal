"""Backend package
Initialises Flask app factory exports for convenience.
"""
from .app import create_app, socketio, db
 
__all__ = [
    "create_app",
    "socketio",
    "db",
] 