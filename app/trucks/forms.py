from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Optional

class TruckForm(FlaskForm):
    name = StringField("Truck Name", validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10)])
    capacity = StringField("Capacity", validators=[DataRequired(), Length(min=3, max=50)])
    available_routes = StringField("Available Routes", validators=[DataRequired(), Length(min=3, max=255)])
    image_url = FileField("Truck Image", validators=[Optional()])
    status = SelectField("Status", choices=[("Available", "Available"), ("Booked", "Booked")], default="Available")
