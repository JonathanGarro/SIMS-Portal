from SIMS_Portal import db
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from SIMS_Portal.models import Alert
from flask_apscheduler import APScheduler
import datetime
import math
import requests
import re
from deepdiff import DeepDiff

scheduler = APScheduler()

@scheduler.task('cron', id='run_surge_alert_refresh', hour='18')
def refresh_surge_alerts():
	print("RUNNING SURGE ALERT CRON JOB\n============================\n")

	existing_alerts = db.session.query(Alert).all()
	existing_alert_ids = []
	existing_statuses = []
	for alert in existing_alerts:
		existing_alert_ids.append(alert.alert_id)
		temp_dict = {}
		temp_dict['id'] = alert.alert_id
		temp_dict['status'] = alert.alert_status
		existing_statuses.append(temp_dict)
	
	api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
	r = requests.get(api_call).json()
	
	tags_list = ['ADMIN-CO', 'ASSES-CO', 'CEA- RCCE', 'CEA-CO', 'CEA-OF', 'CIVMILCO', 'COM-TL', 'COMCO', 'COMOF', 'COMPH', 'COMVID', 'CVACO', 'CVAOF', 'DEP-OPMGR', 'DRR-CO', 'EAREC-OF', 'FIELDCO', 'FIN-CO', 'HEALTH-CO', 'HEALTH-ETL', 'HEOPS', 'HRCO', 'HUMLIAS', 'IDRLCO', 'IM-CO', 'IM-PDC', 'IM-VIZ', 'IMANALYST', 'ITT-CO', 'ITT-OF', 'LIVECO', 'LIVEINCM', 'LIVEMRKT', 'LOG-CO', 'LOG-ETL', 'LOG-OF', 'LOGADMIN', 'LOGAIROPS', 'LOGCASH', 'LOGFLEET', 'LOGPIPELINE', 'LOGPROC', 'LOGWARE', 'MDHEALTH-CO', 'MEDLOG', 'MIG-CO', 'MOVCO', 'NSDCO', 'NSDVOL', 'OPMGR', 'PER-CO', 'PER-OF', 'PGI-CO', 'PGI-OF', 'PHEALTH-CO', 'PMER-CO', 'PMER-OF', 'PRD-NS', 'PRD-OF', 'PSS-CO', 'PSS-ERU', 'PSS-OF', 'PSSCMTY', 'RECCO', 'RELCO', 'RELOF', 'SEC-CO', 'SHCLUSTER-CO', 'SHCLUSTER-DEP', 'SHCLUSTER-ENV', 'SHCLUSTER-HUB', 'SHCLUSTER-IM', 'SHCLUSTER-REC', 'SHCLUSTER-TEC', 'SHELTERP-CB', 'SHELTERP-CO', 'SHELTERP-SP', 'SHELTERP-TEC', 'SHELTERP-TL', 'STAFFHEALTH', 'WASH-CO', 'WASH-ENG', 'WASH-ETL', 'WASH-HP', 'WASH-SAN', 'WASH-TEC']
	
	im_tags = ['IM-CO', 'IM-PDC', 'IM-VIZ', 'IMANALYST']
	
	current_page = 1
	page_count = int(math.ceil(r['count'] / 50))
	print(f"The GO Surge Alert API Call Returned {page_count} pages.")
	
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
						temp_dict['alert_date'] = datetime.datetime.strptime(x['opens'], "%Y-%m-%dT%H:%M:%SZ")
						if x['start']:
							temp_dict['start'] = datetime.datetime.strptime(x['start'], "%Y-%m-%dT%H:%M:%SZ")
						else:
							temp_dict['start'] = datetime.datetime.strptime('1900-01-01T13:33:46Z', "%Y-%m-%dT%H:%M:%SZ")
						if x['end']:
							temp_dict['end'] = datetime.datetime.strptime(x['end'], "%Y-%m-%dT%H:%M:%SZ")
						else:
							temp_dict['end'] = datetime.datetime.strptime('1900-01-01T13:33:46Z', "%Y-%m-%dT%H:%M:%SZ")	
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
			output.append(temp_dict)
				
		if r['next']:
			next_page = requests.get(r['next']).json()
			r = next_page
			current_page += 1
		else:
			break
	
	# add new records
	for alert in output:
		if alert and alert['alert_id'] not in existing_alert_ids:
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
				iso3 = alert['iso3']
			)
			
			db.session.add(individual_alert)
			db.session.commit()
	
	shortened_output = []
	for x in output:
		if x:
			temp_dict = {}
			temp_dict['id'] = x['alert_id']
			temp_dict['status'] = x['alert_status']
			shortened_output.append(temp_dict)
	
	alert_updates = DeepDiff(existing_statuses, shortened_output).get('values_changed',{})

	for key, val in alert_updates.items():
		index = re.sub('\D','', key)
		db.session.query(Alert).filter(Alert.alert_id == existing_statuses[int(index)]['id']).update({'alert_status': val['new_value']})
		db.session.commit()
	
	print("\n==================\nFINISHED CRON JOB")