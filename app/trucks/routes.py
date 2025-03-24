from flask import Blueprint, request, jsonify
from app import db
from app.models import Truck
from flask_login import login_required, current_user

trucks = Blueprint("trucks", __name__)

# Route to add a new truck
@trucks.route("/add", methods=["POST"])
@login_required
def add_truck():
    data = request.get_json()
    
    if not data or "name" not in data or "route" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    new_truck = Truck(
        owner_id=current_user.id,
        name=data["name"],
        route=data["route"],
        available=data.get("available", True),
        image_url=data.get("image_url", "")
    )

    db.session.add(new_truck)
    db.session.commit()

    return jsonify({"message": "Truck added successfully"}), 201

# Route to get all available trucks
@trucks.route("/", methods=["GET"])
def get_trucks():
    trucks = Truck.query.filter_by(available=True).all()
    return jsonify([truck.to_dict() for truck in trucks])

# Route to update truck availability
@trucks.route("/<int:truck_id>/update", methods=["PUT"])
@login_required
def update_truck(truck_id):
    truck = Truck.query.get_or_404(truck_id)

    if truck.owner_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    truck.available = data.get("available", truck.available)
    truck.route = data.get("route", truck.route)
    
    db.session.commit()
    return jsonify({"message": "Truck updated successfully"}), 200
