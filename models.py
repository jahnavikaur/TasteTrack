from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_on    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships — each user owns their own data
    pantry_items  = db.relationship('PantryItem', backref='owner', lazy=True, cascade='all, delete-orphan')
    weekly_plans  = db.relationship('WeeklyPlan',  backref='owner', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class PantryItem(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_name   = db.Column(db.String(100), nullable=False)
    quantity    = db.Column(db.Float, nullable=False)
    unit        = db.Column(db.String(20), default='unit')
    expiry_date = db.Column(db.Date, nullable=True)
    added_on    = db.Column(db.DateTime, default=datetime.utcnow)


class WeeklyPlan(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week_start  = db.Column(db.Date, nullable=False)
    plan_data   = db.Column(db.Text, nullable=False)
    created_on  = db.Column(db.DateTime, default=datetime.utcnow)