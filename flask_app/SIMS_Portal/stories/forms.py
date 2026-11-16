from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from flask_wtf.file import FileField, FileAllowed

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