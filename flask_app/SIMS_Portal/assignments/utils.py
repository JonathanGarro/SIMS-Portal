from SIMS_Portal import db
from SIMS_Portal.models import Assignment, Emergency
from collections import Counter
from datetime import datetime, timedelta
import json

def aggregate_availability(dis_id):
	"""
	Aggregate and structure availability data for a given disaster ID.
	
	Retrieves availability data from the database based on the provided disaster ID, aggregates
	the data, and structures it for front-end visualization. It processes the data to count occurrences of 
	availability dates and formats them for better readability.
	
	Parameters:
	dis_id (int): The ID of the disaster for which to aggregate availability data.
	
	Returns:
	tuple: A tuple containing:
		- values (list): A list of counts of availability dates.
		- labels (list): A list of formatted date labels corresponding to the availability counts.
	
	Side Effects:
	None
	
	Raises:
	None
	"""
	
	# get data from db
	data = db.session.query(Assignment, Emergency).join(Emergency, Emergency.id == Assignment.emergency_id).with_entities(Assignment.availability).filter(Emergency.id == dis_id, Assignment.availability != None, Assignment.assignment_status != 'Removed').all()
	
	# loop over nested data and strip out extra characters on merge
	list_full = []
	for x in data:
		for y in x:
			for z in y.split(', '):
				list_full.append(z.replace('[','').replace(']','').replace("'",''))
	
	# convert list to Counter object
	output = Counter(list_full)
	
	# create list of dictionaries that converts date strings to datetime for better readability
	holder_list = []
	for key, val in output.items():
		temp_dict = {}
		date = datetime.strptime(key, '%Y-%m-%d')
		temp_dict['day_of_week'] = date.strftime('%A') + ' - ' + date.strftime('%b') + ' ' + date.strftime('%d')
		temp_dict['count'] = val
		holder_list.append(temp_dict)
	
	# package data for visualization in json format
	output = json.dumps(holder_list)
	values = []
	labels = []
	for x in holder_list:
		values.append(x['count'])
		labels.append(x['day_of_week'])
		
	return values, labels

def get_dates_current_and_next_week():
	"""
	Get dates for the current and next week starting from today.
	
	This function calculates the dates for the current week starting from today and the entire next week.
	It returns a zip object containing tuples of date objects and their corresponding readable string formats.
	
	Parameters:
	None
	
	Returns:
	zip: A zip object containing tuples of:
		- dates (list of date): Date objects for the current and next week.
		- readable_dates (list of str): Readable string formats of the corresponding dates.
	
	Side Effects:
	None
	
	Raises:
	None
	"""
	
	today = datetime.now().date()
	current_week_start = today - timedelta(days=today.weekday())
	next_week_start = current_week_start + timedelta(days=7)
	
	dates = []
	for i in range(14):
		current_date = current_week_start + timedelta(days=i)
		if current_date >= today:
			dates.append(current_date)
	
	readable_dates = []
	for date in dates:
		readable_dates.append(f"{date.strftime('%A')}, {date.strftime('%B')} {date.day}")
		
	zip_dates = zip(dates,readable_dates)
	
	return zip_dates