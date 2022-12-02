from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user
from wtforms import StringField, PasswordField, FileField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import User, Emergency, NationalSociety, EmergencyType, Portfolio, Skill, Language

class AdminEditUserForm(FlaskForm):
	is_admin = SelectField('Admin Status', choices=[0,1])
	submit = SubmitField('Update User Info')