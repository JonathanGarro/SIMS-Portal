import boto3
from flask import url_for, current_app, flash, redirect
from PIL import Image
from flask_mail import Message
from SIMS_Portal import db
from SIMS_Portal.models import User, Assignment, Emergency
from slack_sdk import WebClient
import os
import secrets
import tempfile
import requests
import http.client, urllib.parse
import json
import logging

def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	filename, file_ext = os.path.splitext(form_picture.filename)
	picture_filename = random_hex + file_ext
	picture_path = f"pictures/{picture_filename}"

	with tempfile.NamedTemporaryFile(suffix=f".{file_ext}") as resized_image_file:
		output_size = (400, 400)
		resized_image = Image.open(form_picture)
		resized_image.thumbnail(output_size)
		resized_image.save(resized_image_file.name)
		s3 = boto3.client("s3")
		s3.upload_file(resized_image_file.name, current_app.config["UPLOAD_BUCKET"], picture_path)

	return picture_path

def send_reset_slack(user):
	token = user.get_reset_token()
	reset_link = url_for("users.reset_token", token=token, _external=True)
	msg = "Looks like you requested a password reset. *If you did not request this, simply ignore this message.* Otherwise, follow the directions on the page <{}|linked here>.".format(reset_link)
	send_slack_dm(msg, user.slack_id)

# send slack alert when new user signs up
def new_user_slack_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'C046A8T9ZJB',
			text = message
		)
	except:
		pass

# send slack alert when new surge alert is released and saved to the database
def new_surge_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'CDUMNN3J8',
			text = message
		)
	except:
		pass

# search for remote coordinators currently active
def rem_cos_search():
	with app.app_context():
		active_SIMS_cos = db.session.query(Assignment, User, Emergency).join(User, User.id == Assignment.user_id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.emergency_status == 'Active', Assignment.role == 'SIMS Remote Coordinator').all()

# general purpose DM messaging bot
def send_slack_dm(message, user):
	slack_token = current_app.config['SIMS_PORTAL_SLACK_BOT']
	data = {
			'token': slack_token,
			'channel': user,    # User's Slack ID
			'as_user': True,
			'text': message
	}
	try:
		requests.post(url='https://slack.com/api/chat.postMessage', data=data)
	except Exception as e:
		current_app.logger.error('send_slack_dm failed: {}'.format(e))
	
def check_valid_slack_ids(id):
	client = WebClient(token=current_app.config['SIMS_PORTAL_SLACK_BOT'])
	
	users_store = []
	
	def save_users_ids(users_array):
		for user in users_array:
			users_store.append(user["id"])
			
	try:
		result = client.users_list()
		save_users_ids(result["members"])
	except Exception as e:
		current_app.logger.error('check_valid_slack_ids failed: {}'.format(e))	
		
	if id in users_store:
		return True
	else:
		return False

def search_location(query):
	position_stack_token = current_app.config['POSITION_STACK_TOKEN']

	conn = http.client.HTTPConnection('api.positionstack.com')
	
	params = urllib.parse.urlencode({
		'access_key': position_stack_token,
		'query': query,
		'limit': 1,
		'timezone_module': 1,
		})
	
	conn.request('GET', '/v1/forward?{}'.format(params))
	
	res = conn.getresponse()
	data = res.read()
	decoded_data = (data.decode('utf-8'))
	
	response = json.loads(decoded_data)
	lat = (response['data'][0]['latitude'])
	long = (response['data'][0]['longitude'])
	place = (response['data'][0]['label'])
	time_zone = (response['data'][0]['timezone_module']['name'])
	offset = (response['data'][0]['timezone_module']['offset_sec']) / 3600

	return lat, long, place, time_zone, offset

	
def update_member_locations():
	member_coordinates = db.session.query(User).all()
	
	list_of_location_dicts = []
	for member in member_coordinates:
		if member.coordinates:
			locations_dict = {}
			strip_brackets = member.coordinates.replace('[', '').replace(']', '').split(", ")
			locations_dict["latitude"] = float(strip_brackets[0])
			locations_dict["longitude"] = float(strip_brackets[1])
			list_of_location_dicts.append(locations_dict)
			
	json_output = json.dumps(list_of_location_dicts)

	json_file_path = "SIMS_Portal/static/data/locations.json"
	if os.path.exists(json_file_path):
		os.remove(json_file_path)
	with open(json_file_path, "w") as outfile:
		outfile.write(json_output)
