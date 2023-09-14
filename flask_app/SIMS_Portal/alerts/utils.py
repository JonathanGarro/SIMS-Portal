from SIMS_Portal import db
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from SIMS_Portal.models import Alert
from SIMS_Portal.users.utils import new_surge_alert
from flask_apscheduler import APScheduler
import datetime
import math
import requests
import logging
import re

scheduler = APScheduler()

tags_list = ['ADMIN-CO', 'ASSESS-CO', 'CEA- RCCE', 'CEA-CO', 'CEA-OF', 'CIVMILCO', 'COM-TL', 'COMCO', 'COMOF', 'COMPH', 'COMVID', 'CVACO', 'CVAOF', 'DEP-OPMGR', 'DRR-CO', 'EAREC-OF', 'FA Of', 'FIELDCO', 'FIN-CO', 'HEALTH-CO', 'HEALTH-ETL', 'HEOPS', 'HRCO', 'HR-OF', 'HUMLIAS', 'IDRLCO', 'IM-CO', 'IM-PDC', 'IM-VIZ', 'IMANALYST', 'ITT-CO', 'ITT-OF', 'LIVECO', 'LIVEINCM', 'LIVEMRKT', 'LOG-CO', 'LOG-ETL', 'LOG-OF', 'LOGADMIN', 'LOGAIROPS', 'LOGCASH', 'LOGFLEET', 'LOGPIPELINE', 'LOGPROC', 'LOGWARE', 'MDHEALTH-CO', 'MEDLOG', 'MIG-CO', 'MOVCO', 'NSDCO', 'NSDVOL', 'OPMGR', 'PER-CO', 'PER-OF', 'PGI-CO', 'PGI-OF', 'PHEALTH-CO', 'PMER-CO', 'PMER-OF', 'PRD-NS', 'PRD-OF', 'PSS-CO', 'PSS-ERU', 'PSS-OF', 'PSSCMTY', 'RECCO', 'RELCO', 'RELOF', 'SEC-CO', 'SHCLUSTER-CO', 'SHCLUSTER-DEP', 'SHCLUSTER-ENV', 'SHCLUSTER-HUB', 'SHCLUSTER-IM', 'SHCLUSTER-REC', 'SHCLUSTER-TEC', 'SHELTERP-CB', 'SHELTERP-CO', 'SHELTERP-SP', 'SHELTERP-TEC', 'SHELTERP-TL', 'SIMSCo', 'STAFFHEALTH', 'WASH-CO', 'WASH-ENG', 'WASH-ETL', 'WASH-HP', 'WASH-OF', 'WASH-SAN', 'WASH-TEC']

# same as molnix tags, this list must be manually updated
im_tags = ['IM-CO', 'IM-PDC', 'IM-VIZ', 'IMANALYST', 'SIMSCo']

region_list = ['AFRICA', 'ASIAP', 'AMER', 'EURO', 'MENA']

scope_list = ['REGIONAL', 'GLOBAL']

def refresh_surge_alerts_latest():
	"""
	Queries the GO API to get the latest surge alerts. This version of the function only looks at the latest page in the results. If this function is run daily, that should catch all alerts that come out. To run the same version of this function but loop through all pages, use the `refresh_surge_alerts()` function available in this same utility file.
	"""
	
	try:
		current_app.logger.info('Surge Alert GO API query started.')
		existing_alerts = db.session.query(Alert).order_by(Alert.alert_id.desc()).all()
		existing_alert_ids = []
		existing_statuses = []
		for alert in existing_alerts:
			existing_alert_ids.append(alert.alert_id)
			temp_dict = {}
			temp_dict['alert_id'] = alert.alert_id
			temp_dict['alert_status'] = alert.alert_status
			existing_statuses.append(temp_dict)
		
		api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
		r = requests.get(api_call).json()
		
		# page flipper for paginated surge alerts
		current_page = 1
		page_count = int(math.ceil(r['count'] / 50))
		current_app.logger.info('Surge Alert GO API query run, returned {} pages.'.format(page_count))
		
		output = []
		
		for x in r['results']:
			temp_dict = {}
			if x['molnix_tags']:
				for y in x['molnix_tags']:
					if y['name'] in tags_list:
						if y['name'] in im_tags:
							temp_dict['im_filter'] = 1
						else:
							temp_dict['im_filter'] = 0 
						temp_dict['role_profile'] = y['description']
						try:
							temp_dict['alert_date'] = datetime.datetime.strptime(x['opens'], "%Y-%m-%dT%H:%M:%SZ")
						except:
							# surge team imported old alerts without 'opens' data that requires this fallback
							temp_dict['alert_date'] = datetime.datetime.strptime('1900-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%SZ")
						if x['start']:
							temp_dict['start'] = datetime.datetime.strptime(x['start'], "%Y-%m-%dT%H:%M:%SZ")
						else:
							temp_dict['start'] = datetime.datetime.strptime('1900-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%SZ")
						if x['end']:
							temp_dict['end'] = datetime.datetime.strptime(x['end'], "%Y-%m-%dT%H:%M:%SZ")
						else:
							temp_dict['end'] = datetime.datetime.strptime('1900-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%SZ")	
						temp_dict['alert_id'] = x['id']
						temp_dict['molnix_id'] = x['molnix_id']
						temp_dict['alert_status'] = x['molnix_status']
						if x['event']:
							temp_dict['event_name'] = x['event']['name']
							try:
								temp_dict['severity'] = x['event']['ifrc_severity_level_display']
							except:
								temp_dict['severity'] = 'n/a'
							temp_dict['event_go_id'] = x['event']['id']
							temp_dict['event_date'] = datetime.datetime.strptime(x['event']['disaster_start_date'], "%Y-%m-%dT%H:%M:%SZ")
							if x['country']:
								temp_dict['country'] = x['country']['name']
								try:
									temp_dict['iso3'] = x['country']['iso3']
								except:
									temp_dict['iso3'] = ''
							else:
								temp_dict['country'] = 'MISSING COUNTRY'
								temp_dict['iso3'] = 'ZZZ'
						else:
							temp_dict['event_name'] = 'MISSING EMERGENCY'
							temp_dict['severity'] = 'MISSING EMERGENCY'
							temp_dict['event_go_id'] = 0
							temp_dict['event_date'] = datetime.date(2000, 1, 1)
							temp_dict['country'] = 'MISSING EMERGENCY'
							temp_dict['iso3'] = 'MISSING EMERGENCY'
				for y in x['molnix_tags']:
					if y['name'] in region_list:
						try:
							if y['name'] == 'AFRICA':
								temp_dict['region'] = 'Africa'
							elif y['name'] == 'AMER':
								temp_dict['region'] = 'Americas'
							elif y['name'] == 'ASIAP':
								temp_dict['region'] = 'Asia Pacific'
							elif y['name'] == 'EURO':
								temp_dict['region'] = 'Europe'
							elif y['name'] == 'MENA':
								temp_dict['region'] = 'Middle East and North Africa'
							else:
								temp_dict['region'] = 'MISSING'
						except:
							pass
				for y in x['molnix_tags']:
					if y['name'] in scope_list:
						try:
							if y['name'] == 'REGIONAL':
								temp_dict['scope'] = 'Regional'
							elif y['name'] == 'GLOBAL':
								temp_dict['scope'] = 'Global'
						except:
							temp_dict['scope'] = 'MISSING'

			if temp_dict.get('alert_id') is not None:
				output.append(temp_dict)
				
		if r['next']:
			next_page = requests.get(r['next']).json()
			r = next_page
			current_page += 1

		
		count_new_records = 0
		
		# add new records
		for alert in output:
			if alert and alert['alert_id'] not in existing_alert_ids:
				try:
					individual_alert = Alert(
						im_filter = alert['im_filter'],
						role_profile = alert['role_profile'],
						alert_date = alert['alert_date'],
						start = alert['start'],
						end = alert['end'],
						alert_id = alert['alert_id'],
						molnix_id = alert['molnix_id'],
						alert_status = alert['alert_status'],
						event_name = alert['event_name'],
						severity = alert['severity'],
						event_go_id = alert['event_go_id'],
						event_date = alert['event_date'],
						country = alert['country'],
						iso3 = alert['iso3'],
						region = alert['region'],
						scope = alert['scope']
					)
				except KeyError as e:
					caused_key = e.args[0]
					if caused_key == 'scope':
						try:
							individual_alert = Alert(
								im_filter = alert['im_filter'],
								role_profile = alert['role_profile'],
								alert_date = alert['alert_date'],
								start = alert['start'],
								end = alert['end'],
								alert_id = alert['alert_id'],
								molnix_id = alert['molnix_id'],
								alert_status = alert['alert_status'],
								event_name = alert['event_name'],
								severity = alert['severity'],
								event_go_id = alert['event_go_id'],
								event_date = alert['event_date'],
								country = alert['country'],
								iso3 = alert['iso3'],
								region = alert['region'],
								scope = 'MISSING'
							)
						except:
							pass
					elif caused_key == 'region':
						try:
							individual_alert = Alert(
								im_filter = alert['im_filter'],
								role_profile = alert['role_profile'],
								alert_date = alert['alert_date'],
								start = alert['start'],
								end = alert['end'],
								alert_id = alert['alert_id'],
								molnix_id = alert['molnix_id'],
								alert_status = alert['alert_status'],
								event_name = alert['event_name'],
								severity = alert['severity'],
								event_go_id = alert['event_go_id'],
								event_date = alert['event_date'],
								country = alert['country'],
								iso3 = alert['iso3'],
								region = 'MISSING',
								scope = alert['scope']
							)
						except:
							pass
					else:
						try:
							individual_alert = Alert(
								im_filter = alert['im_filter'],
								role_profile = alert['role_profile'],
								alert_date = alert['alert_date'],
								start = alert['start'],
								end = alert['end'],
								alert_id = alert['alert_id'],
								molnix_id = alert['molnix_id'],
								alert_status = alert['alert_status'],
								event_name = alert['event_name'],
								severity = alert['severity'],
								event_go_id = alert['event_go_id'],
								event_date = alert['event_date'],
								country = alert['country'],
								iso3 = alert['iso3'],
								region = 'MISSING',
								scope = 'MISSING'
							)
						except:
							pass
				
				if alert['im_filter'] == 1:
					# send IM alerts to the availability channel in SIMS slack
					try:
						# convert emergency classification to emoji
						colors_to_emoji = {'Red': 'a :red_circle: red', 'Orange': 'an :large_orange_circle: orange', 'Yellow': 'a :large_yellow_circle: yellow'}
						# link to ifrc sharepoint's file on the role profile
						standard_profiles = {
							'Information Management Coordinator': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/Ea_YRhCI_IJHkhISEh5zH2YBCUtMAdWUqiC8JH7g1Jj8AQ', 
							'Humanitarian Information Analysis Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/EYUNi8qR395Oq3Ng3SHbsXMBUbS4XdfVw03tECGEb828Nw', 
							'Primary Data Collection Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/EdB7tgvjH5dApy5PcFNZcx0BzGKQJfS2nP-L3CFKRdr5Ow', 
							'Mapping and Data Visualization Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/ER92aBZKBpxHrH61MJf4hLEBxwEnqzfqjLVR7cscPlxDKA',
							'SIMS Remote Coordinator': 'https://go.ifrc.org/deployments/catalogue/infoMgt'
						}
						# construct message
						if alert['scope'] == 'Global':
							message = '\n:rotating_light: *New Global Information Management Surge Alert Released!* :rotating_light:\n\n The following Rapid Response profile has been requested for <https://go.ifrc.org/emergencies/{}|*{}*>, which is {} emergency.\n\n • 1 x *{}*, based in {}, with a desired start date of {}.\n\nYou can find the standard role profile for this position <{}|here>.'.format(alert['event_go_id'], alert['event_name'], colors_to_emoji[alert['severity']], alert['role_profile'], alert['country'], alert['start'].strftime("%B %d"), standard_profiles[alert['role_profile']])
						if alert['scope'] == 'Regional':
							message = "\n*New Regional Information Management Surge Alert Released!*\n\n The {} region has released the following Rapid Response surge alert for <https://go.ifrc.org/emergencies/{}|*{}*>, which is {} emergency.\n\n • 1 x *{}*, based in {}, with a desired start date of {}.\n\n*This is a regional alert only,* and is not being triaged globally. This message is for the SIMS Network's situational awareness only.\n\nYou can find the standard role profile for this position <{}|here>.".format(alert['region'], alert['event_go_id'], alert['event_name'], colors_to_emoji[alert['severity']], alert['role_profile'], alert['country'], alert['start'].strftime("%B %d"), standard_profiles[alert['role_profile']])
						# fire off alert
						new_surge_alert(message)
					# skip if slack api not responsive
					except Exception as e: 
						current_app.logger.error('Send IM Surge Alert to Slack failed: {}'.format(e))
				try:
					db.session.add(individual_alert)
					db.session.commit()
					count_new_records += 1
				except:
					pass
	except Exception as e:
		current_app.logger.error('Surge Alert (Latest) GO API Query Failed: {}'.format(e))
	
	current_app.logger.info('Surge Alert GO API query finished, logged {} new records.'.format(count_new_records))	

def refresh_surge_alerts():
	"""
	Queries the GO API to get the latest surge alerts. This version of the function loops through all pages in the database. For a faster version of this function, use `refresh_surge_alerts_latest`, which will only look at the most recent page, and should still catch all new alerts if it is run at least once per day.
	"""
	try:
		current_app.logger.info('Surge Alert GO API query started.')
		existing_alerts = db.session.query(Alert).order_by(Alert.alert_id.desc()).all()
		existing_alert_ids = []
		existing_statuses = []
		for alert in existing_alerts:
			existing_alert_ids.append(alert.alert_id)
			temp_dict = {}
			temp_dict['alert_id'] = alert.alert_id
			temp_dict['alert_status'] = alert.alert_status
			existing_statuses.append(temp_dict)
		
		api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
		r = requests.get(api_call).json()
		
		# page flipper for paginated surge alerts
		current_page = 1
		page_count = int(math.ceil(r['count'] / 50))
		current_app.logger.info('Surge Alert GO API query run, returned {} pages.'.format(page_count))
		
		output = []
		
		while current_page <= page_count:
			for x in r['results']:
				temp_dict = {}
				if x['molnix_tags']:
					for y in x['molnix_tags']:
						if y['name'] in tags_list:
							if y['name'] in im_tags:
								temp_dict['im_filter'] = 1
							else:
								temp_dict['im_filter'] = 0 
							temp_dict['role_profile'] = y['description']
							try:
								temp_dict['alert_date'] = datetime.datetime.strptime(x['opens'], "%Y-%m-%dT%H:%M:%SZ")
							except:
								# surge team imported old alerts without 'opens' data that requires this fallback
								temp_dict['alert_date'] = datetime.datetime.strptime('1900-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%SZ")
							if x['start']:
								temp_dict['start'] = datetime.datetime.strptime(x['start'], "%Y-%m-%dT%H:%M:%SZ")
							else:
								temp_dict['start'] = datetime.datetime.strptime('1900-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%SZ")
							if x['end']:
								temp_dict['end'] = datetime.datetime.strptime(x['end'], "%Y-%m-%dT%H:%M:%SZ")
							else:
								temp_dict['end'] = datetime.datetime.strptime('1900-01-01T00:00:00Z', "%Y-%m-%dT%H:%M:%SZ")	
							temp_dict['alert_id'] = x['id']
							temp_dict['molnix_id'] = x['molnix_id']
							temp_dict['alert_status'] = x['molnix_status']
							if x['event']:
								temp_dict['event_name'] = x['event']['name']
								try:
									temp_dict['severity'] = x['event']['ifrc_severity_level_display']
								except:
									temp_dict['severity'] = 'n/a'
								temp_dict['event_go_id'] = x['event']['id']
								temp_dict['event_date'] = datetime.datetime.strptime(x['event']['disaster_start_date'], "%Y-%m-%dT%H:%M:%SZ")
								if x['country']:
									temp_dict['country'] = x['country']['name']
									try:
										temp_dict['iso3'] = x['country']['iso3']
									except:
										temp_dict['iso3'] = ''
								else:
									temp_dict['country'] = 'MISSING COUNTRY'
									temp_dict['iso3'] = 'ZZZ'
							else:
								temp_dict['event_name'] = 'MISSING EMERGENCY'
								temp_dict['severity'] = 'MISSING EMERGENCY'
								temp_dict['event_go_id'] = 0
								temp_dict['event_date'] = datetime.date(2000, 1, 1)
								temp_dict['country'] = 'MISSING EMERGENCY'
								temp_dict['iso3'] = 'MISSING EMERGENCY'
					for y in x['molnix_tags']:
						if y['name'] in region_list:
							try:
								if y['name'] == 'AFRICA':
									temp_dict['region'] = 'Africa'
								elif y['name'] == 'AMER':
									temp_dict['region'] = 'Americas'
								elif y['name'] == 'ASIAP':
									temp_dict['region'] = 'Asia Pacific'
								elif y['name'] == 'EURO':
									temp_dict['region'] = 'Europe'
								elif y['name'] == 'MENA':
									temp_dict['region'] = 'Middle East and North Africa'
								else:
									temp_dict['region'] = 'MISSING'
							except:
								pass
					for y in x['molnix_tags']:
						if y['name'] in scope_list:
							try:
								if y['name'] == 'REGIONAL':
									temp_dict['scope'] = 'Regional'
								elif y['name'] == 'GLOBAL':
									temp_dict['scope'] = 'Global'
							except:
								temp_dict['scope'] = 'MISSING'
	
				if temp_dict.get('alert_id') is not None:
					output.append(temp_dict)
					
			if r['next']:
				next_page = requests.get(r['next']).json()
				r = next_page
				current_page += 1
			else:
				break
		
		count_new_records = 0
		
		# add new records
		for alert in output:
			if alert and alert['alert_id'] not in existing_alert_ids:
				try:
					individual_alert = Alert(
						im_filter = alert['im_filter'],
						role_profile = alert['role_profile'],
						alert_date = alert['alert_date'],
						start = alert['start'],
						end = alert['end'],
						alert_id = alert['alert_id'],
						molnix_id = alert['molnix_id'],
						alert_status = alert['alert_status'],
						event_name = alert['event_name'],
						severity = alert['severity'],
						event_go_id = alert['event_go_id'],
						event_date = alert['event_date'],
						country = alert['country'],
						iso3 = alert['iso3'],
						region = alert['region'],
						scope = alert['scope']
					)
				except KeyError as e:
					caused_key = e.args[0]
					if caused_key == 'scope':
						try:
							individual_alert = Alert(
								im_filter = alert['im_filter'],
								role_profile = alert['role_profile'],
								alert_date = alert['alert_date'],
								start = alert['start'],
								end = alert['end'],
								alert_id = alert['alert_id'],
								molnix_id = alert['molnix_id'],
								alert_status = alert['alert_status'],
								event_name = alert['event_name'],
								severity = alert['severity'],
								event_go_id = alert['event_go_id'],
								event_date = alert['event_date'],
								country = alert['country'],
								iso3 = alert['iso3'],
								region = alert['region'],
								scope = 'MISSING'
							)
						except:
							pass
					elif caused_key == 'region':
						try:
							individual_alert = Alert(
								im_filter = alert['im_filter'],
								role_profile = alert['role_profile'],
								alert_date = alert['alert_date'],
								start = alert['start'],
								end = alert['end'],
								alert_id = alert['alert_id'],
								molnix_id = alert['molnix_id'],
								alert_status = alert['alert_status'],
								event_name = alert['event_name'],
								severity = alert['severity'],
								event_go_id = alert['event_go_id'],
								event_date = alert['event_date'],
								country = alert['country'],
								iso3 = alert['iso3'],
								region = 'MISSING',
								scope = alert['scope']
							)
						except:
							pass
					else:
						try:
							individual_alert = Alert(
								im_filter = alert['im_filter'],
								role_profile = alert['role_profile'],
								alert_date = alert['alert_date'],
								start = alert['start'],
								end = alert['end'],
								alert_id = alert['alert_id'],
								molnix_id = alert['molnix_id'],
								alert_status = alert['alert_status'],
								event_name = alert['event_name'],
								severity = alert['severity'],
								event_go_id = alert['event_go_id'],
								event_date = alert['event_date'],
								country = alert['country'],
								iso3 = alert['iso3'],
								region = 'MISSING',
								scope = 'MISSING'
							)
						except:
							pass
				
				if alert['im_filter'] == 1:
					# send IM alerts to the availability channel in SIMS slack
					try:
						# convert emergency classification to emoji
						colors_to_emoji = {'Red': 'a :red_circle: red', 'Orange': 'an :large_orange_circle: orange', 'Yellow': 'a :large_yellow_circle: yellow'}
						# link to ifrc sharepoint's file on the role profile
						standard_profiles = {
							'Information Management Coordinator': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/Ea_YRhCI_IJHkhISEh5zH2YBCUtMAdWUqiC8JH7g1Jj8AQ', 
							'Humanitarian Information Analysis Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/EYUNi8qR395Oq3Ng3SHbsXMBUbS4XdfVw03tECGEb828Nw', 
							'Primary Data Collection Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/EdB7tgvjH5dApy5PcFNZcx0BzGKQJfS2nP-L3CFKRdr5Ow', 
							'Mapping and Data Visualization Officer': 'https://ifrcorg.sharepoint.com/:b:/s/IFRCSharing/ER92aBZKBpxHrH61MJf4hLEBxwEnqzfqjLVR7cscPlxDKA',
							'SIMS Remote Coordinator': 'https://go.ifrc.org/deployments/catalogue/infoMgt'
						}
						# construct message
						if alert['scope'] == 'Global':
							message = '\n:rotating_light: *New Global Information Management Surge Alert Released!* :rotating_light:\n\n The following Rapid Response profile has been requested for <https://go.ifrc.org/emergencies/{}|*{}*>, which is {} emergency.\n\n • 1 x *{}*, based in {}, with a desired start date of {}.\n\nYou can find the standard role profile for this position <{}|here>.'.format(alert['event_go_id'], alert['event_name'], colors_to_emoji[alert['severity']], alert['role_profile'], alert['country'], alert['start'].strftime("%B %d"), standard_profiles[alert['role_profile']])
						if alert['scope'] == 'Regional':
							message = "\n*New Regional Information Management Surge Alert Released!*\n\n The {} region has released the following Rapid Response surge alert for <https://go.ifrc.org/emergencies/{}|*{}*>, which is {} emergency.\n\n • 1 x *{}*, based in {}, with a desired start date of {}.\n\n*This is a regional alert only,* and is not being triaged globally. This message is for the SIMS Network's situational awareness only.\n\nYou can find the standard role profile for this position <{}|here>.".format(alert['region'], alert['event_go_id'], alert['event_name'], colors_to_emoji[alert['severity']], alert['role_profile'], alert['country'], alert['start'].strftime("%B %d"), standard_profiles[alert['role_profile']])
						# fire off alert
						# new_surge_alert(message)
					# skip if slack api not responsive
					except Exception as e: 
						current_app.logger.error('Send IM Surge Alert to Slack failed: {}'.format(e))
				try:
					db.session.add(individual_alert)
					db.session.commit()
					count_new_records += 1
				except:
					pass
	except Exception as e:
		current_app.logger.error('Surge Alert GO API Query Failed: {}'.format(e))
	
	current_app.logger.info('Surge Alert GO API query finished, logged {} new records.'.format(count_new_records))