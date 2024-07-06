from SIMS_Portal import db
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from SIMS_Portal.models import Alert, Log, RegionalFocalPoint, User
from SIMS_Portal.users.utils import new_surge_alert, test_surge_alert
from SIMS_Portal.main.utils import send_error_message
from flask_apscheduler import APScheduler
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math
import requests
import logging
import re

scheduler = APScheduler()

def get_slack_username(user_id):
	"""
	Retrieve the Slack username for a given user ID.
	
	We don't store that value in the users table, so we need to get it via their Slack ID.
	Uses the Slack API to get user information based on the provided user ID. 
	It returns the username if the API call is successful, or logs an error and returns None otherwise.
	
	Parameters:
	user_id (str): The Slack user ID for which to retrieve the username.
	
	Returns:
	str: The Slack username if successful, or None if an error occurs.
	
	Side Effects:
	Logs an error message to the database if the API call fails.
	
	Raises:
	None
	"""
	
	slack_token = current_app.config['SIMS_PORTAL_SLACK_BOT']	
	url = f"https://slack.com/api/users.info?user={user_id}"
	headers = {
		"Content-type": "application/json",
		"Authorization": f"Bearer {slack_token}"
	}
	response = requests.get(url, headers=headers)
	
	if response.status_code != 200:
		log_message = f"[ERROR] The get_slack_username function failed: {response.status_code}."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
		return None
	
	json_response = response.json()
	
	if json_response.get("ok"):
		return json_response.get("user", {}).get("name")
	else:
		print(f"Error: {json_response.get('error')}")
		return None

def calculate_months_difference(start_date, end_date):
	if isinstance(start_date, str):
		start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
	if isinstance(end_date, str):
		end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
	
	date_difference = relativedelta(end_date, start_date)
	
	months_difference = date_difference.years * 12 + date_difference.months + round(date_difference.days / 30, 2)
	
	return months_difference

def send_im_alert_to_slack(alert_info):
	"""
	Send an Information Management (IM) alert message to Slack.
	
	Constructs and sends a formatted alert message to Slack based on the provided alert information.
	The alert can be either global or regional and includes various details such as role profile, event, rotation,
	language requirements, modality, timeframe, and regional focal point.
	
	Parameters:
	alert_info (object): An object containing alert information, including:
		- region_id (int): The ID of the region.
		- role_profile (str): The role profile for the alert.
		- start (datetime): The start date of the alert.
		- end_time (datetime): The end date of the alert.
		- scope (str): The scope of the alert ('Global' or 'Regional').
		- disaster_go_id (int): The ID of the disaster.
		- event (str): The name of the event.
		- ifrc_severity_level_display (str): The severity level of the event.
		- rotation (str): The rotation details for the role.
		- language_required (str): The language requirements for the role.
		- modality (str): The modality of the role.
		- molnix_id (int): The ID of the alert in the IFRC Rapid Response Management System (RRMS).
	
	Returns:
	None
	
	Side Effects:
	Logs a warning message to the database if an error occurs.
	
	Raises:
	None
	"""
	try:
		colors_to_emoji = {
			'Red': 'a :red_circle: red',
			'Orange': 'an :large_orange_circle: orange',
			'Yellow': 'a :large_yellow_circle: yellow'
		}
		
		# link to ifrc sharepoint's file on the role profile
		standard_profiles = {
			'Information Management Coordinator': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/Ea_YRhCI_IJHkhISEh5zH2YBCUtMAdWUqiC8JH7g1Jj8AQ', 
			'Humanitarian Information Analysis Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/EYUNi8qR395Oq3Ng3SHbsXMBUbS4XdfVw03tECGEb828Nw', 
			'Primary Data Collection Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/EdB7tgvjH5dApy5PcFNZcx0BzGKQJfS2nP-L3CFKRdr5Ow', 
			'Mapping and Data Visualization Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/ER92aBZKBpxHrH61MJf4hLEBxwEnqzfqjLVR7cscPlxDKA',
			'SIMS Remote Coordinator': 'https://go.ifrc.org/deployments/catalogue/infoMgt'
		}
		
		# get regional surge email address for alert message
		regional_surge_email_lookup = {
			1: 'surge.africa@ifrc.org',
			2: 'surge.americas@ifrc.org',
			3: 'rapidresponse.ap@ifrc.org',
			4: 'surge.europe@ifrc.org',
			5: '', # mena doesn't have a generic address
		}
		
		regional_surge_email = regional_surge_email_lookup.get(alert_info.region_id, 'surge@ifrc.org')
		
		position_description = standard_profiles.get(alert_info.role_profile, None)
		if position_description is not None:
			position_description_link = f"<{position_description}|Standard role profile for this position>"
		else:
			position_description_link = None
		
		alert_length = calculate_months_difference(alert_info.start, alert_info.end_time)
		
		try:
			regional_focal_point_id = db.session.query(RegionalFocalPoint, User).join(User, User.id == RegionalFocalPoint.focal_point_id).filter(RegionalFocalPoint.regional_id == alert_info.region_id).first()
			regional_focal_point = get_slack_username(regional_focal_point_id.User.slack_id)
		except:
			log_message = f"[WARNING] The Surge Alert (Latest) script could not identify a regional focal point to tag in the Slack availability message."
			new_log = Log(message=log_message, user_id=0)
			db.session.add(new_log)
			db.session.commit()
			regional_focal_point = "Focal Point Missing"
		
		# Check and reformat dates for slack message
		if alert_info.start and alert_info.end_time:
			requested_timeframe_start = alert_info.start.strftime("%B %d, %Y")
			requested_timeframe_end = alert_info.end_time.strftime("%B %d, %Y")
			timeframe_message = f'{requested_timeframe_start} - {requested_timeframe_end} ({alert_length} months)'
		else:
			timeframe_message = "Start and/or end date information missing in API. Please contact the regional focal point for information on the timeframe."
		
		# construct message
		if alert_info.scope == 'Global':
			if alert_info.role_profile == 'SIMS Remote Coordinator':
				message = (
					f"\n:rotating_light: *New Global Information Management Surge Alert Released!* :rotating_light:\n\n A surge alert for a *SIMS Remote Coordinator* has been released for the <https://go.ifrc.org/emergencies/{alert_info.disaster_go_id}|{alert_info.event}>, which is {colors_to_emoji[alert_info.ifrc_severity_level_display]} emergency. \n\n • *Role*: 1 x {alert_info.role_profile} \n\n • *Rotation*: {alert_info.rotation} \n\n • *Language requirements*: {alert_info.language_required} \n\n • *Modality*: {alert_info.modality} \n\n • *Requested timeframe*: {timeframe_message} \n\n • {position_description_link} \n\n • *Regional Focal Point*: <@{regional_focal_point}> \n\n • *Note*: SIMS Remote Coordinator positions are remote \n\n Please follow <https://rrms.ifrc.org/positions/show/{alert_info.molnix_id}|this link> to view the alert in the IFRC Rapid Response Management System (RRMS) and apply. If you have any questions or issues, please contact surge@ifrc.org"
				)
			else:
				message = (
					f"\n:rotating_light: *New Global Information Management Surge Alert Released!* :rotating_light:\n\n A surge alert for a *{alert_info.role_profile}* has been released for the <https://go.ifrc.org/emergencies/{alert_info.disaster_go_id}|{alert_info.event}>, which is {colors_to_emoji[alert_info.ifrc_severity_level_display]} emergency. \n\n • *Role*: 1 x {alert_info.role_profile} \n\n • *Rotation*: {alert_info.rotation} \n\n • *Language requirements*: {alert_info.language_required} \n\n • *Modality*: {alert_info.modality} \n\n • *Requested timeframe*: {timeframe_message} \n\n • {position_description_link} \n\n • *Regional Focal Point*: <@{regional_focal_point}> \n\n Please follow <https://rrms.ifrc.org/positions/show/{alert_info.molnix_id}|this link> to view the alert in the IFRC Rapid Response Management System (RRMS) and apply. If you have any questions or issues, please contact surge@ifrc.org"
				)
		
		if alert_info.scope == 'Regional':
			message = (
				f"\n *New Regional Information Management Surge Alert Released!* \n\n A regional surge alert for a *{alert_info.role_profile}* has been released for the <https://go.ifrc.org/emergencies/{alert_info.disaster_go_id}|{alert_info.event}>, which is {colors_to_emoji[alert_info.ifrc_severity_level_display]} emergency. This alert is not being triaged globally, and this message is for situational awareness only. \n\n • *Role*: 1 x {alert_info.role_profile} \n\n • *Rotation*: {alert_info.rotation} \n\n • *Language requirements*: {alert_info.language_required} \n\n • *Modality*: {alert_info.modality} \n\n • *Requested timeframe*: {timeframe_message} \n\n • {position_description_link} \n\n • *Regional Focal Point*: <@{regional_focal_point}> \n\n Please follow <https://rrms.ifrc.org/positions/show/{alert_info.molnix_id}|this link> to view the alert in the IFRC Rapid Response Management System (RRMS) and apply. If you have any questions or issues, please contact {regional_surge_email}"
			)
		
		new_surge_alert(message)
		
	except Exception as e:
		log_message = f"[WARNING] send_im_alert_to_slack() failed: {e}"
		new_log = Log(message=log_message, user_id=63) # send message as Clara Barton
		db.session.add(new_log)
		db.session.commit()

def refresh_surge_alerts_latest():
	"""
	Refresh and update the latest surge alerts from the GO Admin API.
	
	This function fetches the latest surge alert data from the GO Admin API, processes the data, and updates the
	local database with new or modified alerts. It logs the process and handles any errors that occur during the 
	execution. This version of the function only looks at the latest page in the results. If this function is run daily, that should catch all alerts that come out. To run the same version of this function but loop through all pages, use the `refresh_surge_alerts()` function available in this same utility file.
	
	Parameters:
	None
	
	Returns:
	None
	
	Side Effects:
	- Logs information and errors to the database.
	- Updates existing alert records or adds new ones to the database.
	- Sends IM alerts to Slack if applicable.
	
	Raises:
	None
	"""
	count_new_records = 0
	count_updated_records = 0
	url = "https://goadmin.ifrc.org/api/v2/surge_alert/"
	
	try:
		log_message = f"[INFO] The Surge Alert (Latest) cron job has started."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
	
		log_message = f"[INFO] Fetching existing alerts from the database."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
	
		existing_alerts = db.session.query(Alert).order_by(Alert.molnix_id.desc()).all()
		existing_alert_ids = {alert.alert_id for alert in existing_alerts}
		existing_statuses = {alert.alert_id: alert.alert_status for alert in existing_alerts}
	
		log_message = f"[INFO] Making API request to {url}."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
	
		response = requests.get(url)
		log_message = f"[INFO] API request successful, processing response."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
	
		data = response.json()
		results = data.get("results", [])
	
		result_list = []
		for result in results:
			molnix_tags = result.get("molnix_tags", [])
	
			sectors = []
			roles = []
	
			alert_id = result.get("id", None)
			molnix_id = result.get("molnix_id", None)
			alert_record_created_at = result.get("created_at", None)
			molnix_status = result.get("molnix_status", None)
			alert_status = result.get("status_display", None)
			opens = result.get("opens", None)
			start = result.get("start", None)
			end = result.get("end", None)
	
			modality = None
			im_filter = False
	
			region_id = None
			sector = None
			role_profile = None
			scope = None
	
			for tag in molnix_tags:
				groups = tag.get("groups", [])
	
				if "REGION" in groups:
					region_id = tag.get("description", None)
	
				if "SECTOR" in groups:
					sector = tag.get("description", None)
					sectors.append(sector)
	
				if "ROLES" in groups:
					role_profile = tag.get("description", None)
					roles.append(role_profile)
	
				if "Modality" in groups:
					modality = tag.get("name", None)
	
				if "ALERT TYPE" in groups:
					scope = tag.get("name", None).title()
	
			im_filter = "Information Management" in sectors
	
			language_required = next((tag.get("description", None) for tag in molnix_tags if tag.get("tag_type") == "language"), None)
			rotation = next((group.get("name", None) for group in molnix_tags if "rotation" in group.get("groups", [])), None)
	
			country = result.get("country", {})
			iso3 = country.get("iso3", None)
			country_name = country.get("name", None)
	
			region_ids_dict = {
				"Europe Region": 4,
				"Asia Pacific Region": 3,
				"Americas Region": 2,
				"Africa Region": 1,
				"Middle East & North Africa Region": 5
			}
	
			event = result.get("event", {})
			disaster_type_id = event.get("dtype", {}).get("id", None)
			disaster_type_name = event.get("dtype", {}).get("name", None)
			ifrc_severity_level_display = event.get("ifrc_severity_level_display", None)
			event_name = event.get("name", None)
			disaster_go_id = event.get("id", None)
	
			result_dict = {
				"molnix_id": molnix_id,
				"alert_record_created_at": alert_record_created_at,
				"event": event_name,
				"role_profile": role_profile,
				"rotation": rotation,
				"modality": modality,
				"language_required": language_required,
				"molnix_status": molnix_status,
				"alert_status": alert_status,
				"opens": opens,
				"start": start,
				"end_time": end,
				"sectors": sectors,
				"role_tags": roles,
				"scope": scope,
				"im_filter": im_filter,
				"iso3": iso3,
				"country_name": country_name,
				"disaster_type_id": disaster_type_id,
				"disaster_type_name": disaster_type_name,
				"disaster_go_id": disaster_go_id,
				"ifrc_severity_level_display": ifrc_severity_level_display,
				"alert_id": alert_id,
				"region_id": region_ids_dict.get(region_id, None),
			}
	
			result_list.append(result_dict)
	
		for result in result_list:
			result['sectors'] = ', '.join(result['sectors'])
			result['role_tags'] = ', '.join(result['role_tags'])
	
			existing_alert = next((alert for alert in existing_alerts if alert.alert_id == result['alert_id']), None)
	
			if existing_alert:
				if existing_alert.alert_status != result['alert_status']:
					try:
						existing_alert.alert_status = result['alert_status']
						db.session.commit()
						count_updated_records += 1
						log_message = f"[INFO] Updated alert_status for alert_id {result['alert_id']}."
						new_log = Log(message=log_message, user_id=0)
						db.session.add(new_log)
						db.session.commit()
					except Exception as e:
						db.session.rollback()
						log_message = f"[ERROR] Failed to update alert_status for alert_id {result['alert_id']}: {e}"
						new_log = Log(message=log_message, user_id=0)
						db.session.add(new_log)
						db.session.commit()
	
			else:
				if result['alert_id'] not in existing_alert_ids:
					try:
						individual_alert = Alert(
							molnix_id=result['molnix_id'],
							alert_record_created_at=result['alert_record_created_at'],
							event=result['event'],
							role_profile=result['role_profile'],
							rotation=result['rotation'],
							modality=result['modality'],
							language_required=result['language_required'],
							molnix_status=result['molnix_status'],
							alert_status=result['alert_status'],
							opens=result['opens'],
							start=result['start'],
							end_time=result['end_time'],
							sectors=result['sectors'],
							role_tags=result['role_tags'],
							scope=result['scope'],
							im_filter=result['im_filter'],
							iso3=result['iso3'],
							country_name=result['country_name'],
							disaster_type_id=result['disaster_type_id'],
							disaster_type_name=result['disaster_type_name'],
							disaster_go_id=result['disaster_go_id'],
							ifrc_severity_level_display=result['ifrc_severity_level_display'],
							alert_id=result['alert_id'],
							region_id=result['region_id']
						)
						db.session.add(individual_alert)
						db.session.commit()
						count_new_records += 1
						log_message = f"[INFO] Added new alert with alert_id {individual_alert.alert_id}."
						new_log = Log(message=log_message, user_id=0)
						db.session.add(new_log)
						db.session.commit()
	
						if individual_alert.im_filter:
							send_im_alert_to_slack(individual_alert)
	
					except Exception as e:
						db.session.rollback()
						log_message = f"[ERROR] The refresh_surge_alerts_latest function couldn't add one of the alerts (alert_id={result['alert_id']}) to the database: {e}"
						new_log = Log(message=log_message, user_id=0)
						db.session.add(new_log)
						db.session.commit()
	
	except Exception as e:
		db.session.rollback()
		log_message = f"[ERROR] The Surge Alert cron job has failed: {e}."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
		send_error_message(log_message)
	
	log_message = f"[INFO] The Surge Alert cron job has finished and logged {count_new_records} new records."
	new_log = Log(message=log_message, user_id=0)
	db.session.add(new_log)
	db.session.commit()

def refresh_surge_alerts(pages_to_fetch):
	"""
	Refresh and update surge alerts from the GO Admin API, fetching a specified number of pages.
	
	Retrieves surge alert data from the GO Admin API, processes the data, and updates the local database
	with new or modified alerts. It handles pagination to fetch multiple pages of results and logs the process 
	details and errors.
	
	Parameters:
	pages_to_fetch (int): The number of pages to fetch from the API.
	
	Returns:
	None
	
	Side Effects:
	- Logs information and errors to the database.
	- Updates existing alert records or adds new ones to the database.
	- Sends error messages if necessary.
	
	Raises:
	None
	"""
	
	try:
		log_message = f"[INFO] The Surge Alert (full version) function has started."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
		
		existing_alerts = db.session.query(Alert).order_by(Alert.molnix_id.desc()).all()
		existing_alert_ids = []
		existing_statuses = []
		for alert in existing_alerts:
			existing_alert_ids.append(alert.alert_id)
			alert_dict = {}
			alert_dict['molnix_id'] = alert.alert_id
			alert_dict['alert_status'] = alert.alert_status
			existing_statuses.append(alert_dict)
		
		url = "https://goadmin.ifrc.org/api/v2/surge_alert/"
		result_list = []
		
		current_page = 1
		
		while url and current_page <= pages_to_fetch:
			response = requests.get(url)
			data = response.json()
			results = data.get("results", [])
		
			for result in results:
				molnix_tags = result.get("molnix_tags", [])
			
				sectors = []
				roles = []
				
				alert_id = result.get("id", None)
				molnix_id = result.get("molnix_id", None)
				alert_record_created_at = result.get("created_at", None)
				molnix_status = result.get("molnix_status", None)
				alert_status = result.get("status_display", None)
				opens = result.get("opens", None)
				start = result.get("start", None)
				end = result.get("end", None)
			
				modality = None
				im_filter = False
				
				# predefine these in case they don't appear in molnix tags
				region_id = None
				sector = None
				role_profile = None 
				modality = None
				scope = None
				
				for tag in molnix_tags:
					groups = tag.get("groups", [])
			
					if "SECTOR" in groups:
						sector = tag.get("description", None)
						sectors.append(sector)
			
					if "ROLES" in groups:
						role_profile = tag.get("description", None)
						roles.append(role_profile)
			
					if "Modality" in groups:
						modality = tag.get("name", None)
					
					if "ALERT TYPE" in groups:
						scope = tag.get("name", None).title()
			
				im_filter = "Information Management" in sectors
			
				language_required = next((tag.get("description", None) for tag in molnix_tags if tag.get("tag_type") == "language"), None)
				rotation = next((group.get("name", None) for group in molnix_tags if "rotation" in group.get("groups", [])), None)
			
				country = result.get("country", {})
				iso3 = country.get("iso3", None)
				country_name = country.get("name", None)
			
				event = result.get("event", {})
				disaster_type_id = event.get("dtype", {}).get("id", None)
				disaster_type_name = event.get("dtype", {}).get("name", None)
				ifrc_severity_level_display = event.get("ifrc_severity_level_display", None)
				event_name = event.get("name", None)
				disaster_go_id = event.get("id", None)
			
				result_dict = {
					"molnix_id": molnix_id,
					"alert_record_created_at": alert_record_created_at,
					"event": event_name,
					"role_profile": role_profile,
					"rotation": rotation,
					"modality": modality,
					"language_required": language_required,
					"molnix_status": molnix_status,
					"alert_status": alert_status,
					"opens": opens,
					"start": start,
					"end_time": end,
					"sectors": sectors,
					"role_tags": roles,
					"scope": scope,
					"im_filter": im_filter,
					"iso3": iso3,
					"country_name": country_name,
					"disaster_type_id": disaster_type_id,
					"disaster_type_name": disaster_type_name,
					"disaster_go_id": disaster_go_id,
					"ifrc_severity_level_display": ifrc_severity_level_display,
					"alert_id": alert_id
				}
			
				result_list.append(result_dict)
			
			# flip page for pagination
			url = data.get("next")
			current_page += 1
		
		count_new_records = 0
		count_updated_records = 0
		
		for result in result_list:
			
			# these fields can have multiple values, so strip curly brackets and save as comma-separated strings
			result['sectors'] = ', '.join(result['sectors'])
			result['role_tags'] = ', '.join(result['role_tags'])
			
			existing_alert = next((alert for alert in existing_alerts if alert.alert_id == result['alert_id']), None)
			
			if existing_alert:
				# check if alert_status has changed
				if existing_alert.alert_status != result['alert_status']:
					try:
						# update the existing alert in the database
						existing_alert.alert_status = result['alert_status']
						db.session.commit()
						count_updated_records += 1
					except Exception as e:
						log_message = f"[ERROR] Failed to update alert_status for alert_id {result['alert_id']}: {e}"
						new_log = Log(message=log_message, user_id=0)
						db.session.add(new_log)
						db.session.commit()
			
			else:
				# this is a new alert; add it to the database
				if result['alert_id'] not in existing_alert_ids:
					try:
						individual_alert = Alert(
							molnix_id = result['molnix_id'],
							alert_record_created_at = result['alert_record_created_at'],
							event = result['event'],
							role_profile = result['role_profile'],
							rotation = result['rotation'],
							modality = result['modality'],
							language_required = result['language_required'],
							molnix_status = result['molnix_status'],
							alert_status = result['alert_status'],
							opens = result['opens'],
							start = result['start'],
							end_time = result['end_time'],
							sectors = result['sectors'],
							role_tags = result['role_tags'],
							scope = result['scope'],
							im_filter = result['im_filter'],
							iso3 = result['iso3'],
							country_name = result['country_name'],
							disaster_type_id = result['disaster_type_id'],
							disaster_type_name = result['disaster_type_name'],
							disaster_go_id = result['disaster_go_id'],
							ifrc_severity_level_display = result['ifrc_severity_level_display'],
							alert_id = result['alert_id']
						)
					except Exception as e:
						log_message = f"[WARNING] The refresh_surge_alerts (full version) function couldn't parse one of the alerts it found in the Surge Alert cron job as it tried to instantiate a new Alert object: {e}"
						new_log = Log(message=log_message, user_id=0)
						db.session.add(new_log)
						db.session.commit()
					
					try:
						db.session.add(individual_alert)
						db.session.commit()
						count_new_records += 1
						
					except Exception as e:
						log_message = f"[ERROR] The refresh_surge_alerts (full version) function couldn't add one of the alerts (id={individual_alert.id}) to the database: {e}"
						new_log = Log(message=log_message, user_id=0)
						db.session.add(new_log)
						db.session.commit()
			
	except Exception as e:
		log_message = f"[ERROR] The Surge Alert (full version) cron job has failed: {e}."
		new_log = Log(message=log_message, user_id=0)
		db.session.add(new_log)
		db.session.commit()
		send_error_message(log_message)
	
	log_message = f"[INFO] The Surge Alert (full version) cron job has finished and logged {count_new_records} new records."
	new_log = Log(message=log_message, user_id=0)
	db.session.add(new_log)
	db.session.commit()	