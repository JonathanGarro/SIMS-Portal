from datetime import datetime, timedelta
from flask import current_app
from flask_login import current_user
from SIMS_Portal import db
from sqlalchemy import text
from SIMS_Portal.models import NationalSociety, EmergencyType, Log
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import re

def create_response_channel(location, disaster_type):
	"""
	Create a Slack response channel for a given location and disaster type.
	
	Constructs a channel name using the location's ISO3 code, the current year, and the disaster type.
	It then creates a public Slack channel with this name and logs the operation's success or failure.
	
	Parameters:
	location (int): The location ID (National Society Go ID) for which the channel is created.
	disaster_type (int): The disaster type ID (Emergency Type Go ID) for which the channel is created.
	
	Returns:
	str: The ID of the created Slack channel if successful.
	
	Side Effects:
	- Creates a new public Slack channel.
	- Logs success or error messages to the database.
	
	Raises:
	None
	"""
	
	# grab iso3 and year for channel name constructor
	iso3 = db.session.query(NationalSociety.iso3).filter(NationalSociety.ns_go_id == location).scalar().lower()
	current_year = datetime.now().year
	emergency_type = db.session.query(EmergencyType.emergency_type_name).filter(EmergencyType.emergency_type_go_id == disaster_type).scalar().lower()
	
	# substitute underscores for spaces in emergency_type
	emergency_type = emergency_type.replace(' ', '_')
	
	client = WebClient(token = current_app.config['SIMS_PORTAL_SLACK_BOT'])
	
	try:
		response = client.conversations_create(
			name=f'{current_year}_{iso3}_{emergency_type}',
			is_private=False  
		)
		log_message = f"[INFO] create_response_channel() successfully ran and created channel {response['channel']['id']}."
		new_log = Log(message=log_message, user_id=current_user.id)
		db.session.add(new_log)
		db.session.commit()
		
		return response['channel']['id']
		
	except SlackApiError as e:
		log_message = f"[Error] create_response_channel() utility failed: {e}. It tried to create a channel called: {current_year}_{iso3}_{emergency_type}"
		new_log = Log(message=log_message, user_id=current_user.id)
		db.session.add(new_log)
		db.session.commit()

	
	

def emergency_availability_chart_data(dis_id):
	"""
	Generate chart data for emergency availability for the current week.
	
	Retrieves and processes availability data for a given disaster ID, calculates the frequency
	of available dates for the current week, and formats the data for chart visualization.
	
	Parameters:
	dis_id (int): The ID of the disaster for which to generate availability chart data.
	
	Returns:
	tuple: A tuple containing:
		- formatted_week_dates (list of str): A list of date strings representing each day of the current week.
		- frequency_count (list of int): A list of counts of availability for each corresponding date.
	
	Side Effects:
	None
	
	Raises:
	None
	"""
	
	current_year = datetime.now().year
	current_week = datetime.today().isocalendar()[1]
	year_week = f"{current_year}-{current_week}"
	
	data = db.session.execute(text("SELECT u.id, STRING_AGG(DISTINCT p.name, ', ') AS profile_names, STRING_AGG(DISTINCT a.dates, '; ') AS associated_dates FROM public.user u JOIN public.user_profile up ON up.user_id = u.id JOIN public.profile p ON up.profile_id = p.id JOIN public.availability a ON a.user_id = u.id WHERE a.timeframe = :timeframe AND a.emergency_id = :emergency_id GROUP BY u.id, a.timeframe"), {'timeframe': str(year_week), 'emergency_id': dis_id})
	
	current_date = datetime.now().date()
	start_of_week = current_date - timedelta(days=current_date.weekday())
	week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
	
	current_year = datetime.now().year
	
	date_list = []
	for row in data:
		item = row.associated_dates
		extracted_values = re.findall(r'[A-Za-z]+\s+\d+', item)
		for value in extracted_values:
			date_string = value.strip()
			date_object = datetime.strptime(date_string, "%B %d").date().replace(year=current_year)
			date_list.append(date_object)
	
	frequency_count = [date_list.count(week_date) for week_date in week_dates]
	
	formatted_week_dates = [week_date.strftime("%Y-%m-%d") for week_date in week_dates]
	
	return formatted_week_dates, frequency_count

