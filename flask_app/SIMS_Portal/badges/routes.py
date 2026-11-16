
from flask import (
	request, render_template, url_for, flash, redirect,
	Blueprint
)
from flask_login import (
	current_user, login_required
)
from sqlalchemy import text

from SIMS_Portal.badges.utils import award_badge
from SIMS_Portal import db
from SIMS_Portal.models import (
	Assignment, User, Emergency, Badge
)
from SIMS_Portal.main.forms import (
	BadgeAssignmentViaSIMSCoForm,
	NewBadgeUploadForm
)
from SIMS_Portal.main.utils import (
	check_sims_co, save_new_badge
)


badges_bp = Blueprint('badges', __name__)


@badges_bp.route('/badges')
def badges():
	assigned_badges = db.session.execute(text("SELECT name, badge.id as id, description, badge_url, limited_edition, count(\"user\".id) as count FROM badge LEFT JOIN user_badge ON user_badge.badge_id = badge.id LEFT JOIN \"user\" ON \"user\".id = user_badge.user_id AND \"user\".status = 'Active' WHERE limited_edition = false GROUP BY name, badge.id, description, limited_edition ORDER BY name"))
	all_badges = db.session.query(Badge).all()

	all_limited_edition_badges = db.session.query(Badge).filter(Badge.limited_edition == True).all()
	count_active_members = db.session.query(User).filter(User.status == 'Active').count()

	list_assigned_badges = []
	for badge in assigned_badges:
		temp_dict = {}
		temp_dict['name'] = badge.name
		temp_dict['id'] = badge.id
		temp_dict['badge_url'] = badge.badge_url
		temp_dict['count'] = badge.count
		temp_dict['description'] = badge.description
		temp_dict['limited_edition'] = badge.limited_edition
		list_assigned_badges.append(temp_dict)

	return render_template('badges.html', title='Badges', count_active_members=count_active_members, all_badges=all_badges, list_assigned_badges=list_assigned_badges, all_limited_edition_badges=all_limited_edition_badges)


@badges_bp.route('/badges/create', methods=['GET', 'POST'])
@login_required
def create_badge():
	form = NewBadgeUploadForm()
	if current_user.is_admin is True and form.validate_on_submit() and form.file.data:
		file = save_new_badge(form.file.data, form.name.data)
		if form.limited_edition.data == True:
			is_limited_edition = True
		else:
			is_limited_edition = False
		badge = Badge(name = form.name.data, badge_url = file, limited_edition = is_limited_edition, description = form.description.data)
		db.session.execute(badge)
		db.session.commit()
		flash('New badge successfully created!', 'success')
		return redirect(url_for('portal_admin.admin_upload_badges'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403


@badges_bp.route('/badge_assignment_simsco/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def badge_assignment_sims_co(dis_id):
	badge_form = BadgeAssignmentViaSIMSCoForm()

	event_name = db.session.query(Emergency).filter(Emergency.id == dis_id).first()

	assigned_badges = db.session.execute(text("SELECT u.id, u.firstname, u.lastname, string_agg(b.name, ', ') as badges FROM public.user u JOIN user_badge ub ON ub.user_id = u.id JOIN badge b ON b.id = ub.badge_id JOIN assignment a ON a.user_id = u.id JOIN emergency e ON e.id = a.emergency_id WHERE u.status = 'Active' AND e.id = :emergency_id AND a.role = 'Remote IM Support' AND a.assignment_status = 'Active' GROUP BY u.id ORDER BY u.firstname"), {'emergency_id': dis_id})

	assigned_members = db.session.query(Emergency, Assignment, User).join(Assignment, Assignment.emergency_id == Emergency.id).join(User, User.id == Assignment.user_id).filter(Emergency.id == dis_id).all()

	# generate list of user IDs of users listed as SIMS Remote Coordinators on emergency
	sims_co_ids = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == dis_id, Assignment.role == 'SIMS Remote Coordinator').all()

	user_is_sims_co = check_sims_co(dis_id)

	if request.method == 'GET' and user_is_sims_co == True:
		query = User.query.join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == dis_id, Assignment.role == 'Remote IM Support', Assignment.assignment_status == 'Active')
		badge_form.user_name.query = query
		return render_template('emergency_badge_assignment.html', title='Assign Badges', user_is_sims_co=user_is_sims_co, assigned_members=assigned_members, event_name=event_name, badge_form=badge_form, assigned_badges=assigned_badges)
	elif request.method == 'POST' and user_is_sims_co == True:
		if badge_form.validate_on_submit():
			user_id = badge_form.user_name.data.id
			badge_id = badge_form.badge_name.data.id
			if award_badge(user_id, badge_id, current_user, badge_form.assigner_justify.data):
				flash('Badge successfully assigned.', 'success')
			else:
				flash('Cannot add badge - user already has it.', 'danger')
			return redirect(url_for('badges.badge_assignment_sims_co', dis_id=dis_id))
		else:
			flash('Please fill out all sections of the form.', 'warning')
			return redirect(url_for('badges.badge_assignment_sims_co', dis_id=dis_id))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		print('User {} tried to assign a badge but was denied and given a 403 error.'.format(current_user.fullname))
		return render_template('errors/403.html', list_of_admins=list_of_admins, user_is_sims_co=user_is_sims_co, event_name=event_name, sims_co_ids=sims_co_ids), 403
