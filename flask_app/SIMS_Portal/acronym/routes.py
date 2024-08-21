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

@acronym.route('/acronyms', methods=['GET'])
def acronyms():
    page = request.args.get('page', 1, type=int)
    all_acronyms = db.session.query(Acronym).filter(Acronym.approved_by > 0).order_by(Acronym.acronym_eng)
    paginated_acronyms = all_acronyms.paginate(page=page, per_page=100)
    
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

    return render_template('acronyms.html', paginated_acronyms=paginated_acronyms, user_is_admin=user_is_admin, user_info=user_info)

@acronym.route('/acronyms/search', methods=['GET'])
def search_acronyms():
    """
    Handle the GET request to retrieve and display a paginated list of approved acronyms.
    
    This endpoint retrieves a paginated list of acronyms from the database that have been approved
    (i.e., have a non-zero 'approved_by' field). The acronyms are sorted alphabetically by their
    English representation.
    
    The pagination is determined by the 'page' query parameter, with a default of 100 acronyms per page.
    
    The function also checks if the current user is an admin to determine if they have editing privileges.
    Additionally, it attempts to retrieve the current user's information from the database.
    
    Returns:
        Response: Renders the 'acronyms.html' template with the following context:
            - paginated_acronyms: A paginated list of approved acronyms.
            - user_is_admin: A boolean indicating whether the current user has admin privileges.
            - user_info: The current user's information, or None if not found.
    """
    
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

@acronym.route('/acronyms/api/search', methods=['GET'])
def search_acronyms_api():
    """
    Handle the GET request to search for acronyms based on a specified column and search term.
    
    Endpoint allows users to search for acronyms in the database based on a specified column 
    and search term. The search is case-insensitive and is restricted to acronyms that have been 
    approved (i.e., have a non-zero 'approved_by' field).
    
    The column to search on is determined by the 'search_column' query parameter, with a default 
    of 'acronym_eng'. The search term is provided via the 'search_term' query parameter.
    
    The search results are returned in JSON format, including relevant fields for each matching acronym.
    
    Query Parameters:
        search_column (str): The column to search within the Acronym model (default is 'acronym_eng').
        search_term (str): The term to search for within the specified column.
    
    Returns:
        Response: A JSON object containing the search results, where each result includes:
            - acronym_eng: The English version of the acronym.
            - def_eng: The English definition of the acronym.
            - acronym_esp: The Spanish version of the acronym.
            - def_esp: The Spanish definition of the acronym.
            - acronym_fra: The French version of the acronym.
            - def_fra: The French definition of the acronym.
            - link: A relevant link associated with the acronym.
    """
    
    search_column = request.args.get('search_column', 'acronym_eng')
    search_term = request.args.get('search_term', '')

    # get column attribute from acronym model
    column_attribute = getattr(Acronym, search_column, Acronym.acronym_eng)

    search_results = db.session.query(Acronym).filter(
        Acronym.approved_by > 0,
        column_attribute.ilike(f'%{search_term}%')
    ).order_by(Acronym.acronym_eng).all()

    # convert search results to json
    results = []
    for result in search_results:
        results.append({
            'acronym_eng': result.acronym_eng,
            'def_eng': result.def_eng,
            'acronym_esp': result.acronym_esp,
            'def_esp': result.def_esp,
            'acronym_fra': result.acronym_fra,
            'def_fra': result.def_fra, 
            'link': result.relevant_link
        })

    return jsonify(results=results)

@acronym.route('/view_acronym/<int:id>')
def view_acronym(id):
    """
    Handle the GET request to view details of a specific acronym by its ID.
    
    Endpoint retrieves detailed information about a specific acronym, including the user who 
    added it, based on the acronym's unique ID. The information is gathered by joining the `Acronym` 
    and `User` models. If the acronym is not found, a 404 error is returned.
    
    Additionally, the function attempts to find other acronyms with the same English representation 
    (`acronym_eng`) but with different IDs, which are considered similar matches.
    
    Parameters:
        id (int): The unique identifier of the acronym to be viewed.
    
    Returns:
        Response: If the acronym is found, it returns the details of the acronym and any similar matches.
                  If the acronym is not found, a 404 error is returned.
    
    Exceptions:
        - 404: If no acronym with the specified ID is found.
        - 404: If no results are found when querying the database.
    """
    
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
    Handle the submission of acronyms by routing users to the appropriate submission function based on their authentication status.
    
    There are two ways to submit acronyms:
    1. As a logged-in member: If the user is authenticated, they are redirected to the member-specific acronym submission function.
    2. As an anonymous visitor: If the user is not authenticated, they are redirected to the public (anonymous) acronym submission function.
    
    Returns:
        Response: A redirect to either the 'submit_acronym_member' function for authenticated users or 
                  the 'submit_acronym_public' function for anonymous visitors.
    """
    
    if not current_user.is_authenticated:
        return redirect(url_for('acronym.submit_acronym_public'))
    else:
        return redirect(url_for('acronym.submit_acronym_member'))

@acronym.route('/submit_acronym/member', methods=['GET', 'POST'])
@login_required
def submit_acronym_member():
    """
    Handle the submission of a new acronym by a logged-in member.
    
    Function allows authenticated users to submit a new acronym. It supports both GET and POST requests:
    
    - GET request: 
        Renders the form for submitting a new acronym. Also retrieves and displays the 10 most recent acronyms 
        submitted by users.
    
    - POST request:
        Processes the acronym submission form. If the form is valid, a new acronym is created in the database 
        with the current user's ID as the submitter. The new acronym is automatically approved with a hard-coded 
        'approved_by' value of 63 (Clara Barton). After the acronym is added to the database, a log entry is 
        created, and an alert is generated to notify relevant users.
    
    Parameters:
        None (the function relies on form data and the current user's session).
    
    Returns:
        Response:
            - For GET requests: Renders the 'new_acronym.html' template with the form and latest acronyms.
            - For POST requests:
                - On success: Redirects to the acronym submission page with a success message.
                - On failure: Redirects to the acronym submission page with error messages.
    
    Exceptions:
        - The function handles form validation errors by flashing error messages.
        - Attempts to send an acronym alert email, but passes silently on failure.
    """
    
    form = NewAcronymForm()
    
    if request.method == 'GET': 
        latest_acronyms = db.session.query(Acronym, User).join(User, User.id == Acronym.added_by).order_by(Acronym.id.desc()).limit(10).all()
        return render_template('new_acronym.html', title='Submit a New Acronym', form=form, latest_acronyms=latest_acronyms, anon_user=False)
    else:
        if form.validate_on_submit():
            submitter_id = User.query.filter(User.id==current_user.id).first()
            
            associated_ns = form.associated_ns.data
            associated_ns_go_id = associated_ns.ns_go_id if associated_ns is not None and hasattr(associated_ns, 'ns_go_id') else None
            
            new_acronym = Acronym(
                added_by=submitter_id.id,
                approved_by=63, # user 63 is clara barton
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
                scope=form.scope.data if form.scope.data else None,
                field=form.field.data if form.field.data else None,
                associated_ns=associated_ns_go_id
            )

            db.session.add(new_acronym)
            db.session.commit()
            
            log_message = f"[INFO] User {current_user.id} has added a new acronym."
            new_log = Log(message=log_message, user_id=current_user.id)
            db.session.add(new_log)
            db.session.commit()
            
            try:
                user_info = db.session.query(User).filter(User.id == current_user.id).first()
                new_acronym_alert(f"A new acronym has been added to the SIMS Portal: {new_acronym.def_eng}. It was added by a logged-in SIMS member ({user_info.firstname} {user_info.lastname}), and is therefore approved and available in the acronym list. If it isn't correct, log into the Portal and edit or delete it.")
            except: 
                pass
            flash('New acronym added.', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {getattr(form, field).label.text}: {error}', 'danger')
            return redirect(url_for('acronym.submit_acronym'))
        return redirect(url_for('acronym.submit_acronym'))

@acronym.route('/submit_acronym/public', methods=['GET', 'POST'])
def submit_acronym_public():
    """
    Handle the submission of a new acronym by an anonymous user.
    
    Function allows non-authenticated (anonymous) users to submit a new acronym. It supports both 
    GET and POST requests:
    
    - GET request:
        Renders the form for submitting a new acronym. Additionally, retrieves and displays the 
        10 most recent acronyms submitted by users.
    
    - POST request:
        Processes the acronym submission form. If the form is valid, a new acronym is created in 
        the database with the submission credited to a placeholder account (user ID 63, representing 
        Clara Barton). The acronym is not automatically approved and is queued for review. After the 
        acronym is added, a log entry is created, and an alert is generated to notify administrators 
        of the new submission.
    
    Parameters:
        None (the function relies on form data submitted by the user).
    
    Returns:
        Response:
            - For GET requests: Renders the 'new_acronym.html' template with the form and latest acronyms.
            - For POST requests:
                - On success: Redirects to the acronym list page with a success message indicating that 
                              the acronym has been added to the review queue.
                - On failure: Logs the error, flashes an error message, and redirects back to the form.
    
    Exceptions:
        - The function logs any errors encountered during the submission process and flashes error 
          messages for form validation failures.
        - Attempts to send an acronym alert email, but passes silently on failure.
    """
    
    form = NewAcronymFormPublic()

    if request.method == 'GET': 
        latest_acronyms = db.session.query(Acronym, User).join(User, User.id == Acronym.added_by).order_by(Acronym.id.desc()).limit(10).all()
        return render_template('new_acronym.html', title='Submit a New Acronym', form=form, latest_acronyms=latest_acronyms, anon_user=True)
    elif request.method == 'POST' and form.validate():
        submitter_id = 63  # set to 63 for anonymous users (saves to Clara Barton's account)
        try:
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
                scope=form.scope.data if form.scope.data else None,
                field=form.field.data if form.field.data else None,
                associated_ns=form.associated_ns.data.ns_go_id if form.associated_ns.data.ns_go_id else None,
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
            return redirect(url_for('acronym.acronyms'))
        except Exception as e: 
            log_message = f"[WARNING] An error occurred while adding a public acronym: {e}."
            new_log = Log(message=log_message, user_id=0)
            db.session.add(new_log)
            db.session.commit()

    # if form is not valid, flash errors and redirect back to the form
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error in {getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('acronym.submit_acronym_public'))

@acronym.route('/acronym/approve/<int:id>', methods=['GET', 'POST'])
@login_required
def approve_acronym(id):
    """
    Handle the approval of an acronym by an admin.
    
    Function allows an authenticated admin user to approve an acronym by setting the 
    'approved_by' field to the admin's user ID. Upon approval, the acronym becomes visible 
    to all users.
    
    Parameters:
        id (int): The unique identifier of the acronym to be approved.
    
    Returns:
        Response:
            - If the current user is an admin:
                - The acronym's 'approved_by' field is updated with the admin's ID.
                - A success message is flashed, and the user is redirected to the acronym 
                  administration page (`admin_process_acronyms`).
            - If the current user is not an admin:
                - Renders a template displaying a list of admin users (`portal_admins.html`), 
                  indicating that the current user does not have the necessary privileges to 
                  approve the acronym.
    """
    
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
    """
    Handle the deletion of an acronym by an admin.
    
    Function allows an authenticated admin user to delete an acronym from the database. 
    The acronym is identified by its unique ID. Upon successful deletion, a success message 
    is flashed, and the user is redirected to the acronym administration page.
    
    Parameters:
        id (int): The unique identifier of the acronym to be deleted.
    
    Returns:
        Response:
            - If the current user is an admin:
                - The specified acronym is deleted from the database.
                - A success message is flashed, and the user is redirected to the acronym 
                  administration page (`admin_process_acronyms`).
                - If an error occurs during deletion, the operation is rolled back, an error 
                  message is flashed, and the error is logged. The user is then redirected 
                  to the acronym administration page.
            - If the acronym does not exist, the user is redirected to the acronym administration page.
    """
    
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
    """
    Handle the editing of an existing acronym.
    
    Function allows authenticated users to edit an existing acronym. The user must either be 
    the original submitter of the acronym or an admin to make changes. The function supports both 
    GET and POST requests:
    
    - GET request:
        Retrieves the existing acronym data and pre-fills the editing form. If the acronym does 
        not exist, a 404 error is returned.
    
    - POST request:
        Validates the form data and updates the acronym in the database. If the update is successful, 
        a log entry is created, and the user is redirected to the view page for the acronym. If the 
        user is not authorized to edit the acronym, a 403 error is returned.
    
    Parameters:
        id (int): The unique identifier of the acronym to be edited.
    
    Returns:
        Response:
            - For GET requests: Renders the 'acronym_edit.html' template with the form pre-filled 
              with the existing acronym data.
            - For POST requests:
                - On successful validation and update: Redirects to the view page of the acronym 
                  with a success message.
                - On failure to validate or unauthorized access: Aborts with the appropriate HTTP 
                  status code (404 for not found, 403 for unauthorized).
    """
    
    acronym_info = db.session.query(Acronym).filter(Acronym.id == id).first()
    form = EditAcronymForm(obj=acronym_info)  # Initialize form with acronym_info data

    # Check for the acronym ID
    if not acronym_info:
        abort(404)
    
    if form.validate_on_submit():
        acronym_info.acronym_eng = form.acronym_eng.data if form.acronym_eng.data else None
        acronym_info.def_eng = form.def_eng.data if form.def_eng.data else None
        acronym_info.expl_eng = form.expl_eng.data if form.expl_eng.data else None
        acronym_info.acronym_esp = form.acronym_esp.data if form.acronym_esp.data else None
        acronym_info.def_esp = form.def_esp.data if form.def_esp.data else None
        acronym_info.expl_esp = form.expl_esp.data if form.expl_esp.data else None
        acronym_info.acronym_fra = form.acronym_fra.data if form.acronym_fra.data else None
        acronym_info.def_fra = form.def_fra.data if form.def_fra.data else None
        acronym_info.expl_fra = form.expl_fra.data if form.expl_fra.data else None
        acronym_info.relevant_link = form.relevant_link.data if form.relevant_link.data else None
        acronym_info.scope = form.scope.data if form.scope.data else None
        acronym_info.field = form.field.data if form.field.data else None
        acronym_info.associated_ns = form.associated_ns.data.ns_go_id if form.associated_ns.data else None
        
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
        form.scope.data = acronym_info.scope
        form.field.data = acronym_info.field
        form.associated_ns.data = db.session.query(NationalSociety).filter(NationalSociety.ns_go_id == acronym_info.associated_ns).first()
    
    return render_template('acronym_edit.html', form=form, acronym_info=acronym_info)