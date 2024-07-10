from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField, FileField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc
from flask_wtf.file import FileField, FileAllowed
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import User, Emergency, NationalSociety, EmergencyType

class NewEmergencyForm(FlaskForm):
	emergency_name = StringField('Emergency Name', validators=[DataRequired(), Length(min=5, max=100)])
	emergency_location_id = QuerySelectField('Affected Country (Primary)', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True, validators=[DataRequired()])
	emergency_type_id = QuerySelectField('Emergency Type', query_factory=lambda:EmergencyType.query.order_by(asc(EmergencyType.emergency_type_name)).all(), get_label='emergency_type_name', allow_blank=True, validators=[DataRequired()])
	emergency_glide = StringField('GLIDE Number')
	emergency_go_id = IntegerField('GO ID Number')
	activation_details = TextAreaField('SIMS Activation Details', validators=[DataRequired()])
	slack_channel = StringField('Slack Channel ID')
	dropbox_url = StringField('Dropbox URL')
	github_repo = StringField('GitHub Repo')
	submit = SubmitField('Create Emergency')
	
class UpdateEmergencyForm(FlaskForm):
	emergency_name = StringField('Emergency Name', validators=[DataRequired(), Length(min=5, max=100)])
	emergency_location_id = QuerySelectField('Affected Country (Primary)', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True)
	emergency_type_id = QuerySelectField('Emergency Type', query_factory=lambda:EmergencyType.query.all(), get_label='emergency_type_name', allow_blank=True)
	emergency_glide = StringField('GLIDE Number')
	emergency_go_id = IntegerField('GO ID Number')
	activation_details = TextAreaField('SIMS Activation Details')
	slack_channel = StringField('Slack Channel ID')
	dropbox_url = StringField('Dropbox URL')
	github_repo = StringField('GitHub Repo')
	submit = SubmitField('Update Emergency')