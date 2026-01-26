from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, SelectField, SelectMultipleField, HiddenField, FileField, TextAreaField
from wtforms.widgets import TextArea
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, URL
from flask_wtf.file import FileField, FileAllowed
from wtforms.widgets import HiddenInput
from SIMS_Portal import db
from datetime import datetime
from SIMS_Portal.models import User, Emergency, Portfolio, Skill, Language, EmergencyType, NationalSociety, Badge, Assignment

class ManualSlackMessage(FlaskForm):
	message = TextAreaField('Message', validators=[DataRequired()], render_kw={'style':'height: 100px'})
	user_slack = QuerySelectField('Member', query_factory=lambda: User.query.order_by(User.firstname).all(), get_label='fullname', allow_blank=True)
	submit = SubmitField('Send Message')

class MemberSearchForm(FlaskForm):
	name = StringField('Member Name')
	skills = QuerySelectField('Skill', query_factory=lambda:Skill.query.order_by('name').all(), get_label='name', allow_blank=True)
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
	badge_name = QuerySelectField('Badge', query_factory=lambda:Badge.query.order_by(Badge.name).filter(Badge.limited_edition == 'false').all(), get_label='name', allow_blank=True)
	assigner_justify = StringField('Justification for Assigning this Badge', widget=TextArea(), validators=[DataRequired()], render_kw={'style':'height: 100px'})
	submit_badge = SubmitField('Assign')
	
class SkillCreatorForm(FlaskForm):
	name = StringField('Skill Name')
	category = SelectField('Skill Category', choices=['Coding', 'Data & Information Analysis', 'Data Management', 'Data Visualization', 'Geospatial', "Graphic Design", 'Mobile Data Collection', 'Web Development'])
	submit_skill = SubmitField('Add Skill')

class NewBadgeUploadForm(FlaskForm):
	name = StringField('Badge Name', validators=[DataRequired()])
	file = FileField('Attach File', validators=[FileAllowed(['png'])])
	description = StringField('Badge Description', validators=[DataRequired()])
	limited_edition = BooleanField('Limited Edition?')
	upload_badge = SubmitField('Upload New Badge')

class NewChecklistForm(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired(), Length(min=5, max=100)])
    task_description = TextAreaField('Task Description', validators=[DataRequired()])
    task_url = StringField('Task URL', validators=[DataRequired(), Length(min=5, max=100)])
    submit = SubmitField('Add Task')
	
class UpdateChecklistForm(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired(), Length(min=5, max=100)])
    task_description = TextAreaField('Task Description', validators=[DataRequired()])
    task_url = StringField('Task URL', validators=[DataRequired(), Length(min=5, max=100)])
    submit = SubmitField('Update Task')	

class UpdateEmergenyChecklistForm(FlaskForm):
	emergency_id = HiddenField('emergency_id')
	checklist_id = HiddenField('checklist_id')
	task_completed = BooleanField('Task Completed', default=False, widget=HiddenInput())
	complted_at = DateTimeField('Completed At', format='%Y-%m-%d', default=datetime.now)
	submit = SubmitField('Mark Complete')	

class SubTaskForm(FlaskForm):
    name = StringField('Sub-Task Name', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    task_url = StringField('URL', validators=[Optional(), URL(require_tld=False, message='Invalid URL')])

class EditChecklistForm(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired()])
    task_description = StringField('Description', validators=[Optional()])
    task_url = StringField('URL', validators=[Optional(), URL(require_tld=False, message='Invalid URL')])
    submit = SubmitField('Save')

class EditSubTaskForm(FlaskForm):
    name = StringField('Sub-Task Name', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    task_url = StringField('URL', validators=[Optional(), URL(require_tld=False, message='Invalid URL')])
    submit = SubmitField('Save')

class AssignChecklistToEmergencyForm(FlaskForm):
    emergency_id = SelectField('Select Emergency', coerce=int, validators=[DataRequired()])
    # tasks and subtasks will be handled in the template as checkboxes
    submit = SubmitField('Assign Checklist to Emergency')