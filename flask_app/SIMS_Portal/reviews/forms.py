from flask_wtf import FlaskForm
from SIMS_Portal import db
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, SelectField, SelectMultipleField, HiddenField, FileField
from wtforms.widgets import TextArea
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import User, Emergency, Portfolio, Skill, Language, EmergencyType, NationalSociety, Badge, Assignment, Review

class NewEmergencyReviewForm(FlaskForm):
	category = SelectField('Category', choices=[' ','Success', 'Area for Improvement', 'General Observation'])
	type = SelectField('Type', choices=[' ','Communication and Collaboration', 'Doctrine and Guidance', "Tools and Systems", 'Tasking and Prioritization', 'Other'])
	title = StringField('Title', validators=[DataRequired()])
	description = StringField('Description', widget=TextArea(), validators=[DataRequired()])
	recommendation = StringField('Recommended Action', widget=TextArea())
	follow_up = StringField('SIMS Governance Follow Up Action', widget=TextArea())
	status = SelectField('Review Item Status', choices=['Open', 'Processed', 'Dropped'])
	submit = SubmitField('Save Review Record')