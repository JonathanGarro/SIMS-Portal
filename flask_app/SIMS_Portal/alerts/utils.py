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
import time
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from requests.exceptions import RequestException

scheduler = APScheduler()

def _is_transient_db_error(exc):
	"""
	True for connection-level failures (dropped SSL connections, network blips)
	that are worth retrying, as opposed to data or programming errors that will
	just fail the same way every time.
	"""
	message = str(exc).lower()
	return any(s in message for s in ("ssl syscall error", "server closed the connection", "eof detected", "connection"))

def with_db_retry(operation, on_give_up=None, max_retries=3, retry_delay=2):
	"""
	Run `operation` (a zero-arg callable that touches db.session), retrying with
	backoff on transient connection errors.

	This always leaves db.session in a clean state before returning - including
	when it gives up - by rolling back on every failure. Without that, a single
	transient DB blip (which is otherwise harmless and would resolve itself on
	retry) leaves the session in a broken state that poisons every subsequent
	db.session call for the rest of the job, turning one blip into a total
	cron-job failure.

	Returns (True, result) on success, or (False, None) once retries are
	exhausted or the error isn't retryable.
	"""
	last_exc = None
	for attempt in range(max_retries):
		try:
			return True, operation()
		except Exception as e:
			last_exc = e
			try:
				db.session.rollback()
			except Exception:
				pass

			retryable = isinstance(e, OperationalError) and _is_transient_db_error(e)
			if retryable and attempt < max_retries - 1:
				try:
					db.session.remove()
					db.engine.dispose()
				except Exception:
					pass
				time.sleep(retry_delay * (attempt + 1))
				continue
			break

	if on_give_up:
		try:
			on_give_up(last_exc)
		except Exception:
			pass
	return False, None

def safe_log(message, user_id=0, max_retries=3, retry_delay=2):
	"""
	Write a Log row, retrying with backoff on transient connection errors via
	with_db_retry(). Falls back to stdout (so the message isn't lost outright)
	if the database is unreachable after retries. Returns True on success.
	"""
	def _write():
		new_log = Log(message=message, user_id=user_id)
		db.session.add(new_log)
		db.session.commit()

	def _give_up(exc):
		print(f"DATABASE ERROR: {exc}")
		print(f"Failed to log message: {message}")

	ok, _ = with_db_retry(_write, on_give_up=_give_up, max_retries=max_retries, retry_delay=retry_delay)
	return ok

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
		safe_log(f"[ERROR] The get_slack_username function failed: {response.status_code}.")
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
			5: 'surge.mena@ifrc.org', 
		}
		
		regional_surge_email = regional_surge_email_lookup.get(alert_info.region_id, 'surge@ifrc.org')
		
		position_description = standard_profiles.get(alert_info.role_profile, None)
		if position_description is not None:
			position_description_link = f"<{position_description}|Standard role profile for this position>"
		else:
			position_description_link = None
		
		alert_length = calculate_months_difference(alert_info.start, alert_info.end_time)
		
		# lookup regional IM coordinator
		try:
			regional_focal_point_id = db.session.query(RegionalFocalPoint, User).join(User, User.id == RegionalFocalPoint.focal_point_id).filter(RegionalFocalPoint.regional_id == alert_info.region_id).first()
			regional_focal_point = get_slack_username(regional_focal_point_id.User.slack_id)
		except:
			safe_log(f"[WARNING] The Surge Alert (Latest) script could not identify a regional focal point to tag in the Slack availability message.")
			regional_focal_point = "Focal Point Missing"
		
		# check and reformat dates for slack message
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
		safe_log(f"[WARNING] send_im_alert_to_slack() failed: {e}", user_id=63) # send message as Clara Barton

def refresh_surge_alerts_latest():
	"""
	Refresh and update the latest surge alerts from the GO Admin API.
	
	Fetches the latest surge alert data from the GO Admin API, processes the data, and updates the
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
		# start job and log message with fallback to print if db logging fails
		start_message = f"[INFO] The Surge Alert (Latest) cron job has started."
		if not safe_log(start_message):
			# If we can't even log to the database, send an error alert
			send_error_message(f"Database connection error in Surge Alert cron job. Unable to log to database.")

		safe_log(f"[INFO] Fetching existing alerts from the database.")

		def _fetch_existing_alerts():
			return db.session.query(Alert).order_by(Alert.molnix_id.desc()).all()

		fetched_ok, existing_alerts = with_db_retry(
			_fetch_existing_alerts,
			on_give_up=lambda e: safe_log(f"[ERROR] Failed to fetch existing alerts: {e}")
		)
		if not fetched_ok:
			existing_alerts = []
		existing_alert_ids = {alert.alert_id for alert in existing_alerts}
		existing_statuses = {alert.alert_id: alert.alert_status for alert in existing_alerts}
	
		safe_log(f"[INFO] Making API request to {url}.")
	
		# retry logic for API requests
		max_api_retries = 3
		api_retry_delay = 2
		
		for api_attempt in range(max_api_retries):
			try:
				response = requests.get(url, timeout=30)
				response.raise_for_status()
				break
			except RequestException as e:
				if api_attempt < max_api_retries - 1:
					safe_log(f"[WARNING] API request failed, retrying ({api_attempt + 1}/{max_api_retries}): {str(e)}")
					time.sleep(api_retry_delay)
				else:
					safe_log(f"[ERROR] API request failed after {max_api_retries} attempts: {str(e)}")
					raise
		
		safe_log(f"[INFO] API request successful, processing response.")
	
		try:
			data = response.json()
			results = data.get("results", [])
			
			if not results:
				safe_log(f"[WARNING] No results were returned from the API.")
		except ValueError as e:
			safe_log(f"[ERROR] Failed to parse API response as JSON: {str(e)}")
			safe_log(f"[DEBUG] Response content preview: {response.text[:200]}...")
			raise
	
		result_list = []
		for index, result in enumerate(results):
			try:
				current_molnix_id = result.get("molnix_id", "Unknown")
				
				safe_log(f"[INFO] Processing alert with molnix_id: {current_molnix_id} (index: {index})")
				
				molnix_tags = result.get("molnix_tags", [])
				if molnix_tags is None:
					molnix_tags = []
					safe_log(f"[WARNING] molnix_tags is None for molnix_id: {current_molnix_id}")
		
				sectors = []
				roles = []
		
				alert_id = result.get("id", None)
				molnix_id = result.get("molnix_id", None)
				alert_record_created_at = result.get("created_at", None)
				molnix_status = result.get("molnix_status", None)
				# the API's own "status_display" field has been deprecated and always
				# returns None now; "molnix_status_display" ("Open"/"Stood Down"/"Closed")
				# is the field that's actually populated.
				alert_status = result.get("molnix_status_display", None)
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
					if groups is None:
						groups = []
						tag_description = tag.get("description", "Unknown")
						safe_log(f"[WARNING] groups is None for tag: {tag_description} in molnix_id: {current_molnix_id}")
		
					if "REGION" in groups:
						region_id = tag.get("description", None)
		
					if "SECTOR" in groups:
						sector = tag.get("description", None)
						if sector:
							sectors.append(sector)
		
					if "ROLES" in groups:
						role_profile = tag.get("description", None)
						if role_profile:
							roles.append(role_profile)
		
					if "Modality" in groups:
						modality = tag.get("name", None)
		
					if "ALERT TYPE" in groups:
						scope_name = tag.get("name")
						if scope_name:
							scope = scope_name.title()
		
				im_filter = "Information Management" in sectors
		
				language_required = None
				rotation = None
				
				# safely find language required
				for tag in molnix_tags:
					if tag.get("tag_type") == "language":
						language_required = tag.get("description", None)
						break
						
				# safely find rotation
				for tag in molnix_tags:
					tag_groups = tag.get("groups", [])
					if tag_groups and "rotation" in tag_groups:
						rotation = tag.get("name", None)
						break
		
				country = result.get("country", {})
				if country is None:
					country = {}
					safe_log(f"[WARNING] country is None for molnix_id: {current_molnix_id}")
					
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
				if event is None:
					event = {}
					safe_log(f"[WARNING] event is None for molnix_id: {current_molnix_id}")
					
				dtype = event.get("dtype", {})
				if dtype is None:
					dtype = {}
					safe_log(f"[WARNING] dtype is None for molnix_id: {current_molnix_id}")
					
				disaster_type_id = dtype.get("id", None)
				disaster_type_name = dtype.get("name", None)
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
				
			except Exception as e:
				current_molnix_id = result.get("molnix_id", "Unknown")
				safe_log(f"[ERROR] Error processing alert with molnix_id: {current_molnix_id}, error: {str(e)}")
				continue
	
		for result in result_list:
			try:
				current_molnix_id = result.get('molnix_id', 'Unknown')
				current_alert_id = result.get('alert_id', 'Unknown')
				
				# handle potential None values in lists
				sectors = result.get('sectors', [])
				if sectors is None:
					sectors = []
				
				role_tags = result.get('role_tags', [])
				if role_tags is None:
					role_tags = []
				
				# join sectors and role_tags if they are lists
				if isinstance(sectors, list):
					result['sectors'] = ', '.join(sectors)
				
				if isinstance(role_tags, list):
					result['role_tags'] = ', '.join(role_tags)
		
				existing_alert = next((alert for alert in existing_alerts if alert.alert_id == result['alert_id']), None)
		
				if existing_alert:
					if existing_alert.alert_status != result['alert_status']:
						def _update_alert():
							existing_alert.alert_status = result['alert_status']
							db.session.commit()

						updated_ok, _ = with_db_retry(_update_alert)
						if updated_ok:
							count_updated_records += 1
							safe_log(f"[INFO] Updated alert_status for alert_id {result['alert_id']}, molnix_id: {current_molnix_id}.")
						else:
							safe_log(f"[ERROR] Failed to update alert_status for alert_id {result['alert_id']}, molnix_id: {current_molnix_id}.")

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
						except Exception as e:
							safe_log(f"[ERROR] Couldn't build alert object (alert_id={result['alert_id']}, molnix_id: {current_molnix_id}): {e}")
							continue

						def _add_alert():
							db.session.add(individual_alert)
							db.session.commit()

						added_ok, _ = with_db_retry(_add_alert)
						if added_ok:
							count_new_records += 1
							safe_log(f"[INFO] Added new alert with alert_id {individual_alert.alert_id}, molnix_id: {current_molnix_id}.")

							if individual_alert.im_filter:
								send_im_alert_to_slack(individual_alert)
						else:
							safe_log(f"[ERROR] Couldn't add alert (alert_id={result['alert_id']}, molnix_id: {current_molnix_id}) to the database.")
							
			except Exception as e:
				current_molnix_id = result.get('molnix_id', 'Unknown')
				safe_log(f"[ERROR] Error processing result with molnix_id: {current_molnix_id}, error: {str(e)}")
	
	except Exception as e:
		try:
			db.session.rollback()
		except:
			pass
		
		error_message = f"[ERROR] The Surge Alert cron job has failed: {e}."
		try:
			safe_log(error_message)
		except:
			print(error_message)
		
		send_error_message(error_message)
	finally:
		try:
			completion_message = f"[INFO] The Surge Alert cron job has finished. Added {count_new_records} new records and updated {count_updated_records} records."
			safe_log(completion_message)
		except Exception as final_e:
			print(f"Failed to log completion message: {str(final_e)}")
			send_error_message(f"Failed to log completion of Surge Alert cron job: {str(final_e)}")

def refresh_open_alert_statuses():
	"""
	Re-check the status of every alert we still consider unresolved (anything
	not already "Closed"), one at a time via the single-alert detail endpoint.

	refresh_surge_alerts_latest() only ever looks at the newest ~50 alerts (the
	list endpoint's default ordering is always newest-created-first, and its
	"ordering" query parameter has no effect no matter what field you pass it -
	confirmed directly against the live API). An alert that closes weeks after
	being created scrolls off that page long before it closes, and its status
	then goes stale forever under that function alone. This targets exactly the
	alerts we still think are open, so it scales with how many are actually
	outstanding rather than with the full alert history.

	Parameters:
	None

	Returns:
	None

	Side Effects:
	- Logs information and errors to the database.
	- Updates alert_status (and molnix_status) on existing alert records.
	"""
	count_checked = 0
	count_updated = 0

	def _fetch_unresolved_alerts():
		return db.session.query(Alert).filter(Alert.alert_status != 'Closed').all()

	fetched_ok, unresolved_alerts = with_db_retry(
		_fetch_unresolved_alerts,
		on_give_up=lambda e: safe_log(f"[ERROR] refresh_open_alert_statuses couldn't fetch unresolved alerts: {e}")
	)
	if not fetched_ok:
		return

	safe_log(f"[INFO] refresh_open_alert_statuses checking {len(unresolved_alerts)} unresolved alerts.")

	for alert in unresolved_alerts:
		if not alert.alert_id:
			continue

		try:
			response = requests.get(f"https://goadmin.ifrc.org/api/v2/surge_alert/{alert.alert_id}/", timeout=15)
			response.raise_for_status()
			data = response.json()
		except RequestException as e:
			safe_log(f"[WARNING] refresh_open_alert_statuses couldn't fetch alert_id {alert.alert_id}: {e}")
			continue
		except ValueError as e:
			safe_log(f"[WARNING] refresh_open_alert_statuses got an unparseable response for alert_id {alert.alert_id}: {e}")
			continue

		count_checked += 1
		new_status = data.get("molnix_status_display", None)
		new_molnix_status = data.get("molnix_status", None)
		old_status = alert.alert_status

		if new_status and new_status != old_status:
			def _update_status():
				alert.alert_status = new_status
				if new_molnix_status is not None:
					alert.molnix_status = new_molnix_status
				db.session.commit()

			updated_ok, _ = with_db_retry(_update_status)
			if updated_ok:
				count_updated += 1
				safe_log(f"[INFO] refresh_open_alert_statuses updated alert_id {alert.alert_id}: {old_status} -> {new_status}.")
			else:
				safe_log(f"[ERROR] refresh_open_alert_statuses failed to save the updated status for alert_id {alert.alert_id}.")

		time.sleep(0.2)  # be polite to the external API when checking many alerts individually

	safe_log(f"[INFO] refresh_open_alert_statuses finished. Checked {count_checked} alerts, updated {count_updated}.")

def refresh_surge_alerts(pages_to_fetch=100):
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
	
	count_new_records = 0
	count_updated_records = 0

	try:
		safe_log(f"[INFO] The Surge Alert (full version) function has started.")

		def _fetch_existing_alerts():
			return db.session.query(Alert).order_by(Alert.molnix_id.desc()).all()

		fetched_ok, existing_alerts = with_db_retry(
			_fetch_existing_alerts,
			on_give_up=lambda e: safe_log(f"[ERROR] Failed to fetch existing alerts: {e}")
		)
		if not fetched_ok:
			existing_alerts = []
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
				molnix_tags = result.get("molnix_tags", []) or []

				sectors = []
				roles = []
				
				alert_id = result.get("id", None)
				molnix_id = result.get("molnix_id", None)
				alert_record_created_at = result.get("created_at", None)
				molnix_status = result.get("molnix_status", None)
				# the API's own "status_display" field has been deprecated and always
				# returns None now; "molnix_status_display" ("Open"/"Stood Down"/"Closed")
				# is the field that's actually populated.
				alert_status = result.get("molnix_status_display", None)
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
					groups = tag.get("groups", []) or []

					if "SECTOR" in groups:
						sector = tag.get("description", None)
						sectors.append(sector)

					if "ROLES" in groups:
						role_profile = tag.get("description", None)
						roles.append(role_profile)

					if "Modality" in groups:
						modality = tag.get("name", None)

					if "ALERT TYPE" in groups:
						scope_name = tag.get("name")
						if scope_name:
							scope = scope_name.title()

				im_filter = "Information Management" in sectors

				language_required = next((tag.get("description", None) for tag in molnix_tags if tag.get("tag_type") == "language"), None)
				rotation = next((group.get("name", None) for group in molnix_tags if "rotation" in (group.get("groups") or [])), None)

				country = result.get("country", {}) or {}
				iso3 = country.get("iso3", None)
				country_name = country.get("name", None)

				event = result.get("event", {}) or {}
				dtype = event.get("dtype", {}) or {}
				disaster_type_id = dtype.get("id", None)
				disaster_type_name = dtype.get("name", None)
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
		
		for result in result_list:

			# these fields can have multiple values, so strip curly brackets and save as comma-separated strings
			result['sectors'] = ', '.join(result['sectors'])
			result['role_tags'] = ', '.join(result['role_tags'])

			existing_alert = next((alert for alert in existing_alerts if alert.alert_id == result['alert_id']), None)

			if existing_alert:
				# check if alert_status has changed
				if existing_alert.alert_status != result['alert_status']:
					def _update_alert():
						existing_alert.alert_status = result['alert_status']
						db.session.commit()

					updated_ok, _ = with_db_retry(_update_alert)
					if updated_ok:
						count_updated_records += 1
					else:
						safe_log(f"[ERROR] Failed to update alert_status for alert_id {result['alert_id']}.")

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
						safe_log(f"[WARNING] The refresh_surge_alerts (full version) function couldn't parse one of the alerts it found in the Surge Alert cron job as it tried to instantiate a new Alert object: {e}")
						continue

					def _add_alert():
						db.session.add(individual_alert)
						db.session.commit()

					added_ok, _ = with_db_retry(_add_alert)
					if added_ok:
						count_new_records += 1
					else:
						safe_log(f"[ERROR] The refresh_surge_alerts (full version) function couldn't add one of the alerts (alert_id={result['alert_id']}) to the database.")

	except Exception as e:
		safe_log(f"[ERROR] The Surge Alert (full version) cron job has failed: {e}.")
		send_error_message(f"[ERROR] The Surge Alert (full version) cron job has failed: {e}.")

	safe_log(f"[INFO] The Surge Alert (full version) cron job has finished and logged {count_new_records} new records.")