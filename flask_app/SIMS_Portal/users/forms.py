from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, FileField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from SIMS_Portal.models import User, Emergency, NationalSociety, EmergencyType, Portfolio, Skill, Language

class RegistrationForm(FlaskForm):
	firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=40)])
	lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=40)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	ns_id = QuerySelectField('National Society Country', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True)
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
	submit = SubmitField('Update Profile')
	
	def validate_email(self, email):
		if email.data != current_user.email and current_user.is_admin != 1:
			user = User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError('Email is already registered.')

class RequestResetForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')
	
	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is None:
			raise ValidationError('There is no account with that email.')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=24)])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=6, max=24), EqualTo('password')])
	submit = SubmitField('Reset Password')