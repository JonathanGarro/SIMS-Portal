from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectMultipleField
from wtforms.validators import DataRequired

class AvailabilityForm(FlaskForm):
    available = SelectMultipleField('Available Dates', validators=[DataRequired()])
    submit = SubmitField('Submit')