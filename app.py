from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, FileField, FloatField
from wtforms.validators import DataRequired, EqualTo
from flask_wtf.file import FileField, FileAllowed
from flask_migrate import Migrate
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///translink.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database and login manager
db = SQLAlchemy(app)
# Initialize Flask-Migrate and Flask-Script
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True)
    trucks = db.relationship('Truck', backref='owner', lazy=True)
    cargos = db.relationship('Cargo', backref='owner', lazy=True)  # Relationship with Cargo
    truck_requests = db.relationship('TruckRequest', backref='requester', lazy=True)  # Relationship with TruckRequest

# Truck Model
class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    routes = db.Column(db.String(300), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    available = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='Available')  # Add the status field
    requests = db.relationship('TruckRequest', backref='truck', lazy=True)  # Relationship with TruckRequest

class TruckRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    truck_id = db.Column(db.Integer, db.ForeignKey('truck.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Declined

# Cargo Model
class Cargo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # Weight in kg
    origin = db.Column(db.String(300), nullable=False)  # Origin field remains
    destination = db.Column(db.String(300), nullable=False)  # Use destination instead of route
    image = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='Available')  # Add the status field


# Login Manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registration Form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    avatar = FileField('Profile Picture')
    submit = SubmitField('Register')

# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Truck Form
class TruckForm(FlaskForm):
    name = StringField('Truck Name', validators=[DataRequired()])
    routes = StringField('Routes (Comma separated)', validators=[DataRequired()])
    image = FileField('Truck Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Post Truck')

# Cargo Form
class CargoForm(FlaskForm):
    name = StringField('Cargo Name', validators=[DataRequired()])
    weight = FloatField('Weight (kg)', validators=[DataRequired()])
    origin = StringField('Origin', validators=[DataRequired()])
    destination = StringField('Destination', validators=[DataRequired()])  # Replace route with destination
    image = FileField('Cargo Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Post Cargo')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}
# Routes
@app.route('/', methods=['GET', 'POST'])
def landing():
    login_form = LoginForm()
    register_form = RegisterForm()

    # Handle login
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and check_password_hash(user.password, login_form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    # Handle registration
    if register_form.validate_on_submit():
        existing_user = User.query.filter_by(username=register_form.username.data).first()
        if existing_user:
            flash('Username already taken. Choose another one.', 'danger')
        else:
            hashed_pw = generate_password_hash(register_form.password.data, method='pbkdf2:sha256')
            avatar_filename = None
            if register_form.avatar.data:
                if allowed_file(register_form.avatar.data.filename):
                    avatar_filename = secure_filename(register_form.avatar.data.filename)
                    register_form.avatar.data.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))
                else:
                    flash('Invalid avatar file type. Only images allowed.', 'danger')
                    return render_template('landing.html', login_form=login_form, register_form=register_form)

            new_user = User(username=register_form.username.data, password=hashed_pw, avatar=avatar_filename)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('landing'))  # Stay on the same page after successful registration

    # Render the landing page with login and registration forms inside modals
    return render_template('landing.html', login_form=login_form, register_form=register_form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('landing'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    truck_form = TruckForm()
    cargo_form = CargoForm()

    # Handle Post Truck form submission
    if truck_form.validate_on_submit() and 'submit_truck' in request.form:
        image_filename = None
        if truck_form.image.data:
            image_filename = secure_filename(truck_form.image.data.filename)
            truck_form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        new_truck = Truck(
            name=truck_form.name.data,
            routes=truck_form.routes.data,
            image=image_filename,
            user_id=current_user.id
        )
        db.session.add(new_truck)
        db.session.commit()
        flash('Truck posted successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Handle Post Cargo form submission
    if cargo_form.validate_on_submit() and 'submit_cargo' in request.form:
        image_filename = None
        if cargo_form.image.data:
            image_filename = secure_filename(cargo_form.image.data.filename)
            cargo_form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        new_cargo = Cargo(
            name=cargo_form.name.data,
            weight=cargo_form.weight.data,
            origin=cargo_form.origin.data,
            destination=cargo_form.destination.data,
            image=image_filename,
            user_id=current_user.id,
            status='Available'
        )
        db.session.add(new_cargo)
        db.session.commit()
        flash('Cargo posted successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Fetch trucks and cargos for the current user
    trucks = Truck.query.filter_by(user_id=current_user.id).all()
    cargos = Cargo.query.filter_by(user_id=current_user.id).all()

    # Pass the avatar to the template
    return render_template(
        'dashboard.html',
        trucks=trucks,
        cargos=cargos,
        truck_form=truck_form,
        cargo_form=cargo_form,
        user_avatar=current_user.avatar  # Pass the avatar
    )

@app.route('/toggle_cargo_status/<int:cargo_id>', methods=['POST'])
@login_required
def toggle_cargo_status(cargo_id):
    cargo = Cargo.query.get_or_404(cargo_id)
    
    # Ensure the current user is the owner of the cargo
    if cargo.user_id != current_user.id:
        flash('You are not authorized to update this cargo.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Toggle the status between 'Available' and 'Transported'
    if cargo.status == 'Available':
        cargo.status = 'Transported'
    else:
        cargo.status = 'Available'
    
    db.session.commit()
    flash(f'Cargo status updated to {cargo.status}.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_truck/<int:truck_id>', methods=['POST'])
@login_required
def delete_truck(truck_id):
    # Fetch the truck to delete
    truck = Truck.query.get_or_404(truck_id)

    # Ensure the truck belongs to the current user
    if truck.user_id != current_user.id:
        flash('You are not authorized to delete this truck.', 'danger')
        return redirect(url_for('dashboard'))

    # Delete the truck and commit changes
    db.session.delete(truck)
    db.session.commit()

    flash('Truck deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/toggle_availability/<int:truck_id>', methods=['POST'])
@login_required
def toggle_availability(truck_id):
    truck = Truck.query.get_or_404(truck_id)

    # Ensure the truck belongs to the current user
    if truck.user_id != current_user.id:
        flash('You are not authorized to update this truck.', 'danger')
        return redirect(url_for('dashboard'))

    # Toggle the availability
    truck.available = not truck.available
    db.session.commit()
    flash('Truck availability updated successfully!', 'success')

    return redirect(url_for('dashboard'))

@app.route('/delete_cargo/<int:cargo_id>', methods=['POST'])
@login_required
def delete_cargo(cargo_id):
    # Fetch the cargo to delete
    cargo = Cargo.query.get_or_404(cargo_id)

    # Ensure the cargo belongs to the current user
    if cargo.user_id != current_user.id:
        flash('You are not authorized to delete this truck.', 'danger')
        return redirect(url_for('dashboard'))

    # Delete the cargo and commit changes
    db.session.delete(cargo)
    db.session.commit()

    flash('Cargo deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/browse', methods=['GET'])
def browse():
    # Retrieve search query, filter status, and filter type from GET parameters
    search_query = request.args.get('search', default='', type=str)
    filter_status = request.args.get('status', default='', type=str)
    filter_type = request.args.get('filter', default='', type=str)

    # Retrieve truck and cargo pages from GET parameters
    truck_page = request.args.get('truck_page', default=1, type=int)
    cargo_page = request.args.get('cargo_page', default=1, type=int)

    # Query trucks based on search query and filter status
    trucks = Truck.query.filter(Truck.name.contains(search_query))
    if filter_status == 'Available':
        trucks = trucks.filter(Truck.available == True)
    elif filter_status == 'Booked':
        trucks = trucks.filter(Truck.available == False)

    # Query cargo based on search query and filter status
    cargos = Cargo.query.filter(Cargo.name.contains(search_query))
    if filter_status == 'Available':
        cargos = cargos.filter(Cargo.status == 'Available')
    elif filter_status == 'Booked':
        cargos = cargos.filter(Cargo.status != 'Available')

    # Apply pagination to trucks and cargos
    trucks = trucks.paginate(page=truck_page, per_page=6)
    cargos = cargos.paginate(page=cargo_page, per_page=6)

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
        cargos=cargos
    )

@app.route('/truck_request/<int:truck_id>', methods=['POST'])
@login_required
def request_truck(truck_id):
    truck = Truck.query.get_or_404(truck_id)
    request = TruckRequest(truck_id=truck.id, requester_id=current_user.id)
    db.session.add(request)
    db.session.commit()
    flash('Truck request sent successfully', 'success')
    return redirect(url_for('browse'))

@app.route('/approve_request/<int:request_id>', methods=['GET'])
@login_required
def approve_request(request_id):
    request = TruckRequest.query.get_or_404(request_id)
    request.status = 'Approved'
    db.session.commit()
    flash('Truck request approved successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/decline_request/<int:request_id>', methods=['GET'])
@login_required
def decline_request(request_id):
    request = TruckRequest.query.get_or_404(request_id)
    request.status = 'Declined'
    db.session.commit()
    flash('Truck request declined successfully', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)