from flask import Blueprint, request, jsonify
from app import db
from app.models import Cargo
from flask_login import login_required, current_user

cargo = Blueprint("cargo", __name__)

# Add new cargo
@cargo.route("/add", methods=["POST"])
@login_required
def add_cargo():
    data = request.get_json()

    if not data or not all(k in data for k in ("description", "from_location", "to_location")):
        return jsonify({"error": "Missing required fields"}), 400

    new_cargo = Cargo(
        customer_id=current_user.id,
        description=data["description"],
        from_location=data["from_location"],
        to_location=data["to_location"],
        status="Pending",
    )

    db.session.add(new_cargo)
    db.session.commit()

    return jsonify({"message": "Cargo added successfully", "cargo": new_cargo.to_dict()}), 201


# Get all cargo listings
@cargo.route("/", methods=["GET"])
@login_required
def get_all_cargo():
    cargo_list = Cargo.query.all()
    return jsonify([cargo.to_dict() for cargo in cargo_list]), 200


# Get cargo by ID
@cargo.route("/<int:cargo_id>", methods=["GET"])
@login_required
def get_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    return jsonify(cargo.to_dict()), 200


# Update cargo details
@cargo.route("/update/<int:cargo_id>", methods=["PUT"])
@login_required
def update_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)

    if cargo.customer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if "description" in data:
        cargo.description = data["description"]
    if "from_location" in data:
        cargo.from_location = data["from_location"]
    if "to_location" in data:
        cargo.to_location = data["to_location"]
    if "status" in data:
        cargo.status = data["status"]

    db.session.commit()

    return jsonify({"message": "Cargo updated successfully", "cargo": cargo.to_dict()}), 200


# Delete cargo
@cargo.route("/delete/<int:cargo_id>", methods=["DELETE"])
@login_required
def delete_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)

    if cargo.customer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(cargo)
    db.session.commit()

    return jsonify({"message": "Cargo deleted successfully"}), 200
