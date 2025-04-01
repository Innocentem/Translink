from extensions import db
from flask_login import UserMixin
from sqlalchemy.orm import validates, relationship
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default='default_avatar.jpg')

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    # Relationships
    trucks = relationship('Truck', back_populates='owner', cascade="all, delete-orphan")
    cargos = relationship('Cargo', back_populates='owner', cascade="all, delete-orphan")
    sent_truck_requests = relationship('TruckRequest', back_populates='requester', cascade="all, delete-orphan")
    sent_cargo_requests = relationship('CargoRequest', back_populates='requester', cascade="all, delete-orphan")

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    routes = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(200), nullable=False, default='default_truck.jpg')
    available = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    owner = relationship('User', back_populates='trucks')
    truck_requests = relationship('TruckRequest', back_populates='truck', cascade="all, delete-orphan")

class TruckRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False)
    origin = db.Column(db.String(200), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    cargo_details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    requester = relationship('User', back_populates='sent_truck_requests')
    truck = relationship('Truck', back_populates='truck_requests')

class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    dimensions = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    owner = relationship('User', back_populates='cargos')
    received_requests = relationship('CargoRequest', back_populates='cargo', cascade="all, delete-orphan")

class CargoRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cargo_id = db.Column(db.Integer, db.ForeignKey('cargo.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    requester = relationship('User', back_populates='sent_cargo_requests')
    cargo = relationship('Cargo', back_populates='received_requests')
