from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, current_app, send_file, make_response
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, urljoin
import os
from io import BytesIO, StringIO
import csv
from datetime import datetime, timedelta
from models import User, Truck, TruckRequest, Cargo, CargoRequest, ActivityLog, SystemMetrics
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
    if request.method == 'GET' and current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_routes.analytics_dashboard'))
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
    try:
        print(f"Dashboard route - User: {current_user.username}, Role: {current_user.role}")
        
        if current_user.role == 'admin':
            # Redirect admin users to analytics dashboard
            return redirect(url_for('admin_routes.analytics_dashboard'))
            
        elif current_user.role == 'truck_fleet_owner':
            trucks = Truck.query.filter_by(user_id=current_user.id).all()
            return render_template('dashboard.html', 
                                trucks=trucks,
                                current_user=current_user)
            
        elif current_user.role == 'transportation_service_user':
            sent_requests = TruckRequest.query.filter_by(user_id=current_user.id).all()
            return render_template('dashboard.html', 
                                sent_requests=sent_requests,
                                current_user=current_user)
            
        else:
            flash('Invalid user role!', 'danger')
            return redirect(url_for('auth_routes.landing'))
            
    except Exception as e:
        print(f"Dashboard Error: {str(e)}")
        db.session.rollback()
        flash('Error loading dashboard. Please try again.', 'danger')
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

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    # Get date range for filtering
    days = request.args.get('days', '30')  # Default to 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(days))
    
    # Gather statistics
    stats = {
        'total_users': User.query.count(),
        'new_users': User.query.filter(User.created_at >= start_date).count(),
        'total_trucks': Truck.query.count(),
        'new_trucks': Truck.query.filter(Truck.created_at >= start_date).count(),
        'active_requests': TruckRequest.query.filter(TruckRequest.status == 'Pending').count(),
        'completed_requests': TruckRequest.query.filter(
            TruckRequest.status == 'Accepted',
            TruckRequest.request_date >= start_date
        ).count()
    }
    
    # Get recent activities
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_trucks = Truck.query.order_by(Truck.created_at.desc()).limit(5).all()
    recent_requests = TruckRequest.query.order_by(TruckRequest.request_date.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_trucks=recent_trucks,
                         recent_requests=recent_requests,
                         days=days)

@admin_routes.route('/admin/report')
@login_required
@role_required('admin')
def generate_report():
    try:
        report_type = request.args.get('report_type')
        output = StringIO()
        
        # Create CSV writer with proper encoding
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        
        if report_type == 'activity_log':
            # Write activity log report
            writer.writerow(['Timestamp', 'User', 'Action', 'Details'])
            activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
            
            for activity in activities:
                writer.writerow([
                    activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    activity.user.username,
                    activity.action,
                    activity.details
                ])
            filename = f'activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        elif report_type == 'system_metrics':
            # Write system metrics report
            writer.writerow(['Timestamp', 'Metric', 'Value'])
            metrics = SystemMetrics.query.order_by(SystemMetrics.timestamp.desc()).all()
            
            for metric in metrics:
                writer.writerow([
                    metric.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    metric.metric_name,
                    metric.metric_value
                ])
            filename = f'system_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        else:
            flash('Invalid report type requested', 'danger')
            return redirect(url_for('admin_routes.analytics_dashboard'))

        # Prepare the response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response

    except Exception as e:
        print(f"Report Generation Error: {str(e)}")
        flash('Error generating report', 'danger')
        return redirect(url_for('admin_routes.analytics_dashboard'))

@admin_routes.route('/analytics')
@login_required
@role_required('admin')
def analytics_dashboard():
    try:
        # Get time period from request args (default to last 30 days)
        days = request.args.get('days', '30')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(days))

        # Gather analytics data
        analytics = {
            'users': {
                'total': User.query.count(),
                'new': User.query.filter(User.created_at >= start_date).count(),
                'by_role': {
                    'truck_fleet_owner': User.query.filter_by(role='truck_fleet_owner').count(),
                    'transportation_service_user': User.query.filter_by(role='transportation_service_user').count()
                }
            },
            'trucks': {
                'total': Truck.query.count(),
                'available': Truck.query.filter_by(available=True).count(),
                'booked': Truck.query.filter_by(available=False).count()
            },
            'requests': {
                'total': TruckRequest.query.count(),
                'pending': TruckRequest.query.filter_by(status='Pending').count(),
                'accepted': TruckRequest.query.filter_by(status='Accepted').count(),
                'rejected': TruckRequest.query.filter_by(status='Rejected').count()
            }
        }

        # Get recent activities with user details
        recent_activities = (
            ActivityLog.query
            .join(User)
            .order_by(ActivityLog.timestamp.desc())
            .limit(10)
            .all()
        )

        # Get system metrics
        system_metrics = SystemMetrics.get_latest_metrics()

        # Calculate success rates
        total_completed = analytics['requests']['accepted'] + analytics['requests']['rejected']
        success_rate = (
            (analytics['requests']['accepted'] / total_completed * 100)
            if total_completed > 0 else 0
        )

        return render_template('admin/analytics.html',
                             analytics=analytics,
                             recent_activities=recent_activities,
                             system_metrics=system_metrics,
                             success_rate=success_rate,
                             days=days)

    except Exception as e:
        print(f"Analytics Error: {str(e)}")
        flash('Error loading analytics dashboard', 'danger')
        db.session.rollback()
        return redirect(url_for('dashboard_routes.dashboard'))

@admin_routes.route('/analytics/report')
@login_required
def generate_analytics_report():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard_routes.dashboard'))
    
    report_type = request.args.get('type', 'users')
    start_date = request.args.get('start_date', 
                                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Create CSV file in memory
    output = BytesIO()
    writer = csv.writer(output)
    
    if report_type == 'users':
        # Write users report
        writer.writerow(['Username', 'Role', 'Registration Date'])
        users = User.query.filter(
            User.created_at.between(start_date, end_date)
        ).all()
        for user in users:
            writer.writerow([user.username, user.role, user.created_at])
            
    elif report_type == 'trucks':
        # Write trucks report
        writer.writerow(['Name', 'Plate Number', 'Owner', 'Status', 'Added Date'])
        trucks = Truck.query.filter(
            Truck.created_at.between(start_date, end_date)
        ).all()
        for truck in trucks:
            writer.writerow([
                truck.name, 
                truck.plate_number, 
                truck.owner.username,
                'Available' if truck.available else 'Booked',
                truck.created_at
            ])
            
    elif report_type == 'requests':
        # Write requests report
        writer.writerow(['Date', 'Truck', 'Requester', 'Status', 'Origin', 'Destination'])
        requests = TruckRequest.query.filter(
            TruckRequest.request_date.between(start_date, end_date)
        ).all()
        for req in requests:
            writer.writerow([
                req.request_date,
                req.truck.name,
                req.requester.username,
                req.status,
                req.origin,
                req.destination
            ])
    
    # Prepare response
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'translink_analytics_{report_type}_{datetime.now().strftime("%Y%m%d")}.csv'
    )