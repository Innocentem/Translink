from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_wtf.file import FileField, FileAllowed

# Registration Form
class RegisterForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[DataRequired(), Length(min=3, max=20, message="Username must be between 3 and 20 characters")]
    )
    password = PasswordField(
        'Password', 
        validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters long")]
    )
    confirm_password = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password', message="Passwords must match")]
    )
    avatar = FileField(
        'Profile Picture', 
        validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Only JPG, PNG, and JPEG images are allowed!')]
    )
    role = SelectField(
        'Role', 
        choices=[('truck_fleet_owner', 'Truck Fleet Owner'), ('transportation_service_user', 'Transportation Service User')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Register')
class LoginForm(FlaskForm):
    username = StringField(
        'Username', 
        validators=[DataRequired()]
    )
    password = PasswordField(
        'Password', 
        validators=[DataRequired()]
    )
    submit = SubmitField('Login')
# Truck Form (For Truck Fleet Owners)
class TruckForm(FlaskForm):
    name = StringField('Truck Name', validators=[DataRequired()])
    plate_number = StringField('Plate Number', validators=[DataRequired()])
    driver_name = StringField('Driver Name', validators=[DataRequired()])
    driver_contact = StringField('Driver Contact')
    routes = StringField('Routes', validators=[DataRequired()])
    image = FileField('Truck Image', validators=[DataRequired()])

# Cargo Form (For Transportation Service Users)
class CargoForm(FlaskForm):
    name = StringField(
        'Cargo Name', 
        validators=[DataRequired()]
    )
    weight = FloatField(
        'Weight (kg)', 
        validators=[DataRequired()]
    )
    origin = StringField(
        'Origin', 
        validators=[DataRequired()]
    )
    destination = StringField(
        'Destination', 
        validators=[DataRequired()]
    )
    timeframe = StringField(
        'Timeframe (e.g., Within 3 days)', 
        validators=[DataRequired()]
    )
    image = FileField(
        'Cargo Image', 
        validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')]
    )
    submit = SubmitField('Post Cargo')

# Truck Request Form (For Booking a Truck)
class TruckRequestForm(FlaskForm):
    truck_id = SelectField(
        'Select Truck', 
        coerce=int, 
        validators=[DataRequired()]
    )  # This will be populated dynamically in the view
    cargo_id = SelectField(
        'Select Cargo', 
        coerce=int, 
        validators=[DataRequired()]
    )
    submit = SubmitField('Request Truck')
