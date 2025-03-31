from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default='default_avatar.jpg')  # Default avatar image
    trucks = db.relationship('Truck', backref='user', lazy=True, cascade="all, delete-orphan")
    cargos = db.relationship('Cargo', backref='user', lazy=True, cascade="all, delete-orphan")
    truck_requests = db.relationship('TruckRequest', backref='user', lazy=True, cascade="all, delete-orphan")

# Truck Model
class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    routes = db.Column(db.String(300), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    available = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='Available')
    requests = db.relationship('TruckRequest', backref='truck', lazy=True, cascade="all, delete-orphan")

# Truck Request Model
class TruckRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id', ondelete='CASCADE'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Declined

    requester = relationship('User', backref='truck_requests_backref', lazy=True)

# Cargo Model
class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Weight in kg
    origin = db.Column(db.String(300), nullable=False)
    destination = db.Column(db.String(300), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='Available')
