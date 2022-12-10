from SIMS_Portal import db
from flask import current_app
from SIMS_Portal.models import Alert
from flask_apscheduler import APScheduler
import math
import requests

scheduler = APScheduler()

@scheduler.task('cron', id='run_surge_alert_refresh', minute='*')
def refresh_surge_alerts():

	existing_alerts = db.session.query(Alert).with_entities(Alert.alert_id).all()
	print(existing_alerts)
	
	
	existing_alert_ids = []
	for alert in existing_alerts:
		existing_alert_ids.append(alert.alert_id)
	
	print("RUNNING SURGE ALERT CRON JOB\n================\n")
	
	api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
	r = requests.get(api_call).json()
	
	tags_list = ['ADMIN-CO', 'ASSES-CO', 'CEA- RCCE', 'CEA-CO', 'CEA-OF', 'CIVMILCO', 'COM-TL', 'COMCO', 'COMOF', 'COMPH', 'COMVID', 'CVACO', 'CVAOF', 'DEP-OPMGR', 'DRR-CO', 'EAREC-OF', 'FIELDCO', 'FIN-CO', 'HEALTH-CO', 'HEALTH-ETL', 'HEOPS', 'HRCO', 'HUMLIAS', 'IDRLCO', 'IM-CO', 'IM-PDC', 'IM-VIZ', 'IMANALYST', 'ITT-CO', 'ITT-OF', 'LIVECO', 'LIVEINCM', 'LIVEMRKT', 'LOG-CO', 'LOG-ETL', 'LOG-OF', 'LOGADMIN', 'LOGAIROPS', 'LOGCASH', 'LOGFLEET', 'LOGPIPELINE', 'LOGPROC', 'LOGWARE', 'MDHEALTH-CO', 'MEDLOG', 'MIG-CO', 'MOVCO', 'NSDCO', 'NSDVOL', 'OPMGR', 'PER-CO', 'PER-OF', 'PGI-CO', 'PGI-OF', 'PHEALTH-CO', 'PMER-CO', 'PMER-OF', 'PRD-NS', 'PRD-OF', 'PSS-CO', 'PSS-ERU', 'PSS-OF', 'PSSCMTY', 'RECCO', 'RELCO', 'RELOF', 'SEC-CO', 'SHCLUSTER-CO', 'SHCLUSTER-DEP', 'SHCLUSTER-ENV', 'SHCLUSTER-HUB', 'SHCLUSTER-IM', 'SHCLUSTER-REC', 'SHCLUSTER-TEC', 'SHELTERP-CB', 'SHELTERP-CO', 'SHELTERP-SP', 'SHELTERP-TEC', 'SHELTERP-TL', 'STAFFHEALTH', 'WASH-CO', 'WASH-ENG', 'WASH-ETL', 'WASH-HP', 'WASH-SAN', 'WASH-TEC']
	
	im_tags = ['IM-CO', 'IM-PDC', 'IM-VIZ', 'IMANALYST']
	
	current_page = 1
	page_count = int(math.ceil(r['count'] / 50))
	print(f"THE PAGE COUNT TOTAL IS: {page_count}")
	
	output = []
	
	# while current_page <= page_count:
	for x in r['results']:
		temp_dict = {}
		if x['id'] not in existing_alert_ids:
			if x['molnix_tags']:
				for y in x['molnix_tags']:
					if y['name'] in tags_list:
						if y['name'] in im_tags:
							temp_dict['im_filter'] = 1
						else:
							temp_dict['im_filter'] = 0 
						temp_dict['role_profile'] = y['description']
						temp_dict['alert_date'] = x['opens']
						temp_dict['start'] = x['start']
						temp_dict['end'] = x['end']
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
							temp_dict['event_date'] = x['event']['disaster_start_date']
							if x['country']:
								temp_dict['country'] = x['country']['name']
								try:
									temp_dict['iso3'] = x['country']['iso3']
								except:
									temp_dict['iso3'] = ''
								output.append(temp_dict)
	print(output[:3])
		# if r['next']:
		# 	next_page = requests.get(r['next']).json()
		# 	r = next_page
		# 	current_page += 1
		# else:
		# 	break