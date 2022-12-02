from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import User, Emergency, Portfolio

class PortfolioUploadForm(FlaskForm):
	title = StringField('Product Title', validators=[DataRequired()])
	emergency_id = QuerySelectField('Emergency', query_factory=lambda:Emergency.query.all(), get_label='emergency_name', allow_blank=True)
	creator_id = QuerySelectField('Creator', query_factory=lambda:User.query.filter_by(status='Active'), get_label='fullname', allow_blank=True)
	description = TextAreaField('Description')
	type = SelectField('File Type', choices=['', 'Map', 'Infographic', 'Dashboard', 'Mobile Data Collection', 'Assessment', 'Report - Analysis', 'Other'], validators=[DataRequired()])
	file = FileField('Attach File', validators=[FileAllowed(['jpg', 'png', 'pdf', 'xls', 'xlsm', 'xltx', 'txt', 'doc', 'docx' 'csv', 'shp', 'ai', 'zip'])])
	asset_file_location = StringField('File Assets URL')
	external = BooleanField('Share Publicly')
	submit = SubmitField('Upload SIMS Product')
