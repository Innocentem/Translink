# app/models.py
from app import db, bcrypt
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "fleet_owner" or "customer"
    avatar = db.Column(db.String(120), nullable=True, default="default.jpg")

    # Relationship with trucks
    trucks = db.relationship("Truck", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    image = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=False)
    capacity = db.Column(db.String(50), nullable=False)
    available_routes = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="Available")  # Available / Booked

    # Relationship with the owner
    owner = db.relationship("User", backref="trucks")

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "image": self.image,
            "description": self.description,
            "capacity": self.capacity,
            "available_routes": self.available_routes,
            "status": self.status,
            "owner": {
                "id": self.owner.id,
                "username": self.owner.username,
                "avatar": self.owner.avatar
            }
        }


class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    from_location = db.Column(db.String(100), nullable=False)
    to_location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending / Matched

    # Relationship with the customer
    customer = db.relationship("User", backref="cargo")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "description": self.description,
            "from_location": self.from_location,
            "to_location": self.to_location,
            "status": self.status,
            "customer": {
                "id": self.customer.id,
                "username": self.customer.username,
                "avatar": self.customer.avatar
            }
        }
