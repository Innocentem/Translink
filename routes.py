from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, urljoin
import os
from models import User, Truck, TruckRequest, Cargo, CargoRequest
from forms import RegisterForm, LoginForm
from extensions import db
from functools import wraps

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Unauthorized access!', 'danger')
                return redirect(url_for('auth_routes.landing'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/')
@auth_routes.route('/landing', methods=['GET', 'POST'])
def landing():
    # Add debug print
    print(f"Landing route - User authenticated: {current_user.is_authenticated}")
    
    # Only redirect if user is authenticated and it's a GET request
    if current_user.is_authenticated and request.method == 'GET':
        return redirect(url_for('dashboard_routes.dashboard'))
    
    # Initialize forms
    register_form = RegisterForm()
    login_form = LoginForm()
    
    # Handle login form submission
    if 'login' in request.form and login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        
        if user and check_password_hash(user.password, login_form.password.data):
            login_user(user, remember=True)  # Add remember=True
            return redirect(url_for('dashboard_routes.dashboard'))
        
        flash('Invalid username or password!', 'danger')
    
    # Handle registration form submission
    if 'register' in request.form and register_form.validate_on_submit():
        try:
            # Check for existing username
            if User.query.filter_by(username=register_form.username.data).first():
                flash('Username already exists!', 'danger')
                return render_template('landing.html', 
                                    register_form=register_form, 
                                    login_form=login_form)
            
            # Handle avatar upload
            avatar_filename = 'default-avatar.png'
            if register_form.avatar.data:
                try:
                    avatar = register_form.avatar.data
                    avatar_filename = secure_filename(f"{register_form.username.data}_{avatar.filename}")
                    avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], avatar_filename)
                    avatar.save(avatar_path)
                except Exception as e:
                    flash(f'Error uploading avatar: {str(e)}', 'danger')
                    avatar_filename = 'default-avatar.png'
            
            # Create new user
            new_user = User(
                username=register_form.username.data,
                password=generate_password_hash(register_form.password.data, method='pbkdf2:sha256'),
                role=register_form.role.data,
                avatar=avatar_filename
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth_routes.landing'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('landing.html', 
                                register_form=register_form, 
                                login_form=login_form)
    
    return render_template('landing.html', 
                         register_form=register_form, 
                         login_form=login_form)

# Add this helper function for URL safety check
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_routes.landing'))

@auth_routes.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@auth_routes.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# Create a new Blueprint for dashboard routes
dashboard_routes = Blueprint('dashboard_routes', __name__)

@dashboard_routes.route('/dashboard')
@login_required
def dashboard():
    # Add debug print
    print(f"Dashboard route - User: {current_user.username}, Role: {current_user.role}")
    
    try:
        if current_user.role == 'truck_fleet_owner':
            trucks = Truck.query.filter_by(user_id=current_user.id).all()
            return render_template('dashboard.html', trucks=trucks)
            
        elif current_user.role == 'transportation_service_user':
            sent_requests = TruckRequest.query.filter_by(user_id=current_user.id).all()
            return render_template('dashboard.html', sent_requests=sent_requests)
            
        else:
            logout_user()  # Logout user if role is invalid
            flash('Invalid user role!', 'danger')
            return redirect(url_for('auth_routes.landing'))
            
    except Exception as e:
        print(f"Dashboard Error: {str(e)}")  # Add error logging
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('auth_routes.landing'))

@dashboard_routes.route('/add_cargo', methods=['POST'])
@login_required
def add_cargo():
    if 'image' not in request.files:
        flash('No image file provided', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    image = request.files['image']
    if image.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join('static', 'uploads', filename))
        
        new_cargo = Cargo(
            name=request.form.get('name'),
            origin=request.form.get('origin'),
            destination=request.form.get('destination'),
            weight=float(request.form.get('weight')),
            image=filename,
            user_id=current_user.id,
            status='Available'
        )
        
        db.session.add(new_cargo)
        db.session.commit()
        flash('Cargo added successfully!', 'success')
    
    return redirect(url_for('dashboard_routes.dashboard'))

@dashboard_routes.route('/toggle_truck/<int:truck_id>', methods=['POST'])
@login_required
def toggle_availability(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    if truck.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    truck.available = not truck.available
    db.session.commit()
    flash('Truck status updated!', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))

@dashboard_routes.route('/toggle_cargo/<int:cargo_id>', methods=['POST'])
@login_required
def toggle_cargo_status(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    if cargo.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    cargo.status = 'Available' if cargo.status == 'Transported' else 'Transported'
    db.session.commit()
    flash('Cargo status updated!', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))

@dashboard_routes.route('/delete_truck/<int:truck_id>', methods=['POST'])
@login_required
def delete_truck(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    if truck.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    db.session.delete(truck)
    db.session.commit()
    flash('Truck deleted successfully!', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))

@dashboard_routes.route('/delete_cargo/<int:cargo_id>', methods=['POST'])
@login_required
def delete_cargo(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    if cargo.user_id != current_user.id:
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    db.session.delete(cargo)
    db.session.commit()
    flash('Cargo deleted successfully!', 'success')
    return redirect(url_for('dashboard_routes.dashboard'))

@dashboard_routes.route('/handle_request/<int:request_id>/<action>', methods=['POST'])
@login_required
@role_required('truck_fleet_owner')
def handle_request(request_id, action):
    try:
        truck_request = TruckRequest.query.get_or_404(request_id)
        
        # Verify ownership
        if truck_request.truck.user_id != current_user.id:
            flash('Unauthorized action!', 'danger')
            return redirect(url_for('dashboard_routes.dashboard'))
        
        if action == 'accept':
            truck_request.status = 'Accepted'
            truck_request.truck.available = False
            flash('Request accepted successfully!', 'success')
        elif action == 'reject':
            truck_request.status = 'Rejected'
            flash('Request rejected successfully!', 'success')
        else:
            flash('Invalid action!', 'danger')
            return redirect(url_for('dashboard_routes.dashboard'))
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error handling request: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard_routes.dashboard'))

# Create a new Blueprint for browse routes
browse_routes = Blueprint('browse_routes', __name__)

@browse_routes.route('/browse')
@login_required
def browse():
    print("Debug: Entering browse route")
    
    # Get page numbers from request args, default to 1
    truck_page = request.args.get('truck_page', 1, type=int)
    cargo_page = request.args.get('cargo_page', 1, type=int)
    
    try:
        # Query trucks and apply pagination
        truck_query = Truck.query.filter_by(available=True)
        trucks = truck_query.order_by(Truck.id.desc()).paginate(
            page=truck_page,
            per_page=6,
            error_out=False
        )
        
        # Query cargos and apply pagination
        cargo_query = Cargo.query
        cargos = cargo_query.order_by(Cargo.id.desc()).paginate(
            page=cargo_page,
            per_page=6,
            error_out=False
        )
        
        # Debug prints
        print(f"Debug: Found {trucks.total} total trucks")
        for truck in trucks.items:
            print(f"Debug: Truck - {truck.name}, {truck.plate_number}")
        
        return render_template('browse.html', 
                             trucks=trucks,
                             cargos=cargos,
                             search=request.args.get('search', ''),
                             status=request.args.get('status', ''))
    
    except Exception as e:
        print(f"Debug: Error in browse route - {str(e)}")
        flash('Error loading content', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))

@browse_routes.route('/request_truck/<int:truck_id>', methods=['POST'])
@login_required
def request_truck(truck_id):
    """Request a truck (transportation users only)"""
    if current_user.role != 'transportation_service_user':
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    try:
        truck = Truck.query.get_or_404(truck_id)
        if not truck.available:
            flash('This truck is already booked!', 'danger')
            return redirect(url_for('browse_routes.browse'))
        
        # Create new truck request
        new_request = TruckRequest(
            user_id=current_user.id,
            truck_id=truck_id,
            origin=request.form.get('origin'),
            destination=request.form.get('destination'),
            cargo_details=request.form.get('cargo_details'),
            status='Pending'
        )
        
        db.session.add(new_request)
        db.session.commit()
        flash('Truck requested successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error requesting truck: {str(e)}', 'danger')
        
    return redirect(url_for('browse_routes.browse'))

@dashboard_routes.route('/add_truck', methods=['POST'])
@login_required
def add_truck():
    """Add a new truck (truck fleet owners only)"""
    if current_user.role != 'truck_fleet_owner':
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    try:
        if 'image' not in request.files:
            flash('No image file provided', 'danger')
            return redirect(url_for('dashboard_routes.dashboard'))
        
        image = request.files['image']
        if image.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('dashboard_routes.dashboard'))
        
        # Validate required fields
        name = request.form.get('name')
        plate_number = request.form.get('plate_number')
        driver_name = request.form.get('driver_name')
        routes = request.form.get('routes')
        
        if not all([name, plate_number, driver_name]):
            flash('All fields are required', 'danger')
            return redirect(url_for('dashboard_routes.dashboard'))
        
        # Check if plate number is unique
        if Truck.query.filter_by(plate_number=plate_number).first():
            flash('A truck with this plate number already exists!', 'danger')
            return redirect(url_for('dashboard_routes.dashboard'))
        
        # Save image
        filename = secure_filename(f"{current_user.username}_{plate_number}_{image.filename}")
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        
        # Create new truck with all required fields
        new_truck = Truck(
            name=name,
            plate_number=plate_number,
            driver_name=driver_name,
            routes=routes,
            image=filename,
            user_id=current_user.id,
            available=True
        )
        
        db.session.add(new_truck)
        db.session.commit()
        flash('Truck added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding truck: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard_routes.dashboard'))

@browse_routes.route('/debug/trucks')
def debug_trucks():
    """Debug route to check trucks in database"""
    trucks = Truck.query.all()
    return {
        'total_trucks': len(trucks),
        'trucks': [{
            'id': t.id,
            'name': t.name,
            'plate_number': t.plate_number,
            'available': t.available,
            'user_id': t.user_id
        } for t in trucks]
    }