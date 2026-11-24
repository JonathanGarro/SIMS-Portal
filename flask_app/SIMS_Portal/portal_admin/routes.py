import re

from flask import (
	abort, request, render_template, url_for, flash, redirect,
	Blueprint, current_app
)
from flask_login import (
	current_user, login_required
)
from sqlalchemy import desc, text

from SIMS_Portal.users.utils import assign_profile
from SIMS_Portal.badges.utils import award_badge
from SIMS_Portal import db
from SIMS_Portal.models import (
	User, Emergency, Skill, NationalSociety, Badge, Review, Log, Acronym, RegionalFocalPoint, Region
)
from SIMS_Portal.main.forms import (
	BadgeAssignmentForm, SkillCreatorForm, NewBadgeUploadForm, ManualSlackMessage
)
from SIMS_Portal.main.utils import (
	save_new_badge, send_error_message,
	auto_badge_assigner_big_wig, auto_badge_assigner_maiden_voyage,
	auto_badge_assigner_self_promoter, auto_badge_assigner_polyglot,
	auto_badge_assigner_autobiographer, auto_badge_assigner_jack_of_all_trades,
	auto_badge_assigner_edward_tufte, auto_badge_assigner_world_traveler,
	auto_badge_assigner_old_salt
)
from SIMS_Portal.users.forms import AssignProfileTypesForm, RegionalFocalPointForm
from SIMS_Portal.users.utils import (
	send_slack_dm, bulk_slack_photo_update, alert_inactive_members
)
from SIMS_Portal.alerts.utils import (
	refresh_surge_alerts, refresh_surge_alerts_latest, refresh_open_alert_statuses
)
from SIMS_Portal.availability.utils import (
	request_availability_updates
)

from SIMS_Portal.tasks.utils import refresh_all_active_githubs

portal_admin = Blueprint('portal_admin', __name__)


@portal_admin.route('/admin/send_slack_message', methods=['GET', 'POST'])
@login_required
def send_manual_slack_message():
	message_form = ManualSlackMessage()
	if request.method == 'GET' and current_user.is_admin == 1:
		return render_template('admin_send_slack_message.html', message_form=message_form)

	if request.method == 'POST' and current_user.is_admin == 1:
		if message_form.validate_on_submit():
			message = message_form.message.data
			selected_user = message_form.user_slack.data
			if selected_user:
				user_slack_id = selected_user.slack_id
				send_slack_dm(message, user_slack_id)
				flash('Message sent!', 'success')
				return redirect(url_for('portal_admin.send_manual_slack_message'))
			else:
				flash('Please select a valid user.', 'danger')
		else:
			flash('Invalid form. Please check your inputs.', 'danger')

	return render_template('admin_send_slack_message.html', message_form=message_form)


@portal_admin.route('/admin/manage_profiles', methods=['GET', 'POST'])
@login_required
def admin_manage_profiles():
	profile_form = AssignProfileTypesForm()
	if request.method == 'GET' and current_user.is_admin == 1:
		all_assigned_profiles = db.session.execute(text('SELECT user_id, firstname || \' \' || lastname as user_name, profile_id, max(tier) as max_tier, name FROM user_profile JOIN profile ON profile.id = user_profile.profile_id JOIN "user" ON "user".id = user_profile.user_id WHERE "user".status = \'Active\' GROUP BY user_id, profile_id, firstname, lastname, name ORDER BY user_name'))
		return render_template('admin_profiles.html', profile_form=profile_form, all_assigned_profiles=all_assigned_profiles)

	# assign profile to user
	elif request.method == 'POST' and profile_form.user_name.data and current_user.is_admin == 1:

		user_id = profile_form.user_name.data.id
		try:
			profile_id = profile_form.profiles.data.id
		except:
			flash('A profile is required.', 'danger')
			return redirect(url_for('portal_admin.admin_manage_profiles'))
		tier = profile_form.tier.data
		requested_profile_code = str(user_id) + str(profile_id) + str(tier)

		if tier == '':
			flash('A tier is required.', 'danger')
			return redirect(url_for('portal_admin.admin_manage_profiles'))

		# get the user's existing profiles and tiers, generate unique code that concats all three elements
		users_existing_profiles = db.session.execute(text("SELECT user_id, profile_id, tier, CONCAT(user_id, profile_id, tier) AS unique_code FROM user_profile WHERE user_id = :user_id"), {'user_id': user_id})

		# iterate over SQL object to extract unique_code
		list_to_check = []
		for unique_code in users_existing_profiles:
			list_to_check.append(unique_code.unique_code)

		if requested_profile_code in list_to_check:
			flash('User already has that profile at that tier.', 'danger')
			return redirect(url_for('portal_admin.admin_manage_profiles'))
		else:
			try:
				assign_profile(user_id, profile_id, int(tier), current_user)
				flash('User has been assigned a new profile.', 'success')
			except Exception as e:
				db.session.rollback()
				log_message = f"[ERROR] Error assigning a new profile tier to user {user_id}: {e}."
				db.session.add(Log(message=log_message, user_id=current_user.id))
				db.session.commit()
				send_error_message(log_message)
				flash('There was an error assigning the profile.', 'danger')
			return redirect(url_for('portal_admin.admin_manage_profiles'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403


@portal_admin.route('/admin/assign_badge', methods=['GET', 'POST'])
@login_required
def admin_assign_badge():
	if current_user.is_admin != 1:
		abort(403)
	badge_form = BadgeAssignmentForm()

	if request.method == 'GET' and current_user.is_admin == 1:
		assigned_badges = db.session.execute(text('SELECT u.id, u.firstname, u.lastname, string_agg(b.name, \', \') as badges FROM "user" u JOIN user_badge ub ON ub.user_id = u.id JOIN badge b ON b.id = ub.badge_id WHERE u.status = \'Active\' GROUP BY u.id ORDER BY u.firstname'))
		return render_template('admin_assign_badge.html', assigned_badges=assigned_badges, badge_form=badge_form)

	if request.method == 'POST' and badge_form.submit_badge.data and current_user.is_admin == True:
		if not badge_form.validate_on_submit():
			flash('Please fill out all badge assignment fields.', 'danger')
			return redirect(url_for('portal_admin.admin_assign_badge'))
		user_id = badge_form.user_name.data.id
		badge_id = badge_form.badge_name.data.id

		if award_badge(user_id, badge_id, current_user, badge_form.assigner_justify.data):
			flash('Badge successfully assigned.', 'success')
			return redirect(url_for('portal_admin.admin_assign_badge'))
		else:
			flash('Cannot add badge - user already has it.', 'danger')
			current_app.logger.warning('The system raised an error when trying to assign a badge. Badge-{} was assigned to User-{}, but was given an error that they already have it.'.format(badge_id, user_id))
			return redirect(url_for('portal_admin.admin_assign_badge'))


@portal_admin.route('/admin/upload_badges', methods=['GET', 'POST'])
@login_required
def admin_upload_badges():
	if current_user.is_admin != 1:
		abort(403)
	badge_upload_form = NewBadgeUploadForm()

	if request.method == 'GET' and current_user.is_admin == 1:
		return render_template('admin_upload_badge.html', badge_upload_form=badge_upload_form)

	elif request.method == 'POST' and badge_upload_form.name.data and current_user.is_admin == 1:
		if badge_upload_form.limited_edition.data == True:
			is_limited_edition = 1
		else:
			is_limited_edition = 0
		file = save_new_badge(badge_upload_form.file.data, badge_upload_form.name.data)
		badge = Badge(
			name = badge_upload_form.name.data.title(),
			badge_url = file,
			limited_edition = is_limited_edition,
			description = badge_upload_form.description.data
		)
		db.session.add(badge)
		db.session.commit()
		current_app.logger.info('A new badge called {} has been added to the Portal by User-{}.'.format(badge.name, current_user.id))
		flash('New badge successfully created!', 'success')
		return redirect(url_for('portal_admin.admin_upload_badges'))


@portal_admin.route('/admin/approve_members', methods=['GET', 'POST'])
@login_required
def admin_approve_members():
	pending_users = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.status=='Pending').all()

	return render_template('admin_approve_members.html', pending_users=pending_users)


@portal_admin.route('/admin/process_reviews')
@login_required
def admin_process_reviews():
	open_reviews = db.session.query(Review, Emergency).join(Emergency, Emergency.id == Review.emergency_id).filter(Review.status == 'Open').all()

	return render_template('admin_process_reviews.html', open_reviews=open_reviews)


@portal_admin.route('/admin/edit_skills', methods=['GET', 'POST'])
@login_required
def admin_edit_skills():
	if current_user.is_admin != 1:
		abort(403)
	skill_form = SkillCreatorForm()

	if request.method == 'GET' and current_user.is_admin == 1:
		all_skills = db.session.query(Skill.name, Skill.category).order_by(Skill.category, Skill.name).all()
		return render_template('admin_edit_skills.html', skill_form=skill_form, all_skills=all_skills)

	if request.method == 'POST' and skill_form.submit_skill.data and current_user.is_admin == 1:
		new_skill = Skill(
			name = skill_form.name.data,
			category = skill_form.category.data
		)
		db.session.add(new_skill)
		db.session.commit()

		log_message = f"[INFO] A new skill has been added to the Portal: {new_skill.name}."
		new_log = Log(message=log_message, user_id=current_user.id)
		db.session.add(new_log)
		db.session.commit()

		flash("New Skill Created.", "success")
		return redirect(url_for('portal_admin.admin_edit_skills'))


@portal_admin.route('/admin/process_acronyms', methods=['GET', 'POST'])
@login_required
def admin_process_acronyms():
	# anonymous submissions are attributed to user 63 (Clara Barton)
	# member submissions are auto-approved, so anything still unapproved (e.g. old anonymous
	# submissions, filed under the bot account) is pending review
	pending_acronyms = db.session.query(Acronym).filter(Acronym.approved_by.is_(None))

	return render_template('admin_process_acronyms.html', pending_acronyms=pending_acronyms)


@portal_admin.route('/admin/view_logs', methods=['GET', 'POST'])
@login_required
def view_logs():
	if current_user.is_admin == 1:
		logs = db.session.query(Log, User).outerjoin(User, User.id == Log.user_id).order_by(desc(Log.timestamp)).limit(1000).all()

		# split a leading "[ERROR]"-style tag out of each message for display, without
		# modifying the Log objects themselves (they're attached to the session)
		rows = []
		for log, user in logs:
			message = log.message or ''
			match = re.search(r'\[(\w+)\]', message)
			severity = match.group(1) if match else ''
			if match:
				message = message.replace(match.group(0), '')
			rows.append({'log': log, 'user': user, 'message': message, 'severity': severity})

		return render_template('admin_logs.html', logs=rows)
	else:
		abort(403)


@portal_admin.route('/admin/assign_regional_focal_point', methods=['GET', 'POST'])
@login_required
def assign_regional_focal_point():
	form = RegionalFocalPointForm()

	if request.method == 'GET' and current_user.is_admin == 1:
		current_focal_points = db.session.query(RegionalFocalPoint, User, Region).join(User, User.id == RegionalFocalPoint.focal_point_id).join(Region, Region.id == RegionalFocalPoint.regional_id).all()

		return render_template('admin_assign_regional_focal_point.html', form=form, current_focal_points=current_focal_points)

	if request.method == 'POST' and current_user.is_admin == 1:
		if form.validate_on_submit():
			existing_record = db.session.query(RegionalFocalPoint).filter_by(regional_id=form.region.data.id).first()

			if existing_record:
				# Update existing record
				existing_record.focal_point_id = form.user_name.data.id
				db.session.commit()
				flash("Successfully updated the regional focal point.", "success")
			else:
				# Create a new record
				regional_focal_point = RegionalFocalPoint(
					focal_point_id=form.user_name.data.id,
					regional_id=form.region.data.id
				)
				db.session.add(regional_focal_point)
				db.session.commit()
				flash("Successfully assigned the regional focal point.", "success")

			new_focal_point_info = db.session.query(User).filter(User.id == form.user_name.data.id).first()
			log_message = f"[INFO] {new_focal_point_info.firstname} {new_focal_point_info.lastname} has been assigned a regional IM focal point role in the database."
			db.session.add(Log(message=log_message, user_id=current_user.id))
			db.session.commit()

			return redirect(url_for('portal_admin.assign_regional_focal_point'))
		else:
			flash("Error: Focal point ID is None.", "danger")

	return render_template('admin_assign_regional_focal_point.html', form=form)


# Jobs an admin can trigger from /manual_refresh. Only names listed here can be run.
MANUAL_REFRESH_BADGE_JOBS = {
	'autobiographer': auto_badge_assigner_autobiographer,
	'big_wig': auto_badge_assigner_big_wig,
	'edward_tufte': auto_badge_assigner_edward_tufte,
	'jack_of_all_trades': auto_badge_assigner_jack_of_all_trades,
	'maiden_voyage': auto_badge_assigner_maiden_voyage,
	'old_salt': auto_badge_assigner_old_salt,
	'polyglot': auto_badge_assigner_polyglot,
	'self_promoter': auto_badge_assigner_self_promoter,
	'world_traveler': auto_badge_assigner_world_traveler,
}


MANUAL_REFRESH_JOBS = {
	**MANUAL_REFRESH_BADGE_JOBS,
	'alert_inactive_members': alert_inactive_members,
	'bulk_slack_photo_update': bulk_slack_photo_update,
	'refresh_all_active_githubs': refresh_all_active_githubs,
	'refresh_open_alert_statuses': refresh_open_alert_statuses,
	'refresh_surge_alerts': refresh_surge_alerts,
	'refresh_surge_alerts_latest': refresh_surge_alerts_latest,
	'request_availability_updates': request_availability_updates,
}


_BADGE_RERUN_NOTE = "Members who already have the badge are skipped, so it's safe to run at any time."
_DAILY_BADGE_NOTE = 'Runs automatically every day at 5 PM Eastern.'

# What the manual refresh page shows for each job: (job name, title, description,
# whether running it sends Slack messages to members). Every name must be in
# MANUAL_REFRESH_JOBS, which is what the run route accepts.
MANUAL_REFRESH_BADGE_TASKS = [
	('autobiographer', 'Autobiographer', f'Awards the Autobiographer badge to members whose profile bio is over 500 characters. {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
	('big_wig', 'Big Wig', f'Awards the Big Wig badge to members with five or more remote support assignments (removed assignments don\'t count). {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
	('edward_tufte', 'Edward Tufte', f'Awards the Edward Tufte badge to members with five or more approved infographics in the portfolio. {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
	('jack_of_all_trades', 'Jack of All Trades', f'Awards the Jack of All Trades badge to members with six or more profiles on their account. {_BADGE_RERUN_NOTE} This one isn\'t on the daily schedule, so it only runs from here.', False),
	('maiden_voyage', 'Maiden Voyage', f'Awards the Maiden Voyage badge to members with at least one remote support assignment (removed assignments don\'t count). {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
	('old_salt', 'Old Salt', f'Awards the Old Salt badge to members who have served as SIMS Remote Coordinator on three or more assignments. {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
	('polyglot', 'Polyglot', f'Awards the Polyglot badge to members with two or more languages on their profile. {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
	('self_promoter', 'Self Promoter', f'Awards the Self Promoter badge to members with at least one skill on their profile. {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
	('world_traveler', 'World Traveler', f'Awards the World Traveler badge to members with assignments to emergencies in five or more different countries. {_BADGE_RERUN_NOTE} {_DAILY_BADGE_NOTE}', False),
]

MANUAL_REFRESH_MAINTENANCE_TASKS = [
	('refresh_surge_alerts_latest', 'Refresh Surge Alerts',
	 'Fetches the 50 newest surge alerts from GO, adds any new ones and updates the details of ones already in the Portal. '
	 'New Information Management alerts are announced in Slack. Runs automatically every three hours from 1 AM to 4 PM Eastern; '
	 'run it here to pick up a new alert right away.', True),
	('refresh_open_alert_statuses', 'Re-check Open Surge Alerts',
	 'Looks up every alert the Portal still lists as open, one at a time, and updates its status and details from GO. This catches '
	 'alerts that closed, or were linked to an emergency, after they dropped out of the newest 50. An open alert that has only now '
	 'become an Information Management alert is announced in Slack. Runs automatically with the surge alert refresh.', True),
	('refresh_surge_alerts', 'Full Surge Alert Backfill',
	 'Goes through GO\'s entire surge alert history (a few thousand alerts) and updates every detail of every alert in the Portal, '
	 'adding any that are missing. It doesn\'t send any Slack notices. It takes a minute or two and is usually only needed to repair data.', False),
	('request_availability_updates', 'Request Availability Updates',
	 'Posts a request in the Slack channel of every active emergency asking members to update their availability for that response.', True),
	('alert_inactive_members', 'Alert Inactive Members',
	 'Sends a Slack direct message to every member who hasn\'t logged in for six months, asking them to log in if they want to stay '
	 'listed as Active. Runs automatically every Thursday at 9 AM Eastern, and running it again sends the same messages again.', True),
	('bulk_slack_photo_update', 'Update Missing Avatars',
	 'For every member still using the default avatar, copies their Slack profile photo onto their Portal profile.', False),
	('refresh_all_active_githubs', 'Refresh GitHub Issues for Active Emergencies',
	 'Pulls the latest issues from the GitHub repository of every active emergency so their task lists are up to date.', False),
]

MANUAL_REFRESH_TITLES = {name: title for name, title, _, _ in MANUAL_REFRESH_BADGE_TASKS + MANUAL_REFRESH_MAINTENANCE_TASKS}


@portal_admin.route('/manual_refresh')
@login_required
def manual_refresh_landing():
	if current_user.is_admin != 1:
		list_of_admins = db.session.query(User).filter(User.is_admin == True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
	return render_template(
		'admin_manual_refresh.html',
		task_groups=[
			('maintenance', 'Maintenance Tasks', MANUAL_REFRESH_MAINTENANCE_TASKS),
			('badges', 'Automatic Badge Assigners', MANUAL_REFRESH_BADGE_TASKS),
		],
	)


# POST-only (with the app-wide CSRF token) so a link or embedded image on another
# site can't trigger a job in a logged-in admin's browser
@portal_admin.route('/manual_refresh/<func>', methods=['POST'])
@login_required
def manual_refresh(func):
	if current_user.is_admin != 1:
		list_of_admins = db.session.query(User).filter(User.is_admin == True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403
	job = MANUAL_REFRESH_JOBS.get(func)
	if job is None:
		abort(404)
	job()
	current_app.logger.info('User-{} ran the {} function manually.'.format(current_user.id, func))
	flash('{} ran successfully.'.format(MANUAL_REFRESH_TITLES.get(func, func)), 'success')
	return redirect(url_for('portal_admin.manual_refresh_landing'))
