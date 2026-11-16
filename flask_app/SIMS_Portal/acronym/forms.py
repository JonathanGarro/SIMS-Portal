from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from SIMS_Portal.models import NationalSociety

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
    scope = SelectField('Category', choices=[('general', 'General'), ('humanitarian', 'Humanitarian'), ('rcrc', 'Red Cross Red Crescent'), ('ns', 'National Society')])
    field = StringField('Tags')
    associated_ns = QuerySelectField('Relevant Country (if Applicable)', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True)
    
    submit = SubmitField('Submit Acronym')
    
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
    scope = SelectField('Category', choices=[('general', 'General'), ('humanitarian', 'Humanitarian'), ('rcrc', 'Red Cross Red Crescent'), ('ns', 'National Society')])
    field = StringField('Tags')
    associated_ns = QuerySelectField('National Society Country', query_factory=lambda:NationalSociety.query.all(), get_label='country_name', allow_blank=True)
    
    submit = SubmitField('Update Acronym')