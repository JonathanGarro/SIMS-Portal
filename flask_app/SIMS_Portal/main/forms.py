from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, SelectField, SelectMultipleField, HiddenField, FileField
from wtforms.widgets import TextArea
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from SIMS_Portal import db
from SIMS_Portal.models import User, Emergency, Portfolio, Skill, Language, EmergencyType, NationalSociety, Badge, Assignment

class MemberSearchForm(FlaskForm):
	name = StringField('Member Name')
	skills = QuerySelectField('Skill', query_factory=lambda:Skill.query.all(), get_label='name', allow_blank=True)
	languages = QuerySelectField('Language', query_factory=lambda:Language.query.order_by(Language.name).all(), get_label='name', allow_blank=True)
	submit = SubmitField('Search Members')

class EmergencySearchForm(FlaskForm):
	name = StringField('Emergency Name')
	status = SelectField('SIMS Status', choices=['', 'Active', 'Closed', 'Removed'])
	type = QuerySelectField('Emergency Type', query_factory=lambda:EmergencyType.query.all(), get_label='emergency_type_name', allow_blank=True)
	location = QuerySelectField('Primary Country', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True)
	glide = StringField('GLIDE Number')
	submit = SubmitField('Search Emergencies')

class ProductSearchForm(FlaskForm):
	name = StringField('Product Name')
	type = SelectField('File Type', choices=['', 'Map', 'Infographic', 'Dashboard', 'Mobile Data Collection', 'Assessment', 'Report / Analysis', 'Other'])
	description = StringField('Search Product Description')
	submit = SubmitField('Search Products')
	
class BadgeAssignmentForm(FlaskForm):
	user_name = QuerySelectField('Member', query_factory=lambda:User.query.order_by(User.firstname).filter(User.status == 'Active').all(), get_label='fullname', allow_blank=True)
	badge_name = QuerySelectField('Badge', query_factory=lambda:Badge.query.order_by(Badge.name).all(), get_label='name', allow_blank=True)
	assigner_justify = StringField('Justification for Assigning this Badge', widget=TextArea(), validators=[DataRequired()], render_kw={'style':'height: 100px'})
	submit_badge = SubmitField('Assign')

class BadgeAssignmentViaSIMSCoForm(FlaskForm):
	user_name = QuerySelectField('Member', query_factory=lambda:User.query.order_by(User.firstname).filter(User.status == 'Active').all(), get_label='fullname', allow_blank=True)
	badge_name = QuerySelectField('Badge', query_factory=lambda:Badge.query.order_by(Badge.name).all(), get_label='name', allow_blank=True)
	assigner_justify = StringField('Justification for Assigning this Badge', validators=[DataRequired()], render_kw={'style':'height: 100px'})
	submit_badge = SubmitField('Assign')
	
class SkillCreatorForm(FlaskForm):
	name = StringField('Skill Name')
	category = SelectField('Skill Category', choices=['Geospatial', 'Mobile Data Collection', "Graphic Design", 'Data Visualization', 'Web Development', 'Coding', 'Data Management', 'Information Analysis'])
	submit_skill = SubmitField('Add Skill')

class NewBadgeUploadForm(FlaskForm):
	name = StringField('Badge Name')
	file = FileField('Attach File', validators=[FileAllowed(['png'])])
	upload_badge = SubmitField('Upload New Badge')