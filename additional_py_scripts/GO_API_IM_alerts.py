import requests
import math
import os
from dotenv import load_dotenv
load_dotenv()

@get_go.scheduled_job(trigger = 'cron', second = '*/10')
def get_im_alerts():
	print("RUNNING CRON JOB")
	api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
	headers = {'Authorization': 'Token "FLASK_APP_API_KEY"'}
	r = requests.get(api_call, headers).json()

	current_page = 1
	page_count = int(math.ceil(r['count'] / 50))
	
	alert_messages = []

	while current_page <= page_count:
		for x in r["results"]:
			# if x['molnix_status'] == 'active':
			for y in x['molnix_tags']:
				if "IM-CO" in y['name']:
					alert_messages.append(x['message'])
				elif "IM-PDC" in y['name']:
					alert_messages.append(x['message'])
				elif "IM-VIZ" in y['name']:
					alert_messages.append(x['message'])
				elif "IMANALYST" in y['name']:
					alert_messages.append(x['message'])
		if r['next']:
			next_page = requests.get(r['next'], headers).json()
			r = next_page
		current_page += 1

	return alert_messages