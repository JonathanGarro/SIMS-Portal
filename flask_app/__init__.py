from flask import Flask, session
from apscheduler.schedulers.background import BackgroundScheduler
from flask_app.models import alert
import requests
import math
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = 'FLASK_APP_SECRET_KEY'
app.config['HEADSHOT_FOLDER'] = 'static/uploaded_files/headshots'

get_go = BackgroundScheduler(daemon = True)
get_go.start()

@get_go.scheduled_job(trigger = 'cron', day = '*')
def get_im_alerts():
	print("RUNNING CRON JOB\n================\n")
	alert.Alert.clear_alert_table_before_update() # clear out alerts table before API run
	
	api_call = 'https://goadmin.ifrc.org/api/v2/surge_alert/'
	r = requests.get(api_call).json()
	
	current_page = 1
	page_count = int(math.ceil(r['count'] / 50))
	print(f"THE PAGE COUNT TOTAL IS: {page_count}")
	
	output = []
	
	while current_page <= page_count:
		for x in r['results']:
			temp_dict = {}
			if x['molnix_tags']:
				for y in x['molnix_tags']:
					if ("Manager" in y['description']) or ("Officer" in y['description']) or ("Analyst" in y['description']) or ("Coordinator" in y['description']):
						temp_dict['role_profile'] = y['description']
						temp_dict['alert_date'] = x['opens']
						temp_dict['alert_id'] = x['id']
						temp_dict['alert_status'] = x['molnix_status']
						if x['event']:
							temp_dict['event_name'] = x['event']['name']
							temp_dict['event_go_id'] = x['event']['id']
							temp_dict['event_date'] = x['event']['disaster_start_date']
						if x['country']:
							temp_dict['location'] = x['country']['name']
						output.append(temp_dict)
		if r['next']:
			next_page = requests.get(r['next']).json()
			r = next_page
			current_page += 1
		else:
			break
	for each in output:
		alert.Alert.save_GO_alerts_from_API(each)
	print("\n==================\nFINISHED CRON JOB")