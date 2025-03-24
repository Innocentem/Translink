from app import db

class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    from_location = db.Column(db.String(100), nullable=False)
    to_location = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending / Matched / Delivered

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "description": self.description,
            "from_location": self.from_location,
            "to_location": self.to_location,
            "status": self.status
        }
