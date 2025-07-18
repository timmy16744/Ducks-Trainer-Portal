from .extensions import db
from sqlalchemy import MetaData
import uuid
from datetime import datetime, date

# Naming-convention keeps Alembic happy on SQLite
convention = {
    "ix":  "ix_%(column_0_label)s",
    "uq":  "uq_%(table_name)s_%(column_0_name)s",
    "ck":  "ck_%(table_name)s_%(constraint_name)s",
    "fk":  "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk":  "pk_%(table_name)s"
}

class Client(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    unique_url = db.Column(db.String(200), unique=True, nullable=False)
    features = db.Column(db.Text, default='{}')
    points = db.Column(db.Integer, default=0)
    daily_metrics = db.Column(db.Text, default='{}')
    archived = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)

    # --- Extended Profile Fields ---
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height = db.Column(db.Float)        # cm
    weight = db.Column(db.Float)        # kg
    bodyfat = db.Column(db.Float)
    goals = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    injuries = db.Column(db.Text)
    lifestyle = db.Column(db.Text)
    hours_sleep = db.Column(db.Integer)
    stress_level = db.Column(db.String(20))
    hydration_level = db.Column(db.Float)  # litres per day
    nutrition_habits = db.Column(db.Text)
    workout_history = db.Column(db.Text)
    workout_frequency = db.Column(db.Integer)
    workout_preference = db.Column(db.Text)
    workout_availability = db.Column(db.Text)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Muscle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

exercise_muscle = db.Table('exercise_muscle',
    db.Column('exercise_id', db.String, db.ForeignKey('exercise.id'), primary_key=True),
    db.Column('muscle_id', db.Integer, db.ForeignKey('muscle.id'), primary_key=True)
)

class Exercise(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    media_url = db.Column(db.String(255), nullable=True)
    local_media_path = db.Column(db.String(255), nullable=True)
    bodyPart = db.Column(db.String(100), nullable=True)
    target = db.Column(db.String(100), nullable=True)
    equipment = db.Column(db.String(100), nullable=True)
    secondaryMuscles = db.Column(db.Text, nullable=True)

class WorkoutTemplate(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"wkt_{uuid.uuid4()}")
    name = db.Column(db.String(100), nullable=False)
    days = db.Column(db.Text)  # Storing days structure as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    # user_id = db.Column(db.String, db.ForeignKey('user.id')) # If you have users

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "days": self.days,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_public": self.is_public,
        }

class ProgramAssignment(db.Model):
    __table_args__ = (db.UniqueConstraint('client_id', 'active', name='_client_active_uc'),)
    id = db.Column(db.String, primary_key=True, default=lambda: f"pa_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    template_id = db.Column(db.String, db.ForeignKey('workout_template.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    current_day_index = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    client = db.relationship('Client', backref=db.backref('program_assignments', lazy=True))
    template = db.relationship('WorkoutTemplate', backref=db.backref('program_assignments', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'template_id': self.template_id,
            'start_date': self.start_date.isoformat(),
            'active': self.active,
            'current_day_index': self.current_day_index
        }

class WorkoutLog(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"log_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    assignment_id = db.Column(db.String, db.ForeignKey('program_assignment.id'), nullable=False)
    day_index_completed = db.Column(db.Integer, nullable=False)
    actual_date = db.Column(db.Date, nullable=False)
    performance_data = db.Column(db.Text, default='{}')
    client = db.relationship('Client', backref=db.backref('workout_logs', lazy=True))
    assignment = db.relationship('ProgramAssignment', backref=db.backref('workout_logs', lazy=True))

class Recipe(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"rec_{uuid.uuid4()}")
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, default='[]')
    instructions = db.Column(db.Text)
    macros = db.Column(db.Text, default='{}')

class MealPlan(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"mp_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    recipe_id = db.Column(db.String, db.ForeignKey('recipe.id'), nullable=False)
    assigned_date = db.Column(db.Date, nullable=False)
    client = db.relationship('Client', backref=db.backref('meal_plans', lazy=True))
    recipe = db.relationship('Recipe', backref=db.backref('meal_plans', lazy=True))

class NutritionLog(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"nl_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    log_date = db.Column(db.Date, nullable=False)
    food_item = db.Column(db.String(200), nullable=False)
    macros = db.Column(db.Text, default='{}')
    client = db.relationship('Client', backref=db.backref('nutrition_logs', lazy=True))

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_valid = db.Column(db.Boolean, default=True)

class Prospect(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='New')

class Resource(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"msg_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    sender_type = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    client = db.relationship('Client', backref=db.backref('messages', lazy=True))

class Achievement(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"ach_{uuid.uuid4()}")
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    icon = db.Column(db.String(10))
    client = db.relationship('Client', backref=db.backref('achievements', lazy=True))

class BodyStat(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float)
    measurements = db.Column(db.Text, default='{}')
    client = db.relationship('Client', backref=db.backref('body_stats', lazy=True))

class ProgressPhoto(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    client = db.relationship('Client', backref=db.backref('progress_photos', lazy=True))

class DailyCheckin(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    checkin_date = db.Column(db.Date, nullable=False)
    metrics = db.Column(db.Text, default='{}')
    client = db.relationship('Client', backref=db.backref('daily_checkins', lazy=True))

class Group(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    client_ids = db.Column(db.Text, default='[]')

class Alert(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String, db.ForeignKey('client.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text, default='{}')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    client = db.relationship('Client', backref=db.backref('alerts', lazy=True))

class Program(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: f"prg_{uuid.uuid4()}")
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    weeks = db.Column(db.Text, default='[]') 