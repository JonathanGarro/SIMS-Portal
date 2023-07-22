import boto3
from flask import url_for, current_app, flash, redirect
from PIL import Image
from flask_mail import Message
from SIMS_Portal import db, cache
from SIMS_Portal.models import User, NationalSociety, user_language, Language, Assignment, user_profile, Profile, user_skill, Skill, Emergency
from slack_sdk import WebClient
import os
import secrets
import tempfile
import requests
import http.client, urllib.parse
import json
import logging
from io import BytesIO

def save_picture(form_picture):
	random_hex = secrets.token_hex(8)
	filename, file_ext = os.path.splitext(form_picture.filename)
	if file_ext.lower() == '.jpeg':
		file_ext = '.jpg'
	picture_filename = random_hex + file_ext
	picture_path = f"pictures/{picture_filename}"

	with tempfile.NamedTemporaryFile(suffix=file_ext) as resized_image_file:
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

def new_user_slack_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'C046A8T9ZJB',
			text = message
		)
	except:
		pass

def new_surge_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'CDUMNN3J8',
			text = message
		)
	except:
		pass

def rem_cos_search():
	with app.app_context():
		active_SIMS_cos = db.session.query(Assignment, User, Emergency).join(User, User.id == Assignment.user_id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.emergency_status == 'Active', Assignment.role == 'SIMS Remote Coordinator').all()

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

@cache.cached(timeout=120)
def get_valid_slack_ids():
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
	
	return users_store

def check_valid_slack_ids(id):
	users_store = get_valid_slack_ids()
		
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
		
def download_profile_photo(slack_id):
	url = 'https://slack.com/api/users.profile.get'
	
	access_token = current_app.config['SIMS_PORTAL_SLACK_BOT']
	
	headers = {
		'Authorization': f'Bearer {access_token}'
	}

	params = {
		'user': slack_id
	}

	response = requests.get(url, headers=headers, params=params)

	if response.status_code == 200:
		data = response.json()

		if 'profile' in data and 'image_original' in data['profile']:
			profile_photo_url = data['profile']['image_original']

			photo_response = requests.get(profile_photo_url)
			if photo_response.status_code == 200:
				picture_path = save_picture_from_slack(photo_response.content)
				db.session.query(User).filter(User.slack_id == slack_id).update({'image_file':picture_path})
				db.session.commit()
				
				current_app.logger.info(f"Slack profile photo saved as '{picture_path}' successfully.")
				return picture_path
			else:
				current_app.logger.error("Failed to download profile photo for user with Slack ID {}.".format(slack_id))
		else:
			current_app.logger.error("Profile photo not found for user with Slack ID {}".format(slack_id))
	else:
		current_app.logger.error("Slack API call failed on download_profile_photo function. Check access token and user ID.")
		
def save_picture_from_slack(picture):
	random_hex = secrets.token_hex(8)
	picture_path = f"pictures/{random_hex}.jpg"
	
	output_size = (400, 400)
	
	try:
		image = Image.open(BytesIO(picture))
	except Exception as e:
		current_app.logger.error("Error opening image: {}".format(e))
		return None
	
	image.thumbnail(output_size)
	
	s3 = boto3.client("s3")
	with BytesIO() as image_stream:
		image.save(image_stream, format='JPEG')
		image_stream.seek(0)
		s3.upload_fileobj(image_stream, current_app.config["UPLOAD_BUCKET"], picture_path)
	
	return picture_path