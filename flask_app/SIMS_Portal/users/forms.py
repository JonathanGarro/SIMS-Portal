from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, FileField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField, RadioField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from SIMS_Portal.models import User, Emergency, NationalSociety, EmergencyType, Portfolio, Skill, Language, Profile, Region

class RegistrationForm(FlaskForm):
	firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=40)])
	lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=40)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	ns_id = QuerySelectField('National Society Country', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True)
	slack_id = StringField('SIMS Slack ID', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=24)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6, max=24), EqualTo('password')])
	submit = SubmitField('Register')
	
	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('Email is already registered.')
			
class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=24)])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')

class AssignProfileTypesForm(FlaskForm):
	user_name = QuerySelectField('Member', query_factory=lambda:User.query.order_by(User.firstname).filter(User.status == 'Active').all(), get_label='fullname', allow_blank=True)
	profiles = QuerySelectField('Profiles', query_factory=lambda:Profile.query.order_by(Profile.name).all(), get_label='name', allow_blank=True, validators=[DataRequired()])
	tier = SelectField('Tier', choices=[('',''), ('1', '1 - Foundational'), ('2', '2 - Officer'), ('3', '3 - Coordinator'), ('4', '4 - Manager')])
	submit = SubmitField('Assign')

class UpdateAccountForm(FlaskForm):
	firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=40)])
	lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=40)])
	picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
	email = StringField('Email', validators=[DataRequired(), Email()])
	job_title = StringField('Job Title')
	unit = StringField('Unit')
	ns_id = QuerySelectField('National Society Country', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True)
	bio = TextAreaField('Short Bio (Supports Markdown)', render_kw={'style':'height: 200px'})
	birthday = DateField('Birthday')
	linked_in = StringField('LinkedIn ID')
	molnix_id = IntegerField('Molnix ID')
	slack_id = StringField('SIMS Slack ID')
	twitter = StringField('Twitter Handle')
	github = StringField('Github Username')
	roles = StringField('SIMS Roles')
	messaging_number_country_code = IntegerField('Country Code', validators=[Optional()])
	messaging_number = IntegerField('Messaging Number (Integers Only)', validators=[Optional()])
	languages = SelectMultipleField('Languages', choices=lambda:[language.name for language in Language.query.order_by(Language.name).all()], render_kw={'style':'height: 400px'})
	skills = SelectMultipleField('Skills', choices=lambda:[skill.name for skill in Skill.query.order_by(Skill.name).all()], render_kw={'style':'height: 400px'})
	private_profile = BooleanField('Set Profile Visibility to Private')
	submit = SubmitField('Update Profile')
	
	def validate_email(self, email):
		if email.data != current_user.email:
			user = User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError('Email is already registered.')

class RequestResetForm(FlaskForm):
	slack_id = StringField('Slack ID', validators=[DataRequired()])
	submit = SubmitField('Request Password Reset')
	
	def validate_slack(self, email):
		user = User.query.filter(User.slack_id == slack_id.data).first()
		if user is None:
			raise ValidationError('There is no account with that Slack ID.')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=24)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6, max=24), EqualTo('password')])
	submit = SubmitField('Reset Password')

class UserLocationForm(FlaskForm):
	location = StringField('Enter City and Country', validators=[DataRequired()])
	submit = SubmitField('Search')

class RegionalFocalPointForm(FlaskForm):
	user_name = QuerySelectField('Member', query_factory=lambda: User.query.order_by(User.firstname).filter(User.status == 'Active').all(), get_label='fullname', allow_blank=True)
	region = QuerySelectField('Region', query_factory=lambda: Region.query.order_by(Region.name).all(), get_label='name', allow_blank=True)
	submit = SubmitField('Assign Regional Focal Point')