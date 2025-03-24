from app import db

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=False)
    capacity = db.Column(db.String(50), nullable=False)
    available_routes = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="Available")  # Available / Booked
    
    owner = db.relationship("User", back_populates="trucks")

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "image_url": self.image_url,
            "description": self.description,
            "capacity": self.capacity,
            "available_routes": self.available_routes,
            "status": self.status,
        }
