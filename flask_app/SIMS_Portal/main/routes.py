import csv
import io
import json
import logging
import os
import re
from datetime import datetime

import pandas as pd
from flask import (
	abort, request, render_template, url_for, flash, redirect,
	jsonify, Blueprint, current_app, session, send_file
)
from flask_login import (
	login_user, current_user, logout_user, login_required
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import boto3
import botocore

from SIMS_Portal import db, cache
from SIMS_Portal.config import Config
from SIMS_Portal.models import (
	Assignment, User, Emergency, Alert, user_skill, user_language,
	user_badge, Skill, Language, NationalSociety, Badge, Story,
	EmergencyType, Review, user_profile, Profile
)
from SIMS_Portal.main.forms import (
	MemberSearchForm, EmergencySearchForm, ProductSearchForm,
	BadgeAssignmentForm, SkillCreatorForm, BadgeAssignmentViaSIMSCoForm,
	NewBadgeUploadForm
)
from SIMS_Portal.main.utils import (
	fetch_slack_channels, check_sims_co, save_new_badge,
	auto_badge_assigner_big_wig, auto_badge_assigner_maiden_voyage,
	auto_badge_assigner_self_promoter, auto_badge_assigner_polyglot,
	auto_badge_assigner_autobiographer, auto_badge_assigner_jack_of_all_trades,
	auto_badge_assigner_edward_tufte, auto_badge_assigner_world_traveler,
	auto_badge_assigner_old_salt
)
from SIMS_Portal.users.forms import AssignProfileTypesForm
from SIMS_Portal.users.utils import (
	send_slack_dm, new_surge_alert, send_reset_slack, update_member_locations
)
from SIMS_Portal.alerts.utils import (
	refresh_surge_alerts, refresh_surge_alerts_latest
)
from SIMS_Portal.emergencies.utils import (
	update_response_locations, update_active_response_locations,
	get_trello_tasks
)
from SIMS_Portal.availability.utils import (
	send_slack_availability_request, request_availability_updates
)


main = Blueprint('main', __name__)

@main.route('/') 
def index(): 
	latest_stories = db.session.query(Story, Emergency).join(Emergency, Emergency.id == Story.emergency_id).order_by(Story.id.desc()).limit(3).all()
	return render_template('index.html', latest_stories=latest_stories)
	
@main.route('/about')
def about():
	count_activations = db.session.query(Emergency).count()
	all_activations = db.session.query(Emergency).all()
	lateset_activation = db.session.query(Emergency).order_by(Emergency.created_at.desc()).filter(Emergency.emergency_status != 'Removed').first()
	count_members = db.session.query(User).filter(User.status == 'Active').count()
	return render_template('about.html', count_activations=count_activations, latest_activation=lateset_activation, count_members=count_members, all_activations=all_activations)

@main.route('/portal_admins')
def portal_admins():
	list_admins = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.is_admin == 1).all()
	return render_template('portal_admins.html', list_admins=list_admins)

@main.route('/get_slack_id')
def get_slack_id():
	return render_template('slack-id-how-to.html')

@main.route('/badges')
def badges():
	assigned_badges = db.engine.execute("SELECT name, badge.id as id, description, badge_url, limited_edition, count(user_badge.user_id) as count FROM badge LEFT JOIN user_badge ON user_badge.badge_id = badge.id WHERE limited_edition = false GROUP BY name, badge.id, description, limited_edition ORDER BY name")
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
	
	return render_template('badges.html', count_active_members=count_active_members, all_badges=all_badges, list_assigned_badges=list_assigned_badges, all_limited_edition_badges=all_limited_edition_badges)

@main.route('/badges/create', methods=['GET', 'POST'])
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
		return redirect(url_for('main.admin_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@main.route('/admin_landing', methods=['GET', 'POST'])
@login_required
def admin_landing():
	profile_form = AssignProfileTypesForm()
	badge_form = BadgeAssignmentForm()
	skill_form = SkillCreatorForm()
	badge_upload_form = NewBadgeUploadForm()
	if request.method == 'GET' and current_user.is_admin == 1:
		open_reviews = db.session.query(Review, Emergency).join(Emergency, Emergency.id == Review.emergency_id).filter(Review.status == 'Open').all()
		pending_users = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.status=='Pending').all()
		all_users = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.status == 'Active').order_by(User.firstname).all()
		assigned_badges = db.engine.execute('SELECT u.id, u.firstname, u.lastname, string_agg(b.name, \', \') as badges FROM "user" u JOIN user_badge ub ON ub.user_id = u.id JOIN badge b ON b.id = ub.badge_id WHERE u.status = \'Active\' GROUP BY u.id ORDER BY u.firstname')
		all_skills = db.session.query(Skill.name, Skill.category).order_by(Skill.category, Skill.name).all()
		all_assigned_profiles = db.engine.execute('SELECT user_id, firstname || \' \' || lastname as user_name, profile_id, max(tier) as max_tier, name FROM user_profile JOIN profile ON profile.id = user_profile.profile_id JOIN "user" ON "user".id = user_profile.user_id WHERE "user".status = \'Active\' GROUP BY user_id, profile_id, firstname, lastname, name ORDER BY user_name')
		return render_template('admin_landing.html', pending_users=pending_users, all_users=all_users, badge_form=badge_form, assigned_badges=assigned_badges, skill_form=skill_form, all_skills=all_skills, badge_upload_form=badge_upload_form, open_reviews=open_reviews, profile_form=profile_form,all_assigned_profiles=all_assigned_profiles)
	
	# assign badge
	elif request.method == 'POST' and badge_form.submit_badge.data and current_user.is_admin == True:
		if badge_form.validate_on_submit():
			user_id = badge_form.user_name.data.id
			badge_id = badge_form.badge_name.data.id
			session['assigner_justify'] = badge_form.assigner_justify.data
		else:
			flash('Please fill out all badge assignment fields.', 'danger')
			return redirect(url_for('main.admin_landing'))

		# get list of assigned badges, create column that concats user_id and badge_id to create unique identifier
		badge_ids = db.engine.execute("SELECT CAST(user_id AS text) || CAST(badge_id AS text) as unique_code FROM user_badge WHERE user_id = {}".format(user_id))

		list_to_check = []
		for id in badge_ids:
			list_to_check.append(id[0])
		
		attempted_user_badge_code = str(user_id) + str(badge_id)
		
		# check list against the values we're trying to save, and proceed if user doesn't already have that badge
		if attempted_user_badge_code not in list_to_check:
			return redirect(url_for('main.badge_assignment', user_id=user_id, badge_id=badge_id))
		else:
			flash('Cannot add badge - user already has it.', 'danger')
			current_app.logger.warning('The system raised an error when trying to assign a badge. Badge-{} was assigned to User-{}, but was given an error that they already have it.'.format(badge_id, user_id))
			return redirect(url_for('main.admin_landing'))
	
	# save skill
	elif request.method == 'POST' and skill_form.submit_skill.data and current_user.is_admin == 1:
		new_skill = Skill(
			name = skill_form.name.data,
			category = skill_form.category.data
		)
		db.session.add(new_skill)
		db.session.commit()
		current_app.logger.info('A new skill has been added to the list by {} {}.'.format(current_user.firstname, current_user.lastname))
		flash("New Skill Created.", "success")
		return redirect(url_for('main.admin_landing'))
	
	# upload new badge
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
		return redirect(url_for('main.admin_landing'))
	
	# assign profile to user
	elif request.method == 'POST' and profile_form.user_name.data and current_user.is_admin == 1:
		
		user_id = profile_form.user_name.data.id
		try:
			profile_id = profile_form.profiles.data.id
		except:
			flash('A profile is required.', 'danger')
			return redirect(url_for('main.admin_landing'))
		tier = profile_form.tier.data 
		requested_profile_code = str(user_id) + str(profile_id) + str(tier)
		
		if tier == '':
			flash('A tier is required.', 'danger')
			return redirect(url_for('main.admin_landing'))
		
		# get the user's existing profiles and tiers, generate unique code that concats all three elements
		users_existing_profiles = db.engine.execute("SELECT user_id, profile_id, tier, CONCAT(user_id, profile_id, tier) AS unique_code FROM user_profile WHERE user_id = {}".format(user_id))
		
		# iterate over SQL object to extract unique_code
		list_to_check = []
		for unique_code in users_existing_profiles:
			list_to_check.append(unique_code.unique_code)
		
		if requested_profile_code in list_to_check:
			flash('User already has that profile at that tier.', 'danger')
			return redirect(url_for('main.admin_landing'))
		else:
			return redirect(url_for('users.assign_profiles', user_id=user_id, profile_id=profile_id, tier=tier))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

# route for admin-level users assigning badges
@main.route('/badge_assignment/<int:user_id>/<int:badge_id>')
@login_required
def badge_assignment(user_id, badge_id):
	if current_user.is_admin == 1:
		new_badge = user_badge.insert().values(user_id=user_id, badge_id=badge_id, assigner_id=current_user.id, assigner_justify=session.get('assigner_justify', None))
		db.session.execute(new_badge)
		db.session.commit()
		
		# try sending slack message alerting user to the new badge
		try:
			user_info = db.session.query(User).filter(User.id == user_id).first()
			assigner_info = db.session.query(User).filter(User.id == current_user.id).first()
			badge_info = db.session.query(Badge).filter(Badge.id == badge_id).first()
			assigner_justify = session.get('assigner_justify', None)
			message = 'Hi {}, you have been assigned a new badge on the SIMS Portal! {} has given you the {} badge with the following message: {}'.format(user_info.firstname, assigner_info.fullname, badge_info.name, assigner_justify)
			user = user_info.slack_id
			send_slack_dm(message, user)
		except:
			pass
		flash('Badge successfully assigned.', 'success')
		return redirect(url_for('main.admin_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

# route for sims remote coordinator users assigning badges
@main.route('/badge_assignment/<int:user_id>/<int:badge_id>/<int:assigner_id>/<int:dis_id>')
@login_required
def badge_assignment_via_SIMSCO(user_id, badge_id, assigner_id, dis_id):
	user_is_sims_co = check_sims_co(dis_id)
	badge_form = BadgeAssignmentViaSIMSCoForm()
	if user_is_sims_co:
		assigner_justify = badge_form.assigner_justify.data
		# uses session to get assigner_justify from form
		new_badge = user_badge.insert().values(user_id=user_id, badge_id=badge_id, assigner_id=assigner_id, assigner_justify=session.get('assigner_justify', None))
		db.session.execute(new_badge)
		db.session.commit()
		try:
			assigner = db.session.query(User).filter(User.id == assigner_id).first()
			receiver = db.session.query(User).filter(User.id == user_id).first()
			badge = db.session.query(Badge).filter(Badge.id == badge_id).first()
			message = 'Hi {}, you have been assigned a new badge on the SIMS Portal! {} has given you the {} badge with the following message: {}'.format(receiver.firstname, assigner.fullname, badge.name, session.get('assigner_justify', None))
			user = db.session.query(User).filter(User.id == user_id).first()
			send_slack_dm(message, user.slack_id)
		except Exception as e:
			current_app.logger.error('Badge Assignment via SIMS Remote Coordinator Failed: {}'.format(e))
		current_app.logger.info('A new badge has been assigned to User-{}'.format(receiver.id))
		flash('Badge successfully assigned.', 'success')
		return redirect(url_for('main.badge_assignment_sims_co', dis_id=dis_id))
	elif user_is_sims_co == False:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@main.route('/badge_assignment_simsco/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def badge_assignment_sims_co(dis_id):
	badge_form = BadgeAssignmentViaSIMSCoForm()
	
	event_name = db.session.query(Emergency).filter(Emergency.id == dis_id).first()
	
	assigned_badges = db.engine.execute("SELECT u.id, u.firstname, u.lastname, string_agg(b.name, ', ') as badges FROM public.user u JOIN user_badge ub ON ub.user_id = u.id JOIN badge b ON b.id = ub.badge_id JOIN assignment a ON a.user_id = u.id JOIN emergency e ON e.id = a.emergency_id WHERE u.status = 'Active' AND e.id = {} AND a.role = 'Remote IM Support' AND a.assignment_status = 'Active' GROUP BY u.id ORDER BY u.firstname".format(dis_id))
	
	assigned_members = db.session.query(Emergency, Assignment, User).join(Assignment, Assignment.emergency_id == Emergency.id).join(User, User.id == Assignment.user_id).filter(Emergency.id == dis_id).all()
	
	# generate list of user IDs of users listed as SIMS Remote Coordinators on emergency
	sims_co_ids = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == dis_id, Assignment.role == 'SIMS Remote Coordinator').all()
	
	user_is_sims_co = check_sims_co(dis_id)
	
	if request.method == 'GET' and user_is_sims_co == True:
		query = User.query.join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == dis_id, Assignment.role == 'Remote IM Support', Assignment.assignment_status == 'Active')
		badge_form.user_name.query = query
		return render_template('emergency_badge_assignment.html', title='Assign Badges', user_is_sims_co=user_is_sims_co, assigned_members=assigned_members, event_name=event_name, badge_form=badge_form, assigned_badges=assigned_badges)
	elif request.method == 'POST' and user_is_sims_co == True:
		user_id = badge_form.user_name.data.id
		badge_id = badge_form.badge_name.data.id
		# use flask session to pass 'assigner_justify' field data without passing through URL
		session['assigner_justify'] = badge_form.assigner_justify.data
		
		# get all badges assigned to the user which sims co is trying to assign
		users_badges = db.engine.execute('SELECT u.id, user_badge.user_id, user_badge.badge_id FROM public.user u JOIN user_badge ON user_badge.user_id = u.id WHERE u.id = {}'.format(user_id))
		users_badges_ids = []
		for badge in users_badges:
			users_badges_ids.append(badge.badge_id)
		
		if badge_form.validate_on_submit():
			# check that user does not already have the badge
			if badge_id not in users_badges_ids:
				# pass to assignment route for database interaction
				return redirect(url_for('main.badge_assignment_via_SIMSCO', user_id=user_id, badge_id=badge_id, assigner_id=current_user.id, dis_id=dis_id))
			else:
				flash('Cannot add badge - user already has it.', 'danger')
				return redirect(url_for('main.badge_assignment_sims_co', dis_id=dis_id))
		else:
			flash('Please fill out all sections of the form.', 'warning')
			return redirect(url_for('main.badge_assignment_sims_co', dis_id=dis_id))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==True).all()
		print('User {} tried to assign a badge but was denied and given a 403 error.'.format(current_user.fullname))
		return render_template('errors/403.html', list_of_admins=list_of_admins, user_is_sims_co=user_is_sims_co, event_name=event_name, sims_co_ids=sims_co_ids), 403

@main.route('/learning')
@login_required
def learning():
	return render_template('learning.html')

@main.route('/privacy')
def privacy_policy():
	return render_template('privacy_policy.html')

@main.route('/resources')
def resources():
	return render_template('resources/resources.html')

@main.route('/resources/colors')
@login_required
def resources_colors():
	return render_template('/resources/colors.html')

@main.route('/resources/communication_collaboration')
@login_required
def communication_and_collaboration():
	return render_template('/resources/communication_collaboration.html')

@main.route('/resources/slack')
@login_required
def resources_slack():
	return render_template('/resources/slack.html')

@main.route('/resources/slack/channels')
@login_required
def resources_slack_channels():
	output = fetch_slack_channels()
	return render_template('resources/slack_channels.html', output=output)
	
@main.route('/resources/sims_portal')
@login_required
def resources_sims_portal():
	return render_template('/resources/sims_portal.html')

@main.route('/dashboard')
@login_required
def dashboard():
	active_emergencies = db.session.query(Emergency, NationalSociety, EmergencyType).join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id).join(EmergencyType, EmergencyType.emergency_type_go_id == Emergency.emergency_type_id).filter(Emergency.emergency_status == 'Active').all()
	count_active_emergencies = db.session.query(Emergency, NationalSociety, EmergencyType).join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id).join(EmergencyType, EmergencyType.emergency_type_go_id == Emergency.emergency_type_id).filter(Emergency.emergency_status == 'Active').count()
	
	todays_date = datetime.today()
	
	assignments_by_emergency = db.engine.execute("SELECT emergency_name, COUNT(*) as count_assignments FROM emergency JOIN assignment ON assignment.emergency_id = emergency.id WHERE assignment.assignment_status <> 'Removed' GROUP BY emergency_name")
	data_dict_assignments = [x._asdict() for x in assignments_by_emergency]
	labels_for_assignment = [row['emergency_name'] for row in data_dict_assignments]
	values_for_assignment = [row['count_assignments'] for row in data_dict_assignments]
	
	pending_user_check = db.session.query(User).filter(User.status == 'Pending').all()
	
	products_by_emergency = db.engine.execute("SELECT emergency_name , COUNT(*) as count_products FROM emergency JOIN portfolio ON portfolio.emergency_id = emergency.id WHERE portfolio.product_status <> 'Removed' GROUP BY emergency_name")
	data_dict_products = [y._asdict() for y in products_by_emergency]
	labels_for_product = [row['emergency_name'] for row in data_dict_products]
	values_for_product = [row['count_products'] for row in data_dict_products]
	
	count_active_assignments = db.session.query(Assignment, User, Emergency).join(User, User.id==Assignment.user_id).join(Emergency, Emergency.id==Assignment.emergency_id).filter(Assignment.assignment_status=='Active', Assignment.end_date>todays_date).count()
	active_assignments = db.session.query(Assignment, User, Emergency, NationalSociety).join(User, User.id==Assignment.user_id).join(Emergency, Emergency.id==Assignment.emergency_id).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(Assignment.assignment_status=='Active', Assignment.role != 'Remote IM Support', Assignment.end_date>todays_date).order_by(Emergency.emergency_name, Assignment.end_date).all()

	most_recent_emergencies = db.session.query(Emergency).order_by(Emergency.created_at.desc()).limit(7).all()
	most_recent_members = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.status == 'Active').order_by(User.created_at.desc()).limit(7).all()
	
	surge_alerts = db.session.query(Alert).all()
	
	return render_template('dashboard.html', active_assignments=active_assignments, count_active_assignments=count_active_assignments, most_recent_emergencies=most_recent_emergencies, labels_for_assignment=labels_for_assignment, values_for_assignment=values_for_assignment, labels_for_product=labels_for_product, values_for_product=values_for_product, most_recent_members=most_recent_members, pending_user_check=pending_user_check, active_emergencies=active_emergencies, count_active_emergencies=count_active_emergencies,surge_alerts=surge_alerts)

@main.route('/role_profile/<type>')
def view_role_profile(type):
	capitalized_type = type.capitalize()
	users_with_profile = db.engine.execute('SELECT "user".id, firstname, lastname, max(tier) as tier, image_file FROM "user" JOIN user_profile ON "user".id = user_profile.user_id JOIN profile ON profile.id = user_profile.profile_id WHERE image = \'{}\' GROUP BY "user".id'.format(capitalized_type))
	
	users_with_profile_tier_1 = []
	users_with_profile_tier_2 = []
	users_with_profile_tier_3 = []
	users_with_profile_tier_4 = []
	for user in users_with_profile:
		if user.tier == 1:
			users_with_profile_tier_1.append(user)
		elif user.tier == 2:
			users_with_profile_tier_2.append(user)
		elif user.tier == 3:
			users_with_profile_tier_3.append(user)
		elif user.tier == 4:
			users_with_profile_tier_4.append(user)
	
	count_users_with_profile = db.engine.execute('SELECT count(distinct("user".id)) as count FROM "user" JOIN user_profile ON "user".id = user_profile.user_id JOIN profile ON profile.id = user_profile.profile_id WHERE image = \'{}\''.format(capitalized_type))
	unpacked_count = [x.count for x in count_users_with_profile][0]
	
	return render_template('role_profile_{}.html'.format(type), users_with_profile_tier_1=users_with_profile_tier_1, users_with_profile_tier_2=users_with_profile_tier_2, users_with_profile_tier_3=users_with_profile_tier_3, users_with_profile_tier_4=users_with_profile_tier_4, unpacked_count=unpacked_count)

@main.route('/manual_refresh')
@login_required
def manual_refresh_landing():
	badge_refresh_list = ['big_wig', 'maiden_voyage', 'self_promoter', 'polyglot', 'autobiographer', 'jack_of_all_trades','edward_tufte', 'world_traveler','old_salt']
	sorted_badge_refresh_list = sorted(badge_refresh_list)
	if current_user.is_admin == 1:
		return render_template('manual_refresh.html', sorted_badge_refresh_list=sorted_badge_refresh_list)

@main.route('/manual_refresh/<func>')
@login_required
def manual_refresh(func):
	if current_user.is_admin == 1:
		badge_refresh_list = ['big_wig', 'maiden_voyage', 'self_promoter', 'polyglot', 'autobiographer', 'jack_of_all_trades','edward_tufte', 'world_traveler','old_salt']
		if func in badge_refresh_list:
			function_constructor = 'auto_badge_assigner_' + func + '()'
		else:
			function_constructor = func + '()'
		eval(function_constructor)
		current_app.logger.info('User-{} ran the {} function manually.'.format(current_user.id, func))
		flash('{} function ran successfully.'.format(func), 'success')
		return redirect(url_for('main.manual_refresh_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin == 1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@main.route('/staging') 
def staging(): 
	if current_user.is_admin == 1:
		# put code to debug here

		return render_template('visualization.html')
	else:
		current_app.logger.warning('User-{}, a non-administrator, tried to access the staging area'.format(current_user.id))
		list_of_admins = db.session.query(User).filter(User.is_admin == 1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@main.route("/uploads/<path:name>")
def download_file(name):
    s3 = boto3.resource('s3')
    file_stream = io.BytesIO()
    s3_object = s3.Object(current_app.config['UPLOAD_BUCKET'], name)
    try:
        s3_object.download_fileobj(file_stream)
    except botocore.exceptions.ClientError as e:
        current_app.logger.error(e)
        abort(404)
    file_stream.seek(0)
    return send_file(file_stream, mimetype=s3_object.content_type)
