from SIMS_Portal import db
from SIMS_Portal.models import Assignment, Emergency
from collections import Counter
from datetime import datetime
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
