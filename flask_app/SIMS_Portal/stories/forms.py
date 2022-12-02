from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField, FileField
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.file import FileField, FileAllowed
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import User, Emergency, NationalSociety, EmergencyType, Story

class NewStoryForm(FlaskForm):
	header_image = FileField('Header Image', validators=[FileAllowed(['jpg', 'png'])])
	header_caption = StringField('Header Image Caption')
	entry = TextAreaField('Entry (Markdown Supported)', render_kw={'style':'height: 500px'})
	submit = SubmitField('Create Story')

class UpdateStoryForm(FlaskForm):
	header_image = FileField('Header Image', validators=[FileAllowed(['jpg', 'png'])])
	header_caption = StringField('Header Image Caption')
	entry = TextAreaField('Entry (Markdown Supported)', render_kw={'style':'height: 500px'})
	submit = SubmitField('Update Story')