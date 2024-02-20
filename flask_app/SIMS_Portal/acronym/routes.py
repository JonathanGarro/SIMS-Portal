import logging
from datetime import datetime, date, timedelta

from flask import (
    request, render_template, url_for, flash, redirect,
    jsonify, Blueprint, current_app, redirect, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    login_user, current_user, logout_user, login_required
)
from sqlalchemy.orm.exc import NoResultFound

from SIMS_Portal.models import Acronym, User
from SIMS_Portal.users.utils import send_slack_dm, new_acronym_alert
from SIMS_Portal import db, login_manager
from SIMS_Portal.acronym.forms import NewAcronymForm

acronym = Blueprint('acronym', __name__)

@acronym.route('/acronyms')
def acronyms():
    all_acronyms = db.session.query(Acronym).filter(Acronym.approved_by > 0).all()
    
    return render_template('acronyms.html', all_acronyms=all_acronyms)

@acronym.route('/view_acronym/<int:id>')
def view_acronym(id):
    try:
        acronym_info = db.session.query(Acronym, User).join(User, User.id == Acronym.added_by).filter(Acronym.id == id).first()
        
        if acronym_info is None: 
            abort(404)
    
        try:
            similar_matches = db.session.query(Acronym).filter(Acronym.acronym_eng == acronym_info.Acronym.acronym_eng, Acronym.id != id).all()
        except:
            similar_matches = None
    except NoResultFound:
        abort(404)

    return render_template('view_acronym.html', acronym_info=acronym_info, similar_matches=similar_matches)

@acronym.route('/submit_acronym', methods=['GET', 'POST'])
@login_required
def submit_acronym():
    form = NewAcronymForm()
    
    if request.method == 'GET': 
        latest_acronyms = db.session.query(Acronym, User).join(User, User.id == Acronym.added_by).order_by(Acronym.id.desc()).limit(10).all()
        return render_template('new_acronym.html', title='Submit a New Acronym', form=form, latest_acronyms=latest_acronyms)
    else:
        if form.validate_on_submit():
            submitter_id = User.query.filter(User.id==current_user.id).first()
            
            new_acronym = Acronym(
                added_by=submitter_id.id,
                date_added=datetime.now(),
                acronym_eng=form.data['acronym_eng'],
                def_eng=form.data['def_eng'],
                expl_eng=form.data['expl_eng'],
                acronym_esp=form.data['acronym_esp'],
                def_esp=form.data['def_esp'],
                expl_esp=form.data['expl_esp'],
                acronym_fra=form.data['acronym_fra'],
                def_fra=form.data['def_fra'],
                expl_fra=form.data['expl_fra'],
                relevant_link=form.data['relevant_link']
            )


            db.session.add(new_acronym)
            db.session.commit()
            try:
                new_acronym_alert(f"A new acronym has been added to the SIMS Portal: {new_acronym.def_eng}. Log into the Admin portal to approve or reject it.")
            except: 
                pass
            flash('New acronym added to review queue.', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {getattr(form, field).label.text}: {error}', 'danger')
            return redirect(url_for('acronym.submit_acronym'))
        return redirect(url_for('acronym.submit_acronym'))
