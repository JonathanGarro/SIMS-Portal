from flask import request, render_template, url_for, flash, redirect, jsonify, Blueprint, current_app, session
from SIMS_Portal.models import Assignment, User, Emergency, Alert, user_skill, user_language, user_badge, Skill, Language, NationalSociety, Badge, Story, EmergencyType, Review
from SIMS_Portal import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from SIMS_Portal.main.forms import MemberSearchForm, EmergencySearchForm, ProductSearchForm, BadgeAssignmentForm, SkillCreatorForm, BadgeAssignmentViaSIMSCoForm, NewBadgeUploadForm
from collections import defaultdict, Counter
from datetime import date, timedelta
from SIMS_Portal.config import Config
from SIMS_Portal.main.utils import fetch_slack_channels, check_sims_co, save_new_badge
from SIMS_Portal.users.utils import send_slack_dm
import os
import tweepy
import re
import csv
import json
import pandas as pd

main = Blueprint('main', __name__)

@main.route('/') 
def index(): 
	consumer_key = current_app.config['CONSUMER_KEY']
	consumer_secret = current_app.config['CONSUMER_SECRET']
	access_token = current_app.config['ACCESS_TOKEN']
	access_token_secret = current_app.config['ACCESS_TOKEN_SECRET']
	
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	api = tweepy.API(auth)
	
	public_tweets = api.user_timeline(screen_name='IFRC_SIMS', count=3, tweet_mode="extended")
	
	# list comprehension to grab relevant fields and regex to remove URLs in tweet
	tweets = [{'tweet': re.sub(r"http\S+", "", t.full_text), 'created_at_year': t.created_at.year, 'created_at_month': t.created_at.month, 'created_at_day': t.created_at.day, 'headshot_url': t.user.profile_image_url, 'username': t.user.name, 'screen_name': t.user.screen_name, 'location': t.user.location, 'id': t.id_str} for t in public_tweets]
	
	latest_stories = db.session.query(Story, Emergency).join(Emergency, Emergency.id == Story.emergency_id).order_by(Story.id.desc()).limit(3).all()
	return render_template('index.html', latest_stories=latest_stories, tweets=tweets)
	
@main.route('/about')
def about():
	count_activations = db.session.query(Emergency).count()
	lateset_activation = db.session.query(Emergency).order_by(Emergency.created_at.desc()).first()
	count_members = db.session.query(User).filter(User.status == 'Active').count()
	return render_template('about.html', count_activations=count_activations, latest_activation=lateset_activation, count_members=count_members)
	
@main.route('/badges')
def badges():
	badges = db.engine.execute("SELECT * FROM user_badge JOIN Badge ON Badge.id = user_badge.badge_id")
	count_active_members = db.session.query(User).filter(User.status == 'Active').count()
	
	# loop over each item in sqlalchemy object, append the badge name to a list, and use Counter() to summarize
	count_list = []
	for badge in badges:
		count_list.append(badge[7])
	badge_counts = Counter(count_list)
	
	return render_template('badges.html', badge_counts=badge_counts, count_active_members=count_active_members)

@main.route('/badges/create', methods=['GET', 'POST'])
@login_required
def create_badge():
	form = NewBadgeUploadForm()
	if current_user.is_admin == 1 and form.validate_on_submit() and form.file.data:
		file = save_new_badge(form.file.data)
		badge = Badge(name = form.name.data, badge_url = file)
		db.session.execute(badge)
		db.session.commit()
		flash('New badge successfully created!', 'success')
		return redirect(url_for('main.admin_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@main.route('/admin_landing', methods=['GET', 'POST'])
@login_required
def admin_landing():
	badge_form = BadgeAssignmentForm()
	skill_form = SkillCreatorForm()
	badge_upload_form = NewBadgeUploadForm()
	if request.method == 'GET' and current_user.is_admin == 1:
		open_reviews = db.session.query(Review, Emergency).join(Emergency, Emergency.id == Review.emergency_id).filter(Review.status == 'Open').all()
		pending_users = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.status=='Pending').all()
		all_users = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.status == 'Active').order_by(User.firstname).all()
		assigned_badges = db.engine.execute("SELECT u.id, u.firstname, u.lastname, GROUP_CONCAT(b.name, ', ') as badges FROM user u JOIN user_badge ub ON ub.user_id = u.id JOIN badge b ON b.id = ub.badge_id WHERE u.status = 'Active' GROUP BY u.id ORDER BY u.firstname")
		all_skills = db.session.query(Skill.name, Skill.category).order_by(Skill.category, Skill.name).all()
		return render_template('admin_landing.html', pending_users=pending_users, all_users=all_users, badge_form=badge_form, assigned_badges=assigned_badges, skill_form=skill_form, all_skills=all_skills, badge_upload_form=badge_upload_form, open_reviews=open_reviews)
	elif request.method == 'POST' and badge_form.submit_badge.data and current_user.is_admin == 1: 
		user_id = badge_form.user_name.data.id
		badge_id = badge_form.badge_name.data.id
		session['assigner_justify'] = badge_form.assigner_justify.data

		users_badges = db.engine.execute('SELECT user.id, user_badge.user_id, user_badge.badge_id FROM user JOIN user_badge ON user_badge.user_id = user.id WHERE user.id = {}'.format(user_id))
		users_badges_ids = []
		for badge in users_badges:
			users_badges_ids.append(badge.badge_id)

		# get list of assigned badges, create column that concats user_id and badge_id to create unique identifier
		badge_ids = db.engine.execute("SELECT user_id || badge_id as unique_code FROM user_badge")
		list_to_check = []
		for id in badge_ids:
			list_to_check.append(id[0])
		# check list against the values we're trying to save, and proceed if user doesn't already have that badge
		if (str(user_id) + str(badge_id)) not in list_to_check:
			return redirect(url_for('main.badge_assignment', user_id=user_id, badge_id=badge_id))
		else:
			flash('Cannot add badge - user already has it.', 'danger')
			return redirect(url_for('main.admin_landing'))
	elif request.method == 'POST' and skill_form.submit_skill.data and current_user.is_admin == 1: 
		new_skill = Skill(
			name = skill_form.name.data,
			category = skill_form.category.data
		)
		db.session.add(new_skill)
		db.session.commit()
		flash("New Skill Created.", "success")
		return redirect(url_for('main.admin_landing'))
	elif request.method == 'POST' and badge_upload_form.name.data and current_user.is_admin == 1:
		file = save_new_badge(badge_upload_form.file.data)
		badge = Badge(
			name = badge_upload_form.name.data, 
			badge_url = file
		)
		db.session.add(badge)
		db.session.commit()
		flash('New badge successfully created!', 'success')
		return redirect(url_for('main.admin_landing'))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
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
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
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
		flash('Badge successfully assigned.', 'success')
		return redirect(url_for('main.badge_assignment_sims_co', dis_id=dis_id))
	elif user_is_sims_co == False:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		return render_template('errors/403.html', list_of_admins=list_of_admins), 403

@main.route('/badge_assignment_simsco/<int:dis_id>', methods=['GET', 'POST'])
@login_required
def badge_assignment_sims_co(dis_id):
	badge_form = BadgeAssignmentViaSIMSCoForm()
	
	event_name = db.session.query(Emergency).filter(Emergency.id == dis_id).first()
	
	assigned_badges = db.engine.execute("SELECT u.id, u.firstname, u.lastname, GROUP_CONCAT(b.name, ', ') as badges FROM user u JOIN user_badge ub ON ub.user_id = u.id JOIN badge b ON b.id = ub.badge_id JOIN assignment a ON a.user_id = u.id JOIN emergency e ON e.id = a.emergency_id WHERE u.status = 'Active' AND e.id = {} AND a.role = 'Remote IM Support' GROUP BY u.id ORDER BY u.firstname".format(dis_id))
	
	assigned_members = db.session.query(Emergency, Assignment, User).join(Assignment, Assignment.emergency_id == Emergency.id).join(User, User.id == Assignment.user_id).filter(Emergency.id == dis_id).all()
	
	# generate list of user IDs of users listed as SIMS Remote Coordinators on emergency
	sims_co_ids = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == dis_id, Assignment.role == 'SIMS Remote Coordinator').all()
	
	user_is_sims_co = check_sims_co(dis_id)
	
	if request.method == 'GET' and user_is_sims_co == True:
		query = User.query.join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == dis_id, Assignment.role == 'Remote IM Support')
		badge_form.user_name.query = query
		return render_template('emergency_badge_assignment.html', title='Assign Badges', user_is_sims_co=user_is_sims_co, assigned_members=assigned_members, event_name=event_name, badge_form=badge_form, assigned_badges=assigned_badges)
	elif request.method == 'POST' and user_is_sims_co == True:
		user_id = badge_form.user_name.data.id
		badge_id = badge_form.badge_name.data.id
		# use flask session to pass 'assigner_justify' field data without passing through URL
		session['assigner_justify'] = badge_form.assigner_justify.data
		
		# get all badges assigned to the user which sims co is trying to assign
		users_badges = db.engine.execute('SELECT user.id, user_badge.user_id, user_badge.badge_id FROM user JOIN user_badge ON user_badge.user_id = user.id WHERE user.id = {}'.format(user_id))
		users_badges_ids = []
		for badge in users_badges:
			users_badges_ids.append(badge.badge_id)
		
		# check that user does not already have the badge
		if badge_id not in users_badges_ids:
			return redirect(url_for('main.badge_assignment_via_SIMSCO', user_id=user_id, badge_id=badge_id, assigner_id=current_user.id, dis_id=dis_id))
		else:
			flash('Cannot add badge - user already has it.', 'danger')
			return redirect(url_for('main.badge_assignment_sims_co', dis_id=dis_id))
	else:
		list_of_admins = db.session.query(User).filter(User.is_admin==1).all()
		print('User {} tried to assign a badge but was denied and given a 403 error.'.format(current_user.fullname))
		return render_template('errors/403.html', list_of_admins=list_of_admins, user_is_sims_co=user_is_sims_co, event_name=event_name, sims_co_ids=sims_co_ids), 403

@main.route('/staging') 
@login_required
def staging(): 
	active_emergencies = db.session.query(Emergency, NationalSociety, EmergencyType).join(NationalSociety, NationalSociety.ns_go_id == Emergency.emergency_location_id).join(EmergencyType, EmergencyType.emergency_type_go_id == Emergency.emergency_type_id).filter(Emergency.emergency_status == 'Active').all()
	
	return render_template('visualization.html', active_emergencies=active_emergencies)

@main.route('/learning')
@login_required
def learning():
	return render_template('learning.html')

@main.route('/resources')
@login_required
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

@main.route('/search/members', methods=['GET', 'POST'])
def search_members():
	member_form = MemberSearchForm()
	if request.method == 'GET':
		return render_template('search_members.html', member_form=member_form)
	if member_form.name.data or member_form.skills.data or member_form.languages.data: 
		name_search = member_form.name.data
		# convert name search to proper syntax for LIKE operator
		search_for_name = "'%{}%'".format(name_search)
		try:
			skill_search = member_form.skills.data.id
			skill_search_name = member_form.skills.data.name
		except:
			skill_search = 0
			skill_search_name = ''
		try:
			language_search = member_form.languages.data.id
			language_search_name = member_form.languages.data.name
		except:
			language_search = 0
			language_search_name = ''
		if name_search:
			name_query_converted = "SELECT user.id, firstname, lastname, email, job_title, slack_id FROM user WHERE firstname LIKE {} OR lastname LIKE {}".format(search_for_name, search_for_name)
			query_by_name = db.engine.execute(name_query_converted)
			result_by_name = [r._asdict() for r in query_by_name]
		else:
			query_by_name = db.engine.execute("SELECT user.id, firstname, lastname, email, job_title, slack_id FROM user WHERE firstname LIKE 'xxxx'")
			result_by_name = [r._asdict() for r in query_by_name]
	
		if skill_search:
			query_by_skill = db.engine.execute("SELECT user.id, firstname, lastname, email, job_title, slack_id FROM user JOIN user_skill ON user_skill.user_id = user.id JOIN skill ON skill.id = user_skill.skill_id WHERE skill_id = :skill", {'skill': skill_search})
			result_by_skill = [r._asdict() for r in query_by_skill]
		else:
			query_by_skill = db.engine.execute("SELECT user.id, firstname, lastname, email, job_title, slack_id FROM user JOIN user_skill ON user_skill.user_id = user.id JOIN skill ON skill.id = user_skill.skill_id WHERE skill_id = 0")
			result_by_skill = [r._asdict() for r in query_by_skill]
		if language_search:
			query_by_language = db.engine.execute("SELECT user.id, firstname, lastname, email, job_title, slack_id FROM user JOIN user_language ON user_language.user_id = user.id JOIN language ON language.id = user_language.language_id WHERE language_id = :language", {'language': language_search})
			result_by_language = [r._asdict() for r in query_by_language]
		else:
			query_by_language = db.engine.execute("SELECT user.id, firstname, lastname, email, job_title, slack_id FROM user JOIN user_language ON user_language.user_id = user.id JOIN language ON language.id = user_language.language_id WHERE language_id = 0")
			result_by_language = [r._asdict() for r in query_by_language]
		
		# merge all queries into one list
		master_search = {x['id']:x for x in result_by_language + result_by_skill + result_by_name}.values()
		return render_template('search_members_results.html', master_search=master_search)

@main.route('/search/emergencies', methods=['GET', 'POST'])
@login_required
def search_emergencies():
	emergency_form = EmergencySearchForm()
	if request.method == 'GET':
		return render_template('search_emergencies.html', emergency_form=emergency_form)
	if emergency_form.name.data or emergency_form.status.data or emergency_form.type.data or emergency_form.location.data or emergency_form.glide.data: 
		emergency_search = emergency_form.name.data
		# convert name search to proper syntax for LIKE operator
		search_for_emergency = "'%{}%'".format(emergency_search)
		
		glide_search = emergency_form.glide.data
		# convert name search to proper syntax for LIKE operator
		search_for_glide = "'%{}%'".format(glide_search)
		try:
			status_search = emergency_form.status.data
		except:
			status_search = ''
		try:
			type_search = emergency_form.type.data.emergency_type_go_id
			type_search_name = emergency_form.type.data.emergency_type_name
		except:
			type_search = 0
			type_search_name = ''
		try:
			location_search = emergency_form.location.data.id
			location_search_name = emergency_form.location.data.country_name
		except:
			location_search = 0
			location_search_name = ''
			
		if emergency_search:
			emergency_query_converted = "SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE emergency_name LIKE {}".format(search_for_emergency)
			query_by_name = db.engine.execute(emergency_query_converted)
			result_by_name = [r._asdict() for r in query_by_name]
		else:
			query_by_name = db.engine.execute("SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE emergency_name LIKE 'xxxx'")
			result_by_name = [r._asdict() for r in query_by_name]

		if status_search:
			status_query_converted = "SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE emergency_status = '{}'".format(status_search)
			query_by_status = db.engine.execute(status_query_converted)
			result_by_status = [r._asdict() for r in query_by_status]
		else:
			query_by_status = db.engine.execute("SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE e.emergency_status LIKE 'xxxx'")
			result_by_status = [r._asdict() for r in query_by_status]

		if glide_search:
			glide_query_converted = "SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE e.emergency_glide LIKE {}".format(search_for_glide)
			query_by_glide = db.engine.execute(glide_query_converted)
			result_by_glide = [r._asdict() for r in query_by_glide]
		else:
			query_by_glide = db.engine.execute("SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE e.emergency_glide LIKE 'xxxx'")
			result_by_glide = [r._asdict() for r in query_by_glide]
			
		if type_search:
			type_query_converted = "SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE e.emergency_type_id = {}".format(type_search)
			query_by_type = db.engine.execute(type_query_converted)
			result_by_type = [r._asdict() for r in query_by_type]
		else:
			query_by_type =db.engine.execute("SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE e.emergency_type_id = 0")
			result_by_type = [r._asdict() for r in query_by_type]
			
		if location_search:
			location_query_converted = "SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE n.country_name = '{}'".format(location_search_name)
			query_by_location = db.engine.execute(location_query_converted)
			result_by_location = [r._asdict() for r in query_by_location]
		else:
			query_by_location =db.engine.execute("SELECT e.id, e.emergency_name, e.emergency_status, e.emergency_glide, n.country_name, t.emergency_type_name FROM emergency e JOIN nationalsociety n ON n.ns_go_id = e.emergency_location_id JOIN emergencytype t ON t.emergency_type_go_id = e.emergency_type_id WHERE n.country_name = 'xxxx'")
			result_by_location = [r._asdict() for r in query_by_location]
		
		# merge all queries into one list and remove duplicates
		master_search = {x['id']:x for x in result_by_name + result_by_glide + result_by_status + result_by_location + result_by_type}.values()
		
		return render_template('search_emergencies_results.html', master_search=master_search)

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
	active_assignments = db.session.query(Assignment, User, Emergency, NationalSociety).join(User, User.id==Assignment.user_id).join(Emergency, Emergency.id==Assignment.emergency_id).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(Assignment.assignment_status=='Active', Assignment.end_date>todays_date).order_by(Emergency.emergency_name, Assignment.end_date).all()

	most_recent_emergencies = db.session.query(Emergency).order_by(Emergency.created_at.desc()).limit(7).all()
	most_recent_members = db.session.query(User, NationalSociety).join(NationalSociety, NationalSociety.ns_go_id == User.ns_id).filter(User.status == 'Active').order_by(User.created_at.desc()).limit(7).all()
	
	return render_template('dashboard.html', active_assignments=active_assignments, count_active_assignments=count_active_assignments, most_recent_emergencies=most_recent_emergencies, labels_for_assignment=labels_for_assignment, values_for_assignment=values_for_assignment, labels_for_product=labels_for_product, values_for_product=values_for_product, most_recent_members=most_recent_members, pending_user_check=pending_user_check, active_emergencies=active_emergencies, count_active_emergencies=count_active_emergencies)
	
	