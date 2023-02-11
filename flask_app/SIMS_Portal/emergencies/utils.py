from flask import url_for, current_app, flash, redirect
from SIMS_Portal import db
from SIMS_Portal.models import User, Assignment, Emergency, NationalSociety
from slack_sdk import WebClient
import os
import csv
import logging

def update_response_locations():
	"""
	Updates a CSV file with all countries' ISO3 codes and the count of emergencies to which SIMS has responded there.
	"""
	response_locations = db.engine.execute("SELECT iso3, count(*) AS count_location FROM nationalsociety JOIN emergency ON emergency_location_id = nationalsociety.ns_go_id GROUP BY iso3")
	
	list_of_location_dicts = []
	for location in response_locations:
		locations_dict = {}
		locations_dict['iso3'] = location[0]
		locations_dict['count'] = location[1]
		list_of_location_dicts.append(locations_dict)
	csv_file_path = "SIMS_Portal/static/data/emergencies_viz.csv"
	keys = ('iso3', 'count')
	with open(csv_file_path, 'w') as outfile:
		dict_writer = csv.DictWriter(outfile, keys)
		dict_writer.writeheader()
		dict_writer.writerows(list_of_location_dicts)
		outfile.close()
	
	current_app.logger.info('The update_response_locations function ran successfully.')
	
def update_active_response_locations():
	"""
	Updates a CSV file with all countries' ISO3 codes of active emergencies to which SIMS is currently responding.
	"""
	# active_response_locations = db.session.query(Emergency, NationalSociety).join(NationalSociety.ns_go_id == Emergency.emergency_location_id).filter(Emergency.emergency_status == 'Active').all()
	active_response_locations = db.engine.execute("SELECT * FROM emergency JOIN nationalsociety ON nationalsociety.ns_go_id = emergency.emergency_location_id WHERE emergency.emergency_status = 'Active'")
	
	list_of_location_dicts = []
	for location in active_response_locations:
		locations_dict = {}
		locations_dict['iso3'] = location.iso3
		locations_dict['count'] = 1
		list_of_location_dicts.append(locations_dict)
	csv_file_path = "SIMS_Portal/static/data/active_emergencies.csv"
	keys = ('iso3', 'count')
	with open(csv_file_path, 'w') as outfile:
		dict_writer = csv.DictWriter(outfile, keys)
		dict_writer.writeheader()
		dict_writer.writerows(list_of_location_dicts)
		outfile.close()
	
	current_app.logger.info('The update_active_response_locations function ran successfully.')