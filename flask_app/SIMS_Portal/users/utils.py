import boto3
from flask import url_for, current_app, flash, redirect, session
from PIL import Image
from flask_mail import Message
from SIMS_Portal import db, cache
from SIMS_Portal.models import User, NationalSociety, user_language, Language, Assignment, user_profile, Profile, user_skill, Skill, Emergency, Log
from slack_sdk import WebClient
from datetime import datetime, timedelta
import os
import secrets
import tempfile
import requests
import http.client, urllib.parse
import json
import logging
from io import BytesIO
from sqlalchemy import select, func, Column, Integer, String, DateTime, outerjoin
from sqlalchemy.orm import aliased


def save_picture(form_picture):
	"""
	Saves a picture uploaded via a form to an S3 bucket after processing and resizing it.
	
	Args:
		form_picture (FileStorage): The file object representing the uploaded picture.
	
	Returns:
		str: The path to the saved picture in the S3 bucket.
	
	This function performs the following steps:
		1. Generates a random hex string to create a unique filename for the picture.
		2. Extracts the file extension from the uploaded picture and normalizes it to '.jpg' if it's '.jpeg'.
		3. Constructs the path where the picture will be saved within the S3 bucket.
		4. Resizes the uploaded picture to a maximum size of 400x400 pixels.
		5. Saves the resized picture to a temporary file.
		6. Uploads the resized picture to the specified S3 bucket using the `boto3` library.
		7. Returns the path to the saved picture in the S3 bucket.
	
	Notes:
		- The function uses the `secrets` library to generate a random filename for security.
		- The image is resized using the `Pillow` library to ensure it meets the required dimensions.
		- A temporary file is used to handle the resized image before uploading it to S3.
		- The AWS S3 client is created using the `boto3` library.
	
	Example:
		picture_path = save_picture(request.files['picture'])
		print(f"Picture saved to: {picture_path}")
	"""
	
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
	except Exception as e:
		current_app.logger.error('new_user_slack_alert Slack message failed: {}'.format(e))

def new_surge_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'CDUMNN3J8',
			text = message
		)
	except Exception as e:
		current_app.logger.error('new_surge_alert Slack message failed: {}'.format(e))

def test_surge_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'C046A8T9ZJB',
			text = message
		)
	except Exception as e:
		current_app.logger.error('new_surge_alert Slack message failed: {}'.format(e))

def new_acronym_alert(message):
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	try:
		result = client.chat_postMessage(
			channel = 'C046A8T9ZJB',
			text = message
		)
	except Exception as e:
		current_app.logger.error('new_acronym_alert Slack message failed: {}'.format(e))

def rem_cos_search():
	with app.app_context():
		active_SIMS_cos = db.session.query(Assignment, User, Emergency).join(User, User.id == Assignment.user_id).join(Emergency, Emergency.id == Assignment.emergency_id).filter(Emergency.emergency_status == 'Active', Assignment.role == 'SIMS Remote Coordinator').all()

def send_slack_dm(message, user):
	"""
	Sends a direct message (DM) to a Slack user.
	
	Args:
		message (str): The message to be sent.
		user (int): The Slack user ID or channel ID where the message will be sent.
	
	This function performs the following steps:
		1. Retrieves the Slack bot token from the Flask application configuration.
		2. Constructs the data payload including the token, target user ID, message content, and 'as_user' flag.
		3. Sends a POST request to the Slack API endpoint for sending messages.
		4. Logs any errors that occur during the message sending process.
	
	Notes:
		- The function assumes it is running within the SIMS Portal's Flask application context and uses `current_app` 
		  for accessing configuration and logging.
		- It utilizes the `requests` library to make HTTP requests to the Slack API.
		- The message is sent as the bot user (`as_user=True`) to ensure consistent behavior.
	
	Example:
		send_slack_dm("Hello there!", "U12345678")
		This will send the message "Hello there!" to the Slack user with the ID "U12345678".
	"""
	
	log_message = f"[INFO] send_slack_dm() triggered for user {user}."
	new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
	db.session.add(new_log)
	db.session.commit()
	
	slack_token = current_app.config['SIMS_PORTAL_SLACK_BOT']
	data = {
			'token': slack_token,
			'channel': user,
			'as_user': True,
			'text': message
	}
	try:
		response = requests.post(url='https://slack.com/api/chat.postMessage', data=data)
		response_data = response.json()
		if not response_data.get('ok'):
			log_message = f"[ERROR] send_slack_dm() failed: {response_data.get('error')}"
			new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
			db.session.add(new_log)
			db.session.commit()
			return False
		return True
	except Exception as e:
		log_message = f"[ERROR] send_slack_dm() failed: {e}."
		new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
		db.session.add(new_log)
		db.session.commit()
		return False


@cache.cached(timeout=120)
def get_valid_slack_ids():
	"""
	Retrieves a list of valid Slack user IDs using the Slack WebClient API.
	
	Returns:
		list: A list of valid Slack user IDs.
	
	This function performs the following steps:
		1. Creates a Slack WebClient instance using the token retrieved from the Flask application configuration.
		2. Defines an empty list to store the Slack user IDs.
		3. Defines an inner function `save_users_ids` to extract and save user IDs from the response.
		4. Attempts to fetch the list of users from the Slack workspace using the WebClient.
		5. Calls the `save_users_ids` function to extract and store the user IDs from the response.
		6. Logs any errors that occur during the retrieval process.
		7. Returns the list of Slack user IDs.
	
	Notes:
		- The function assumes it is running within the SIMS Portal's Flask application context and uses `current_app` 
		  for accessing configuration and logging.
		- Slack WebClient is used to interact with the Slack API to retrieve user information.
		- The function caches the result for 120 seconds using the `@cache.cached` decorator. This is to avoid rate limits.
	
	Example:
		slack_ids = get_valid_slack_ids()
		print(f"Valid Slack user IDs: {slack_ids}")
	"""
	
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
	"""
	Searches for a location using the PositionStack API based on the provided query.
	
	Args:
		query (str): The location query string to search for.
	
	Returns:
		tuple: A tuple containing the latitude (float), longitude (float), place name (str), 
			   time zone name (str), and time zone offset in hours (float) for the found location.
	
	This function performs the following steps:
		1. Retrieves the PositionStack API token from the Flask application configuration.
		2. Establishes an HTTP connection to the PositionStack API endpoint.
		3. Encodes the query parameters including the access token, query string, and limit.
		4. Makes a GET request to the PositionStack API endpoint to search for the location.
		5. Parses the response data and extracts the latitude, longitude, place name, time zone name, and offset.
		6. Returns a tuple containing the extracted information.
	
	Notes:
		- The function assumes it is running within the SIMS Portal's Flask application context and uses `current_app` 
		  for accessing configuration.
		- The PositionStack API is used for location search, and the API token is required for authentication.
		- The function handles errors gracefully and returns None if no location is found or if an error occurs.
		- Time zone information includes the name of the time zone and the offset from UTC in hours.
	
	Example:
		lat, long, place, timezone, offset = search_location('New York')
		print(f"Latitude: {lat}, Longitude: {long}, Place: {place}, Timezone: {timezone}, Offset: {offset}")
	"""
	
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
	"""
	Updates the JSON file with the locations of all members having coordinates.
	
	This function performs the following steps:
		1. Queries the database to retrieve all user records.
		2. Iterates through each user to extract and parse their coordinates if available.
		3. Converts the coordinates to a dictionary format with 'latitude' and 'longitude' keys.
		4. Collects all location dictionaries into a list.
		5. Serializes the list of location dictionaries into a JSON string.
		6. Writes the JSON string to a file located at 'SIMS_Portal/static/data/locations.json'.
		7. Removes any existing file at the specified path before writing the new file.
	
	Notes:
		- The function assumes that user coordinates are stored as strings in the format "[latitude, longitude]".
		- Coordinates are parsed and converted to float before being added to the dictionary.
		- The function uses the `db.session` to query user data and the `json` library to serialize the data.
		- The file path is hard-coded to "SIMS_Portal/static/data/locations.json", and any existing file at 
		  this path will be replaced.
	
	Example:
		update_member_locations()
		This will update the 'locations.json' file with the current member locations.
	"""
	
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
	"""
	Downloads and saves a Slack user's profile photo.
	
	Args:
		slack_id (str): The Slack user ID whose profile photo needs to be downloaded.
	
	Returns:
		str: The path to the saved profile photo if successful, otherwise None.
	
	This function performs the following steps:
		1. Constructs the URL and headers for the Slack API request.
		2. Retrieves the Slack bot access token from the Flask application configuration.
		3. Makes a GET request to the Slack API to fetch the user's profile information.
		4. Checks the response for a successful status code and the presence of the original profile photo URL.
		5. Downloads the profile photo from the provided URL.
		6. Saves the downloaded photo using the `save_picture_from_slack` function.
		7. Updates the user's profile in the database with the path to the saved photo.
		8. Commits the database transaction.
		9. Logs the outcome of the operation and returns the path to the saved photo.
	
	Notes:
		- The function assumes it is running within the SIMS Portal's Flask application context and uses `current_app` 
		  for configuration and logging.
		- The function uses the `requests` library to make HTTP requests to the Slack API.
		- The `save_picture_from_slack` function is called to handle the image processing and saving.
		- The database session (`db.session`) is used to update the user's profile photo path.
	
	Example:
		picture_path = download_profile_photo('U12345678')
		if picture_path:
			print(f"Profile photo saved to: {picture_path}")
	"""
	
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
	"""
	Saves a picture from Slack to an S3 bucket after processing it.
	
	Args:
		picture (bytes): The image data in bytes format.
	
	Returns:
		str: The path to the saved picture in the S3 bucket if successful, otherwise None.
	
	This function performs the following steps:
		1. Generates a random hex string to create a unique filename for the picture.
		2. Defines the path where the picture will be saved.
		3. Sets the output size for the image thumbnail (400x400 pixels).
		4. Tries to open the image from the byte data. If unsuccessful, logs an error and returns None.
		5. Resizes the image to the defined output size.
		6. Uploads the processed image to an S3 bucket.
		7. Returns the path to the uploaded picture.
	
	Notes:
		- The function uses the `secrets` library to generate a random filename for security.
		- The image is processed using the `Pillow` library to ensure it meets the required dimensions.
		- The function assumes it is running within a Flask application context and uses `current_app` 
		  to access configuration and logging.
		- AWS S3 is used for storing the image, and the S3 client is created using the `boto3` library.
	
	Example:
		picture_path = save_picture_from_slack(picture_data)
		if picture_path:
			print(f"Picture saved to: {picture_path}")
	"""
	
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

def bulk_slack_photo_update():
	"""
	Automatically updates the profile photos of users with the default avatar using their Slack photos.
	
	This function performs the following steps:
		1. Imports the `save_slack_photo_to_profile` function to avoid circular import issues.
		2. Queries the database to find all users with the default profile image ('default.png').
		3. Iterates over each user and attempts to update their profile photo using their Slack photo.
		4. Logs an informational message for each successful update, including the user's ID, first name, and last name.
		5. Clears any pending flash messages to avoid alerting all users about the changes.
		6. Logs a warning message if an error occurs during the update process for any user.
	
	Notes:
		- This function assumes it is running within the SIMS Portal's Flask application context and uses `current_app` 
		  for logging and accessing the session.
		- It handles exceptions individually for each user to ensure that an error with one user does not 
		  interrupt the entire update process.
	
	Example:
		bulk_slack_photo_update()
		This will update the profile photos of all users with the default avatar by fetching their Slack photos.
	"""
	
	# lazy import to avoid circular import error
	from SIMS_Portal.users.routes import save_slack_photo_to_profile
	
	users_with_default_avatar = db.session.query(User).filter(User.image_file == 'default.png').all()
	
	for user in users_with_default_avatar:
		try:
			save_slack_photo_to_profile(user.id)
			current_app.logger.info("User-{} ({} {}) has had their avatar automatically updated with their Slack photo.".format(user.id, user.firstname, user.lastname))
			
			# flush pending flashes to avoid alerting all users to this change
			session['_flashes'] = []
		except Exception as e:
			current_app.logger.warning("bulk_slack_photo_update failed for user-{}: {}".format(user.id, e))
			
def update_robots_txt(user_id, disallow=True):
	"""
	Updates the `robots.txt` file to disallow or allow search engine indexing of a user's profile view.
	
	Args:
		user_id (str): The ID of the user whose profile view setting is being updated.
		disallow (bool, optional): A flag to indicate whether to disallow (True) or allow (False) 
								   indexing of the user's profile view. Defaults to True.
	
	This function performs the following steps:
		1. Reads the existing content of the `robots.txt` file if it exists.
		2. Constructs the appropriate rule based on the `disallow` flag.
		3. Updates or appends the rule for the given `user_id` in the `robots.txt` file.
		4. Writes the updated content back to the `robots.txt` file.
		5. Logs an informational message indicating whether a new rule was added or an existing rule was updated.
	
	The `robots.txt` rule format is:
		- "Disallow: /profile/view/<user_id>/" if `disallow` is True
		- "Allow: /profile/view/<user_id>/" if `disallow` is False
	
	Example:
		update_robots_txt('user123', disallow=True)
		This will add or update the rule "Disallow: /profile/view/user123/" in the `robots.txt` file.
	
	Notes:
		- The function assumes it is running within a Flask application context and uses `current_app` 
		  to access the application root path and logger.
	"""
	
	robots_txt_path = os.path.join(current_app.root_path, 'robots.txt')
	
	# read the existing "robots.txt" content, if it exists
	existing_content = []
	if os.path.exists(robots_txt_path):
		with open(robots_txt_path, 'r') as robots_file:
			existing_content = robots_file.readlines()
	
	# flag to track if the rule was updated
	rule_updated = False
	
	updated_content = []
	
	# construct the new Disallow or Allow rule
	new_rule = "Disallow: /profile/view/{}/".format(user_id) if disallow else "Allow: /profile/view/{}/".format(user_id)
	
	# loop through existing rules
	for line in existing_content:
		# Check if the rule for the current user_id already exists
		if line.strip().startswith("Disallow: /profile/view/{}/".format(user_id)) or line.strip().startswith("Allow: /profile/view/{}/".format(user_id)):
			# if Disallow=False, replace with Allow
			if not disallow:
				updated_content.append(new_rule + "\n")
				rule_updated = True
		else:
			# keep other rules unchanged
			updated_content.append(line)
	
	# if Disallow=True and the rule didn't exist, append it
	if disallow and not rule_updated:
		updated_content.append(new_rule + "\n")
	
	# write the updated content back to the "robots.txt" file
	with open(robots_txt_path, 'w') as robots_file:
		robots_file.writelines(updated_content)
	
	if rule_updated:
		current_app.logger.info('User {} has updated their search engine settings on robots.txt'.format(user_id))
	else:
		current_app.logger.info('A new robots.txt rule as has been added for user {}'.format(user_id))

def invite_user_to_github(username):
	"""
	Invites a user to join the SIMS GitHub organization.
	
	Parameters:
		username (str): The GitHub username of the user to be invited.
	
	Returns:
		bool: True if the user was successfully invited to the organization, False otherwise.
	
	Note:
		This function requires a personal access token with 'admin:org' scope
		to authenticate with the GitHub API. Ensure that the token used has
		sufficient permissions to add users to the organization.
	
	Example:
		>>> invite_user_to_github('example_user')
		True
	"""
	
	github_base_url = 'https://api.github.com'
	org_name = 'Surge-Information-Management-Support'
	access_token = current_app.config['GITHUB_TOKEN']
	
	headers = {
		'Authorization': f'token {access_token}',
		'Accept': 'application/vnd.github.v3+json'
	}
	
	url = f'{github_base_url}/orgs/{org_name}/memberships/{username}'
	response = requests.put(url, headers=headers)
	if response.status_code == 200:
		log_message = f"[INFO] GitHub user {username} was invited to join the SIMS GitHub organization."
		new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
		db.session.add(new_log)
		db.session.commit()
		return True 
	else:
		log_message = f"[ERROR] invite_user_to_github() function ran for user {username} but encountered an error: {response.status_code} | {response.text}."
		new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
		db.session.add(new_log)
		db.session.commit()
		return False

def process_inactive_members():
	"""
	Identify and process inactive members who have not logged in for over six and a half months.
	The extra two weeks after the six month mark gives users two weeks (and two Slack alert messages)
		to log in before having this function mark them as inactive.
	
	This function performs the following steps:
	1. Calculates the date six and a half months ago from the current date.
	2. Creates a subquery to find the most recent login timestamp for each user.
	3. Queries the database to find users whose:
		a. Last login is before the calculated date.
		b. Status is currently marked as 'Active'.
	4. Iterates through the identified inactive members and marks them as inactive using the set_user_inactive() function.
	
	Returns:
		List of members that have been processed and marked as inactive, including their user IDs,
		last login timestamps, login messages, first names, and last names.
	"""
	
	six_and_a_half_months_ago = datetime.now() - timedelta(days=194)
	
	subquery = db.session.query(
		Log.user_id,
		func.max(Log.timestamp).label('max_timestamp')
	).filter(
		Log.message.like('%logged in%')
	).group_by(Log.user_id).subquery()
	
	to_be_marked_inactive = db.session.query(
		Log.user_id,
		Log.timestamp,
		Log.message,
		User.firstname,
		User.lastname, 
		User.slack_id
	).join(
		User, User.id == Log.user_id
	).join(
		subquery,
		(Log.user_id == subquery.c.user_id) &
		(Log.timestamp == subquery.c.max_timestamp)
	).filter(
		Log.timestamp < six_and_a_half_months_ago,
		User.status == 'Active'
	).all()
	
	for member in to_be_marked_inactive:
		set_user_inactive(member.user_id)
		message = f"Hi, {member.firstname}! Your account on the SIMS Portal has been automatically marked as Inactive because it has been more than six months since you last logged in. If you'd like to update it to be Active again, just <https://www.rcrcsims.org/login|login>."
		try:
			success = send_slack_dm(message, member.slack_id)
		except Exception as e:
			log_message = f"[ERROR] Failed to send Slack DM to user {member.user_id}: {e}."
			new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
			db.session.add(new_log)
			db.session.commit()
	
	log_message = f"[INFO] process_inactive_members() function ran."
	new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
	db.session.add(new_log)
	db.session.commit()
	
	return to_be_marked_inactive

def audit_inactive_members():
	"""
	Retrieve the latest login activity of members who have been inactive for more than six months.

	Returns:
		list: A list of tuples containing the user_id, timestamp of the last login, message of the last login,
			  first name, and last name of the inactive members.

	Notes:
		This function queries the database to find members who have been inactive for more than six months
		based on their last login timestamp. It retrieves the latest login activity for each member and
		returns the relevant information.
	"""
	six_months_ago = datetime.now() - timedelta(days=180)
	
	subquery = db.session.query(
		Log.user_id,
		func.max(Log.timestamp).label('max_timestamp')
	).filter(
		Log.message.like('%logged in%')
	).group_by(Log.user_id).subquery()
	
	latest_logins = db.session.query(
		Log.user_id,
		Log.timestamp,
		Log.message,
		User.firstname,
		User.lastname
	).join(
		User, User.id == Log.user_id
	).join(
		subquery,
		(Log.user_id == subquery.c.user_id) &
		(Log.timestamp == subquery.c.max_timestamp)
	).filter(
		Log.timestamp < six_months_ago,
		User.status == 'Active'
	).all()
	
	return latest_logins
		
def alert_inactive_members():
	"""
	Alert members who have been inactive for more than six months by logging a message.
	"""
	try:
		potentially_inactive_members = audit_inactive_members()
		
		for member in potentially_inactive_members:
			message = f"Hi there, {member.firstname}! I wanted to let you know that it's been six months since you last logged into the SIMS Portal. *If you would like to remain listed as an Active member of SIMS*, please log into the <https://www.rcrcsims.org/login|SIMS Portal>. No further action is required after logging in.\n\nRegular audits of our member list helps keep various elements inside the application running smoothly and reduces server overhead."
			send_slack_dm(message, member.slack_id)
		
	except Exception as e:
		log_message = f"[ERROR] alert_inactive_members() function encountered an error: {e}."
		new_log = Log(message=log_message, user_id=63) # save message as Clara Barton
		db.session.add(new_log)
		db.session.commit()

def set_user_inactive(user_id):
	"""
	Marks a user as inactive and logs this action in the database.
	
	This function updates the status of the user with the given user_id to 'Inactive'
	and logs the action. If the user is not found, it logs an error message.
	
	Args:
		user_id (int): The ID of the user to be marked as inactive.
	
	Returns:
		User: The updated User object if the user was found and updated, otherwise None.
	"""
	
	inactive_user = db.session.query(User).filter(User.id == user_id).first()
	if inactive_user:
		inactive_user.status = 'Inactive'
		db.session.commit()
		
		log_message = f"[INFO] User {inactive_user.id} has been automatically marked as inactive."
		new_log = Log(message=log_message, user_id=inactive_user.id)
		db.session.add(new_log)
		db.session.commit()
	else:
		log_message = f"[ERROR] set_user_inactive() failed to set user {inactive_user.id} as inactive."
		new_log = Log(message=log_message, user_id=inactive_user.id)
		db.session.add(new_log)
		db.session.commit()
		
	return inactive_user

def set_user_active(user_id):
	"""
	Marks a user as active and logs this action in the database.
	
	This function updates the status of the user with the given user_id to 'Active'
	and logs the action. If the user is not found, it logs an error message.
	
	Args:
		user_id (int): The ID of the user to be marked as active.
	
	Returns:
		User: The updated User object if the user was found and updated, otherwise None.
	"""
	
	active_user = db.session.query(User).filter(User.id == user_id).first()
	if active_user.status == 'Inactive':
		active_user.status = 'Active'
		db.session.commit()
		
		log_message = f"[INFO] User {active_user.id} has been automatically marked as active."
		new_log = Log(message=log_message, user_id=active_user.id)
		db.session.add(new_log)
		db.session.commit()
	else:
		log_message = f"[ERROR] set_user_inactive() failed to set user {active_user.id} as active."
		new_log = Log(message=log_message, user_id=active_user.id)
		db.session.add(new_log)
		db.session.commit()
		
	return active_user