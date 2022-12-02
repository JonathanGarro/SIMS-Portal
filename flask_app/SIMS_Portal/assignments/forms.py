from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField
from flask_sqlalchemy import SQLAlchemy
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import User, Emergency, Assignment

class NewAssignmentForm(FlaskForm):
	user_id = QuerySelectField('SIMS Member', query_factory=lambda:User.query.filter_by(status='Active').order_by('firstname'), get_label='fullname', allow_blank=True)
	emergency_id = QuerySelectField('Emergency', query_factory=lambda:Emergency.query.all(), get_label='emergency_name', allow_blank=True)
	role = SelectField("Role Type", choices=['', 'SIMS Remote Coordinator', 'FACT/CAP Information Management', 'Information Management Coordinator', 'Information Analyst', 'Primary Data Collection Officer', 'Mapping and Visualization Officer', 'Remote IM Support'])
	start_date = DateTimeField('Start Date', format='%Y-%m-%d')
	end_date = DateTimeField('End Date', format='%Y-%m-%d')
	remote = BooleanField('Remote?')
	assignment_details = TextAreaField('Assignment Description')
	submit = SubmitField('Create Assignment')
	
class UpdateAssignmentForm(FlaskForm):
	user_id = QuerySelectField('SIMS Member', query_factory=lambda:User.query.filter_by(status='Active'), get_label='fullname', allow_blank=True)
	emergency_id = QuerySelectField('Emergency', query_factory=lambda:Emergency.query.all(), get_label='emergency_name', allow_blank=True)
	role = SelectField("Role Type", choices=['', 'SIMS Remote Coordinator', 'FACT/CAP Information Management', 'Information Management Coordinator', 'Information Analyst', 'Primary Data Collection Officer', 'Mapping and Visualization Officer', 'Remote IM Support'])
	start_date = DateTimeField('Start Date', format='%Y-%m-%d')
	end_date = DateTimeField('End Date', format='%Y-%m-%d')
	remote = BooleanField('Remote?')
	assignment_details = TextAreaField('Assignment Description')
	submit = SubmitField('Update Assignment')