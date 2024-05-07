import logging
from datetime import datetime, date, timedelta

from flask import (
    request, render_template, url_for, flash, redirect,
    jsonify, Blueprint, current_app, redirect, abort, session
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    login_user, current_user, logout_user, login_required
)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from SIMS_Portal.models import Acronym, User, Log, NationalSociety
from SIMS_Portal.users.utils import send_slack_dm, new_acronym_alert
from SIMS_Portal import db, login_manager
from SIMS_Portal.acronym.forms import NewAcronymForm, NewAcronymFormPublic, EditAcronymForm

acronym = Blueprint('acronym', __name__)

@acronym.route('/acronyms')
def acronyms():
    all_acronyms = db.session.query(Acronym).filter(Acronym.approved_by > 0).order_by(Acronym.acronym_eng).all()
    
    # check if user is admin for edit power
    try:
        user_is_admin = current_user.is_admin
    except:
        user_is_admin = False
    
    user_info = None  # initialize user_info to None
    try:
        user_info = db.session.query(User).filter(User.id == current_user.id).first()
    except AttributeError:
        # set user_info.id to zero if the attribute error occurs
        if user_info is not None:
            user_info.id = 0

    return render_template('acronyms.html', all_acronyms=all_acronyms, user_is_admin=user_is_admin, user_info=user_info)

@acronym.route('/acronyms/search', methods=['GET'])
def search_acronyms():
    search_column = request.args.get('search_column', 'acronym_eng')
    search_term = request.args.get('search_term', '')

    # get column attribute from acronym model
    column_attribute = getattr(Acronym, search_column, Acronym.acronym_eng)

    search_results = db.session.query(Acronym).filter(
        Acronym.approved_by > 0,
        column_attribute.ilike(f'%{search_term}%')
    ).order_by(Acronym.acronym_eng).all()

    # check if user is admin for edit power
    try:
        user_is_admin = current_user.is_admin
    except:
        user_is_admin = False

    user_info = None  # initialize user_info to None
    try:
        user_info = db.session.query(User).filter(User.id == current_user.id).first()
    except AttributeError:
        # set user_info.id to zero if the attribute error occurs
        if user_info is not None:
            user_info.id = 0
            
    db_col_name = {
        'acronym_eng': 'Acronym (English)',
        'def_eng': 'Definition (English)',
        'acronym_esp': 'Acrónimo (Español)',
        'def_esp': 'Definición (Español)',
        'acronym_fra': 'Acronyme (Français)',
        'def_fra': 'Définition (Français)'
    }
    
    search_column_display = db_col_name.get(search_column)
    
    row_count = db.session.query(Acronym).filter(
        Acronym.approved_by > 0,
        column_attribute.ilike(f'%{search_term}%')
    ).count()
    
    return render_template('acronyms_search.html', search_results=search_results, user_is_admin=user_is_admin, user_info=user_info, search_column_display=search_column_display, search_term=search_term, row_count=row_count)

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

@acronym.route('/submit_acronym')
def submit_acronym():
    """
    There are two ways to submit acroynms: as a logged in member and as an anonymous visitor. 
    This function checks to see which this user is and routes them to the appropriate submission function.
    """
    if not current_user.is_authenticated:
        return redirect(url_for('acronym.submit_acronym_public'))
    else:
        return redirect(url_for('acronym.submit_acronym_member'))

@acronym.route('/submit_acronym/member', methods=['GET', 'POST'])
@login_required
def submit_acronym_member():
    form = NewAcronymForm()
    
    if request.method == 'GET': 
        latest_acronyms = db.session.query(Acronym, User).join(User, User.id == Acronym.added_by).order_by(Acronym.id.desc()).limit(10).all()
        return render_template('new_acronym.html', title='Submit a New Acronym', form=form, latest_acronyms=latest_acronyms, anon_user=False)
    else:
        if form.validate_on_submit():
            submitter_id = User.query.filter(User.id==current_user.id).first()
            
            new_acronym = Acronym(
                added_by=submitter_id.id,
                approved_by=63, # user 63 is clara barton
                date_added=datetime.now(),
                acronym_eng=form.data['acronym_eng'] if form.data['acronym_eng'] else None,
                def_eng=form.data['def_eng'] if form.data['def_eng'] else None,
                expl_eng=form.data['expl_eng'] if form.data['expl_eng'] else None,
                acronym_esp=form.data['acronym_esp'] if form.data['acronym_esp'] else None,
                def_esp=form.data['def_esp'] if form.data['def_esp'] else None,
                expl_esp=form.data['expl_esp'] if form.data['expl_esp'] else None,
                acronym_fra=form.data['acronym_fra'] if form.data['acronym_fra'] else None,
                def_fra=form.data['def_fra'] if form.data['def_fra'] else None,
                expl_fra=form.data['expl_fra'] if form.data['expl_fra'] else None,
                relevant_link=form.data['relevant_link'] if form.data['relevant_link'] else None
            )

            db.session.add(new_acronym)
            db.session.commit()
            
            log_message = f"[INFO] User {current_user.id} has added a new acronym."
            new_log = Log(message=log_message, user_id=current_user.id)
            db.session.add(new_log)
            db.session.commit()
            
            try:
                user_info = db.session.query(User).filter(User.id == current_user.id)
                new_acronym_alert(f"A new acronym has been added to the SIMS Portal: {new_acronym.def_eng}. It was added by a logged-in SIMS member ({user_info.firstname} {user_info.lastname}), and is therefore approved and available in the acronym list. If it isn't correct, log into the Portal and edit or delete it.")
            except: 
                pass
            flash('New acronym added to review queue.', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {getattr(form, field).label.text}: {error}', 'danger')
            return redirect(url_for('acronym.submit_acronym'))
        return redirect(url_for('acronym.submit_acronym'))

@acronym.route('/submit_acronym/public', methods=['GET', 'POST'])
def submit_acronym_public():
    form = NewAcronymFormPublic()

    if request.method == 'GET': 
        latest_acronyms = db.session.query(Acronym, User).join(User, User.id == Acronym.added_by).order_by(Acronym.id.desc()).limit(10).all()
        return render_template('new_acronym.html', title='Submit a New Acronym', form=form, latest_acronyms=latest_acronyms, anon_user=True)
    elif request.method == 'POST' and form.validate():
        submitter_id = 63  # set to 63 for anonymous users (saves to Clara Barton's account)

        new_acronym = Acronym(
            added_by=submitter_id,
            date_added=datetime.now(),
            acronym_eng=form.acronym_eng.data if form.acronym_eng.data else None,
            def_eng=form.def_eng.data if form.def_eng.data else None,
            expl_eng=form.expl_eng.data if form.expl_eng.data else None,
            acronym_esp=form.acronym_esp.data if form.acronym_esp.data else None,
            def_esp=form.def_esp.data if form.def_esp.data else None,
            expl_esp=form.expl_esp.data if form.expl_esp.data else None,
            acronym_fra=form.acronym_fra.data if form.acronym_fra.data else None,
            def_fra=form.def_fra.data if form.def_fra.data else None,
            expl_fra=form.expl_fra.data if form.expl_fra.data else None,
            relevant_link=form.relevant_link.data if form.relevant_link.data else None,
            anonymous_submitter_name=form.anonymous_submitter_name.data if form.anonymous_submitter_name.data else None,
            anonymous_submitter_email=form.anonymous_submitter_email.data if form.anonymous_submitter_email.data else None
        )

        db.session.add(new_acronym)
        db.session.commit()

        log_message = f"[INFO] An anonymous user has added a new acronym."
        new_log = Log(message=log_message, user_id=0)
        db.session.add(new_log)
        db.session.commit()

        try:
            new_acronym_alert(f"A new acronym has been added to the SIMS Portal by {new_acronym.anonymous_submitter_name}: {new_acronym.def_eng}. Since it was submitted by someone that did not log into the Portal, it must be manually approved.")
        except:
            pass

        flash('New acronym added to review queue.', 'success')
        return redirect(url_for('portfolios.view_documentation'))

    # if form is not valid, flash errors and redirect back to the form
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error in {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('acronym.submit_acronym_public'))


@acronym.route('/acronym/approve/<int:id>', methods=['GET', 'POST'])
@login_required
def approve_acronym(id):
    if current_user.is_admin == 1:
        db.session.query(Acronym).filter(Acronym.id == id).update({'approved_by':current_user.id})
        db.session.commit()
        flash('Acronym has been approved and is now listed for all viewers.', 'success')
        return redirect(url_for('main.admin_process_acronyms'))
    else:
        list_admins = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.is_admin == True).all()
        return render_template('portal_admins.html', list_admins=list_admins)

@acronym.route('/acronym/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_acronym(id):
    if current_user.is_admin == 1:
        acronym_to_delete = db.session.query(Acronym).filter(Acronym.id == id).first()
        if acronym_to_delete:
            try:
                db.session.delete(acronym_to_delete)
                db.session.commit()
                flash('Acronym has been deleted.', 'success')
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred while deleting the acronym.', 'danger')
                
                log_message = f"[ERROR] User {current_user.id} encountered an error when deleting acronym."
                new_log = Log(message=log_message, user_id=current_user.id)
                db.session.add(new_log)
                db.session.commit()
                
                return redirect(url_for('main.admin_process_acronyms'))
        
        return redirect(url_for('main.admin_process_acronyms'))
        
@acronym.route('/acronym/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_acronym(id):
    form = EditAcronymForm()
    acronym_info = db.session.query(Acronym).filter(Acronym.id == id).first()
    latest_acronyms = db.session.query(Acronym, User).join(User, User.id == Acronym.added_by).order_by(Acronym.id.desc()).limit(10).all()
    
    # check for the acronym ID
    if not acronym_info:
        abort(404)
    
    if form.validate_on_submit():
        acronym_info.acronym_eng = form.acronym_eng.data
        acronym_info.def_eng = form.def_eng.data
        acronym_info.expl_eng = form.expl_eng.data
        acronym_info.acronym_esp = form.acronym_esp.data
        acronym_info.def_esp = form.def_esp.data
        acronym_info.expl_esp = form.expl_esp.data
        acronym_info.acronym_fra = form.acronym_fra.data
        acronym_info.def_fra = form.def_fra.data
        acronym_info.expl_fra = form.expl_fra.data
        acronym_info.relevant_link = form.relevant_link.data
        
        if current_user.is_admin or acronym_info.added_by == current_user.id:
            db.session.commit()
            flash('Acronym record updated.', 'success')
        
            log_message = f"[INFO] User {current_user.id} edited acronym {acronym_info.id}."
            new_log = Log(message=log_message, user_id=current_user.id)
            db.session.add(new_log)
            db.session.commit()
            
            return redirect(url_for('acronym.view_acronym', id=id))
        else:
            abort(403)
        
        return redirect(url_for('acronym.view_acronym', id=id))
    elif request.method == 'GET':
        form.acronym_eng.data = acronym_info.acronym_eng
        form.def_eng.data = acronym_info.def_eng
        form.expl_eng.data = acronym_info.expl_eng
        form.acronym_esp.data = acronym_info.acronym_esp
        form.def_esp.data = acronym_info.def_esp
        form.expl_esp.data = acronym_info.expl_esp
        form.acronym_fra.data = acronym_info.acronym_fra
        form.def_fra.data = acronym_info.def_fra
        form.expl_fra.data = acronym_info.expl_fra
        form.relevant_link.data = acronym_info.relevant_link
    return render_template('acronym_edit.html', form=form, acronym_info=acronym_info, latest_acronyms=latest_acronyms)