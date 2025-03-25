from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    avatar = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(50), nullable=False)  # 'driver' or 'customer'
    trucks = db.relationship('Truck', backref='owner', lazy=True)

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    available = db.Column(db.Boolean, default=True)
    image = db.Column(db.String(200))
    routes = db.Column(db.String(200))  # Example: "Uganda, Kenya, Tanzania"
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class CargoRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'confirmed', 'rejected'
