from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField, FileField, FloatField
from wtforms.validators import DataRequired, EqualTo
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
    origin = db.Column(db.String(300), nullable=False)  # New 'origin' field
    destination = db.Column(db.String(300), nullable=False)
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
    image = FileField('Truck Image')
    submit = SubmitField('Post Truck')

# Cargo Form
class CargoForm(FlaskForm):
    name = StringField('Cargo Name', validators=[DataRequired()])
    weight = FloatField('Weight (kg)', validators=[DataRequired()])
    origin = StringField('Origin', validators=[DataRequired()])  # Add the origin field
    destination = StringField('Destination', validators=[DataRequired()])
    image = FileField('Cargo Image')
    submit = SubmitField('Post Cargo')

# Routes
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already taken. Choose another one.', 'danger')
        else:
            hashed_pw = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            avatar_filename = None
            if form.avatar.data:
                avatar_filename = secure_filename(form.avatar.data.filename)
                form.avatar.data.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))
            new_user = User(username=form.username.data, password=hashed_pw, avatar=avatar_filename)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('landing'))

@app.route('/dashboard')
@login_required
def dashboard():
    trucks = Truck.query.filter_by(user_id=current_user.id).all()
    cargos = Cargo.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', trucks=trucks, cargos=cargos)

@app.route('/post-truck', methods=['GET', 'POST'])
@login_required
def post_truck():
    form = TruckForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        new_truck = Truck(name=form.name.data, routes=form.routes.data, image=image_filename, user_id=current_user.id)
        db.session.add(new_truck)
        db.session.commit()
        flash('Truck posted successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('post_truck.html', form=form)

@app.route('/post-cargo', methods=['GET', 'POST'])
@login_required
def post_cargo():
    form = CargoForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        # Remove any non-numeric characters from weight and convert to float
        weight = ''.join(filter(str.isdigit, form.weight.data))
        weight = float(weight)
        
        # Create a new Cargo object with all fields, including 'origin'
        new_cargo = Cargo(
            name=form.name.data, 
            weight=weight, 
            origin=form.origin.data,  # Add origin to the Cargo model
            destination=form.destination.data, 
            image=image_filename, 
            user_id=current_user.id
        )
        
        # Add the new cargo to the database and commit
        db.session.add(new_cargo)
        db.session.commit()
        
        flash('Cargo posted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('post_cargo.html', form=form)

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

@app.route('/edit_truck/<int:truck_id>', methods=['GET', 'POST'])
@login_required
def edit_truck(truck_id):
    # Fetch the truck to edit
    truck = Truck.query.get_or_404(truck_id)

    # Ensure the truck belongs to the current user
    if truck.user_id != current_user.id:
        flash('You are not authorized to edit this truck.', 'danger')
        return redirect(url_for('dashboard'))

    # Create the form
    form = TruckForm()

    if form.validate_on_submit():
        # Update the truck with new data
        truck.name = form.name.data
        truck.routes = form.routes.data

        # Handle image upload if a new image is uploaded
        if form.image.data:
            image_filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            truck.image = image_filename

        db.session.commit()
        flash('Truck updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Pre-fill the form with existing truck data
    form.name.data = truck.name
    form.routes.data = truck.routes
    return render_template('edit_truck.html', form=form, truck=truck)

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

@app.route('/edit_cargo/<int:cargo_id>', methods=['GET', 'POST'])
@login_required
def edit_cargo(cargo_id):
    # Fetch the cargo to edit
    cargo = Cargo.query.get_or_404(cargo_id)

    # Ensure the cargo belongs to the current user
    if cargo.user_id != current_user.id:
        flash('You are not authorized to edit this cargo.', 'danger')
        return redirect(url_for('dashboard'))

    # Create the form
    form = CargoForm()

    if form.validate_on_submit():
        # Update the cargo with new data
        cargo.name = form.name.data
        cargo.weight = float(form.weight.data)
        cargo.destination = form.destination.data

        # Handle image upload if a new image is uploaded
        if form.image.data:
            image_filename = secure_filename(form.image.data.filename)
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            cargo.image = image_filename

        db.session.commit()
        flash('Cargo updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    # Pre-fill the form with existing cargo data
    form.name.data = cargo.name
    form.weight.data = str(cargo.weight)
    form.destination.data = cargo.destination

    return render_template('edit_cargo.html', form=form, cargo=cargo)

@app.route('/browse', methods=['GET'])
def browse():
    cargo_status = request.args.get('cargo_status', 'available')  # Default is available
    truck_status = request.args.get('truck_status', 'available')  # Default is available
    search_query = request.args.get('search', '')  # Get search query if any
    
    # Pagination settings
    cargo_page = request.args.get('cargo_page', 1, type=int)
    truck_page = request.args.get('truck_page', 1, type=int)
    
    # Fetch filtered and paginated cargo based on status and search query
    cargo_query = Cargo.query.filter(Cargo.status == cargo_status)
    if search_query:
        cargo_query = cargo_query.filter(Cargo.origin.contains(search_query) | Cargo.destination.contains(search_query))
    cargo = cargo_query.paginate(page=cargo_page, per_page=6, error_out=False)  # Corrected argument names

    # Fetch filtered and paginated trucks based on availability and search query
    if truck_status == 'available':
        truck_query = Truck.query.filter(Truck.available == True)  # Only available trucks
    else:
        truck_query = Truck.query.filter(Truck.available == False)  # Only booked trucks
    
    if search_query:
        truck_query = truck_query.filter(Truck.name.contains(search_query))  # Assuming search is by truck name
    
    trucks = truck_query.paginate(page=truck_page, per_page=6, error_out=False)  # Corrected argument names

    return render_template('browse.html', cargo=cargo, trucks=trucks, 
                           cargo_status=cargo_status, truck_status=truck_status,
                           search_query=search_query)

if __name__ == '__main__':
    app.run(debug=True)
