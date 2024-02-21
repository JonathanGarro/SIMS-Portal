from flask import url_for, current_app, jsonify
import logging
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from SIMS_Portal.models import Emergency, NationalSociety, User, Assignment, user_badge, user_skill, user_language, user_profile, Skill, Language, Profile, Portfolio
from SIMS_Portal import db
from flask_login import current_user
import boto3
from sqlalchemy import func, String, distinct, desc, asc, select, text
from sqlalchemy.orm import aliased
import requests

def send_error_message(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'C046A8T9ZJB',
			text = message
		)
	except Exception as e:
		current_app.logger.error('new_acronym_alert Slack message failed: {}'.format(e))

def user_info_by_ns(ns_id):
	query_text = text(
		"""
		SELECT u.id, u.firstname, u.lastname, u.status,
			MAX(CASE WHEN up.profile_id = 1 THEN up.tier END) AS geospatial,
			MAX(CASE WHEN up.profile_id = 2 THEN up.tier END) AS webviz,
			MAX(CASE WHEN up.profile_id = 3 THEN up.tier END) AS infodes,
			MAX(CASE WHEN up.profile_id = 4 THEN up.tier END) AS datatrans,
			MAX(CASE WHEN up.profile_id = 5 THEN up.tier END) AS datacollect,
			MAX(CASE WHEN up.profile_id = 6 THEN up.tier END) AS remoteco
		FROM public.nationalsociety ns
		JOIN public.user u ON u.ns_id = ns.ns_go_id
		LEFT JOIN public.user_profile up ON up.user_id = u.id
		WHERE ns.ns_go_id = :ns_id AND u.status != 'Other'
		GROUP BY u.id, u.firstname, u.lastname
		ORDER BY u.firstname
		"""
	)
	
	results = db.engine.execute(query_text, ns_id=ns_id)
	processed_results = [dict(row) for row in results]
	
	return processed_results

def get_ns_list():
	ns_query = select([distinct(NationalSociety.ns_go_id), NationalSociety.ns_name, NationalSociety.country_name]) \
		.join(User, NationalSociety.ns_go_id == User.ns_id) \
		.filter(~NationalSociety.ns_name.like('%IFRC%')) \
		.order_by(asc(NationalSociety.country_name))
	
	ns_list = db.session.execute(ns_query).fetchall()
	
	return ns_list

def heartbeats(name, url):
	"""
	fires off GET requests to betterstack/logtail to serve as heartbeats for cron job monitoring
	"""
	response = requests.get(url)
	
	if response.status_code == 200:
		current_app.logger.info("heartbeat GET request successfully ran for {}".format(name))
		return "Request successful"
	else:
		current_app.logger.error("heartbeat GET request failed for {}".format(name))
		return "Request failed"

def fetch_slack_channels():
	token = current_app.config['SIMS_PORTAL_SLACK_BOT']
	client = WebClient(token=token)
	logger = logging.getLogger(__name__)
	
	conversations_store = {}
	
	def fetch_conversations():
		try:
			result = client.conversations_list()
			save_conversations(result["channels"])
			
		except SlackApiError as e:
			current_app.logger.error("Error fetching conversations: {}".format(e))
			
	# put conversations into the JavaScript object
	def save_conversations(conversations):
		conversation_id = ""
		for conversation in conversations:
			# key conversation info on its unique ID
			conversation_id = conversation["id"]
			# Store the entire conversation object
			conversations_store[conversation_id] = conversation
	
	fetch_conversations()
	
	dicts = [value for value in conversations_store.values()]
	
	output = []
	for d in dicts:
		temp_dict = {}
		if d['is_private'] == False and d['is_archived'] == False:
			temp_dict['id'] = d['id']
			temp_dict['channel_name'] = d['name']
			temp_dict['count_members'] = d['num_members']
			if d['purpose']:
				temp_dict['purpose'] = d['purpose']['value']
				output.append(temp_dict)
	return output

def generate_new_response_map():
	"""Gets full list of countries where SIMS has responded, and writes results to a CSV stored in the static folder."""
	
	all_emergencies = db.engine.execute("SELECT iso3, COUNT(*) as count FROM emergency JOIN nationalsociety WHERE emergency.emergency_location_id = nationalsociety.ns_go_id AND emergency_status <> 'Removed' GROUP BY iso3")
		
	header_row = ['iso3', 'count']
	with open('SIMS_Portal/static/data/emergencies_viz.csv', 'w', newline='') as f:
		f.write(','.join(header_row) + '\n')
		writer = csv.writer(f)
		for x in all_emergencies:
			writer.writerow([x.iso3, x.count])

def check_sims_co(emergency_id):
	"""
	Takes in an emergency id record and verifies that the current user is listed as a SIMS Remove Coordinator for that record in order to allow additional permission sets.
	"""
	sims_co_ids = db.session.query(User, Assignment, Emergency).join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.id == emergency_id, Assignment.role == 'SIMS Remote Coordinator').all()
	sims_co_list = []
	for coordinator in sims_co_ids:
		sims_co_list.append(coordinator.User.id)
	if current_user.id in sims_co_list:
		user_is_sims_co = True
	else:
		user_is_sims_co = False
		
	return user_is_sims_co

def save_new_badge(file, name):
	filename, file_ext = os.path.splitext(file.filename)
	filename = name.title().replace(' ','-')
	file_merged = filename + file_ext
	file_path = f"badges/{file_merged}"	

	s3 = boto3.client("s3")
	s3.upload_fileobj(file, current_app.config["UPLOAD_BUCKET"], file_path)

	return file_path

def auto_badge_assigner_maiden_voyage():
	"""
	Checks for users that have at least one remote support assignment and assigns the Maiden Voyage badge if they don't already have it.
	"""
	current_app.logger.info('Maiden Voyage Auto-Assign Ran')
	try:
		remote_assignment_counts = db.session.query(
			User.id.label('user_id'),
			User.firstname,
			User.lastname,
			func.count(Assignment.id).label('count_assignments')
		).join(
			Assignment, Assignment.user_id == User.id
		).filter(
			Assignment.assignment_status != 'Removed'
		).group_by(
			User.id
		).all()
		
		existing_maiden_voyage_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 3")
		
		list_user_ids_with_maiden_voyage = []
		for user in existing_maiden_voyage_badges:
			list_user_ids_with_maiden_voyage.append(user.user_id)	
		
		for user in remote_assignment_counts:
			if user.count_assignments >= 1 and user.user_id not in list_user_ids_with_maiden_voyage:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 3, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.user_id)
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Maiden Voyage Auto-Assign Failed: {}'.format(e))
	
def auto_badge_assigner_big_wig():
	"""
	Checks for users that have 5 or more remote support assignments and assigns the Big Wig badge if they don't already have it.
	"""
	current_app.logger.info('Big Wig Auto-Assign Ran')
	try:
		remote_assignment_counts = db.session.query(
			User.id.label('user_id'),
			User.firstname,
			User.lastname,
			func.count(Assignment.id).label('count_assignments')
		).join(
			Assignment, Assignment.user_id == User.id
		).filter(
			Assignment.assignment_status != 'Removed'
		).group_by(
			User.id
		).all()
		
		existing_big_wig_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 20")
	
		list_user_ids_with_big_wig = []
		for user in existing_big_wig_badges:
			list_user_ids_with_big_wig.append(user.user_id)	
		
		for user in remote_assignment_counts:
			if user.count_assignments >= 5 and user.user_id not in list_user_ids_with_big_wig:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 20, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.user_id)
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Big Wig Auto-Assign Failed: {}'.format(e))

def auto_badge_assigner_self_promoter():
	"""
	Checks for users that have at least 1 skill shared on their profile and assigns the Self Promoter badge if they don't already have it.
	"""
	current_app.logger.info('Self Promoter Auto-Assign Ran')
	try:
		users_with_skills = db.session.query(
			User.id.label('user_id'),
			User.firstname,
			User.lastname,
			func.string_agg(Skill.name, ', ').label('skill_names'),
			func.string_agg(func.cast(Skill.id, String), ', ').label('skill_ids')
		).join(
			user_skill,
			User.id == user_skill.c.user_id
		).join(
			Skill,
			Skill.id == user_skill.c.skill_id
		).group_by(
			User.id
		).all()
		
		# users_with_skills = db.engine.execute("SELECT user.id AS user_id, firstname, lastname, GROUP_CONCAT(skill.name, ', ') as skill_names, GROUP_CONCAT(skill.id, ', ') as skill_ids FROM user JOIN user_skill ON user.id = user_skill.user_id JOIN skill ON skill.id = user_skill.skill_id GROUP BY user.id")
		existing_self_promoter_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 4")
		
		list_user_ids_with_self_promoter = []
		for user in existing_self_promoter_badges:
			list_user_ids_with_self_promoter.append(user.user_id)
			
		for user in users_with_skills:
			if user.user_id not in list_user_ids_with_self_promoter:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 4, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.user_id)
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Self Promoter Auto-Assign Failed: {}'.format(e))

def auto_badge_assigner_polyglot():
	"""
	Checks for users that have at least 2 languages listed on their profile and assigns the Polyglot badge if they don't already have it.
	"""
	current_app.logger.info('Polyglot Auto-Assign Ran')
	try:
		users_with_languages = db.session.query(User.id.label('user_id'), User.firstname, User.lastname, func.string_agg(Language.id.cast(String), ', ').label('languages')).join(user_language, User.id == user_language.c.user_id).join(Language, Language.id == user_language.c.language_id).group_by(User.id).all()
		
		# users_with_languages = db.engine.execute("SELECT user.id AS user_id, firstname, lastname, GROUP_CONCAT(language.id, ', ') as languages FROM user JOIN user_language ON user_language.user_id = user.id JOIN language ON language.id = user_language.language_id GROUP BY user_id")
		existing_polyglot_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 1")
		
		list_users_with_languages = []
		for user in users_with_languages:
			temp_dict = {}
			temp_dict['user_id'] = user.user_id
			list_langs = []
			for lang in user['languages'].split(","):
				list_langs.append(int(lang))
			temp_dict['langs'] = list_langs
			for x in temp_dict['langs']:
				temp_dict['lang_count'] = len(temp_dict['langs'])
			list_users_with_languages.append(temp_dict)
		
		list_user_ids_with_polyglot = []
		for user in existing_polyglot_badges:
			list_user_ids_with_polyglot.append(user.user_id)
		
		for user in list_users_with_languages:
			if user['user_id'] not in list_user_ids_with_polyglot and user['lang_count'] > 1:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 1, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user['user_id'])
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Polyglot Auto-Assign Failed: {}'.format(e))
	
def auto_badge_assigner_autobiographer():
	"""
	Checks for users that have at 500+ characters in their bio and assigns the Autobiographer badge if they don't already have it.
	"""
	current_app.logger.info('Biographer Auto-Assign Ran')
	try:
		all_users = db.session.query(User).filter(User.bio != '').all()
		existing_autobiographer_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 21")
		
		list_user_ids_with_autobiographer = []
		for user in existing_autobiographer_badges:
			list_user_ids_with_autobiographer.append(user.user_id)
		
		for user in all_users:
			if user.id not in list_user_ids_with_autobiographer and len(user.bio) > 500:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 21, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.id)
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Autobiographer Auto-Assign Failed: {}'.format(e))

def auto_badge_assigner_jack_of_all_trades():
	"""
	Checks for users that have at 500+ characters in their bio and assigns the Autobiographer badge if they don't already have it.
	"""
	current_app.logger.info('Jack of All Trades Auto-Assign Ran')
	try:
		users_with_profiles = db.session.query(
			func.concat(User.firstname, ' ', User.lastname).label('name'),
			User.id.label('user_id'),
			func.string_agg(Profile.name, ', ').label('profiles')
		).join(user_profile, User.id == user_profile.c.user_id).join(
			Profile, Profile.id == user_profile.c.profile_id
		).group_by(User.id, func.concat(User.firstname, ' ', User.lastname)).all()
		
		existing_jack_of_all_trades_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 22")
		
		list_users_with_profiles = []
		for user in users_with_profiles:
			temp_dict = {}
			temp_dict['user_id'] = user.user_id
			list_profs = []
			for prof in user['profiles'].split(","):
				list_profs.append(int(prof))
			temp_dict['profs'] = list_profs
			for x in temp_dict['profs']:
				temp_dict['prof_count'] = len(temp_dict['profs'])
			list_users_with_profiles.append(temp_dict)
		
		list_user_ids_with_jack_of_all_trades = []
		for user in existing_jack_of_all_trades_badges:
			list_user_ids_with_jack_of_all_trades.append(user.user_id)
		
		for user in list_users_with_profiles:
			if user['user_id'] not in list_user_ids_with_jack_of_all_trades and user['prof_count'] > 5:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 22, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user['user_id'])
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Jack of All Trades Auto-Assign Failed: {}'.format(e))

def auto_badge_assigner_edward_tufte():
	"""
	Checks for users that have at 5+ public infographics posted to the Portal and assigns the Edward Tufte badge if they don't already have it.
	"""
	try:
		current_app.logger.info('Edward Tufte Auto-Assign Ran')
		existing_edward_tufte_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 31")
		
		list_user_ids_with_edward_tufte = []
		for user in existing_edward_tufte_badges:
			list_user_ids_with_edward_tufte.append(user.user_id)
			
		users_eligible_for_edward_tufte = db.session.query(User.id, User.firstname, User.lastname, Portfolio.type, func.count().label('total')).join(Portfolio, Portfolio.creator_id == User.id).filter(Portfolio.product_status == 'Approved').filter(Portfolio.type == 'Infographic').group_by(User.id, Portfolio.type).having(func.count() >= 5).all()
		
		# users_eligible_for_edward_tufte = db.engine.execute("SELECT user.id, firstname, lastname, type, count(*) as count FROM user JOIN portfolio ON portfolio.creator_id = user.id WHERE product_status = 'Approved' AND type = 'Infographic' GROUP BY user.id HAVING count >= 5")
		
		list_users_eligible_for_edward_tufte = []
		for user in users_eligible_for_edward_tufte:
			if user.id not in list_user_ids_with_edward_tufte:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 31, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.id)
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Edward Tufte Auto-Assign Failed: {}'.format(e))

def auto_badge_assigner_world_traveler():
	"""
	Checks for users that have assignments tagged to emergencies in five distinct countries and assigns the World Traveler badge if they don't already have it.
	"""
	try:
		current_app.logger.info('World Traveler Auto-Assign Ran')
		existing_world_traveler_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 5")
		
		list_user_ids_with_world_traveler = []
		for user in existing_world_traveler_badges:
			list_user_ids_with_world_traveler.append(user.user_id)
	
		users_eligible_for_world_traveler = db.session.query(User.id, User.firstname, User.lastname, func.count(func.distinct(NationalSociety.country_name)).label('count_countries')).join(Assignment, Assignment.user_id == User.id).join(Emergency, Emergency.id == Assignment.emergency_id).join(NationalSociety, NationalSociety.id == Emergency.id).group_by(User.id, User.firstname, User.lastname).having(func.count(func.distinct(NationalSociety.country_name)) > 4).all()
		
		# users_eligible_for_world_traveler = db.engine.execute("SELECT user.id, firstname, lastname, count(distinct country_name) as count_countries FROM User JOIN Assignment ON Assignment.user_id = User.id JOIN Emergency ON Emergency.id = Assignment.emergency_id JOIN nationalsociety ON nationalsociety.ns_go_id = emergency.emergency_location_id GROUP BY user.id HAVING count_countries > 4")
	
		for user in users_eligible_for_world_traveler:
			if user.id not in list_user_ids_with_world_traveler:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 5, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.id)
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('World Traveler Auto-Assign Failed: {}'.format(e))
		
def auto_badge_assigner_old_salt():
	"""
	Checks for users that have 3 assignments with SIMS Remote Coordinator as the role and assigns the Old Salt badge if they don't already have it.
	"""
	try:
		current_app.logger.info('Old Salt Auto-Assign Ran')
		existing_old_salt_badges = db.engine.execute("SELECT user_id, badge_id FROM public.user_badge WHERE badge_id = 25")
		
		list_user_ids_with_old_salt = []
		for user in existing_old_salt_badges:
			list_user_ids_with_old_salt.append(user.user_id)
		
		users_eligible_for_old_salt = db.session.query(Assignment.id, User.id, User.firstname, User.lastname, func.count().label('count')).join(User, User.id == Assignment.user_id).filter(Assignment.role == 'SIMS Remote Coordinator').group_by(Assignment.id, User.id, User.firstname, User.lastname).having(func.count() > 2).all()
		
		# users_eligible_for_old_salt = db.engine.execute("SELECT assignment.id, user.id, firstname, lastname, count(*) as count FROM assignment JOIN user ON user.id = assignment.user_id WHERE role = 'SIMS Remote Coordinator' GROUP BY user.id HAVING count > 2")
		
		for user in users_eligible_for_old_salt:
			if user.id not in list_user_ids_with_old_salt:
				new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 25, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.id)
				db.session.execute(new_badge)
		db.session.commit()
	except Exception as e:
		current_app.logger.error('Old Salt Auto-Assign Failed: {}'.format(e))