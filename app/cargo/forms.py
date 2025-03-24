from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

# Form to post new cargo
class CargoForm(FlaskForm):
    description = TextAreaField("Cargo Description", validators=[DataRequired(), Length(min=5, max=500)])
    from_location = StringField("Pickup Location", validators=[DataRequired(), Length(min=2, max=100)])
    to_location = StringField("Destination", validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField("Post Cargo")

# Form to search for cargo transport
class CargoSearchForm(FlaskForm):
    from_location = StringField("Pickup Location", validators=[Length(min=2, max=100)])
    to_location = StringField("Destination", validators=[Length(min=2, max=100)])
    submit = SubmitField("Search Cargo")
