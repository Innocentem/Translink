from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField
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
    submit = SubmitField('Register')

# Login Form
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

# Truck Form
class TruckForm(FlaskForm):
    name = StringField(
        'Truck Name', 
        validators=[DataRequired()]
    )
    routes = StringField(
        'Routes (Comma separated)', 
        validators=[DataRequired()]
    )
    image = FileField(
        'Truck Image', 
        validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')]
    )
    submit = SubmitField('Post Truck')

# Cargo Form
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
    )  # Changed from "route" to "destination"
    image = FileField(
        'Cargo Image', 
        validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')]
    )
    submit = SubmitField('Post Cargo')
