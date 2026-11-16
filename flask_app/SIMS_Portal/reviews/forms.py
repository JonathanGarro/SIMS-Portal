from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired

class NewEmergencyReviewForm(FlaskForm):
	category = SelectField('Category', choices=[' ','Success', 'Area for Improvement', 'General Observation'])
	type = SelectField('Type', choices=[' ','Communication and Collaboration', 'Doctrine and Guidance', "Tools and Systems", 'Tasking and Prioritization', 'Other'])
	title = StringField('Title', validators=[DataRequired()])
	description = StringField('Description', widget=TextArea(), validators=[DataRequired()])
	recommendation = StringField('Recommended Action', widget=TextArea())
	follow_up = StringField('SIMS Governance Follow Up Action', widget=TextArea())
	status = SelectField('Review Item Status', choices=['Open', 'Processed', 'Dropped'])
	submit = SubmitField('Save Review Record')
	
class ProcessEmergencyReviewForm(FlaskForm):
	follow_up = StringField('SIMS Governance Follow Up Action', widget=TextArea())
	submit = SubmitField('Process Review Record')