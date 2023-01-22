from flask import url_for, current_app, jsonify
import logging
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from SIMS_Portal.models import Emergency, NationalSociety, User, Assignment, user_badge
from SIMS_Portal import db
from flask_login import current_user

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
			logger.error("Error fetching conversations: {}".format(e))
			
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
	file_path = os.path.join(current_app.root_path, 'static/assets/img/badges', file_merged)
	file_path_extension = '/static/assets/img/badges/' + file_merged
	file.save(file_path)
	
	return file_path_extension

def auto_badge_assigner_big_wig():
	"""
	Checks for users that have 5 or more remote support assignments and assigns the Big Wig badge if they don't already have it.
	"""
	remote_assignment_counts = db.engine.execute("SELECT user.id as user_id, firstname, lastname, count(assignment.id) as count_assignments FROM user JOIN assignment ON assignment.user_id = user.id WHERE assignment.assignment_status <> 'Removed' GROUP BY user.id")
	existing_big_wig_badges = db.engine.execute("SELECT user_id, badge_id FROM user_badge WHERE badge_id = 20")
	
	list_user_ids_with_big_wig = []
	for user in existing_big_wig_badges:
		list_user_ids_with_big_wig.append(user.user_id)	
	
	for user in remote_assignment_counts:
		if user.count_assignments >= 5 and user.user_id not in list_user_ids_with_big_wig:
			new_badge = "INSERT INTO user_badge (user_id, badge_id, assigner_id, assigner_justify) VALUES ({}, 20, 0, 'Badge automatically assigned by SIMS Portal bot.')".format(user.user_id)
			db.session.execute(new_badge)
	db.session.commit()