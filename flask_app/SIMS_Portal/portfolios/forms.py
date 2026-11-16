from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, URL
from SIMS_Portal.models import User, Emergency


class PortfolioUploadForm(FlaskForm):
	title = StringField('Product Title', validators=[DataRequired()])
	emergency_id = QuerySelectField('Emergency', query_factory=lambda:Emergency.query.all(), get_label='emergency_name', allow_blank=True)
	creator_id = QuerySelectField('Creator', query_factory=lambda:User.query.filter_by(status='Active'), get_label='fullname', allow_blank=True)
	description = TextAreaField('Description', validators=[DataRequired()])
	type = SelectField('File Type', choices=['', 'Map', 'Infographic', 'Dashboard', 'Mobile Data Collection', 'Assessment', 'Internal Analysis', 'External Report', 'Code Snippet', 'Other'], validators=[DataRequired()])
	file = FileField('Final Product and File Assets (50MB Max)')
	image_file = FileField('Attach Cover Image (Optional - See Sidebar Guidance)')
	format = SelectField('Final Product Format', choices=['', 'AI', 'APK', 'CSV', 'DOC', 'DOCX', 'EXE', 'GPKG', 'HTML', 'INDD', 'JAVA', 'JPG', 'JPEG', 'JS', 'JSON', 'KML', 'KMZ', 'PBIX', 'PDF', 'PHP', 'PNG', 'PPT', 'PPTX', 'PSD', 'PY', 'QGIS', 'SHP', 'SQL', 'SVG', 'TXT', 'XLS', 'XLSX', 'XML', 'ZIP', 'OTHER'], validators=[DataRequired()])
	external = BooleanField('Share Publicly')
	submit = SubmitField('Upload SIMS Product')

class NewDocumentationForm(FlaskForm):
	article_name = StringField('Article Title', validators=[DataRequired()])
	url = StringField('Article URL', validators=[DataRequired(), URL()])
	category = SelectField('Categories', choices=['', 'Data Collection and Survey Design', 'Data Transformation and Analysis', 'Geospatial', 'Information Design', 'SIMS Remote Coordination', 'Standard Operating Procedures', 'Style Guidance', 'Web Visualization'], validators=[DataRequired()])
	author_id =  QuerySelectField('Author', query_factory=lambda:User.query.filter_by(status='Active').order_by(User.firstname), get_label='fullname', allow_blank=True, validators=[DataRequired()])
	summary = TextAreaField('Brief Summary of Article (One to two sentences)', validators=[DataRequired()], render_kw={'style':'height: 100px'})
	featured = BooleanField('Featured')
	submit = SubmitField('Submit Documentation')