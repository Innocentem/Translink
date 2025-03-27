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

# Truck Model
class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    routes = db.Column(db.String(300), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    available = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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
    search_query = request.args.get('search', '')
    truck_status = request.args.get('truck_status', 'all')
    cargo_status = request.args.get('cargo_status', 'all')

    # Pagination for Trucks
    truck_page = request.args.get('truck_page', 1, type=int)
    trucks = Truck.query.paginate(page=truck_page, per_page=6)

    # Pagination for Cargo
    cargo_page = request.args.get('cargo_page', 1, type=int)
    cargo_query = Cargo.query

    # Filter cargos by status if specified
    if cargo_status != 'all':
        cargo_query = cargo_query.filter(Cargo.status == cargo_status)

    # Filter cargos by search query if specified
    if search_query:
        cargo_query = cargo_query.filter(Cargo.name.ilike(f'%{search_query}%'))

    # Paginate cargos
    cargos = cargo_query.paginate(page=cargo_page, per_page=6)

    # Debugging output
    print("Trucks:", trucks.items)
    print("Cargos:", cargos.items)

    # Pass the correct variables to the template
    return render_template(
        'browse.html',
        trucks=trucks,
        cargos=cargos,  # Ensure 'cargos' is passed here
        search_query=search_query,
        truck_status=truck_status,
        cargo_status=cargo_status
    )

if __name__ == '__main__':
    app.run(debug=True)
