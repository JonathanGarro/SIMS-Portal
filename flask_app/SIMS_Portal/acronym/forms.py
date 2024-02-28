from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, DateTimeField, TextAreaField, SelectField, SelectMultipleField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SIMS_Portal.models import User, Acronym

class NewAcronymForm(FlaskForm):
    acronym_eng = StringField('Acronym (English)')
    def_eng = TextAreaField('Definition (English)', render_kw={'style':'height: 100px'})
    expl_eng = TextAreaField('Explanation (English)', render_kw={'style':'height: 100px'})
    acronym_esp = StringField('Acronym (Spanish)')
    def_esp = TextAreaField('Definition (Spanish)', render_kw={'style':'height: 100px'})
    expl_esp = TextAreaField('Explanation (Spanish)', render_kw={'style':'height: 100px'})
    acronym_fra = StringField('Acronym (French)')
    def_fra = TextAreaField('Definition (French)', render_kw={'style':'height: 100px'})
    expl_fra = TextAreaField('Explanation (French)', render_kw={'style':'height: 100px'})
    relevant_link = StringField('Relevant URL (if Applicable)')
    
    submit = SubmitField('Submit Acronym')
    
class NewAcronymFormPublic(NewAcronymForm):
    anonymous_submitter_name = StringField('Your Name', validators=[DataRequired()])
    anonymous_submitter_email = StringField('Your Email', validators=[DataRequired(), Email()])

class EditAcronymForm(FlaskForm):
    acronym_eng = StringField('Acronym (English)')
    def_eng = TextAreaField('Definition (English)', render_kw={'style':'height: 100px'})
    expl_eng = TextAreaField('Explanation (English)', render_kw={'style':'height: 100px'})
    acronym_esp = StringField('Acronym (Spanish)')
    def_esp = TextAreaField('Definition (Spanish)', render_kw={'style':'height: 100px'})
    expl_esp = TextAreaField('Explanation (Spanish)', render_kw={'style':'height: 100px'})
    acronym_fra = StringField('Acronym (French)')
    def_fra = TextAreaField('Definition (French)', render_kw={'style':'height: 100px'})
    expl_fra = TextAreaField('Explanation (French)', render_kw={'style':'height: 100px'})
    relevant_link = StringField('Relevant URL (if Applicable)')
    
    submit = SubmitField('Update Acronym')