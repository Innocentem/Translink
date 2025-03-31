from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from utils import allowed_file  
from forms import RegisterForm, LoginForm, TruckForm, CargoForm
import os
from sqlalchemy.orm import joinedload



# Blueprints for routes
auth_routes = Blueprint('auth_routes', __name__)
dashboard_routes = Blueprint('dashboard_routes', __name__)
browse_routes = Blueprint('browse_routes', __name__)

# Landing Page (Login & Registration)
@auth_routes.route('/', methods=['GET', 'POST'])
def landing():
    login_form = LoginForm()
    register_form = RegisterForm()

    # Debug: Print if request method is POST
    print("Request Method:", request.method)

    # Handle login
    if login_form.validate_on_submit():
        print("Login Form Validated!")  # Debugging
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and check_password_hash(user.password, login_form.password.data):
            login_user(user)
            return redirect(url_for('dashboard_routes.dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    # Handle registration
    if request.method == 'POST' and register_form.validate_on_submit():
        print("Register Form Validated!")  # Debugging
        existing_user = User.query.filter_by(username=register_form.username.data).first()
        
        if existing_user:
            flash('Username already taken. Choose another one.', 'danger')
        else:
            hashed_pw = generate_password_hash(register_form.password.data, method='pbkdf2:sha256')
            print("Hashed Password:", hashed_pw)  # Debugging

            avatar_filename = None
            if register_form.avatar.data:
                if allowed_file(register_form.avatar.data.filename):
                    avatar_filename = secure_filename(register_form.avatar.data.filename)
                    avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], avatar_filename)
                    register_form.avatar.data.save(avatar_path)
                    print("Avatar saved at:", avatar_path)  # Debugging
                else:
                    flash('Invalid avatar file type. Only images allowed.', 'danger')
                    return render_template('landing.html', login_form=login_form, register_form=register_form)

            # Create new user
            new_user = User(username=register_form.username.data, password=hashed_pw, avatar=avatar_filename)
            db.session.add(new_user)
            db.session.commit()
            print("New user registered:", new_user.username)  # Debugging
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth_routes.landing'))  # Redirect after registration

    # Debug: If form validation fails, print errors
    if request.method == 'POST':
        print("Register Form Errors:", register_form.errors)  # Debugging

    # Render the landing page
    return render_template('landing.html', login_form=login_form, register_form=register_form)
# Dashboard Route

@dashboard_routes.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    truck_form = TruckForm()
    cargo_form = CargoForm()

    def handle_file_upload(form, field_name):
        """Handles file upload for both truck and cargo forms."""
        image_filename = None
        if getattr(form, field_name).data:
            image_filename = secure_filename(getattr(form, field_name).data.filename)
            getattr(form, field_name).data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename))
        return image_filename

    # Handle Post Truck form submission
    if truck_form.validate_on_submit() and 'submit_truck' in request.form:
        image_filename = handle_file_upload(truck_form, 'image')

        new_truck = Truck(
            name=truck_form.name.data,
            routes=truck_form.routes.data,
            image=image_filename,
            user_id=current_user.id
        )
        
        # Check if the truck already exists in the database
        existing_truck = Truck.query.filter_by(name=new_truck.name, user_id=current_user.id).first()
        if existing_truck:
            flash('Truck with the same name already exists!', 'error')
        else:
            db.session.add(new_truck)
            db.session.commit()
            flash('Truck added successfully!', 'success')
            return redirect(url_for('dashboard_routes.dashboard'))

    # Handle Post Cargo form submission
    if cargo_form.validate_on_submit() and 'submit_cargo' in request.form:
        image_filename = handle_file_upload(cargo_form, 'image')

        new_cargo = Cargo(
            name=cargo_form.name.data,
            weight=cargo_form.weight.data,
            origin=cargo_form.origin.data,
            destination=cargo_form.destination.data,
            image=image_filename,
            user_id=current_user.id
        )

        # Check if the cargo already exists in the database
        existing_cargo = Cargo.query.filter_by(name=new_cargo.name, user_id=current_user.id).first()
        if existing_cargo:
            flash('Cargo with the same name already exists!', 'error')
        else:
            db.session.add(new_cargo)
            db.session.commit()
            flash('Cargo added successfully!', 'success')
            return redirect(url_for('dashboard_routes.dashboard'))

    # Eagerly load trucks, cargos, and their associated requests (with requester)
    trucks = Truck.query.filter_by(user_id=current_user.id).options(joinedload(Truck.requests).joinedload(TruckRequest.requester)).all()
    cargos = Cargo.query.filter_by(user_id=current_user.id).all()

    # Pass current_user to the template to access avatar
    return render_template(
        'dashboard.html',
        truck_form=truck_form,
        cargo_form=cargo_form,
        trucks=trucks,
        cargos=cargos,
        user=current_user  # Pass current_user to the template
    )

@auth_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth_routes.landing'))

# Browse Trucks and Cargo
@browse_routes.route('/browse', methods=['GET'])
def browse():
    # Retrieve search query, filter status, and filter type from GET parameters
    search_query = request.args.get('search', default='', type=str)
    filter_status = request.args.get('status', default='', type=str)
    filter_type = request.args.get('filter', default='', type=str)

    # Retrieve truck and cargo pages from GET parameters
    truck_page = request.args.get('truck_page', default=1, type=int)
    cargo_page = request.args.get('cargo_page', default=1, type=int)

    # Query trucks based on search query and filter status
    trucks_query = db.session.query(Truck).filter(Truck.name.contains(search_query))
    if filter_status == 'Available':
        trucks_query = trucks_query.filter(Truck.available == True)
    elif filter_status == 'Booked':
        trucks_query = trucks_query.filter(Truck.available == False)

    # Query cargo based on search query and filter status
    cargos_query = db.session.query(Cargo).filter(Cargo.name.contains(search_query))
    if filter_status == 'Available':
        cargos_query = cargos_query.filter(Cargo.status == 'Available')
    elif filter_status == 'Booked':
        cargos_query = cargos_query.filter(Cargo.status != 'Available')

    # Apply pagination to trucks and cargos
    trucks = trucks_query.paginate(page=truck_page, per_page=6)
    cargos = cargos_query.paginate(page=cargo_page, per_page=6)

    # Separate 'Booked' trucks and 'Transported' cargo into their own sections
    booked_trucks = [truck for truck in trucks.items if not truck.available]
    available_trucks = [truck for truck in trucks.items if truck.available]

    transported_cargos = [cargo for cargo in cargos.items if cargo.status != 'Available']
    available_cargos = [cargo for cargo in cargos.items if cargo.status == 'Available']

    return render_template(
        'browse.html',
        booked_trucks=booked_trucks,
        available_trucks=available_trucks,
        transported_cargos=transported_cargos,
        available_cargos=available_cargos,
        search_query=search_query,
        filter_status=filter_status,
        filter_type=filter_type,
        trucks=trucks,
        cargos=cargos # Pass current_user to the template
    )

@dashboard_routes.route('/toggle_availability/<int:truck_id>', methods=['POST'])
@login_required
def toggle_availability(truck_id):
    truck = Truck.query.get_or_404(truck_id)

    # Ensure the truck belongs to the current user
    if truck.user_id != current_user.id:
        flash('You are not authorized to update this truck.', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))

    # Toggle the availability
    truck.available = not truck.available
    db.session.commit()
    flash('Truck availability updated successfully!', 'success')

    return redirect(url_for('dashboard_routes.dashboard'))
@dashboard_routes.route('/delete_truck/<int:truck_id>', methods=['POST'])
@login_required
def delete_truck(truck_id):
    # Fetch the truck to delete
    truck = Truck.query.get_or_404(truck_id)

    # Ensure the truck belongs to the current user
    if truck.user_id != current_user.id:
        flash('You are not authorized to delete this truck.', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))

    # Delete the truck and commit changes
    db.session.delete(truck)
    db.session.commit()

    flash('Truck deleted successfully!', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))

@dashboard_routes.route('/delete_cargo/<int:cargo_id>', methods=['POST'])
@login_required
def delete_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)

    if cargo.user_id != current_user.id:
        flash('You are not authorized to delete this truck.', 'danger')  # <== Bug: Should be "cargo"
        return redirect(url_for('dashboard_routes.dashboard'))

    db.session.delete(cargo)
    db.session.commit()

    flash('Cargo deleted successfully!', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))
@dashboard_routes.route('/toggle_cargo_status/<int:cargo_id>', methods=['POST'])
@login_required
def toggle_cargo_status(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    
    # Ensure the current user is the owner of the cargo
    if cargo.user_id != current_user.id:
        flash('You are not authorized to update this cargo.', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    # Toggle the status between 'Available' and 'Transported'
    if cargo.status == 'Available':
        cargo.status = 'Transported'
    else:
        cargo.status = 'Available'

    db.session.commit()
    flash('Cargo status updated successfully!', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))

@browse_routes.route('/truck_request/<int:truck_id>', methods=['POST'])
@login_required
def request_truck(truck_id):
    existing_request = TruckRequest.query.filter_by(truck_id=truck_id, requester_id=current_user.id).first()
    if existing_request:
        flash('You have already requested this truck.', 'warning')
    else:
        truck = Truck.query.get_or_404(truck_id)
        new_request = TruckRequest(truck_id=truck.id, requester_id=current_user.id)
        db.session.add(new_request)
        db.session.commit()
        flash('Truck request sent successfully', 'success')

    return redirect(url_for('browse_routes.browse'))

@dashboard_routes.route('/approve_request/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    request = TruckRequest.query.get_or_404(request_id)
    request.status = 'Approved'
    db.session.commit()
    flash('Truck request approved successfully', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))

@dashboard_routes.route('/decline_request/<int:request_id>', methods=['POST'])
@login_required
def decline_request(request_id):
    request = TruckRequest.query.get_or_404(request_id)
    request.status = 'Declined'
    db.session.commit()
    flash('Truck request declined successfully', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))