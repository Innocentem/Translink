from extensions import db
from flask_login import UserMixin
from sqlalchemy.orm import validates, relationship
from sqlalchemy import func
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default='default_avatar.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

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

    @property
    def total_trucks(self):
        return len(self.trucks)

    @property
    def total_cargos(self):
        return len(self.cargos)

    @property
    def request_success_rate(self):
        total_requests = TruckRequest.query.filter_by(user_id=self.id).count()
        if total_requests == 0:
            return 0
        successful = TruckRequest.query.filter_by(
            user_id=self.id, 
            status='Accepted'
        ).count()
        return (successful / total_requests) * 100

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    routes = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(200), nullable=False, default='default_truck.jpg')
    available = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    driver_contact = db.Column(db.String(20), nullable=True)
    
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
    cargo_image = db.Column(db.String(200), nullable=True)  # Add this line
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

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship('User', backref=db.backref('activities', lazy='dynamic'))

    @staticmethod
    def log_activity(user_id, action, details=None):
        log = ActivityLog(user_id=user_id, action=action, details=details)
        db.session.add(log)
        db.session.commit()

class SystemMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def update_metric(cls, name, value):
        metric = cls(metric_name=name, metric_value=value)
        db.session.add(metric)
        db.session.commit()

    @classmethod
    def get_latest_metrics(cls):
        return cls.query.order_by(cls.timestamp.desc()).limit(10).all()
