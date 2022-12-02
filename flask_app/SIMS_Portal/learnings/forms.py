from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField
from flask_sqlalchemy import SQLAlchemy
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import Learning

class NewAssignmentLearningForm(FlaskForm):
	overall_score = IntegerField('Rank your overall experience (1 = Terrible, 5 = Fantastic)', validators=[DataRequired()])
	overall_exp = TextAreaField('Explain why you chose that score')
	
	got_support = IntegerField('I got the support I needed from the network when I had an issue or question')
	internal_resource = IntegerField('I found the necessary internal support documentation, templates, and other resources from the SIMS Portal')
	external_resource = IntegerField('When I encountered a technical challenge, I was able to find external documentation or other resources (i.e. Google found relevant stuff to help me complete my tasks)')
	clear_tasks = IntegerField('The tasks I took on were clearly articulated')
	field_communication = IntegerField('There was good communication with operational stakeholders in the field when I had a question about a requested product')
	clear_deadlines = IntegerField('Deadlines were realistic and clearly communicated')
	coordination_tools = IntegerField('The coordination tools (Dropbox, Trello, Slack) were easy to access and use')
	
	submit = SubmitField('Submit Learning Review')